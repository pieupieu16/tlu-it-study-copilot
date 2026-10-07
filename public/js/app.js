/**
 * TLU IT Study Copilot - Main Application Coordinator & Dual Portal Switcher
 * Module: public/js/app.js
 * Invariant Rule: 100% Light Mode, Zero Icons (no SVG, font icons, emojis).
 */

(function () {
  'use strict';

  class TLUApplication {
    constructor() {
      // Dual Portal Selectors
      this.btnPortalStudent = document.getElementById('btn-portal-student');
      this.btnPortalAdmin = document.getElementById('btn-portal-admin');
      this.navStudentTabs = document.getElementById('nav-student-tabs');
      this.navAdminTabs = document.getElementById('nav-admin-tabs');
      this.adminRoleBadge = document.getElementById('admin-role-badge');
      this.studentControls = document.getElementById('student-header-controls');
      this.studentPortalIndicator = document.getElementById('student-portal-indicator');
      this.adminPortalIndicator = document.getElementById('admin-portal-indicator');

      // Login & Auth Selectors
      this.loginScreen = document.getElementById('login-screen');
      this.loginForm = document.getElementById('login-form');
      this.loginStudentId = document.getElementById('login-student-id');
      this.loginPassword = document.getElementById('login-password');
      this.btnLoginSubmit = document.getElementById('btn-login-submit');
      this.btnQuickLoginAn = document.getElementById('btn-quick-login-an');
      this.btnQuickLoginLinh = document.getElementById('btn-quick-login-linh');
      this.linkGotoAdmin = document.getElementById('link-goto-admin');
      this.btnLogout = document.getElementById('btn-logout');
      this.btnAdminReturnStudent = document.getElementById('btn-admin-return-student');

      // Tabs across both portals
      this.tabButtons = {
        socratic: document.getElementById('tab-btn-socratic'),
        slides: document.getElementById('tab-btn-slides'),
        multiagent: document.getElementById('tab-btn-multiagent'),
        ops: document.getElementById('tab-btn-ops')
      };

      // Workspaces
      this.workspaces = {
        socratic: document.getElementById('workspace-socratic'),
        slides: document.getElementById('workspace-slides'),
        multiagent: document.getElementById('workspace-multiagent'),
        ops: document.getElementById('workspace-ops')
      };

      // Modals
      this.slideModal = document.getElementById('slide-modal');
      this.btnCloseSlideModal = document.getElementById('btn-close-slide-modal');

      this.proModal = document.getElementById('pro-modal');
      this.btnCloseProModal = document.getElementById('btn-close-pro-modal');
      this.btnConfirmProPayment = document.getElementById('btn-confirm-pro-payment');

      this.article25Modal = document.getElementById('article25-modal');
      this.btnViewArticle25 = document.getElementById('btn-view-article25');
      this.btnCloseArticle25Modal = document.getElementById('btn-close-article25-modal');

      this.currentPortal = 'student';
      this.currentTab = 'slides';

      this.init();
    }

    init() {
      this.bindPortalEvents();
      this.bindAuthEvents();
      this.bindTabEvents();
      this.bindModalEvents();
      this.bindMessengerChat();
      this.bindGlobalShortcuts();
      this.checkInitialRouteAndAuth();

      console.log('TLU IT Study Copilot Dual Portal Coordinator initialized.');
    }

    checkInitialRouteAndAuth() {
      const path = window.location.pathname;
      const hash = window.location.hash;
      const params = new URLSearchParams(window.location.search);
      const isAdminRoute = path.startsWith('/admin') || hash === '#admin' || params.get('portal') === 'admin';

      if (isAdminRoute) {
        if (this.loginScreen) this.loginScreen.classList.add('hidden');
        this.switchPortal('admin');
      } else {
        const authState = sessionStorage.getItem('tlu_auth_logged_in');
        if (authState === 'true') {
          if (this.loginScreen) this.loginScreen.classList.add('hidden');
          this.switchPortal('student');
        } else {
          if (this.loginScreen) this.loginScreen.classList.remove('hidden');
          this.switchPortal('student');
          if (window.TLUMascot) {
            window.TLUMascot.setCheering('Chào bạn! Rồng Xanh TLU đang vẫy tay chào đón bạn! Hãy đăng nhập để bắt đầu nhé!');
          }
        }
      }
    }

    bindAuthEvents() {
      const doLogin = (studentId, studentName) => {
        sessionStorage.setItem('tlu_auth_logged_in', 'true');
        sessionStorage.setItem('tlu_student_id', studentId);

        if (this.loginScreen) {
          this.loginScreen.classList.add('hidden');
        }

        const currentIdBadge = document.getElementById('current-student-id');
        if (currentIdBadge) currentIdBadge.textContent = studentId;

        const personaSelect = document.getElementById('persona-select');
        if (personaSelect) {
          personaSelect.value = studentId === 'A38901' ? 'linh' : 'an';
          personaSelect.dispatchEvent(new Event('change'));
        }

        this.switchPortal('student');

        if (window.TLUMascot) {
          window.TLUMascot.setCheering(`Chào mừng ${studentName || studentId}! Chúc bạn có buổi học hiệu quả cùng Rồng TLU!`);
        }
      };

      if (this.loginForm) {
        this.loginForm.addEventListener('submit', (e) => {
          e.preventDefault();
          const studentId = this.loginStudentId && this.loginStudentId.value.trim() ? this.loginStudentId.value.trim() : 'A41234';
          const studentName = studentId === 'A38901' ? 'Trần Mai Linh' : 'Nguyễn Văn An';
          doLogin(studentId, studentName);
        });
      }

      if (this.btnQuickLoginAn) {
        this.btnQuickLoginAn.addEventListener('click', () => {
          if (this.loginStudentId) this.loginStudentId.value = 'A41234';
          doLogin('A41234', 'Nguyễn Văn An');
        });
      }

      if (this.btnQuickLoginLinh) {
        this.btnQuickLoginLinh.addEventListener('click', () => {
          if (this.loginStudentId) this.loginStudentId.value = 'A38901';
          doLogin('A38901', 'Trần Mai Linh');
        });
      }

      if (this.btnLogout) {
        this.btnLogout.addEventListener('click', () => {
          sessionStorage.removeItem('tlu_auth_logged_in');
          if (this.loginScreen) {
            this.loginScreen.classList.remove('hidden');
          }
          if (window.TLUMascot) {
            window.TLUMascot.setIdle('Hẹn gặp lại bạn ở các buổi học tiếp theo nhé!');
          }
        });
      }

      if (this.linkGotoAdmin) {
        this.linkGotoAdmin.addEventListener('click', (e) => {
          e.preventDefault();
          if (this.loginScreen) this.loginScreen.classList.add('hidden');
          try {
            history.pushState(null, '', '/admin');
          } catch (err) {}
          this.switchPortal('admin');
        });
      }

      if (this.btnAdminReturnStudent) {
        this.btnAdminReturnStudent.addEventListener('click', () => {
          try {
            history.pushState(null, '', '/');
          } catch (err) {}
          const authState = sessionStorage.getItem('tlu_auth_logged_in');
          if (authState === 'true') {
            this.switchPortal('student');
          } else {
            if (this.loginScreen) this.loginScreen.classList.remove('hidden');
            this.switchPortal('student');
          }
        });
      }

      window.addEventListener('popstate', () => {
        this.checkInitialRouteAndAuth();
      });
    }

    bindPortalEvents() {
      if (this.btnPortalStudent) {
        this.btnPortalStudent.addEventListener('click', () => this.switchPortal('student'));
      }
      if (this.btnPortalAdmin) {
        this.btnPortalAdmin.addEventListener('click', () => this.switchPortal('admin'));
      }
    }

    switchPortal(portal) {
      this.currentPortal = portal;

      if (portal === 'student') {
        // Portal Indicators
        if (this.studentPortalIndicator) this.studentPortalIndicator.classList.remove('hidden');
        if (this.adminPortalIndicator) this.adminPortalIndicator.classList.add('hidden');

        // Portal button styles
        if (this.btnPortalStudent) {
          this.btnPortalStudent.className = 'portal-tab-btn px-3.5 py-1.5 text-xs font-bold rounded-lg bg-[#0D62FE] text-white shadow-xs transition-all';
        }
        if (this.btnPortalAdmin) {
          this.btnPortalAdmin.className = 'portal-tab-btn px-3.5 py-1.5 text-xs font-bold rounded-lg text-[#475569] hover:text-[#0D62FE] hover:bg-[#E2E8F0] transition-all';
        }

        // Toggle nav tabs
        if (this.navStudentTabs) this.navStudentTabs.classList.remove('hidden');
        if (this.navAdminTabs) this.navAdminTabs.classList.add('hidden');

        // Toggle header badges
        if (this.adminRoleBadge) this.adminRoleBadge.classList.add('hidden');
        if (this.studentControls) this.studentControls.classList.remove('hidden');

        // Switch to default student tab (Slide Center)
        this.switchTab('slides');

        if (window.TLUMascot) {
          window.TLUMascot.setCheering('Đang ở Cổng Sinh Viên: Kho bài giảng & slide chính khóa kết hợp Chatbot Khủng Long Rồng TLU bên cạnh!');
        }
      } else {
        // Admin Portal
        if (this.studentPortalIndicator) this.studentPortalIndicator.classList.add('hidden');
        if (this.adminPortalIndicator) this.adminPortalIndicator.classList.remove('hidden');

        if (this.btnPortalStudent) {
          this.btnPortalStudent.className = 'portal-tab-btn px-3.5 py-1.5 text-xs font-bold rounded-lg text-[#475569] hover:text-[#0D62FE] hover:bg-[#E2E8F0] transition-all';
        }
        if (this.btnPortalAdmin) {
          this.btnPortalAdmin.className = 'portal-tab-btn px-3.5 py-1.5 text-xs font-bold rounded-lg bg-[#0F172A] text-white shadow-xs transition-all';
        }

        // Toggle nav tabs
        if (this.navStudentTabs) this.navStudentTabs.classList.add('hidden');
        if (this.navAdminTabs) this.navAdminTabs.classList.remove('hidden');

        // Toggle header badges
        if (this.adminRoleBadge) this.adminRoleBadge.classList.remove('hidden');
        if (this.studentControls) this.studentControls.classList.add('hidden');

        // Switch to default admin tab
        this.switchTab('multiagent');

        if (window.TLUMascot) {
          window.TLUMascot.setThinking('Đang ở Cổng Quản Trị (/admin): Giám sát hạ tầng tác tử, chi phí FinOps và logs hệ thống.');
        }
      }
    }

    bindTabEvents() {
      Object.keys(this.tabButtons).forEach((tabKey) => {
        const btn = this.tabButtons[tabKey];
        if (btn) {
          btn.addEventListener('click', () => this.switchTab(tabKey));
        }
      });
    }

    switchTab(tabKey) {
      this.currentTab = tabKey;

      // Update Tab Buttons UI
      Object.keys(this.tabButtons).forEach((k) => {
        const btn = this.tabButtons[k];
        if (btn) {
          if (k === tabKey) {
            btn.className = 'tab-btn active px-3 py-2 text-xs font-bold rounded-lg bg-[#0D62FE] text-white shadow-xs transition-all';
          } else {
            btn.className = 'tab-btn px-3 py-2 text-xs font-bold rounded-lg text-[#64748B] hover:text-[#0F172A] hover:bg-[#F1F5F9] transition-all';
          }
        }
      });

      // Update Workspace Visibility
      Object.keys(this.workspaces).forEach((k) => {
        const ws = this.workspaces[k];
        if (ws) {
          if (k === tabKey) {
            ws.classList.remove('hidden');
          } else {
            ws.classList.add('hidden');
          }
        }
      });

      // Trigger custom event for submodules
      const activeBtnId = this.tabButtons[tabKey] ? this.tabButtons[tabKey].id : '';
      document.dispatchEvent(new CustomEvent('tab-activated', {
        detail: { tabKey, tabId: activeBtnId }
      }));
    }

    bindModalEvents() {
      // Slide Modal
      if (this.btnCloseSlideModal && this.slideModal) {
        this.btnCloseSlideModal.addEventListener('click', () => this.closeSlideModal());
      }

      // Pro Modal
      if (this.btnCloseProModal && this.proModal) {
        this.btnCloseProModal.addEventListener('click', () => this.closeProModal());
      }

      if (this.btnConfirmProPayment) {
        this.btnConfirmProPayment.addEventListener('click', () => this.handleProPayment());
      }

      // Article 25 Modal
      if (this.btnViewArticle25 && this.article25Modal) {
        this.btnViewArticle25.addEventListener('click', () => this.openArticle25Modal());
      }

      if (this.btnCloseArticle25Modal && this.article25Modal) {
        this.btnCloseArticle25Modal.addEventListener('click', () => this.closeArticle25Modal());
      }

      // Pro modal open triggers
      document.querySelectorAll('#btn-header-pro, #btn-portal-upgrade').forEach((btn) => {
        btn.addEventListener('click', () => this.openProModal());
      });

      // Payment method selection buttons
      const btnPayVnpay = document.getElementById('btn-pay-vnpay');
      const btnPayMomo = document.getElementById('btn-pay-momo');
      if (btnPayVnpay && btnPayMomo) {
        btnPayVnpay.addEventListener('click', () => {
          btnPayVnpay.className = 'p-2.5 border-2 border-[#0D62FE] bg-[#EEF4FF] rounded-xl text-center font-bold text-[#0D62FE] transition-all cursor-pointer';
          btnPayMomo.className = 'p-2.5 border border-[#E2E8F0] hover:border-[#0D62FE] rounded-xl text-center font-bold text-[#475569] transition-all cursor-pointer';
        });
        btnPayMomo.addEventListener('click', () => {
          btnPayMomo.className = 'p-2.5 border-2 border-[#0D62FE] bg-[#EEF4FF] rounded-xl text-center font-bold text-[#0D62FE] transition-all cursor-pointer';
          btnPayVnpay.className = 'p-2.5 border border-[#E2E8F0] hover:border-[#0D62FE] rounded-xl text-center font-bold text-[#475569] transition-all cursor-pointer';
        });
      }

      // Close modals on backdrop click
      [this.slideModal, this.proModal, this.article25Modal].forEach((modal) => {
        if (modal) {
          modal.addEventListener('click', (e) => {
            if (e.target === modal) {
              modal.classList.add('hidden');
            }
          });
        }
      });
    }

    openSlideModal(slideMeta) {
      if (!this.slideModal) return;
      const title = document.getElementById('slide-modal-title');
      const breadcrumb = document.getElementById('slide-modal-breadcrumb');
      const snippet = document.getElementById('slide-modal-snippet');

      if (title && slideMeta) {
        title.textContent = slideMeta.title || slideMeta.breadcrumb || 'Chi Tiết Slide Bài Giảng TLU';
      }
      if (breadcrumb && slideMeta) {
        breadcrumb.textContent = slideMeta.breadcrumb || 'IT101 > Tuần 03 > Slide 18';
      }
      if (snippet && slideMeta) {
        snippet.textContent = slideMeta.snippet || slideMeta.text || 'Nội dung trích dẫn giáo trình chính khóa Khoa CNTT TLU.';
      }

      this.slideModal.classList.remove('hidden');
    }

    closeSlideModal() {
      if (this.slideModal) this.slideModal.classList.add('hidden');
    }

    openProModal() {
      if (this.proModal) this.proModal.classList.remove('hidden');
    }

    closeProModal() {
      if (this.proModal) this.proModal.classList.add('hidden');
    }

    openArticle25Modal() {
      if (this.article25Modal) this.article25Modal.classList.remove('hidden');
    }

    closeArticle25Modal() {
      if (this.article25Modal) this.article25Modal.classList.add('hidden');
    }

    async handleProPayment() {
      const btn = this.btnConfirmProPayment;
      if (!btn) return;

      const originalText = btn.textContent;
      btn.textContent = 'Đang xử lý qua cổng thanh toán VNPAY...';
      btn.disabled = true;

      try {
        const res = await fetch('/api/subscription/tier', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id: 'A41234',
            target_tier: 'PRO',
            amount_vnd: 69000
          })
        });

        if (res.ok) {
          const data = await res.json();
          alert(`Nâng cấp thành công! Chào mừng bạn đến với Gói Pro Sinh Viên TLU (Hạn mức: ${data.daily_query_quota || 9999} lượt/ngày).`);
          this.closeProModal();
          const headerProBtn = document.getElementById('btn-header-pro');
          if (headerProBtn) {
            headerProBtn.textContent = 'Đã Kích Hoạt Gói Pro';
            headerProBtn.className = 'px-3 py-1.5 bg-[#10B981] text-white text-xs font-extrabold rounded-lg shadow-xs';
          }
          if (window.TLUMascot) {
            window.TLUMascot.setCheering('Chúc mừng bạn đã nâng cấp Gói Pro! Không giới hạn lượt hỏi.');
          }
        }
      } catch (err) {
        alert('Giao dịch hoàn tất mô phỏng! Tài khoản sinh viên A41234 đã nâng cấp gói Pro.');
        this.closeProModal();
      } finally {
        btn.textContent = originalText;
        btn.disabled = false;
      }
    }

    bindMessengerChat() {
      const bubbleTrigger = document.getElementById('mascot-messenger-trigger');
      const chatWindow = document.getElementById('mascot-chat-window');
      const btnMinimize = document.getElementById('btn-minimize-chat');
      const openTriggers = [
        document.getElementById('btn-open-messenger-chat'),
        document.getElementById('btn-trigger-messenger-panel'),
        document.getElementById('btn-ask-slide-mascot'),
        document.getElementById('btn-open-messenger-from-studio')
      ].filter(Boolean);

      const openChat = () => {
        if (chatWindow) {
          chatWindow.classList.remove('hidden');
          const input = document.getElementById('chat-input');
          if (input) input.focus();
        }
      };

      const closeChat = () => {
        if (chatWindow) {
          chatWindow.classList.add('hidden');
        }
      };

      const toggleChat = () => {
        if (chatWindow) {
          if (chatWindow.classList.contains('hidden')) {
            openChat();
          } else {
            closeChat();
          }
        }
      };

      if (bubbleTrigger) {
        bubbleTrigger.addEventListener('click', toggleChat);
      }
      if (btnMinimize) {
        btnMinimize.addEventListener('click', (e) => {
          e.stopPropagation();
          closeChat();
        });
      }
      openTriggers.forEach((btn) => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          openChat();
        });
      });

      // Quick Slide Queries
      document.querySelectorAll('.btn-quick-slide-query').forEach((btn) => {
        btn.addEventListener('click', () => {
          const query = btn.getAttribute('data-query');
          openChat();
          const input = document.getElementById('chat-input');
          if (input && query) {
            input.value = query;
            input.focus();
          }
        });
      });

      // Ask Slide Mascot button
      const btnAskSlide = document.getElementById('btn-ask-slide-mascot');
      if (btnAskSlide) {
        btnAskSlide.addEventListener('click', () => {
          openChat();
          const input = document.getElementById('chat-input');
          if (input) {
            input.value = 'Nhờ Rồng TLU giải thích slide Tuần 3 về con trỏ và quản lý bộ nhớ heap cho mình.';
            input.focus();
          }
        });
      }

      // Practice Slide Code button
      const btnPractice = document.getElementById('btn-practice-slide-code');
      if (btnPractice) {
        btnPractice.addEventListener('click', () => {
          this.switchTab('socratic');
        });
      }

      // Back to Slides button
      const btnBackToSlides = document.getElementById('btn-back-to-slides');
      if (btnBackToSlides) {
        btnBackToSlides.addEventListener('click', () => {
          this.switchTab('slides');
        });
      }

      // Goto Socratic Optional button
      const btnGotoSocratic = document.getElementById('btn-goto-socratic-optional');
      if (btnGotoSocratic) {
        btnGotoSocratic.addEventListener('click', () => {
          this.switchTab('socratic');
        });
      }
    }

    bindGlobalShortcuts() {
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          this.closeSlideModal();
          this.closeProModal();
          this.closeArticle25Modal();
          const uploadModal = document.getElementById('upload-slide-modal');
          if (uploadModal) uploadModal.classList.add('hidden');
          const catalogModal = document.getElementById('catalog-slide-modal');
          if (catalogModal) catalogModal.classList.add('hidden');
        }
      });
    }
  }

  // Mount to window with readyState guard
  function initApp() {
    if (!window.TLUApp) {
      window.TLUApp = new TLUApplication();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
  } else {
    initApp();
  }
})();
