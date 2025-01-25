import click
from ecommerce_tracker import track_product

@click.command()
@click.argument('product_name')
@click.option('-s', '--site', default='noon.com', help='E-commerce site to search on')
def main(product_name, site):
    """Track product prices and availability on e-commerce sites."""
    track_product(product_name, site)

if __name__ == '__main__':
    main() 