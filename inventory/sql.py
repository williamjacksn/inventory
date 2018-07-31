import logging
import psycopg2
import psycopg2.extras
import uuid

log = logging.getLogger(__name__)
psycopg2.extras.register_uuid()


class InventoryDatabase:
    def __init__(self, dsn: str):
        self.cnx = psycopg2.connect(dsn=dsn, cursor_factory=psycopg2.extras.RealDictCursor)
        self.cnx.autocommit = True

    def _q(self, sql, args=None):
        if args is None:
            args = []
        with self.cnx.cursor() as c:
            c.execute(sql, args)
            return c.fetchall()

    def _q_one(self, sql, args=None):
        for row in self._q(sql, args):
            return row
        return None

    def _u(self, sql, args=None):
        if args is None:
            args = []
        with self.cnx.cursor() as c:
            c.execute(sql, args)
            return c.rowcount

    def _valid_order(self, params):
        # params = {
        #   'order_id': <uuid>,
        #   'user_email': 'user@example.com'
        # }
        sql = '''
            SELECT order_id
            FROM orders JOIN users USING (user_id)
            WHERE order_id = %(order_id)s AND user_email = %(user_email)s
        '''
        order = self._q_one(sql, params)
        return order is not None

    def _valid_sale(self, params):
        # params = {
        #   'sale_id': <uuid>,
        #   'user_email': 'user@example.com'
        # }
        sql = '''
            SELECT sale_id
            FROM sales JOIN users USING (user_id)
            WHERE sale_id = %(sale_id)s AND user_email = %(user_email)s
        '''
        sale = self._q_one(sql, params)
        return sale is not None

    def _valid_sample(self, params):
        # params = {
        #   'sample_id': <uuid>,
        #   'user_email': 'user@example.com'
        # }
        sql = '''
            SELECT sample_id
            FROM samples JOIN items USING (item_id) JOIN users USING (user_id)
            WHERE sample_id = %(sample_id)s AND user_email = %(user_email)s
        '''
        return self._q_one(sql, params) is not None

    def add_item_to_order(self, params):
        # params = {
        #   'item_category': 'A category',
        #   'item_name': 'An item',
        #   'order_id': <uuid>,
        #   'quantity': 1,
        #   'user_email': 'user@example.com'
        # }
        if not self._valid_order(params):
            return

        params['item_id'] = self.get_or_add_item(params)
        sql = 'SELECT order_id, item_id FROM order_items WHERE order_id = %(order_id)s AND item_id = %(item_id)s'
        existing = self._q_one(sql, params)
        if existing is None:
            sql = '''
                INSERT INTO order_items (order_id, item_id, quantity)
                VALUES (%(order_id)s, %(item_id)s, %(quantity)s)
            '''
        else:
            sql = '''
                UPDATE order_items SET quantity = %(quantity)s WHERE order_id = %(order_id)s AND item_id = %(item_id)s
            '''
        self._u(sql, params)

    def add_item_to_sale(self, params):
        # params = {
        #   'sale_id': <uuid>,
        #   'user_email': 'user@example.com'
        # }
        sql = '''
            SELECT sale_id
            FROM sales JOIN users USING (user_id)
            WHERE sale_id = %(sale_id)s AND user_email = %(user_email)s
        '''
        sale = self._q_one(sql, params)
        if sale is None:
            return
        params.update(self.get_or_add_user(params))
        params['item_id'] = self.get_or_add_item(params)
        sql = 'SELECT sale_id, item_id FROM sale_items WHERE sale_id = %(sale_id)s AND item_id = %(item_id)s'
        existing = self._q_one(sql, params)
        if existing is None:
            sql = '''
                INSERT INTO sale_items (sale_id, item_id, quantity)
                VALUES (%(sale_id)s, %(item_id)s, %(quantity)s)
            '''
        else:
            sql = '''
                UPDATE sale_items SET quantity = %(quantity)s WHERE sale_id = %(sale_id)s AND item_id = %(item_id)s
            '''
        self._u(sql, params)

    def add_order(self, params):
        # params = {
        #   'order_created_at': <date>,
        #   'order_note': 'text',
        #   'user_email': 'user@example.com'
        # }
        params['order_id'] = uuid.uuid4()
        params.update(self.get_or_add_user(params))
        sql = '''
            INSERT INTO orders (order_id, user_id, order_created_at, order_note)
            VALUES (%(order_id)s, %(user_id)s, %(order_created_at)s, %(order_note)s)
        '''
        self._u(sql, params)
        return params.get('order_id')

    def add_sale(self, params):
        # params = {
        #   'sale_created_at': <date>,
        #   'sale_customer': 'text',
        #   'user_email': 'user@example.com'
        # }
        params['sale_id'] = uuid.uuid4()
        params.update(self.get_or_add_user(params))
        sql = '''
            INSERT INTO sales (sale_id, user_id, sale_created_at, sale_customer)
            VALUES (%(sale_id)s, %(user_id)s, %(sale_created_at)s, %(sale_customer)s)
        '''
        self._u(sql, params)
        return params.get('sale_id')

    def add_sample(self, params):
        # params = {
        #   'item_category': 'Category',
        #   'item_name': 'Item',
        #   'quantity': 1,
        #   'user_email': 'user@example.com'
        # }
        params['item_id'] = self.get_or_add_item(params)
        params['sample_id'] = uuid.uuid4()
        sql = 'INSERT INTO samples (sample_id, item_id, quantity) VALUES (%(sample_id)s, %(item_id)s, %(quantity)s)'
        self._u(sql, params)

    def destroy(self):
        log.debug('Removing all tables and types from database')
        self._u('DROP TABLE IF EXISTS sale_items, order_items, sales, orders, items, users, flags CASCADE')
        self._u('DROP TYPE IF EXISTS user_level_enum, order_item_status_enum CASCADE')

    def delete_item(self, params):
        # params = {
        #   'item_id': <uuid>,
        #   'user_email': 'user@example.com'
        # }
        sql = '''
            SELECT item_id
            FROM items JOIN users USING (user_id)
            WHERE user_email = %(user_email)s AND item_id = %(item_id)s
        '''
        item = self._q_one(sql, params)
        if item is None:
            return
        self._u('DELETE FROM items WHERE item_id = %(item_id)s', params)

    def delete_item_from_order(self, params):
        # params = {
        #   'item_id': <uuid>,
        #   'order_id': <uuid>,
        #   'user_email': 'user@example.com'
        # }
        if not self._valid_order(params):
            return

        self._u('DELETE FROM order_items WHERE order_id = %(order_id)s AND item_id = %(item_id)s', params)

    def delete_item_from_sale(self, params):
        # params = {
        #   'item_id': <uuid>,
        #   'sale_id': <uuid>,
        #   'user_email': 'user@example.com'
        # }
        if not self._valid_sale(params):
            return

        self._u('DELETE FROM sale_items WHERE sale_id = %(sale_id)s AND item_id = %(item_id)s', params)

    def delete_order(self, params):
        # params = {
        #   'order_id': <uuid>,
        #   'user_email': 'user@example.com'
        # }
        sql = '''
            DELETE FROM orders
            WHERE order_id = %(order_id)s
            AND user_id IN (SELECT user_id FROM users WHERE user_email = %(user_email)s)
        '''
        self._u(sql, params)

    def delete_sale(self, params):
        # params = {
        #   'sale_id': <uuid>,
        #   'user_email': 'user@example.com'
        # }
        sql = '''
            DELETE FROM sales
            WHERE sale_id = %(sale_id)s
            AND user_id IN (SELECT user_id FROM users WHERE user_email = %(user_email)s)
        '''
        self._u(sql, params)

    def delete_sample(self, params):
        # params = {
        #   'sample_id': <uuid>,
        #   'user_email': 'user@example.com'
        # }
        if not self._valid_sample(params):
            return
        self._u('DELETE FROM samples WHERE sample_id = %(sample_id)s', params)

    def get_customers(self, params):
        # params = {'user_email': 'user@example.com'}
        sql = '''
            SELECT sale_customer
            FROM sales JOIN users USING (user_id)
            WHERE user_email = %(user_email)s AND char_length(sale_customer) > 0
        '''
        return [row['sale_customer'] for row in self._q(sql, params)]

    def get_inventory(self, params):
        # params = {'user_email': 'user@example.com'}
        sql = '''
            SELECT item_id, item_name, item_category,
                concat_ws(' ', lower(item_name), lower(item_category)) filter_value,
                sum(CASE order_items.status WHEN 'ordered' THEN order_items.quantity ELSE 0 END ) qty_ordered,
                sum(CASE order_items.status WHEN 'received' THEN order_items.quantity ELSE 0 END ) qty_received,
                qty_committed, qty_sold, qty_sample_active, qty_sample_used
            FROM items
            JOIN users USING (user_id)
            LEFT JOIN order_items USING (item_id)
            LEFT JOIN (
                SELECT item_id,
                    sum(CASE WHEN sale_delivered THEN 0 ELSE coalesce(sale_items.quantity, 0) END) qty_committed,
                    sum(CASE WHEN sale_delivered THEN sale_items.quantity ELSE 0 END) qty_sold
                FROM items
                LEFT JOIN sale_items USING (item_id)
                LEFT JOIN sales USING (sale_id)
                GROUP BY item_id) sale_quantities USING (item_id)
            LEFT JOIN (
                SELECT item_id,
                    sum(CASE WHEN sample_used THEN samples.quantity ELSE 0 END) qty_sample_used,
                    sum(CASE WHEN sample_used THEN 0 ELSE coalesce(samples.quantity, 0) END) qty_sample_active
                FROM items
                LEFT JOIN samples USING (item_id)
                GROUP BY item_id) sample_quantities USING (item_id)
            WHERE user_email = %(user_email)s
            GROUP BY item_id, item_name, item_category, qty_committed, qty_sold, qty_sample_active, qty_sample_used
            ORDER BY item_name
        '''
        return self._q(sql, params)

    def get_item_details(self, params):
        # params = {
        #   'item_id': <uuid>,
        #   'user_email': 'user@example.com'
        # }
        sql = '''
            SELECT item_id, item_name, item_category
            FROM items JOIN users USING (user_id)
            WHERE user_email = %(user_email)s AND item_id = %(item_id)s
        '''
        item = self._q_one(sql, params)
        if item is None:
            return
        sql = '''
            SELECT order_id, quantity, status, order_created_at, order_note
            FROM order_items JOIN orders USING (order_id)
            WHERE item_id = %(item_id)s
        '''
        item['orders'] = self._q(sql, params)
        sql = '''
            SELECT sale_id, quantity, sale_created_at, sale_customer, sale_paid, sale_delivered
            FROM sale_items JOIN sales USING (sale_id)
            WHERE item_id = %(item_id)s
        '''
        item['sales'] = self._q(sql, params)
        sql = 'SELECT sample_id, quantity, sample_used FROM samples WHERE item_id = %(item_id)s'
        item['samples'] = self._q(sql, params)
        item['deletable'] = True
        if any([item['orders'], item['sales'], item['samples']]):
            item['deletable'] = False
        return item

    def get_or_add_item(self, params):
        # params = {
        #   'item_category': 'A category',
        #   'item_name': 'An item',
        #   'user_email': 'user@example.com'
        # }
        sql = '''
            SELECT item_id FROM items JOIN users USING (user_id)
            WHERE item_name = %(item_name)s AND item_category = %(item_category)s AND user_email = %(user_email)s
        '''
        item = self._q_one(sql, params)
        if item is None:
            params.update(self.get_or_add_user(params))
            params['item_id'] = uuid.uuid4()
            sql = '''
                INSERT INTO items (item_id, user_id, item_name, item_category)
                VALUES (%(item_id)s, %(user_id)s, %(item_name)s, %(item_category)s)
            '''
            self._u(sql, params)
            return params.get('item_id')
        return item.get('item_id')

    def get_or_add_user(self, params):
        # params = {'user_email': 'user@example.com'}
        row = self._q_one('SELECT user_id, user_email FROM users WHERE user_email = %(user_email)s', params)
        if row is None:
            params['user_id'] = uuid.uuid4()
            self._u('INSERT INTO users (user_id, user_email) VALUES (%(user_id)s, %(user_email)s)', params)
            return params
        return row

    def get_order(self, params):
        # params = {
        #   'order_id': <uuid>,
        #   'user_email': 'user@example.com'
        # }
        sql = '''
            SELECT order_id, order_created_at, coalesce(order_note, '') order_note, order_locked
            FROM orders JOIN users USING (user_id)
            WHERE order_id = %(order_id)s AND user_email = %(user_email)s
        '''
        order = self._q_one(sql, params)
        if order is None:
            return
        sql = '''
            SELECT
                item_id, item_name, item_category, quantity, status,
                CASE status
                    WHEN 'ordered' THEN 'label-danger' WHEN 'received' THEN 'label-success' ELSE 'label-default'
                END label_class
            FROM order_items LEFT JOIN items USING (item_id)
            WHERE order_id = %(order_id)s
            ORDER BY item_name
        '''
        order['order_items'] = self._q(sql, params)
        order['num_items'] = sum([i.get('quantity') for i in order.get('order_items')])
        return order

    def get_orders(self, params):
        # params = {'user_email': 'user@example.com'}
        sql = '''
            SELECT order_id, order_created_at, coalesce(order_note, '') order_note,
                coalesce(sum(quantity), 0) num_items,
                bool_or(status = 'ordered') waiting_to_receive,
                json_agg(json_build_object(
                    'name', item_name, 'quantity', quantity, 'status', status, 'label_class',
                    CASE status
                        WHEN 'ordered' THEN 'label-danger' WHEN 'received' THEN 'label-success' ELSE 'label-default'
                    END
                ) ORDER BY item_name) order_items
            FROM orders
            JOIN users USING (user_id)
            LEFT JOIN order_items USING (order_id)
            LEFT JOIN items USING (item_id)
            WHERE user_email = %(user_email)s
            GROUP BY order_id, order_created_at, order_note
            ORDER BY order_created_at DESC
        '''
        return self._q(sql, params)

    def get_sale(self, params):
        # params = {
        #   'sale_id': <uuid>,
        #   'user_email': 'user@example.com'
        # }
        params.update(self.get_or_add_user(params))
        sql = '''
            SELECT sale_id, sale_created_at, sale_customer, sale_paid, sale_delivered
            FROM sales
            WHERE sale_id = %(sale_id)s AND user_id = %(user_id)s
        '''
        sale = self._q_one(sql, params)
        if sale is None:
            return
        sql = '''
            SELECT item_id, item_name, item_category, quantity
            FROM sale_items LEFT JOIN items USING (item_id)
            WHERE sale_id = %(sale_id)s
            ORDER BY item_name
        '''
        sale['sale_items'] = self._q(sql, params)
        sale['num_items'] = sum([i.get('quantity') for i in sale['sale_items']])
        return sale

    def get_sales(self, params):
        # params = {'user_email': 'user@example.com'}
        sql = '''
            SELECT sale_id, sale_created_at, sale_customer, sale_paid, sale_delivered,
                coalesce(sum(quantity), 0) num_items,
                json_agg(json_build_object('name', item_name, 'quantity', quantity) ORDER BY item_name) sale_items
            FROM sales
            JOIN users USING (user_id)
            LEFT JOIN sale_items USING (sale_id)
            LEFT JOIN items USING (item_id)
            WHERE user_email= %(user_email)s
            GROUP BY sale_id, sale_created_at, sale_customer, sale_paid, sale_delivered
            ORDER BY sale_created_at DESC
        '''
        return self._q(sql, params)

    def get_samples(self, params):
        # params = {'user_email': 'user@example.com'}
        sql = '''
            SELECT sample_id, item_id, item_name, item_category, quantity, sample_used
            FROM samples
            JOIN items USING (item_id)
            JOIN users USING (user_id)
            WHERE user_email = %(user_email)s
            ORDER BY sample_used, item_name
        '''
        return self._q(sql, params)

    def migrate(self):
        log.debug('Checking for database migrations')
        if self.version == 0:
            # version 1 is the initial table layout
            log.debug('Migrating from version 0 to version 1')
            self._u("CREATE TYPE user_level_enum AS ENUM ('admin', 'standard')")
            self._u("CREATE TYPE order_item_status_enum AS ENUM ('ordered', 'received', 'cancelled')")
            self._u('''
                CREATE TABLE IF NOT EXISTS flags (
                    flag_name TEXT PRIMARY KEY,
                    flag_text TEXT,
                    flag_int INT,
                    flag_timestamp TIMESTAMP
                )
            ''')
            self._u('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id UUID PRIMARY KEY,
                    user_email TEXT NOT NULL,
                    user_level user_level_enum NOT NULL DEFAULT 'standard'
                )
            ''')
            self._u('''
                CREATE TABLE IF NOT EXISTS items (
                    item_id UUID PRIMARY KEY,
                    user_id UUID REFERENCES users,
                    item_name TEXT NOT NULL,
                    item_category TEXT
                )
            ''')
            self._u('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id UUID PRIMARY KEY,
                    user_id UUID REFERENCES users,
                    order_created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
                    order_locked BOOLEAN NOT NULL DEFAULT FALSE,
                    order_note TEXT DEFAULT ''
                )
            ''')
            self._u('''
                CREATE TABLE IF NOT EXISTS sales (
                    sale_id UUID PRIMARY KEY,
                    user_id UUID REFERENCES users,
                    sale_created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
                    sale_customer TEXT DEFAULT '',
                    sale_paid BOOLEAN NOT NULL DEFAULT FALSE,
                    sale_delivered BOOLEAN NOT NULL DEFAULT FALSE
                )
            ''')
            self._u('''
                CREATE TABLE IF NOT EXISTS order_items (
                    order_id UUID REFERENCES orders ON DELETE CASCADE,
                    item_id UUID REFERENCES items,
                    quantity INT NOT NULL,
                    status order_item_status_enum NOT NULL DEFAULT 'ordered',
                    PRIMARY KEY (order_id, item_id)
                )
            ''')
            self._u('''
                CREATE TABLE IF NOT EXISTS sale_items (
                    sale_id UUID REFERENCES sales ON DELETE CASCADE,
                    item_id UUID REFERENCES items,
                    quantity INT NOT NULL,
                    PRIMARY KEY (sale_id, item_id)
                )
            ''')
            self._u('''
                CREATE TABLE IF NOT EXISTS samples (
                    sample_id UUID PRIMARY KEY,
                    item_id UUID REFERENCES items,
                    quantity INT NOT NULL,
                    sample_used BOOLEAN NOT NULL DEFAULT FALSE
                )
            ''')
            self._u('INSERT INTO flags (flag_name, flag_int) VALUES (%s, %s)', ['db_version', 1])

    def set_order_item_status(self, params):
        # params = {
        #   'item_id': <uuid>,
        #   'order_id': <uuid>,
        #   'status': 'received',
        #   'user_email': 'user@example.com'
        # }
        if not self._valid_order(params):
            return

        sql = 'UPDATE order_items SET status = %(status)s WHERE order_id = %(order_id)s AND item_id = %(item_id)s'
        self._u(sql, params)

    def set_order_lock(self, params):
        # params = {
        #   'order_id': <uuid>,
        #   'order_locked': True/False,
        #   'user_email': 'user@example.com'
        # }
        if not self._valid_order(params):
            return

        sql = 'UPDATE orders SET order_locked = %(order_locked)s WHERE order_id = %(order_id)s'
        self._u(sql, params)

    def set_order_details(self, params):
        # params = {
        #   'order_created_at': <date>,
        #   'order_id': <uuid>,
        #   'order_note': 'text',
        #   'user_email': 'user@example.com'
        # }
        if not self._valid_order(params):
            return

        sql = '''
            UPDATE orders
            SET order_created_at = %(order_created_at)s, order_note = %(order_note)s
            WHERE order_id = %(order_id)s
        '''
        self._u(sql, params)

    def set_sale_details(self, params):
        # params = {
        #   'sale_created_at': <date>,
        #   'sale_customer': 'Name',
        #   'sale_delivered': True,
        #   'sale_id': <uuid>,
        #   'sale_paid': True,
        #   'user_email': 'user@example.com'
        # }
        sql = '''
            SELECT sale_id
            FROM sales JOIN users USING (user_id)
            WHERE user_email = %(user_email)s AND sale_id = %(sale_id)s
        '''
        sale = self._q_one(sql, params)
        if sale is None:
            return
        sql = '''
            UPDATE sales
            SET sale_created_at = %(sale_created_at)s,
                sale_customer = %(sale_customer)s,
                sale_paid = %(sale_paid)s, sale_delivered = %(sale_delivered)s
            WHERE sale_id = %(sale_id)s
        '''
        self._u(sql, params)

    def set_sample_used(self, params):
        # params = {
        #   'sample_id': <uuid>,
        #   'sample_used': True/False,
        #   'user_email': 'user@example.com'
        # }
        if not self._valid_sample(params):
            return
        sql = 'UPDATE samples SET sample_used = %(sample_used)s WHERE sample_id = %(sample_id)s'
        self._u(sql, params)

    @property
    def version(self):
        row = self._q_one('SELECT 1 FROM pg_tables WHERE tablename = %s', ['flags'])
        if row is None:
            return 0
        row = self._q_one('SELECT flag_int FROM flags WHERE flag_name = %s', ['db_version'])
        return row.get('flag_int')
