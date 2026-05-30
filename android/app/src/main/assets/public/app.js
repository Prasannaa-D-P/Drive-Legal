// DriveLegal Main Application Controller
// Orchestrates theme switching, tab routing, geofencing queries, directory renders, and offline triggers.

// Global instances
let chatbot;
let calculator;
let radar;

// Page Lifecycle Initialization
document.addEventListener('DOMContentLoaded', async () => {
  // Theme initialization
  initTheme();

  // Chatbot initialization
  chatbot = new TrafficLegalChatbot('chatMessagesContainer', 'chatInputField');
  chatbot.initWelcome();

  // Sync rules database from backend SQLite on load
  await syncDatabaseRules();

  // Calculator initialization
  calculator = new ChallanCalculator();
  calculator.initSelectors();
  calculator.renderViolations();
  calculator.renderReceipt();

  // Radar canvas initialization
  radar = new JurisdictionRadar('radarCanvas');
  radar.setJurisdictionPoints('delhi'); // Default
  updateRadarInfoPanels('delhi'); // Pre-populate sidebar with Delhi data
  
  // Directory rendering
  initDirectory();

  // Network offline status event listeners
  window.addEventListener('online', updateNetworkStatus);
  window.addEventListener('offline', updateNetworkStatus);
  updateNetworkStatus(); // Run check on load

  // Register PWA service worker
  registerServiceWorker();
});

