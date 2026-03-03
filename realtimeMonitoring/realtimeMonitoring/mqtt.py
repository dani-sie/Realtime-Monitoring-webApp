import json
import os
from datetime import timedelta

import paho.mqtt.client as mqtt
from django.db.models import Avg
from django.utils import timezone

from realtimeGraph.models import SensorData
from realtimeGraph.views import (
    create_sensorData,
    get_or_create_location,
    get_or_create_sensor,
    get_or_create_user,
)

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8080"))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
MQTT_CA_CERT = os.getenv("MQTT_CA_CERT")
MQTT_SUB_TOPIC = os.getenv("MQTT_SUB_TOPIC", "#")
MQTT_ACT_TOPIC_PREFIX = os.getenv("MQTT_ACT_TOPIC_PREFIX", "actuador/led")

TEMP_THRESHOLD = float(os.getenv("TEMP_THRESHOLD", "28"))
TEMP_WINDOW_MINUTES = int(os.getenv("TEMP_WINDOW_MINUTES", "10"))


def publish_actuator_command(client, user, state):
    topic = f"{MQTT_ACT_TOPIC_PREFIX}/{user}"
    client.publish(topic, state, qos=0, retain=False)


def evaluate_temperature_event(client, sensor, user):
    window_start = timezone.now() - timedelta(minutes=TEMP_WINDOW_MINUTES)
    avg_value = (
        SensorData.objects.filter(sensor=sensor, dateTime__gte=window_start)
        .aggregate(avg=Avg("value"))
        .get("avg")
    )
    if avg_value is None:
        return

    state = "ON" if avg_value > TEMP_THRESHOLD else "OFF"
    publish_actuator_command(client, user, state)


def on_message(client, userdata, message):
    payload = message.payload.decode("utf-8")
    payload_json = json.loads(payload)
    topic_parts = message.topic.split("/")

    if len(topic_parts) < 3:
        return

    variable = topic_parts[0].lower()
    location = topic_parts[1]
    user = topic_parts[2]

    user_obj = get_or_create_user(user)
    location_obj = get_or_create_location(location)
    sensor_obj = get_or_create_sensor(variable, user_obj, location_obj)
    create_sensorData(sensor_obj, payload_json["value"])

    if variable == "temperatura":
        evaluate_temperature_event(client, sensor_obj, user)


print("MQTT Start")
client = mqtt.Client("")
client.on_message = on_message

if MQTT_USER and MQTT_PASS:
    client.username_pw_set(MQTT_USER, MQTT_PASS)

if MQTT_CA_CERT:
    client.tls_set(ca_certs=MQTT_CA_CERT)

client.connect(MQTT_HOST, MQTT_PORT, 60)
client.subscribe(MQTT_SUB_TOPIC)
