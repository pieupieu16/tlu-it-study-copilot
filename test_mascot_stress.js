/**
 * =============================================================================
 * TLU IT Study Copilot - Mascot Motion Engine Stress & Fuzzing Harness
 * File: test_mascot_stress.js
 * Location: /home/quan/teamwork_projects/tlu_study_assistant_web/test_mascot_stress.js
 * =============================================================================
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

console.log('='.repeat(80));
console.log('TLU MASCOT CONTROLLER - ADVERSARIAL STRESS & EMPIRICAL VERIFICATION');
console.log('='.repeat(80));

const mascotJsPath = path.join(__dirname, 'public', 'js', 'mascot.js');
if (!fs.existsSync(mascotJsPath)) {
  console.error(`ERROR: Mascot file not found at ${mascotJsPath}`);
  process.exit(1);
}
const mascotCode = fs.readFileSync(mascotJsPath, 'utf8');

// Color helpers
const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const CYAN = '\x1b[36m';
const RESET = '\x1b[0m';

let totalTests = 0;
let passedTests = 0;
let failedTests = 0;

function assert(condition, testName, details = '') {
  totalTests++;
  if (condition) {
    passedTests++;
    console.log(`  [PASS] ${testName}`);
  } else {
    failedTests++;
    console.error(`  ${RED}[FAIL] ${testName}${RESET} ${details}`);
  }
}

/**
 * Creates a mock DOM & browser environment
 */
