import datetime
import flask
import functools
import inventory.config
import inventory.sql
import jwt
import logging
import requests
import signal
import sys
import urllib.parse
import uuid
import waitress
import werkzeug.middleware.proxy_fix

config = inventory.config.Config()

app = flask.Flask(__name__)
app.wsgi_app = werkzeug.middleware.proxy_fix.ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_port=1)

app.config['PREFERRED_URL_SCHEME'] = config.scheme
app.config['SECRET_KEY'] = config.secret_key


def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        session_email = flask.session.get('email')
        if session_email is None:
            return flask.redirect(flask.url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def _get_db():
    _db = flask.g.get('_db')
    if _db is None:
        _db = inventory.sql.InventoryDatabase(config.dsn)
        flask.g._db = _db
    return _db


@app.route('/')
def index():
    email = flask.session.get('email')
    if email is None:
        return flask.render_template('index.html')
    flask.g.inventory = _get_db().get_inventory({'user_email': email})
    return flask.render_template('index_signed_in.html')


@app.route('/authorize')
def authorize():
    for key, value in flask.request.values.items():
        app.logger.debug(f'{key}: {value}')
    if flask.session.get('state') != flask.request.values.get('state'):
        return 'State mismatch', 401
    discovery_document = requests.get(config.openid_discovery_document).json()
    token_endpoint = discovery_document.get('token_endpoint')
    data = {
        'code': flask.request.values.get('code'),
        'client_id': config.openid_client_id,
        'client_secret': config.openid_client_secret,
        'redirect_uri': flask.url_for('authorize', _external=True),
        'grant_type': 'authorization_code'
    }
    app.logger.debug(f'token endpoint data: {data}')
    resp = requests.post(token_endpoint, data=data).json()
    app.logger.debug(f'token endpoint response: {resp}')
    id_token = resp.get('id_token')
    algorithms = discovery_document.get('id_token_signing_alg_values_supported')
    claim = jwt.decode(id_token, verify=False, algorithms=algorithms)
    flask.session['email'] = claim.get('email')
    return flask.redirect(flask.url_for('index'))


@app.route('/sign-in')
def sign_in():
    state = str(uuid.uuid4())
    flask.session['state'] = state
    redirect_uri = flask.url_for('authorize', _external=True)
    query = {
        'client_id': config.openid_client_id,
        'response_type': 'code',
        'scope': 'openid email profile',
        'redirect_uri': redirect_uri,
        'state': state
    }
    discovery_document = requests.get(config.openid_discovery_document).json()
    auth_endpoint = discovery_document.get('authorization_endpoint')
    auth_url = f'{auth_endpoint}?{urllib.parse.urlencode(query)}'
    return flask.redirect(auth_url, 307)


@app.route('/customers.json')
@login_required
def customers_json():
    email = flask.session.get('email')
    return flask.jsonify(_get_db().get_customers({'user_email': email}))


@app.route('/inventory.json')
@login_required
def inventory_json():
    email = flask.session.get('email')
    return flask.jsonify(_get_db().get_inventory({'user_email': email}))


@app.route('/items/<item_id>')
@login_required
def item_detail(item_id):
    email = flask.session.get('email')
    params = {
        'user_email': email,
        'item_id': item_id
    }
    flask.g.item = _get_db().get_item_details(params)
    return flask.render_template('item_detail.html')


@app.route('/items/delete', methods=['POST'])
@login_required
def items_delete():
    email = flask.session.get('email')
    params = {
        'user_email': email,
        'item_id': flask.request.form.get('item_id')
    }
    _get_db().delete_item(params)
    return flask.redirect(flask.url_for('index'))


@app.route('/orders')
@login_required
def orders():
    email = flask.session.get('email')
    flask.g.today = datetime.date.today()
    flask.g.orders = _get_db().get_orders({'user_email': email})
    return flask.render_template('orders.html')


@app.route('/orders/add_item', methods=['POST'])
@login_required
def orders_add_item():
    email = flask.session.get('email')
    params = {
        'order_id': flask.request.form.get('order_id'),
        'user_email': email,
        'item_name': flask.request.form.get('item_name'),
        'item_category': flask.request.form.get('item_category'),
        'quantity': flask.request.form.get('quantity')
    }
    _get_db().add_item_to_order(params)
    return flask.redirect(flask.url_for('order_detail', order_id=flask.request.form.get('order_id')))


@app.route('/orders/delete', methods=['POST'])
@login_required
def orders_delete():
    email = flask.session.get('email')
    params = {
        'order_id': flask.request.form.get('order_id'),
        'user_email': email
    }
    _get_db().delete_order(params)
    return flask.redirect(flask.url_for('orders'))


@app.route('/orders/delete_item', methods=['POST'])
@login_required
def orders_delete_item():
    email = flask.session.get('email')
    params = {
        'user_email': email,
        'order_id': flask.request.form.get('order_id'),
        'item_id': flask.request.form.get('item_id')
    }
    _get_db().delete_item_from_order(params)
    return flask.redirect(flask.url_for('order_detail', order_id=params.get('order_id')))


@app.route('/orders/new', methods=['POST'])
@login_required
def orders_new():
    email = flask.session.get('email')
    params = {
        'user_email': email,
        'order_created_at': flask.request.form.get('order_created_at'),
        'order_note': flask.request.form.get('order_note')
    }
    order_id = _get_db().add_order(params)
    return flask.redirect(flask.url_for('order_detail', order_id=order_id))


@app.route('/orders/set_details', methods=['POST'])
@login_required
def orders_set_details():
    email = flask.session.get('email')
    params = {
        'user_email': email,
        'order_id': flask.request.form.get('order_id'),
        'order_created_at': flask.request.form.get('order_created_at'),
        'order_note': flask.request.form.get('order_note')
    }
    _get_db().set_order_details(params)
    return flask.redirect(flask.url_for('order_detail', order_id=params.get('order_id')))


@app.route('/orders/set_item_status', methods=['POST'])
@login_required
def orders_set_item_status():
    email = flask.session.get('email')
    params = {
        'user_email': email,
        'order_id': flask.request.form.get('order_id'),
        'item_id': flask.request.form.get('item_id'),
        'status': flask.request.form.get('status')
    }
    _get_db().set_order_item_status(params)
    return flask.redirect(flask.url_for('order_detail', order_id=params.get('order_id')))


@app.route('/orders/set_lock', methods=['POST'])
@login_required
def orders_set_lock():
    email = flask.session.get('email')
    params = {
        'user_email': email,
        'order_id': flask.request.form.get('order_id'),
        'order_locked': flask.request.form.get('lock_status') == 'locked'
    }
    _get_db().set_order_lock(params)
    return flask.redirect(flask.url_for('order_detail', order_id=params.get('order_id')))


@app.route('/orders/<order_id>')
@login_required
def order_detail(order_id):
    email = flask.session.get('email')
    flask.g.order = _get_db().get_order({'user_email': email, 'order_id': order_id})
    if flask.g.order is None:
        flask.abort(404)
    return flask.render_template('order_detail.html')


@app.route('/sales')
@login_required
def sales():
    email = flask.session.get('email')
    flask.g.today = datetime.date.today()
    flask.g.sales = _get_db().get_sales({'user_email': email})
    return flask.render_template('sales.html')


@app.route('/sales/add_item', methods=['POST'])
@login_required
def sales_add_item():
    email = flask.session.get('email')
    params = {
        'sale_id': flask.request.form.get('sale_id'),
        'user_email': email,
        'item_name': flask.request.form.get('item_name'),
        'item_category': flask.request.form.get('item_category'),
        'quantity': flask.request.form.get('quantity')
    }
    _get_db().add_item_to_sale(params)
    return flask.redirect(flask.url_for('sale_detail', sale_id=flask.request.form.get('sale_id')))


@app.route('/sales/delete', methods=['POST'])
@login_required
def sales_delete():
    email = flask.session.get('email')
    params = {
        'sale_id': flask.request.form.get('sale_id'),
        'user_email': email
    }
    _get_db().delete_sale(params)
    return flask.redirect(flask.url_for('sales'))


@app.route('/sales/delete_item', methods=['POST'])
@login_required
def sales_delete_item():
    email = flask.session.get('email')
    params = {
        'user_email': email,
        'sale_id': flask.request.form.get('sale_id'),
        'item_id': flask.request.form.get('item_id')
    }
    _get_db().delete_item_from_sale(params)
    return flask.redirect(flask.url_for('sale_detail', sale_id=params.get('sale_id')))


@app.route('/sales/new', methods=['POST'])
@login_required
def sales_new():
    email = flask.session.get('email')
    params = {
        'user_email': email,
        'sale_created_at': flask.request.form.get('sale_created_at'),
        'sale_customer': flask.request.form.get('sale_customer')
    }
    sale_id = _get_db().add_sale(params)
    return flask.redirect(flask.url_for('sale_detail', sale_id=sale_id))


@app.route('/sales/set_details', methods=['POST'])
@login_required
def sales_set_details():
    email = flask.session.get('email')
    params = {
        'user_email': email,
        'sale_id': flask.request.form.get('sale_id'),
        'sale_created_at': flask.request.form.get('sale_created_at'),
        'sale_customer': flask.request.form.get('sale_customer'),
        'sale_paid': 'sale_paid' in flask.request.form,
        'sale_delivered': 'sale_delivered' in flask.request.form
    }
    _get_db().set_sale_details(params)
    return flask.redirect(flask.url_for('sale_detail', sale_id=params.get('sale_id')))


@app.route('/sales/<sale_id>')
@login_required
def sale_detail(sale_id):
    email = flask.session.get('email')
    flask.g.sale = _get_db().get_sale({'user_email': email, 'sale_id': sale_id})
    if flask.g.sale is None:
        flask.abort(404)
    return flask.render_template('sale_detail.html')


@app.route('/samples')
@login_required
def samples():
    email = flask.session.get('email')
    flask.g.samples = _get_db().get_samples({'user_email': email})
    return flask.render_template('samples.html')


@app.route('/samples/delete', methods=['POST'])
@login_required
def samples_delete():
    email = flask.session.get('email')
    _get_db().delete_sample({'user_email': email, 'sample_id': flask.request.form.get('sample_id')})
    return flask.redirect(flask.url_for('samples'))


@app.route('/samples/new', methods=['POST'])
@login_required
def samples_new():
    email = flask.session.get('email')
    params = {
        'user_email': email,
        'item_name': flask.request.form.get('item_name'),
        'item_category': flask.request.form.get('item_category'),
        'quantity': flask.request.form.get('quantity')
    }
    _get_db().add_sample(params)
    return flask.redirect(flask.url_for('samples'))


@app.route('/samples/use', methods=['POST'])
@login_required
def samples_use():
    email = flask.session.get('email')
    params = {
        'user_email': email,
        'sample_id': flask.request.form.get('sample_id'),
        'sample_used': True
    }
    _get_db().set_sample_used(params)
    return flask.redirect(flask.url_for('samples'))


@app.route('/sign_out')
def sign_out():
    flask.session.pop('email', None)
    return flask.redirect(flask.url_for('index'))


def handle_sigterm(_signal, _frame):
    sys.exit()


def main():
    signal.signal(signal.SIGTERM, handle_sigterm)
    logging.basicConfig(format=config.log_format, level='DEBUG', stream=sys.stdout)
    app.logger.debug(f'Changing log level to {config.log_level}')
    logging.getLogger().setLevel(config.log_level)

    with app.app_context():
        _get_db().migrate()

    waitress.serve(app, port=config.port)


if __name__ == '__main__':
    main()
