import datetime
import flask
import flask_oauth2_login
import flask_sslify
import functools
import inventory.sql
import logging
import os
import sys
import waitress

log = logging.getLogger(__name__)

app = flask.Flask(__name__)

DEFAULTS = {
    'LOG_FORMAT': '%(levelname)s [%(name)s] %(message)s',
    'LOG_LEVEL': 'DEBUG',
    'PORT': 8080
}

for key in ['ADMIN_EMAIL', 'DSN', 'GOOGLE_LOGIN_CLIENT_ID', 'GOOGLE_LOGIN_CLIENT_SECRET',
            'GOOGLE_LOGIN_REDIRECT_SCHEME', 'LOG_FORMAT', 'LOG_LEVEL', 'PORT', 'SECRET_KEY', 'UNIX_SOCKET']:
    app.config[key] = os.environ.get(key, DEFAULTS.get(key))

if app.config.get('GOOGLE_LOGIN_REDIRECT_SCHEME').lower() == 'https':
    sslify = flask_sslify.SSLify(app)

google_login = flask_oauth2_login.GoogleLogin(app)


@google_login.login_success
def login_success(_, profile):
    flask.session['profile'] = profile
    log.debug('Google login success')
    return flask.redirect(flask.url_for('index'))


@google_login.login_failure
def login_failure(e):
    log.debug(f'Google login failure: {e}')
    return flask.jsonify(errors=str(e))


