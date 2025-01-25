# E-commerce Product Tracker

An intelligent e-commerce product tracking tool that uses vision-language models and browser automation to track prices and product information across various e-commerce sites.

## Features

- 🔍 Automated product search across e-commerce platforms
- 📸 Visual validation with screenshots
- 💰 Price tracking and comparison
- 📊 Detailed product information extraction
- 📝 Excel report generation
- 🌐 Multi-language support (including Arabic)
- 🤖 AI-powered navigation and data extraction

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd track
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package in development mode:
```bash
pip install -r requirements.txt
pip install -e .
```

4. Create a `.env` file in the project root with your API keys:
```env
FIREWORKS_API_KEY=your_fireworks_api_key
OPENAI_API_KEY=your_openai_api_key
NOON_URL=https://www.noon.com
```

## Usage

### Command Line Interface

Track a product using the command-line tool:

```bash
ecommerce-tracker "product name" -s site.com
```

Example:
```bash
ecommerce-tracker "iphone 15" -s noon.com
```

### Options

- `-s`, `--sites`: Specify e-commerce sites to check (can be multiple)
- `-o`, `--output-dir`: Directory to save reports (default: 'reports')

### Output

The tool generates:
- Excel report with product details
- Screenshots of product listings
- Console output with real-time progress

## Features in Detail

### Visual Validation
- Takes screenshots of product listings
- Saves visual evidence of prices and availability
- Helps verify data accuracy

### Price Tracking
- Extracts current prices
- Handles different price formats
- Supports multiple currencies

### Product Information
- Product name
- Price
- Availability status
- Seller rating
- Additional product details

### Browser Automation
- Intelligent navigation
- Popup handling
- Scroll management
- Multi-language support

## Development

### Project Structure
```
track/
├── src/
│   ├── ecommerce_tracker/
│   │   ├── __init__.py
│   │   ├── ecommerce_tracker.py
│   │   ├── browser_manager.py
│   │   └── price_tracker_agent.py
│   ├── __init__.py
│   └── cli.py
├── requirements.txt
├── setup.py
└── README.md
```

### Adding New Features

1. Tool Functions:
```python
@tool
def your_new_tool(param: str) -> str:
    """Your tool description.
    
    Args:
        param: Parameter description
        
    Returns:
        str: Return value description
    """
    # Tool implementation
    return result
```

2. Add the tool to the agent:
```python
agent = CodeAgent(
    tools=[existing_tools, your_new_tool],
    model=model,
    step_callbacks=[save_screenshot],
    max_steps=15
)
```

## Requirements

- Python 3.8+
- Chrome browser
- Internet connection
- Fireworks AI API key
- Required Python packages (see requirements.txt)

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Acknowledgments

- Built with [smolagents](https://github.com/smol-ai/smolagents)
- Uses Fireworks AI for vision-language processing
- Selenium and Helium for browser automation 