// --- THEME MANAGEMENT ---
function initTheme() {
  const savedTheme = localStorage.getItem('drivelegal_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('drivelegal_theme', newTheme);
  updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
  const icon = document.getElementById('themeIcon');
  if (icon) {
    if (theme === 'light') {
      icon.className = 'fa-solid fa-sun';
    } else {
      icon.className = 'fa-solid fa-moon';
    }
  }
}

// --- NETWORK OFFLINE / ONLINE STATUS ---
function updateNetworkStatus() {
  const indicator = document.getElementById('offlineIndicator');
  const text = document.getElementById('offlineIndicatorText');
  
  if (!indicator || !text) return;

  if (navigator.onLine) {
    indicator.className = 'offline-indicator online-state';
    text.textContent = 'Online';
    indicator.setAttribute('title', 'Network connected');
  } else {
    indicator.className = 'offline-indicator offline-state';
    text.textContent = 'Offline Mode';
    indicator.setAttribute('title', 'Offline - Running on local database');
    
    // Add chatbot message notifying offline functionality
    if (chatbot && chatbot.history.length === 0) {
       chatbot.appendMessage("bot", "<i class='fa-solid fa-wifi'></i> <strong>Offline Mode Activated.</strong> All traffic databases and calculator compounding matrices are loaded locally and are 100% operational.");
    }
  }
}

// --- TAB ROUTING SYSTEM ---
function switchTab(tabId) {
  // Hide all tab panels
  const contentTabs = ['chatbot', 'calculator', 'radar', 'directory'];
  contentTabs.forEach(id => {
    const content = document.getElementById(`tabContent${id.charAt(0).toUpperCase() + id.slice(1)}`);
    const btn = document.getElementById(`tabBtn${id.charAt(0).toUpperCase() + id.slice(1)}`);
    if (content) content.classList.remove('active');
    if (btn) btn.classList.remove('active');
  });

  // Activate target
  const activeContent = document.getElementById(`tabContent${tabId.charAt(0).toUpperCase() + tabId.slice(1)}`);
  const activeBtn = document.getElementById(`tabBtn${tabId.charAt(0).toUpperCase() + tabId.slice(1)}`);
  
  if (activeContent) activeContent.classList.add('active');
  if (activeBtn) activeBtn.classList.add('active');

  // Specific tab entry hooks
  if (tabId === 'radar') {
    radar.start();
    // Update radar coordinates to match selected calculator state
    radar.setJurisdictionPoints(calculator.selectedState);
    updateRadarInfoPanels(calculator.selectedState);
  } else {
    radar.stop();
  }

  if (tabId === 'calculator') {
    calculator.renderViolations();
    calculator.renderReceipt();
  }
}

// --- CHAT INTERACTIVE UTILITIES ---
function sendSuggestion(text) {
  const input = document.getElementById('chatInputField');
  if (input) {
    input.value = text;
    handleUserMessageSubmit();
  }
}

function handleUserMessageSubmit() {
  const input = document.getElementById('chatInputField');
  if (input && chatbot) {
    const text = input.value;
    chatbot.handleMessage(text);
    input.value = "";
  }
}

function toggleVoiceInput() {
  if (chatbot) chatbot.toggleVoice();
}

function clearChat() {
  const container = document.getElementById('chatMessagesContainer');
  if (container && chatbot) {
    container.innerHTML = "";
    chatbot.history = [];
    chatbot.initWelcome();
  }
}

// Bridging mechanism from chatbot suggestions straight to active challan receipt
function injectIntoCalculator(stateKey, vehicleKey, violationId) {
  // Switch view
  switchTab('calculator');
  
  // Set parameters
  calculator.selectedState = stateKey;
  calculator.selectedVehicle = vehicleKey;
  calculator.selectedViolations.add(violationId);

  // Sync Selectors UI
  document.getElementById('stateSelector').value = stateKey;
  document.getElementById('vehicleTypeSelector').value = vehicleKey;

  // Refresh
  calculator.renderViolations();
  calculator.renderReceipt();

  // Scroll receipt into view if on mobile/small screen
  const receipt = document.getElementById('receiptPanelContainer');
  if (receipt) {
    receipt.scrollIntoView({ behavior: 'smooth' });
  }
}

// --- CHALLAN CALCULATOR INPUT LISTENERS ---
function handleCalculatorStateOrVehicleChange() {
  if (!calculator) return;
  
  const stateVal = document.getElementById('stateSelector').value;
  const vehicleVal = document.getElementById('vehicleTypeSelector').value;
  
  calculator.selectedState = stateVal;
  calculator.selectedVehicle = vehicleVal;
  
  calculator.renderViolations();
  calculator.renderReceipt();
}

function filterViolations() {
  if (!calculator) return;
  const val = document.getElementById('violationSearchField').value;
  calculator.searchQuery = val;
  calculator.renderViolations();
}

function toggleRepeatOffenseMultiplier() {
  if (!calculator) return;
  const checked = document.getElementById('repeatOffenseToggle').checked;
  calculator.repeatOffense = checked;
  calculator.renderViolations();
  calculator.renderReceipt();
}

function resetCalculatorReceipt() {
  if (calculator) calculator.resetCalculatorReceipt();
}

function printOrSaveReceipt() {
  if (calculator) calculator.printOrSaveReceipt();
}

// --- GEO-FENCING SIMULATOR ACTIONS ---
function triggerGeofencedLocate() {
  if (!navigator.geolocation) {
    triggerGeofencedLocateSim("delhi");
    return;
  }

  const locateBtn = document.getElementById('geoLocateBtn');
  locateBtn.innerHTML = "<i class='fa-solid fa-spinner fa-spin'></i> Scanning GPS...";
  locateBtn.disabled = true;

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;
      
      document.getElementById('gpsLatitudeText').textContent = lat.toFixed(4);
      document.getElementById('gpsLongitudeText').textContent = lng.toFixed(4);
      
      let matchedStateKey = "delhi"; // fallback
      
      try {
        const response = await fetch('/api/geo/check', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ latitude: lat, longitude: lng })
        });
        if (response.ok) {
          const geoData = await response.json();
          matchedStateKey = geoData.state_code;
          console.log(`[Radar] Geofence matched state: ${geoData.state_name} via backend.`);
        } else {
          throw new Error('API return status not OK');
        }
      } catch (err) {
        console.warn("Geofence API failed, fallback to local geofencing logic", err);
        // Fallback geofencing check
        for (const [key, state] of Object.entries(DRIVELEGAL_DATA.states)) {
          const fence = state.geofence;
          if (lat >= fence.latMin && lat <= fence.latMax && lng >= fence.lngMin && lng <= fence.lngMax) {
            matchedStateKey = key;
            break;
          }
        }
      }
      
      // Sync radar sweep points and panels
      radar.setJurisdictionPoints(matchedStateKey);
      updateRadarInfoPanels(matchedStateKey);
      
      // Select state in calculator
      calculator.selectedState = matchedStateKey;
      document.getElementById('stateSelector').value = matchedStateKey;
      
      locateBtn.innerHTML = "<i class='fa-solid fa-location-arrow'></i> Detect Location";
      locateBtn.disabled = false;
    },
    (error) => {
      console.warn("Geolocation failed. Running simulated location scan:", error);
      // Run random simulation for Demonstration
      const states = Object.keys(DRIVELEGAL_DATA.states);
      const randomState = states[Math.floor(Math.random() * states.length)];
      triggerGeofencedLocateSim(randomState);
    },
    { timeout: 5000 }
  );
}

