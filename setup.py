from setuptools import setup, find_packages

setup(
    name='ecommerce-tracker',
    version='0.1',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        'Click',
        'helium',
        'selenium',
        'undetected-chromedriver',
        'python-dotenv',
    ],
    entry_points={
        'console_scripts': [
            'ecommerce-tracker=cli:main',
        ],
    },
) 