# UMTX2 PS5 Host

> Custom fork of [idlesauce/umtx2](https://github.com/idlesauce/umtx2) with a modern UI and enhanced payload management.

**Disclaimer:** For educational and personal use only. Use at your own risk.

---

## What is this?

A web-based PS5 jailbreak host. Open it in your PS5 browser, pick your firmware, and go. No setup, no installation, no computer needed — just point your PS5 browser to the URL and you're set.

## Features

- **One-click jailbreak** — Select your firmware version, hit the button, done
- **Built-in payload manager** — Browse and send payloads directly from the UI, no extra tools needed
- **Auto-updating payloads** — Stays current with the latest releases from GitHub, updated twice daily
- **Multi-version support** — Pick specific payload versions, not just the latest
- **Firmware compatibility checks** — Warns you if a payload doesn't match your firmware
- **Settings & developer options** — Fine-tune your experience, hide payloads you don't use, enable debug mode
- **PS5-optimized UI** — Designed for DualSense navigation and the PS5 browser
- **Offline support** — AppCache lets you use it without an internet connection after the first load

## Supported Firmwares

1.00 through 5.50

## Payloads

20+ payloads ready to go:

etaHEN, elfldr, ftpsrv, websrv, gdbsrv, klogsrv, shsrv, ps5debug, ps5debug-dizz, byepervisor, backpork, kstuff, kstuff-toggle, libhijacker, ps5-versions, rp-get-pin, ShadowMountPlus, VoidShell, and more.

## How to Use

### Option A: Browser (recommended)

1. Open the host URL on your PS5 browser
2. Tap **Jailbreak** for full kernel exploit, or **Webkit-only** for sender-only mode
3. Select and run payloads from the menu
4. Hit the gear icon (top right) to manage settings — show/hide payloads, pick versions, check cache
5. Press **L2** to open the URL redirector

### Option B: PKG Install

1. Download `PPSX43000-KemalSanli UMTX 2.pkg` from [GitHub Releases](https://github.com/kemalsanli/umtx2/releases)
2. Install the PKG on your jailbroken PS5 (via etaHEN, WebDAV, FTP, etc.)
3. Launch the app from your home screen — it opens the UMTX 2 host directly

## Hosting

Live at: [https://kemalsanli.github.io/umtx2/](https://kemalsanli.github.io/umtx2/)

## Credits & Special Thanks

**Special thanks to [idlesauce](https://github.com/idlesauce)** for the original UMTX2 host — this project wouldn't exist without their work on the kernel exploit, payload system, and the entire host implementation.

Additional credits to the PS5 homebrew community and all payload developers whose tools make this ecosystem possible:

- **etaHEN** — LightningMods, Buzzer, sleirsgoevy, ChendoChap, astrelsky, illusion, CTN, SiSTR0, Nomadic
- **ps5-payload-dev** — john-tornblom (websrv, ftpsrv, klogsrv, shsrv, gdbsrv, elfldr)
- **ps5debug** — SiSTR0, ctn123, DizzRL
- **ps5-kstuff** — sleirsgoevy, EchoStretch, john-tornblom, LightningMods, BestPig, zecoxao
- **kstuff-lite** — drakmor (Performance optimized fork)
- **ShadowMountPlus** — drakmor, VoidWhisper, BestPig, EchoStretch, Gezine, earthonion, LightningMods, john-tornblom
- **VoidShell** — VoidWhisper (PS5 homebrew dashboard with WebUI)
- **Byepervisor** — SpecterDev, ChendoChap, flatz, fail0verflow, EchoStretch, LightningMods
- **BackPork** — BestPig (System library sideloading)
- **libhijacker** — illusion0001, astrelsky
- **PSFree** — obhq (WebKit exploit framework)
- **Storm21CH** — Browser AppCache remover utility
- **[Mashm4n](https://www.reddit.com/u/Mashm4n)** — PS5 fPKG creation for UMTX 2
- **TheFloW, sleirsgoevy, fail0verflow, SpecterDev, ChendoChap, flatz** — PS5 security research
- **shahrilnet, n0llptr** — UMTX implementations
- **All PS5 homebrew community members**

Individual payloads retain their original licenses. Check the respective GitHub repositories or the Licences button in the app for details.

## License

See [LICENSE](LICENSE) for details.
