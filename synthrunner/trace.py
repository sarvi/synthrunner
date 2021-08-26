import os
import socket
import uuid
import time
import logging
import json
import pprint
import random
from os import environ
from confluent_kafka import Producer
from opentelemetry.exporter.kafka.json import KafkaExporter, StartEndSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry import trace


log = logging.getLogger(__name__)  # pylint: disable=locally-disabled, invalid-name
tracer = trace.get_tracer(__name__)

TRACE_ID=str(uuid.uuid4()).replace('-','')

def trace_init():
    resource = Resource.create(
        attributes={
            "service.name": 'cli_synthrunner',
            "service.namespace": os.environ.get('SYNTHSERVICE'),
        })

    traceprovider = TracerProvider(resource=resource)
    trace.set_tracer_provider(traceprovider)

    # create a ZipkinExporter
    kafka_exporter = KafkaExporter(
        # kafkatopic="<KAFKA Topic to send tracing to",
        # kafkanodes=[<list of Kafka Nodes>],
        # version=Protocol.V2
        # optional:
        # local_node_ipv4="192.168.0.1",
        # local_node_ipv6="2001:db8::c001",
        # local_node_port=31313,
        # max_tag_value_length=256
        # timeout=5 (in seconds)
    )

    # Create a BatchSpanProcessor and add the exporter to it
    span_processor = StartEndSpanExporter(kafka_exporter)

    traceprovider.add_span_processor(span_processor)
    # tested_service_namespace='com.cisco.devx.wit'
    # tested_service_name='cli_wit'
    # tested_service_method='cli/wit/space/create'

    # tracer = trace.get_tracer(__name__)
    # with tracer.start_as_current_span(f"{tested_service_namespace}.{tested_service_name}{tested_service_method}", kind=trace.SpanKind.CLIENT) as span:
    #     span.set_attributes({
    #         "peer.service.namespace": f"{tested_service_namespace}",
    #         "peer.service.name": f"{tested_service_name}",
    #         "peer.service.method": f"{tested_service_method}",
    #         'location.site': environ.get('SITE', 'unknown')
    #     })
    #     print("Hello world!")
    #     # time.sleep(5)
    #     span.set_status(Status(StatusCode.OK))
    # # time.sleep(5)
    # print('Hello World')


# def push_trace(trace_data):
#     """ Push data to kafka topic """
#     kafka_nodes = [x.strip() for x in os.environ.get('KAFKA_NODES').split(',')] if os.environ.get('KAFKA_NODES', None) else []
#     kafka_topic = os.environ.get('KAFKA_TOPIC')
#     if not (kafka_nodes and kafka_topic):
#         # telemetry kafka config not initialized
#         log.debug("Telemetry: {}".format(pprint.pformat(trace_data)))
#         log.debug(f"Not sending telemetry. kafka_topic={kafka_topic} OR kafka_nodes={kafka_nodes} not defined. \nTelemetry")
#         return
#     log.debug("Sending telemetry to {} on {}\n{}".format(kafka_topic, kafka_nodes, pprint.pformat(trace_data)))
#     producer = Producer({'bootstrap.servers': ','.join(kafka_nodes)})
#     producer.produce(kafka_topic, key=trace_data['dataKey'].encode('utf-8'), value=json.dumps(trace_data).encode('utf-8'))
#     producer.flush()

def trace_start(request_type, name, instance=None):
    if isinstance(name, list):
        name = ' '.join(name)
    name = os.path.basename(name)
    tested_service_type = "cli" if request_type == "EXEC" else "rest"
    tested_service_namespace=os.environ.get('TESTEDTOOL')
    if instance is not None:
        tested_service_namespace = '.'.join([tested_service_namespace, instance])
    tested_service_name=os.path.basename(name.split(' ')[0]) if request_type == "EXEC" else tested_service_namespace.split(".")[-1]
    tested_service_name=f"{tested_service_type}_{tested_service_name}".lower()
    tested_service_method=f"{tested_service_type}/{name}".replace(" ", "/") if request_type == "EXEC" else f"{tested_service_type}/{request_type}{name}"
    assert tested_service_name is not None

    span = tracer.start_span(
        f"{tested_service_namespace}.{tested_service_name}/{tested_service_method}",
        kind=trace.SpanKind.CLIENT,
        attributes={
            "peer.service.namespace": f"{tested_service_namespace}",
            "peer.service.name": f"{tested_service_name}",
            "peer.service.method": f"{tested_service_method}",
            'location.site': environ.get('SITE', 'unknown')
        })
    return span

def getstatus(status):
    forced_status = environ.get('TESTING_FORCE_ERROR', None)
    if forced_status is not None:
        forced_status = forced_status.strip()
        log.debug(f"TESTING_FORCE_ERROR Forcing status from {status} to {forced_status}")
        if forced_status=="ERROR":
            status = trace.StatusCode.ERROR
        elif forced_status == "OK":
            status = trace.StatusCode.OK
        elif forced_status == "UNSET":
            status = trace.StatusCode.UNSET
        else:
            log.debug(f"Unkown forced status {forced_status}")
    return trace.status.Status(status)


def trace_end(span, status):
    span.set_status(getstatus(status))
    span.end()