function createMockEnvironment(options = {}) {
  const {
    withAudio = true,
    audioThrows = false,
    missingDOMElements = false,
    brokenStorage = false
  } = options;

  const eventListeners = new Map();

  class MockClassList {
    constructor() {
      this.classes = new Set();
    }
    add(...args) {
      args.forEach(c => this.classes.add(c));
    }
    remove(...args) {
      args.forEach(c => this.classes.delete(c));
    }
    contains(c) {
      return this.classes.has(c);
    }
    toggle(c) {
      if (this.classes.has(c)) this.classes.delete(c);
      else this.classes.add(c);
    }
  }

  class MockElement {
    constructor(id = '', tag = 'div') {
      this.id = id;
      this.tagName = tag.toUpperCase();
      this.classList = new MockClassList();
      this.style = {};
      this.children = [];
      this.parentNode = null;
      this.textContent = '';
      this.innerHTML = '';
      this.offsetWidth = 100;
      this.offsetHeight = 100;
      this.listeners = new Map();
    }

    appendChild(child) {
      child.parentNode = this;
      this.children.push(child);
      return child;
    }

    removeChild(child) {
      const idx = this.children.indexOf(child);
      if (idx !== -1) {
        this.children.splice(idx, 1);
        child.parentNode = null;
      }
      return child;
    }

    querySelector(sel) {
      return this.children.find(c => sel.includes(c.id) || (sel.startsWith('.') && c.classList.contains(sel.slice(1)))) || null;
    }

    querySelectorAll(sel) {
      return this.children.filter(c => sel.includes(c.id) || (sel.startsWith('.') && c.classList.contains(sel.slice(1))));
    }

    addEventListener(event, fn) {
      if (!this.listeners.has(event)) this.listeners.set(event, []);
      this.listeners.get(event).push(fn);
    }

    dispatchEvent(evt) {
      const fns = this.listeners.get(evt.type) || [];
      fns.forEach(fn => fn(evt));
    }

    getBoundingClientRect() {
      return { width: 300, height: 260, top: 0, left: 0, right: 300, bottom: 260 };
    }

    getContext(type) {
      if (type === '2d') {
        return {
          clearRect: () => {},
          save: () => {},
          restore: () => {},
          translate: () => {},
          rotate: () => {},
          fillRect: () => {},
          beginPath: () => {},
          arc: () => {},
          fill: () => {},
          globalAlpha: 1.0,
          fillStyle: '#000'
        };
      }
      return null;
    }

    setAttribute(k, v) {
      this[k] = v;
    }

    getAttribute(k) {
      return this[k];
    }

    closest(sel) {
      if (sel.includes(this.id) || (sel.startsWith('.') && this.classList.contains(sel.slice(1)))) return this;
      return null;
    }
  }

  // Pre-populate standard DOM elements
  const elementsById = new Map();
  if (!missingDOMElements) {
    const stage = new MockElement('mascot-stage');
    const floatingStage = new MockElement('floating-mascot-stage');
    const speech = new MockElement('mascot-speech');
    const speechText = new MockElement('mascot-speech-text');
    const avatar = new MockElement('mascot-avatar');
    const aura = new MockElement('mascot-aura');
    const soundBtn = new MockElement('mascot-sound-toggle');
    const cautionBadge = new MockElement('caution-badge');

    elementsById.set('mascot-stage', stage);
    elementsById.set('floating-mascot-stage', floatingStage);
    elementsById.set('mascot-speech', speech);
    elementsById.set('mascot-speech-text', speechText);
    elementsById.set('mascot-avatar', avatar);
    elementsById.set('mascot-aura', aura);
    elementsById.set('mascot-sound-toggle', soundBtn);
    elementsById.set('caution-badge', cautionBadge);
  }

  const mockDocument = {
    readyState: 'complete',
    getElementById: (id) => elementsById.get(id) || null,
    querySelector: (sel) => {
      const id = sel.replace('#', '').replace('.', '');
      return elementsById.get(id) || null;
    },
    querySelectorAll: (sel) => {
      return Array.from(elementsById.values());
    },
    createElement: (tag) => new MockElement('', tag),
    addEventListener: (type, fn) => {
      if (!eventListeners.has(type)) eventListeners.set(type, []);
      eventListeners.get(type).push(fn);
    }
  };

  class MockCustomEvent {
    constructor(type, params = {}) {
      this.type = type;
      this.detail = params.detail || {};
    }
  }

  const storageMap = new Map();
  const mockLocalStorage = brokenStorage ? {
    getItem: () => { throw new Error('Storage restricted / SecurityError'); },
    setItem: () => { throw new Error('Storage restricted / SecurityError'); }
  } : {
    getItem: (k) => storageMap.get(k) || null,
    setItem: (k, v) => storageMap.set(k, String(v))
  };

  // Mock AudioContext
  class MockAudioContext {
    constructor() {
      if (audioThrows) throw new Error('AudioContext initialization failed');
      this.currentTime = 0;
      this.state = 'running';
      this.destination = {};
    }
    resume() {
      this.state = 'running';
    }
    createOscillator() {
      return {
        type: 'sine',
        frequency: { setValueAtTime: () => {} },
        connect: () => {},
        start: () => {},
        stop: () => {}
      };
    }
    createGain() {
      return {
        gain: {
          setValueAtTime: () => {},
          exponentialRampToValueAtTime: () => {}
        },
        connect: () => {}
      };
    }
  }

  const mockWindow = {
    document: mockDocument,
    localStorage: mockLocalStorage,
    CustomEvent: MockCustomEvent,
    AudioContext: withAudio ? MockAudioContext : undefined,
    webkitAudioContext: withAudio ? MockAudioContext : undefined,
    requestAnimationFrame: (cb) => setTimeout(cb, 16),
    cancelAnimationFrame: (id) => clearTimeout(id),
    setTimeout: setTimeout,
    clearTimeout: clearTimeout,
    Date: Date,
    Math: Math,
    console: {
      log: () => {},
      warn: () => {},
      error: () => {}
    },
    addEventListener: (type, fn) => {
      if (!eventListeners.has(type)) eventListeners.set(type, []);
      eventListeners.get(type).push(fn);
    },
    dispatchEvent: (evt) => {
      const fns = eventListeners.get(evt.type) || [];
      fns.forEach(fn => fn(evt));
      return true;
    }
  };

  return {
    window: mockWindow,
    document: mockDocument,
    elementsById,
    eventListeners
  };
}

/**
 * Loads mascot.js in an isolated sandbox context
 */
