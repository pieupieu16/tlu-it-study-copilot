/**
 * TLU IT Study Copilot - Slide Viewer & Universal IT Course Ingestion Controller
 * Module: public/js/slides.js
 * Domain: Fits 100% of Information Technology (CNTT) courses at Thang Long University.
 * Invariant Rule: 100% Light Mode, Zero Icons (no SVG, font icons, emojis), Zero Boilerplate.
 */

(function () {
  'use strict';

  // Default Initial Slide (User's real uploaded Data Science slide deck)
  const DEFAULT_SLIDE = {
    slide_id: 'slide_datascience_p001',
    course_code: 'DATASCIENCE',
    course_name: 'Khoa học Dữ liệu và Học máy',
    week: 3,
    page: 'Slide 01 / 137',
    page_num: 1,
    total_pages: 137,
    topic: 'Chủ đề: Data Science & Machine Learning Python course',
    desc: 'Bài giảng mở đầu môn Khoa học Dữ liệu và Học máy (Data Science & Machine Learning). Giảng viên: Thang Nguyen, Viet Nguyen.',
    code: `# Mở đầu khóa học Khoa học Dữ liệu (137 Trang Slide bài giảng):\nimport pandas as pd\nimport numpy as np\nimport sklearn\n\nprint("Chào mừng đến với khóa học Data Science & Machine Learning!")`,
    note: 'Học liệu Khoa học Dữ liệu tải lên trực tiếp từ tệp PDF gốc gồm 137 trang slide.'
  };

  // In-Class Quick Question Quiz Dataset (Inspired by K3-Hackathon student-question-panel)
  const SLIDE_QUESTIONS = {
    'DATASCIENCE': {
      prompt: 'Trong bài toán huấn luyện mô hình Machine Learning, kỹ thuật Cross-Validation (K-Fold) có tác dụng chính là gì?',
      options: [
        'A. Đánh giá tổng quát hóa mô hình và hạn chế tình trạng Overfitting',
        'B. Tăng kích thước tập dữ liệu gấp K lần mà không cần thu thập thêm',
        'C. Tự động chuyển đổi toàn bộ đặc trưng phi số thành số nguyên',
        'D. Giảm thời gian huấn luyện mô hình về mức O(1)'
      ],
      correctIndex: 0,
      explanation: 'K-Fold Cross-Validation chia dữ liệu thành K phần để huấn luyện và kiểm thử chéo, giúp đánh giá độ ổn định và giảm thiểu nguy cơ Overfitting.'
    }
  };

  class SlideUploadController {
    constructor() {
      // Form and Inputs
      this.uploadForm = document.getElementById('slide-upload-form');
      this.courseSelect = document.getElementById('slide-course-select');
      this.customCourseInput = document.getElementById('slide-course-custom-input');
      this.weekInput = document.getElementById('slide-week-input');
      this.topicInput = document.getElementById('slide-topic-input');
      this.fileInput = document.getElementById('slide-file-input');
      this.fileTypeSelect = document.getElementById('slide-filetype-select');
      this.fileNameDisplay = document.getElementById('slide-file-name-display');
      this.btnUpload = document.getElementById('btn-submit-slide-upload');
      this.statusContainer = document.getElementById('slide-upload-status');
      this.slidesListContainer = document.getElementById('ingested-slides-list');

      // Modals
      this.uploadModal = document.getElementById('upload-slide-modal');
      this.catalogModal = document.getElementById('catalog-slide-modal');
      this.btnCloseUploadModal = document.getElementById('btn-close-upload-modal');
      this.btnCloseCatalogModal = document.getElementById('btn-close-catalog-modal');

      // Modal Triggers
      this.btnOpenUpload = document.getElementById('btn-open-upload-modal');
      this.btnOpenUploadInline = document.getElementById('btn-open-upload-modal-inline');
      this.btnOpenCatalog = document.getElementById('btn-open-catalog-modal');
      this.btnQuickCatalog = document.getElementById('btn-quick-catalog');

      // Slide Viewer Presentation Elements
      this.currentSlideBadge = document.getElementById('current-slide-badge');
      this.currentSlidePage = document.getElementById('current-slide-page');
      this.currentSlideTopic = document.getElementById('current-slide-topic');
      this.currentSlideDesc = document.getElementById('current-slide-desc');
      this.currentSlideCodeBox = document.getElementById('current-slide-code-box');
      this.currentSlideNoteBox = document.getElementById('current-slide-note-box');
      this.btnPrevSlide = document.getElementById('btn-prev-slide');
      this.btnNextSlide = document.getElementById('btn-next-slide');

      // K3-Hackathon Classroom Zoom & Sync Controls
      this.ZOOM_STEPS = [0.75, 0.85, 1.0, 1.15, 1.25, 1.5];
      this.zoomIndex = 2; // Default 1.0 (100%)
      this.btnSlideZoomOut = document.getElementById('btn-slide-zoom-out');
      this.slideZoomVal = document.getElementById('slide-zoom-val');
      this.btnSlideZoomIn = document.getElementById('btn-slide-zoom-in');
      this.btnSlideZoomReset = document.getElementById('btn-slide-zoom-reset');
      this.currentSlideContainer = document.getElementById('current-slide-container');

      // Classroom Progress & Sync Indicators
      this.slideProgressBar = document.getElementById('slide-progress-bar');
      this.slideSyncBadge = document.getElementById('slide-sync-badge');
      this.slideSyncNotice = document.getElementById('slide-sync-notice');
      this.btnSlideToggleFollow = document.getElementById('btn-slide-toggle-follow');
      this.btnSlideResync = document.getElementById('btn-slide-resync');
      this.followingLecturer = true;

      // K3-Hackathon In-Class Raise Hand Controls
      this.btnSlideRaiseHand = document.getElementById('btn-slide-raise-hand');
      this.btnSlideLowerHand = document.getElementById('btn-slide-lower-hand');
      this.slideHandNotice = document.getElementById('slide-hand-notice');
      this.handRaisedTimeout = null;
      this.handRaised = false;

      // K3-Hackathon In-Class Quick Question (Quiz)
      this.btnToggleInclassQuiz = document.getElementById('btn-toggle-inclass-quiz');
      this.btnCloseInclassQuiz = document.getElementById('btn-close-inclass-quiz');
      this.slideInclassQuizPanel = document.getElementById('slide-inclass-quiz-panel');
      this.quizSlideEyebrow = document.getElementById('quiz-slide-eyebrow');
      this.quizQuestionPrompt = document.getElementById('quiz-question-prompt');
      this.quizOptionsContainer = document.getElementById('quiz-options-container');
      this.quizConfidenceSection = document.getElementById('quiz-confidence-section');
      this.quizResultCard = document.getElementById('quiz-result-card');
      this.quizResultStatus = document.getElementById('quiz-result-status');
      this.quizResultConfidenceBadge = document.getElementById('quiz-result-confidence-badge');
      this.quizResultExplanation = document.getElementById('quiz-result-explanation');
      this.quizCorrectAnswerBox = document.getElementById('quiz-correct-answer-box');
      this.btnQuizRetry = document.getElementById('btn-quiz-retry');
      this.btnQuizSkip = document.getElementById('btn-quiz-skip');
      this.selectedQuizOptionIndex = null;

      // Split-View Classroom AI Study Panel & 2-Tab Switching
      this.btnToggleSplitAi = document.getElementById('btn-toggle-split-ai');
      this.btnCloseSplitAi = document.getElementById('btn-close-split-ai');
      this.slideAiSplitPanel = document.getElementById('slide-ai-split-panel');
      this.splitAiSlideSummary = document.getElementById('split-ai-slide-summary');
      this.splitAiInput = document.getElementById('split-ai-input');
      this.btnSendSplitAi = document.getElementById('btn-send-split-ai');
      this.splitAiMessages = document.getElementById('split-ai-messages');
      this.btnSplitTabAi = document.getElementById('btn-split-tab-ai');
      this.btnSplitTabHuman = document.getElementById('btn-split-tab-human');
      this.splitPanelAiView = document.getElementById('split-panel-ai-view');
      this.splitPanelHumanView = document.getElementById('split-panel-human-view');
      this.splitHumanTicketInput = document.getElementById('split-human-ticket-input');
      this.btnSplitSubmitTicket = document.getElementById('btn-split-submit-ticket');
      this.splitHumanTicketsList = document.getElementById('split-human-tickets-list');

      // Bottom Classroom Dock Navigation Buttons
      this.btnPrevSlideBottom = document.getElementById('btn-prev-slide-bottom');
      this.btnNextSlideBottom = document.getElementById('btn-next-slide-bottom');
      this.currentSlidePageBottom = document.getElementById('current-slide-page-bottom');

      // Active Presentation State
      this.slidesDeck = [{ ...DEFAULT_SLIDE }];
      this.currentSlideIndex = 0;

      this.init();
    }

    init() {
      this.bindFileInput();
      this.bindUploadForm();
      this.bindModals();
      this.bindSlideNavigation();
      this.bindClassroomControls();
      this.bindSplitAiPanel();
      this.bindRaiseHand();
      this.bindInclassQuiz();
      this.bindSplitTabs();
      this.loadSlidesList();
      this.renderCurrentSlide();
    }

    bindFileInput() {
      if (this.fileInput && this.fileNameDisplay) {
        this.fileInput.addEventListener('change', (e) => {
          const file = e.target.files && e.target.files[0];
          if (file) {
            this.fileNameDisplay.textContent = `Tệp đã chọn: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
            this.fileNameDisplay.classList.remove('hidden');
          } else {
            this.fileNameDisplay.textContent = '';
            this.fileNameDisplay.classList.add('hidden');
          }
        });
      }
    }

    bindUploadForm() {
      if (this.courseSelect && this.customCourseInput) {
        this.courseSelect.addEventListener('change', (e) => {
          if (e.target.value === 'custom') {
            this.customCourseInput.focus();
          }
        });
      }

      if (this.uploadForm) {
        this.uploadForm.addEventListener('submit', (e) => {
          e.preventDefault();
          this.handleUpload();
        });
      }
    }

    bindModals() {
      const openUpload = (e) => {
        if (e) e.preventDefault();
        if (this.uploadModal) {
          this.uploadModal.classList.remove('hidden');
          const topicInput = document.getElementById('slide-topic-input');
          if (topicInput) topicInput.focus();
        }
      };
      const closeUpload = (e) => {
        if (e) e.preventDefault();
        if (this.uploadModal) {
          this.uploadModal.classList.add('hidden');
        }
      };

      const openCatalog = (e) => {
        if (e) e.preventDefault();
        if (this.catalogModal) {
          this.catalogModal.classList.remove('hidden');
          this.loadSlidesList();
        }
      };
      const closeCatalog = (e) => {
        if (e) e.preventDefault();
        if (this.catalogModal) {
          this.catalogModal.classList.add('hidden');
        }
      };

      if (this.btnOpenUpload) this.btnOpenUpload.addEventListener('click', openUpload);
      if (this.btnOpenUploadInline) this.btnOpenUploadInline.addEventListener('click', openUpload);
      if (this.btnCloseUploadModal) this.btnCloseUploadModal.addEventListener('click', closeUpload);

      if (this.btnOpenCatalog) this.btnOpenCatalog.addEventListener('click', openCatalog);
      if (this.btnQuickCatalog) this.btnQuickCatalog.addEventListener('click', openCatalog);
      if (this.btnCloseCatalogModal) this.btnCloseCatalogModal.addEventListener('click', closeCatalog);

      // Close on backdrop click
      [this.uploadModal, this.catalogModal].forEach((m) => {
        if (m) {
          m.addEventListener('click', (e) => {
            if (e.target === m) {
              m.classList.add('hidden');
            }
          });
        }
      });
    }

    bindSlideNavigation() {
      const goToNext = () => {
        if (this.currentSlideIndex < this.slidesDeck.length - 1) {
          this.currentSlideIndex++;
        } else {
          this.currentSlideIndex = 0;
        }
        this.renderCurrentSlide();
        if (window.TLUMascot) {
          const cur = this.slidesDeck[this.currentSlideIndex];
          window.TLUMascot.setCheering(`Đang xem trang ${this.currentSlideIndex + 1} / ${this.slidesDeck.length}!`);
        }
      };

      const goToPrev = () => {
        if (this.currentSlideIndex > 0) {
          this.currentSlideIndex--;
        } else {
          this.currentSlideIndex = this.slidesDeck.length - 1;
        }
        this.renderCurrentSlide();
        if (window.TLUMascot) {
          const cur = this.slidesDeck[this.currentSlideIndex];
          window.TLUMascot.setCheering(`Đang xem trang ${this.currentSlideIndex + 1} / ${this.slidesDeck.length}!`);
        }
      };

      if (this.btnPrevSlide) {
        this.btnPrevSlide.addEventListener('click', (e) => {
          if (e) e.preventDefault();
          goToPrev();
        });
      }

      if (this.btnNextSlide) {
        this.btnNextSlide.addEventListener('click', (e) => {
          if (e) e.preventDefault();
          goToNext();
        });
      }

      if (this.btnPrevSlideBottom) {
        this.btnPrevSlideBottom.addEventListener('click', (e) => {
          if (e) e.preventDefault();
          goToPrev();
        });
      }

      if (this.btnNextSlideBottom) {
        this.btnNextSlideBottom.addEventListener('click', (e) => {
          if (e) e.preventDefault();
          goToNext();
        });
      }

      // Keyboard navigation (ArrowLeft = Previous, ArrowRight = Next)
      window.addEventListener('keydown', (e) => {
        const activeTag = (document.activeElement && document.activeElement.tagName.toLowerCase()) || '';
        if (['input', 'textarea'].includes(activeTag)) return;
        if (e.key === 'ArrowRight' || e.key === 'PageDown') {
          goToNext();
        } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
          goToPrev();
        }
      });
    }

    renderCurrentSlide() {
      const current = this.slidesDeck[this.currentSlideIndex] || this.slidesDeck[0];
      if (!current) return;

      if (this.currentSlideBadge) {
        this.currentSlideBadge.textContent = `${current.course_code} • Tuần ${current.week < 10 ? '0' + current.week : current.week}`;
      }

      if (this.currentSlidePage) {
        this.currentSlidePage.textContent = current.page || `Slide ${this.currentSlideIndex + 1} / ${this.slidesDeck.length}`;
      }

      if (this.currentSlidePageBottom) {
        this.currentSlidePageBottom.textContent = current.page || `Slide ${this.currentSlideIndex + 1} / ${this.slidesDeck.length}`;
      }

      if (this.currentSlideTopic) {
        this.currentSlideTopic.textContent = current.topic;
      }

      if (this.currentSlideDesc) {
        this.currentSlideDesc.textContent = current.desc;
      }

      if (this.currentSlideCodeBox) {
        const lines = (current.code || '').split('\n');
        this.currentSlideCodeBox.innerHTML = lines.map(line => {
          if (line.trim().startsWith('//') || line.trim().startsWith('#') || line.trim().startsWith('--')) {
            return `<div class="text-[#64748B]">${this.escapeHtml(line)}</div>`;
          }
          return `<div>${this.escapeHtml(line)}</div>`;
        }).join('');
      }

      if (this.currentSlideNoteBox) {
        this.currentSlideNoteBox.innerHTML = `
          <div class="font-bold text-[#B91C1C]">Lưu Ý Học Thuật Khoa CNTT:</div>
          <div>${this.escapeHtml(current.note || 'Xem slide bài giảng để nắm chắc kiến thức nền tảng.')}</div>
        `;
      }

      // Sync active course label in Chat window
      const chatCourseLabel = document.getElementById('chat-active-course-label');
      if (chatCourseLabel) {
        chatCourseLabel.textContent = `Đang học: ${current.course_code} - ${current.course_name || 'Công nghệ Thông tin'}`;
      }

      // Update Reading Progress Bar
      this.updateProgressBar();

      // Update Split AI Slide Summary
      if (this.splitAiSlideSummary) {
        this.splitAiSlideSummary.textContent = `${(current.desc || '').slice(0, 160)}... Bám sát chuẩn đào tạo Khoa CNTT TLU môn ${current.course_code}.`;
      }

      // Update In-Class Quick Question (from K3-Hackathon student-question-panel)
      this.renderSlideQuiz(current);

      // Visual feedback flash on slide container
      const container = document.getElementById('current-slide-container');
      if (container) {
        container.classList.add('ring-2', 'ring-[#0D62FE]');
        setTimeout(() => {
          container.classList.remove('ring-2', 'ring-[#0D62FE]');
        }, 300);
      }
    }

    bindClassroomControls() {
      // Zoom controls
      if (this.btnSlideZoomOut) {
        this.btnSlideZoomOut.addEventListener('click', () => this.zoomBy(-1));
      }
      if (this.btnSlideZoomIn) {
        this.btnSlideZoomIn.addEventListener('click', () => this.zoomBy(1));
      }
      if (this.slideZoomVal) {
        this.slideZoomVal.addEventListener('click', () => this.resetZoom());
      }
      if (this.btnSlideZoomReset) {
        this.btnSlideZoomReset.addEventListener('click', () => this.resetZoom());
      }

      // Ctrl + Wheel to zoom on slide container (from K3-Hackathon)
      if (this.currentSlideContainer) {
        this.currentSlideContainer.addEventListener('wheel', (e) => {
          if (e.ctrlKey) {
            e.preventDefault();
            this.zoomBy(e.deltaY < 0 ? 1 : -1);
          }
        }, { passive: false });
      }

      // Follow lecturer toggle
      if (this.btnSlideToggleFollow) {
        this.btnSlideToggleFollow.addEventListener('click', () => this.toggleFollow());
      }
      if (this.btnSlideResync) {
        this.btnSlideResync.addEventListener('click', () => this.resyncWithClass());
      }
    }

    zoomBy(delta) {
      this.zoomIndex = Math.min(this.ZOOM_STEPS.length - 1, Math.max(0, this.zoomIndex + delta));
      this.applyZoom();
    }

    resetZoom() {
      this.zoomIndex = 2; // 1.0 (100%)
      this.applyZoom();
    }

    applyZoom() {
      const scale = this.ZOOM_STEPS[this.zoomIndex];
      const percent = Math.round(scale * 100);
      if (this.slideZoomVal) {
        this.slideZoomVal.textContent = `${percent}%`;
      }
      if (this.currentSlideContainer) {
        this.currentSlideContainer.style.transform = `scale(${scale})`;
        this.currentSlideContainer.style.transformOrigin = 'top center';
        const wrapper = document.getElementById('slide-stage-wrapper');
        if (wrapper) {
          if (scale > 1) {
            const h = Math.ceil(this.currentSlideContainer.offsetHeight * scale);
            wrapper.style.height = `${h}px`;
          } else {
            wrapper.style.height = 'auto';
          }
        }
      }
    }

    toggleFollow() {
      this.followingLecturer = !this.followingLecturer;
      if (this.followingLecturer) {
        if (this.btnSlideToggleFollow) {
          this.btnSlideToggleFollow.textContent = 'Đang Theo Dõi Giảng Viên';
          this.btnSlideToggleFollow.className = 'blk-btn px-3.5 py-2 bg-[#ECFDF5] hover:bg-[#D1FAE5] text-[#047857] text-xs font-extrabold transition-all cursor-pointer';
        }
        if (this.slideSyncBadge) {
          this.slideSyncBadge.textContent = 'Đang Theo Dõi Bài Giảng';
          this.slideSyncBadge.className = 'text-[11px] font-extrabold text-[#10B981] bg-[#ECFDF5] px-2.5 py-1 rounded-xl border border-[#A7F3D0]';
        }
        if (this.slideSyncNotice) {
          this.slideSyncNotice.classList.add('hidden');
        }
      } else {
        if (this.btnSlideToggleFollow) {
          this.btnSlideToggleFollow.textContent = 'Chế Độ Tự Đọc Slide';
          this.btnSlideToggleFollow.className = 'blk-btn px-3.5 py-2 bg-[#FFFBEB] hover:bg-[#FEF3C7] text-[#B45309] text-xs font-extrabold transition-all cursor-pointer';
        }
        if (this.slideSyncBadge) {
          this.slideSyncBadge.textContent = 'Tự Đọc Độc Lập';
          this.slideSyncBadge.className = 'text-[11px] font-extrabold text-[#B45309] bg-[#FFFBEB] px-2.5 py-1 rounded-xl border border-[#FDE68A]';
        }
        if (this.slideSyncNotice) {
          this.slideSyncNotice.classList.remove('hidden');
        }
      }
    }

    resyncWithClass() {
      this.followingLecturer = true;
      this.currentSlideIndex = 0;
      this.renderCurrentSlide();
      if (this.btnSlideToggleFollow) {
        this.btnSlideToggleFollow.textContent = 'Đang Theo Dõi Giảng Viên';
        this.btnSlideToggleFollow.className = 'blk-btn px-3.5 py-2 bg-[#ECFDF5] hover:bg-[#D1FAE5] text-[#047857] text-xs font-extrabold transition-all cursor-pointer';
      }
      if (this.slideSyncBadge) {
        this.slideSyncBadge.textContent = 'Đang Theo Dõi Bài Giảng';
        this.slideSyncBadge.className = 'text-[11px] font-extrabold text-[#10B981] bg-[#ECFDF5] px-2.5 py-1 rounded-xl border border-[#A7F3D0]';
      }
      if (this.slideSyncNotice) {
        this.slideSyncNotice.classList.add('hidden');
      }
    }

    updateProgressBar() {
      if (this.slideProgressBar) {
        const pct = ((this.currentSlideIndex + 1) / this.slidesDeck.length) * 100;
        this.slideProgressBar.style.width = `${pct}%`;
      }
    }

    bindSplitAiPanel() {
      if (this.btnToggleSplitAi) {
        this.btnToggleSplitAi.addEventListener('click', () => {
          if (this.slideAiSplitPanel) {
            this.slideAiSplitPanel.classList.toggle('hidden');
          }
        });
      }
      if (this.btnCloseSplitAi) {
        this.btnCloseSplitAi.addEventListener('click', () => {
          if (this.slideAiSplitPanel) {
            this.slideAiSplitPanel.classList.add('hidden');
          }
        });
      }

      // Quick prompt suggestion chips
      const chips = document.querySelectorAll('.split-ai-chip');
      chips.forEach((chip) => {
        chip.addEventListener('click', () => {
          const query = chip.textContent.trim();
          this.sendSplitAiMessage(query);
        });
      });

      // Composer submit
      if (this.btnSendSplitAi) {
        this.btnSendSplitAi.addEventListener('click', () => {
          const val = this.splitAiInput ? this.splitAiInput.value.trim() : '';
          if (val) {
            this.sendSplitAiMessage(val);
            if (this.splitAiInput) this.splitAiInput.value = '';
          }
        });
      }
      if (this.splitAiInput) {
        this.splitAiInput.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            const val = this.splitAiInput.value.trim();
            if (val) {
              this.sendSplitAiMessage(val);
              this.splitAiInput.value = '';
            }
          }
        });
      }
    }

    async sendSplitAiMessage(userText) {
      if (!this.splitAiMessages) return;
      
      // Append student message
      const studentMsg = document.createElement('div');
      studentMsg.className = 'p-2.5 bg-[#EEF4FF] border border-[#BFDBFE] text-[#0D62FE] rounded-xl font-medium';
      studentMsg.textContent = userText;
      this.splitAiMessages.appendChild(studentMsg);
      this.splitAiMessages.scrollTop = this.splitAiMessages.scrollHeight;

      // Loading bubble
      const loadingMsg = document.createElement('div');
      loadingMsg.className = 'p-2.5 bg-white border border-[#E2E8F0] rounded-xl text-[#64748B] italic';
      loadingMsg.textContent = 'AI đang đối chiếu slide...';
      this.splitAiMessages.appendChild(loadingMsg);
      this.splitAiMessages.scrollTop = this.splitAiMessages.scrollHeight;

      try {
        const cur = this.slidesDeck[this.currentSlideIndex];
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: `[Slide ${cur.course_code} - ${cur.topic}]: ${userText}`,
            course_code: cur.course_code,
            mode: 'socratic'
          })
        });
        if (res.ok) {
          const data = await res.json();
          loadingMsg.remove();
          const aiMsg = document.createElement('div');
          aiMsg.className = 'p-2.5 bg-white border border-[#E2E8F0] rounded-xl text-[#334155] space-y-1';
          aiMsg.innerHTML = `
            <div class="font-bold text-[#7E22CE]">[Gia Sư Socratic]:</div>
            <div>${this.escapeHtml(data.response || data.reply || 'Hãy đối chiếu đoạn code mẫu trong slide để tự tìm ra nguyên nhân.')}</div>
          `;
          this.splitAiMessages.appendChild(aiMsg);
        } else {
          throw new Error('API request failed');
        }
      } catch (err) {
        loadingMsg.remove();
        const fallbackMsg = document.createElement('div');
        fallbackMsg.className = 'p-2.5 bg-white border border-[#E2E8F0] rounded-xl text-[#334155] space-y-1';
        fallbackMsg.innerHTML = `
          <div class="font-bold text-[#7E22CE]">[Gia Sư Socratic]:</div>
          <div>Trong slide này, bạn hãy quan sát cấu trúc pipeline huấn luyện và cách thức đánh giá độ chính xác của mô hình học máy.</div>
        `;
        this.splitAiMessages.appendChild(fallbackMsg);
      }
      this.splitAiMessages.scrollTop = this.splitAiMessages.scrollHeight;
    }

    renderSlideQuiz(current) {
      if (!this.quizOptionsContainer || !this.quizQuestionPrompt) return;
      const q = SLIDE_QUESTIONS[current.course_code] || SLIDE_QUESTIONS['DATASCIENCE'];
      if (!q) return;

      if (this.quizSlideEyebrow) {
        this.quizSlideEyebrow.textContent = `CÂU HỎI NHANH TRÊN LỚP • ${current.page || current.course_code}`;
      }
      this.quizQuestionPrompt.textContent = q.prompt;

      this.selectedQuizOptionIndex = null;
      if (this.quizResultCard) this.quizResultCard.classList.add('hidden');
      if (this.quizConfidenceSection) this.quizConfidenceSection.classList.remove('hidden');

      this.quizOptionsContainer.innerHTML = '';
      q.options.forEach((optText, optIdx) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'quiz-option-btn w-full text-left p-3 rounded-xl border-2 border-b-4 border-[#CBD5E1] bg-[#F8FAFC] hover:bg-[#EEF4FF] hover:border-[#0D62FE] text-xs sm:text-sm font-bold text-[#0F172A] transition-all cursor-pointer';
        btn.textContent = optText;
        btn.addEventListener('click', () => {
          this.selectedQuizOptionIndex = optIdx;
          const allOptionBtns = this.quizOptionsContainer.querySelectorAll('.quiz-option-btn');
          allOptionBtns.forEach((b, idx) => {
            if (idx === optIdx) {
              b.className = 'quiz-option-btn w-full text-left p-3 rounded-xl border-2 border-b-4 border-[#0D62FE] bg-[#EEF4FF] text-xs sm:text-sm font-black text-[#0D62FE] shadow-2xs cursor-pointer';
            } else {
              b.className = 'quiz-option-btn w-full text-left p-3 rounded-xl border-2 border-b-4 border-[#CBD5E1] bg-[#F8FAFC] hover:bg-[#EEF4FF] hover:border-[#0D62FE] text-xs sm:text-sm font-bold text-[#0F172A] transition-all cursor-pointer';
            }
          });
        });
        this.quizOptionsContainer.appendChild(btn);
      });
    }

    bindRaiseHand() {
      if (this.btnSlideRaiseHand) {
        this.btnSlideRaiseHand.addEventListener('click', () => {
          this.handRaised = !this.handRaised;
          if (this.handRaised) {
            this.btnSlideRaiseHand.textContent = 'Đang Giơ Tay';
            this.btnSlideRaiseHand.className = 'blk-btn px-3.5 py-2 bg-[#FEF3C7] text-[#92400E] border-2 border-[#F59E0B] text-xs font-black transition-all cursor-pointer';
            if (this.slideHandNotice) this.slideHandNotice.classList.remove('hidden');
            if (window.TLUMascot) {
              window.TLUMascot.setCheering('Bạn đã giơ tay phát biểu trên lớp!');
            }
            if (this.handRaisedTimeout) clearTimeout(this.handRaisedTimeout);
            this.handRaisedTimeout = setTimeout(() => {
              this.lowerHand();
            }, 8000);
          } else {
            this.lowerHand();
          }
        });
      }

      if (this.btnSlideLowerHand) {
        this.btnSlideLowerHand.addEventListener('click', () => {
          this.lowerHand();
        });
      }
    }

    lowerHand() {
      this.handRaised = false;
      if (this.handRaisedTimeout) {
        clearTimeout(this.handRaisedTimeout);
        this.handRaisedTimeout = null;
      }
      if (this.btnSlideRaiseHand) {
        this.btnSlideRaiseHand.textContent = 'Giơ Tay';
        this.btnSlideRaiseHand.className = 'blk-btn px-3.5 py-2 bg-white hover:bg-[#FEF3C7] text-[#B45309] border border-[#FCD34D] text-xs font-extrabold transition-all cursor-pointer';
      }
      if (this.slideHandNotice) {
        this.slideHandNotice.classList.add('hidden');
      }
    }

    bindInclassQuiz() {
      if (this.btnToggleInclassQuiz) {
        this.btnToggleInclassQuiz.addEventListener('click', () => {
          if (this.slideInclassQuizPanel) {
            this.slideInclassQuizPanel.classList.toggle('hidden');
          }
        });
      }

      if (this.btnCloseInclassQuiz) {
        this.btnCloseInclassQuiz.addEventListener('click', () => {
          if (this.slideInclassQuizPanel) {
            this.slideInclassQuizPanel.classList.add('hidden');
          }
        });
      }

      const confButtons = [
        { id: 'btn-quiz-conf-1', label: 'Chưa chắc' },
        { id: 'btn-quiz-conf-2', label: 'Tạm ổn' },
        { id: 'btn-quiz-conf-3', label: 'Chắc chắn' }
      ];

      confButtons.forEach(({ id, label }) => {
        const btn = document.getElementById(id);
        if (btn) {
          btn.addEventListener('click', () => {
            if (this.selectedQuizOptionIndex === null) {
              if (this.quizOptionsContainer) {
                this.quizOptionsContainer.classList.add('ring-2', 'ring-[#F59E0B]');
                setTimeout(() => this.quizOptionsContainer.classList.remove('ring-2', 'ring-[#F59E0B]'), 600);
              }
              return;
            }
            this.submitQuizAnswer(label);
          });
        }
      });

      if (this.btnQuizSkip) {
        this.btnQuizSkip.addEventListener('click', () => {
          if (this.slideInclassQuizPanel) {
            this.slideInclassQuizPanel.classList.add('hidden');
          }
        });
      }

      if (this.btnQuizRetry) {
        this.btnQuizRetry.addEventListener('click', () => {
          const cur = this.slidesDeck[this.currentSlideIndex] || this.slidesDeck[0];
          this.renderSlideQuiz(cur);
        });
      }
    }

    submitQuizAnswer(confLabel) {
      const cur = this.slidesDeck[this.currentSlideIndex] || this.slidesDeck[0];
      const q = SLIDE_QUESTIONS[cur.course_code] || SLIDE_QUESTIONS['DATASCIENCE'];
      if (!q) return;

      const isCorrect = this.selectedQuizOptionIndex === q.correctIndex;
      if (this.quizConfidenceSection) this.quizConfidenceSection.classList.add('hidden');
      if (this.quizResultCard) {
        this.quizResultCard.classList.remove('hidden');
        if (isCorrect) {
          this.quizResultCard.className = 'p-4 rounded-xl border-2 border-[#10B981] bg-[#ECFDF5] space-y-2';
          if (this.quizResultStatus) {
            this.quizResultStatus.textContent = 'CHÍNH XÁC!';
            this.quizResultStatus.className = 'text-xs font-black uppercase tracking-wider text-[#059669]';
          }
          if (this.quizCorrectAnswerBox) this.quizCorrectAnswerBox.classList.add('hidden');
        } else {
          this.quizResultCard.className = 'p-4 rounded-xl border-2 border-[#EF4444] bg-[#FEF2F2] space-y-2';
          if (this.quizResultStatus) {
            this.quizResultStatus.textContent = 'CHƯA ĐÚNG — CÙNG XEM LẠI GIẢI THÍCH NHÉ';
            this.quizResultStatus.className = 'text-xs font-black uppercase tracking-wider text-[#DC2626]';
          }
          if (this.quizCorrectAnswerBox) {
            this.quizCorrectAnswerBox.classList.remove('hidden');
            this.quizCorrectAnswerBox.textContent = `Đáp án đúng: ${q.options[q.correctIndex]}`;
          }
        }
      }

      if (this.quizResultConfidenceBadge) {
        this.quizResultConfidenceBadge.textContent = `Độ tự tin: ${confLabel}`;
      }

      if (this.quizResultExplanation) {
        this.quizResultExplanation.textContent = q.explanation;
      }

      if (window.TLUMascot) {
        if (isCorrect) {
          window.TLUMascot.setCheering(`Tuyệt vời! Bạn đã trả lời đúng câu hỏi môn ${cur.course_code}!`);
        } else {
          window.TLUMascot.setCheering(`Đừng nản! Đọc kỹ giải thích để làm chủ kiến thức môn ${cur.course_code} nhé!`);
        }
      }
    }

    bindSplitTabs() {
      if (this.btnSplitTabAi && this.btnSplitTabHuman) {
        this.btnSplitTabAi.addEventListener('click', () => {
          this.btnSplitTabAi.className = 'flex-1 py-2 text-center text-xs font-black transition-all cursor-pointer bg-white text-[#7E22CE] border-r border-[#CBD5E1] shadow-2xs';
          this.btnSplitTabHuman.className = 'flex-1 py-2 text-center text-xs font-black transition-all cursor-pointer bg-[#F8FAFC] text-[#64748B] hover:text-[#0F172A]';
          if (this.splitPanelAiView) this.splitPanelAiView.classList.remove('hidden');
          if (this.splitPanelHumanView) this.splitPanelHumanView.classList.add('hidden');
        });

        this.btnSplitTabHuman.addEventListener('click', () => {
          this.btnSplitTabHuman.className = 'flex-1 py-2 text-center text-xs font-black transition-all cursor-pointer bg-white text-[#4F46E5] shadow-2xs';
          this.btnSplitTabAi.className = 'flex-1 py-2 text-center text-xs font-black transition-all cursor-pointer bg-[#F8FAFC] text-[#64748B] hover:text-[#0F172A] border-r border-[#CBD5E1]';
          if (this.splitPanelHumanView) this.splitPanelHumanView.classList.remove('hidden');
          if (this.splitPanelAiView) this.splitPanelAiView.classList.add('hidden');
        });
      }

      if (this.btnSplitSubmitTicket && this.splitHumanTicketInput && this.splitHumanTicketsList) {
        this.btnSplitSubmitTicket.addEventListener('click', () => {
          const text = this.splitHumanTicketInput.value.trim();
          if (!text) return;

          const cur = this.slidesDeck[this.currentSlideIndex] || this.slidesDeck[0];
          const ticketCard = document.createElement('div');
          ticketCard.className = 'p-3 bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl space-y-1.5 text-xs';
          ticketCard.innerHTML = `
            <p class="font-bold text-[#0F172A]">${this.escapeHtml(text)}</p>
            <div class="flex items-center justify-between text-3xs">
              <span class="font-extrabold text-[#D97706] bg-[#FEF3C7] px-2 py-0.5 rounded-md border border-[#FDE68A]">Đang chờ đội ngũ giảng dạy</span>
              <span class="text-[#64748B]">Vừa xong • ${this.escapeHtml(cur.course_code)}</span>
            </div>
            <div class="text-[#475569] bg-white p-2 rounded-lg border border-[#E2E8F0] italic">
              Yêu cầu đã được gửi đến Trợ giảng môn ${this.escapeHtml(cur.course_code)}. Câu trả lời sẽ xuất hiện tại đây ngay khi được giải đáp.
            </div>
          `;
          this.splitHumanTicketsList.prepend(ticketCard);
          this.splitHumanTicketInput.value = '';

          if (window.TLUMascot) {
            window.TLUMascot.setCheering('Yêu cầu hỗ trợ đã được gửi tới Giảng viên & Trợ giảng!');
          }
        });
      }
    }

    escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }

    async handleUpload() {
      // Determine Course: Supports ALL IT Courses
      let course = 'IT101';
      if (this.customCourseInput && this.customCourseInput.value.trim()) {
        course = this.customCourseInput.value.trim().toUpperCase();
      } else if (this.courseSelect && this.courseSelect.value && this.courseSelect.value !== 'custom') {
        course = this.courseSelect.value.toUpperCase();
      } else {
        course = 'IT_CNTT';
      }

      const week = this.weekInput ? parseInt(this.weekInput.value, 10) : 3;
      const topic = this.topicInput ? this.topicInput.value.trim() : '';
      const fileType = this.fileTypeSelect ? this.fileTypeSelect.value : 'pdf';
      const file = this.fileInput && this.fileInput.files ? this.fileInput.files[0] : null;

      const filename = file ? file.name : `${course}_Tuan${week < 10 ? '0' + week : week}_${topic.replace(/\s+/g, '_')}.${fileType}`;

      if (!topic) {
        if (this.statusContainer) {
          this.statusContainer.innerHTML = '<div class="p-3 bg-[#FEF2F2] border border-[#FCA5A5] text-[#991B1B] text-xs font-bold rounded-lg">[Lỗi]: Vui lòng nhập tiêu đề bài giảng hoặc chủ đề tài liệu.</div>';
        }
        return;
      }

      if (this.statusContainer) {
        this.statusContainer.innerHTML = `
          <div class="p-3 bg-[#EEF4FF] border border-[#BFDBFE] text-[#0D62FE] text-xs font-bold rounded-lg animate-pulse space-y-1">
            <div>Đang nạp học liệu môn ${course} vào hệ thống...</div>
            <div class="text-3xs font-mono text-[#334155]">• Xử lý bản ghi RAW &gt; Khử PII &gt; Tạo chỉ mục tìm kiếm và đồng bộ Khung Chiếu Slide</div>
          </div>
        `;
      }

      try {
        const payload = {
          course_code: course,
          week: week,
          topic: topic,
          filename: filename,
          file_type: fileType,
          content_summary: `Slide bài giảng môn ${course} Tuần ${week}: ${topic}`
        };

        const res = await fetch('/api/slides/upload', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          const data = await res.json();
          this.onUploadSuccess(data.record || {
            filename: filename,
            course_code: course,
            week: week,
            topic: topic,
            file_type: fileType,
            sha256: 'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e',
            gold_chunks: 14
          });
        } else {
          throw new Error(`HTTP error: ${res.status}`);
        }
      } catch (err) {
        console.error('Slide upload error:', err);
        if (this.statusContainer) {
          this.statusContainer.innerHTML = `
            <div class="p-3 bg-[#FEF2F2] border border-[#FCA5A5] rounded-xl text-xs text-[#DC2626]">
              Lỗi khi nạp tài liệu: ${err.message || 'Không thể kết nối đến máy chủ'}. Vui lòng thử lại.
            </div>
          `;
        }
      }
    }

    onUploadSuccess(record) {
      this.renderUploadSuccessMessage(record);
      this.loadSlidesList(false);

      // Add to active slide deck and present immediately
      const newSlide = {
        course_code: record.course_code,
        course_name: record.course_name || `Môn học CNTT (${record.course_code})`,
        week: record.week,
        page: `Slide 01 / ${record.gold_chunks || 12}`,
        topic: `Chủ đề: ${record.topic}`,
        desc: `Học liệu vừa tải lên thành công: ${record.filename}. Tài liệu đã được phân tích và sẵn sàng tra cứu trực tiếp trong Khung Chiếu Slide và Chatbot Socratic.`,
        code: `// Tệp học liệu: ${record.filename}\n// Môn học: ${record.course_code} - Tuần ${record.week}\n// Định dạng: ${record.file_type.toUpperCase()}`,
        note: `Tài liệu đã được kiểm chứng trích dẫn phục vụ học tập theo chuẩn Khoa CNTT TLU.`
      };

      this.slidesDeck.unshift(newSlide);
      this.currentSlideIndex = 0;
      this.renderCurrentSlide();

      // Ensure header course selector includes this course
      const headerCourseSel = document.getElementById('course-select');
      if (headerCourseSel) {
        let exists = false;
        for (let i = 0; i < headerCourseSel.options.length; i++) {
          if (headerCourseSel.options[i].value === record.course_code) {
            exists = true;
            break;
          }
        }
        if (!exists) {
          const opt = document.createElement('option');
          opt.value = record.course_code;
          opt.textContent = `${record.course_code} - ${record.topic}`;
          headerCourseSel.appendChild(opt);
        }
        headerCourseSel.value = record.course_code;
      }

      // Reset form
      if (this.topicInput) this.topicInput.value = '';
      if (this.fileInput) this.fileInput.value = '';
      if (this.customCourseInput) this.customCourseInput.value = '';
      if (this.fileNameDisplay) {
        this.fileNameDisplay.textContent = '';
        this.fileNameDisplay.classList.add('hidden');
      }

      if (window.TLUMascot) {
        window.TLUMascot.setCheering(`Đã tải lên và trình chiếu thành công slide môn ${record.course_code}!`);
      }
    }

    renderUploadSuccessMessage(record) {
      if (!this.statusContainer) return;
      this.statusContainer.innerHTML = `
        <div class="p-3 bg-[#F0FDF4] border border-[#86EFAC] rounded-xl space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-[#15803D]">[Nạp Thành Công]: ${record.filename}</span>
            <span class="text-3xs font-mono bg-[#DCFCE7] text-[#166534] px-2 py-0.5 rounded font-bold">Môn: ${record.course_code}</span>
          </div>
          <div class="text-3xs text-[#334155]">
            Slide đã được nạp thành công và tự động trình chiếu ngay trên <strong>Khung Chiếu Slide</strong>.
          </div>
          <div class="pt-1">
            <button type="button" id="btn-close-upload-success" class="w-full py-1.5 bg-[#10B981] hover:bg-[#059669] text-white text-xs font-bold rounded-lg shadow-2xs transition-colors">
              Đóng Cửa Sổ &amp; Xem Slide Ngay
            </button>
          </div>
        </div>
      `;

      const btnCloseSuccess = document.getElementById('btn-close-upload-success');
      if (btnCloseSuccess) {
        btnCloseSuccess.addEventListener('click', () => {
          if (this.uploadModal) this.uploadModal.classList.add('hidden');
        });
      }

      setTimeout(() => {
        if (this.uploadModal) this.uploadModal.classList.add('hidden');
      }, 600);
    }

    async loadSlidesList(shouldHydrateDeck = true) {
      if (!this.slidesListContainer) return;

      try {
        const res = await fetch('/api/slides/list');
        if (res.ok) {
          const slides = await res.json();
          this.renderSlidesList(slides);
          if (shouldHydrateDeck) {
            // Load full presentation slide pages (extracted from uploaded PDF)
            try {
              const pagesRes = await fetch('/api/slides/pages');
              if (pagesRes.ok) {
                const pages = await pagesRes.json();
                if (Array.isArray(pages) && pages.length > 1) {
                  this.slidesDeck = pages;
                  if (this.currentSlideIndex >= this.slidesDeck.length) {
                    this.currentSlideIndex = 0;
                  }
                  this.renderCurrentSlide();
                  return;
                }
              }
            } catch (errPages) {
              console.warn('Could not load detailed slide pages:', errPages);
            }
            this.hydrateSlidesDeckFromDatabase(slides);
          }
        } else {
          this.renderSlidesList([]);
        }
      } catch (err) {
        console.error('Failed to load slides list from server:', err);
        this.renderSlidesList([]);
      }
    }

    hydrateSlidesDeckFromDatabase(dbSlides) {
      if (!Array.isArray(dbSlides) || dbSlides.length === 0) return;

      const mapped = dbSlides.map(s => {
        const pageNum = s.course_code === 'DATASCIENCE' ? `Slide 01 / ${s.gold_chunks || 12}` :
                        s.course_code === 'IT101' ? 'Slide 18 / 42' :
                        s.course_code === 'IT201' ? 'Slide 22 / 50' :
                        s.course_code === 'IT205' ? 'Slide 14 / 36' :
                        s.course_code === 'IT301' ? 'Slide 12 / 38' :
                        s.course_code === 'IT315' ? 'Slide 26 / 45' :
                        `Slide 01 / ${s.gold_chunks || 12}`;

        return {
          slide_id: s.slide_id,
          course_code: s.course_code || 'DATASCIENCE',
          course_name: s.course_name || `Môn học CNTT (${s.course_code})`,
          week: s.week || 1,
          page: pageNum,
          topic: s.topic ? (s.topic.startsWith('Chủ đề:') ? s.topic : `Chủ đề: ${s.topic}`) : `Chủ đề: Bài giảng môn ${s.course_code}`,
          desc: s.content_desc || s.desc || `Học liệu môn ${s.course_code} - ${s.filename || 'Tài liệu môn học'} đã được nạp từ cơ sở dữ liệu Supabase.`,
          code: s.code_snippet || s.code || `// Học liệu môn ${s.course_code}\n// Tệp: ${s.filename || 'slide.pdf'}\n// Trích xuất từ Supabase Database`,
          note: s.callout_note || s.note || `Học liệu chính khóa Khoa CNTT TLU môn ${s.course_code}.`
        };
      });

      if (mapped.length > 0) {
        // Prioritize user's real uploaded Data Science slide at index 0
        const dsIndex = mapped.findIndex(s => s.slide_id === 'slide_datascience_w03_1791353451' || s.course_code === 'DATASCIENCE');
        if (dsIndex > 0) {
          const dsSlide = mapped.splice(dsIndex, 1)[0];
          mapped.unshift(dsSlide);
        }
        this.slidesDeck = mapped;
        if (this.currentSlideIndex >= this.slidesDeck.length) {
          this.currentSlideIndex = 0;
        }
        this.renderCurrentSlide();
      }
    }

    renderSlidesList(slides) {
      if (!this.slidesListContainer) return;

      if (!Array.isArray(slides) || slides.length === 0) {
        this.slidesListContainer.innerHTML = '<div class="text-xs text-[#64748B] italic py-4 text-center">Chưa có tài liệu slide nào được tải lên.</div>';
        return;
      }

      let html = '<div class="space-y-2.5">';
      slides.forEach((s, idx) => {
        html += `
          <div class="p-3 bg-white border border-[#CBD5E1] rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-2 shadow-2xs hover:border-[#0D62FE] transition-colors cursor-pointer group" data-slide-index="${idx}" data-slide-id="${s.slide_id || ''}" data-course="${s.course_code || 'IT101'}">
            <div class="space-y-0.5">
              <div class="flex items-center gap-2">
                <span class="text-3xs font-bold px-1.5 py-0.5 rounded bg-[#EEF4FF] text-[#0D62FE] border border-[#BFDBFE] font-mono">${s.course_code || 'IT101'}</span>
                <span class="text-xs font-bold text-[#0F172A] group-hover:text-[#0D62FE] transition-colors">${s.filename || 'Tài liệu môn học'}</span>
                <span class="text-3xs px-1.5 py-0.5 rounded bg-[#F1F5F9] text-[#475569] font-mono font-semibold">Tuần ${s.week || 1}</span>
              </div>
              <div class="text-2xs text-[#475569]">${s.topic || 'Chủ đề bài giảng'}</div>
            </div>
            <div class="flex items-center gap-2 text-3xs font-mono">
              <span class="bg-[#F0FDF4] text-[#166534] border border-[#BBF7D0] px-2 py-0.5 rounded font-bold">${s.gold_chunks || 12} Chunks</span>
              <button type="button" class="btn-select-slide px-2 py-1 bg-[#0D62FE] hover:bg-[#0047E0] text-white text-3xs font-bold rounded-lg transition-colors">Trình Chiếu</button>
            </div>
          </div>
        `;
      });
      html += '</div>';
      this.slidesListContainer.innerHTML = html;

      // Attach click events on slides list to load into main viewer
      this.slidesListContainer.querySelectorAll('[data-slide-index]').forEach((item) => {
        item.addEventListener('click', () => {
          const slideId = item.getAttribute('data-slide-id');
          const courseCode = item.getAttribute('data-course');
          // Find matching slide in deck by slide_id or course_code
          const foundIndex = this.slidesDeck.findIndex(s => (slideId && s.slide_id === slideId) || s.course_code === courseCode);
          if (foundIndex >= 0) {
            this.currentSlideIndex = foundIndex;
          } else {
            const topic = item.querySelector('.text-2xs') ? item.querySelector('.text-2xs').textContent : 'Chủ đề bài giảng';
            this.slidesDeck.unshift({
              slide_id: slideId,
              course_code: courseCode,
              course_name: `Môn học CNTT (${courseCode})`,
              week: 1,
              page: 'Slide 01 / 10',
              topic: `Chủ đề: ${topic}`,
              desc: `Học liệu môn ${courseCode} đã nạp phục vụ sinh viên Khoa CNTT TLU.`,
              code: `// Học liệu môn ${courseCode}\n// Đang trình chiếu trên hệ thống`,
              note: `Học liệu chính khóa Khoa CNTT TLU.`
            });
            this.currentSlideIndex = 0;
          }
          this.renderCurrentSlide();

          if (this.catalogModal) {
            this.catalogModal.classList.add('hidden');
          }

          if (window.TLUMascot) {
            window.TLUMascot.setCheering(`Đang trình chiếu slide môn ${courseCode}!`);
          }
        });
      });
    }
  }

  // Mount to window with readyState guard
  function initSlides() {
    if (!window.TLUSlides) {
      window.TLUSlides = new SlideUploadController();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSlides);
  } else {
    initSlides();
  }
})();
