// Interactive Jurisdiction Geofencing Radar Simulator
// Uses HTML5 Canvas to render a high-quality sweeping radar screen representing regional law jurisdictions.

class JurisdictionRadar {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.angle = 0;
    this.speed = 0.02; // Radian speed per frame
    this.active = false;
    this.blips = [];
    this.pulseRadius = 0;
    
    // Resize handling (making it responsive)
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    if (!this.canvas) return;
    const parent = this.canvas.parentElement;
    const size = Math.min(parent.clientWidth, parent.clientHeight, 500);
    this.canvas.width = size;
    this.canvas.height = size;
  }

  setJurisdictionPoints(stateKey) {
    this.blips = [];
    
    // Reference coordinates for major city centers in each state
    const references = {
      delhi: { name: "Delhi", lat: 28.6139, lng: 77.2090, points: [
        { name: "Connaught Place Checkpoint", latOffset: 0.016, lngOffset: 0.001, type: "checkpost" },
        { name: "DND Flyway Speed Camera", latOffset: -0.034, lngOffset: 0.061, type: "camera" },
        { name: "NH44 Speed Trap", latOffset: 0.106, lngOffset: -0.079, type: "camera" },
        { name: "Gurugram Border Toll Gate", latOffset: -0.134, lngOffset: -0.129, type: "toll" },
        { name: "Noida Link Rd Police Post", latOffset: -0.024, lngOffset: 0.081, type: "checkpost" }
      ]},
      karnataka: { name: "Bengaluru", lat: 12.9716, lng: 77.5946, points: [
        { name: "MG Road Intercept Checkpoint", latOffset: 0.005, lngOffset: 0.012, type: "checkpost" },
        { name: "Electronic City Expressway Cam", latOffset: -0.121, lngOffset: 0.065, type: "camera" },
        { name: "NICE Road Speed Trap", latOffset: -0.071, lngOffset: -0.094, type: "camera" },
        { name: "Kempegowda Airport Toll Gate", latOffset: 0.224, lngOffset: 0.111, type: "toll" },
        { name: "Yeshwanthpur Traffic Police Post", latOffset: 0.065, lngOffset: -0.054, type: "checkpost" }
      ]},
      maharashtra: { name: "Mumbai", lat: 18.9696, lng: 72.8230, points: [
        { name: "Bandra-Worli Sea Link Camera", latOffset: 0.052, lngOffset: -0.013, type: "camera" },
        { name: "Gateway of India Police Naka", latOffset: -0.048, lngOffset: 0.007, type: "checkpost" },
        { name: "Thane Check Naka", latOffset: 0.211, lngOffset: 0.137, type: "toll" },
        { name: "Eastern Express Highway Trap", latOffset: 0.125, lngOffset: 0.095, type: "camera" },
        { name: "Vashi Bridge Toll Post", latOffset: 0.062, lngOffset: 0.165, type: "toll" }
      ]},
      tamil_nadu: { name: "Chennai", lat: 13.0827, lng: 80.2707, points: [
        { name: "Anna Salai Police Checkpoint", latOffset: -0.025, lngOffset: -0.015, type: "checkpost" },
        { name: "OMR Speed Camera Sector 2", latOffset: -0.121, lngOffset: 0.008, type: "camera" },
        { name: "ECR Toll Naka (Uthandi)", latOffset: -0.198, lngOffset: 0.021, type: "toll" },
        { name: "Koyambedu Junction Camera", latOffset: -0.012, lngOffset: -0.068, type: "camera" },
        { name: "Tambaram Circle Check Gate", latOffset: -0.214, lngOffset: -0.162, type: "checkpost" }
      ]},
      west_bengal: { name: "Kolkata", lat: 22.5726, lng: 88.3639, points: [
        { name: "Howrah Bridge Police Post", latOffset: 0.008, lngOffset: -0.024, type: "checkpost" },
        { name: "Maa Flyover Speed Camera", latOffset: -0.032, lngOffset: 0.031, type: "camera" },
        { name: "Vidyasagar Setu Toll Plaza", latOffset: -0.021, lngOffset: -0.048, type: "toll" },
        { name: "EM Bypass Radar Gate", latOffset: -0.082, lngOffset: 0.042, type: "camera" },
        { name: "Salt Lake Sector V Patrol", latOffset: 0.002, lngOffset: 0.071, type: "checkpost" }
      ]},
      telangana: { name: "Hyderabad", lat: 17.3850, lng: 78.4867, points: [
        { name: "Charminar Police Post", latOffset: -0.022, lngOffset: -0.009, type: "checkpost" },
        { name: "PVNR Expressway Cam 1", latOffset: -0.052, lngOffset: -0.061, type: "camera" },
        { name: "Outer Ring Road (ORR) Speed Gate", latOffset: -0.158, lngOffset: 0.092, type: "camera" },
        { name: "Secunderabad Patrol Naka", latOffset: 0.065, lngOffset: 0.018, type: "checkpost" },
        { name: "Gachibowli Junction Monitor", latOffset: 0.015, lngOffset: -0.125, type: "camera" }
      ]}
    };

    const config = references[stateKey] || references.delhi;
    const canvasCenter = this.canvas.width / 2;
    const maxRadius = canvasCenter * 0.85;

    // Convert offsets into polar coordinates relative to the radar size
    this.blips = config.points.map(p => {
      // Map offsets to canvas coordinates (scale factor 1500)
      const x = canvasCenter + p.lngOffset * 1500;
      const y = canvasCenter - p.latOffset * 1500; // Invert y for standard latitude orientation
      
      // Calculate polar coordinates relative to center
      const dx = x - canvasCenter;
      const dy = y - canvasCenter;
      const r = Math.sqrt(dx * dx + dy * dy);
      const angle = Math.atan2(dy, dx);
      
      // Bound the radius to fit on the screen
      const displayRadius = Math.min(r, maxRadius);
      const displayX = canvasCenter + displayRadius * Math.cos(angle);
      const displayY = canvasCenter + displayRadius * Math.sin(angle);

      return {
        name: p.name,
        type: p.type,
        x: displayX,
        y: displayY,
        angle: angle < 0 ? angle + Math.PI * 2 : angle, // Normalize angle to [0, 2pi]
        radius: displayRadius,
        intensity: 0,
        active: true
      };
    });
  }

  start() {
    this.active = true;
    this.animate();
  }

  stop() {
    this.active = false;
  }

  animate() {
    if (!this.active || !this.canvas) return;

    this.draw();
    
    // Increment angle
    this.angle += this.speed;
    if (this.angle >= Math.PI * 2) {
      this.angle -= Math.PI * 2;
    }

    // Increment central pulse
    this.pulseRadius += 0.5;
    if (this.pulseRadius > 30) {
      this.pulseRadius = 0;
    }

    requestAnimationFrame(() => this.animate());
  }

  draw() {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const maxR = cx * 0.9;

    // Clear with transparency trail
    ctx.fillStyle = 'rgba(11, 15, 25, 0.15)'; // Trail length depends on opacity
    ctx.fillRect(0, 0, w, h);

    // Draw concentric circles
    ctx.strokeStyle = 'rgba(99, 102, 241, 0.08)';
    ctx.lineWidth = 1;
    
    for (let r = 0.25; r <= 1.0; r += 0.25) {
      ctx.beginPath();
      ctx.arc(cx, cy, maxR * r, 0, Math.PI * 2);
      ctx.stroke();
      
      // Text labels for simulated range
      ctx.fillStyle = 'rgba(156, 163, 175, 0.2)';
      ctx.font = '9px monospace';
      ctx.fillText(`${(r * 10).toFixed(0)} km`, cx + 5, cy - maxR * r + 12);
    }

    // Draw grid crosshairs
    ctx.beginPath();
    ctx.moveTo(cx - maxR, cy);
    ctx.lineTo(cx + maxR, cy);
    ctx.moveTo(cx, cy - maxR);
    ctx.lineTo(cx, cy + maxR);
    ctx.stroke();

    // Draw diagonal crosshairs
    ctx.strokeStyle = 'rgba(99, 102, 241, 0.03)';
    ctx.beginPath();
    ctx.moveTo(cx - maxR * 0.7, cy - maxR * 0.7);
    ctx.lineTo(cx + maxR * 0.7, cy + maxR * 0.7);
    ctx.moveTo(cx - maxR * 0.7, cy + maxR * 0.7);
    ctx.lineTo(cx + maxR * 0.7, cy - maxR * 0.7);
    ctx.stroke();

    // Draw Sweep Line
    const sweepX = cx + maxR * Math.cos(this.angle);
    const sweepY = cy + maxR * Math.sin(this.angle);
    
    // Radial gradient for sweep line (simulates glow fade)
    ctx.strokeStyle = 'rgba(79, 70, 229, 0.6)';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(sweepX, sweepY);
    ctx.stroke();
    
    // Draw sweep tail gradient (pie slice trail)
    const trailSegments = 25;
    for (let i = 0; i < trailSegments; i++) {
      const alpha = (1 - (i / trailSegments)) * 0.15;
      const trailAngle = this.angle - (i * 0.015);
      
      ctx.fillStyle = `rgba(99, 102, 241, ${alpha})`;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, maxR, trailAngle, trailAngle + 0.016, false);
      ctx.closePath();
      ctx.fill();
    }

    // Process and draw blips
    this.blips.forEach(blip => {
      // Calculate angular distance between sweep and blip
      let diff = this.angle - blip.angle;
      if (diff < 0) diff += Math.PI * 2;
      
      // If sweep is passing over blip, lock and trigger blip flare
      if (diff < 0.1) {
        blip.intensity = 1.0;
        // Display details when locked
        this.triggerLockFeedback(blip);
      } else {
        // Fade out intensity
        blip.intensity -= 0.01;
        if (blip.intensity < 0) blip.intensity = 0;
      }

      if (blip.intensity > 0) {
        const radiusVal = 4 + blip.intensity * 6;
        let color = 'rgba(6, 182, 212,'; // Cyan for checkposts
        
        if (blip.type === 'camera') {
          color = 'rgba(239, 68, 68,'; // Red for speed traps
        } else if (blip.type === 'toll') {
          color = 'rgba(245, 158, 11,'; // Gold for tolls
        }

        // Draw blip outer glow ring
        ctx.fillStyle = `${color} ${blip.intensity * 0.25})`;
        ctx.beginPath();
        ctx.arc(blip.x, blip.y, radiusVal * 2, 0, Math.PI * 2);
        ctx.fill();

        // Draw blip core
        ctx.fillStyle = `${color} ${blip.intensity})`;
        ctx.beginPath();
        ctx.arc(blip.x, blip.y, 4, 0, Math.PI * 2);
        ctx.fill();

        // Draw name label for intense blips
        if (blip.intensity > 0.4) {
          ctx.fillStyle = `rgba(243, 244, 246, ${blip.intensity})`;
          ctx.font = '10px "Outfit", sans-serif';
          ctx.fillText(blip.name, blip.x + 8, blip.y + 3);
          
          // Small technical border indicators
          ctx.strokeStyle = `rgba(99, 102, 241, ${blip.intensity * 0.4})`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.arc(blip.x, blip.y, radiusVal + 4, 0, Math.PI * 2);
          ctx.stroke();
        }
      }
    });

    // Draw central pulsing user dot (representing current GPS lock)
    ctx.fillStyle = 'rgba(99, 102, 241, 0.15)';
    ctx.beginPath();
    ctx.arc(cx, cy, 10 + this.pulseRadius, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = 'var(--primary-hover)';
    ctx.beginPath();
    ctx.arc(cx, cy, 5, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.strokeStyle = 'white';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(cx, cy, 5, 0, Math.PI * 2);
    ctx.stroke();
  }

  // Visual lock notifications
  triggerLockFeedback(blip) {
    const marker = document.getElementById('radarCoordMarker');
    if (!marker) return;

    // Place absolute marker on the screen relative to canvas position
    const rect = this.canvas.getBoundingClientRect();
    const x = rect.left + blip.x;
    const y = rect.top + blip.y;
    
    marker.style.left = `${blip.x - 5}px`;
    marker.style.top = `${blip.y - 5}px`;
    marker.style.display = 'block';
    
    // Add targeted custom classes or triggers in main application if required
  }
}
