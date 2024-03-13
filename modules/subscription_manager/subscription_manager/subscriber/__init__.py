from datetime import datetime
from fnmatch import fnmatch
import json
import logging
import os
import ssl

import paho.mqtt.client as mqtt

from task_manager.workflows import wis2_download_and_ingest

LOGGER = logging.getLogger(__name__)

LOG_LEVEL = os.getenv("LOG_LEVEL","DEBUG").upper()
LOGGER.setLevel(LOG_LEVEL)

class Subscriber():
    def __init__(self, broker: str = "globalbroker.meteo.fr",
                 port: int = 443, uid: str = "everyone",
                 pwd: str = "everyone", protocol: str = "websockets"):
        self.broker = broker
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, transport = protocol)
        self.client.tls_set(ca_certs=None, certfile=None, keyfile=None,
                            cert_reqs=ssl.CERT_REQUIRED,
                            tls_version=ssl.PROTOCOL_TLS, ciphers=None)
        self.client.username_pw_set(uid, pwd)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe
        self.active_subscriptions = {}
        result = self.client.connect(broker, port)
    def _on_connect(self, client, userdata, flags, rc):
        LOGGER.debug("Connected")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        LOGGER.debug("Subscribed")

    def _on_message(self, client, userdata, msg):
        LOGGER.debug(f"Message received on topic {msg.topic}")
        job = {
            "topic": msg.topic,
            "payload": json.loads(msg.payload),
            "target": self.active_subscriptions.get(msg.topic),
            "_broker": self.broker,
            "_received": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
        if job['target'] == None:
            # We are likely using a wildcard in our subscription, we need to
            # use a different (more costly match)
            for key, value in self.active_subscriptions.items():
                if fnmatch(msg.topic, value['pattern']):
                    job['target'] = value['target']
                    break

        if job['target'] == None:
            LOGGER.warning("Message received but unable to match target")
            LOGGER.warning(f"Topic: {msg.topic}")
            LOGGER.warning(f"Payload: {msg.payload}")
            LOGGER.warning(f"Active subscriptions:\n{json.dumps(self.active_subscriptions, indent=4)}")
            LOGGER.warning("Message skipped")
        else:
            job['_queued'] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            workflow = wis2_download_and_ingest(job)
            workflow.apply_async()

    def subscribe(self, topic, target):
        if topic in self.active_subscriptions:
            LOGGER.warning(f"Topic ({topic}) already subscribed.")
        else:
            self.active_subscriptions[topic] = {
                'target': target,
                'pattern': topic.replace("+","*").replace("#","*")
            }
            self.client.subscribe(topic)
            LOGGER.info(f"Subscribed to {topic} on {self.broker}")

        return self.active_subscriptions

    def unsubscribe(self, topic):
        if topic in self.active_subscriptions:
            self.client.unsubscribe(topic)
            del self.active_subscriptions[topic]
        else:
            LOGGER.warning(f"subscription for topic {topic} not found")

        return self.active_subscriptions