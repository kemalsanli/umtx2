// @ts-check

/**
 * Shared constants and mutable state for the UMTX2 UI.
 * All constants and state are attached to `window` for global scope access.
 * No ES6 module syntax — PS5 WebKit compatibility.
 */

// ── localStorage keys ───────────────────────────────────────
window.LOCALSTORE_REDIRECTOR_LAST_URL_KEY = "redirector_last_url";
window.SESSIONSTORE_ON_LOAD_AUTORUN_KEY = "on_load_autorun";
window.MAINLOOP_EXECUTE_PAYLOAD_REQUEST = "mainloop_execute_payload_request";
window.SETTINGS_PAYLOAD_VISIBILITY = "payload_visibility";
window.SETTINGS_PAYLOAD_VERSIONS = "payload_versions";
window.SETTINGS_DEV_MODE = "dev_mode";
window.SETTINGS_PAYLOAD_CACHE_STATE = "payload_cache_state";

// ── Toast timeouts ─────────────────────────────────────────
window.TOAST_SUCCESS_TIMEOUT = 2000;
window.TOAST_ERROR_TIMEOUT = 5000;

// ── Konami code sequences ──────────────────────────────────
// PS5 Controller: Up=12, Down=13, Left=14, Right=15 (directions only — Cross/Circle interact with browser)
window.KONAMI_CODE = [12, 12, 13, 13, 14, 15, 14, 15];
window.KONAMI_CODE_KEYBOARD = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight'];

// ── Mutable shared state ───────────────────────────────────
window.devOptions = {
    bypassFirmware: false,
    showAllPayloads: false,
    showPreRelease: true,
    debugMode: false
};

// ── Exploit state ──────────────────────────────────────────
window.exploitStarted = false;

// ── Settings mode state ────────────────────────────────────
window.settingsMode = false;
