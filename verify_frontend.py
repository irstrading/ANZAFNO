from playwright.sync_api import sync_playwright

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # Navigate to the dashboard
            page.goto("http://localhost:5173", wait_until="networkidle")

            # Take a screenshot
            page.screenshot(path="frontend_verification.png", full_page=True)
            print("Verification successful! Screenshot saved as frontend_verification.png")

        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="frontend_failure.png", full_page=True)
        finally:
            browser.close()

if __name__ == "__main__":
    verify_frontend()
