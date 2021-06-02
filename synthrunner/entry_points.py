"""
synthrunner.entry_points.py
~~~~~~~~~~~~~~~~~~~~~~

This module contains the entry-point functions for the synthrunner module,
that are referenced in setup.py.
"""
import json
import os
import socket
import time

from dotenv import load_dotenv
from kafka import KafkaProducer
from locust.main import main as locust_main
from locust_plugins import *


def push_telemetry(name, val, label_dict):
    """ Push data to kafka topic """
    kafka_nodes = [x.strip() for x in os.environ.get('KAFKA_BOOTSTRAP_NODES', '').split(',')]
    kafka_topic = os.environ.get('KAFKA_TOPIC')
    message = {
        'name': name,
        'type': 'histogram',
        'value': val,
        'documentation': 'Synthetic Run Elapsed Time',
        'timestamp': round(time.time() * 1000),
        'labels': label_dict or {}
    }
    if not (kafka_nodes and kafka_topic):
        # telemetry kafka config not initialized
        return
    print("Metrics payload: \n" + json.dumps(message, indent=4))
    return
    producer = KafkaProducer(bootstrap_servers=kafka_nodes,
                             value_serializer=lambda v:
                             json.dumps(v).encode('utf-8'))
    producer.send(kafka_topic, message)
    producer.flush()


@events.request.add_listener
def my_request_handler(request_type, name, response_time, response_length, response,
                       context, exception, **kwargs):
    if exception:
        print(f"Request to {name} failed with exception {exception}")
    else:
        print(f"Successfully made a request to: {name}")
    # Send telemetry data
    labels = {
        'endpoint': name,
        'method': request_type,
        'version': os.environ.get('VERSION', 'unknown'),
        'status': 'SUCCESS' if not exception and response.ok else 'FAILURE',
        'status_code': response.status_code,
        'env': os.environ.get('ENV', 'STAGE'),
        'hostname': socket.getfqdn(),
        'site': os.environ.get('SITE', 'unknown'),
        'realUser': None,
        'processUser': os.environ.get('USER', 'ngdevx'),
        'runMode': 'CLI' if request_type == "EXEC" else "REST"
    }
    push_telemetry('out_synrunner_time', response_time, labels)


def main() -> None:
    """Main package entry point.

    Delegates to other functions based on user input.
    """

    try:
        load_dotenv()
        # Ensure that number of locust iterations is set, defaults to 1
        # Synthetic runner must not spawn new instances unless iterations > 1
        os.environ.setdefault('LOCUST_ITERATIONS', '1')
        # Synth runner always run in headless mode
        os.environ.setdefault('LOCUST_HEADLESS', 'true')
        locust_main()
    except IndexError:
        RuntimeError('please supply a command for synthrunner - e.g. install.')
    return None
