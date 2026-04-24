#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::{Arc, Mutex};
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Emitter, Manager,
};
use tauri_plugin_shell::{process::CommandChild, ShellExt};

/// Shared handle to the sidecar child process so we can kill it on exit.
type SidecarHandle = Arc<Mutex<Option<CommandChild>>>;

// ── Sidecar status broadcast ──────────────────────────────────────────────────
//
// We emit these events on the main window so the frontend can react:
//   "sidecar:ready"   — backend is up and healthy  → window is shown here
//   "sidecar:error"   — backend failed to start (payload = human-readable reason)

#[derive(Clone, serde::Serialize)]
struct SidecarErrorPayload {
    reason: String,
}

// ── Process-tree kill ─────────────────────────────────────────────────────────
//
// PyInstaller on Windows spawns a parent + child pair.  `CommandChild::kill()`
// only terminates the immediate child, leaving the bootloader alive as a zombie.
// On Windows we use `taskkill /F /T /PID <pid>` which recursively kills the
// entire tree.  On other platforms a standard SIGKILL on the process group works.

#[cfg(target_os = "windows")]
fn kill_process_tree(pid: u32) {
    let _ = std::process::Command::new("taskkill")
        .args(["/F", "/T", "/PID", &pid.to_string()])
        .creation_flags(0x08000000) // CREATE_NO_WINDOW — no console flash
        .status();
}

#[cfg(not(target_os = "windows"))]
fn kill_process_tree(pid: u32) {
    unsafe {
        libc::killpg(pid as i32, libc::SIGKILL);
    }
}

/// Kill the sidecar and its entire process tree, then clear the stored handle.
fn kill_sidecar(guard: &mut Option<CommandChild>) {
    if let Some(child) = guard.take() {
        let pid = child.pid();
        let _ = child.kill();
        kill_process_tree(pid);
    }
}

// ── Tauri commands ────────────────────────────────────────────────────────────

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from GAIA!", name)
}

#[tauri::command]
fn get_backend_status() -> String {
    "online".to_string()
}

#[tauri::command]
async fn restart_backend(app: tauri::AppHandle) -> Result<String, String> {
    let handle: SidecarHandle = app
        .try_state::<SidecarHandle>()
        .ok_or("sidecar state not initialised")?
        .inner()
        .clone();

    {
        let mut guard = handle.lock().map_err(|e| e.to_string())?;
        kill_sidecar(&mut guard);
    }

    let shell = app.shell();
    let cmd = shell
        .sidecar("gaia-backend")
        .map_err(|e| e.to_string())?;
    let (_rx, child) = cmd.spawn().map_err(|e| e.to_string())?;

    {
        let mut guard = handle.lock().map_err(|e| e.to_string())?;
        *guard = Some(child);
    }

    Ok("restarted".to_string())
}

/// Open the GAIA log directory in the OS file explorer.
/// Path: %APPDATA%\GAIA\logs  (Windows) or ~/.local/share/GAIA/logs (Linux/macOS)
#[tauri::command]
async fn open_log_dir(app: tauri::AppHandle) -> Result<(), String> {
    use tauri_plugin_opener::OpenerExt;

    let app_data = app
        .path()
        .app_data_dir()
        .map_err(|e| e.to_string())?;
    let logs_dir = app_data.join("logs");

    if !logs_dir.exists() {
        std::fs::create_dir_all(&logs_dir).map_err(|e| e.to_string())?;
    }

    app.opener()
        .open_path(logs_dir.to_string_lossy().to_string(), None::<&str>)
        .map_err(|e| e.to_string())?;

    Ok(())
}

// ── Sidecar startup ───────────────────────────────────────────────────────────

