import click
from typing import List
import os
from datetime import datetime
from dotenv import load_dotenv
from .price_tracker_agent import PriceTrackerAgent
from smolagents import OpenAIServerModel

# Load environment variables from .env file
load_dotenv()

@click.command()
@click.argument('product_name')
@click.option('--sites', '-s', multiple=True, help='E-commerce sites to check')
@click.option('--output-dir', '-o', default='reports', help='Directory to save reports')
def track_prices(product_name: str, sites: List[str], output_dir: str):
    """Track prices for a product across e-commerce sites"""
    
    # Verify API key is set
    api_key = os.getenv("FIREWORKS_API_KEY")
    if not api_key:
        raise click.ClickException(
            "FIREWORKS_API_KEY not found. Please set it in your .env file or environment variables."
        )
    
    if not sites:
        sites = ['amazon.com', 'walmart.com', 'target.com']  # Default sites
        
    # Initialize model with specific configuration
    model = OpenAIServerModel(
        api_key=api_key,
        api_base="https://api.fireworks.ai/inference/v1",
        model_id="accounts/fireworks/models/qwen2-vl-72b-instruct",
        max_tokens=2048,
        temperature=0.7
    )
    
    agent = PriceTrackerAgent(model=model)
    
    try:
        results = agent.track_product(product_name, sites)
        
        # Create report directory
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save report
        report_path = os.path.join(output_dir, f"report_{timestamp}.txt")
        with open(report_path, 'w') as f:
            f.write(f"Price Report for: {product_name}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for result in results:
                f.write(f"\nSite: {result.site}\n")
                f.write(f"Price: ${result.price:.2f}\n")
                f.write(f"Availability: {result.availability}\n")
                if result.seller_rating:
                    f.write(f"Seller Rating: {result.seller_rating}/5.0\n")
                    
                # Save screenshot
                if result.screenshot:
                    screenshot_path = os.path.join(
                        output_dir, 
                        f"screenshot_{timestamp}_{result.site.replace('.', '_')}.png"
                    )
                    result.screenshot.save(screenshot_path)
                    f.write(f"Screenshot saved: {screenshot_path}\n")
                    
        click.echo(f"Report generated: {report_path}")
        
    finally:
        agent.cleanup()

if __name__ == '__main__':
    track_prices() 