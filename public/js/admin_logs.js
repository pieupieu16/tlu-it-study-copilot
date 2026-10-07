/**
 * TLU IT Study Copilot - Admin Infrastructure, Observability & Logs Controller
 * Module: public/js/admin_logs.js
 * Invariant Rule: 100% Light Mode, Zero Icons (no SVG, font icons, emojis).
 */

(function () {
  'use strict';

  class AdminLogsController {
    constructor() {
      this.logsTableBody = document.getElementById('admin-logs-table-body');
      this.dlqTableBody = document.getElementById('admin-dlq-table-body');
      this.logFilterSelect = document.getElementById('admin-log-filter');
      this.btnRefreshLogs = document.getElementById('btn-refresh-admin-logs');

      // FinOps overview cards
      this.budgetDisplay = document.getElementById('admin-finops-budget');
      this.consumedDisplay = document.getElementById('admin-finops-consumed');
      this.cacheRateDisplay = document.getElementById('admin-finops-cache');
      this.marginDisplay = document.getElementById('admin-finops-margin');

      this.currentFilter = 'all';
      this.cachedLogs = null;

      this.init();
    }

    init() {
      if (this.btnRefreshLogs) {
        this.btnRefreshLogs.addEventListener('click', () => {
          this.fetchLogs();
          this.fetchFinops();
        });
      }

      if (this.logFilterSelect) {
        this.logFilterSelect.addEventListener('change', (e) => {
          this.currentFilter = e.target.value;
          this.renderFilteredLogs();
        });
      }

      // Initial load
      this.fetchLogs();
      this.fetchFinops();
    }

    async fetchLogs() {
      try {
        const res = await fetch('/api/admin/logs');
        if (res.ok) {
          const data = await res.json();
          this.cachedLogs = data;
          this.renderFilteredLogs();
          this.renderDLQ(data.dead_letter_queue || []);
        } else {
          this.renderMockLogs();
        }
      } catch (err) {
        this.renderMockLogs();
      }
    }

    async fetchFinops() {
      try {
        const res = await fetch('/api/admin/finops');
        if (res.ok) {
          const data = await res.json();
          this.renderFinops(data);
        } else {
          this.renderMockFinops();
        }
      } catch (err) {
        this.renderMockFinops();
      }
    }

    renderFinops(data) {
      if (this.budgetDisplay) {
        this.budgetDisplay.textContent = `${(data.monthly_budget_vnd || 15000000).toLocaleString('vi-VN')} đ`;
      }
      if (this.consumedDisplay) {
        this.consumedDisplay.textContent = `${(data.consumed_vnd || 6842000).toLocaleString('vi-VN')} đ`;
      }
      if (this.cacheRateDisplay) {
        this.cacheRateDisplay.textContent = `${((data.prompt_cache_hit_rate || 0.684) * 100).toFixed(1)}%`;
      }
      if (this.marginDisplay) {
        const margin = data.subscription_economics ? data.subscription_economics.gross_margin_percent : 54.16;
        this.marginDisplay.textContent = `${margin.toFixed(2)}%`;
      }
    }

    renderMockFinops() {
      this.renderFinops({
        monthly_budget_vnd: 15000000,
        consumed_vnd: 6842000,
        prompt_cache_hit_rate: 0.684,
        subscription_economics: { gross_margin_percent: 54.16 }
      });
    }

    renderFilteredLogs() {
      if (!this.logsTableBody || !this.cachedLogs) return;

      let rows = [];

      // Audit logs
      if (this.currentFilter === 'all' || this.currentFilter === 'audit') {
        (this.cachedLogs.audit_logs || []).forEach((log) => {
          rows.push({
            type: 'AUDIT',
            typeBadge: 'bg-[#EEF4FF] text-[#0D62FE] border-[#BFDBFE]',
            time: log.timestamp,
            target: `${log.student_id} (${log.course})`,
            detail: log.action,
            status: log.status,
            statusClass: 'text-[#16A34A] font-bold'
          });
        });
      }

      // Inference traces
      if (this.currentFilter === 'all' || this.currentFilter === 'inference') {
        (this.cachedLogs.inference_traces || []).forEach((tr) => {
          rows.push({
            type: 'INFERENCE',
            typeBadge: 'bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]',
            time: 'Mới thực thi',
            target: `${tr.provider} • ${tr.model}`,
            detail: `Prompt: ${tr.prompt_tokens} tokens | Comp: ${tr.completion_tokens} tokens`,
            status: `${tr.latency_ms} ms ${tr.cache_hit ? '(Cache Hit)' : ''}`,
            statusClass: 'text-[#0D62FE] font-mono font-bold'
          });
        });
      }

      // Safety guardrail logs
      if (this.currentFilter === 'all' || this.currentFilter === 'safety') {
        (this.cachedLogs.guardrails_safety_logs || []).forEach((gr) => {
          rows.push({
            type: 'SAFETY',
            typeBadge: 'bg-[#F0FDF4] text-[#15803D] border-[#BBF7D0]',
            time: gr.timestamp,
            target: `Mã SV: ${gr.preserved_id}`,
            detail: `Khử CCCD: ${gr.cccd_redacted} | Cờ Điều 25: ${gr.article_25_flag ? 'Bật' : 'Tắt'}`,
            status: gr.verdict,
            statusClass: gr.article_25_flag ? 'text-[#DC2626] font-bold' : 'text-[#16A34A] font-bold'
          });
        });
      }

      if (rows.length === 0) {
        this.logsTableBody.innerHTML = '<tr><td colspan="5" class="py-4 text-center text-xs text-[#64748B] italic">Không tìm thấy bản ghi nhật ký phù hợp.</td></tr>';
        return;
      }

      let html = '';
      rows.forEach((r) => {
        html += `
          <tr class="border-b border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors text-2xs">
            <td class="py-2.5 px-3 font-mono font-bold"><span class="px-1.5 py-0.5 rounded border text-3xs ${r.typeBadge}">${r.type}</span></td>
            <td class="py-2.5 px-3 font-mono text-[#64748B]">${r.time}</td>
            <td class="py-2.5 px-3 font-bold text-[#0F172A]">${r.target}</td>
            <td class="py-2.5 px-3 text-[#475569] font-mono">${r.detail}</td>
            <td class="py-2.5 px-3 ${r.statusClass}">${r.status}</td>
          </tr>
        `;
      });
      this.logsTableBody.innerHTML = html;
    }

    renderDLQ(dlqItems) {
      if (!this.dlqTableBody) return;

      if (!Array.isArray(dlqItems) || dlqItems.length === 0) {
        this.dlqTableBody.innerHTML = '<tr><td colspan="5" class="py-3 text-center text-xs text-[#16A34A] font-semibold">Hàng đợi DLQ trống. Không có tệp lỗi nào cần xử lý lại.</td></tr>';
        return;
      }

      let html = '';
      dlqItems.forEach((d) => {
        html += `
          <tr class="border-b border-[#E2E8F0] hover:bg-[#F8FAFC] text-2xs font-mono">
            <td class="py-2 px-3 font-bold text-[#0D62FE]">${d.dlq_id}</td>
            <td class="py-2 px-3 text-[#64748B]">${d.timestamp}</td>
            <td class="py-2 px-3 text-[#DC2626] font-bold">${d.error_code}</td>
            <td class="py-2 px-3 text-[#0F172A]">${d.source_file}</td>
            <td class="py-2 px-3 text-[#15803D] font-bold">${d.resolved ? 'Đã giải quyết (Resolved)' : 'Cần xử lý'}</td>
          </tr>
        `;
      });
      this.dlqTableBody.innerHTML = html;
    }

    renderMockLogs() {
      const nowStr = new Date().toLocaleTimeString('vi-VN');
      this.cachedLogs = {
        audit_logs: [
          { timestamp: nowStr, student_id: 'A41234', action: 'CHAT_SOCRATIC_QUERY', course: 'IT101', status: '200_OK' },
          { timestamp: nowStr, student_id: 'A38901', action: 'CODE_STUDIO_EXECUTE', course: 'IT201', status: '200_OK' },
          { timestamp: nowStr, student_id: 'A41234', action: 'SLIDE_INGESTION_UPLOAD', course: 'IT101', status: '200_OK' }
        ],
        inference_traces: [
          { provider: 'Groq Cloud', model: 'qwen/qwen3.8-27b', prompt_tokens: 185, completion_tokens: 92, latency_ms: 210.4, cache_hit: true },
          { provider: 'Google Gemini', model: 'gemini-3.5-flash-lite', prompt_tokens: 320, completion_tokens: 140, latency_ms: 680.2, cache_hit: false },
          { provider: 'Groq Cloud', model: 'openai/gpt-oss-120b', prompt_tokens: 410, completion_tokens: 185, latency_ms: 340.8, cache_hit: true }
        ],
        guardrails_safety_logs: [
          { timestamp: nowStr, preserved_id: 'A41234', cccd_redacted: 0, article_25_flag: false, verdict: 'APPROVED' },
          { timestamp: nowStr, preserved_id: 'A38901', cccd_redacted: 1, article_25_flag: false, verdict: 'MASKED_APPROVED' },
          { timestamp: nowStr, preserved_id: 'A41234', cccd_redacted: 0, article_25_flag: true, verdict: 'SOCRATIC_CAUTION_APPLIED' }
        ],
        dead_letter_queue: [
          { dlq_id: 'dlq_001', timestamp: '2026-10-06 13:15:00', error_code: 'ENCODING_CP1258_CORRUPTION', source_file: 'old_assignment_k33.cpp', resolved: true },
          { dlq_id: 'dlq_002', timestamp: '2026-10-06 14:02:10', error_code: 'AST_SYNTAX_PARSE_ERROR', source_file: 'incomplete_lab_snippet.java', resolved: true }
        ]
      };
      this.renderFilteredLogs();
      this.renderDLQ(this.cachedLogs.dead_letter_queue);
    }
  }

  // Mount to window
  window.addEventListener('DOMContentLoaded', () => {
    window.TLUAdminLogs = new AdminLogsController();
  });
})();
