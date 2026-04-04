// @ts-check

/**
 * Settings view - Pre-JB payload settings grid.
 * Depends on: constants, settings-manager, firmware-compat,
 *             toast-notifications, page-switcher, version-selection
 */

/**
 * Open the settings screen from the landing page.
 * Shows ALL payloads (including hidden ones) in a 2-column grid.
 */
function openSettings() {
    if (window.settingsMode) {
        closeSettings();
        return;
    }
    window.settingsMode = true;
    populateSettingsGrid();
    switchPage("settings-view");
}

/**
 * Close the settings screen and return to the landing page.
 */
function closeSettings() {
    preFetchSelectedPayloads();
    window.settingsMode = false;
    switchPage("pre-jb-view");
}

/**
 * Pre-fetch non-default payload versions into browser HTTP cache.
 * Iterates over all visible payloads and fetches selected non-default versions.
 * This is fire-and-forget - errors are silently ignored.
 */
function preFetchSelectedPayloads() {
    var count = 0;
    
    for (var i = 0; i < payload_map.length; i++) {
        var payload = payload_map[i];
        
        // Skip hidden payloads
        if (!isPayloadVisible(payload.id)) {
            continue;
        }
        
        // Get the active version for this payload
        var versionInfo = resolveActiveVersion(payload);
        if (!versionInfo || !versionInfo.filePath) {
            continue;
        }
        
        // Skip default versions (already in AppCache)
        // Find the actual version object to check isDefault flag
        var isDefault = false;
        if (payload.versions && payload.versions.length > 0) {
            for (var j = 0; j < payload.versions.length; j++) {
                if (payload.versions[j].version === versionInfo.version) {
                    isDefault = payload.versions[j].isDefault;
                    break;
                }
            }
        }
        
        if (isDefault) {
            continue;
        }
        
        // Fire-and-forget fetch to pre-load into HTTP cache
        count++;
        fetch(versionInfo.filePath, { cache: "default" })
            ["catch"](function(err) {
                // Silently ignore errors
            });
    }
    
    // Show brief notification if we're caching anything
    if (count > 0) {
        showToast("Caching selected payloads...", 2000);
    }
}

/**
 * Populate the settings payload grid with ALL payloads.
 * Hidden payloads are shown with reduced opacity and a "Hidden" badge.
 * Clicking a payload opens the version selection sub-screen.
 */
function populateSettingsGrid() {
    var grid = document.getElementById('settings-payloads-grid');

    while (grid.firstChild) {
        grid.removeChild(grid.firstChild);
    }

    for (var i = 0; i < payload_map.length; i++) {
        var payload = payload_map[i];
        var visible = isPayloadVisible(payload.id);
        var activeVersionInfo = resolveActiveVersion(payload);
        var activeVersion = activeVersionInfo.version;

        var payloadButton = document.createElement("a");
        payloadButton.classList.add("btn");
        payloadButton.tabIndex = 0;
        payloadButton.style.position = "relative";
        if (!visible) {
            payloadButton.classList.add("settings-payload-hidden");
        }

        // Badge container (top-right)
        var badgeContainer = document.createElement("div");
        badgeContainer.className = "payload-badge-container";

        // Version badge
        var versionBadge = document.createElement("span");
        versionBadge.className = "payload-badge version-badge";
        versionBadge.textContent = "v" + activeVersion;
        badgeContainer.appendChild(versionBadge);

        // Firmware compatibility badge
        var isCompatible = isFirmwareCompatible(payload);
        if (!isCompatible) {
            var incompatibleBadge = document.createElement("span");
            incompatibleBadge.className = "payload-badge incompatible-badge";
            incompatibleBadge.textContent = "Incompatible";
            badgeContainer.appendChild(incompatibleBadge);
        }

        // Hidden badge
        if (!visible) {
            var hiddenBadge = document.createElement("span");
            hiddenBadge.className = "payload-badge hidden-badge";
            hiddenBadge.textContent = "Hidden";
            badgeContainer.appendChild(hiddenBadge);
        }

        // Pre-release badge - check if selected version is pre-release
        var selectedVersionData = payload.versions ? payload.versions.find(function (v) { return v.version === activeVersion; }) : null;
        if (selectedVersionData && selectedVersionData.isPreRelease) {
            var prereleaseBadge = document.createElement("span");
            prereleaseBadge.className = "payload-badge prerelease-badge";
            prereleaseBadge.textContent = "Pre-release";
            badgeContainer.appendChild(prereleaseBadge);
        }

        payloadButton.appendChild(badgeContainer);

        var payloadTitle = document.createElement("p");
        payloadTitle.classList.add("payload-btn-title");
        payloadTitle.textContent = payload.displayTitle;

        var payloadDescription = document.createElement("p");
        payloadDescription.classList.add("payload-btn-description");
        payloadDescription.textContent = payload.description;

        var payloadInfo = document.createElement("p");
        payloadInfo.classList.add("payload-btn-info");
        payloadInfo.textContent = payload.author;

        payloadButton.appendChild(payloadTitle);
        payloadButton.appendChild(payloadDescription);
        payloadButton.appendChild(payloadInfo);

        // Click → open version selection sub-screen (settings mode)
        // Use IIFE to capture payload in closure
        (function (p) {
            payloadButton.addEventListener("click", function () {
                showSettingsVersionPage(p);
            });
        })(payload);

        grid.appendChild(payloadButton);
    }

    // Developer Settings button at the bottom of settings grid
    var devBtn = document.createElement("div");
    devBtn.className = "settings-dev-btn";
    devBtn.tabIndex = 0;
    devBtn.setAttribute("role", "button");
    devBtn.onclick = function () {
        openDevChallenge();
    };

    var devIcon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    devIcon.setAttribute("class", "dev-btn-icon");
    devIcon.setAttribute("viewBox", "0 0 24 24");
    devIcon.setAttribute("fill", "none");
    var gearPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
    gearPath.setAttribute("d", "M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.07-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.8,11.69,4.8,12s0.02,0.64,0.07,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z");
    gearPath.setAttribute("fill", "currentColor");
    devIcon.appendChild(gearPath);

    var devText = document.createElement("span");
    devText.className = "dev-btn-text";
    devText.textContent = "Developer Settings";

    var devArrow = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    devArrow.setAttribute("class", "dev-btn-arrow");
    devArrow.setAttribute("viewBox", "0 0 24 24");
    devArrow.setAttribute("fill", "none");
    var arrowPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
    arrowPath.setAttribute("d", "M9 18l6-6-6-6");
    arrowPath.setAttribute("stroke", "currentColor");
    arrowPath.setAttribute("stroke-width", "2");
    arrowPath.setAttribute("stroke-linecap", "round");
    arrowPath.setAttribute("stroke-linejoin", "round");
    arrowPath.setAttribute("fill", "none");
    devArrow.appendChild(arrowPath);

    devBtn.appendChild(devIcon);
    devBtn.appendChild(devText);
    devBtn.appendChild(devArrow);
    grid.appendChild(devBtn);
}

