from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from PIL import Image
import helium
from io import BytesIO
import time
from smolagents import tool
import random
import undetected_chromedriver as uc
import os

class BrowserManager:
    def __init__(self, headless: bool = True):
        self.driver = None
        self.headless = headless
        self._close_popups_tool = None
        
    def initialize(self) -> None:
        """Initialize the browser with configured options"""
        try:
            # First try with undetected-chromedriver
            options = uc.ChromeOptions()
            if self.headless:
                options.add_argument('--headless=new')
            
            # Add anti-detection measures
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-extensions')
            
            # Add random user agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            ]
            options.add_argument(f'user-agent={random.choice(user_agents)}')
            
            try:
                print("Initializing undetected-chromedriver...")
                self.driver = uc.Chrome(options=options, version_main=131)
                print("Successfully initialized undetected-chromedriver")
            except Exception as e:
                print(f"Failed to initialize with version_main=131: {str(e)}")
                print("Trying without version specification...")
                self.driver = uc.Chrome(options=options)
                
        except Exception as e:
            print(f"Failed to initialize undetected-chromedriver: {str(e)}")
            print("Falling back to regular ChromeDriver...")
            
            options = Options()
            if self.headless:
                options.add_argument('--headless=new')
            
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--start-maximized')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            self.driver = webdriver.Chrome(options=options)
        
        print("Setting up helium...")
        helium.set_driver(self.driver)
        
        print("Creating popup tool...")
        self._close_popups_tool = create_close_popups_tool(self.driver)
        
    @property
    def close_popups_tool(self):
        """Get the close popups tool configured with current driver"""
        return self._close_popups_tool
        
    def wait_and_find_element(self, selector: str, timeout: int = 10) -> Optional[webdriver.remote.webelement.WebElement]:
        """Wait for and find an element using a CSS selector"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        except Exception as e:
            print(f"Failed to find element {selector}: {str(e)}")
            return None
            
    def get_page_source(self) -> str:
        """Get current page source for debugging"""
        return self.driver.page_source if self.driver else ""
        
    def get_current_url(self) -> str:
        """Get current URL for debugging"""
        return self.driver.current_url if self.driver else ""
        
    def capture_screenshot(self) -> Optional[Image.Image]:
        """Capture screenshot of current page"""
        if not self.driver:
            return None
            
        time.sleep(1.0)  # Allow for animations
        png_bytes = self.driver.get_screenshot_as_png()
        return Image.open(BytesIO(png_bytes))
        
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()

def create_close_popups_tool(driver: webdriver.Chrome):
    """Create a close popups tool configured with the given driver"""
    @tool
    def close_popups() -> str:
        """Close common modal popups and overlays on the current page."""
        modal_selectors = [
            "[role='dialog']",
            "button[class*='close']",
            "[class*='modal']",
            "[class*='modal'] button",
            "[class*='CloseButton']",
            "[aria-label*='close']",
            ".modal-close",
            ".modal-overlay",
            "[class*='overlay']"
        ]
        
        wait = WebDriverWait(driver, timeout=0.5)
        
        for selector in modal_selectors:
            try:
                elements = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                for element in elements:
                    if element.is_displayed():
                        driver.execute_script("arguments[0].click();", element)
            except Exception:
                continue
                
        # Try closing with Escape key
        from selenium.webdriver.common.keys import Keys
        try:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        except:
            pass
            
        return "Attempted to close popups"
    
    return close_popups 