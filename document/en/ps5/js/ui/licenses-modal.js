// @ts-check

/**
 * Licenses modal.
 * Depends on: constants (payload_map is global from payload_map.js)
 */

/**
 * Open the licenses modal.
 */
function openLicenses() {
    var modal = document.getElementById('licenses-modal');
    if (modal) {
        populateLicensesContent();
        modal.classList.add('show');
    }
}

/**
 * Close the licenses modal.
 */
function closeLicenses() {
    var modal = document.getElementById('licenses-modal');
    if (modal) {
        modal.classList.remove('show');
    }
}

/**
 * Switch between licenses tabs.
 * @param {string} tab - 'payloads' or 'tools'
 */
function switchLicenseTab(tab) {
    // Update tab buttons
    var tabs = document.querySelectorAll('.modal-tab');
    for (var i = 0; i < tabs.length; i++) {
        if ((tab === 'payloads' && i === 0) || (tab === 'tools' && i === 1)) {
            tabs[i].classList.add('active');
        } else {
            tabs[i].classList.remove('active');
        }
    }

    // Update content
    var payloadsTab = document.getElementById('licenses-payloads-tab');
    var toolsTab = document.getElementById('licenses-tools-tab');

    if (tab === 'payloads') {
        payloadsTab.classList.add('active');
        toolsTab.classList.remove('active');
    } else {
        payloadsTab.classList.remove('active');
        toolsTab.classList.add('active');
    }
}

/**
 * Populate the licenses modal content.
 */
