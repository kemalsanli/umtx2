# Changelog

All notable changes to this project will be documented in this file.

This is a custom fork of [idlesauce/umtx2](https://github.com/idlesauce/umtx2). Changes listed here are specific to this fork.

## [2.1.1] - 2026-04-03

### Added
- **PS5 fPKG Package** — Install UMTX 2 directly on your PS5 home screen (`PPSX43000-KemalSanli UMTX 2.pkg`)
- **PKG Install instructions** — Added "Option B: PKG Install" to README

### Credits
- Thanks to [u/Mashm4n](https://www.reddit.com/u/Mashm4n) for creating the PS5 fPKG

---

## [2.1.0] - 2026-03-30

### Added
- **ShadowMountPlus** — Automatic game image mounter (`.ffpkg`, `.exfat`, `.ffpfs`). 16 versions included, supports FW 3.xx–5.xx
- **kstuff-lite (drakmor fork)** — Performance optimized FPKG enabler with 1.5–2x speed improvement. Hidden from UI via `willHideEveryTime` (loaded internally by etaHEN)
- **`willHideEveryTime` payload hiding mechanism** — New metadata property that permanently hides a payload from the UI, regardless of user settings or developer mode. Used for payloads that are loaded internally by other tools and should not be sent manually

### Changed
- **README** — Added ShadowMountPlus and kstuff-lite to payload list, added developer notes section documenting `willHideEveryTime`

---

## [2.0.0] - 2026-03-29

### Added
- **Modern PS5 UI** - Complete redesign with PS5-style interface
- **Top Bar** - Settings icon, profile avatar, live clock
- **Runtime Payload Updates** - GitHub API-based auto-update system
- **Tinfoil Developer Challenge** - Konami code unlock with progress indicator
- **Developer Settings** - Dedicated settings panel with gear icon
- **Credits Display** - Link to original UMTX2 by idlesauce

### Changed
- **Modular Architecture** - Refactored from monolithic to 11 modules
- **README** - Rewritten with user-friendly tone
- **Workflow** - Payload updates twice daily (06:00/18:00 UTC)
- **Pre-release Toggle** - Default enabled for bleeding-edge payloads

### Fixed
- Unicode character rendering (replaced with SVG icons)
- Settings grid layout inconsistencies
- Badge positioning in post-JB view

### Removed
- Test mode bypasses and debug code

---

**Note:** For the original UMTX2 features (PS5 jailbreak, payload loading, firmware detection), see [idlesauce/umtx2](https://github.com/idlesauce/umtx2).

[2.1.1]: https://github.com/kemalsanli/umtx2/releases/tag/v2.1.1
[2.1.0]: https://github.com/kemalsanli/umtx2/releases/tag/v2.1.0
[2.0.0]: https://github.com/kemalsanli/umtx2/releases/tag/v2.0.0
