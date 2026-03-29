// @ts-check

/**
 * Developer options & Konami code.
 * Depends on: constants, toast-notifications
 */

var konamiIndex = 0;
var konamiIndexKeyboard = 0;

/**
 * Load developer options from localStorage.
 */
function loadDevOptions() {
    try {
        var saved = localStorage.getItem(SETTINGS_DEV_MODE);
        if (saved) {
            var parsed = JSON.parse(saved);
            for (var key in parsed) {
                if (parsed.hasOwnProperty(key)) {
                    window.devOptions[key] = parsed[key];
                }
            }
        }
    } catch (e) {
        console.error("Error loading dev options:", e);
    }
}

/**
 * Save developer options to localStorage.
 */
function saveDevOptions() {
    try {
        localStorage.setItem(SETTINGS_DEV_MODE, JSON.stringify(window.devOptions));
    } catch (e) {
        console.error("Error saving dev options:", e);
    }
}

/**
 * Activate developer mode and show the developer options modal.
 */
function activateDevMode() {
    showToast("🎮 Developer Mode Activated!", TOAST_SUCCESS_TIMEOUT);
    openDevOptions();
}

/**
 * Open the developer options modal.
 */
function openDevOptions() {
    var modal = document.getElementById('dev-options-modal');
    if (modal) {
        populateDevOptions();
        modal.classList.add('show');
    }
}

/**
 * Close the developer options modal.
 */
function closeDevOptions() {
    var modal = document.getElementById('dev-options-modal');
    if (modal) {
        modal.classList.remove('show');
    }
}

/**
 * Create a toggle switch for developer options.
 * @param {string} label - The label text
 * @param {boolean} checked - Initial checked state
 * @param {function} onChange - Callback when toggled
 * @returns {HTMLElement}
 */
function createDevToggle(label, checked, onChange) {
    var container = document.createElement('div');
    container.className = 'dev-option-toggle';

    var labelEl = document.createElement('label');
    labelEl.className = 'dev-option-label';
    labelEl.textContent = label;
    container.appendChild(labelEl);

    var toggle = document.createElement('label');
    toggle.className = 'switch';

    var input = document.createElement('input');
    input.type = 'checkbox';
    input.checked = checked;
    input.addEventListener('change', function (e) {
        onChange(e.target.checked);
    });
    toggle.appendChild(input);

    var slider = document.createElement('span');
    slider.className = 'slider round';
    toggle.appendChild(slider);

    container.appendChild(toggle);

    return container;
}

/**
 * Populate the developer options modal with current settings.
 */
function populateDevOptions() {
    var body = document.getElementById('dev-options-body');
    if (!body) return;

    body.innerHTML = '';

    // Bypass Firmware Compatibility toggle
    body.appendChild(createDevToggle(
        'Bypass Firmware Compatibility',
        window.devOptions.bypassFirmware,
        function (enabled) {
            window.devOptions.bypassFirmware = enabled;
            saveDevOptions();
            showToast(enabled ? "Firmware check disabled" : "Firmware check enabled", TOAST_SUCCESS_TIMEOUT);
        }
    ));

    // Show All Payloads toggle
    body.appendChild(createDevToggle(
        'Show All Payloads',
        window.devOptions.showAllPayloads,
        function (enabled) {
            window.devOptions.showAllPayloads = enabled;
            saveDevOptions();
            showToast(enabled ? "All payloads will be shown" : "Payload visibility restored", TOAST_SUCCESS_TIMEOUT);
        }
    ));

    // Show Pre-release Versions toggle
    body.appendChild(createDevToggle(
        'Show Pre-release Versions',
        window.devOptions.showPreRelease,
        function (enabled) {
            window.devOptions.showPreRelease = enabled;
            saveDevOptions();
            showToast(enabled ? "Pre-release versions will be shown" : "Pre-release versions hidden", TOAST_SUCCESS_TIMEOUT);
        }
    ));

    // Debug Mode toggle
    body.appendChild(createDevToggle(
        'Debug Mode',
        window.devOptions.debugMode,
        function (enabled) {
            window.devOptions.debugMode = enabled;
            saveDevOptions();
            showToast(enabled ? "Debug logging enabled" : "Debug logging disabled", TOAST_SUCCESS_TIMEOUT);
        }
    ));

    // Clear All Cache button
    var clearCacheBtn = document.createElement('button');
    clearCacheBtn.className = 'dev-option-button';
    clearCacheBtn.textContent = 'Clear All Cache';
    clearCacheBtn.onclick = function () {
        localStorage.clear();
        sessionStorage.clear();
        showToast("All cache cleared", TOAST_SUCCESS_TIMEOUT);
    };
    body.appendChild(clearCacheBtn);

    // Reset Settings button
    var resetBtn = document.createElement('button');
    resetBtn.className = 'dev-option-button danger';
    resetBtn.textContent = 'Reset Settings';
    resetBtn.onclick = function () {
        localStorage.clear();
        sessionStorage.clear();
        location.reload();
    };
    body.appendChild(resetBtn);

}