// Simulated GPS scanning for geofencing demo
function triggerGeofencedLocateSim(stateKey) {
  const locateBtn = document.getElementById('geoLocateBtn');
  if (locateBtn) {
    locateBtn.innerHTML = "<i class='fa-solid fa-spinner fa-spin'></i> Mocking GPS Sweep...";
    locateBtn.disabled = true;
  }

  // Predefined mock coordinates centers of cities
  const coordinates = {
    delhi: { lat: 28.6139, lng: 77.2090 },
    karnataka: { lat: 12.9716, lng: 77.5946 },
    maharashtra: { lat: 18.9696, lng: 72.8230 },
    tamil_nadu: { lat: 13.0827, lng: 80.2707 },
    west_bengal: { lat: 22.5726, lng: 88.3639 },
    telangana: { lat: 17.3850, lng: 78.4867 }
  };

  const coords = coordinates[stateKey] || coordinates.delhi;

  setTimeout(async () => {
    document.getElementById('gpsLatitudeText').textContent = coords.lat.toFixed(4);
    document.getElementById('gpsLongitudeText').textContent = coords.lng.toFixed(4);
    
    let matchedStateKey = stateKey;
    try {
      const response = await fetch('/api/geo/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ latitude: coords.lat, longitude: coords.lng })
      });
      if (response.ok) {
        const geoData = await response.json();
        matchedStateKey = geoData.state_code;
      }
    } catch (err) {
      console.warn("Geofence API failed in simulation", err);
    }
    
    radar.setJurisdictionPoints(matchedStateKey);
    updateRadarInfoPanels(matchedStateKey);
    
    calculator.selectedState = matchedStateKey;
    document.getElementById('stateSelector').value = matchedStateKey;
    
    if (locateBtn) {
      locateBtn.innerHTML = "<i class='fa-solid fa-location-arrow'></i> Detect Location";
      locateBtn.disabled = false;
    }
  }, 1000);
}

function updateRadarInfoPanels(stateKey) {
  const stateObj = DRIVELEGAL_DATA.states[stateKey];
  if (!stateObj) return;

  // Name
  document.getElementById('radarJurisdictionNameText').textContent = stateObj.name;
  
  // Emergency contacts grid
  const contactsGrid = document.getElementById('radarEmergencyContactsGrid');
  if (contactsGrid) {
    contactsGrid.innerHTML = "";
    Object.entries(stateObj.emergency_contacts).forEach(([name, num]) => {
      const row = document.createElement('div');
      row.className = 'emergency-row';
      row.innerHTML = `
        <span>${name}</span>
        <span class="emergency-phone"><i class="fa-solid fa-phone"></i> ${num}</span>
      `;
      contactsGrid.appendChild(row);
    });
  }

  // Enforced local rules list
  const rulesList = document.getElementById('radarLocalRulesList');
  if (rulesList) {
    rulesList.innerHTML = "";
    stateObj.local_rules.forEach(rule => {
      const li = document.createElement('li');
      li.textContent = rule;
      rulesList.appendChild(li);
    });
  }
}

