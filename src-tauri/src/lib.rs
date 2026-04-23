use std::sync::{Arc, Mutex};
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager,
};
use tauri_plugin_shell::{process::CommandChild, ShellExt};

/// Shared handle to the sidecar child process so we can kill it on exit.
type SidecarHandle = Arc<Mutex<Option<CommandChild>>>;

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

    // Kill existing process if running
    {
        let mut guard = handle.lock().map_err(|e| e.to_string())?;
        if let Some(child) = guard.take() {
            let _ = child.kill();
        }
    }

    // Spawn a fresh sidecar
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

/// Spawn the Python sidecar, store handle, poll /health until ready.
fn start_python_sidecar(app: &tauri::App, handle: SidecarHandle) {
    let shell = app.shell();
    let sidecar_cmd = shell
        .sidecar("gaia-backend")
        .expect("gaia-backend sidecar not found — run PyInstaller first");

    tauri::async_runtime::spawn(async move {
        let spawn_result = sidecar_cmd.spawn();
        match spawn_result {
            Err(e) => {
                eprintln!("[GAIA] Failed to spawn sidecar: {e}");
                return;
            }
            Ok((_rx, child)) => {
                {
                    let mut guard = handle.lock().unwrap();
                    *guard = Some(child);
                }

                // Poll /health with exponential backoff — max 30 s
                let client = reqwest::Client::new();
                let mut delay_ms = 300u64;
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
                            return;
                        }
                        _ => {}
                    }
                    delay_ms = (delay_ms * 3 / 2).min(3000);
                }
                eprintln!("[GAIA] WARNING: backend did not become ready within 30 s");
            }
        }
    });
}

pub fn run() {
    let sidecar_handle: SidecarHandle = Arc::new(Mutex::new(None));

    tauri::Builder::default()
        .manage(sidecar_handle.clone())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(|app| {
            // ── Sidecar ───────────────────────────────────────────────────
            let handle = app
                .state::<SidecarHandle>()
                .inner()
                .clone();
            start_python_sidecar(app, handle);

            // ── Tray ──────────────────────────────────────────────────────
            let open = MenuItem::with_id(app, "open", "Open GAIA", true, None::<&str>)?;
            let check_updates = MenuItem::with_id(app, "updates", "Check for Updates", true, None::<&str>)?;
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
                        // Gracefully kill sidecar before exit
                        if let Some(state) = app.try_state::<SidecarHandle>() {
                            if let Ok(mut guard) = state.lock() {
                                if let Some(child) = guard.take() {
                                    let _ = child.kill();
                                }
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
        // Graceful shutdown on window close
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let app = window.app_handle();
                if let Some(state) = app.try_state::<SidecarHandle>() {
                    if let Ok(mut guard) = state.lock() {
                        if let Some(child) = guard.take() {
                            let _ = child.kill();
                        }
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![greet, get_backend_status, restart_backend])
        .run(tauri::generate_context!())
        .expect("error while running GAIA");
}
