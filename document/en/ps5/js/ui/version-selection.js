// @ts-check

/**
 * Version selection view.
 * Shows version cards for a payload in SETTINGS mode.
 * Depends on: constants, settings-manager, firmware-compat,
 *             toast-notifications, page-switcher, settings-view
 */

/**
 * Show the version selection page for a payload in SETTINGS mode.
 * This is a sub-screen of settings. Selecting a version returns to settings.
 * Includes a "Hide/Show Payload" toggle.
 * @param {Object} payload - The payload object from payload_map
 */
async function showSettingsVersionPage(payload) {
    var versionView = document.getElementById('version-selection-view');

    // Clear previous content
    while (versionView.firstChild) {
        versionView.removeChild(versionView.firstChild);
    }

    // --- Header ---
    var header = document.createElement("div");
    header.className = "version-selection-header";

    // Back button → returns to settings view
    var backBtn = document.createElement("button");
    backBtn.className = "version-back-btn";
    backBtn.tabIndex = 0;
    backBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"></path></svg> Back';
    backBtn.addEventListener("click", async function () {
        populateSettingsGrid();
        await switchPage("settings-view");
    });

    // Hide/Show toggle
    var visible = isPayloadVisible(payload.id);
    var toggleBtn = document.createElement("button");
    toggleBtn.className = "version-toggle-btn" + (visible ? "" : " hidden-state");
    toggleBtn.tabIndex = 0;
    toggleBtn.textContent = visible ? "Hide Payload" : "Show Payload";
    toggleBtn.addEventListener("click", function () {
        var currentlyVisible = isPayloadVisible(payload.id);
        setPayloadVisible(payload.id, !currentlyVisible);
        if (!currentlyVisible) {
            toggleBtn.textContent = "Hide Payload";
            toggleBtn.classList.remove("hidden-state");
            showToast(payload.displayTitle + " is now visible", TOAST_SUCCESS_TIMEOUT);
        } else {
            toggleBtn.textContent = "Show Payload";
            toggleBtn.classList.add("hidden-state");
            showToast(payload.displayTitle + " is now hidden", TOAST_SUCCESS_TIMEOUT);
        }
    });

    header.appendChild(backBtn);

    // Payload info (name + description) between back button and toggle
    var payloadInfoContainer = document.createElement("div");
    payloadInfoContainer.className = "version-header-info";

    var payloadName = document.createElement("span");
    payloadName.className = "version-header-title";
    payloadName.textContent = payload.displayTitle || "";
    payloadInfoContainer.appendChild(payloadName);

    if (payload.description) {
        var payloadDesc = document.createElement("span");
        payloadDesc.className = "version-header-description";
        payloadDesc.textContent = payload.description;
        payloadInfoContainer.appendChild(payloadDesc);
    }

    header.appendChild(payloadInfoContainer);
    header.appendChild(toggleBtn);
    versionView.appendChild(header);

    // --- Version Grid ---
    var grid = document.createElement("div");
    grid.className = "version-selection-grid";

    var currentSelectedVersion = getSelectedVersion(payload.id);

    // Check firmware compatibility for this payload
    var isPayloadFwCompatible = isFirmwareCompatible(payload);
    var currentFw = window.fw_str || "";

    if (payload.versions && payload.versions.length > 0) {
        // If the payload itself is incompatible, show warning
        if (!isPayloadFwCompatible && !window.devOptions.bypassFirmware) {
            var warningDiv = document.createElement("div");
            warningDiv.className = "fw-incompatible-warning";
            warningDiv.innerHTML = '<p>All versions are incompatible with your firmware (' + currentFw + '). This payload is hidden from the launch menu.</p><p class="fw-incompatible-sub">Enable "Bypass Firmware Compatibility" in Developer Options to override.</p>';
            grid.appendChild(warningDiv);
        }

        for (var vi = 0; vi < payload.versions.length; vi++) {
            var ver = payload.versions[vi];

            // Skip pre-release versions unless dev option enabled
            if (ver.isPreRelease && !window.devOptions.showPreRelease) {
                continue;
            }

            var card = document.createElement("div");
            card.className = "version-card";
            if (!isPayloadFwCompatible) {
                card.classList.add("version-card-incompatible");
            }
            card.tabIndex = 0;

            // Card header
            var cardHeader = document.createElement("div");
            cardHeader.className = "version-card-header";

            var cardTitle = document.createElement("p");
            cardTitle.className = "version-card-title";
            cardTitle.textContent = "v" + ver.version;
            cardHeader.appendChild(cardTitle);

            // Badge container for version card
            var cardBadges = document.createElement("div");
            cardBadges.style.display = "flex";
            cardBadges.style.gap = "0.3rem";
            cardBadges.style.alignItems = "center";

            // Firmware incompatibility badge
            if (!isPayloadFwCompatible) {
                var incompatBadge = document.createElement("span");
                incompatBadge.className = "version-card-incompat-badge";
                incompatBadge.textContent = "Incompatible with FW " + currentFw;
                cardBadges.appendChild(incompatBadge);
            }

            // Pre-release badge
            if (ver.isPreRelease) {
                var preReleaseBadge = document.createElement("span");
                preReleaseBadge.className = "prerelease-badge";
                preReleaseBadge.textContent = "Pre-release";
                cardBadges.appendChild(preReleaseBadge);
            }

            // Cached (offline) badge for default versions
            if (ver.isDefault === true) {
                var cachedBadge = document.createElement('span');
                cachedBadge.className = 'version-card-cached-badge';
                cachedBadge.textContent = 'Cached';
                cachedBadge.title = 'Available offline (in AppCache)';
                cardBadges.appendChild(cachedBadge);
            } else {
                // Non-default versions require network
                var onlineBadge = document.createElement('span');
                onlineBadge.className = 'version-card-online-badge';
                onlineBadge.textContent = 'Online Required';
                onlineBadge.title = 'This version is not in AppCache and requires network';
                cardBadges.appendChild(onlineBadge);
            }

            // Check if this version is currently selected
            var isSelected = currentSelectedVersion === ver.version ||
                (!currentSelectedVersion && ver.isDefault);
            if (isSelected) {
                var selectedBadge = document.createElement("span");
                selectedBadge.className = "version-card-selected";
                selectedBadge.textContent = "Selected";
                cardBadges.appendChild(selectedBadge);
            }

            cardHeader.appendChild(cardBadges);
            card.appendChild(cardHeader);

            // Release date
            if (ver.releaseDate) {
                var dateEl = document.createElement("p");
                dateEl.className = "version-card-date";
                dateEl.textContent = ver.releaseDate;
                card.appendChild(dateEl);
            }

            // Pre-release warning in changelog
            if (ver.isPreRelease) {
                var prereleaseWarning = document.createElement("div");
                prereleaseWarning.className = "prerelease-warning";
                prereleaseWarning.textContent = "This is a pre-release version and may be unstable.";
                card.appendChild(prereleaseWarning);
            }

            // Changelog
            if (ver.changelog && ver.changelog.length > 0) {
                var changelogSection = document.createElement("div");
                changelogSection.className = "version-card-changelog";

                var changelogTitle = document.createElement("p");
                changelogTitle.className = "version-card-changelog-title";
                changelogTitle.textContent = "Changelog:";
                changelogSection.appendChild(changelogTitle);

                var changelogList = document.createElement("ul");
                changelogList.className = "version-card-changelog-list";

                for (var ci = 0; ci < ver.changelog.length; ci++) {
                    var li = document.createElement("li");
                    li.className = "version-card-changelog-item";
                    li.textContent = ver.changelog[ci];
                    changelogList.appendChild(li);
                }

                changelogSection.appendChild(changelogList);
                card.appendChild(changelogSection);
            }

            // Select button
            var selectBtn = document.createElement("button");
            selectBtn.className = "version-card-select-btn";
            selectBtn.tabIndex = 0;
            selectBtn.textContent = isSelected ? "Selected" : "Select";

            // Disable select for incompatible versions
            if (!isPayloadFwCompatible) {
                selectBtn.classList.add("version-card-select-btn-disabled");
                selectBtn.textContent = "Incompatible";
            } else if (isSelected) {
                selectBtn.style.backgroundColor = "rgba(76, 175, 80, 0.2)";
                selectBtn.style.color = "#4CAF50";
            }

            // Use IIFE to capture ver in closure
            (function (currentVer, compatible) {
                if (compatible) {
                    selectBtn.addEventListener("click", async function (e) {
                        e.stopPropagation();
                        setSelectedVersion(payload.id, currentVer.version);
                        showToast(payload.displayTitle + " - v" + currentVer.version + " selected", TOAST_SUCCESS_TIMEOUT);
                        // Return to settings view
                        populateSettingsGrid();
                        await switchPage("settings-view");
                    });
                } else {
                    // Prevent selection of incompatible version
                    selectBtn.addEventListener("click", function (e) {
                        e.stopPropagation();
                        showToast("This payload is incompatible with your firmware", TOAST_ERROR_TIMEOUT);
                    });
                }
            })(ver, isPayloadFwCompatible);

            card.appendChild(selectBtn);

            // Clicking the card itself selects version and returns to settings
            (function (currentVer, compatible) {
                if (compatible) {
                    card.addEventListener("click", async function () {
                        setSelectedVersion(payload.id, currentVer.version);
                        showToast(payload.displayTitle + " - v" + currentVer.version + " selected", TOAST_SUCCESS_TIMEOUT);
                        populateSettingsGrid();
                        await switchPage("settings-view");
                    });
                } else {
                    card.addEventListener("click", function (e) {
                        e.preventDefault();
                        showToast("This payload is incompatible with your firmware", TOAST_ERROR_TIMEOUT);
                    });
                }
            })(ver, isPayloadFwCompatible);

            grid.appendChild(card);
        }
    } else {
        // No versions available
        var noVersions = document.createElement("p");
        noVersions.style.color = "var(--text-color-tertiary)";
        noVersions.style.padding = "2rem";
        noVersions.style.gridColumn = "span 2";
        noVersions.style.textAlign = "center";
        noVersions.textContent = "No version information available for this payload.";
        grid.appendChild(noVersions);
    }

    versionView.appendChild(grid);

    // Switch to version selection view
    await switchPage("version-selection-view");
}

// Export to global scope
window.showSettingsVersionPage = showSettingsVersionPage;
