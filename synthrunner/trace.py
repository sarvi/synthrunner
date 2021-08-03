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

TRACE_ID=str(uuid.uuid4()).replace('-','')

def push_trace(trace_data):
    """ Push data to kafka topic """
    kafka_nodes = [x.strip() for x in os.environ.get('KAFKA_NODES').split(',')] if os.environ.get('KAFKA_NODES', None) else []
    kafka_topic = os.environ.get('KAFKA_TOPIC')
    if not (kafka_nodes and kafka_topic):
        # telemetry kafka config not initialized
        log.debug("Telemetry: {}".format(pprint.pformat(trace_data)))
        log.debug(f"Not sending telemetry. kafka_topic={kafka_topic} OR kafka_nodes={kafka_nodes} not defined. \nTelemetry")
        return
    log.debug("Sending telemetry to {} on {}\n{}".format(kafka_topic, kafka_nodes, pprint.pformat(trace_data)))
    producer = Producer({'bootstrap.servers': ','.join(kafka_nodes)})
    producer.produce(kafka_topic, key=trace_data['dataKey'].encode('utf-8'), value=json.dumps(trace_data).encode('utf-8'))
    producer.flush()

def trace_start(request_type, name):
    if isinstance(name, list):
        name = ' '.join(name)
    span_id = "{}".format(random.getrandbits(64))
    synth_service_namespace = os.environ.get('SYNTHSERVICE', 'com.cisco.devx.synthrunner')
    service_type = "cli" if request_type == "EXEC" else "rest"
    synth_service_name="cli_{}".format(synth_service_namespace.split('.')[-1])
    tested_service_namespace=os.environ.get('TESTEDTOOL')
    tested_service_name=name.split(' ')[0] if request_type == "EXEC" else tested_service_namespace.split(".")[-1]
    tested_service_name=f"{service_type}_{tested_service_name}".lower()
    tested_service_method=f"{service_type}/{name}".replace(" ", "/") if request_type == "EXEC" else f"{service_type}/{request_type}{name}"
    assert synth_service_namespace is not None and tested_service_name is not None
    # Send telemetry data
    trace = {
        'name': f"{tested_service_namespace}.{tested_service_name}/{tested_service_method}",
        'trace_id': TRACE_ID,
        'span_id': span_id,
        'trace_state': {},
        "parent_id": None, # OPTIONAL. defaults to null
        "kind": "SpanKind.CLIENT",
        "start_time": int(round(time.time() * 1000)),
        "end_time": None,
        'status.status_code': 'UNSET',
        'status.status_value': 0,
        "service.name": synth_service_name,
        'service.namespace': synth_service_namespace,
        "host.name": socket.getfqdn().split('.')[0],
        'deployment.environment': os.environ.get('INSTALLTYPE', 'staging'),
        "peer.service.namespace": f"{tested_service_namespace}",
        "peer.service.name": f"{tested_service_name}",
        "peer.service.method": f"{tested_service_method}",
        'enduser.id': os.environ.get('USER', 'ngdevx'),
        'location.site': os.environ.get('SITE', 'unknown')
    }
    trace_data = {
        "source": os.environ.get('EVENT_SOURCE', 'com.cisco.devx.at'),
        "event": 'trace',
        "startTime": trace['start_time'],
        "endTime": trace.get('end_time', None),
        "dataKey": f'{TRACE_ID}.{span_id}',
        "data": trace
    }
    push_trace(trace_data)
    return trace_data

def trace_end(trace_data, status):
    trace_data['data']['end_time'] = int(round(time.time() * 1000))
    trace_data['data']['status.status_code'] = status
    assert status != 'UNSET', "Status needs to be set when ending a trace"
    trace_data['data']['status.status_value'] = 1 if status =='OK' else 2

    trace_data["endTime"] = trace_data['data']['end_time']
    push_trace(trace_data)
    return trace_data

