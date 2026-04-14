# Dart / Flutter — GAIA-APP Language Preface

**Role:** iOS and Android mobile companion app  
**Phase:** Future — Mobile Layer (post-desktop stability)  
**Stack:** Dart language + Flutter framework + FastAPI backend

---

## Why GAIA Needs Dart / Flutter

The Tauri desktop app is GAIA's primary home. But the Gaian lives in a body
that moves through the world — and the most intimate biometric data (HRV,
steps, sleep, temple heat) lives in the phone they carry.

Flutter is the only framework that lets a single Dart codebase compile to
native iOS and Android apps with full hardware access — camera, Bluetooth,
Health Kit, Google Fit. This is the mobile layer that:

1. **Carries the BCI engine into daily life** — passive HRV monitoring
   between sessions, feeding `bci_coherence.py` even when the desktop is closed
2. **Surfaces Vitality Engine alerts natively** — "Your noosphere resonance
   label is 48 hours old. Return to neutral baseline?" as a push notification
3. **Enables offline-first sessions** — GAIA conversations while walking,
   grounded by on-device models
4. **Closes the wearable sensor loop** — direct Bluetooth pairing with
   HRV bands, EEG headsets, and ring sensors (T5-D mobile equivalent)

---

## What Dart / Flutter Will Build

### 1. Mobile Chat Interface (`lib/screens/chat_screen.dart`)
Mirrors the desktop chat — streaming responses, epistemic labels,
MC stage indicator — in a mobile-native layout.

### 2. Passive BCI Monitor (`lib/services/bci_monitor.dart`)
```dart
class BCIMonitorService {
  Stream<HRVReading> streamHRV() {
    // Reads from Health Kit (iOS) or Google Fit (Android)
    // Posts to FastAPI /bci/stream endpoint every 30s
  }
}
```

### 3. Vitality Push Notifications (`lib/services/vitality_notifier.dart`)
Periodically polls the `/gaian/{slug}/vitality` endpoint.
Converts deficiency flags into actionable push notifications.

### 4. Offline GAIAN Presence (`lib/services/local_inference.dart`)
A lightweight on-device model (e.g., Gemma 2B via MediaPipe LLM)
for short grounding exchanges when the desktop server is unavailable.

---

## When It Becomes Relevant

Flutter becomes the build target after:
- The Tauri desktop app is stable and feature-complete
- T5-D (live sensor wiring) is proven on desktop
- The FastAPI backend has a stable mobile API surface

Estimated phase: **post-Sprint G** (after the current engine upgrades
are fully wired and tested).

---

## How It Connects to Python

```
Dart / Flutter                       Python (FastAPI)
──────────────                       ────────────────
HTTP dio package         ←REST→      server.py
  chat_screen.dart                     POST /chat
  bci_monitor.dart                     POST /bci/stream

WebSocket (web_socket_channel) ←WS→  mother_thread.py
  vitality_notifier.dart               broadcast_pulse()
```

---

## Learning Path

1. **Flutter docs** — [docs.flutter.dev](https://docs.flutter.dev) (start with "Get started")
2. **Dart language tour** — [dart.dev/language](https://dart.dev/language)
3. **flutter_blue_plus** (BLE) — [pub.dev/packages/flutter_blue_plus](https://pub.dev/packages/flutter_blue_plus)
4. **health** package (HealthKit/GoogleFit) — [pub.dev/packages/health](https://pub.dev/packages/health)

Dart is syntactically close to TypeScript. If you can write TypeScript,
you will feel at home in Dart within a few hours.