/// Emit a sidecar:error event and show a native dialog.
fn emit_backend_error(app: &tauri::AppHandle, reason: &str) {
    eprintln!("[GAIA] Backend error: {reason}");

    if let Some(window) = app.get_webview_window("main") {
        let _ = window.emit(
            "sidecar:error",
            SidecarErrorPayload {
                reason: reason.to_string(),
            },
        );
        let _ = window.show();
        let _ = window.set_focus();
    }

    let app_clone = app.clone();
    let reason_owned = reason.to_string();
    tauri::async_runtime::spawn(async move {
        use tauri_plugin_dialog::{DialogExt, MessageDialogKind};
        let _ = app_clone
            .dialog()
            .message(format!(
                "GAIA's Python backend failed to start.\n\n\
                 Reason: {reason_owned}\n\n\
                 Please restart the app. If the problem persists, \
                 check that no other process is using port 8008."
            ))
            .kind(MessageDialogKind::Error)
            .title("GAIA — Backend Error")
            .blocking_show();
    });
}

/// Spawn the Python sidecar, store the handle, poll /health until ready.
///
/// Startup sequence:
///   1. Window is hidden (visible: false in tauri.conf.json)
///   2. Sidecar spawns in the background
///   3. /health is polled with exponential back-off (max 30 s)
///   4a. On success  → emit sidecar:ready → show + focus window
///   4b. On failure  → emit sidecar:error → show window with error state
fn start_python_sidecar(app: &tauri::App, handle: SidecarHandle) {
    let shell = app.shell();
    let app_handle = app.handle().clone();

    let sidecar_result = shell.sidecar("gaia-backend");
    let sidecar_cmd = match sidecar_result {
        Ok(cmd) => cmd,
        Err(e) => {
            emit_backend_error(
                &app_handle,
                &format!("sidecar binary not found — run PyInstaller first ({e})"),
            );
            return;
        }
    };

    tauri::async_runtime::spawn(async move {
        match sidecar_cmd.spawn() {
            Err(e) => {
                emit_backend_error(
                    &app_handle,
                    &format!("failed to launch gaia-backend: {e}"),
                );
            }
            Ok((_rx, child)) => {
                {
                    let mut guard = handle.lock().unwrap();
                    *guard = Some(child);
                }

                let client = reqwest::Client::new();
                let mut delay_ms = 300u64;
                let mut ready = false;

                for attempt in 0..20 {
                    tokio::time::sleep(std::time::Duration::from_millis(delay_ms)).await;
                    match client
                        .get("http://127.0.0.1:8008/health")
                        .timeout(std::time::Duration::from_secs(2))
                        .send()
                        .await
                    {
                        Ok(resp) if resp.status().is_success() => {
                            println!("[GAIA] Python backend ready after attempt {attempt} ✓");
                            ready = true;
                            break;
                        }
                        _ => {}
                    }
                    delay_ms = (delay_ms * 3 / 2).min(3000);
                }

                if ready {
                    if let Some(window) = app_handle.get_webview_window("main") {
                        let _ = window.emit("sidecar:ready", ());
                        let _ = window.show();
                        let _ = window.set_focus();
                    }
                } else {
                    emit_backend_error(
                        &app_handle,
                        "health check timed out after 30 s — port 8008 may be blocked",
                    );
                }
            }
        }
    });
}

// ── App entry point ───────────────────────────────────────────────────────────

pub fn run() {
    let sidecar_handle: SidecarHandle = Arc::new(Mutex::new(None));

    tauri::Builder::default()
        .manage(sidecar_handle.clone())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(|app| {
            let handle = app.state::<SidecarHandle>().inner().clone();
            start_python_sidecar(app, handle);

            let open = MenuItem::with_id(app, "open", "Open GAIA", true, None::<&str>)?;
            let check_updates =
                MenuItem::with_id(app, "updates", "Check for Updates", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&open, &check_updates, &quit])?;

            let _tray = TrayIconBuilder::new()
                .menu(&menu)
                .tooltip("GAIA - Your Sovereign AI")
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "open" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    "quit" => {
                        if let Some(state) = app.try_state::<SidecarHandle>() {
                            if let Ok(mut guard) = state.lock() {
                                kill_sidecar(&mut guard);
                            }
                        }
                        app.exit(0);
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(app)?;

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let app = window.app_handle();
                if let Some(state) = app.try_state::<SidecarHandle>() {
                    if let Ok(mut guard) = state.lock() {
                        kill_sidecar(&mut guard);
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            greet,
            get_backend_status,
            restart_backend,
            open_log_dir
        ])
        .run(tauri::generate_context!())
        .expect("error while running GAIA");
}
