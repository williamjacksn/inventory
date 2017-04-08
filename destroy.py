import inventory.sql
import logging
import os
import sys

logging.basicConfig(stream=sys.stdout, level='DEBUG', format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
d = inventory.sql.InventoryDatabase(os.environ.get('DSN'))
d.destroy()
