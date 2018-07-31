from setuptools import setup

setup(
    name='inventory',
    version='2.0.1',
    description='A basic inventory management web app',
    url='https://github.com/williamjacksn/inventory',
    author='William Jackson',
    author_email='william@subtlecoolness.com',
    install_requires=['Flask', 'Flask-OAuth2-Login', 'Flask-SSLify', 'psycopg2', 'waitress'],
    packages=['inventory'],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'inventory = inventory.inventory:main'
        ]
    }
)
