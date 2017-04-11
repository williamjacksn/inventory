from setuptools import setup

setup(
    name='inventory',
    version='1.0.1',
    description='A basic inventory management web app',
    install_requires=['Flask', 'Flask-OAuth2-Login', 'psycopg2', 'waitress'],
    packages=['inventory'],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'inventory = inventory.inventory:main'
        ]
    }
)