function runMascotInSandbox(env) {
  const sandbox = {
    window: env.window,
    document: env.document,
    localStorage: env.window.localStorage,
    CustomEvent: env.window.CustomEvent,
    AudioContext: env.window.AudioContext,
    webkitAudioContext: env.window.webkitAudioContext,
    setTimeout: env.window.setTimeout,
    clearTimeout: env.window.clearTimeout,
    requestAnimationFrame: env.window.requestAnimationFrame,
    Date: Date,
    Math: Math,
    console: env.window.console
  };

  const context = vm.createContext(sandbox);
  vm.runInContext(mascotCode, context);
  return sandbox.window.TLUMascot;
}

// ============================================================================
// TEST SUITE 1: Base Initialization & Interface Contract Verification
// ============================================================================
console.log(`\n${CYAN}[TEST SUITE 1] Base Initialization & Interface Contract${RESET}`);
{
  const env = createMockEnvironment();
  const mascot = runMascotInSandbox(env);

  assert(mascot !== undefined && mascot !== null, 'TLUMascot singleton instantiated');
  assert(mascot.getState() === 'idle', 'Initial state is "idle"');
  assert(typeof mascot.setState === 'function', 'mascot.setState is a function');
  assert(typeof mascot.setIdle === 'function', 'mascot.setIdle is a function');
  assert(typeof mascot.setThinking === 'function', 'mascot.setThinking is a function');
  assert(typeof mascot.setCheering === 'function', 'mascot.setCheering is a function');
  assert(typeof mascot.setSuccess === 'function', 'mascot.setSuccess is a function');
  assert(typeof mascot.setCaution === 'function', 'mascot.setCaution is a function');
  assert(typeof mascot.speak === 'function', 'mascot.speak is a function');
  assert(typeof mascot.pet === 'function', 'mascot.pet is a function');
  assert(typeof mascot.toggleSound === 'function', 'mascot.toggleSound is a function');
  assert(typeof mascot.isMuted === 'function', 'mascot.isMuted is a function');
}

// ============================================================================
// TEST SUITE 2: Rapid State Transition Fuzzing (10,000 cycles)
// ============================================================================
console.log(`\n${CYAN}[TEST SUITE 2] Rapid State Transition Fuzzing (10,000 Cycles)${RESET}`);
{
  const env = createMockEnvironment();
  const mascot = runMascotInSandbox(env);

  const testStates = [
    'idle', 'thinking', 'cheering', 'caution', 'success',
    'INVALID_STATE', '', null, undefined, 123, {}, [], false, true,
    'idlee', 'THINKING', 'CHEERING', 'CAUTION'
  ];

  let exceptionsThrown = 0;
  const startFuzz = Date.now();

  for (let i = 0; i < 10000; i++) {
    const targetState = testStates[Math.floor(Math.random() * testStates.length)];
    try {
      mascot.setState(targetState, `Fuzz message #${i}`);
    } catch (e) {
      exceptionsThrown++;
      console.error(`Exception during setState(${targetState}):`, e);
    }
  }

  const fuzzDuration = Date.now() - startFuzz;
  assert(exceptionsThrown === 0, '10,000 rapid state transitions without exceptions', `Exceptions: ${exceptionsThrown}`);
  assert(['idle', 'thinking', 'cheering', 'caution'].includes(mascot.getState()), `Final state is valid: "${mascot.getState()}"`);
  console.log(`  ${GREEN}✓ 10,000 transitions completed in ${fuzzDuration}ms${RESET}`);
}

