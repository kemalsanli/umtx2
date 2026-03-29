// @ts-check

/**
 * Toast notification system.
 */

/**
 * Show a toast notification.
 * @param {string} message
 * @param {number} [timeout=2000] - Auto-dismiss after ms. Use -1 for persistent.
 * @returns {HTMLElement} The toast element (for updates/removal).
 */
function showToast(message, timeout = 2000) {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;

    toastContainer.appendChild(toast);

    // Trigger reflow to enable animation
    toast.offsetHeight;

    toast.classList.add('show');

    if (timeout > 0) {
        setTimeout(() => {
            removeToast(toast);
        }, timeout);
    }

    return toast;
}

/**
 * Update the message of an existing toast.
 * @param {HTMLElement} toast
 * @param {string} message
 */
function updateToastMessage(toast, message) {
    if (!toast) {
        return;
    }
    toast.textContent = message;
}

/**
 * Animate removal of a toast.
 * @param {HTMLElement} toast
 */
async function removeToast(toast) {
    if (!toast) {
        return;
    }
    toast.classList.add('hide');
    toast.addEventListener('transitionend', () => {
        toast.remove();
    });
}

// Export to global scope
window.showToast = showToast;
window.updateToastMessage = updateToastMessage;
window.removeToast = removeToast;
