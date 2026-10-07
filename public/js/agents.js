/**
 * TLU IT Study Copilot - Live Multi-Agent Workflow Visualizer
 * Module: public/js/agents.js
 * Invariant Rule: 100% Light Mode, Zero Icons (no SVG, font icons, emojis).
 */

(function () {
  'use strict';

  class MultiAgentVisualizer {
    constructor() {
      this.container = document.getElementById('workspace-multiagent');
      this.init();
    }

    init() {
      // Load initial workflow data
      this.fetchWorkflowState();

      // Listen for tab activation
      document.addEventListener('tab-activated', (e) => {
        if (e.detail && e.detail.tabId === 'tab-btn-multiagent') {
          this.fetchWorkflowState();
        }
      });
    }

    async fetchWorkflowState() {
      try {
        const response = await fetch('/api/multi-agent/workflow');
        if (response.ok) {
          const data = await response.json();
          this.renderWorkflow(data);
        } else {
          this.renderLocalWorkflow();
        }
      } catch (err) {
        this.renderLocalWorkflow();
      }
    }

    renderWorkflow(data) {
      const activeWorker = data.active_worker || 'Code Debugger Worker';
      const studentId = data.student_id || 'A41234';
      const course = data.course_code || 'IT101';

      // Update Node 1
      const n1 = document.getElementById('flow-node-supervisor');
      if (n1) {
        n1.querySelector('.node-status')?.replaceChildren(this.createTextBadge('Đang hoạt động', 'bg-[#DCFCE7] text-[#166534]'));
      }

      // Update Node 2
      const n2 = document.getElementById('flow-node-worker');
      if (n2) {
        const title = n2.querySelector('.node-title');
        if (title) title.textContent = activeWorker;
      }

      // Update Memory Counters
      const workingMem = document.getElementById('mem-working-tokens');
      if (workingMem) workingMem.textContent = `${data.working_memory_tokens || 420} tokens`;

      const sessionMem = document.getElementById('mem-session-turns');
      if (sessionMem) sessionMem.textContent = `${data.session_turns || 4} lượt`;

      const declMem = document.getElementById('mem-student-profile');
      if (declMem) declMem.textContent = `Hồ sơ: ${studentId} (${course})`;
    }

    renderLocalWorkflow() {
      this.renderWorkflow({
        active_worker: 'Code Debugger Worker (IT101)',
        student_id: 'A41234',
        course_code: 'IT101',
        working_memory_tokens: 385,
        session_turns: 3
      });
    }

    createTextBadge(text, colorClasses) {
      const span = document.createElement('span');
      span.className = `text-3xs font-bold uppercase tracking-wider px-2 py-0.5 rounded border border-current ${colorClasses}`;
      span.textContent = text;
      return span;
    }
  }

  window.addEventListener('DOMContentLoaded', () => {
    window.TLUAgents = new MultiAgentVisualizer();
  });
})();
