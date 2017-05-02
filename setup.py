from setuptools import setup

setup(
    name='inventory',
    version='1.0.5',
    description='A basic inventory management web app',
    install_requires=['Flask', 'Flask-OAuth2-Login', 'Flask-SSLify', 'lxml', 'psycopg2', 'waitress'],
    packages=['inventory'],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'check_stock = inventory.check_stock:main',
            'inventory = inventory.inventory:main'
        ]
    }
)