def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        profile = flask.session.get('profile')
        if profile is None:
            return flask.redirect(flask.url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def _get_db():
    _db = flask.g.get('_db')
    if _db is None:
        _db = inventory.sql.InventoryDatabase(app.config.get('DSN'))
        flask.g._db = _db
    return _db


@app.route('/')
def index():
    profile = flask.session.get('profile')
    if profile is None:
        return flask.render_template('index.html', c={'sign_in_url': google_login.authorization_url()})
    c = {'inventory': _get_db().get_inventory({'user_email': profile.get('email')})}
    return flask.render_template('index_signed_in.html', c=c)


@app.route('/customers.json')
@login_required
def customers_json():
    profile = flask.session.get('profile')
    return flask.jsonify(_get_db().get_customers({'user_email': profile.get('email')}))


@app.route('/inventory.json')
@login_required
def inventory_json():
    profile = flask.session.get('profile')
    return flask.jsonify(_get_db().get_inventory({'user_email': profile.get('email')}))


@app.route('/items/<item_id>')
@login_required
def item_detail(item_id):
    profile = flask.session.get('profile')
    params = {
        'user_email': profile.get('email'),
        'item_id': item_id
    }
    c = _get_db().get_item_details(params)
    return flask.render_template('item_detail.html', c=c)


@app.route('/items/delete', methods=['POST'])
@login_required
def items_delete():
    profile = flask.session.get('profile')
    params = {
        'user_email': profile.get('email'),
        'item_id': flask.request.form.get('item_id')
    }
    _get_db().delete_item(params)
    return flask.redirect(flask.url_for('index'))


@app.route('/orders')
@login_required
def orders():
    profile = flask.session.get('profile')
    c = {'orders': _get_db().get_orders({'user_email': profile.get('email')}), 'today': datetime.date.today()}
    return flask.render_template('orders.html', c=c)


@app.route('/orders/add_item', methods=['POST'])
@login_required
def orders_add_item():
    profile = flask.session.get('profile')
    params = {
        'order_id': flask.request.form.get('order_id'),
        'user_email': profile.get('email'),
        'item_name': flask.request.form.get('item_name'),
        'item_category': flask.request.form.get('item_category'),
        'quantity': flask.request.form.get('quantity')
    }
    _get_db().add_item_to_order(params)
    return flask.redirect(flask.url_for('order_detail', order_id=flask.request.form.get('order_id')))


@app.route('/orders/delete', methods=['POST'])
@login_required
def orders_delete():
    profile = flask.session.get('profile')
    params = {
        'order_id': flask.request.form.get('order_id'),
        'user_email': profile.get('email')
    }
    _get_db().delete_order(params)
    return flask.redirect(flask.url_for('orders'))


@app.route('/orders/delete_item', methods=['POST'])
@login_required
def orders_delete_item():
    profile = flask.session.get('profile')
    params = {
        'user_email': profile.get('email'),
        'order_id': flask.request.form.get('order_id'),
        'item_id': flask.request.form.get('item_id')
    }
    _get_db().delete_item_from_order(params)
    return flask.redirect(flask.url_for('order_detail', order_id=params.get('order_id')))


@app.route('/orders/new', methods=['POST'])
@login_required
def orders_new():
    profile = flask.session.get('profile')
    params = {
        'user_email': profile.get('email'),
        'order_created_at': flask.request.form.get('order_created_at'),
        'order_note': flask.request.form.get('order_note')
    }
    order_id = _get_db().add_order(params)
    return flask.redirect(flask.url_for('order_detail', order_id=order_id))


@app.route('/orders/set_details', methods=['POST'])
@login_required
def orders_set_details():
    profile = flask.session.get('profile')
    params = {
        'user_email': profile.get('email'),
        'order_id': flask.request.form.get('order_id'),
        'order_created_at': flask.request.form.get('order_created_at'),
        'order_note': flask.request.form.get('order_note')
    }
    _get_db().set_order_details(params)
    return flask.redirect(flask.url_for('order_detail', order_id=params.get('order_id')))


@app.route('/orders/set_item_status', methods=['POST'])
@login_required
def orders_set_item_status():
    profile = flask.session.get('profile')
    params = {
        'user_email': profile.get('email'),
        'order_id': flask.request.form.get('order_id'),
        'item_id': flask.request.form.get('item_id'),
        'status': flask.request.form.get('status')
    }
    _get_db().set_order_item_status(params)
    return flask.redirect(flask.url_for('order_detail', order_id=params.get('order_id')))


@app.route('/orders/set_lock', methods=['POST'])
@login_required
def orders_set_lock():
    profile = flask.session.get('profile')
    params = {
        'user_email': profile.get('email'),
        'order_id': flask.request.form.get('order_id'),
        'order_locked': flask.request.form.get('lock_status') == 'locked'
    }
    _get_db().set_order_lock(params)
    return flask.redirect(flask.url_for('order_detail', order_id=params.get('order_id')))


@app.route('/orders/<order_id>')
@login_required
def order_detail(order_id):
    profile = flask.session.get('profile')
    order = _get_db().get_order({'user_email': profile.get('email'), 'order_id': order_id})
    if order is None:
        flask.abort(404)
    return flask.render_template('order_detail.html', c={'order': order})


@app.route('/sales')
@login_required
def sales():
    profile = flask.session.get('profile')
    c = {'sales': _get_db().get_sales({'user_email': profile.get('email')}), 'today': datetime.date.today()}
    return flask.render_template('sales.html', c=c)


@app.route('/sales/add_item', methods=['POST'])
@login_required
def sales_add_item():
    profile = flask.session.get('profile')
    params = {
        'sale_id': flask.request.form.get('sale_id'),
        'user_email': profile.get('email'),
        'item_name': flask.request.form.get('item_name'),
        'item_category': flask.request.form.get('item_category'),
        'quantity': flask.request.form.get('quantity')
    }
    _get_db().add_item_to_sale(params)
    return flask.redirect(flask.url_for('sale_detail', sale_id=flask.request.form.get('sale_id')))


@app.route('/sales/delete', methods=['POST'])
@login_required
def sales_delete():
    profile = flask.session.get('profile')
    params = {
        'sale_id': flask.request.form.get('sale_id'),
        'user_email': profile.get('email')
    }
    _get_db().delete_sale(params)
    return flask.redirect(flask.url_for('sales'))


@app.route('/sales/delete_item', methods=['POST'])
@login_required
def sales_delete_item():
    profile = flask.session.get('profile')
    params = {
        'user_email': profile.get('email'),
        'sale_id': flask.request.form.get('sale_id'),
        'item_id': flask.request.form.get('item_id')
    }
    _get_db().delete_item_from_sale(params)
    return flask.redirect(flask.url_for('sale_detail', sale_id=params.get('sale_id')))


@app.route('/sales/new', methods=['POST'])
@login_required
def sales_new():
    profile = flask.session.get('profile')
    params = {
        'user_email': profile.get('email'),
        'sale_created_at': flask.request.form.get('sale_created_at'),
        'sale_customer': flask.request.form.get('sale_customer')
    }
    sale_id = _get_db().add_sale(params)
    return flask.redirect(flask.url_for('sale_detail', sale_id=sale_id))


@app.route('/sales/set_details', methods=['POST'])
@login_required
def sales_set_details():
    profile = flask.session.get('profile')
    params = {
        'user_email': profile.get('email'),
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
    profile = flask.session.get('profile')
    sale = _get_db().get_sale({'user_email': profile.get('email'), 'sale_id': sale_id})
    if sale is None:
        flask.abort(404)
    return flask.render_template('sale_detail.html', c={'sale': sale})


@app.route('/samples')
@login_required
def samples():
    profile = flask.session.get('profile')
    c = {'samples': _get_db().get_samples({'user_email': profile.get('email')})}
    return flask.render_template('samples.html', c=c)


@app.route('/samples/delete', methods=['POST'])
@login_required
def samples_delete():
    profile = flask.session.get('profile')
    _get_db().delete_sample({'user_email': profile.get('email'), 'sample_id': flask.request.form.get('sample_id')})
    return flask.redirect(flask.url_for('samples'))


@app.route('/samples/new', methods=['POST'])
@login_required
def samples_new():
    profile = flask.session.get('profile')
    params = {
        'user_email': profile.get('email'),
        'item_name': flask.request.form.get('item_name'),
        'item_category': flask.request.form.get('item_category'),
        'quantity': flask.request.form.get('quantity')
    }
    _get_db().add_sample(params)
    return flask.redirect(flask.url_for('samples'))


@app.route('/samples/use', methods=['POST'])
@login_required
def samples_use():
    profile = flask.session.get('profile')
    params = {
        'user_email': profile.get('email'),
        'sample_id': flask.request.form.get('sample_id'),
        'sample_used': True
    }
    _get_db().set_sample_used(params)
    return flask.redirect(flask.url_for('samples'))


@app.route('/sign_out')
def sign_out():
    flask.session.pop('profile')
    return flask.redirect(flask.url_for('index'))


def main():
    logging.basicConfig(format=app.config['LOG_FORMAT'], level=app.config['LOG_LEVEL'], stream=sys.stdout)
    with app.app_context():
        _get_db().migrate()
    if app.config['UNIX_SOCKET']:
        waitress.serve(app, unix_socket=app.config['UNIX_SOCKET'], unix_socket_perms='666')
    else:
        waitress.serve(app, port=app.config['PORT'])
