from playwright.sync_api import sync_playwright
import time
import os

class Visualizer:
    def __init__(self, output_dir="screenshots"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def capture_chart(self, symbol="BTC"):
        """
        Captures a screenshot of the TradingView chart for the given symbol.
        """
        url = f"https://www.tradingview.com/chart/?symbol={symbol}USD"
        output_path = f"{self.output_dir}/chart_{symbol}_{int(time.time())}.png"
        
        try:
            with sync_playwright() as p:
                # Launch browser (headless for server environments)
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Set viewport for a nice image size
                page.set_viewport_size({"width": 1280, "height": 720})
                
                print(f"Navigating to {url}...")
                page.goto(url)
                
                # Wait for chart to load (simple timeout, can be improved with selectors)
                page.wait_for_timeout(5000) 
                
                # Take screenshot
                page.screenshot(path=output_path)
                print(f"Screenshot saved to {output_path}")
                
                browser.close()
                return output_path
        except Exception as e:
            print(f"Error capturing chart: {e}")
            return None

if __name__ == "__main__":
    # Test visualizer
    viz = Visualizer()
    print("Capturing BTC chart...")
    viz.capture_chart("BTC")
