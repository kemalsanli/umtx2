// @ts-check

/**
 * Post-JB payloads view.
 * Populates the payloads grid after jailbreak and dispatches payload execution.
 * Depends on: constants, settings-manager, firmware-compat
 */

/**
 * Populate the post-jailbreak payloads grid.
 * Only shows VISIBLE payloads with their selected versions.
 * Clicking a payload DISPATCHES it for execution (original behavior).
 * @param {boolean} [wkOnlyMode=false]
 */
function populatePayloadsPage(wkOnlyMode) {
    if (wkOnlyMode === undefined) wkOnlyMode = false;

    var payloadsView = document.getElementById('payloads-view');

    while (payloadsView.firstChild) {
        payloadsView.removeChild(payloadsView.firstChild);
    }

    for (var i = 0; i < payload_map.length; i++) {
        var payload = payload_map[i];

        if (wkOnlyMode && !payload.toPort && !payload.customAction) {
            continue;
        }

        // Use isFirmwareCompatible which respects dev mode bypass
        if (!isFirmwareCompatible(payload)) {
            continue;
        }

        // Skip hidden payloads - they don't show in post-JB view
        if (!isPayloadVisible(payload.id)) {
            continue;
        }

        // Resolve active version
        var versionInfo = resolveActiveVersion(payload);
        var activeVersion = versionInfo.version;
        var activeFileName = versionInfo.fileName;
        var activeFilePath = versionInfo.filePath;

        var payloadButton = document.createElement("a");
        payloadButton.classList.add("btn");
        payloadButton.classList.add("w-100");
        payloadButton.tabIndex = 0;
        payloadButton.style.position = "relative";

        var payloadTitle = document.createElement("p");
        payloadTitle.classList.add("payload-btn-title");
        payloadTitle.textContent = payload.displayTitle;

        // Inline version next to title (subtle, no floating badge)
        var fwVersion = document.createElement("span");
        fwVersion.className = "fw-version";
        fwVersion.textContent = "v" + activeVersion;
        payloadTitle.appendChild(fwVersion);

        var payloadDescription = document.createElement("p");
        payloadDescription.classList.add("payload-btn-description");
        payloadDescription.textContent = payload.description;

        var payloadInfo = document.createElement("p");
        payloadInfo.classList.add("payload-btn-info");
        payloadInfo.textContent = payload.author;

        payloadButton.appendChild(payloadTitle);
        payloadButton.appendChild(payloadDescription);
        payloadButton.appendChild(payloadInfo);

        // Click → DISPATCH PAYLOAD FOR EXECUTION (original behavior)
        // Use IIFE to capture variables in closure
        (function (p, ver, fn, fp) {
            payloadButton.addEventListener("click", function () {
                // Create a copy with resolved version/fileName/filePath for dispatch
                var resolvedPayload = {};
                for (var key in p) {
                    resolvedPayload[key] = p[key];
                }
                resolvedPayload.version = ver;
                resolvedPayload.fileName = fn;
                resolvedPayload.filePath = fp;
                window.dispatchEvent(new CustomEvent(MAINLOOP_EXECUTE_PAYLOAD_REQUEST, { detail: resolvedPayload }));
            });
        })(payload, activeVersion, activeFileName, activeFilePath);

        payloadsView.appendChild(payloadButton);
    }
}

// Export to global scope
window.populatePayloadsPage = populatePayloadsPage;
