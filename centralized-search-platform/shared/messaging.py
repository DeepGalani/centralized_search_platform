import pika
import json
import os
from datetime import datetime

import threading

class RabbitMQPublisher:
    def __init__(self, queue_name: str):
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.host = os.getenv("RABBITMQ_HOST", "localhost")
        self.user = os.getenv("RABBITMQ_USER", "user")
        self.password = os.getenv("RABBITMQ_PASS", "password")
        self._lock = threading.Lock()

    def connect(self):
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(host=self.host, credentials=credentials)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True)

    def publish_event(self, event_type: str, data: dict):
        with self._lock:
            if not self.connection or self.connection.is_closed:
                self.connect()
            
            message = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                )
            )
            print(f" [x] Sent {event_type} event")

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