/**
 * Generate a simple fingerprint from payload_map for comparison.
 * Extracts id + versions data from the current in-memory payload_map.
 * @returns {string} JSON fingerprint of [{ id, versions: [{version, hash}] }]
 */
function generatePayloadFingerprint() {
    var fingerprint = [];
    for (var i = 0; i < payload_map.length; i++) {
        var p = payload_map[i];
        var versionInfo = [];
        if (p.versions) {
            for (var j = 0; j < p.versions.length; j++) {
                var v = p.versions[j];
                versionInfo.push({ version: v.version, hash: v.hash });
            }
        }
        fingerprint.push({ id: p.id, versions: versionInfo });
    }
    return JSON.stringify(fingerprint);
}

/**
 * Extract a simple fingerprint from the fetched payload_map.js text.
 * Uses position-based token extraction: finds all id: tokens, splits the text
 * into per-payload blocks, then extracts version+hash pairs from each block.
 * This avoids fragile regex matching against nested braces/brackets.
 * @param {string} text - The fetched payload_map.js file content
 * @returns {string} JSON fingerprint of [{ id, versions: [{version, hash}] }]
 */
function extractFingerprintFromText(text) {
    var fingerprint = [];

    // Step 1: Find all id: "xxx" occurrences with their positions.
    // In payload_map.js, "id:" is unique to each payload entry (authors use "name:").
    var idPattern = /id:\s*["']([^"']+)["']/g;
    var idPositions = [];
    var idMatch;
    while ((idMatch = idPattern.exec(text)) !== null) {
        idPositions.push({ id: idMatch[1], pos: idMatch.index });
    }

    // Step 2: For each payload, extract the text block between this id and the next,
    // then pull version + hash pairs from that block.
    for (var i = 0; i < idPositions.length; i++) {
        var startPos = idPositions[i].pos;
        var endPos = (i + 1 < idPositions.length) ? idPositions[i + 1].pos : text.length;
        var block = text.substring(startPos, endPos);

        var versionInfo = [];
        // version: always appears before hash: in each version object, and
        // [\s\S]*? (non-greedy) ensures we pair each version with its own hash.
        var versionPattern = /version:\s*["']([^"']+)["'][\s\S]*?hash:\s*["']([^"']*)["']/g;
        var vMatch;
        while ((vMatch = versionPattern.exec(block)) !== null) {
            versionInfo.push({ version: vMatch[1], hash: vMatch[2] });
        }

        fingerprint.push({ id: idPositions[i].id, versions: versionInfo });
    }

    return JSON.stringify(fingerprint);
}

/**
 * Fetch the latest payload_map.js from the server and check if it matches local.
 * Uses a simple fingerprint comparison: if id + versions match, no update needed.
 */
async function refreshPayloads() {
    var refreshBtn = document.getElementById("refresh-payloads-btn");
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.classList.add("loading");
    }

    var toast = showToast("Checking for updates...", -1);

    try {
        // Build a relative URL to payload_map.js (same directory as index.html)
        var basePath = window.location.pathname.replace(/\/[^/]*$/, "");
        var updateUrl = basePath + "/payload_map.js?t=" + Date.now();

        var response = await fetch(updateUrl, { cache: "no-store" });
        if (!response.ok) {
            throw new Error("HTTP " + response.status);
        }

        var text = await response.text();

        // Generate fingerprints
        var localFingerprint = generatePayloadFingerprint();
        var remoteFingerprint = extractFingerprintFromText(text);

        if (localFingerprint === remoteFingerprint) {
            updateToastMessage(toast, "No updates available.");
        } else {
            updateToastMessage(toast, "Payloads updated. Reload the page to apply changes.");
        }

        // Auto-dismiss toast after 5 seconds
        setTimeout(function () {
            removeToast(toast);
        }, 5000);

    } catch (error) {
        updateToastMessage(toast, "Update check failed: " + error.message);
        setTimeout(function () {
            removeToast(toast);
        }, 5000);
    } finally {
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.classList.remove("loading");
        }
    }
}

// Export to global scope
window.openSettings = openSettings;
window.closeSettings = closeSettings;
window.populateSettingsGrid = populateSettingsGrid;
window.refreshPayloads = refreshPayloads;
window.preFetchSelectedPayloads = preFetchSelectedPayloads;
