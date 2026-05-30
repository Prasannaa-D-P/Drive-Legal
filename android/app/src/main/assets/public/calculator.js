// Indian Traffic Challan Calculator Logic
// Manages selected violations, state tax, repeat multipliers, legal advisories, and receipt generation.

class ChallanCalculator {
  constructor() {
    this.selectedState = "delhi";
    this.selectedVehicle = "lmv";
    this.selectedViolations = new Set(); // Stores violation IDs
    this.repeatOffense = false;
    this.searchQuery = "";
  }

  // Populate state and vehicle dropdown selectors
  initSelectors() {
    const stateSel = document.getElementById('stateSelector');
    const vehicleSel = document.getElementById('vehicleTypeSelector');
    
    if (stateSel) {
      stateSel.innerHTML = "";
      for (const [key, state] of Object.entries(DRIVELEGAL_DATA.states)) {
        const opt = document.createElement('option');
        opt.value = key;
        opt.textContent = state.name;
        stateSel.appendChild(opt);
      }
      stateSel.value = this.selectedState;
    }

    if (vehicleSel) {
      vehicleSel.innerHTML = "";
      for (const [key, vehicle] of Object.entries(DRIVELEGAL_DATA.vehicleTypes)) {
        const opt = document.createElement('option');
        opt.value = key;
        opt.textContent = vehicle.name;
        vehicleSel.appendChild(opt);
      }
      vehicleSel.value = this.selectedVehicle;
    }
  }

  // Calculate the compound fee for a single violation based on state and vehicle class
  calculateViolationFee(violation, stateKey, vehicleKey, isRepeat) {
    const stateObj = DRIVELEGAL_DATA.states[stateKey];
    const baseFine = violation.base_fines[vehicleKey] || 0;
    
    // Check if violation is applicable to this vehicle type
    if (baseFine === 0 && (violation.id === 'no_helmet' || violation.id === 'triple_riding')) {
      return 0; // Not applicable
    }

    // Get base compounding rate from state overrides
    let amount = baseFine;
    if (stateObj.compounding_fees && stateObj.compounding_fees[violation.id]) {
      const overrides = stateObj.compounding_fees[violation.id];
      amount = overrides[vehicleKey] !== undefined ? overrides[vehicleKey] : (overrides.all !== undefined ? overrides.all : baseFine);
    }

    // Apply repeat offense rule
    if (isRepeat) {
      if (violation.repeat_fines && violation.repeat_fines[vehicleKey] !== undefined) {
        amount = violation.repeat_fines[vehicleKey];
      } else {
        // If not specified, default to doubling the fine under MVA rules
        amount = amount * 2;
      }
    }

    return amount;
  }

