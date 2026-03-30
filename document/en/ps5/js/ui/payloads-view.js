// @ts-check

/**
 * Post-JB payloads view.
 * Populates the payloads grid after jailbreak and dispatches payload execution.
 * Version selection is done in Settings, not here - this view only displays the selected version.
 * Depends on: constants, settings-manager, firmware-compat, toast-notifications
 */

/**
 * Populate the post-jailbreak payloads grid.
 * Only shows VISIBLE payloads with their selected versions.
 * Clicking a payload DISPATCHES it for execution (original behavior).
 * Version selection is done in Settings - here we only show the selected version.
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

        // Skip payloads marked as willHideEveryTime - never show in UI under any circumstance
        if (payload.willHideEveryTime) {
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

        // Always show selected version as inline text badge
        // Version selection is done in Settings, not here
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

        // Store active version as data attributes for dispatch
        payloadButton.setAttribute("data-active-version", activeVersion);
        payloadButton.setAttribute("data-active-filename", activeFileName);
        payloadButton.setAttribute("data-active-filepath", activeFilePath);

        // Click → DISPATCH PAYLOAD FOR EXECUTION (original behavior)
        // Read the currently active version from data attributes (may have been changed by dropdown)
        (function (p) {
            payloadButton.addEventListener("click", function () {
                var btn = this;
                var resolvedVer = btn.getAttribute("data-active-version") || activeVersion;
                var resolvedFn = btn.getAttribute("data-active-filename") || activeFileName;
                var resolvedFp = btn.getAttribute("data-active-filepath") || activeFilePath;

                // Create a copy with resolved version/fileName/filePath for dispatch
                var resolvedPayload = {};
                for (var key in p) {
                    resolvedPayload[key] = p[key];
                }
                resolvedPayload.version = resolvedVer;
                resolvedPayload.fileName = resolvedFn;
                resolvedPayload.filePath = resolvedFp;
                window.dispatchEvent(new CustomEvent(MAINLOOP_EXECUTE_PAYLOAD_REQUEST, { detail: resolvedPayload }));
            });
        })(payload);

        payloadsView.appendChild(payloadButton);
    }
}

// Export to global scope
window.populatePayloadsPage = populatePayloadsPage;
