from flask import Flask, render_template, jsonify, request
import mysql.connector
import paho.mqtt.client as mqttclient
import time
import json  # Added import

app = Flask(__name__, static_url_path='/static')

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

# Initialize mqtt_data as a global variable
mqtt_data = ""


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Client is Connected")
        global connected
        connected = True
        # Subscribe to the "/ARMTEST" topic when connected
        client.subscribe("/ARMTEST")
        client.subscribe("/LIGHT")  # Subscribe to the "/LIGHT" topic
    else:
        print("Connection Failed")


def on_message(client, userdata, message):
    print(
        f"Received message '{message.payload.decode()}' on topic '{message.topic}'")


connected = False
broker_address = "45.136.239.169"
port = 1883
user = "dev"
password = "cegn2023"

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
    return render_template('main.html')


@app.route('/main')
def main_page():
    return render_template('index.html')


led_state = "off"  # Initial LED state


@app.route('/publish')
def publish_led():
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

    # Insert data into the MySQL database
    try:
        insert_query = "INSERT INTO led_status (l_status, L_date_in) VALUES (%s, NOW())"
        data = (led_state,)
        db_cursor.execute(insert_query, data)
        db_connection.commit()
        app.logger.info("Data inserted into MySQL database successfully.")
    except Exception as e:
        app.logger.error(f"Error inserting data into MySQL database: {e}")

    return f"Data sent to MQTT (LED state: {led_state})"


# Define a callback function for receiving MQTT messages
def on_mqtt_message(client, userdata, message):
    global mqtt_data

    # Extract the message payload
    mqtt_data = message.payload.decode()

    # Split the message payload into a key-value pair
    try:
        data = json.loads(mqtt_data)
        key = "Sensor"
        value = data.get(key)
    except json.JSONDecodeError as e:
        # Handle JSON parsing errors
        app.logger.error(f"Error parsing MQTT data: {e}")
        return


# Serve the HTML form at this route
@app.route('/data_input_form', methods=['GET'])
def data_input_form():
    return render_template('data_input_form.html')


@app.route('/insert_data', methods=['GET'])
def insert_data():
    try:
        sensor_value1 = request.form.get('sensor_value1')
        lux = request.form.get('lux')

        # Insert data into the database
        insert_query = "INSERT INTO data_detail (d_val_1, d_date_in) VALUES (%s, NOW())"
        data = (lux,)

        db_cursor.execute(insert_query, data)
        db_connection.commit()

        return "Data inserted successfully.", 200
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return f"Error: {str(e)}", 500

    time.sleep(4)


@app.route('/subscribe')
def subscribe_mqtt_data():
    global mqtt_data

    # Get the MQTT data from the global variable
    mqtt_payload = mqtt_data

    # Check if there is MQTT data available
    if mqtt_payload:
        try:
            # Parse the MQTT data into key-value pairs
            key, value = mqtt_payload.split(':')

            # Insert the data into the database
            insert_query = "INSERT INTO data_detail (d_val_1, d_date_in) VALUES (%s, NOW())"
            data = (value,)
            db_cursor.execute(insert_query, data)
            db_connection.commit()

            # Return a response indicating success
            return jsonify({"message": "Data inserted successfully."})
        except Exception as e:
            # Handle any errors that may occur during insertion
            app.logger.error(f"Error inserting data into MySQL database: {e}")
            return jsonify({"error": str(e)}), 500
    else:
        # Handle the case when there is no MQTT data available
        return jsonify({"message": "No MQTT data available."})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