function populateLicensesContent() {
    // Populate Payloads tab
    var payloadsTab = document.getElementById('licenses-payloads-tab');
    if (payloadsTab) {
        payloadsTab.innerHTML = '';

        for (var i = 0; i < payload_map.length; i++) {
            var payload = payload_map[i];
            var licenseCard = document.createElement('div');
            licenseCard.className = 'license-card';

            var cardHeader = document.createElement('div');
            cardHeader.className = 'license-card-header';

            var cardTitle = document.createElement('h3');
            cardTitle.className = 'license-card-title';
            cardTitle.textContent = payload.displayTitle;
            cardHeader.appendChild(cardTitle);

            if (payload.projectUrl) {
                var projectLink = document.createElement('a');
                projectLink.className = 'license-card-link';
                projectLink.href = payload.projectUrl;
                projectLink.target = '_blank';
                projectLink.textContent = 'View Project';
                cardHeader.appendChild(projectLink);
            }

            licenseCard.appendChild(cardHeader);

            // Authors
            var authorsSection = document.createElement('div');
            authorsSection.className = 'license-card-section';

            var authorsLabel = document.createElement('span');
            authorsLabel.className = 'license-card-label';
            authorsLabel.textContent = 'Authors: ';
            authorsSection.appendChild(authorsLabel);

            var authorsValue = document.createElement('span');
            authorsValue.className = 'license-card-value';
            authorsValue.textContent = payload.author || 'Unknown';
            authorsSection.appendChild(authorsValue);

            licenseCard.appendChild(authorsSection);

            // License
            var licenseSection = document.createElement('div');
            licenseSection.className = 'license-card-section';

            var licenseLabel = document.createElement('span');
            licenseLabel.className = 'license-card-label';
            licenseLabel.textContent = 'License: ';
            licenseSection.appendChild(licenseLabel);

            var licenseValue = document.createElement('span');
            licenseValue.className = 'license-card-value';
            var licenseType = (payload.license && payload.license.type) ? payload.license.type : 'Unknown';
            licenseValue.textContent = licenseType;
            licenseSection.appendChild(licenseValue);

            if (payload.license && payload.license.url) {
                var licenseLink = document.createElement('a');
                licenseLink.href = payload.license.url;
                licenseLink.target = '_blank';
                licenseLink.className = 'license-card-link small';
                licenseLink.textContent = 'View License';
                licenseSection.appendChild(licenseLink);
            }

            licenseCard.appendChild(licenseSection);

            payloadsTab.appendChild(licenseCard);
        }
    }

    // Populate Tools & Resources tab
    var toolsTab = document.getElementById('licenses-tools-tab');
    if (toolsTab) {
        toolsTab.innerHTML = '';

        var tools = [
            {
                name: 'UMTX2 (Upstream)',
                description: 'Original PS5 jailbreak host by idlesauce — This project is a customized fork with enhanced features.',
                license: 'BSD',
                url: 'https://github.com/idlesauce/umtx2',
                author: 'idlesauce',
                authorUrl: 'https://github.com/idlesauce'
            },
            {
                name: 'PSFree',
                description: 'WebKit exploit for PS5',
                license: 'GPLv3',
                url: 'https://github.com/obhq/psfree'
            },
            {
                name: 'UMTX2 Exploit',
                description: 'Kernel exploit for PS5',
                license: 'BSD',
                url: 'https://github.com/idlesauce/umtx2'
            },
            {
                name: 'ROP Framework',
                description: 'Return-oriented programming utilities',
                license: 'Custom',
                url: ''
            },
            {
                name: 'int64.js',
                description: '64-bit integer arithmetic library',
                license: 'Custom',
                url: ''
            },
            {
                name: 'AppCache System',
                description: 'Offline caching and auto-update system',
                license: 'Custom',
                url: ''
            }
        ];

        for (var j = 0; j < tools.length; j++) {
            var tool = tools[j];
            var toolCard = document.createElement('div');
            toolCard.className = 'license-card';

            var toolCardHeader = document.createElement('div');
            toolCardHeader.className = 'license-card-header';

            var toolCardTitle = document.createElement('h3');
            toolCardTitle.className = 'license-card-title';
            toolCardTitle.textContent = tool.name;
            toolCardHeader.appendChild(toolCardTitle);

            if (tool.url) {
                var toolProjectLink = document.createElement('a');
                toolProjectLink.className = 'license-card-link';
                toolProjectLink.href = tool.url;
                toolProjectLink.target = '_blank';
                toolProjectLink.textContent = 'View Project';
                toolCardHeader.appendChild(toolProjectLink);
            }

            toolCard.appendChild(toolCardHeader);

            // Author (if present)
            if (tool.author) {
                var authorSection = document.createElement('div');
                authorSection.className = 'license-card-section';

                var authorLabel = document.createElement('span');
                authorLabel.className = 'license-card-label';
                authorLabel.textContent = 'Author: ';
                authorSection.appendChild(authorLabel);

                if (tool.authorUrl) {
                    var authorLink = document.createElement('a');
                    authorLink.href = tool.authorUrl;
                    authorLink.target = '_blank';
                    authorLink.className = 'license-card-value';
                    authorLink.textContent = tool.author;
                    authorSection.appendChild(authorLink);
                } else {
                    var authorValue = document.createElement('span');
                    authorValue.className = 'license-card-value';
                    authorValue.textContent = tool.author;
                    authorSection.appendChild(authorValue);
                }

                toolCard.appendChild(authorSection);
            }

            // Description
            var descSection = document.createElement('div');
            descSection.className = 'license-card-section';

            var descValue = document.createElement('span');
            descValue.className = 'license-card-value';
            descValue.textContent = tool.description;
            descSection.appendChild(descValue);

            toolCard.appendChild(descSection);

            // License
            var toolLicenseSection = document.createElement('div');
            toolLicenseSection.className = 'license-card-section';

            var toolLicenseLabel = document.createElement('span');
            toolLicenseLabel.className = 'license-card-label';
            toolLicenseLabel.textContent = 'License: ';
            toolLicenseSection.appendChild(toolLicenseLabel);

            var toolLicenseValue = document.createElement('span');
            toolLicenseValue.className = 'license-card-value';
            toolLicenseValue.textContent = tool.license;
            toolLicenseSection.appendChild(toolLicenseValue);

            toolCard.appendChild(toolLicenseSection);

            toolsTab.appendChild(toolCard);
        }
    }
}

// Export to global scope
window.openLicenses = openLicenses;
window.closeLicenses = closeLicenses;
window.switchLicenseTab = switchLicenseTab;
window.populateLicensesContent = populateLicensesContent;
