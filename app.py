import random
import time
import uuid

import requests
from celery import Celery
from celery.utils.log import get_task_logger
from flask import (Flask, current_app, jsonify, redirect, render_template,
                   request, session, url_for)
from flask_socketio import SocketIO, disconnect, emit

logger = get_task_logger(__name__)

app = Flask(__name__)
app.debug = True
app.clients = {}
app.config['SECRET_KEY'] = 'top-secret!'

# Celery configuration

# Redis
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# RabbitMQ
# app.config['CELERY_BROKER_URL'] = 'amqp://localhost://'
# app.config['CELERY_RESULT_BACKEND'] = 'rpc://'

# SocketIO
socketio = SocketIO(app)

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


@celery.task(bind=True)
def long_task(self, elementid, userid, url: str):
    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
        meta = {'current': i, 'total': total, 'status': message,
                'elementid': elementid, 'userid': userid}
        requests.post(url, json=meta)
        logger.info(msg='#'*20+'Before'+'#'*20)
        logger.info(msg=time.time())
        time.sleep(1)
        logger.info(msg=time.time())
        logger.info(msg='#'*20+'After'+'#'*20)

    meta = {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42, 'elementid': elementid, 'userid': userid}
    r = requests.post(url, json=meta)
    if r.status_code == 404:
        logger.info('client disconnected')
        logger.info('should stop sending updates to the client')
    return meta


def write_to_log(d):
    with open('log.log', 'a') as logfile:
        logfile.write(str(d)+'\n')


@app.route('/clients', methods=['GET'])
def clients():
    return jsonify({'clients': app.clients.keys()})


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')

    return redirect(url_for('index'))


@app.route('/longtask', methods=['POST'])
def longtask():
    # from IPython.core.debugger import Tracer; Tracer()()
    elementid = request.json['elementid']
    userid = request.json['userid']
    _ = long_task.delay(elementid, userid, url_for('event', _external=True))
    return jsonify({}), 202


@app.route('/event/', methods=['POST'])
def event():
    userid = request.json['userid']
    data = request.json
    ns = app.clients.get(userid)
    if ns and data:
        socketio.emit('celerystatus', data, namespace=ns)
        return 'ok'
    return 'error', 404


@socketio.on('status', namespace='/events')
def events_message(message):
    emit('status', {'status': message['status']})


@socketio.on('disconnect request', namespace='/events')
def disconnect_request():
    emit('status', {'status': 'Disconnected!'})
    disconnect()


@socketio.on('connect', namespace='/events')
def events_connect():
    userid = str(uuid.uuid4())
    session['userid'] = userid
    current_app.clients[userid] = request.namespace
    emit('userid', {'userid': userid})
    emit('status', {'status': 'Connected user', 'userid': userid})


@socketio.on('disconnect', namespace='/events')
def events_disconnect():
    del current_app.clients[session['userid']]
    print('Client %s disconnected' % session['userid'])


if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app)
