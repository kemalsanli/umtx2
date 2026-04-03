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

- **[etaHEN](https://github.com/etaHEN/etaHEN)** — [LightningMods](https://github.com/LightningMods), [Buzzer](https://github.com/Buzzer), [sleirsgoevy](https://github.com/sleirsgoevy), [ChendoChap](https://github.com/ChendoChap), [astrelsky](https://github.com/astrelsky), [illusion](https://github.com/illusion), [CTN](https://github.com/CTN), [SiSTR0](https://github.com/SiSTR0), [Nomadic](https://github.com/Nomadic)
- **ps5-payload-dev** — [john-tornblom](https://github.com/john-tornblom) ([websrv](https://github.com/ps5-payload-dev/websrv), [ftpsrv](https://github.com/ps5-payload-dev/ftpsrv), [klogsrv](https://github.com/ps5-payload-dev/klogsrv), [shsrv](https://github.com/ps5-payload-dev/shsrv), [gdbsrv](https://github.com/ps5-payload-dev/gdbsrv), [elfldr](https://github.com/ps5-payload-dev/elfldr))
- **[ps5debug](https://github.com/idlesauce/ps5debug)** — [SiSTR0](https://github.com/SiSTR0), ctn123, [Dizz](https://github.com/Dizz), [golden](https://github.com/golden), [idlesauce](https://github.com/idlesauce)
- **[ps5-kstuff](https://github.com/EchoStretch/kstuff)** — [sleirsgoevy](https://github.com/sleirsgoevy), [EchoStretch](https://github.com/EchoStretch), [john-tornblom](https://github.com/john-tornblom), [LightningMods](https://github.com/LightningMods), [BestPig](https://github.com/BestPig), [zecoxao](https://github.com/zecoxao), [buzzer-re](https://github.com/buzzer-re)
- **[kstuff-lite](https://github.com/drakmor/kstuff-lite)** — [drakmor](https://github.com/drakmor) (Performance optimized fork)
- **[ShadowMountPlus](https://github.com/drakmor/ShadowMountPlus)** — [drakmor](https://github.com/drakmor), [VoidWhisper](https://github.com/VoidWhisper), [BestPig](https://github.com/BestPig), [EchoStretch](https://github.com/EchoStretch), [Gezine](https://github.com/Gezine), [earthonion](https://github.com/earthonion), [LightningMods](https://github.com/LightningMods), [john-tornblom](https://github.com/john-tornblom)
- **VoidShell** — [VoidWhisper](https://github.com/VoidWhisper) ([Ko-fi](https://ko-fi.com/voidwhisper))
- **[Byepervisor](https://github.com/EchoStretch/Byepervisor)** — [SpecterDev](https://github.com/SpecterDev), [ChendoChap](https://github.com/ChendoChap), [flatz](https://github.com/flatz), [fail0verflow](https://github.com/fail0verflow), [Znullptr](https://github.com/Znullptr), [kiwidog](https://github.com/kiwidog), [sleirsgoevy](https://github.com/sleirsgoevy), [EchoStretch](https://github.com/EchoStretch), [LightningMods](https://github.com/LightningMods), [BestPig](https://github.com/BestPig), [zecoxao](https://github.com/zecoxao), [TheOfficialFloW](https://github.com/TheOfficialFloW)
- **[BackPork](https://github.com/BestPig/BackPork)** — [BestPig](https://github.com/BestPig) (System library sideloading)
- **[libhijacker](https://github.com/illusion0001/libhijacker)** — [illusion0001](https://github.com/illusionyy), [astrelsky](https://github.com/astrelsky)
- **PSFree** — obhq (WebKit exploit framework)
- **[Browser AppCache Remover](https://github.com/Storm21CH/PS5_Browser_appCache_remove)** — [Storm21CH](https://github.com/Storm21CH)
- **[Mashm4n](https://www.reddit.com/u/Mashm4n)** — PS5 fPKG creation for UMTX 2
- **[TheOfficialFloW](https://github.com/TheOfficialFloW)**, [sleirsgoevy](https://github.com/sleirsgoevy), [fail0verflow](https://github.com/fail0verflow), [SpecterDev](https://github.com/SpecterDev), [ChendoChap](https://github.com/ChendoChap), [flatz](https://github.com/flatz) — PS5 security research
- **[shahrilnet](https://github.com/shahrilnet)**, n0llptr — UMTX implementations
- **All PS5 homebrew community members**

Individual payloads retain their original licenses. Check the respective GitHub repositories or the Licences button in the app for details.

## License

See [LICENSE](LICENSE) for details.
