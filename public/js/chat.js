/**
 * TLU IT Study Copilot - Socratic Tutoring Chat Engine
 * Module: public/js/chat.js
 * Invariant Rule: 100% Light Mode, Zero Icons (no SVG, font icons, emojis).
 */

(function () {
  'use strict';

  class SocraticChatEngine {
    constructor() {
      this.messagesContainer = document.getElementById('chat-messages');
      this.chatForm = document.getElementById('chat-form');
      this.chatInput = document.getElementById('chat-input');
      this.btnSend = document.getElementById('btn-chat-send');
      this.btnClear = document.getElementById('btn-clear-chat');
      this.courseSelect = document.getElementById('course-select');
      this.personaSelect = document.getElementById('persona-select');
      this.activeCourseLabel = document.getElementById('chat-active-course-label');

      this.currentCourse = (this.courseSelect && this.courseSelect.value) ? this.courseSelect.value : 'DATASCIENCE';
      this.currentPersona = {
        name: 'Nguyễn Văn An',
        id: 'A41234',
        class: 'K35'
      };

      this.conversationHistory = [];
      this.init();
    }

    init() {
      if (this.courseSelect) {
        this.courseSelect.addEventListener('change', (e) => this.handleCourseChange(e.target.value));
      }

      if (this.personaSelect) {
        this.personaSelect.addEventListener('change', (e) => this.handlePersonaChange(e.target.value));
      }

      if (this.chatForm) {
        this.chatForm.addEventListener('submit', (e) => {
          e.preventDefault();
          this.handleSendMessage();
        });
      }

      if (this.btnClear) {
        this.btnClear.addEventListener('click', () => this.clearChat());
      }

      // Quick prompt buttons if present
      document.querySelectorAll('.btn-quick-prompt, .chip-btn').forEach((btn) => {
        btn.addEventListener('click', (e) => {
          const text = e.target.getAttribute('data-prompt') || e.target.textContent;
          if (this.chatInput) {
            this.chatInput.value = text.trim();
            this.chatInput.focus();
          }
        });
      });
    }

    handleCourseChange(courseCode) {
      this.currentCourse = courseCode;
      if (this.activeCourseLabel) {
        this.activeCourseLabel.textContent = `Môn hiện tại: ${courseCode}`;
      }
      if (window.TLUMascot) {
        window.TLUMascot.onCourseChange(courseCode);
      }
      // Notify code playground
      if (window.TLUPlayground && typeof window.TLUPlayground.setCourse === 'function') {
        window.TLUPlayground.setCourse(courseCode);
      }
    }

    handlePersonaChange(personaId) {
      if (personaId === 'A41234') {
        this.currentPersona = { name: 'Nguyễn Văn An', id: 'A41234', class: 'K35' };
      } else {
        this.currentPersona = { name: 'Trần Mai Linh', id: 'A38901', class: 'K34' };
      }
      if (window.TLUMascot) {
        window.TLUMascot.onPersonaChange(this.currentPersona.name, this.currentPersona.class);
      }
    }

    async handleSendMessage() {
      const text = this.chatInput ? this.chatInput.value.trim() : '';
      if (!text) return;

      // Append user message
      this.appendUserMessage(text);
      if (this.chatInput) this.chatInput.value = '';

      // Set Mascot to thinking state
      if (window.TLUMascot) {
        window.TLUMascot.setThinking('Đang kích hoạt quy trình phân tích Socratic đa tác tử...');
      }

      // Code context if any
      const codeContext = window.TLUPlayground && typeof window.TLUPlayground.getCode === 'function'
        ? window.TLUPlayground.getCode()
        : null;

      try {
        const payload = {
          course_code: this.currentCourse,
          student_id: this.currentPersona.id,
          message: text,
          code_context: codeContext
        };

        const response = await fetch('/api/chat/socratic', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (response.ok) {
          const data = await response.json();
          this.appendAssistantMessage(data);

          // Update mascot state according to response
          if (window.TLUMascot) {
            if (data.article_25_triggered) {
              window.TLUMascot.setCaution(data.mascot_message || 'Quy chế Điều 25 TLU: Không giải hộ bài tập lớn!');
            } else if (data.mascot_state === 'cheering') {
              window.TLUMascot.setCheering(data.mascot_message || 'Lời giải logic chính xác!');
            } else {
              window.TLUMascot.setIdle(data.mascot_message || 'Đã phân tích xong câu hỏi Socratic của bạn.');
            }
          }
        } else {
          throw new Error(`HTTP error: ${response.status}`);
        }
      } catch (err) {
        console.warn('API fallback to local simulation:', err);
        // Fallback local Socratic simulation
        this.simulateLocalSocraticReply(text);
      }
    }

    appendUserMessage(text) {
      if (!this.messagesContainer) return;

      const msgDiv = document.createElement('div');
      msgDiv.className = 'flex flex-col items-end mb-4';

      const meta = document.createElement('div');
      meta.className = 'text-2xs text-[#64748B] mb-1 font-semibold';
      meta.textContent = `${this.currentPersona.name} (${this.currentPersona.id}) • ${new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}`;

      const bubble = document.createElement('div');
      bubble.className = 'bg-[#0D62FE] text-white text-xs rounded-2xl rounded-tr-xs px-4 py-2.5 max-w-[85%] shadow-xs leading-relaxed whitespace-pre-wrap';
      bubble.textContent = text;

      msgDiv.appendChild(meta);
      msgDiv.appendChild(bubble);
      this.messagesContainer.appendChild(msgDiv);
      this.scrollToBottom();
    }

    appendAssistantMessage(data) {
      if (!this.messagesContainer) return;

      const msgDiv = document.createElement('div');
      msgDiv.className = 'flex flex-col items-start mb-4';

      const meta = document.createElement('div');
      meta.className = 'text-2xs text-[#0D62FE] mb-1 font-bold';
      let metaText = `Gia Sư Socratic TLU (${this.currentCourse}) • ${new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}`;
      if (data.provider_used && data.model_used) {
        metaText += ` • [Động cơ: ${data.provider_used.toUpperCase()} (${data.model_used}) - ${data.latency_ms || 0}ms]`;
      }
      meta.textContent = metaText;

      const card = document.createElement('div');
      card.className = 'bg-white border border-[#CBD5E1] rounded-2xl rounded-tl-xs p-4 max-w-[90%] shadow-xs space-y-3';

      // Article 25 badge if triggered
      if (data.article_25_triggered) {
        const warning = document.createElement('div');
        warning.className = 'bg-[#FEF2F2] border border-[#FCA5A5] text-[#991B1B] text-xs font-bold px-3 py-1.5 rounded-lg';
        warning.textContent = '[Cảnh Báo Điều 25 Quy Chế Đào Tạo TLU]: Hệ thống từ chối viết hộ toàn bộ code nộp chấm điểm. Chuyển sang hướng dẫn gợi mở tư duy từng bước.';
        card.appendChild(warning);
      }

      // Thinking summary
      if (data.thinking) {
        const thinkingBox = document.createElement('div');
        thinkingBox.className = 'bg-[#F8FAFC] border-l-2 border-[#0D62FE] px-3 py-2 text-2xs text-[#475569] rounded-r-md';
        thinkingBox.innerHTML = `<span class="font-bold text-[#0F172A]">[Phân Tích Sư Phạm]:</span> ${this.escapeHtml(data.thinking)}`;
        card.appendChild(thinkingBox);
      }

      // Main Reply Text
      const replyBody = document.createElement('div');
      replyBody.className = 'text-xs text-[#0F172A] leading-relaxed whitespace-pre-wrap';
      replyBody.textContent = data.reply || data.response?.summary || '';
      card.appendChild(replyBody);

      // Socratic Steps list
      const steps = data.socratic_steps || data.response?.socratic_steps;
      if (Array.isArray(steps) && steps.length > 0) {
        const stepsContainer = document.createElement('div');
        stepsContainer.className = 'bg-[#EEF4FF] border border-[#BFDBFE] rounded-xl p-3 space-y-2';

        const stepsTitle = document.createElement('div');
        stepsTitle.className = 'text-xs font-bold text-[#0D62FE] tracking-wide uppercase';
        stepsTitle.textContent = 'Các Bước Gợi Mở Tư Duy:';
        stepsContainer.appendChild(stepsTitle);

        steps.forEach((step, idx) => {
          const stepItem = document.createElement('div');
          stepItem.className = 'text-xs text-[#1E293B] pl-2 border-l border-[#93C5FD]';
          if (typeof step === 'string') {
            stepItem.textContent = `${idx + 1}. ${step}`;
          } else {
            stepItem.innerHTML = `<strong class="text-[#0D62FE]">${step.title || `Bước ${step.step_number || idx + 1}`}:</strong> ${this.escapeHtml(step.guidance || '')}`;
          }
          stepsContainer.appendChild(stepItem);
        });
        card.appendChild(stepsContainer);
      }

      // Citations / Breadcrumbs
      const citations = data.citations || data.response?.citations;
      if (Array.isArray(citations) && citations.length > 0) {
        const citeBox = document.createElement('div');
        citeBox.className = 'pt-2 border-t border-[#E2E8F0] flex flex-wrap items-center gap-2';

        const citeLabel = document.createElement('span');
        citeLabel.className = 'text-2xs font-bold text-[#64748B] uppercase';
        citeLabel.textContent = 'Trích dẫn slide chính khóa:';
        citeBox.appendChild(citeLabel);

        citations.forEach((c) => {
          const btnCite = document.createElement('button');
          btnCite.className = 'px-2 py-0.5 bg-[#F1F5F9] hover:bg-[#E2E8F0] text-[#0D62FE] text-2xs font-semibold rounded border border-[#CBD5E1] transition-colors';
          btnCite.textContent = c.breadcrumb || `${c.course_code || this.currentCourse} > Tuần ${c.week || 1} > Slide ${c.slide_number || 1}`;
          btnCite.addEventListener('click', () => {
            if (window.TLUApp && typeof window.TLUApp.openSlideModal === 'function') {
              window.TLUApp.openSlideModal(c);
            }
          });
          citeBox.appendChild(btnCite);
        });
        card.appendChild(citeBox);
      }

      msgDiv.appendChild(meta);
      msgDiv.appendChild(card);
      this.messagesContainer.appendChild(msgDiv);
      this.scrollToBottom();
    }

    simulateLocalSocraticReply(userText) {
      const lower = (userText || '').trim().toLowerCase();
      const isTurnkey = /viết hộ|giải hộ|làm hộ|cho xin full code/i.test(lower);
      const isGreeting = /^(hi|hello|hey|chào|xin chào|alo|hế lô|hê lô|bạn là ai|cho mình hỏi|cho em hỏi)\b/i.test(lower) || /^(chào|hello|hi|alo)[\s!\.,\?]*$/i.test(lower);

      const itKeywords = ['con trỏ', 'pointer', 'mảng', 'hàm', 'lỗi', 'segfault', 'bộ nhớ', 'c++', 'c', 'java', 'sql', 'python', 'danh sách', 'cây', 'đồ thị', 'database', 'mạng', 'cpu', 'it101', 'it201', 'it205', 'it301', 'it315'];
      const isOffTopic = !isGreeting && !isTurnkey && !itKeywords.some(kw => lower.includes(kw)) && lower.split(/\s+/).length >= 3;

      let replyData;

      if (isTurnkey) {
        replyData = {
          article_25_triggered: true,
          mascot_state: 'caution',
          mascot_message: 'Rồng TLU nhắc bạn: Tuân thủ Điều 25 Quy chế TLU, chúng ta chỉ gợi ý từng bước nhé!',
          thinking: 'Phát hiện yêu cầu giải hộ bài tập vi phạm Điều 25. Kích hoạt Socratic Invariant.',
          reply: `Chào bạn ${this.currentPersona.name}, theo Điều 25 Quy chế Đào tạo TLU về Liêm chính Học thuật, hệ thống không sinh toàn bộ bài giải bài tập lớn. Tuy nhiên, mình sẽ đồng hành cùng bạn phân tích từng dòng logic.`,
          socratic_steps: [
            { title: 'Bước 1: Xác định bài toán', guidance: 'Đọc kỹ đề bài và xác định yêu cầu đầu vào / đầu ra.' },
            { title: 'Bước 2: Lựa chọn cấu trúc dữ liệu', guidance: 'Chọn cấu trúc dữ liệu phù hợp mà không phụ thuộc code mẫu.' },
            { title: 'Bước 3: Tự thiết kế giải thuật', guidance: 'Từng bước triển khai thuật toán độc lập.' }
          ],
          citations: [
            {
              course_code: this.currentCourse,
              breadcrumb: `${this.currentCourse} > Quy chế > Điều 25 > Liêm chính học thuật`,
              snippet: 'Sinh viên phải tự mình hoàn thành bài tập, nghiêm cấm sao chép lời giải hoàn chỉnh.'
            }
          ]
        };
      } else if (isGreeting) {
        replyData = {
          article_25_triggered: false,
          mascot_state: 'cheering',
          mascot_message: 'Chào mừng bạn đến với buổi ôn tập CNTT TLU!',
          thinking: `Sinh viên ${this.currentPersona.name} gửi lời chào xã giao. Guardrails chấp thuận (APPROVED). Chào đón nhiệt tình và định hướng môn ${this.currentCourse}.`,
          reply: `Chào bạn ${this.currentPersona.name}! Mình là Trợ lý Học tập Socratic của Khoa CNTT - Đại học Thăng Long (TLU). Rất vui được đồng hành cùng bạn ôn luyện môn ${this.currentCourse}. Hôm nay bạn đang học phần nào và cần hỗ trợ giải đáp hay gỡ lỗi code gì không?`,
          socratic_steps: [
            { title: 'Bước 1: Chọn chủ đề thảo luận', guidance: `Nêu chủ đề hoặc bài tập trong môn ${this.currentCourse} bạn đang làm.` },
            { title: 'Bước 2: Cung cấp mã nguồn hoặc lỗi', guidance: 'Chia sẻ đoạn code hoặc thông báo lỗi nếu có.' },
            { title: 'Bước 3: Cùng gia sư Socratic bóc tách logic', guidance: 'Chúng ta sẽ phân tích từng bước để thấu hiểu bản chất.' }
          ],
          citations: [
            {
              course_code: this.currentCourse,
              breadcrumb: `${this.currentCourse} > Giới thiệu môn học > Đề cương học phần`,
              snippet: `Chào mừng sinh viên ${this.currentPersona.id} đến với môn học ${this.currentCourse}. Trợ lý Socratic luôn sẵn sàng đồng hành.`
            }
          ]
        };
      } else if (isOffTopic) {
        replyData = {
          article_25_triggered: false,
          mascot_state: 'idle',
          mascot_message: 'Cùng tập trung vào các môn học CNTT TLU nhé!',
          thinking: `Câu hỏi ngoài lề môn học CNTT TLU. Guardrails chấp thuận (APPROVED) không chặn. Phản hồi lịch sự và điều hướng quay lại môn ${this.currentCourse}.`,
          reply: `Chào bạn ${this.currentPersona.name}! Mình là Trợ lý Học tập Socratic chuyên biệt cho các môn học CNTT tại Đại học Thăng Long. Câu hỏi này nằm ngoài phạm vi học tập, chúng ta hãy cùng tập trung vào các bài tập lập trình hoặc lý thuyết môn ${this.currentCourse} nhé!`,
          socratic_steps: [
            { title: 'Bước 1: Xác định mục tiêu buổi học', guidance: `Tập trung vào nội dung kiến thức môn ${this.currentCourse}.` },
            { title: 'Bước 2: Đặt câu hỏi chuyên môn', guidance: 'Hỏi về cú pháp, giải thuật hoặc bài thực hành lab.' },
            { title: 'Bước 3: Giải quyết vấn đề kỹ thuật', guidance: 'Từng bước rèn luyện tư duy lập trình vững chắc.' }
          ],
          citations: [
            {
              course_code: this.currentCourse,
              breadcrumb: `${this.currentCourse} > Phương pháp học tập > Tập trung kiến thức trọng tâm`,
              snippet: 'Khuyến khích sinh viên tập trung vào các kỹ năng lập trình và thực hành lab.'
            }
          ]
        };
      } else {
        replyData = {
          article_25_triggered: false,
          mascot_state: 'thinking',
          mascot_message: 'Đang xem xét bản chất logic và slide học liệu...',
          thinking: `Khảo sát lỗi ngữ nghĩa và bối cảnh môn ${this.currentCourse}. Áp dụng phương pháp gợi mở không giải thay.`,
          reply: `Để giải quyết vấn đề "${userText.slice(0, 40)}...", bạn hãy cùng mình xem xét cấu trúc điều khiển và địa chỉ bộ nhớ tương ứng.`,
          socratic_steps: [
            { title: 'Bước 1: Xác định biến đầu vào', guidance: 'Kiểm tra kiểu dữ liệu và phạm vi hợp lệ của biến trước khi thực thi.' },
            { title: 'Bước 2: Phân tích điều kiện rẽ nhánh', guidance: 'Đặt câu hỏi: Điều kiện dừng của vòng lặp hoặc lệnh if đã bao quát trường hợp biên chưa?' },
            { title: 'Bước 3: Tự viết thử nghiệm', guidance: 'Sử dụng Code Playground bên phải để chạy thử đoạn mã nhỏ tối thiểu.' }
          ],
          citations: [
            {
              course_code: this.currentCourse,
              week: 3,
              slide_number: 14,
              breadcrumb: `${this.currentCourse} > Tuần 03 > Bài giảng chính khóa > Slide 14`,
              title: 'Kỹ thuật lập trình và cấu trúc dữ liệu cơ sở',
              snippet: 'Quy tắc thực hành lab: Luôn khởi tạo giá trị trước khi sử dụng và kiểm tra điều kiện con trỏ khác NULL.'
            }
          ]
        };
      }

      setTimeout(() => {
        this.appendAssistantMessage(replyData);
        if (window.TLUMascot) {
          window.TLUMascot.setState(replyData.mascot_state, replyData.mascot_message);
        }
      }, 500);
    }

    clearChat() {
      if (!this.messagesContainer) return;
      this.messagesContainer.innerHTML = '';
      const notice = document.createElement('div');
      notice.className = 'text-center text-xs text-[#94A3B8] my-4 italic';
      notice.textContent = 'Cuộc trò chuyện đã được làm mới. Hãy chọn môn học và nhập câu hỏi của bạn.';
      this.messagesContainer.appendChild(notice);
      if (window.TLUMascot) {
        window.TLUMascot.setIdle('Cuộc trò chuyện mới đã bắt đầu. Cùng ôn bài nào!');
      }
    }

    scrollToBottom() {
      if (this.messagesContainer) {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
      }
    }

    escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }
  }

  // Mount to window
  window.addEventListener('DOMContentLoaded', () => {
    window.TLUChat = new SocraticChatEngine();
  });
})();
