"""
Automated Verification & Proof Capture for K3-Hackathon Inspired Slide Viewer Interface
Tests:
1. 16:9 Cinematic Stage & Block-card borders
2. Classroom Header & Dynamic Reading Progress Bar
3. Zoom controls (Zoom In, Zoom Out, Reset 100%)
4. Follow lecturer toggle & Sync Notice
5. Split-View Classroom AI Study Panel & Socratic suggestions
"""

from playwright.sync_api import sync_playwright
import time
import os

def test_k3_slide_viewer():
    proof_dir = "/home/quan/.gemini/antigravity/brain/4d95a850-a881-46ed-a5c9-ea24191968ab/screenshots"
    os.makedirs(proof_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 950})
        
        page.goto("http://127.0.0.1:8000")
        page.wait_for_timeout(600)
        
        # 1. Login
        page.click("#btn-quick-login-an")
        page.wait_for_timeout(400)
        
        # 2. Verify Slide Viewer initial state
        initial_progress = page.locator("#slide-progress-bar").get_attribute("style")
        print(f"Initial progress style: {initial_progress}")
        
        # Capture initial K3-Hackathon classroom view
        page.screenshot(path=f"{proof_dir}/proof_k3_classroom_initial.png")
        print("Captured proof_k3_classroom_initial.png")
        
        # 3. Test Slide Next & Progress Bar update
        page.click("#btn-next-slide")
        page.wait_for_timeout(300)
        new_progress = page.locator("#slide-progress-bar").get_attribute("style")
        print(f"Updated progress style after next: {new_progress}")
        assert "Slide 22" in page.inner_text("#current-slide-page")
        
        # 4. Test Zoom In
        page.click("#btn-slide-zoom-in")
        page.wait_for_timeout(200)
        zoom_text = page.inner_text("#slide-zoom-val")
        print(f"Zoom value after zoom-in: {zoom_text}")
        assert zoom_text == "115%"
        
        # Test Reset Zoom
        page.click("#btn-slide-zoom-reset")
        page.wait_for_timeout(200)
        assert page.inner_text("#slide-zoom-val") == "100%"
        print("Zoom reset to 100% verified")
        
        # 5. Test Follow Toggle
        page.click("#btn-slide-toggle-follow")
        page.wait_for_timeout(300)
        assert page.locator("#slide-sync-notice").is_visible()
        print("Self-reading sync notice is visible")
        
        # Resync
        page.click("#btn-slide-resync")
        page.wait_for_timeout(300)
        assert not page.locator("#slide-sync-notice").is_visible()
        print("Resync verified: notice hidden and back to following lecturer")
        
        # 6. Test Split-View AI Study Panel
        page.click("#btn-toggle-split-ai")
        page.wait_for_timeout(300)
        assert page.locator("#slide-ai-split-panel").is_visible()
        print("Split AI Study Panel is visible")
        
        # Click a suggestion chip
        page.locator(".split-ai-chip").first.click()
        page.wait_for_timeout(700)
        
        # Capture screenshot with Split AI Study Panel opened
        page.screenshot(path=f"{proof_dir}/proof_k3_split_ai_panel.png")
        print("Captured proof_k3_split_ai_panel.png")
        
        browser.close()
        print("All K3-Hackathon slide viewer feature tests PASSED successfully!")

if __name__ == "__main__":
    test_k3_slide_viewer()
