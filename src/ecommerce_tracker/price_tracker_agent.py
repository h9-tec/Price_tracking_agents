from dataclasses import dataclass
from typing import List, Optional, Dict
from PIL import Image as PILImage
from smolagents import CodeAgent, tool
from smolagents.agents import ActionStep
from helium import *
import time
import random
from .browser_manager import BrowserManager

HELIUM_INSTRUCTIONS = """
Use the browser that is already initialized. The following tools and functions are available:
- helium_goto(url)
- helium_write(text, into=element)
- helium_click(element)
- helium_press_enter()
- helium_exists(selector)
- helium_find_all(selector)

Try to find and extract product information:

1. Navigate to the search page using helium_goto.
2. Find and interact with the search box using helium_write and helium_click.
3. Extract price, availability, and rating using helium_exists and helium_find_all.
4. Return the results.

Example selectors that might work:
- Search box: input[data-qa="txt_searchBar"], input[type="search"], input[placeholder*="Search"]
- Price: div[data-qa="product-price"], .priceNow, span[data-currency="EGP"]
- Availability: div[data-qa="availability"], .stockStatus, .delivery-message
- Rating: div[data-qa="product-rating"], .ratingValue, .rating-stars

The code should handle errors gracefully and return default values if data cannot be found.
"""

@dataclass
class ProductInfo:
    site: str
    price: float
    availability: str
    seller_rating: Optional[float]
    screenshot: Optional[PILImage.Image]

# First create tool-wrapped versions of the Helium functions
@tool
def helium_goto(url: str) -> None:
    """Navigate to a specified URL using Helium.
    
    Args:
        url: The URL to navigate to (e.g. 'https://www.example.com')
    """
    go_to(url)

@tool
def helium_write(text: str, into: str = None) -> None:
    """Write text into a specified element using Helium.
    
    Args:
        text: The text to write
        into: CSS selector for the target element (e.g. 'input[type="search"]')
    """
    if into:
        write(text, into=S(into))
    else:
        write(text)

@tool
def helium_click(element: str) -> None:
    """Click on an element using Helium.
    
    Args:
        element: CSS selector for the element to click (e.g. 'button.submit')
    """
    click(S(element))

@tool
def helium_press_enter() -> None:
    """Press the Enter key."""
    press(ENTER)

@tool
def helium_exists(selector: str) -> bool:
    """Check if an element exists on the page.
    
    Args:
        selector: CSS selector to check for existence (e.g. 'div.product-price')
    
    Returns:
        bool: True if the element exists, False otherwise
    """
    return S(selector).exists()

@tool
def helium_find_all(selector: str) -> List:
    """Find all elements matching a selector.
    
    Args:
        selector: CSS selector to find elements (e.g. '.product-item')
    
    Returns:
        List: List of matching elements
    """
    return find_all(S(selector))

@tool
def helium_wait_for(selector: str, timeout: int = 10) -> bool:
    """Wait for an element to appear on the page.
    
    Args:
        selector: CSS selector to wait for
        timeout: Maximum time to wait in seconds
    
    Returns:
        bool: True if element was found, False if timeout occurred
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if S(selector).exists():
            return True
        time.sleep(0.5)
    return False

class PriceTrackerAgent:
    def __init__(self, model, max_steps: int = 10):
        self.browser = BrowserManager(headless=True)
        self.browser.initialize()
        
        def screenshot_callback(step_log: ActionStep, agent: CodeAgent) -> None:
            try:
                screenshot = self.browser.capture_screenshot()
                if screenshot:
                    if not hasattr(step_log, 'observations_images') or step_log.observations_images is None:
                        step_log.observations_images = []
                    step_log.observations_images.append(screenshot)
                
                url_info = f"Current URL: {self.browser.driver.current_url}"
                if not hasattr(step_log, 'observations') or step_log.observations is None:
                    step_log.observations = url_info
                else:
                    step_log.observations += f"\n{url_info}"
            except Exception as e:
                print(f"Screenshot callback error: {str(e)}")

        self.agent = CodeAgent(
            tools=[
                self.browser.close_popups_tool,
                helium_goto,
                helium_write,
                helium_click,
                helium_press_enter,
                helium_exists,
                helium_find_all,
                helium_wait_for
            ],
            model=model,
            additional_authorized_imports=["helium", "time", "random"],
            step_callbacks=[screenshot_callback],
            max_steps=max_steps,
            verbosity_level=1
        )
        
    def track_product(self, product_name: str, sites: List[str] = None) -> List[ProductInfo]:
        results = []

        try:
            scraping_code = f"""
# Initialize result dictionary
result = {{
    'price': '0.00',
    'availability': 'Unknown',
    'rating': '0.0'
}}

