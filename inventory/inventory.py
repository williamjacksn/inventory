import flask
import flask_oauth2_login
import flask_sslify
import functools
import inventory.sql
import logging
import os
import waitress

log = logging.getLogger(__name__)

app = flask.Flask(__name__)

for key in ['ADMIN_EMAIL', 'DSN', 'GOOGLE_LOGIN_CLIENT_ID', 'GOOGLE_LOGIN_CLIENT_SECRET',
            'GOOGLE_LOGIN_REDIRECT_SCHEME', 'SECRET_KEY']:
    app.config[key] = os.environ.get(key)

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


@app.route('/orders')
@login_required
def orders():
    profile = flask.session.get('profile')
    c = {'orders': _get_db().get_orders({'user_email': profile.get('email')})}
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


@app.route('/orders/new', methods=['POST'])
@login_required
def orders_new():
    profile = flask.session.get('profile')
    order_id = _get_db().add_order({'user_email': profile.get('email')})
    return flask.redirect(flask.url_for('order_detail', order_id=order_id))


@app.route('/orders/set_details',methods=['POST'])
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
    c = {'sales': _get_db().get_sales({'user_email': profile.get('email')})}
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


@app.route('/sales/new', methods=['POST'])
@login_required
def sales_new():
    profile = flask.session.get('profile')
    sale_id = _get_db().add_sale({'user_email': profile.get('email')})
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


@app.route('/sign_out')
def sign_out():
    flask.session.pop('profile')
    return flask.redirect(flask.url_for('index'))


def main():
    with app.app_context():
        _get_db().migrate()
    waitress.serve(app)
