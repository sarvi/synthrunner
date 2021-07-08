import os
import socket
import uuid
import time
import logging
import json
import pprint
import random
from confluent_kafka import Producer


log = logging.getLogger(__name__)  # pylint: disable=locally-disabled, invalid-name

TRACE_ID=str(uuid.uuid4())

def push_trace(trace_data):
    """ Push data to kafka topic """
    kafka_nodes = [x.strip() for x in os.environ.get('KAFKA_NODES', '').split(',')]
    kafka_topic = os.environ.get('KAFKA_TOPIC')
    if not (kafka_nodes and kafka_topic):
        # telemetry kafka config not initialized
        log.debug(f"Not sending telemetry. kafka_nodes={kafka_nodes} or kafka_topic={kafka_topic} not defined")
        return
    log.debug("Sending telemetry to {} on {}\n{}".format(kafka_topic, kafka_nodes, pprint.pformat(trace_data)))
    producer = Producer({'bootstrap.servers': ','.join(kafka_nodes)})
    producer.produce(kafka_topic, key=trace_data['dataKey'].encode('utf-8'), value=json.dumps(trace_data).encode('utf-8'))
    producer.flush()

def trace_start(request_type, name):
    span_id = "{}".format(random.getrandbits(64))
    service_type = "cli" if request_type == "EXEC" else "rest"
    testservice="{}.{}_{}".format(os.environ.get('TESTSERVICE'), service_type, os.environ.get('TESTSERVICE').split('.')[-1])
    service=os.environ.get('TOOL')
    microservice=name.split(" ")[0] if request_type == "EXEC" else service.split(".")[-1]
    microservice=f"{request_type}_{microservice}".lower()
    attributes = {

    } if request_type == 'EXEC' else {

    }
    attributes.update({
        'enduser.id': os.environ.get('USER', 'ngdevx'),
        'location.site': os.environ.get('SITE', 'unknown')
    })

    method=f"{service_type}/{name}".replace(" ", "/") if request_type == "EXEC" else f"{service_type}/{request_type}{name}"
    assert service is not None and microservice is not None
    # Send telemetry data
    trace = {
        'name': f"{service}.{microservice}/{method}",
        'context': {
            'trace_id': TRACE_ID,
            'span_id': span_id,
            'trace_state': {},
        },
        "parent_id": None, # OPTIONAL. defaults to null
        "kind": "SpanKind.CLIENT",
        "start_time": int(round(time.time() * 1000)),
        "end_time": None,
        'status': {
            'status_code': 'UNSET',
        },
        'attributes': attributes,
        'resource': {
            "service.name": testservice,
            "host.name": socket.getfqdn().split('.')[0],
            'env.name': os.environ.get('INSTALLTYPE', 'STAGE'),
        },
    }
    trace_data = {
        "source": os.environ.get('NG_SOURCE', 'com.cisco.devx.synthrunner.trace'),
        "event": trace['kind'],
        "startTime": trace['start_time'],
        "endTime": trace.get('end_time', None),
        "dataKey": str(uuid.uuid4()),
        "data": trace
    }
    push_trace(trace_data)
    return trace_data

def trace_end(trace_data, status):
    trace_data['data']['end_time'] = int(round(time.time() * 1000))
    trace_data['data']['status']['status_code'] = status
    trace_data["endTime"] = trace_data['data']['end_time']
    push_trace(trace_data)
    return trace_data