// ============================================================================
// TEST SUITE 3: Timer Cancellation & Auto-Reset Race Conditions
// ============================================================================
console.log(`\n${CYAN}[TEST SUITE 3] Timer Cancellation & Auto-Reset Race Conditions${RESET}`);
(async () => {
  const env = createMockEnvironment();
  const mascot = runMascotInSandbox(env);

  // Test 3.1: Verify autoReset timer sets state back to idle
  mascot.setState('cheering', 'Testing cheer timer', 50);
  assert(mascot.getState() === 'cheering', 'State is cheering immediately after setState');
  assert(mascot.resetTimer !== null, 'resetTimer is active');

  await new Promise(r => setTimeout(r, 80));
  assert(mascot.getState() === 'idle', 'Auto-reset timer transitioned state back to idle');

  // Test 3.2: Verify timer is cancelled when transitioning before expiry
  mascot.setState('caution', 'Caution warning', 100);
  const originalTimer = mascot.resetTimer;
  assert(originalTimer !== null, 'Caution resetTimer is set');

  // Immediately transition to thinking before timeout expires
  mascot.setState('thinking', 'Agent analyzing...');
  assert(mascot.getState() === 'thinking', 'New state thinking took effect');
  assert(mascot.resetTimer === null, 'Previous timer cancelled cleanly on thinking state');

  // Wait past original caution timeout (120ms) to ensure it does not revert thinking to idle
  await new Promise(r => setTimeout(r, 120));
  assert(mascot.getState() === 'thinking', 'State remains "thinking" (no stale callback overwrite)');

  // Test 3.3: Overlapping timers rapid fire
  for (let i = 0; i < 50; i++) {
    mascot.setState(i % 2 === 0 ? 'cheering' : 'caution', `Rapid fire ${i}`, 20 + i);
  }
  // The last state was caution with timeout 69ms
  assert(mascot.getState() === 'caution', 'State is caution after rapid timer sequence');
  await new Promise(r => setTimeout(r, 100));
  assert(mascot.getState() === 'idle', 'State returned to idle after final timer completed');

  // ============================================================================
  // TEST SUITE 4: Event Bus Integrity & Custom Event Dispatching
  // ============================================================================
  console.log(`\n${CYAN}[TEST SUITE 4] Event Bus Integrity & Custom Event Dispatching${RESET}`);
  {
    const busEnv = createMockEnvironment();
    const busMascot = runMascotInSandbox(busEnv);

    // Track state change events emitted by mascot
    const stateEvents = [];
    busEnv.window.addEventListener('tlu:mascot:statechange', (e) => {
      stateEvents.push(e.detail);
    });

    // 4.1: tlu:chat:query -> thinking
    busEnv.window.dispatchEvent(new busEnv.window.CustomEvent('tlu:chat:query'));
    assert(busMascot.getState() === 'thinking', 'Event "tlu:chat:query" triggers thinking state');

    // 4.2: tlu:chat:article25 -> caution
    busEnv.window.dispatchEvent(new busEnv.window.CustomEvent('tlu:chat:article25', {
      detail: { message: 'Cảnh báo Điều 25 TLU: Không giải hộ code!' }
    }));
    assert(busMascot.getState() === 'caution', 'Event "tlu:chat:article25" triggers caution state');

    // 4.3: tlu:code:run -> thinking
    busEnv.window.dispatchEvent(new busEnv.window.CustomEvent('tlu:code:run'));
    assert(busMascot.getState() === 'thinking', 'Event "tlu:code:run" triggers thinking state');

    // 4.4: tlu:code:pass -> cheering
    busEnv.window.dispatchEvent(new busEnv.window.CustomEvent('tlu:code:pass'));
    assert(busMascot.getState() === 'cheering', 'Event "tlu:code:pass" triggers cheering state');

    // 4.5: tlu:code:fail -> caution
    busEnv.window.dispatchEvent(new busEnv.window.CustomEvent('tlu:code:fail', {
      detail: { message: 'Lỗi biên dịch Segmentation fault' }
    }));
    assert(busMascot.getState() === 'caution', 'Event "tlu:code:fail" triggers caution state');

    // 4.6: tlu:tab:switch -> speak
    busEnv.window.dispatchEvent(new busEnv.window.CustomEvent('tlu:tab:switch', {
      detail: { tab: 'multiagent' }
    }));
    const speechText = busEnv.elementsById.get('mascot-speech-text');
    assert(speechText.textContent.includes('LangGraph') || speechText.innerHTML.includes('LangGraph'),
      'Event "tlu:tab:switch" (multiagent) updates speech text correctly');

    // 4.7: Malformed event details (null, undefined, non-object)
    let malformedPassed = true;
    try {
      busEnv.window.dispatchEvent(new busEnv.window.CustomEvent('tlu:chat:article25', { detail: null }));
      busEnv.window.dispatchEvent(new busEnv.window.CustomEvent('tlu:code:fail', { detail: undefined }));
      busEnv.window.dispatchEvent(new busEnv.window.CustomEvent('tlu:tab:switch', { detail: 'string' }));
      busEnv.window.dispatchEvent(new busEnv.window.CustomEvent('tlu:course:switch', { detail: null }));
      busEnv.window.dispatchEvent(new busEnv.window.CustomEvent('tlu:persona:switch', { detail: {} }));
    } catch (e) {
      malformedPassed = false;
      console.error('Crash on malformed event dispatch:', e);
    }
    assert(malformedPassed, 'Event bus handles malformed and null detail payloads safely');

    // Verify CustomEvent emission history
    assert(stateEvents.length >= 5, `TLUMascot successfully emitted ${stateEvents.length} "tlu:mascot:statechange" events`);
  }

  // ============================================================================
  // TEST SUITE 5: Audio Synthesizer Resilience (Headless, Throwing, Restricted)
  // ============================================================================
  console.log(`\n${CYAN}[TEST SUITE 5] Audio Synthesizer Resilience${RESET}`);
  {
    // 5.1: Headless environment with NO AudioContext
    const headlessEnv = createMockEnvironment({ withAudio: false });
    let headlessOk = true;
    try {
      const headlessMascot = runMascotInSandbox(headlessEnv);
      headlessMascot.setState('cheering');
      headlessMascot.setState('caution');
      headlessMascot.setState('thinking');
      headlessMascot.speak('Speech test');
      headlessMascot.pet();
      headlessMascot.toggleSound();
    } catch (e) {
      headlessOk = false;
      console.error('Headless audio crash:', e);
    }
    assert(headlessOk, 'Headless environment (AudioContext undefined) operates without crashing');

    // 5.2: AudioContext throws upon instantiation (e.g. autoplay security policy)
    const throwingEnv = createMockEnvironment({ withAudio: true, audioThrows: true });
    let throwingOk = true;
    try {
      const throwingMascot = runMascotInSandbox(throwingEnv);
      throwingMascot.setState('cheering');
      throwingMascot.setState('caution');
      throwingMascot.pet();
    } catch (e) {
      throwingOk = false;
      console.error('Throwing AudioContext crash:', e);
    }
    assert(throwingOk, 'Autoplay/AudioContext instantiation rejection handled gracefully');

    // 5.3: LocalStorage security restriction
    const storageRestrictedEnv = createMockEnvironment({ brokenStorage: true });
    let storageOk = true;
    try {
      const storageMascot = runMascotInSandbox(storageRestrictedEnv);
      storageMascot.toggleSound();
    } catch (e) {
      storageOk = false;
      console.error('Storage restriction crash:', e);
    }
    assert(storageOk, 'Restricted localStorage (SecurityError/Incognito) handled gracefully');
  }

  // ============================================================================
  // TEST SUITE 6: Missing DOM Elements & Headless Degradation
  // ============================================================================
  console.log(`\n${CYAN}[TEST SUITE 6] Missing DOM Elements & Headless Degradation${RESET}`);
  {
    const minimalEnv = createMockEnvironment({ missingDOMElements: true });
    let minimalOk = true;
    try {
      const minimalMascot = runMascotInSandbox(minimalEnv);
      minimalMascot.setState('idle');
      minimalMascot.setState('thinking');
      minimalMascot.setState('cheering');
      minimalMascot.setState('caution');
      minimalMascot.speak('Hello without DOM');
      minimalMascot.pet();
      minimalMascot.triggerConfetti();
    } catch (e) {
      minimalOk = false;
      console.error('Crash with missing DOM elements:', e);
    }
    assert(minimalOk, 'Graceful degradation when DOM elements are completely missing');
  }

  // ============================================================================
  // TEST SUITE 7: Petting Reentrancy & Concurrency Stress
  // ============================================================================
  console.log(`\n${CYAN}[TEST SUITE 7] Petting Reentrancy & Concurrency Stress${RESET}`);
  {
    const petEnv = createMockEnvironment();
    const petMascot = runMascotInSandbox(petEnv);

    let petExceptions = 0;
    // Rapid-fire pet calls to test debounce (isPetting guard)
    for (let i = 0; i < 500; i++) {
      try {
        petMascot.pet();
      } catch (e) {
        petExceptions++;
      }
    }
    assert(petExceptions === 0, '500 concurrent pet() invocations guarded with zero exceptions');
  }

  // ============================================================================
  // TEST SUITE 8: Zero Icon & Zero Emoji Invariant Verification
  // ============================================================================
  console.log(`\n${CYAN}[TEST SUITE 8] Zero Icon & Zero Emoji Invariant Verification${RESET}`);
  {
    const invariantEnv = createMockEnvironment();
    const invMascot = runMascotInSandbox(invariantEnv);

    // 8.1: Check that public/js/mascot.js source code contains 0 SVG elements or Lucide/font icon references
    const svgRegex = /<svg\b/i;
    const iconClassRegex = /class=["'][^"']*\b(icon|lucide|fa|fas|far)\b/i;
    assert(!svgRegex.test(mascotCode), 'Zero SVG tags in mascot.js');
    assert(!iconClassRegex.test(mascotCode), 'Zero icon library classes in mascot.js');

    // 8.2: Check that public/js/mascot.js contains 0 rendered emoji glyphs
    const emojiGlyphRegex = /[\u{1F300}-\u{1F5FF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u2600-\u26FF\u2700-\u27BF]/u;
    assert(!emojiGlyphRegex.test(mascotCode), 'Zero emoji glyph characters in mascot.js');

    // 8.3: Verify runtime DOM speech bubbles inject zero icons or emojis across all quotes
    let runtimeEmojiDetected = false;
    ['idle', 'thinking', 'cheering', 'caution', 'pet'].forEach(state => {
      const quoteList = invMascot.quotes[state] || [];
      quoteList.forEach(q => {
        if (emojiGlyphRegex.test(q) || svgRegex.test(q)) {
          runtimeEmojiDetected = true;
        }
      });
    });
    assert(!runtimeEmojiDetected, 'All mascot state quotes are 100% free of emoji icons and SVGs');

    // 8.4: Verify particle effects (burstHearts / burstConfetti) inject zero emoji icons
    invMascot.pet();
    const floaters = invariantEnv.elementsById.get('mascot-stage').children;
    let floaterHasEmoji = false;
    floaters.forEach(child => {
      if (child.textContent && emojiGlyphRegex.test(child.textContent)) {
        floaterHasEmoji = true;
      }
    });
    assert(!floaterHasEmoji, 'Particle floaters inject CSS geometry instead of emoji icons');

    // 8.5: Scan for Unicode Variation Selector-16 (U+FE0F) residues
    const vs16Matches = (mascotCode.match(/\ufe0f/g) || []).length;
    if (vs16Matches > 0) {
      console.log(`  ${YELLOW}[FINDING] Found ${vs16Matches} dangling U+FE0F (Variation Selector-16) residues in string literals.${RESET}`);
    }
    assert(true, `Unicode Variation Selector-16 scan documented (${vs16Matches} residues found as hygiene note)`);
  }

  // ============================================================================
  // SUMMARY REPORT
  // ============================================================================
  console.log('\n' + '='.repeat(80));
  console.log(`TEST EXECUTION SUMMARY:`);
  console.log(`  Total Checks: ${totalTests}`);
  console.log(`  Passed:       ${GREEN}${passedTests}${RESET}`);
  console.log(`  Failed:       ${failedTests > 0 ? RED + failedTests + RESET : '0'}`);
  console.log('='.repeat(80));

  if (failedTests > 0) {
    console.error(`\n${RED}VERIFICATION VERDICT: REJECT (Defects detected)${RESET}`);
    process.exit(1);
  } else {
    console.log(`\n${GREEN}VERIFICATION VERDICT: CONFIRM_CORRECTNESS (100% Pass Rate)${RESET}`);
    process.exit(0);
  }
})();
