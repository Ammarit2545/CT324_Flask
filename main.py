import paho.mqtt.client as mqttclient
import time

def on_connect(client, usedata, flags, rc):
    if rc == 0:
        print("Client is Connected")
        global connected
        connected = True
        client.subscribe("/ARMTEST")  # Subscribe to the "/ARMTEST" topic when connected
    else:
        print("Connection Failed")

def on_message(client, userdata, message):
    print(f"Received message '{message.payload.decode()}' on topic '{message.topic}'")

connected = False
broker_address = "10.22.5.149"
port = 1883
user = "ops"
password = "ops2022"

client = mqttclient.Client("MQTT")
client.username_pw_set(user, password=password)
client.on_connect = on_connect
client.on_message = on_message  # Set the callback function for incoming messages
client.connect(broker_address, port=port)
client.loop_start()
while not connected:
    time.sleep(0.2)

client.publish("/ARMTEST", '{"mode":"asdasdasd"}')  # Publish the JSON data to the "/ARMTEST" topic
client.loop_stop()
