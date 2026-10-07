/**
 * =============================================================================
 * TLU IT Study Copilot - Dynamic Mascot Motion Engine (TLUMascotController)
 * File: public/js/mascot.js
 * Version: 1.0.0
 * Architecture: Modular Vanilla ES6+ Class, Zero External Dependencies
 * Branding: Thang Long University IT Dragon Mascot
 * Palette: Primary Blue (#0D62FE), Crown Amber (#FFB800), Coral Red (#FF3B30)
 * =============================================================================
 */

(function (window, document) {
  'use strict';

  /**
   * Sound FX Engine using HTML5 Web Audio API
   * Pure procedural synthesis: 0 audio file assets required.
   */
  class MascotAudioSynthesizer {
    constructor() {
      this.audioCtx = null;
      this.isMuted = false;
      try {
        const stored = localStorage.getItem('tlu_mascot_sound_muted');
        if (stored !== null) {
          this.isMuted = stored === 'true';
        }
      } catch (e) {
        this.isMuted = false;
      }
    }

    initContext() {
      if (!this.audioCtx && typeof window.AudioContext !== 'undefined') {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        this.audioCtx = new AudioContextClass();
      }
      if (this.audioCtx && this.audioCtx.state === 'suspended') {
        this.audioCtx.resume();
      }
    }

    toggleMute() {
      this.isMuted = !this.isMuted;
      try {
        localStorage.setItem('tlu_mascot_sound_muted', String(this.isMuted));
      } catch (e) {}
      return this.isMuted;
    }

    playTone(frequency, type, durationMs, startTimeOffset = 0, peakGain = 0.08) {
      if (this.isMuted) return;
      try {
        this.initContext();
        if (!this.audioCtx) return;

        const ctx = this.audioCtx;
        const now = ctx.currentTime + startTimeOffset;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = type;
        osc.frequency.setValueAtTime(frequency, now);

        gain.gain.setValueAtTime(0.001, now);
        gain.gain.exponentialRampToValueAtTime(peakGain, now + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + (durationMs / 1000));

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(now);
        osc.stop(now + (durationMs / 1000) + 0.05);
      } catch (e) {
        // Fallback silently if device audio is restricted
      }
    }

    playChime() {
      this.playTone(659.25, 'sine', 180, 0, 0.06);     // E5
      this.playTone(880.00, 'sine', 260, 0.12, 0.07);  // A5
    }

    playCheer() {
      // Ascending C-Major fanfare: C5 -> E5 -> G5 -> C6
      this.playTone(523.25, 'triangle', 160, 0.00, 0.08); // C5
      this.playTone(659.25, 'triangle', 160, 0.10, 0.09); // E5
      this.playTone(783.99, 'triangle', 180, 0.20, 0.10); // G5
      this.playTone(1046.50, 'sine', 450, 0.32, 0.12);    // C6
    }

    playCaution() {
      // Two-tone warning tone: F#5 -> D5
      this.playTone(739.99, 'triangle', 200, 0.00, 0.09); // F#5
      this.playTone(587.33, 'sine', 320, 0.18, 0.08);     // D5
    }

    playThink() {
      this.playTone(392.00, 'sine', 150, 0, 0.04);       // G4 soft blip
    }

    playPet() {
      // Harp shimmer: G5 -> B5 -> E6
      this.playTone(783.99, 'sine', 120, 0.00, 0.06);     // G5
      this.playTone(987.77, 'sine', 140, 0.08, 0.06);     // B5
      this.playTone(1318.51, 'sine', 220, 0.16, 0.07);    // E6
    }
  }

  /**
   * Lightweight Canvas Particle Confetti & Sparkle Engine
   */
  class MascotParticleEngine {
    constructor(container) {
      this.container = container;
      this.canvas = null;
      this.ctx = null;
      this.particles = [];
      this.animId = null;
      this.colors = ['#0D62FE', '#FFB800', '#FF3B30', '#10B981', '#38BDF8', '#FFC72C'];
    }

    ensureCanvas() {
      if (!this.canvas && this.container) {
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'mascot-particle-canvas';
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '10';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
        this.resize();
        window.addEventListener('resize', () => this.resize());
      }
    }

    resize() {
      if (!this.canvas || !this.container) return;
      const rect = this.container.getBoundingClientRect();
      this.canvas.width = rect.width || 300;
      this.canvas.height = rect.height || 260;
    }

    burstConfetti(count = 35) {
      this.ensureCanvas();
      if (!this.ctx) return;
      this.resize();

      const cx = this.canvas.width / 2;
      const cy = this.canvas.height * 0.45;

      for (let i = 0; i < count; i++) {
        const angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.5;
        const speed = 3.5 + Math.random() * 5.5;
        this.particles.push({
          x: cx,
          y: cy,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed - 2.5,
          color: this.colors[Math.floor(Math.random() * this.colors.length)],
          size: 4 + Math.random() * 4,
          shape: Math.random() > 0.4 ? 'rect' : 'circle',
          rotation: Math.random() * 360,
          rotationSpeed: (Math.random() - 0.5) * 12,
          gravity: 0.18,
          drag: 0.985,
          alpha: 1.0,
          fade: 0.012 + Math.random() * 0.015
        });
      }

      if (!this.animId) {
        this.tick();
      }
    }

    burstHearts(count = 6) {
      if (!this.container) return;
      const rect = this.container.getBoundingClientRect();
      const cx = rect.width / 2;
      const cy = rect.height * 0.4;

      for (let i = 0; i < count; i++) {
        const floater = document.createElement('span');
        floater.textContent = ''; floater.style.width = '6px'; floater.style.height = '6px'; floater.style.borderRadius = '50%'; floater.style.background = '#FFB800';
        floater.className = 'mascot-floater-sparkle';
        floater.style.position = 'absolute';
        floater.style.left = (cx + (Math.random() - 0.5) * 60) + 'px';
        floater.style.top = (cy + (Math.random() - 0.5) * 30) + 'px';
        floater.style.fontSize = (16 + Math.random() * 8) + 'px';
        floater.style.pointerEvents = 'none';
        floater.style.zIndex = '20';
        floater.style.transition = 'all 1.2s cubic-bezier(0.2, 0.8, 0.4, 1)';
        floater.style.transform = 'translateY(0) scale(0.6)';
        floater.style.opacity = '1';

        this.container.appendChild(floater);

        setTimeout(() => {
          floater.style.transform = `translate(${(Math.random() - 0.5) * 60}px, -60px) scale(1.2)`;
          floater.style.opacity = '0';
        }, 30);

        setTimeout(() => {
          if (floater.parentNode) floater.parentNode.removeChild(floater);
        }, 1300);
      }
    }

    tick() {
      if (!this.ctx || !this.canvas) return;
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

      for (let i = this.particles.length - 1; i >= 0; i--) {
        const p = this.particles[i];
        p.vx *= p.drag;
        p.vy = p.vy * p.drag + p.gravity;
        p.x += p.vx;
        p.y += p.vy;
        p.rotation += p.rotationSpeed;
        p.alpha -= p.fade;

        if (p.alpha <= 0 || p.y > this.canvas.height + 20) {
          this.particles.splice(i, 1);
          continue;
        }

        this.ctx.save();
        this.ctx.globalAlpha = Math.max(0, p.alpha);
        this.ctx.translate(p.x, p.y);
        this.ctx.rotate((p.rotation * Math.PI) / 180);
        this.ctx.fillStyle = p.color;

        if (p.shape === 'rect') {
          this.ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 1.4);
        } else {
          this.ctx.beginPath();
          this.ctx.arc(0, 0, p.size / 2, 0, Math.PI * 2);
          this.ctx.fill();
        }
        this.ctx.restore();
      }

      if (this.particles.length > 0) {
        if (typeof requestAnimationFrame !== 'undefined') {
          this.animId = requestAnimationFrame(() => this.tick());
        }
      } else {
        this.animId = null;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      }
    }
  }

  /**
   * Main Mascot State Controller (window.TLUMascot)
   */
  class TLUMascotController {
    constructor() {
      this.state = 'idle';
      this.previousState = null;
      this.resetTimer = null;
      this.elements = {};
      this.audio = new MascotAudioSynthesizer();
      this.particles = null;
      this.isPetting = false;
      this.quoteIndex = 0;

      this.quotes = {
        idle: [
          'Chào bạn! Rồng Xanh TLU sẵn sàng đồng hành cùng bạn chinh phục 5 môn CNTT TLU! ',
          'Hôm nay chúng ta sẽ ôn luyện thuật toán, SQL hay kiến trúc máy tính nào? ',
          'Nắm chắc lý thuyết, thực hành vững vàng - đó là tinh thần sinh viên TLU! '
        ],
        thinking: [
          'Hội đồng Tác tử LangGraph đang phân tích ngữ cảnh học liệu và giải thuật... ',
          'Đang tra cứu kho học liệu Medallion qua Hybrid Search (BGE-M3 + BM25)... ',
          'Đang thẩm định phản hồi sư phạm qua chốt chặn Socratic Reviewer... '
        ],
        cheering: [
          'Xuất sắc! Code đã vượt qua kiểm thử! Rồng TLU chúc mừng bạn! ',
          'Tuyệt vời! Thuật toán đã tối ưu và logic hoạt động hoàn hảo! ',
          'Bạn nắm bài rất nhanh! Cứ giữ vững phong độ này nhé! '
        ],
        caution: [
          'Rồng TLU nhắc bạn: Theo Điều 25 Quy chế Đào tạo TLU, mình chỉ gợi ý tư duy từng bước chứ không giải hộ bài tập đâu nha! ',
          'Cảnh báo an toàn học thuật: Hãy tự tay viết code để rèn luyện kỹ năng sinh viên TLU nhé! ',
          'Đừng lo lắng khi gặp bug! Hãy xem gợi ý phân tích từng bước bên dưới nào! '
        ],
        pet: [
          'Rồng TLU chúc bạn học tốt và đạt điểm A môn này nha! ',
          'Chăm chỉ ôn tập mỗi ngày, tấm bằng Kỹ sư CNTT Thăng Long đang vẫy gọi! ',
          'Học công nghệ tại TLU thật tuyệt! Cần mình gợi ý phần nào không? ',
          'Nạp chút năng lượng nào! Uống ngụm nước rồi cùng code tiếp nhé! ',
          'Gặp bug khó? Nghỉ ngơi 5 phút, rồi phân tích từng bước Socratic cùng mình nha! '
        ]
      };
    }

    init() {
      this.cacheDOMElements();
      if (this.elements.stage) {
        this.particles = new MascotParticleEngine(this.elements.stage);
      }
      this.bindUserInteractions();
      this.bindSystemEvents();
      this.updateDOMState('idle');
      this.updateSpeech(this.getRandomQuote('idle'));
      return this;
    }

    cacheDOMElements() {
      this.elements = {
        stage: document.getElementById('mascot-stage') || document.querySelector('.mascot-stage'),
        floatingStage: document.getElementById('floating-mascot-stage') || document.querySelector('.floating-mascot-stage') || document.getElementById('mascot-floating-widget'),
        speech: document.getElementById('mascot-speech') || document.querySelector('.mascot-speech') || document.getElementById('mascot-bubble'),
        speechText: document.getElementById('mascot-speech-text'),
        avatar: document.getElementById('mascot-avatar') || document.getElementById('mascot-img') || document.querySelector('.mascot-img') || document.querySelector('.mascot-avatar'),
        aura: document.getElementById('mascot-aura') || document.querySelector('.mascot-aura'),
        soundBtn: document.getElementById('mascot-sound-toggle') || document.querySelector('.mascot-sound-btn'),
        cautionBadge: document.getElementById('caution-badge') || document.getElementById('mascot-caution-badge') || document.querySelector('.caution-badge')
      };
    }

    setState(newState, customMessage = null, autoResetMs = 0) {
      const normalizedState = newState === 'success' ? 'cheering' : newState;
      const validStates = ['idle', 'thinking', 'cheering', 'caution'];

      if (!validStates.includes(normalizedState)) {
        console.warn(`[TLUMascot] Invalid state: "${newState}". Valid: ${validStates.join(', ')}`);
        return;
      }

      this.previousState = this.state;
      this.state = normalizedState;

      if (this.resetTimer) {
        clearTimeout(this.resetTimer);
        this.resetTimer = null;
      }

      this.updateDOMState(normalizedState);

      const messageToDisplay = customMessage || this.getRandomQuote(normalizedState);
      this.updateSpeech(messageToDisplay, normalizedState);

      this.triggerAudioAndFX(normalizedState);

      if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function' && typeof CustomEvent !== 'undefined') {
        const event = new CustomEvent('tlu:mascot:statechange', {
          detail: {
            state: normalizedState,
            previousState: this.previousState,
            message: messageToDisplay,
            timestamp: Date.now()
          }
        });
        window.dispatchEvent(event);
      }

      let timeout = autoResetMs;
      if (timeout <= 0) {
        if (normalizedState === 'cheering') timeout = 5000;
        else if (normalizedState === 'caution') timeout = 7000;
      }

      if (timeout > 0 && normalizedState !== 'idle') {
        this.resetTimer = setTimeout(() => {
          this.setState('idle', 'Mình sẵn sàng hỗ trợ bài học tiếp theo của bạn! ');
        }, timeout);
      }
    }

    getState() {
      return this.state;
    }

    setIdle(message = null) {
      this.setState('idle', message);
    }

    setThinking(message = null) {
      this.setState('thinking', message);
    }

    setCheering(message = null, autoResetMs = 5000) {
      this.setState('cheering', message, autoResetMs);
    }

    setSuccess(message = null, autoResetMs = 5000) {
      this.setState('cheering', message, autoResetMs);
    }

    setCaution(message = null, autoResetMs = 7000) {
      this.setState('caution', message, autoResetMs);
    }

    onPersonaChange(name, className) {
      this.setCheering(`Chào mừng bạn ${name || ''} (${className || ''})! Rồng TLU đã sẵn sàng đồng hành cùng bạn!`);
    }

    onCourseChange(courseCode) {
      this.setCheering(`Đã chuyển sang môn học ${courseCode}. Cùng bắt đầu ôn luyện nhé!`);
    }

    speak(message, durationMs = 4000) {
      this.updateSpeech(message, this.state);
      this.audio.playChime();
      if (durationMs > 0 && this.state === 'idle') {
        if (this.resetTimer) clearTimeout(this.resetTimer);
        this.resetTimer = setTimeout(() => {
          this.updateSpeech(this.getRandomQuote('idle'), 'idle');
        }, durationMs);
      }
    }

    pet() {
      if (this.isPetting) return;
      this.isPetting = true;
      this.audio.playPet();

      const avatar = this.elements.avatar;

      if (avatar) {
        avatar.classList.add('animate-pet-wiggle');
        setTimeout(() => avatar.classList.remove('animate-pet-wiggle'), 600);
      }

      if (this.particles) {
        this.particles.burstHearts(6);
      }

      const quote = this.quotes.pet[this.quoteIndex % this.quotes.pet.length];
      this.quoteIndex++;
      this.speak(quote, 4500);

      setTimeout(() => {
        this.isPetting = false;
      }, 700);
    }

    triggerConfetti() {
      if (this.particles) {
        this.particles.burstConfetti(45);
      }
    }

    toggleSound() {
      const isMuted = this.audio.toggleMute();
      this.updateSoundButtonUI(isMuted);
      if (!isMuted) {
        this.audio.playChime();
      }
      return !isMuted;
    }

    isMuted() {
      return this.audio.isMuted;
    }

    updateDOMState(state) {
      const stages = [this.elements.stage, this.elements.floatingStage].filter(Boolean);
      const allStateClasses = ['state-idle', 'state-thinking', 'state-cheering', 'state-success', 'state-caution'];

      stages.forEach((stageEl) => {
        allStateClasses.forEach((cls) => stageEl.classList.remove(cls));
        stageEl.classList.add(`state-${state}`);
        if (state === 'cheering') {
          stageEl.classList.add('state-success');
        }
      });

      if (this.elements.cautionBadge) {
        if (state === 'caution') {
          this.elements.cautionBadge.classList.remove('hidden');
          this.elements.cautionBadge.style.display = 'inline-flex';
        } else {
          this.elements.cautionBadge.classList.add('hidden');
          this.elements.cautionBadge.style.display = 'none';
        }
      }

      if (this.elements.aura) {
        if (state === 'thinking') {
          this.elements.aura.classList.remove('hidden');
          this.elements.aura.style.display = 'block';
        } else {
          this.elements.aura.classList.add('hidden');
          this.elements.aura.style.display = 'none';
        }
      }
    }

    updateSpeech(message, state = 'idle') {
      const speechEl = this.elements.speech;
      const speechTextEl = this.elements.speechText;
      if (!speechEl) return;

      const targetTextNode = speechTextEl || speechEl;

      if (state === 'thinking') {
        targetTextNode.innerHTML = `
          <span class="inline-flex items-center gap-1.5">
            <span>${message}</span>
            <span class="inline-flex gap-1 ml-1">
              <span class="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce" style="animation-delay: 0s"></span>
              <span class="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce" style="animation-delay: 0.15s"></span>
              <span class="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce" style="animation-delay: 0.3s"></span>
            </span>
          </span>
        `;
      } else {
        targetTextNode.textContent = message;
      }

      speechEl.classList.remove('mascot-bubble-pop');
      void speechEl.offsetWidth; // Force DOM reflow to re-trigger animation
      speechEl.classList.add('mascot-bubble-pop');
    }

    triggerAudioAndFX(state) {
      switch (state) {
        case 'cheering':
          this.audio.playCheer();
          this.triggerConfetti();
          break;
        case 'caution':
          this.audio.playCaution();
          break;
        case 'thinking':
          this.audio.playThink();
          break;
        case 'idle':
        default:
          break;
      }
    }

    getRandomQuote(state) {
      const list = this.quotes[state] || this.quotes.idle;
      return list[Math.floor(Math.random() * list.length)];
    }

    updateSoundButtonUI(isMuted) {
      const btn = this.elements.soundBtn;
      if (!btn) return;
      btn.setAttribute('aria-pressed', String(!isMuted));
      btn.title = isMuted ? 'Bật âm thanh linh vật' : 'Tắt âm thanh linh vật';
      if (isMuted) {
        btn.classList.add('opacity-50');
      } else {
        btn.classList.remove('opacity-50');
      }
    }

    bindUserInteractions() {
      const clickableTargets = [this.elements.avatar, this.elements.stage, this.elements.floatingStage].filter(Boolean);
      clickableTargets.forEach((target) => {
        target.addEventListener('click', (e) => {
          if (e.target.closest('#mascot-sound-toggle') || e.target.closest('.mascot-sound-btn') || e.target.closest('#mascot-controls-bar')) return;
          this.pet();
        });
      });

      if (this.elements.soundBtn) {
        this.elements.soundBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          this.toggleSound();
        });
        this.updateSoundButtonUI(this.audio.isMuted);
      }
    }

    bindSystemEvents() {
      if (typeof window === 'undefined') return;

      window.addEventListener('tlu:chat:query', () => {
        this.setThinking();
      });

      window.addEventListener('tlu:chat:article25', (e) => {
        const msg = (e.detail && e.detail.message) ||
          'Rồng TLU nhắc bạn: Theo Điều 25 Quy chế Đào tạo TLU, mình chỉ gợi ý tư duy từng bước chứ không giải hộ bài tập đâu nha! ';
        this.setCaution(msg, 8000);
      });

      window.addEventListener('tlu:code:run', () => {
        this.setThinking('Rồng TLU đang biên dịch và chạy thử mã nguồn...');
      });

      window.addEventListener('tlu:code:pass', () => {
        this.setCheering('Xuất sắc! Code đã vượt qua kiểm thử! Rồng TLU chúc mừng bạn! ', 6000);
      });

      window.addEventListener('tlu:code:fail', (e) => {
        const msg = (e.detail && e.detail.message) ||
          'Có chút lỗi cú pháp rồi! Đừng nản, cùng Rồng TLU xem Diff Viewer để sửa nhé! ';
        this.setCaution(msg, 6000);
      });

      window.addEventListener('tlu:tab:switch', (e) => {
        const tab = e.detail && e.detail.tab;
        if (tab === 'socratic') {
          this.speak('Chào bạn tại Studio Gia sư Socratic! Hôm nay chúng ta luyện môn gì nào? ', 4000);
        } else if (tab === 'multiagent') {
          this.speak('Chào mừng đến Trung tâm Đa tác tử LangGraph & Medallion Lakehouse! ', 4000);
        } else if (tab === 'ops') {
          this.speak('Bảng điều khiển FinOps & Viễn thám OpenTelemetry sẵn sàng kiểm tra 6 Golden Signals! ', 4000);
        }
      });

      window.addEventListener('tlu:course:switch', (e) => {
        const code = e.detail && e.detail.courseCode;
        const courseGreetings = {
          IT101: 'Cơ sở lập trình C/C++: Nhớ cẩn thận cấp phát con trỏ và giải phóng bộ nhớ nha! ',
          IT201: 'OOP Java: Đóng gói, Kế thừa, Đa hình và Trừu tượng - 4 trụ cột hướng đối tượng vững chắc! ',
          IT205: 'Hệ quản trị CSDL SQL: Chú ý khóa chính, khóa ngoại và chỉ mục B-Tree để truy vấn siêu tốc! ',
          IT301: 'Python & Thuật toán: Độ phức tạp O(n log n), đệ quy và cấu trúc dữ liệu tối ưu! ',
          IT315: 'Kiến trúc máy tính & HĐH: Pipeline CPU, Phân trang bộ nhớ ảo và Đa luồng song song! '
        };
        if (courseGreetings[code]) {
          this.speak(courseGreetings[code], 5000);
        }
      });

      window.addEventListener('tlu:persona:switch', (e) => {
        const persona = e.detail && e.detail.persona;
        if (persona === 'an') {
          this.speak('Chào bạn An (K35)! Cùng nắm chắc nền tảng C/C++ nhé, Rồng TLU luôn ở đây trợ giúp từng bước! ', 4500);
        } else if (persona === 'linh') {
          this.speak('Chào bạn Linh (K34)! Cùng tối ưu hóa hiệu năng hệ thống và truy vấn cơ sở dữ liệu nào! ', 4500);
        }
      });
    }
  }

  // Instantiate singleton and mount to global window
  const mascotInstance = new TLUMascotController();
  window.TLUMascot = mascotInstance;

  // Auto initialize on DOM readiness
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => mascotInstance.init());
  } else {
    mascotInstance.init();
  }

})(window, document);
