"""
synthrunner.entry_points.py
~~~~~~~~~~~~~~~~~~~~~~

This module contains the entry-point functions for the synthrunner module,
that are referenced in setup.py.
"""
import json
import locust_plugins
import os
import time
from locust.main import main as locust_main
from dotenv import load_dotenv
from locust import events
from kafka import KafkaProducer

def push_telemetry(name, val, label_dict):
    """ Push data to kafka topic """
    kafka_nodes = os.environ.get('KAFKA_BOOTSTRAP_NODES', '').split(',')
    kafka_topic = os.environ.get('KAFKA_TOPIC')
    if not(kafka_nodes and kafka_topic):
        # telemetry kafka config not initialized
        return
    message = {
        'name': name,
        'type': 'histogram',
        'value': 0 if val else 1,
        'documentation': 'Synthetic Run Result',
        'timestamp': round(time.time() * 1000),
        'labels': label_dict or {}
    }
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

    rval = False if exception else response.ok
    # Send telemetry data
    labels = {
        'endpoint': name,
        'method': request_type,
        'version': os.environ.get('VERSION', 'unknown'),
        'status': 'SUCCESS' if not exception and response.ok else 'FAILURE',
        'status_code': response.status_code,
        'env': os.environ.get('ENV', 'STAGE'),
        'hostname': os.environ.get('HOST'),
        'site': os.environ.get('SITE', 'unknown'),
        'realUser': None,
        'processUser': os.environ.get('USER', 'ngdevx'),
        'runMode': "REST"
    }
    push_telemetry('synthetic_run', rval, labels)


def main() -> None:
    """Main package entry point.

    Delegates to other functions based on user input.
    """

    try:
        load_dotenv()
        # Ensure that number of locust iterations is set, defaults to 1
        # Synthetic runner must not spawn new instances unless iterations > 1
        os.environ.setdefault('LOCUST_ITERATIONS', '1')
        locust_main()
    except IndexError:
        RuntimeError('please supply a command for synthrunner - e.g. install.')
    return None
