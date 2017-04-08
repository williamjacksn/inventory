import inventory.inventory
import logging
import sys

logging.basicConfig(stream=sys.stdout, level='DEBUG', format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
inventory.inventory.main()
