from setuptools import setup

setup(
    name='inventory',
    version='1.0.8',
    description='A basic inventory management web app',
    url='https://github.com/williamjacksn/inventory',
    author='William Jackson',
    author_email='william@subtlecoolness.com',
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