  // Render list of available violations in left pane
  renderViolations() {
    const container = document.getElementById('violationsScrollerContainer');
    if (!container) return;

    container.innerHTML = "";

    // Group violations by category
    const categories = {};
    DRIVELEGAL_DATA.violations.forEach(v => {
      // Apply search query filter
      const matchesSearch = v.name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
                            v.section.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
                            v.description.toLowerCase().includes(this.searchQuery.toLowerCase());
      if (!matchesSearch) return;

      if (!categories[v.category]) {
        categories[v.category] = [];
      }
      categories[v.category].push(v);
    });

    const categoryKeys = Object.keys(categories);
    if (categoryKeys.length === 0) {
      container.innerHTML = `
        <div class="empty-receipt-msg">
          <i class="fa-solid fa-magnifying-glass empty-receipt-icon"></i>
          <p>No violations match your search query.</p>
        </div>
      `;
      return;
    }

    categoryKeys.forEach(categoryName => {
      const block = document.createElement('div');
      block.className = 'category-block';
      
      const title = document.createElement('h3');
      title.className = 'category-title';
      title.textContent = categoryName;
      block.appendChild(title);

      const grid = document.createElement('div');
      grid.className = 'violations-grid';

      categories[categoryName].forEach(v => {
        const fine = this.calculateViolationFee(v, this.selectedState, this.selectedVehicle, this.repeatOffense);
        const isSelected = this.selectedViolations.has(v.id);
        const isApplicable = fine > 0 || (v.base_fines[this.selectedVehicle] !== 0);

        const card = document.createElement('div');
        card.className = `glass-card violation-card ${isSelected ? 'selected' : ''} ${!isApplicable ? 'disabled-card' : ''}`;
        if (!isApplicable) {
          card.style.opacity = "0.5";
          card.style.pointerEvents = "none";
        }

        const isCourtOnly = v.court_only;

        card.innerHTML = `
          <div class="violation-card-top">
            <div>
              <span class="violation-sec">${v.section}</span>
              <h4 class="violation-heading">${v.name}</h4>
            </div>
            ${isCourtOnly ? '<span class="violation-sec" style="color:var(--accent-red); background:rgba(239,68,68,0.1); border:1px solid var(--accent-red-glow);">COURT</span>' : ''}
          </div>
          <p class="violation-desc">${v.description}</p>
          <div class="violation-card-bottom">
            <span class="violation-fine-tag">${fine > 0 ? `₹${fine.toLocaleString('en-IN')}` : 'N/A'}</span>
            <button class="violation-add-btn" onclick="calculator.toggleViolation('${v.id}')">
              ${isSelected ? '<i class="fa-solid fa-check"></i> Remove' : '<i class="fa-solid fa-plus"></i> Add'}
            </button>
          </div>
        `;

        grid.appendChild(card);
      });

      block.appendChild(grid);
      container.appendChild(block);
    });
  }

  // Toggle selection state of violation
  toggleViolation(id) {
    if (this.selectedViolations.has(id)) {
      this.selectedViolations.delete(id);
    } else {
      this.selectedViolations.add(id);
    }
    this.renderViolations();
    this.renderReceipt();
  }

  // Render receipt items on the right side
  renderReceipt() {
    const container = document.getElementById('receiptItemsContainer');
    if (!container) return;

    container.innerHTML = "";

    // Update metadata on receipt panel
    const stateObj = DRIVELEGAL_DATA.states[this.selectedState];
    const vehicleObj = DRIVELEGAL_DATA.vehicleTypes[this.selectedVehicle];
    
    document.getElementById('receiptJurisdictionText').textContent = stateObj.name;
    document.getElementById('receiptVehicleText').textContent = vehicleObj.name;

    if (this.selectedViolations.size === 0) {
      container.innerHTML = `
        <div class="empty-receipt-msg">
          <i class="fa-solid fa-receipt empty-receipt-icon"></i>
          <p>No violations selected.</p>
          <p style="font-size:0.75rem;">Select items from the list to compute compounding rates.</p>
        </div>
      `;
      
      document.getElementById('receiptBasePenaltyText').textContent = "₹0";
      document.getElementById('receiptSurchargeText').textContent = "₹0";
      document.getElementById('receiptTotalText').textContent = "₹0";
      document.getElementById('receiptLegalAdviceBox').style.display = "none";
      return;
    }

    let baseSubtotal = 0;
    let courtOnlyPresent = false;
    let licenseSuspensionTriggered = false;

    this.selectedViolations.forEach(id => {
      const v = DRIVELEGAL_DATA.violations.find(item => item.id === id);
      if (!v) return;

      const fine = this.calculateViolationFee(v, this.selectedState, this.selectedVehicle, this.repeatOffense);
      baseSubtotal += fine;

      if (v.court_only) courtOnlyPresent = true;
      
      // Certain rules trigger license suspension (helmet, triple riding, PUC, subsequent speeding)
      if (v.id === 'no_helmet' || v.id === 'triple_riding' || v.id === 'no_pucc' || (v.id === 'speeding' && this.repeatOffense)) {
        licenseSuspensionTriggered = true;
      }

      const itemCard = document.createElement('div');
      itemCard.className = 'receipt-item-card';
      itemCard.innerHTML = `
        <button class="receipt-item-remove" onclick="calculator.toggleViolation('${v.id}')"><i class="fa-solid fa-xmark"></i></button>
        <div class="receipt-item-name">${v.name}</div>
        <div class="receipt-item-meta">
          <span>${v.section}</span>
          <span class="receipt-item-fine">₹${fine.toLocaleString('en-IN')}</span>
        </div>
      `;
      container.appendChild(itemCard);
    });

    // Simulate minor administrative surcharge/road safety fund contribution (e.g. ₹100 per violation)
    const surcharge = this.selectedViolations.size * 100;
    const totalSum = baseSubtotal + surcharge;

    // Update totals UI
    document.getElementById('receiptBasePenaltyText').textContent = `₹${baseSubtotal.toLocaleString('en-IN')}`;
    document.getElementById('receiptSurchargeText').textContent = `₹${surcharge.toLocaleString('en-IN')} (Safety Surcharge)`;
    document.getElementById('receiptTotalText').textContent = `₹${totalSum.toLocaleString('en-IN')}`;

    // Update Legal Advisory Warning Box
    const adviceBox = document.getElementById('receiptLegalAdviceBox');
    if (adviceBox) {
      let adviceHTML = "";
      
      if (courtOnlyPresent) {
        adviceHTML += `
          <p><i class="fa-solid fa-gavel"></i> <strong>Court Appearance Required:</strong> Drunk Driving and other serious violations cannot be compounded on the spot. You must attend court to settle.</p>
        `;
      }
      
      if (licenseSuspensionTriggered) {
        adviceHTML += `
          <p><i class="fa-solid fa-id-card-clip"></i> <strong>Driving License Disqualification:</strong> Under Section 194D/194C/190(2), this combination of offenses carries a mandatory 3-month DL suspension.</p>
        `;
      }
      
      // General legal note
      adviceHTML += `
        <p style="font-size:0.65rem; border-top:1px solid rgba(245,158,11,0.2); padding-top:0.4rem; margin-top:0.4rem; color:var(--text-muted);">
          Note: Settle compoundable fines within 15 days at nearest traffic station or e-challan portal to avoid court summons.
        </p>
      `;

      adviceBox.innerHTML = adviceHTML;
      adviceBox.style.display = "block";
    }
  }

