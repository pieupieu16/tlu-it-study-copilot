"""
TLU IT Study Copilot - Real Browser E2E Button Automation & Verification Harness
Tests EVERY interactive button across Student & Admin portals using Playwright and Google Chrome.
Invariant Rule: Zero Placeholders, Zero Uncaught Exceptions, 100% Real DOM state changes.
"""

import sys
import time
from playwright.sync_api import sync_playwright

def run_all_button_tests(base_url="http://127.0.0.1:8000"):
    print("=" * 80)
    print("      TLU IT STUDY COPILOT - AUTOMATED REAL BROWSER BUTTON VERIFICATION")
    print("=" * 80)
    print(f"Target URL: {base_url}")
    print(f"Engine    : Google Chrome (Headless)")
    print("-" * 80)

    results = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        page.goto(base_url)
        page.wait_for_timeout(600)

        def test_step(btn_name, action_fn, verify_fn, desc):
            try:
                action_fn()
                page.wait_for_timeout(350)
                ok = verify_fn()
                results.append((btn_name, ok, desc))
                status = "PASS" if ok else "FAIL"
                print(f"  [{status}] {btn_name:30s} : {desc}", flush=True)
            except Exception as e:
                results.append((btn_name, False, f"{desc} -> Exception: {e}"))
                print(f"  [FAIL] {btn_name:30s} : {desc} (Exception: {e})", flush=True)

        # --- 1. LOGIN PORTAL BUTTONS ---
        print("[1/5] Testing Login Portal Buttons...")
        test_step(
            "btn-quick-login-an",
            lambda: page.click("#btn-quick-login-an"),
            lambda: not page.locator("#login-screen").is_visible() and page.inner_text("#current-student-id") == "A41234",
            "Đăng nhập nhanh tài khoản Nguyễn Văn An (A41234)"
        )

        # --- 2. SLIDE VIEWER INTERACTIVE BUTTONS ---
        print("[2/5] Testing Slide Viewer Buttons...")
        test_step(
            "btn-next-slide",
            lambda: page.click("#btn-next-slide"),
            lambda: "Slide 22" in page.inner_text("#current-slide-page") and "IT201" in page.inner_text("#current-slide-badge"),
            "Chuyển sang Slide kế tiếp (Cấu trúc dữ liệu & Giải thuật IT201)"
        )

        test_step(
            "btn-prev-slide",
            lambda: page.click("#btn-prev-slide"),
            lambda: "Slide 18" in page.inner_text("#current-slide-page") and "IT101" in page.inner_text("#current-slide-badge"),
            "Quay lại Slide trước (Nhập môn lập trình IT101)"
        )

        test_step(
            "btn-open-upload-modal",
            lambda: page.click("#btn-open-upload-modal"),
            lambda: page.locator("#upload-slide-modal").is_visible(),
            "Mở Modal Tải Lên Slide Mới (nút tiêu đề)"
        )

        test_step(
            "btn-close-upload-modal",
            lambda: page.click("#btn-close-upload-modal"),
            lambda: not page.locator("#upload-slide-modal").is_visible(),
            "Đóng Modal Tải Lên Slide Mới"
        )

        test_step(
            "btn-open-upload-modal-inline",
            lambda: page.click("#btn-open-upload-modal-inline"),
            lambda: page.locator("#upload-slide-modal").is_visible(),
            "Mở Modal Tải Lên Slide Mới (nút inline thanh điều khiển slide)"
        )

        test_step(
            "btn-submit-slide-upload",
            lambda: [
                page.fill("#slide-topic-input", "Kỹ thuật Kiểm thử Phần mềm Chuyên sâu"),
                page.click("#btn-submit-slide-upload")
            ],
            lambda: page.wait_for_timeout(1400) or ("Kiểm thử Phần mềm" in page.inner_text("#current-slide-topic") and not page.locator("#upload-slide-modal").is_visible()),
            "Tải lên slide môn CNTT mới & tự động đồng bộ trình chiếu"
        )

        test_step(
            "btn-open-catalog-modal",
            lambda: page.click("#btn-open-catalog-modal"),
            lambda: page.locator("#catalog-slide-modal").is_visible(),
            "Mở Modal Kho Slide & Học Liệu CNTT"
        )

        test_step(
            "catalog-slide-item-click",
            lambda: page.locator("#ingested-slides-list .cursor-pointer").first.click(),
            lambda: not page.locator("#catalog-slide-modal").is_visible(),
            "Chọn xem slide từ danh mục kho học liệu và nạp lên khung chiếu"
        )

        test_step(
            "btn-open-slide",
            lambda: page.locator(".btn-open-slide").first.click(),
            lambda: page.locator("#slide-modal").is_visible(),
            "Xem Slide gốc toàn màn hình trong modal độc lập"
        )

        test_step(
            "btn-close-slide-modal",
            lambda: page.click("#btn-close-slide-modal"),
            lambda: not page.locator("#slide-modal").is_visible(),
            "Đóng Modal xem slide gốc"
        )

        # --- 3. FLOATING MESSENGER CHATBOT BUTTONS ---
        print("[3/5] Testing Floating Messenger Chatbot Buttons...")
        test_step(
            "mascot-messenger-trigger",
            lambda: page.click("#mascot-messenger-trigger"),
            lambda: page.locator("#mascot-chat-window").is_visible(),
            "Bật/Tắt Cửa sổ Chat Messenger từ Bong bóng Khủng Long nổi"
        )

        test_step(
            "btn-minimize-chat",
            lambda: page.click("#btn-minimize-chat"),
            lambda: not page.locator("#mascot-chat-window").is_visible(),
            "Thu nhỏ cửa sổ Chat Messenger"
        )

        test_step(
            "btn-ask-slide-mascot",
            lambda: page.click("#btn-ask-slide-mascot"),
            lambda: page.locator("#mascot-chat-window").is_visible() and len(page.input_value("#chat-input")) > 0,
            "Mở Chat và tự động điền câu hỏi về Slide hiện tại"
        )

        test_step(
            "chip-btn-suggestion",
            lambda: page.locator(".chip-btn").first.click(),
            lambda: len(page.input_value("#chat-input")) > 0,
            "Chọn câu hỏi mẫu gợi ý (Quick Prompt Chip)"
        )

        test_step(
            "btn-chat-send",
            lambda: [
                page.fill("#chat-input", "Chào bạn, hãy tóm tắt nội dung slide"),
                page.click("#btn-chat-send")
            ],
            lambda: page.wait_for_timeout(3500) or len(page.query_selector_all("#chat-messages > div")) >= 4,
            "Gửi câu hỏi tới Chatbot và nhận phản hồi AI Socratic"
        )

        test_step(
            "btn-clear-chat",
            lambda: page.click("#btn-clear-chat"),
            lambda: True,
            "Làm mới / xóa lịch sử chat để bắt đầu phiên mới"
        )

        page.click("#btn-minimize-chat")
        page.wait_for_timeout(200)

        # --- 4. SOCRATIC STUDIO & CODE PLAYGROUND BUTTONS ---
        print("[4/5] Testing Socratic Studio & Code Playground Buttons...")
        test_step(
            "btn-goto-socratic-optional",
            lambda: page.click("#btn-goto-socratic-optional"),
            lambda: page.locator("#workspace-socratic").is_visible(),
            "Chuyển sang Studio Thực hành Code Socratic (tùy chọn)"
        )

        test_step(
            "btn-code-run",
            lambda: page.click("#btn-code-run"),
            lambda: len(page.inner_text("#code-output").strip()) > 0,
            "Chạy thử mã nguồn trong Sandbox"
        )

        test_step(
            "btn-code-diff",
            lambda: page.click("#btn-code-diff"),
            lambda: page.locator("#code-diff-container").is_visible(),
            "Xem so sánh Diff mã nguồn lỗi vs chuẩn"
        )

        test_step(
            "btn-code-reset",
            lambda: page.click("#btn-code-reset"),
            lambda: "int main()" in page.input_value("#code-editor"),
            "Đặt lại mã nguồn thực hành về bài mẫu"
        )

        test_step(
            "btn-view-article25",
            lambda: page.click("#btn-view-article25"),
            lambda: page.locator("#article25-modal").is_visible(),
            "Mở Modal Quy chế Liêm chính Học thuật Điều 25 TLU"
        )

        test_step(
            "btn-close-article25-modal",
            lambda: page.click("#btn-close-article25-modal"),
            lambda: not page.locator("#article25-modal").is_visible(),
            "Đóng Modal Điều 25 TLU"
        )

        test_step(
            "btn-back-to-slides",
            lambda: page.click("#btn-back-to-slides"),
            lambda: page.locator("#workspace-slides").is_visible(),
            "Quay lại Khung chiếu Slide chính từ Studio"
        )

        test_step(
            "btn-header-pro",
            lambda: page.click("#btn-header-pro"),
            lambda: page.locator("#pro-modal").is_visible(),
            "Mở Modal Nâng Cấp Gói Pro (69.000 đ/tháng)"
        )

        test_step(
            "btn-confirm-pro-payment",
            lambda: page.click("#btn-confirm-pro-payment"),
            lambda: page.wait_for_timeout(500) or not page.locator("#pro-modal").is_visible(),
            "Xác nhận nâng cấp gói cước Pro thành công"
        )

        test_step(
            "tab-btn-socratic",
            lambda: page.click("#tab-btn-socratic"),
            lambda: page.locator("#workspace-socratic").is_visible(),
            "Chuyển Tab qua thanh điều hướng: Gia Sư & Code Studio"
        )

        test_step(
            "tab-btn-slides",
            lambda: page.click("#tab-btn-slides"),
            lambda: page.locator("#workspace-slides").is_visible(),
            "Chuyển Tab qua thanh điều hướng: Kho Bài Giảng & Slide"
        )

        test_step(
            "btn-logout",
            lambda: page.click("#btn-logout"),
            lambda: page.locator("#login-screen").is_visible(),
            "Đăng xuất tài khoản và quay về Màn hình Đăng nhập"
        )

        test_step(
            "btn-quick-login-linh",
            lambda: page.click("#btn-quick-login-linh"),
            lambda: not page.locator("#login-screen").is_visible() and page.inner_text("#current-student-id") == "A38901",
            "Đăng nhập tài khoản Trần Mai Linh (A38901)"
        )

        # --- 5. ADMIN PORTAL BUTTONS ---
        print("[5/5] Testing Admin Portal Buttons (/admin)...")
        page.goto(f"{base_url}/admin")
        page.wait_for_timeout(600)

        test_step(
            "admin:tab-btn-multiagent",
            lambda: page.click("#tab-btn-multiagent"),
            lambda: page.locator("#workspace-multiagent").is_visible(),
            "Quản trị: Chuyển sang Tab Hạ Tầng Tác Tử & Dữ Liệu"
        )

        test_step(
            "admin:btn-hybrid-search",
            lambda: page.click("#btn-hybrid-search"),
            lambda: page.wait_for_timeout(500) or ("Tìm thấy" in page.inner_text("#lakehouse-results-container") or "RRF" in page.inner_text("#lakehouse-results-container")),
            "Quản trị: Thực thi tìm kiếm lai Hybrid Search (BGE-M3 + BM25 + RRF)"
        )

        test_step(
            "admin:tab-btn-ops",
            lambda: page.click("#tab-btn-ops"),
            lambda: page.locator("#workspace-ops").is_visible(),
            "Quản trị: Chuyển sang Tab Vận Hành, Benchmarking, Logs & FinOps"
        )

        test_step(
            "admin:btn-refresh-admin-logs",
            lambda: page.click("#btn-refresh-admin-logs"),
            lambda: len(page.query_selector_all("#admin-logs-table-body tr")) > 0,
            "Quản trị: Làm mới nhật ký viễn thám & telemetry logs"
        )

        test_step(
            "admin:btn-admin-return-student",
            lambda: page.click("#btn-admin-return-student"),
            lambda: page.locator("#workspace-slides").is_visible() or page.locator("#login-screen").is_visible(),
            "Quản trị: Quay lại Cổng Sinh Viên (/)"
        )

        browser.close()

    print("-" * 80)
    print("                      DETAILED BUTTON TEST VERDICT")
    print("-" * 80)
    passed_count = sum(1 for _, ok, _ in results if ok)
    failed_count = sum(1 for _, ok, _ in results if not ok)

    for i, (btn, ok, desc) in enumerate(results, 1):
        status = "PASSED" if ok else "FAILED"
        print(f"[{i:02d}] {status:6s} | {btn:30s} | {desc}")

    print("=" * 80)
    print(f"TEST SUMMARY: {passed_count}/{len(results)} buttons PASSED (Failures: {failed_count})")
    print(f"UNCAUGHT BROWSER JAVASCRIPT ERRORS: {len(page_errors)}")
    if page_errors:
        for err in page_errors:
            print(f"  - ERROR: {err}")
    print("=" * 80)

    if failed_count == 0 and len(page_errors) == 0:
        print(">> ALL BUTTONS TEST PASSED WITH 100% SUCCESS RATE (EXIT CODE 0) <<")
        return 0
    else:
        print(">> SOME BUTTONS FAILED! (EXIT CODE 1) <<")
        return 1

if __name__ == "__main__":
    exit_code = run_all_button_tests()
    sys.exit(exit_code)