// --- RULES COMPENDIUM DIRECTORY ---
function initDirectory() {
  const container = document.getElementById('directoryAccordionContainer');
  if (!container) return;

  container.innerHTML = "";

  DRIVELEGAL_DATA.violations.forEach(v => {
    const item = document.createElement('div');
    item.className = 'glass-panel accordion-item';
    item.id = `directory-item-${v.id}`;
    
    // Build side-by-side state comparative table rows
    let tableRows = "";
    for (const [key, state] of Object.entries(DRIVELEGAL_DATA.states)) {
      // Find state rate overrides
      const baseFine = v.base_fines.lmv || v.base_fines.two_wheeler || v.base_fines.other || 0;
      let fine = baseFine;
      
      if (state.compounding_fees && state.compounding_fees[v.id]) {
        const overrides = state.compounding_fees[v.id];
        // Just show general or vehicle-specific baseline for representation
        fine = overrides.all !== undefined ? overrides.all : (overrides.lmv !== undefined ? overrides.lmv : (overrides.two_wheeler !== undefined ? overrides.two_wheeler : baseFine));
      }

      tableRows += `
        <tr>
          <td><strong>${state.name}</strong></td>
          <td>₹${fine.toLocaleString('en-IN')}</td>
          <td>${v.court_only ? '<span style="color:var(--accent-red)">Court Only</span>' : 'Compoundable'}</td>
        </tr>
      `;
    }

    item.innerHTML = `
      <div class="accordion-header" onclick="toggleAccordion('directory-item-${v.id}')">
        <div class="accordion-item-title-block">
          <span class="accordion-item-section-badge">${v.section}</span>
          <span class="accordion-item-title">${v.name}</span>
        </div>
        <i class="fa-solid fa-chevron-down accordion-item-arrow"></i>
      </div>
      <div class="accordion-content">
        <p><strong>Description:</strong> ${v.description}</p>
        <p style="margin-top:0.5rem;"><strong>Central Penalties:</strong> ${v.penalties}</p>
        
        <div class="directory-detail-grid">
          <div class="directory-detail-box">
            <div class="directory-detail-box-title">Vehicle Penalty Scale (MVA Baseline)</div>
            <ul style="padding-left:1rem; font-size:0.85rem; color:var(--text-muted);">
              ${Object.entries(v.base_fines).map(([vClass, amount]) => {
                if (amount === 0) return '';
                const cName = DRIVELEGAL_DATA.vehicleTypes[vClass] ? DRIVELEGAL_DATA.vehicleTypes[vClass].name : vClass;
                return `<li><strong>${cName}:</strong> ₹${amount.toLocaleString('en-IN')}</li>`;
              }).join('')}
            </ul>
          </div>
          
          <div class="directory-detail-box">
            <div class="directory-detail-box-title">State Compounding Comparison</div>
            <table class="directory-state-table">
              <thead>
                <tr>
                  <th>State</th>
                  <th>Fee Rate</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                ${tableRows}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
    
    container.appendChild(item);
  });
}

function toggleAccordion(itemId) {
  const target = document.getElementById(itemId);
  if (!target) return;
  
  const isOpen = target.classList.contains('open');
  
  // Close all other accordion items
  const items = document.querySelectorAll('.accordion-item');
  items.forEach(el => el.classList.remove('open'));

  // Toggle target
  if (!isOpen) {
    target.classList.add('open');
    
    // Fetch live state comparison details from backend if online
    const violationId = itemId.replace('directory-item-', '');
    fetchStateComparison(violationId);
  }
}

function filterDirectory() {
  const query = document.getElementById('directorySearchField').value.toLowerCase();
  const category = document.getElementById('directoryCategoryFilter').value;

  DRIVELEGAL_DATA.violations.forEach(v => {
    const item = document.getElementById(`directory-item-${v.id}`);
    if (!item) return;

    const matchesQuery = v.name.toLowerCase().includes(query) ||
                          v.section.toLowerCase().includes(query) ||
                          v.description.toLowerCase().includes(query);
                          
    const matchesCategory = category === 'all' || v.category === category;

    if (matchesQuery && matchesCategory) {
      item.style.display = "block";
    } else {
      item.style.display = "none";
    }
  });
}

// --- PWA SERVICE WORKER REGISTRATION ---
function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('sw.js')
        .then(reg => {
          console.log('ServiceWorker registered successfully with scope: ', reg.scope);
        })
        .catch(err => {
          console.warn('ServiceWorker registration failed: ', err);
        });
    });
  }
}

// --- BACKEND API SYNCHRONIZATION AND LOOKUPS ---

// Synchronize rules from SQLite DB on startup if backend is online
async function syncDatabaseRules() {
  try {
    const response = await fetch('/api/rules/');
    if (response.ok) {
      const data = await response.json();
      if (Array.isArray(data) && data.length > 0) {
        DRIVELEGAL_DATA.violations = data;
        console.log('[Sync] Successfully synced violations database with backend SQLite.');
      }
    }
  } catch (error) {
    console.warn('[Sync] Failed to fetch rules from backend. Relying on local offline JSON.', error);
  }
}

// Query vehicle registration number to pull e-challans from RTO database
async function fetchOfficialRTOChallan() {
  const field = document.getElementById('rtoVehicleSearchField');
  if (!field) return;
  const vn = field.value.trim();
  if (!vn) {
    showToast("Please enter a vehicle registration number first.", "warning");
    return;
  }

  const btn = document.getElementById('fetchRtoBtn');
  const originalText = btn.innerHTML;
  btn.innerHTML = "<i class='fa-solid fa-spinner fa-spin'></i> Querying RTO...";
  btn.disabled = true;

  try {
    const response = await fetch(`/api/challan/lookup/${encodeURIComponent(vn)}`);
    if (!response.ok) {
      throw new Error(`RTO query failed: ${response.statusText}`);
    }
    const data = await response.json();
    
    if (data.challans && data.challans.length > 0) {
      showToast(`Retrieved ${data.challans.length} active challan(s) for ${vn}`, "success");
      const vehicle = data.vehicle;
      if (vehicle) {
        calculator.selectedVehicle = vehicle.vehicle_type;
        document.getElementById('vehicleTypeSelector').value = vehicle.vehicle_type;
      }
      
      const firstChallan = data.challans[0];
      calculator.selectedState = firstChallan.state_code;
      document.getElementById('stateSelector').value = firstChallan.state_code;
      
      calculator.selectedViolations.clear();
      
      firstChallan.items.forEach(item => {
        if (item.violation_id) {
          calculator.selectedViolations.add(item.violation_id);
        }
      });
      
      calculator.renderViolations();
      calculator.renderReceipt();
      
    } else {
      showToast(`No active challans found for vehicle ${vn} in the RTO database.`, "info");
    }
  } catch (error) {
    console.error("RTO lookup failed:", error);
    showToast("RTO API is offline. Manually configure violations in the calculator.", "error");
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

// Upload file for OCR challan parsing
async function uploadChallanReceiptForOcr(file) {
  if (!file) return;

  const uploadText = document.getElementById('ocrUploadText');
  const originalText = uploadText.innerHTML;
  uploadText.innerHTML = "<i class='fa-solid fa-spinner fa-spin'></i> Running OCR parsing...";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch('/api/challan/upload-receipt', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`OCR Upload failed: ${response.statusText}`);
    }

    const data = await response.json();
    
    if (data.violations && data.violations.length > 0) {
      if (data.state_code) {
        calculator.selectedState = data.state_code;
        document.getElementById('stateSelector').value = data.state_code;
      }
      if (data.vehicle_type) {
        calculator.selectedVehicle = data.vehicle_type;
        document.getElementById('vehicleTypeSelector').value = data.vehicle_type;
      }

      data.violations.forEach(vId => {
        calculator.selectedViolations.add(vId);
      });

      calculator.renderViolations();
      calculator.renderReceipt();

      showToast(`OCR parsed! Detected: ${data.state_code.toUpperCase()} | ${data.vehicle_type.toUpperCase()} | ${data.violations.length} violation(s)`, "success");
    } else {
      showToast("OCR scan complete — no matching violations identified in document.", "info");
    }
  } catch (error) {
    console.error("OCR parse failed:", error);
    showToast("OCR API offline. Running manual calculations.", "error");
  } finally {
    uploadText.innerHTML = originalText;
  }
}

// Fetch live comparative rates from backend
async function fetchStateComparison(violationId) {
  try {
    const response = await fetch(`/api/rules/compare/${violationId}`);
    if (response.ok) {
      const data = await response.json();
      const tableBody = document.querySelector(`#directory-item-${violationId} .directory-state-table tbody`);
      if (tableBody && data.comparison) {
        let tableRows = "";
        for (const [stateKey, info] of Object.entries(data.comparison)) {
          tableRows += `
            <tr>
              <td><strong>${info.state_name}</strong></td>
              <td>₹${info.fine_rate.toLocaleString('en-IN')}</td>
              <td>${info.court_only ? '<span style="color:var(--accent-red)">Court Only</span>' : 'Compoundable'}</td>
            </tr>
          `;
        }
        tableBody.innerHTML = tableRows;
        console.log(`[Sync] Updated comparative fees for violation: ${violationId}`);
      }
    }
  } catch (error) {
    console.warn(`[Sync] Failed to fetch state comparison for ${violationId}, using static offline rates.`, error);
  }
}

// --- TOAST NOTIFICATION SYSTEM ---
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icons = { success: 'fa-circle-check', error: 'fa-circle-xmark', warning: 'fa-triangle-exclamation', info: 'fa-circle-info' };
  const icon = icons[type] || icons.info;

  toast.innerHTML = `
    <i class="fa-solid ${icon} toast-icon"></i>
    <span class="toast-msg">${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()"><i class="fa-solid fa-xmark"></i></button>
  `;

  container.appendChild(toast);

  // Auto-dismiss after 4 seconds
  setTimeout(() => {
    toast.classList.add('toast-hide');
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}

// Expose functions globally for inline HTML events
window.fetchOfficialRTOChallan = fetchOfficialRTOChallan;
window.uploadChallanReceiptForOcr = uploadChallanReceiptForOcr;
window.syncDatabaseRules = syncDatabaseRules;
window.fetchStateComparison = fetchStateComparison;
window.showToast = showToast;