  // Settle parameters and reset
  resetCalculatorReceipt() {
    this.selectedViolations.clear();
    this.repeatOffense = false;
    
    const repeatToggle = document.getElementById('repeatOffenseToggle');
    if (repeatToggle) repeatToggle.checked = false;

    this.renderViolations();
    this.renderReceipt();
  }

  // Print/Save receipt page generator
  async printOrSaveReceipt() {
    if (this.selectedViolations.size === 0) {
      alert("Please add at least one violation to print a receipt summary.");
      return;
    }

    const stateObj = DRIVELEGAL_DATA.states[this.selectedState];
    const vehicleObj = DRIVELEGAL_DATA.vehicleTypes[this.selectedVehicle];
    const dateStr = new Date().toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' });

    let itemsHTML = "";
    let baseSubtotal = 0;
    
    this.selectedViolations.forEach(id => {
      const v = DRIVELEGAL_DATA.violations.find(item => item.id === id);
      const fine = this.calculateViolationFee(v, this.selectedState, this.selectedVehicle, this.repeatOffense);
      baseSubtotal += fine;

      itemsHTML += `
        <tr style="border-bottom: 1px solid #ddd;">
          <td style="padding: 10px; font-weight: bold;">${v.name}<br><small style="color: #666; font-weight: normal;">${v.section}</small></td>
          <td style="padding: 10px; text-align: right;">₹${fine.toLocaleString('en-IN')}</td>
        </tr>
      `;
    });

    const surcharge = this.selectedViolations.size * 100;
    const totalSum = baseSubtotal + surcharge;

    // Call POST /api/challan/save to persist the challan in the backend database
    let challanNo = "DL-OFFLINE-" + Math.floor(10000000 + Math.random() * 90000000);
    try {
      const payload = {
        state_code: this.selectedState,
        vehicle_type: this.selectedVehicle,
        violations: Array.from(this.selectedViolations),
        is_repeat: this.repeatOffense
      };

      const response = await fetch('/api/challan/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const result = await response.json();
        challanNo = result.challan_number;
        console.log(`[Calculator] Challan saved to backend database successfully: ${challanNo}`);
      } else {
        throw new Error('Save status not OK');
      }
    } catch (err) {
      console.warn("[Calculator] Failed to save challan to backend database. Running in local fallback.", err);
    }

    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <html>
      <head>
        <title>DriveLegal Traffic Challan Breakdown Summary</title>
        <style>
          body { font-family: 'Segoe UI', Roboto, sans-serif; color: #333; margin: 40px; }
          .receipt-box { max-width: 600px; margin: auto; border: 1px solid #ccc; padding: 25px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.05); }
          .title { text-align: center; font-size: 24px; font-weight: bold; text-transform: uppercase; color: #4f46e5; margin-bottom: 5px; }
          .subtitle { text-align: center; color: #666; font-size: 12px; margin-bottom: 25px; }
          .metadata-table { width: 100%; margin-bottom: 20px; font-size: 14px; border-collapse: collapse; }
          .metadata-table td { padding: 4px 0; }
          .metadata-table td:last-child { text-align: right; font-weight: bold; }
          .items-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
          .items-table th { background-color: #f3f4f6; padding: 10px; text-align: left; }
          .summary-table { width: 100%; margin-top: 15px; border-top: 2px solid #333; font-size: 14px; }
          .summary-table td { padding: 8px 0; }
          .summary-table td:last-child { text-align: right; }
          .total-row { font-size: 18px; font-weight: bold; color: #d97706; }
          .disclaimer { font-size: 10px; color: #888; text-align: center; margin-top: 30px; border-top: 1px dashed #ccc; padding-top: 15px; line-height: 1.4; }
          @media print {
            body { margin: 20px; }
            .receipt-box { border: none; box-shadow: none; padding: 0; }
          }
        </style>
      </head>
      <body>
        <div class="receipt-box">
          <div class="title">DRIVELEGAL INDIA</div>
          <div class="subtitle">ESTIMATED COMPOUNDING CHALLAN breakdown</div>
          
          <table class="metadata-table">
            <tr><td>Date Generated:</td><td>${dateStr}</td></tr>
            <tr><td>Challan Number:</td><td><strong>${challanNo}</strong></td></tr>
            <tr><td>Legal Jurisdiction:</td><td>${stateObj.name}</td></tr>
            <tr><td>Vehicle Category:</td><td>${vehicleObj.name}</td></tr>
            <tr><td>Offense Type:</td><td>${this.repeatOffense ? 'Subsequent (Repeat Offense)' : 'First Offense'}</td></tr>
          </table>
          
          <table class="items-table">
            <thead>
              <tr>
                <th style="border-bottom: 2px solid #ccc;">Violation Description</th>
                <th style="border-bottom: 2px solid #ccc; text-align: right;">Compounding Fee</th>
              </tr>
            </thead>
            <tbody>
              ${itemsHTML}
            </tbody>
          </table>
          
          <table class="summary-table">
            <tr><td>Base Compounding Fine Subtotal:</td><td style="font-weight: bold;">₹${baseSubtotal.toLocaleString('en-IN')}</td></tr>
            <tr><td>Road Safety Admin Surcharge:</td><td style="font-weight: bold;">₹${surcharge.toLocaleString('en-IN')}</td></tr>
            <tr class="total-row"><td>Estimated Challan Total:</td><td>₹${totalSum.toLocaleString('en-IN')}</td></tr>
          </table>
          
          <div class="disclaimer">
            <strong>DISCLAIMER:</strong> This receipt is an AI-generated compounding calculation estimate for educational and advisory compliance awareness under the Motor Vehicles Act 2019. It does NOT constitute an official court summons, legal fine receipt, or liability. Official payments must be conducted solely via the Parivahan e-Challan portal or designated judicial courts.
          </div>
        </div>
        <script>
          window.onload = function() { window.print(); }
        </script>
      </body>
      </html>
    `);
    printWindow.document.close();
  }
}
