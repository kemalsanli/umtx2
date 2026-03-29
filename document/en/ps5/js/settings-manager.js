// @ts-check

/**
 * Payload visibility settings (payloadId → boolean).
 * @type {Object<string, boolean>}
 */
let payloadVisibility = {};

/**
 * Payload version overrides (payloadId → versionString).
 * @type {Object<string, string>}
 */
let payloadVersions = {};

/**
 * Load settings from localStorage.
 */
function loadSettings() {
    try {
        const visibility = localStorage.getItem(window.SETTINGS_PAYLOAD_VISIBILITY);
        const versions = localStorage.getItem(window.SETTINGS_PAYLOAD_VERSIONS);
        payloadVisibility = visibility ? JSON.parse(visibility) : {};
        payloadVersions = versions ? JSON.parse(versions) : {};
    } catch (e) {
        console.error("Error loading settings:", e);
        payloadVisibility = {};
        payloadVersions = {};
    }
}

/**
 * Save settings to localStorage.
 */
function saveSettings() {
    try {
        localStorage.setItem(window.SETTINGS_PAYLOAD_VISIBILITY, JSON.stringify(payloadVisibility));
        localStorage.setItem(window.SETTINGS_PAYLOAD_VERSIONS, JSON.stringify(payloadVersions));
    } catch (e) {
        console.error("Error saving settings:", e);
    }
}

/**
 * Check if a payload is visible.
 * Developer mode override allows showing all payloads.
 * @param {string} payloadId
 * @returns {boolean}
 */
function isPayloadVisible(payloadId) {
    if (window.devOptions.showAllPayloads) {
        return true;
    }
    return payloadVisibility[payloadId] !== false;
}

/**
 * Set payload visibility.
 * @param {string} payloadId
 * @param {boolean} visible
 */
function setPayloadVisible(payloadId, visible) {
    payloadVisibility[payloadId] = visible;
    saveSettings();
}

/**
 * Get selected version for a payload.
 * @param {string} payloadId
 * @returns {string|null}
 */
function getSelectedVersion(payloadId) {
    return payloadVersions[payloadId] || null;
}

/**
 * Set selected version for a payload.
 * @param {string} payloadId
 * @param {string} version
 */
function setSelectedVersion(payloadId, version) {
    if (version) {
        payloadVersions[payloadId] = version;
    } else {
        // Clear stale selection by removing the key entirely
        delete payloadVersions[payloadId];
    }
    saveSettings();
}

/**
 * Resolve the active version info for a payload.
 * Returns filePath (new v2 format) with fallback to fileName (legacy).
 * @param {Object} payload
 * @returns {{version: string, fileName: string, filePath: string}}
 */
function resolveActiveVersion(payload) {
    if (payload.versions && payload.versions.length > 0) {
        const selectedVer = getSelectedVersion(payload.id);
        let verData = null;

        if (selectedVer) {
            verData = payload.versions.find(v => v.version === selectedVer);
        }

        if (!verData) {
            verData = payload.versions.find(v => v.isDefault) || payload.versions[0];
        }

        if (verData) {
            // v2 format: use filePath; fallback to "payloads/" + fileName for legacy
            const filePath = verData.filePath || ("payloads/" + verData.fileName);
            return {
                version: verData.version,
                fileName: verData.fileName,
                filePath: filePath
            };
        }
    }

    // Legacy fallback (should not happen with v2 payload_map.js)
    return {
        version: payload.version || "",
        fileName: payload.fileName || "",
        filePath: payload.fileName ? ("payloads/" + payload.fileName) : ""
    };
}

/**
 * Get all cached/selected payload file paths for AppCache optimization.
 * Returns an array of filePaths that should be included in the AppCache manifest.
 * @returns {string[]}
 */
function getCachedPayloads() {
    const cachedPaths = [];

    for (const payload of window.payload_map) {
        const { filePath } = resolveActiveVersion(payload);
        if (filePath) {
            cachedPaths.push(filePath);
        }
    }

    return cachedPaths;
}

// Export to global scope
window.loadSettings = loadSettings;
window.saveSettings = saveSettings;
window.isPayloadVisible = isPayloadVisible;
window.setPayloadVisible = setPayloadVisible;
window.getSelectedVersion = getSelectedVersion;
window.setSelectedVersion = setSelectedVersion;
window.resolveActiveVersion = resolveActiveVersion;
window.getCachedPayloads = getCachedPayloads;

// Load settings on script init
loadSettings();
