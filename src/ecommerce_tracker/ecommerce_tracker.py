import sys
import codecs
import pandas as pd
from datetime import datetime
import helium
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from time import sleep
from PIL import Image
import io
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
from dataclasses import dataclass
from smolagents import CodeAgent, tool, OpenAIServerModel
from smolagents.agents import ActionStep

# Load environment variables
load_dotenv()

# Initialize the vision-language model
model = OpenAIServerModel(
    api_key=os.getenv("FIREWORKS_API_KEY"),
    api_base="https://api.fireworks.ai/inference/v1",
    model_id="accounts/fireworks/models/qwen2-vl-72b-instruct",
)

@dataclass
class ProductInfo:
    name: str
    price: float
    availability: str
    rating: Optional[float] = None
    screenshot_path: Optional[str] = None
    site: str = "noon.com"

def save_screenshot(step_log: ActionStep, agent: CodeAgent) -> None:
    """Callback to save screenshots during agent execution"""
    sleep(1.0)  # Let animations complete
    driver = helium.get_driver()
    if driver:
        png_bytes = driver.get_screenshot_as_png()
        image = Image.open(io.BytesIO(png_bytes))
        step_log.observations_images = [image.copy()]
        
        # Save screenshot to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"product_screenshot_{timestamp}.png"
        image.save(filename)
        
        # Update step log with file path
        step_log.observations = f"Screenshot saved: {filename}"

@tool
def search_product(keyword: str) -> str:
    """Search for a product on the current e-commerce site.
    
    Args:
        keyword: The product name or search term to look for
        
    Returns:
        str: A message confirming the search was performed
    """
    search_box = helium.S("#searchBar")
    helium.click(search_box)
    helium.write(keyword, into=search_box)
    sleep(1)
    
    try:
        helium.click(helium.Button("بحث"))  # Arabic "Search"
    except:
        helium.press(helium.ENTER)
    
    return f"Searching for {keyword}"

@tool
def scroll_page(pixels: int = 800) -> str:
    """Scroll the page down by a specified number of pixels.
    
    Args:
        pixels: Number of pixels to scroll down (default: 800)
        
    Returns:
        str: A message confirming the scroll action
    """
    helium.scroll_down(pixels)
    sleep(0.5)
    return f"Scrolled down {pixels} pixels"

@tool
def close_popups() -> str:
    """Close any visible popups or cookie consent modals on the page.
    
    Returns:
        str: A message indicating whether popups were found and closed
    """
    try:
        if helium.Text("Accept Cookies").exists():
            helium.click("Accept")
        return "Closed popups"
    except:
        return "No popups found"

@tool
def extract_product_info(container_selector: str = "div[class*='grid'] > span[class*='wrapper productContainer']") -> List[ProductInfo]:
    """Extract product information from containers on the current page.
    
    Args:
        container_selector: CSS selector for product containers (default: standard noon.com container)
        
    Returns:
        List[ProductInfo]: List of extracted product information
    """
    driver = helium.get_driver()
    results = []
    
    containers = driver.find_elements(By.CSS_SELECTOR, container_selector)
    print(f"Found {len(containers)} product containers")
    
    for container in containers:
        try:
            product = ProductInfo(
                name='',
                price=0.0,
                availability='',
                site='noon.com'
            )
            
            # Extract name
            name_elem = container.find_element(By.CSS_SELECTOR, "div[data-qa='product-name']")
            if name_elem:
                product.name = name_elem.get_attribute('title')
            
            # Extract price with fallbacks
            price_selectors = [
                "strong.amount",
                "div[class*='fUFHwr'] strong",
                "span.currency + strong",
                "[class*='amount']"
            ]
            
            for selector in price_selectors:
                try:
                    price_elem = container.find_element(By.CSS_SELECTOR, selector)
                    if price_elem and price_elem.text:
                        price_text = ''.join(filter(str.isdigit, price_elem.text))
                        product.price = float(price_text)
                        break
                except:
                    continue
            
            # Extract rating and availability
            try:
                rating_elem = container.find_element(By.CSS_SELECTOR, "div[class*='ioGuPV'], div[class*='sc-2709a77c-2']")
                if rating_elem:
                    product.rating = float(rating_elem.text.split('/')[0])
            except:
                pass
            
            try:
                avail_elem = container.find_element(By.CSS_SELECTOR, "span[class*='gkJOgT'], span[class*='sc-cd83bba5-5']")
                if avail_elem:
                    product.availability = avail_elem.text.strip()
            except:
                pass
            
            if product.name or product.price:
                results.append(product)
                
        except Exception as e:
            print(f"Error extracting product data: {str(e)}")
            continue
            
    return results

def track_product(product_name: str, site: str = "noon.com") -> List[ProductInfo]:
    """Track product prices and information using CodeAgent"""
    
    # Initialize the agent
    agent = CodeAgent(
        tools=[search_product, scroll_page, close_popups, extract_product_info],
        model=model,  # You'll need to configure this based on your setup
        step_callbacks=[save_screenshot],
        max_steps=15,
        verbosity_level=2
    )
    
    # Create the task prompt
    task = f"""
    Follow these steps to track product information on {site}:
    1. Navigate to the site and handle any popups
    2. Search for the product: {product_name}
    3. Scroll through results to ensure all products load
    4. Extract product information from all visible containers
    5. Save screenshots for verification
    
    Return the collected product information.
    """
    
    try:
        # Start browser
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--lang=ar')
        chrome_options.add_argument('--accept-lang=ar')
        chrome_options.add_argument('--charset=UTF-8')
        
        driver = helium.start_chrome(options=chrome_options, headless=False)
        
        # Navigate to site
        helium.go_to(f"https://www.{site}/egypt-ar/")
        sleep(3)
        
        # Run the agent
        results = agent.run(task)
        
        # Save results
        if results:
            df = pd.DataFrame([
                {
                    'Name': r.name,
                    'Price': r.price,
                    'Rating': r.rating,
                    'Availability': r.availability,
                    'Screenshot': r.screenshot_path,
                    'Site': r.site
                } for r in results
            ])
            
            filename = f"noon_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            print(f"\nResults saved to {filename}")
            
        return results
        
    except Exception as e:
        print(f"Error during tracking: {str(e)}")
        return []
    finally:
        try:
            helium.kill_browser()
        except:
            pass

# Set up console for Arabic text
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer) 