/**
 * Developer challenge modal state
 */
var devChallengeIndex = 0;
var KONAMI_SEQUENCE = [38, 38, 40, 40, 37, 39, 37, 39]; // ↑↑↓↓←→←→

/**
 * Open the developer challenge modal (Tinfoil-style).
 * If skip code is enabled, bypass directly to dev options.
 */
function openDevChallenge() {
    // Open challenge modal
    devChallengeIndex = 0;
    resetProgressBoxes();
    var modal = document.getElementById('dev-challenge-modal');
    if (modal) {
        modal.classList.add('show');
    }

    // Add keyboard listener
    document.addEventListener('keydown', handleDevChallengeKey);
}

/**
 * Close the developer challenge modal.
 */
function closeDevChallenge() {
    var modal = document.getElementById('dev-challenge-modal');
    if (modal) {
        modal.classList.remove('show');
    }
    document.removeEventListener('keydown', handleDevChallengeKey);
    devChallengeIndex = 0;
}

/**
 * Handle keydown events in the developer challenge modal.
 * @param {KeyboardEvent} e
 */
function handleDevChallengeKey(e) {
    if (e.keyCode === KONAMI_SEQUENCE[devChallengeIndex]) {
        // Correct key - highlight box in green
        var box = document.getElementById('prog-' + devChallengeIndex);
        if (box) {
            box.classList.add('correct');
        }
        devChallengeIndex++;

        if (devChallengeIndex >= KONAMI_SEQUENCE.length) {
            // All code entered! Success!
            document.removeEventListener('keydown', handleDevChallengeKey);

            setTimeout(function () {
                closeDevChallenge();
                openDevOptions();
                showToast("Developer mode activated!", 3000);
            }, 500);
        }
    } else if (e.keyCode === 27) { // ESC
        closeDevChallenge();
    } else {
        // Wrong key - reset
        devChallengeIndex = 0;
        resetProgressBoxes();
        // Red flash effect
        var progress = document.getElementById('dev-challenge-progress');
        if (progress) {
            progress.classList.add('shake');
            setTimeout(function () {
                progress.classList.remove('shake');
            }, 500);
        }
    }
}

/**
 * Reset all progress boxes to default state.
 */
function resetProgressBoxes() {
    for (var i = 0; i < 8; i++) {
        var box = document.getElementById('prog-' + i);
        if (box) {
            box.classList.remove('correct');
        }
    }
}

/**
 * Register the Konami code listener.
 * Activates developer options when the code is entered.
 */
function registerKonamiCode() {
    // Load developer options from localStorage
    loadDevOptions();

    document.addEventListener('keydown', function (event) {
        // Only active on landing page (pre-jb-view)
        var preJbView = document.getElementById('pre-jb-view');
        if (!preJbView || !preJbView.classList.contains('selected')) {
            return;
        }

        // PS5 Controller input
        if (event.keyCode >= 1 && event.keyCode <= 15) {
            if (event.keyCode === KONAMI_CODE[konamiIndex]) {
                konamiIndex++;
                if (konamiIndex === KONAMI_CODE.length) {
                    activateDevMode();
                    konamiIndex = 0;
                }
            } else {
                konamiIndex = 0;
            }
        }

        // Keyboard input (for testing)
        if (event.key) {
            if (event.key.toLowerCase() === KONAMI_CODE_KEYBOARD[konamiIndexKeyboard].toLowerCase()) {
                konamiIndexKeyboard++;
                if (konamiIndexKeyboard === KONAMI_CODE_KEYBOARD.length) {
                    activateDevMode();
                    konamiIndexKeyboard = 0;
                }
            } else {
                konamiIndexKeyboard = 0;
            }
        }
    });
}

// Export to global scope
window.loadDevOptions = loadDevOptions;
window.saveDevOptions = saveDevOptions;
window.activateDevMode = activateDevMode;
window.openDevOptions = openDevOptions;
window.closeDevOptions = closeDevOptions;
window.createDevToggle = createDevToggle;
window.populateDevOptions = populateDevOptions;
window.registerKonamiCode = registerKonamiCode;
window.openDevChallenge = openDevChallenge;
window.closeDevChallenge = closeDevChallenge;
window.handleDevChallengeKey = handleDevChallengeKey;
window.resetProgressBoxes = resetProgressBoxes;
