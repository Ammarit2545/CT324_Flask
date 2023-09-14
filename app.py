import paho.mqtt.client as mqttclient
import time
from flask import Flask, render_template

import mysql.connector

app = Flask(__name__)

# Define your MySQL database configuration
db_config = {
    'host': '161.82.216.192',
    'user': 'root',
    'password': 'ctkbu123',
    'database': 'ct_324_ammarit',  # Replace with your actual database name
    'port': 3306,
}

# Create a MySQL connection
db_connection = mysql.connector.connect(**db_config)
db_cursor = db_connection.cursor()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Client is Connected")
        global connected
        connected = True
        client.subscribe("/ARMTEST")  # Subscribe to the "/ARMTEST" topic when connected
        client.subscribe("/LIGHT")  # Subscribe to the "/LIGHT" topic
    else:
        print("Connection Failed")

def on_message(client, userdata, message):
    print(f"Received message '{message.payload.decode()}' on topic '{message.topic}'")

connected = False
broker_address = "10.22.5.149"
port = 1883
user = ""
password = ""

client = mqttclient.Client("MQTT")
client.username_pw_set(username=user, password=password)
client.on_connect = on_connect
client.on_message = on_message  # Set the callback function for incoming messages
client.connect(broker_address, port=port)
client.loop_start()
while not connected:
    time.sleep(0.2)

@app.route('/')
def index():
    return render_template('index.html')

led_state = "off"  # Initial LED state

@app.route('/publish')
def publish_led_off():
    global led_state  # Access the global variable to track LED state

    # Toggle the LED state
    if led_state == "off":
        led_state = "on"
        message = '{"mode":"ledon"}'
    else:
        led_state = "off"
        message = '{"mode":"ledoff"}'

    # Publish the MQTT message
    client.publish("/LIGHT", message)

    return f"Data sent to MQTT (LED state: {led_state})"

# Define a callback function for receiving MQTT messages
def on_mqtt_message(client, userdata, message):
    global mqtt_data

    # Extract the message payload
    mqtt_data = message.payload.decode()

    # Insert data into the MySQL database
    try:
        insert_query = "INSERT INTO led_status (l_status, L_date_in) VALUES (%s, NOW())"
        data = (mqtt_data,)
        db_cursor.execute(insert_query, data)
        db_connection.commit()
        print("Data inserted into MySQL database successfully.")
    except Exception as e:
        print(f"Error inserting data into MySQL database: {e}")

# Set the callback function for the /SENSOR topic
client.subscribe("/SENSOR")
client.on_message = on_mqtt_message

if __name__ == "__main__":
    app.run(debug=True)
