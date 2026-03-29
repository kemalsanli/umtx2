// @ts-check

/**
 * App entry point - initialization and event handlers.
 * This file should be loaded LAST (after all other modules).
 * Depends on: all other modules
 */

// =====================================================
// === PS5 CLOCK ===
// =====================================================

function updateClock() {
    var clock = document.getElementById('ps5-clock');
    if (clock) {
        var now = new Date();
        var hours = String(now.getHours()).padStart(2, '0');
        var minutes = String(now.getMinutes()).padStart(2, '0');
        clock.textContent = hours + ':' + minutes;
    }
}

// Update every 60 seconds
setInterval(updateClock, 60000);
// Initial call
updateClock();

// =====================================================
// === RUN / EXPLOIT ENTRY POINT ===
// =====================================================

async function run(wkonly, animate) {
    if (wkonly === undefined) wkonly = false;
    if (animate === undefined) animate = true;

    if (window.exploitStarted) {
        return;
    }
    window.exploitStarted = true;

    await switchPage("console-view", animate);

    // not setting it in the catch since we want to retry both on a handled error and on a browser crash
    sessionStorage.setItem(SESSIONSTORE_ON_LOAD_AUTORUN_KEY, wkonly ? "wkonly" : "kernel");

    try {
        if (!animate) {
            // hack but waiting a bit seems to help
            // this only gets hit when auto-running on page load
            await new Promise(function (resolve) { setTimeout(resolve, 100); });
        }
        await run_psfree(fw_str);

    } catch (error) {
        log("Webkit exploit failed: " + error, LogLevel.ERROR);

        log("Retrying in 2 seconds...", LogLevel.LOG);
        await new Promise(function (resolve) { setTimeout(resolve, 2000); });
        window.location.reload();
        return; // this is necessary
    }

    try {
        await main(window.p, wkonly); // if all goes well, this should block forever
    } catch (error) {
        log("Kernel exploit/main() failed: " + error, LogLevel.ERROR);
        // p.write8(new int64(0,0), 0); // crash
    }

    log("Retrying in 4 seconds...", LogLevel.LOG);
    await new Promise(function (resolve) { setTimeout(resolve, 4000); });
    window.location.reload();
}


// =====================================================
// === EVENT HANDLERS ===
// =====================================================

function registerAppCacheEventHandlers() {
    var appCache = window.applicationCache;

    var toast;
    var toastTimeout; // Track the timeout ID

    function createOrUpdateAppCacheToast(message, timeout) {
        if (timeout === undefined) timeout = -1;

        if (!toast) {
            toast = showToast(message, timeout);
        } else {
            updateToastMessage(toast, message);
        }

        // Clear any existing timeout before setting a new one
        if (toastTimeout) {
            clearTimeout(toastTimeout);
            toastTimeout = null;
        }

        if (timeout > 0) {
            toastTimeout = setTimeout(function () {
                removeToast(toast);
                toast = null;
                toastTimeout = null;
            }, timeout);
        }
    }

    if (document.documentElement.hasAttribute("manifest")) {
        if (!navigator.onLine) {
            createOrUpdateAppCacheToast('Offline.', 2000);
        }
    }

    appCache.addEventListener('cached', function (e) {
        createOrUpdateAppCacheToast('Finished caching site.', 1500);
    }, false);

    appCache.addEventListener('checking', function (e) {
        createOrUpdateAppCacheToast("Checking for updates...", 3000);
    }, false);

    appCache.addEventListener('downloading', function (e) {
        createOrUpdateAppCacheToast('Downloading new cache...', 5000);
    }, false);

    appCache.addEventListener('error', function (e) {
        // only show error toast if we're online
        if (navigator.onLine) {
            createOrUpdateAppCacheToast('Error while caching site.', 5000);
        } else {
            createOrUpdateAppCacheToast('Offline.', 2000);
        }
    }, false);

    appCache.addEventListener('noupdate', function (e) {
        createOrUpdateAppCacheToast('Cache is up-to-date.', 1500);
    }, false);

    appCache.addEventListener('obsolete', function (e) {
        createOrUpdateAppCacheToast('Site is obsolete.', 5000);
    }, false);

    appCache.addEventListener('progress', function (e) {
        var percentage = Math.round((e.loaded / e.total) * 100);

        createOrUpdateAppCacheToast('Downloading new cache... ' + percentage + '%', 10000);

        // the last item takes an unreasonably long time to complete (with a big update)
        if (e.loaded + 1 == e.total) {
            createOrUpdateAppCacheToast("Processing... This may take a minute.", 30000);
        }
    }, false);

    appCache.addEventListener('updateready', function (e) {
        if (window.applicationCache.status == window.applicationCache.UPDATEREADY) {
            createOrUpdateAppCacheToast('The site was updated. Refresh to switch to updated version', 10000);
        }
    }, false);
}

function registerL2ButtonHandler() {
    document.addEventListener("keydown", async function (event) {
        // Circle button (keyCode 1) - Go back (context-aware)
        if (event.keyCode === 1) {
            var versionView = document.getElementById('version-selection-view');
            if (versionView && versionView.classList.contains('selected')) {
                event.preventDefault();
                if (window.settingsMode) {
                    // In settings mode: version-selection → settings-view
                    populateSettingsGrid();
                    await switchPage("settings-view");
                } else {
                    // In post-JB mode: version-selection → payloads-view
                    await switchPage("payloads-view");
                }
                return;
            }

            // If on settings view, go back to pre-jb
            var settingsView = document.getElementById('settings-view');
            if (settingsView && settingsView.classList.contains('selected')) {
                event.preventDefault();
                closeSettings();
                return;
            }
        }

        // L2 button (keyCode 118) - Redirect
        if (event.keyCode === 118) {
            var lastRedirectorValue = localStorage.getItem(LOCALSTORE_REDIRECTOR_LAST_URL_KEY) || "http://";
            var redirectorValue = prompt("Enter url", lastRedirectorValue);

            // pressing cancel works as expected, but pressing the back button unfortunately is the same as pressing ok
            if (redirectorValue && redirectorValue !== "http://") {
                localStorage.setItem(LOCALSTORE_REDIRECTOR_LAST_URL_KEY, redirectorValue);
                window.location.href = redirectorValue;
            }
        }

        // R2 button (keyCode 119) - Licences modal toggle
        if (event.keyCode === 119) {
            event.preventDefault();

            // Visual feedback on the licences button
            var licensesBtn = document.querySelector('.licenses-btn');
            if (licensesBtn) {
                licensesBtn.classList.add('pressed');
                setTimeout(function () {
                    licensesBtn.classList.remove('pressed');
                }, 200);
            }

            // Toggle licenses modal
            var licensesModal = document.getElementById('licenses-modal');
            if (licensesModal && licensesModal.classList.contains('show')) {
                closeLicenses();
            } else {
                openLicenses();
            }
            return;
        }
    });
}

// Export to global scope
window.run = run;
window.registerAppCacheEventHandlers = registerAppCacheEventHandlers;
window.registerL2ButtonHandler = registerL2ButtonHandler;
