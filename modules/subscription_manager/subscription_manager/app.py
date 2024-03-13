import logging
import os
import threading

from flask import Flask, request

from task_manager.worker import app as celery_app

from subscription_manager.subscriber import Subscriber

LOG_LEVEL = os.getenv("LOG_LEVEL","DEBUG").upper()

# LOGGER
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger(__name__)

def create_app(test_config=None):

    # create subscriber
    subscriber = Subscriber()
    # start as thread
    mqtt_thread = threading.Thread(target=subscriber.client.loop_forever,
                                   daemon=True).start()

    # Load and start subscriptions
    #with open("subscriptions.json") as fh:
    #    subs = json.load(fh)
    subs = {}
    for topic, target in subs.items():
        subscriber.subscribe(topic, target)

    # Now create the flask app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    # Celery configuration
    app.config['CELERY_BROKER_URL'] = 'redis://redis:6379/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379/0'
    # Set up Celery
    celery_app.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND']
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


    @app.route('/wis2/subscriptions/list')
    def list_subscriptions():
        return subs

    @app.route('/wis2/subscriptions/add')
    def add_subscription():
        topic = request.args.get('topic', None)
        target = request.args.get('target', '')
        if topic==None:
            return "No topic passed"
        subscriber.subscribe(topic, target)

        return subscriber.active_subscriptions

    @app.route('/wis2/subscriptions/delete')
    def delete_subscription():
        topic = request.args.get('topic', None)
        if topic==None:
            return "No topic passed"
        subscriber.unsubscribe(topic)
        return subscriber.active_subscriptions

    return app

def main():
    app = create_app()
    app.run(host='0.0.0.0', port=5001)

if __name__ == "__main__":
    main()


# curl http://localhost:5001/wis2/subscriptions/add?topic=cache/a/wis2/%2B/%2B/data/core/weather/surface-based-observations/%23&target=test