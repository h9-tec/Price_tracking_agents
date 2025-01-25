import time
from helium import (
    start_chrome,
    kill_browser,
    go_to as helium_goto,
    write as helium_write,
    press as helium_press,
    find_all as helium_find_all,
    Text,
    S,
    ENTER,
)

def track_product(product_name, site="noon.com"):
    # Initialize result dictionary
    result = {
        'price': '0.00',
        'availability': 'Unknown',
        'rating': '0.0'
    }

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
            if S(selector).exists():
                print(f"Found search box with selector: {selector}")
                helium_write(product_name, into=S(selector))
                helium_press(ENTER)
                search_found = True
                time.sleep(5)  # Wait for search results
                break
            time.sleep(1)

        if not search_found:
            print("Failed to find search box")
            return result

        # Step 3: Extract product information
        print("Step 3: Extracting product information...")
        time.sleep(3)

        # Find price
        price_selectors = [
            "div[data-qa='product-price']",
            "div.priceNow",
            "span[data-currency='EGP']",
            "div.productPrice"
        ]

        for selector in price_selectors:
            element = S(selector)
            if element.exists():
                price_text = element.web_element.text
                result['price'] = price_text.replace('EGP', '').replace('$', '').strip()
                print(f"Found price: {result['price']}")
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
            element = S(selector)
            if element.exists():
                result['availability'] = element.web_element.text.strip()
                print(f"Found availability: {result['availability']}")
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
            element = S(selector)
            if element.exists():
                rating_text = element.web_element.text.strip()
                result['rating'] = rating_text.split('/')[0].strip()
                print(f"Found rating: {result['rating']}")
                break
            time.sleep(0.5)

    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    finally:
        try:
            kill_browser()
        except:
            pass

    # Print final results
    print("\nFinal Results:")
    print(f"Price: ${result['price']}")
    print(f"Availability: {result['availability']}")
    print(f"Rating: {result['rating']}/5")

    return result

if __name__ == "__main__":
    track_product("iPhone 16 Pro") 