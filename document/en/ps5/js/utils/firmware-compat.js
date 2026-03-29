// @ts-check

/**
 * Check if a payload is compatible with the current firmware.
 * Developer mode bypass allows all payloads.
 * @param {Object} payload - The payload object from payload_map
 * @returns {boolean}
 */
function isFirmwareCompatible(payload) {
    // Developer mode bypass
    if (window.devOptions.bypassFirmware) {
        return true;
    }
    
    // No firmware restrictions = compatible
    if (!payload.supportedFirmwares || payload.supportedFirmwares.length === 0) {
        return true;
    }
    
    // Check if current firmware matches any supported prefix
    const currentFw = window.fw_str || "";
    return payload.supportedFirmwares.some(fwPrefix => currentFw.startsWith(fwPrefix));
}

// Export to global scope
window.isFirmwareCompatible = isFirmwareCompatible;
