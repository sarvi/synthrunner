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
import uuid
import logging
from synthrunner import utils

from dotenv import load_dotenv
from confluent_kafka import Producer
from locust.main import main as locust_main
from locust_plugins import *

log = logging.getLogger(__name__)  # pylint: disable=locally-disabled, invalid-name

def push_telemetry(val, label_dict):
    """ Push data to kafka topic """
    kafka_nodes = [x.strip() for x in os.environ.get('KAFKA_NODES', '').split(',')]
    kafka_topic = os.environ.get('KAFKA_TOPIC')
    cid = uuid.uuid4()
    end_ts = round(time.time() * 1000)
    start_ts = end_ts - round(val)
    data = {
        "source": os.environ.get('NG_SOURCE', 'com.cisco.devx.synthrunner.trace'),
        "event": os.environ.get('NG_EVENT', 'SpanKindClient'),
        "startTime": start_ts,
        "endTime": end_ts,
        "dataKey": str(cid),
        "data": label_dict or {}
    }
    if not (kafka_nodes and kafka_topic):
        # telemetry kafka config not initialized
        log.debug(f"Not sending telemetry. kafka_nodes={kafka_nodes} or kafka_topic={kafka_topic} not defined")
        return
    log.debug(f"Sending telemetry {data}")
    producer = Producer({'bootstrap.servers': ','.join(kafka_nodes)})
    producer.produce(kafka_topic, key=data['dataKey'].encode('utf-8'), value=json.dumps(data).encode('utf-8'))
    producer.flush()


@events.request.add_listener
def my_request_handler(request_type, name, response_time, response_length, response,
                       context, exception, **kwargs):
    if exception:
        log.debug(f"Request to {name} failed with exception {exception}")
    else:
        log.debug(f"Successfully made a request to: {name}")
    # Send telemetry data
    labels = {
        'name': os.environ.get('TOOL', 'synthrunner'),
        'endpoint': '%s %s' % (request_type, name),
        'endpoint_type': 'CLI' if request_type == "EXEC" else "API",
        'status': 'ERROR' if exception else ('OK' if response.ok else 'FAIL'),
        'status_code': response.status_code,
        'env': os.environ.get('ENV', 'STAGE'),
        'hostname': socket.getfqdn().split('.')[0],
        'site': os.environ.get('SITE', 'unknown'),
        'userId': os.environ.get('USER', 'ngdevx'),
    }
    push_telemetry(response_time, labels)

@utils.timethis
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
        os.environ.setdefault('LOCUST_TAGS', 'synth')
        locust_main()
    except IndexError:
        RuntimeError('please supply a command for synthrunner - e.g. install.')
    return None
