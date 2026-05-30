// Offline Client-Side NLP Chatbot Engine for DriveLegal India
// Utilizes keyword matching, similarity tokens, and mapping algorithms to parse legal queries.

class TrafficLegalChatbot {
  constructor(containerId, inputId) {
    this.container = document.getElementById(containerId);
    this.input = document.getElementById(inputId);
    this.history = [];
    this.typingSpeed = 30; // Milliseconds per character for typing simulation
    
    // DB Session
    this.sessionId = localStorage.getItem('drivelegal_chat_session') || this.generateSessionId();
    localStorage.setItem('drivelegal_chat_session', this.sessionId);

    // Voice Recognition setup
    this.recognition = null;
    this.isListening = false;
    this.initVoice();
  }

  generateSessionId() {
    return 'sess_' + Math.random().toString(36).substring(2, 15);
  }

  async initSession() {
    try {
      // Create or get session
      await fetch(`${API_BASE_URL}/chat/session?session_id=${this.sessionId}`, { method: 'POST' });
      
      // Load history
      const res = await fetch(`${API_BASE_URL}/chat/${this.sessionId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.messages && data.messages.length > 0) {
          data.messages.forEach(msg => {
            this.appendMessage(msg.sender, msg.text, null, true);
          });
        } else {
          this.initWelcome();
        }
      } else {
        this.initWelcome();
      }
    } catch (e) {
      console.warn("Failed to init chat session from DB", e);
      this.initWelcome();
    }
  }

  async saveMessageToDB(sender, text) {
    try {
      await fetch(`${API_BASE_URL}/chat/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: this.sessionId,
          sender: sender,
          text: text,
          timestamp: new Date().toISOString()
        })
      });
    } catch (e) {
      console.warn("Failed to save message to DB", e);
    }
  }

  // Set up Speech Recognition if supported
  initVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.lang = 'en-IN'; // Indian English
      this.recognition.interimResults = false;
      this.recognition.maxAlternatives = 1;

      this.recognition.onstart = () => {
        const btn = document.getElementById('voiceInputBtn');
        if (btn) btn.classList.add('listening');
        this.isListening = true;
      };

      this.recognition.onend = () => {
        const btn = document.getElementById('voiceInputBtn');
        if (btn) btn.classList.remove('listening');
        this.isListening = false;
      };

      this.recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        if (this.input) {
          this.input.value = text;
          this.handleMessage(text);
        }
      };

      this.recognition.onerror = (e) => {
        console.error("Speech Recognition Error:", e);
        this.appendMessage("bot", "<i class='fa-solid fa-triangle-exclamation'></i> Sorry, I couldn't capture your voice clearly. Please try typing your request.");
      };
    }
  }

  toggleVoice() {
    if (!this.recognition) {
      alert("Speech recognition is not supported in this browser. Please use Chrome or Safari.");
      return;
    }
    if (this.isListening) {
      this.recognition.stop();
    } else {
      this.recognition.start();
    }
  }

  // Initialize chatbot with welcome message
  initWelcome() {
    const welcomeHTML = `
      <p>Namaste! I am <strong>LegalBot</strong>, your client-side offline traffic law assistant.</p>
      <p>I can help you look up <strong>Motor Vehicles Act (2019)</strong> violations, fine schedules, state modifications, and local safety rules.</p>
      <p>Try asking me questions like:</p>
      <ul>
        <li><em>"What is the penalty for driving without a helmet in Mumbai?"</em></li>
        <li><em>"Tell me the speeding fine for cars in Delhi."</em></li>
        <li><em>"Is a pillion rider helmet compulsory in Bengaluru?"</em></li>
      </ul>
      <p>How can I assist you with road compliance today?</p>
    `;
    this.appendMessage("bot", welcomeHTML);
  }

  // Append visual messages to UI
  appendMessage(sender, htmlContent, actions = null, skipDbSave = false) {
    if (!this.container) return;

    // Save to DB
    if (!skipDbSave) {
      this.saveMessageToDB(sender, htmlContent);
    }

    // Create wrapper element
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    // Avatar
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.innerHTML = sender === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-gavel"></i>';
    
    // Bubble
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    bubbleDiv.innerHTML = htmlContent;

    // Actions button
    if (actions) {
      const actionButton = document.createElement('button');
      actionButton.className = 'chat-action-btn';
      actionButton.innerHTML = actions.label;
      actionButton.onclick = actions.callback;
      bubbleDiv.appendChild(actionButton);
    }

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(bubbleDiv);
    this.container.appendChild(messageDiv);
    
    // Scroll to bottom
    this.container.scrollTop = this.container.scrollHeight;
  }

  // Typing simulation placeholder
  showTypingIndicator() {
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'message bot typing-indicator-wrapper';
    indicatorDiv.id = 'typingIndicator';
    indicatorDiv.innerHTML = `
      <div class="message-avatar"><i class="fa-solid fa-gavel"></i></div>
      <div class="message-bubble">
        <div class="typing-indicator">
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
        </div>
      </div>
    `;
    this.container.appendChild(indicatorDiv);
    this.container.scrollTop = this.container.scrollHeight;
  }

  removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
      indicator.remove();
    }
  }

  // Handle user incoming text query
  async handleMessage(text) {
    if (!text || text.trim() === "") return;
    
    // Show user message in UI
    this.appendMessage("user", escapeHTML(text));
    
    // Show bot thinking
    this.showTypingIndicator();
    
    // Determine state code
    let stateKey = null;
    const normalized = text.toLowerCase();
    const stateKeywords = {
      delhi: [/delhi/, /nct/, /capital/, /new delhi/],
      karnataka: [/karnataka/, /bengaluru/, /bangalore/, /mysore/, /ka\d+/],
      maharashtra: [/maharashtra/, /mumbai/, /bombay/, /pune/, /nagpur/, /mh\d+/],
      tamil_nadu: [/tamil nadu/, /tamilnadu/, /chennai/, /madras/, /coimbatore/, /tn\d+/],
      west_bengal: [/west bengal/, /westbengal/, /kolkata/, /calcutta/, /wb\d+/],
      telangana: [/telangana/, /hyderabad/, /ts\d+/, /tg\d+/]
    };
    for (const [key, regexes] of Object.entries(stateKeywords)) {
      if (regexes.some(rx => normalized.match(rx))) {
        stateKey = key;
        break;
      }
    }
    
    if (!stateKey && window.calculator && window.calculator.selectedState) {
      stateKey = window.calculator.selectedState;
    }
    if (!stateKey) {
      stateKey = "delhi";
    }
    
    const stateCode = (DRIVELEGAL_DATA.states[stateKey] && DRIVELEGAL_DATA.states[stateKey].code) || "DL";
    
    let backendAnswered = false;
    let responseHTML = "";
    
    try {
      const response = await fetch(`${API_BASE_URL}/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          state_code: stateCode,
          language: 'en'
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success' && data.matched_question) {
          backendAnswered = true;
          const matchedStateName = DRIVELEGAL_DATA.states[stateKey] ? DRIVELEGAL_DATA.states[stateKey].name : stateKey;
          responseHTML = `<p><strong>Matched FAQ:</strong> "${escapeHTML(data.matched_question)}" (${escapeHTML(matchedStateName)})</p>
                          <div style="background: rgba(59,130,246,0.08); border-left: 4px solid var(--accent-blue); padding: 0.8rem; margin: 0.75rem 0; border-radius: 4px;">
                            <p style="margin: 0; line-height: 1.5;">${escapeHTML(data.answer)}</p>
                          </div>`;
        }
      }
    } catch (err) {
      console.warn("Failed to get response from backend AI chat endpoint, falling back to local NLP parser", err);
    }
    
    setTimeout(() => {
      this.removeTypingIndicator();
      if (backendAnswered) {
        // Also look up if we can offer an action button for calculator injection if it's a known violation
        let matchedViolation = null;
        const violationKeywords = {
          no_helmet: [/helmet/, /headgear/, /head protect/],
          triple_riding: [/triple/, /3 riding/, /three riding/, /three people on bike/, /3 people on bike/],
          no_seatbelt: [/seatbelt/, /seat belt/, /belt/],
          drunk_driving: [/drunk/, /drink/, /alcohol/, /liquor/, /whisky/, /beer/, /intoxicated/],
          speeding: [/speed/, /speeding/, /fast/, /limit/],
          red_light_jumping: [/red light/, /signal/, /traffic light/, /signal jump/, /jump/],
          using_mobile: [/phone/, /mobile/, /texting/, /calling/, /handheld/, /cellular/],
          no_driving_license: [/license/, /licence/, /driving license/, /dl/],
          no_rc: [/rc/, /registration/, /rc book/, /reg certificate/],
          no_insurance: [/insurance/, /third party/, /insurace/],
          no_pucc: [/puc/, /pucc/, /pollution/, /smoke/, /emission/, /exhaust/],
          obstructive_parking: [/park/, /parking/, /wrong park/, /no parking/],
          emergency_vehicle_blocking: [/ambulance/, /emergency/, /fire engine/, /blocking ambulance/],
          no_entry: [/no entry/, /wrong way/, /one way/, /one-way/, /against traffic/]
        };

        for (const [id, regexes] of Object.entries(violationKeywords)) {
          if (regexes.some(rx => normalized.match(rx))) {
            matchedViolation = DRIVELEGAL_DATA.violations.find(v => v.id === id);
            break;
          }
        }

        let action = null;
        if (matchedViolation) {
          let matchedVehicleKey = "lmv";
          const vehicleKeywords = {
            two_wheeler: [/bike/, /motorcycle/, /two wheeler/, /2 wheeler/, /scooter/, /scoty/, /bullet/, /activa/],
            three_wheeler: [/auto/, /rickshaw/, /three wheeler/, /3 wheeler/, /tuk/],
            lmv: [/car/, /jeep/, /suv/, /sedan/, /hatchback/, /lmv/],
            hgv: [/truck/, /bus/, /lorry/, /heavy vehicle/, /hgv/, /dumper/]
          };
          for (const [key, regexes] of Object.entries(vehicleKeywords)) {
            if (regexes.some(rx => normalized.match(rx))) {
              matchedVehicleKey = key;
              break;
            }
          }
          if (matchedViolation.id === 'no_helmet' || matchedViolation.id === 'triple_riding') {
            matchedVehicleKey = 'two_wheeler';
          }
          action = {
            label: `<i class="fa-solid fa-cart-plus"></i> Add to Challan Calculator`,
            callback: () => {
              injectIntoCalculator(stateKey, matchedVehicleKey, matchedViolation.id);
            }
          };
        }
        
        this.appendMessage("bot", responseHTML, action);
      } else {
        const response = this.parseQuery(text);
        this.appendMessage("bot", response.html, response.action);
      }
    }, 600);
  }

  // Core NLP engine: analyzes natural language text and yields a structured response
  parseQuery(queryText) {
    const normalized = queryText.toLowerCase().trim();
    
    // 1. Basic greeting handler
    if (normalized.match(/^(hi|hello|hey|greetings|namaste|hola|good morning|good afternoon)/)) {
      return {
        html: `<p>Hello! How can I help you understand traffic violations or fine schedules today? Feel free to mention a specific city or offense.</p>`
      };
    }
    
    if (normalized.match(/^(thank you|thanks|great|cool|awesome|perfect)/)) {
      return {
        html: `<p>You are welcome! Drive safe and stay compliant with safety rules on the road. Let me know if you have any other questions.</p>`
      };
    }

    // 2. Identify State / Location Entity
    let matchedStateKey = null;
    let matchedStateName = "";
    
    const stateKeywords = {
      delhi: [/delhi/, /nct/, /capital/, /new delhi/],
      karnataka: [/karnataka/, /bengaluru/, /bangalore/, /mysore/, /ka\d+/],
      maharashtra: [/maharashtra/, /mumbai/, /bombay/, /pune/, /nagpur/, /mh\d+/],
      tamil_nadu: [/tamil nadu/, /tamilnadu/, /chennai/, /madras/, /coimbatore/, /tn\d+/],
      west_bengal: [/west bengal/, /westbengal/, /kolkata/, /calcutta/, /wb\d+/],
      telangana: [/telangana/, /hyderabad/, /ts\d+/, /tg\d+/]
    };

    for (const [key, regexes] of Object.entries(stateKeywords)) {
      if (regexes.some(rx => normalized.match(rx))) {
        matchedStateKey = key;
        matchedStateName = DRIVELEGAL_DATA.states[key].name;
        break;
      }
    }

    // 3. Identify Vehicle Type Entity
    let matchedVehicleKey = "lmv"; // Default if not specified
    let vehicleSpecified = false;
    
    const vehicleKeywords = {
      two_wheeler: [/bike/, /motorcycle/, /two wheeler/, /2 wheeler/, /scooter/, /scoty/, /bullet/, /activa/],
      three_wheeler: [/auto/, /rickshaw/, /three wheeler/, /3 wheeler/, /tuk/],
      lmv: [/car/, /jeep/, /suv/, /sedan/, /hatchback/, /lmv/],
      hgv: [/truck/, /bus/, /lorry/, /heavy vehicle/, /hgv/, /dumper/]
    };

    for (const [key, regexes] of Object.entries(vehicleKeywords)) {
      if (regexes.some(rx => normalized.match(rx))) {
        matchedVehicleKey = key;
        vehicleSpecified = true;
        break;
      }
    }

    // 4. Identify Violation Intent
    let matchedViolation = null;
    
    const violationKeywords = {
      no_helmet: [/helmet/, /headgear/, /head protect/],
      triple_riding: [/triple/, /3 riding/, /three riding/, /three people on bike/, /3 people on bike/],
      no_seatbelt: [/seatbelt/, /seat belt/, /belt/],
      drunk_driving: [/drunk/, /drink/, /alcohol/, /liquor/, /whisky/, /beer/, /intoxicated/],
      speeding: [/speed/, /speeding/, /fast/, /limit/],
      red_light_jumping: [/red light/, /signal/, /traffic light/, /signal jump/, /jump/],
      using_mobile: [/phone/, /mobile/, /texting/, /calling/, /handheld/, /cellular/],
      no_driving_license: [/license/, /licence/, /driving license/, /dl/],
      no_rc: [/rc/, /registration/, /rc book/, /reg certificate/],
      no_insurance: [/insurance/, /third party/, /insurace/],
      no_pucc: [/puc/, /pucc/, /pollution/, /smoke/, /emission/, /exhaust/],
      obstructive_parking: [/park/, /parking/, /wrong park/, /no parking/],
      emergency_vehicle_blocking: [/ambulance/, /emergency/, /fire engine/, /blocking ambulance/],
      no_entry: [/no entry/, /wrong way/, /one way/, /one-way/, /against traffic/]
    };

    for (const [id, regexes] of Object.entries(violationKeywords)) {
      if (regexes.some(rx => normalized.match(rx))) {
        matchedViolation = DRIVELEGAL_DATA.violations.find(v => v.id === id);
        break;
      }
    }

    // If helmet query, override vehicle type to 2W (makes sense)
    if (matchedViolation && (matchedViolation.id === 'no_helmet' || matchedViolation.id === 'triple_riding')) {
      matchedVehicleKey = 'two_wheeler';
      vehicleSpecified = true;
    }

    // 5. Generate Response Logic based on extraction results
    
    // CASE A: Both Violation and State found
    if (matchedViolation && matchedStateKey) {
      const stateObj = DRIVELEGAL_DATA.states[matchedStateKey];
      const baseFine = matchedViolation.base_fines[matchedVehicleKey] || 0;
      
      // Get compounding override from state if exists
      let compoundedFine = baseFine;
      if (stateObj.compounding_fees && stateObj.compounding_fees[matchedViolation.id]) {
        const fees = stateObj.compounding_fees[matchedViolation.id];
        compoundedFine = fees[matchedVehicleKey] !== undefined ? fees[matchedVehicleKey] : (fees.all !== undefined ? fees.all : baseFine);
      }

      // Check if fine applies to this vehicle (e.g. helmet fine doesn't apply to cars)
      if (baseFine === 0 && (matchedViolation.id === 'no_helmet' || matchedViolation.id === 'triple_riding')) {
        return {
          html: `<p>In <strong>${stateObj.name}</strong>, regulations for <em>"${matchedViolation.name}"</em> apply specifically to **Two-Wheelers**. Since you inquired about a different vehicle class, no corresponding fine exists for that type.</p>`
        };
      }

      let responseHTML = `
        <p>In <strong>${stateObj.name}</strong>, <em>"${matchedViolation.name}"</em> is governed by <strong>${matchedViolation.section}</strong> of the Motor Vehicles Act.</p>
        <div style="background: rgba(245,158,11,0.08); border-left: 4px solid var(--accent-gold); padding: 0.8rem; margin: 0.75rem 0; border-radius: 4px;">
          <p style="margin-bottom: 0.25rem;"><strong>Fine (Compounding Rate):</strong> ₹${compoundedFine.toLocaleString('en-IN')}</p>
          <p style="font-size: 0.82rem; color: var(--text-muted); margin: 0;"><strong>Vehicular Class:</strong> ${DRIVELEGAL_DATA.vehicleTypes[matchedVehicleKey].name}</p>
        </div>
      `;

      if (matchedViolation.court_only) {
        responseHTML += `
          <p><i class="fa-solid fa-gavel" style="color: var(--accent-red)"></i> <strong>Court challan only:</strong> This violation is non-compoundable on the spot by traffic police. You will receive a magistrate summons to settle the fine in court.</p>
        `;
      } else {
        responseHTML += `
          <p><strong>Additional Penalties:</strong> ${matchedViolation.penalties}</p>
        `;
      }

      // Add local specific rules if any (e.g., pillion rider helmet KA, odd-even DL)
      const relatedLocalRules = stateObj.local_rules.filter(rule => 
        rule.toLowerCase().includes(matchedViolation.id.replace('_', ' ')) || 
        (matchedViolation.id === 'no_helmet' && rule.toLowerCase().includes('pillion'))
      );

      if (relatedLocalRules.length > 0) {
        responseHTML += `
          <div style="margin-top: 0.75rem;">
            <strong>Local Jurisdictional Guideline:</strong>
            <ul style="margin-top: 0.25rem; font-size: 0.85rem; color: var(--text-muted);">
              ${relatedLocalRules.map(r => `<li>${r}</li>`).join('')}
            </ul>
          </div>
        `;
      }

      return {
        html: responseHTML,
        action: {
          label: `<i class="fa-solid fa-cart-plus"></i> Add to Challan Calculator`,
          callback: () => {
            // Trigger calculator state injection
            injectIntoCalculator(matchedStateKey, matchedVehicleKey, matchedViolation.id);
          }
        }
      };
    }

    // CASE B: Violation found, but State is missing
    if (matchedViolation) {
      const baseFine = matchedViolation.base_fines[matchedVehicleKey] || 0;
      
      let responseHTML = `
        <p>I found details for <strong>"${matchedViolation.name}"</strong> under <strong>${matchedViolation.section}</strong> of the Motor Vehicles Act.</p>
        <p><strong>National baseline fine:</strong> ₹${baseFine.toLocaleString('en-IN')} (applies if states haven't overridden compounding rates).</p>
        <p>Which state are you driving in? Compounding fees vary. Please click a state below to check exact rates:</p>
        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.75rem;">
      `;

      // Render quick state buttons
      for (const [key, state] of Object.entries(DRIVELEGAL_DATA.states)) {
        responseHTML += `
          <button class="chat-action-btn" style="margin:0;" onclick="sendSuggestion('What is the fine for ${matchedViolation.name} in ${state.name}?')">
            ${state.name}
          </button>
        `;
      }
      responseHTML += `</div>`;

      return {
        html: responseHTML
      };
    }

    // CASE C: State found, but Violation is missing
    if (matchedStateKey) {
      const stateObj = DRIVELEGAL_DATA.states[matchedStateKey];
      
      let responseHTML = `
        <p>I detected that you are asking about <strong>${stateObj.name}</strong>.</p>
        <p>Here are the active local traffic rules and hotlines for ${stateObj.name}:</p>
        
        <h4 style="margin-top:0.5rem; font-size: 0.88rem;">Key Regional Rules:</h4>
        <ul style="font-size:0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;">
          ${stateObj.local_rules.map(r => `<li>${r}</li>`).join('')}
        </ul>

        <h4 style="font-size: 0.88rem;">Emergency Responders:</h4>
        <ul style="font-size:0.85rem; color: var(--text-muted);">
          ${Object.entries(stateObj.emergency_contacts).map(([name, phone]) => `<li><strong>${name}:</strong> ${phone}</li>`).join('')}
        </ul>
        <p style="margin-top:0.5rem; font-size:0.82rem;">You can check specific violations in ${stateObj.name} by combining them in your prompt, e.g., <em>"helmet fine in ${stateObj.name}"</em>.</p>
      `;

      return {
        html: responseHTML,
        action: {
          label: `<i class="fa-solid fa-radar"></i> Open in Jurisdiction Radar`,
          callback: () => {
            switchTab('radar');
            document.getElementById('stateSelector').value = matchedStateKey;
            triggerGeofencedLocateSim(matchedStateKey);
          }
        }
      };
    }

    // CASE D: None matched - general advice
    return {
      html: `
        <p>I couldn't identify the specific traffic violation or state in your query.</p>
        <p>Please rephrase your question. Be sure to specify:</p>
        <ul>
          <li><strong>The offense</strong> (e.g. <em>helmet, speeding, drunk driving, red light, parking</em>)</li>
          <li><strong>The state/city</strong> (e.g. <em>Delhi, Bengaluru, Mumbai, Chennai, West Bengal</em>)</li>
        </ul>
        <p>Example: <em>"Seatbelt fine in Pune"</em> or <em>"Overspeeding fee in Karnataka"</em>.</p>
      `
    };
  }
}

// Utility function to escape HTML to prevent XSS
function escapeHTML(str) {
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}