try:
    # Step 1: Navigate to site
    print("Step 1: Navigating to noon.com...")
    helium_goto("https://www.noon.com/egypt-en/")
    time.sleep(5)  # Wait for initial page load
    
    # Step 2: Find and interact with search box
    print("Step 2: Looking for search box...")
    search_selectors = [
        "input[type='search']",
        "input[data-qa='txt_searchBar']",
        "input[placeholder*='Search']"
    ]
    
    search_found = False
    for selector in search_selectors:
        if helium_exists(selector):
            print(f"Found search box with selector: {{selector}}")
            helium_write("{product_name}", selector)
            helium_press_enter()
            search_found = True
            time.sleep(5)  # Wait for search results
            break
        time.sleep(1)
    
    if not search_found:
        print("Failed to find search box")
        return result
    
    # Step 3: Wait for and extract product information
    print("Step 3: Extracting product information...")
    time.sleep(3)  # Wait for products to load
    
    # Find price
    price_selectors = [
        "div[data-qa='product-price']",
        "div.priceNow",
        "span[data-currency='EGP']",
        "div.productPrice"
    ]
    
    for selector in price_selectors:
        if helium_exists(selector):
            elements = helium_find_all(selector)
            if elements:
                price_text = elements[0].web_element.text
                result['price'] = price_text.replace('EGP', '').replace('$', '').strip()
                print(f"Found price: {{result['price']}}")
                break
        time.sleep(0.5)
    
    # Find availability
    availability_selectors = [
        "div[data-qa='delivery-message']",
        "div.fulfillmentText",
        "div.stockStatus",
        "div[data-qa='availability']"
    ]
    
    for selector in availability_selectors:
        if helium_exists(selector):
            elements = helium_find_all(selector)
            if elements:
                result['availability'] = elements[0].web_element.text.strip()
                print(f"Found availability: {{result['availability']}}")
                break
        time.sleep(0.5)
    
    # Find rating
    rating_selectors = [
        "div[data-qa='product-rating']",
        "div.ratingValue",
        "div.rating",
        "span.stars"
    ]
    
    for selector in rating_selectors:
        if helium_exists(selector):
            elements = helium_find_all(selector)
            if elements:
                rating_text = elements[0].web_element.text.strip()
                result['rating'] = rating_text.split('/')[0].strip()
                print(f"Found rating: {{result['rating']}}")
                break
        time.sleep(0.5)

except Exception as e:
    print(f"Error during scraping: {{str(e)}}")

# Print final results
print("\\nFinal Results:")
print(f"Price: ${{result['price']}}")
print(f"Availability: {{result['availability']}}")
print(f"Rating: {{result['rating']}}/5")

return result
"""

            # Run the code using the agent
            print("\nStarting web scraping...")
            response = self.agent.run(scraping_code)
            print("Web scraping completed")

            # Parse the response
            try:
                output_text = ""
                screenshot = None

                if hasattr(response, 'steps') and response.steps:
                    # Collect all output from steps
                    for step in response.steps:
                        if step.output:
                            output_text += step.output + "\n"
                        if hasattr(step, 'observations') and step.observations:
                            output_text += step.observations + "\n"
                        if hasattr(step, 'observations_images') and step.observations_images:
                            screenshot = step.observations_images[-1]

                print("\nParsing output...")
                print(f"Raw output:\n{output_text}")

                # Extract values
                price = self.extract_field(output_text, "Price", default=0.0, is_float=True)
                availability = self.extract_field(output_text, "Availability", default="Unknown")
                rating = self.extract_field(output_text, "Rating", default=0.0, is_float=True)

                print(f"\nExtracted values:")
                print(f"Price: ${price}")
                print(f"Availability: {availability}")
                print(f"Rating: {rating}")

                results.append(ProductInfo(
                    site="noon.com",
                    price=price,
                    availability=availability,
                    seller_rating=rating,
                    screenshot=screenshot
                ))

            except Exception as parse_error:
                print(f"Error parsing response: {str(parse_error)}")
                results.append(ProductInfo(
                    site="noon.com",
                    price=0.0,
                    availability="Error parsing response",
                    seller_rating=0.0,
                    screenshot=None
                ))

        except Exception as track_error:
            print(f"Error tracking product: {str(track_error)}")
            results.append(ProductInfo(
                site="noon.com",
                price=0.0,
                availability=f"Error: {str(track_error)}",
                seller_rating=0.0,
                screenshot=None
            ))

        return results
        
    def cleanup(self):
        """Clean up resources"""
        self.browser.cleanup()

    @staticmethod
    def extract_field(output: str, field_name: str, default, is_float: bool = False):
        """Extract a field value from the output text."""
        try:
            print(f"Extracting {field_name} from output...")
            if not output:
                print(f"No output text to extract {field_name}")
                return default
            
            # Find the last occurrence of the field in the output
            lines = output.split('\n')
            field_lines = [l for l in lines if field_name in l]
            if not field_lines:
                print(f"No lines found containing {field_name}")
                return default
            
            # Use the last occurrence of the field
            field_line = field_lines[-1]
            value = field_line.split(':', 1)[1].strip()
            if not value:
                print(f"Empty value for {field_name}")
                return default
            
            # Clean and convert the value
            if is_float:
                clean_value = ''.join(c for c in value if c.isdigit() or c in '.-')
                if not clean_value:
                    print(f"No numeric value found in {value}")
                    return default
                return float(clean_value)
            
            return value.strip('$ ')
        
        except Exception as e:
            print(f"Error extracting {field_name}: {str(e)}")
            return default