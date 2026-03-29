// @ts-check

/**
 * Page switching utilities.
 * Handles animated/instant page transitions within #main-content.
 */

/**
 * Switch to a target page within #main-content.
 * @param {string} id - The ID of the target element to switch to.
 * @param {boolean} [animate=true] - Whether to animate the transition.
 */
async function switchPage(id, animate) {
    if (animate === undefined) animate = true;

    var parentElement = document.getElementById('main-content');
    var targetElement = document.getElementById(id);
    if (!targetElement || targetElement.parentElement !== parentElement) {
        throw new Error('Invalid target element');
    }

    // Toggle jailbreak-active class on body for payloads-view
    // This allows CSS to hide/show elements like the top-right buttons
    if (id === 'payloads-view') {
        document.body.classList.add('jailbreak-active');
    } else {
        document.body.classList.remove('jailbreak-active');
    }

    var oldSelectedElement = parentElement.querySelector('.selected');

    if (oldSelectedElement) {
        if (animate) {
            var oldSelectedElementTransitionEnd = new Promise(function (resolve) {
                oldSelectedElement.addEventListener("transitionend", function handler(event) {
                    // we get back transitionend for children too but we don't want that
                    if (event.target === oldSelectedElement) {
                        oldSelectedElement.removeEventListener("transitionend", handler);
                        resolve();
                    }
                });
            });
            oldSelectedElement.classList.remove('selected');
            await oldSelectedElementTransitionEnd;
        } else {
            // override transition with none for instant switch
            oldSelectedElement.style.setProperty('transition', 'none', 'important');
            oldSelectedElement.offsetHeight;
            oldSelectedElement.classList.remove('selected');
            oldSelectedElement.offsetHeight;
            oldSelectedElement.style.removeProperty('transition');
        }
    }

    if (animate) {
        var targetElementTransitionEnd = new Promise(function (resolve) {
            targetElement.addEventListener("transitionend", function handler(event) {
                // we get back transitionend for children too but we don't want that
                if (event.target === targetElement) {
                    targetElement.removeEventListener("transitionend", handler);
                    resolve();
                }
            });
        });
        targetElement.classList.add('selected');
        await targetElementTransitionEnd;
    } else {
        // override transition with none for instant switch
        targetElement.style.setProperty('transition', 'none', 'important');
        targetElement.offsetHeight;
        targetElement.classList.add('selected');
        targetElement.offsetHeight;
        targetElement.style.removeProperty('transition');
    }
}

// Export to global scope
window.switchPage = switchPage;
