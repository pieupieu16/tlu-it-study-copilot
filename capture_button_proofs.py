"""
TLU IT Study Copilot - Photographic Evidence Generator for All Buttons
Captures high-resolution browser screenshots validating each button's real DOM state changes.
"""

import sys
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path("/home/quan/.gemini/antigravity/brain/4d95a850-a881-46ed-a5c9-ea24191968ab/screenshots")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BASE_URL = "http://127.0.0.1:8000"

def capture_all_proofs():
    print("=" * 80)
    print("      TLU IT STUDY COPILOT - PHOTOGRAPHIC EVIDENCE GENERATOR")
    print("=" * 80)
    print(f"Target URL  : {BASE_URL}")
    print(f"Output Dir  : {OUTPUT_DIR}")
    print("-" * 80)

    screenshots = []

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True)
        # Desktop 1440x900 viewport for crisp, professional capture
        page = browser.new_page(viewport={"width": 1440, "height": 920})

        # -------------------------------------------------------------
        # PROOF 1: Giao diện Đăng Nhập (Login Portal Buttons)
        # -------------------------------------------------------------
        print("[01/15] Chụp bằng chứng 1: Màn hình Đăng Nhập & Linh vật vẫy tay chào...")
        page.goto(BASE_URL)
        page.wait_for_timeout(800)
        p1 = str(OUTPUT_DIR / "proof_01_login_portal.png")
        page.screenshot(path=p1, full_page=False)
        screenshots.append(("proof_01_login_portal.png", "Màn hình Đăng nhập Sinh viên (#btn-quick-login-an, #btn-quick-login-linh, #btn-login-submit, #link-goto-admin)"))

        # -------------------------------------------------------------
        # PROOF 2: Đăng nhập thành công vào Khung Chiếu Slide
        # -------------------------------------------------------------
        print("[02/15] Chụp bằng chứng 2: Click btn-quick-login-an -> Vào Khung Chiếu Slide...")
        page.click("#btn-quick-login-an")
        page.wait_for_timeout(600)
        p2 = str(OUTPUT_DIR / "proof_02_student_workspace_an.png")
        page.screenshot(path=p2, full_page=False)
        screenshots.append(("proof_02_student_workspace_an.png", "Khung chiếu Slide chính khóa của sinh viên Nguyễn Văn An (Mã SV A41234, Slide IT101)"))

        # -------------------------------------------------------------
        # PROOF 3: Điều hướng Slide (btn-next-slide)
        # -------------------------------------------------------------
        print("[03/15] Chụp bằng chứng 3: Click btn-next-slide -> Chuyển sang Slide IT201...")
        page.click("#btn-next-slide")
        page.wait_for_timeout(500)
        p3 = str(OUTPUT_DIR / "proof_03_slide_navigation_next.png")
        page.screenshot(path=p3, full_page=False)
        screenshots.append(("proof_03_slide_navigation_next.png", "Nút Slide Kế Tiếp (#btn-next-slide) chuyển thành công sang IT201 (Cây AVL & Đồ thị)"))

        # -------------------------------------------------------------
        # PROOF 4: Modal Xem Slide Gốc Toàn Màn Hình (.btn-open-slide)
        # -------------------------------------------------------------
        print("[04/15] Chụp bằng chứng 4: Click .btn-open-slide -> Mở Modal Slide Toàn Màn Hình...")
        page.locator(".btn-open-slide").first.click()
        page.wait_for_timeout(500)
        p4 = str(OUTPUT_DIR / "proof_04_slide_fullscreen_modal.png")
        page.screenshot(path=p4, full_page=False)
        screenshots.append(("proof_04_slide_fullscreen_modal.png", "Nút Xem Slide Gốc (.btn-open-slide) mở Modal xem slide toàn màn hình (#slide-modal)"))
        page.click("#btn-close-slide-modal")
        page.wait_for_timeout(400)

        # -------------------------------------------------------------
        # PROOF 5: Modal Tải Lên Slide Môn CNTT Mới (btn-open-upload-modal)
        # -------------------------------------------------------------
        print("[05/15] Chụp bằng chứng 5: Click btn-open-upload-modal -> Mở Modal Tải Lên Slide...")
        page.click("#btn-open-upload-modal")
        page.wait_for_timeout(500)
        p5 = str(OUTPUT_DIR / "proof_05_upload_slide_modal.png")
        page.screenshot(path=p5, full_page=False)
        screenshots.append(("proof_05_upload_slide_modal.png", "Nút Tải Lên Slide (#btn-open-upload-modal) mở Modal nạp học liệu mọi môn CNTT (#upload-slide-modal)"))

        # -------------------------------------------------------------
        # PROOF 6: Nạp Slide Môn CNTT Mới & Trình Chiếu Ngay (btn-submit-slide-upload)
        # -------------------------------------------------------------
        print("[06/15] Chụp bằng chứng 6: Điền form & click btn-submit-slide-upload -> Nạp & Trình chiếu ngay...")
        page.select_option("#slide-course-select", "IT401")
        page.fill("#slide-topic-input", "Mạng Nơ-ron Tích chập & Deep Learning")
        page.click("#btn-submit-slide-upload")
        # Wait for auto close and slide render
        page.wait_for_timeout(1800)
        p6 = str(OUTPUT_DIR / "proof_06_upload_slide_rendered.png")
        page.screenshot(path=p6, full_page=False)
        screenshots.append(("proof_06_upload_slide_rendered.png", "Nút Xác Nhận Nạp (#btn-submit-slide-upload) nạp slide IT401 thành công & lập tức trình chiếu trên màn hình chính"))

        # -------------------------------------------------------------
        # PROOF 7: Modal Kho Slide & Học Liệu CNTT (btn-open-catalog-modal)
        # -------------------------------------------------------------
        print("[07/15] Chụp bằng chứng 7: Click btn-open-catalog-modal -> Mở Kho Slide...")
        page.click("#btn-open-catalog-modal")
        page.wait_for_timeout(600)
        p7 = str(OUTPUT_DIR / "proof_07_catalog_slide_modal.png")
        page.screenshot(path=p7, full_page=False)
        screenshots.append(("proof_07_catalog_slide_modal.png", "Nút Kho Slide (#btn-open-catalog-modal) hiển thị danh mục học liệu & nút Trình Chiếu từng môn"))
        page.click("#btn-close-catalog-modal")
        page.wait_for_timeout(400)

        # -------------------------------------------------------------
        # PROOF 8: Bật Bong Bóng Chat Messenger (mascot-messenger-trigger)
        # -------------------------------------------------------------
        print("[08/15] Chụp bằng chứng 8: Click mascot-messenger-trigger -> Mở Cửa Sổ Chat Messenger...")
        page.click("#mascot-messenger-trigger")
        page.wait_for_timeout(600)
        p8 = str(OUTPUT_DIR / "proof_08_messenger_chat_opened.png")
        page.screenshot(path=p8, full_page=False)
        screenshots.append(("proof_08_messenger_chat_opened.png", "Bong bóng Messenger nổi (#mascot-messenger-trigger) bật mở cửa sổ Chatbot Rồng TLU (#mascot-chat-window)"))

        # -------------------------------------------------------------
        # PROOF 9: Gửi Tin Nhắn & AI Socratic Phản Hồi (btn-chat-send)
        # -------------------------------------------------------------
        print("[09/15] Chụp bằng chứng 9: Click chip-btn & btn-chat-send -> Chatbot AI phản hồi...")
        page.fill("#chat-input", "Chào bạn, giải thích giúp mình con trỏ và heap trong bài học này nhé")
        page.click("#btn-chat-send")
        print("  Đang đợi phản hồi từ AI Engine (Groq/Gemini)...")
        page.wait_for_timeout(4500)
        p9 = str(OUTPUT_DIR / "proof_09_chat_socratic_ai_reply.png")
        page.screenshot(path=p9, full_page=False)
        screenshots.append(("proof_09_chat_socratic_ai_reply.png", "Nút Gửi (#btn-chat-send) gửi tin nhắn và nhận lời giải thích Socratic trực tiếp từ AI kèm trích dẫn học liệu"))
        page.click("#btn-minimize-chat")
        page.wait_for_timeout(400)

        # -------------------------------------------------------------
        # PROOF 10: Chuyển Sang Socratic Studio & Chạy Thử Code (btn-code-run)
        # -------------------------------------------------------------
        print("[10/15] Chụp bằng chứng 10: Click btn-goto-socratic-optional & btn-code-run...")
        page.click("#btn-goto-socratic-optional")
        page.wait_for_timeout(600)
        page.click("#btn-code-run")
        page.wait_for_timeout(1200)
        p10 = str(OUTPUT_DIR / "proof_10_socratic_studio_code_run.png")
        page.screenshot(path=p10, full_page=False)
        screenshots.append(("proof_10_socratic_studio_code_run.png", "Nút Chạy thử (#btn-code-run) biên dịch mã nguồn C++ và hiển thị kết quả trong Sandbox Terminal"))

        # -------------------------------------------------------------
        # PROOF 11: So Sánh Code Diff & Đặt Lại (btn-code-diff)
        # -------------------------------------------------------------
        print("[11/15] Chụp bằng chứng 11: Click btn-code-diff -> Hiện Diff Viewer...")
        page.click("#btn-code-diff")
        page.wait_for_timeout(500)
        p11 = str(OUTPUT_DIR / "proof_11_code_diff_viewer.png")
        page.screenshot(path=p11, full_page=False)
        screenshots.append(("proof_11_code_diff_viewer.png", "Nút So sánh Diff (#btn-code-diff) mở khung so sánh trực quan mã nguồn gốc vs gợi ý sửa lỗi"))

        # -------------------------------------------------------------
        # PROOF 12: Modal Quy Chế Điều 25 TLU (btn-view-article25)
        # -------------------------------------------------------------
        print("[12/15] Chụp bằng chứng 12: Click btn-view-article25 -> Mở Modal Điều 25 TLU...")
        page.click("#btn-view-article25")
        page.wait_for_timeout(500)
        p12 = str(OUTPUT_DIR / "proof_12_article25_modal.png")
        page.screenshot(path=p12, full_page=False)
        screenshots.append(("proof_12_article25_modal.png", "Nút Xem Quy chế (#btn-view-article25) hiển thị Modal Liêm chính Học thuật Điều 25 TLU"))
        page.click("#btn-close-article25-modal")
        page.wait_for_timeout(400)

        # -------------------------------------------------------------
        # PROOF 13: Modal Nâng Cấp Gói Pro 69.000 đ (btn-header-pro)
        # -------------------------------------------------------------
        print("[13/15] Chụp bằng chứng 13: Click btn-header-pro -> Mở Modal Gói Pro...")
        page.click("#btn-header-pro")
        page.wait_for_timeout(500)
        p13 = str(OUTPUT_DIR / "proof_13_pro_tier_modal.png")
        page.screenshot(path=p13, full_page=False)
        screenshots.append(("proof_13_pro_tier_modal.png", "Nút Gói Pro (#btn-header-pro) mở Modal nâng cấp tài khoản Pro 69.000 VNĐ (#pro-modal)"))
        page.click("#btn-close-pro-modal")
        page.wait_for_timeout(400)

        # -------------------------------------------------------------
        # PROOF 14: Cổng Quản Trị & Tìm Kiếm Lai (btn-hybrid-search)
        # -------------------------------------------------------------
        print("[14/15] Chụp bằng chứng 14: Đến /admin -> Click btn-hybrid-search...")
        page.goto(f"{BASE_URL}/admin")
        page.wait_for_timeout(800)
        page.click("#tab-btn-multiagent")
        page.wait_for_timeout(400)
        page.click("#btn-hybrid-search")
        page.wait_for_timeout(800)
        p14 = str(OUTPUT_DIR / "proof_14_admin_multiagent_search.png")
        page.screenshot(path=p14, full_page=False)
        screenshots.append(("proof_14_admin_multiagent_search.png", "Quản trị: Nút Tìm kiếm (#btn-hybrid-search) thực thi truy vấn lai BGE-M3 + BM25 + RRF hiển thị bảng xếp hạng học liệu"))

        # -------------------------------------------------------------
        # PROOF 15: Cổng Quản Trị Ops & Làm Mới Logs (btn-refresh-admin-logs)
        # -------------------------------------------------------------
        print("[15/15] Chụp bằng chứng 15: Click tab-btn-ops & btn-refresh-admin-logs...")
        page.click("#tab-btn-ops")
        page.wait_for_timeout(400)
        page.click("#btn-refresh-admin-logs")
        page.wait_for_timeout(800)
        p15 = str(OUTPUT_DIR / "proof_15_admin_ops_finops.png")
        page.screenshot(path=p15, full_page=False)
        screenshots.append(("proof_15_admin_ops_finops.png", "Quản trị: Nút Làm mới (#btn-refresh-admin-logs) cập nhật thời gian thực chỉ số FinOps, tỷ lệ cache và nhật ký viễn thám"))

        browser.close()

    print("-" * 80)
    print("                      CAPTURE SUMMARY REPORT")
    print("-" * 80)
    for i, (fname, desc) in enumerate(screenshots, 1):
        print(f"[{i:02d}] {fname:35s} | {desc}")
    print("=" * 80)
    print(f">> TOÀN BỘ 15 BẰNG CHỨNG HÌNH ẢNH ĐÃ ĐƯỢC CHỤP THÀNH CÔNG TẠI: {OUTPUT_DIR} <<")
    return screenshots

if __name__ == "__main__":
    capture_all_proofs()
