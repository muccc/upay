#!/usr/bin/env python
from flask import Flask, jsonify, Response, request, abort, url_for
from flask import make_response
from OpenSSL import SSL
from functools import wraps
import time
import uuid
from decimal import Decimal
import nupay
import ConfigParser
import sys

config = ConfigParser.RawConfigParser()
config.read(sys.argv[1])

context = SSL.Context(SSL.SSLv23_METHOD)
context.use_privatekey_file('test.key')
context.use_certificate_file('test.crt')

session_manager = nupay.ServerSessionManager(config)

def check_auth(username, password):
    if username == 'admin' and password == 'secret':
        return True
    return username == 'admin2' and password == 'secret'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(jsonify({'error': 'Login required'}), 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def check_session_id_and_transaction_id(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        session_id = kwargs['session_id']
        check_session_timeouts()

        if session_id not in sessions.keys():
            abort(404)
        if sessions[session_id]['owner'] != request.authorization.username: 
            abort(403)
        
        if 'transaction_id' in kwargs:
            transaction_id = kwargs['transaction_id']
            if transaction_id not in sessions[session_id]['transactions']:
                abort(404)
        return f(*args, **kwargs)
    return decorated

import threading
global_lock = threading.RLock()

def get_global_lock(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        with global_lock:
            return f(*args, **kwargs)
    return decorated


app = Flask(__name__)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)

sessions = {}
SESSION_TIMEOUT = 300

def remove_session(session_id):
    sessions[session_id]['database_session'].close()
    del sessions[session_id]

def get_uri_for_session(session):
    return url_for('get_session', session_id = session['id'], _external = True)

def get_uri_for_valid_tokens(session):
    return url_for('get_valid_tokens', session_id = session['id'], _external = True)

def get_uri_for_transaction(session, transaction_id):
    return url_for('get_transaction', session_id = session['id'],
            transaction_id = transaction_id, _external = True)

def make_public_session(session):
    public_fields = ('id', 'name', 'owner', 'timeout')
    public_session = {}
    for field in session:
        if field in public_fields:
            public_session[field] = session[field]
        if field == 'id':
            public_session['uri'] = get_uri_for_session(session)
        elif field == 'timeout':
            public_session['timeout'] = int(public_session['timeout'] - time.time())
        if field == 'database_session':
            database_session = session[field]
            public_session['total'] = database_session.total
            public_session['credit'] = database_session.credit

    return public_session

def make_public_transaction(transaction):
    public_fields = ('id', 'amount', 'used_tokens')
    public_transaction = {}

    for field in transaction:
        if field in public_fields:
            public_transaction[field] = transaction[field]
        if field == 'used_tokens':
            public_transaction['used_tokens'] = \
                    map(str, transaction[field])

    return public_transaction

def is_token_unused(token):
    for session in sessions.values():
        if token in session['database_session'].valid_tokens:
            return False
    return True

def check_session_timeouts():
    timed_out = []
    for session_id in sessions:
        session = sessions[session_id]
        if session['timeout'] < time.time():
            timed_out.append(session_id)
    for session_id in timed_out:
        print session_id, "timed out. deleting it"
        remove_session(session_id)

def reset_session_timeout(session):
    session['timeout'] = time.time() + SESSION_TIMEOUT

@app.route('/v1.0/status', methods = ['GET'])
@get_global_lock
def get_status():
    return jsonify( { 'status': {'pay': {'sessions': len(sessions)}} } )

@app.route('/v1.0/pay/sessions', methods = ['POST'])
@get_global_lock
@requires_auth
def post_session():
    if not request.json or not 'name' in request.json:
        abort(400)

    id = str(uuid.uuid4())
    database_session = session_manager.create_session()

    session = {'id': id, 'name': request.json['name'], 'owner': request.authorization.username,
                'database_session': database_session, 'transactions': {}}
    reset_session_timeout(session);
    sessions[id] = session
    location = get_uri_for_session(session)

    response = get_session(session_id=id)
    response.headers['Location'] = location
    response.status_code = 201
    return response

@app.route('/v1.0/pay/sessions/<session_id>', methods = ['GET'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def get_session(session_id):
    return make_response(jsonify({'session': make_public_session(sessions[session_id])}))

@app.route('/v1.0/pay/sessions/<session_id>/keepalive', methods = ['POST'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def post_session_keepalive(session_id):
    session = sessions[session_id]
    reset_session_timeout(session)

    response = get_session(session_id=session_id)
    response.headers['Location'] = get_uri_for_session(session)

    return response

@app.route('/v1.0/pay/sessions/<session_id>', methods = ['DELETE'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def delete_session(session_id):
    remove_session(session_id)
    return make_response(jsonify({}), 204)

@app.route('/v1.0/pay/sessions/<session_id>/tokens', methods = ['POST'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def post_tokens(session_id):
    if not request.json or not 'tokens' in request.json:
        abort(400)
    if not type(request.json['tokens']) == type([]):
        abort(400)

    session = sessions[session_id]
    reset_session_timeout(session)
    tokens = map(nupay.Token,  request.json['tokens'])
    unsused_tokens = filter(is_token_unused, tokens)
    session['database_session'].validate_tokens(unsused_tokens)

    response = get_valid_tokens(session_id=session_id)
    response.headers['Location'] = get_uri_for_valid_tokens(session)
    response.status_code = 201
    return response

@app.route('/v1.0/pay/sessions/<session_id>/valid_tokens', methods = ['GET'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def get_valid_tokens(session_id):
    session = sessions[session_id]
    return make_response(jsonify( { 'valid_tokens': map(str, session['database_session'].valid_tokens) } ))

@app.route('/v1.0/pay/sessions/<session_id>/transactions', methods = ['POST'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def post_transaction(session_id):
    if not request.json or not 'amount' in request.json:
        abort(400)
    try:
        amount = Decimal(request.json['amount'])
    except:
        abort(400)

    session = sessions[session_id]
    reset_session_timeout(session)
    transaction_id = str(uuid.uuid4())
    transaction = {'amount': amount, 'id': transaction_id}

    try:
        transaction['used_tokens'] = session['database_session'].cash(amount)
        session['transactions'][transaction_id] = transaction
        
        response = get_transaction(session_id=session_id,
                transaction_id=transaction_id)
        response.headers['Location'] = get_uri_for_transaction(session,
                transaction_id)
        response.status_code = 201
        return response
    except nupay.NotEnoughCreditError as e:
        data = {'message': 'Balance too low'}
        data['info'] = e.message[0]
        data['amount'] = e.message[1]
        return make_response(jsonify({'error': data}), 402)

@app.route('/v1.0/pay/sessions/<session_id>/transaction/<transaction_id>', methods = ['GET'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def get_transaction(session_id, transaction_id):
    transaction = sessions[session_id]['transactions'][transaction_id]
    transaction = make_public_transaction(transaction)
    return make_response(jsonify({'transaction': transaction}))

@app.route('/v1.0/pay/sessions/<session_id>/transaction/<transaction_id>', methods = ['DELETE'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def delete_transaction(session_id, transaction_id):
    session = sessions[session_id]
    reset_session_timeout(session)
    session['database_session'].rollback(
            session['transactions'][transaction_id]['used_tokens'])
    del session['transactions'][transaction_id]
    return make_response(jsonify({}), 204)

if __name__ == '__main__':
    app.run(debug = True, ssl_context=context)





