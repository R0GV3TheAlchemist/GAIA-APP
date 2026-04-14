# Rust (Tauri Layer) — GAIA-APP Language Preface

**Role:** Native OS operations, Bluetooth HRV sensor wiring, file system access, security boundary  
**Phase:** T5-D (Live Sensor Wiring) — Week 3+  
**Files already in repo:** `src-tauri/` directory

---

## Why GAIA Needs Rust

Tauri uses Rust as its native layer — the code that runs *outside* the browser
sandbox with full OS access. For GAIA, this matters in three specific places:

1. **Bluetooth Low Energy (BLE) sensor access** — the phone/wearable HRV and
   EEG data for the BCI engine cannot be read from Python or TypeScript alone.
   Tauri's Rust layer can call the OS Bluetooth API directly.

2. **Local memory store security** — the Gaian's long-term memory (Akashic Field)
   should live encrypted on-device, not in the cloud. Rust handles file I/O
   and encryption at the OS level.

3. **Tauri command bridge** — every TypeScript call that needs native capability
   crosses into Rust via a `#[tauri::command]` function. This is the security
   boundary between the UI and the OS.

---

## What Rust Will Build

### 1. BLE HRV Command (`src-tauri/src/commands/bci.rs`)
```rust
#[tauri::command]
async fn read_hrv_stream(device_id: String) -> Result<HRVReading, String> {
    // Connects to Bluetooth HRV device
    // Streams RMSSD and LF/HF ratio to Python via local WebSocket
}
```
This is the live sensor wire for T5-D. Once this exists, `bci_coherence.py`
can switch from `BCISource.SYNTHETIC` to `BCISource.LIVE`.

### 2. Encrypted Local Memory (`src-tauri/src/commands/memory.rs`)
Read/write Gaian memory fragments to an encrypted local SQLite database.
The Python MemoryStore calls this via Tauri's IPC bridge.

### 3. System Tray + Native Notifications
GAIA running in the background, surfacing a Vitality Engine alert
("Your canon grounding is weakening — 3 days since last [C##] citation")
as a native OS notification.

---

## When It Becomes Relevant

Rust is **not needed yet**. The current Python + TypeScript sprint can run
entirely without touching `src-tauri/`. Rust becomes the build target when:
- T5-D (live sensor wiring) is scheduled (Week 3+)
- Local encrypted memory storage is prioritised
- Native system tray integration is needed

---

## How It Connects to Python

```
Rust (Tauri)                         Python (FastAPI)
────────────                         ────────────────
bci.rs read_hrv_stream()   →WS→     bci_coherence.py
  emits HRV JSON                       BCISource.LIVE

memory.rs read_memory()    →IPC→    memory_store.py
  SQLite encrypted read                AkashicRetrieval
```

---

## Learning Path (if new to Rust)

1. **The Rust Book** — [doc.rust-lang.org/book](https://doc.rust-lang.org/book) (free, official)
2. **Tauri v2 Rust commands** — [tauri.app/v2/guide/calling-rust](https://tauri.app/v2/guide/calling-rust)
3. **btleplug** (BLE library) — [github.com/deviceplug/btleplug](https://github.com/deviceplug/btleplug)

The Tauri team has designed the Rust layer to be approachable even for
non-Rust developers. Most Tauri commands are 10–30 lines. You do not need
to master Rust's ownership model deeply to build GAIA's sensor bridge.
