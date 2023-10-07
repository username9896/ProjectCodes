import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pyrebase
import requests
import paho.mqtt.client as mqtt
import threading  # Import the threading module
import datetime
import re

# Firebase Configuration
config = {
  "apiKey" : "AIzaSyA3ihdn7YGt4_LPSMIgYU0Oa87p_cNUgHg",
  "authDomain": "shms-3646a.firebaseapp.com",
  "databaseURL": "https://shms-3646a-default-rtdb.firebaseio.com",
  "projectId": "shms-3646a",
  "storageBucket": "shms-3646a.appspot.com",
  "messagingSenderId": "719820678843",
  "appId": "1:719820678843:web:973f33b8f01c7fc590ab9e"
}

# Initialize Firebase
firebase = pyrebase.initialize_app(config)
db = firebase.database()

# Variables to store fetched data
bpm_data = []
ir_data = []
heart_rate_data = []
temperature_data = []
mqtt_recieve = " "

# MQTT broker information
broker_address = "broker.hivemq.com"  # Replace with your HiveMQ broker address
port = 1883  # Default MQTT port
topic = "shms"  # Replace with the MQTT topic you want to subscribe to
# MQTT topic to publish the emergency message
emergency_topic = "shms/rec"
root = tk.Tk()
emergency_frame = tk.Frame(root, bg="#4CAF50", height=110)
heart_rate_description = tk.Text(emergency_frame, height=2, width=37, wrap=tk.WORD, font=('Arial', 16), relief=tk.FLAT, bg="white")


# Callback when the client connects to the MQTT broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        client.subscribe(topic)
    else:
        print(f"Failed to connect to MQTT broker with code {rc}")

# Callback when a new message is received on the subscribed topic
def on_message(client, userdata, message):
    mqtt_recieve = message.payload.decode();
    print(f"Received message on topic '{message.topic}': {mqtt_recieve}")

    heart_rate_description.delete(1.0, tk.END)
    heart_rate_description.insert(tk.END, mqtt_recieve)
    
# Create an MQTT client
client = mqtt.Client()

# Set callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
client.connect(broker_address, port)

def mqtt_thread():
    client.loop_forever()

mqtt_thread = threading.Thread(target=mqtt_thread)
mqtt_thread.daemon = True  # Daemonize the thread
mqtt_thread.start()  # Start the MQTT thread

# Function to parse the date string with timezone information
def parse_date_with_timezone(date_str):
    # Use regular expressions to extract date, time, and timezone components
    match = re.match(r'(\w+ \w+ \d+ \d+ \d+:\d+:\d+) GMT\+(\d+) \(.+\)', date_str)
    if match:
        date_part = match.group(1)
        timezone_offset = int(match.group(2))
        
        # Convert timezone offset to hours and minutes
        hours, minutes = divmod(timezone_offset, 100)
        
        # Construct a datetime object with timezone information
        date_obj = datetime.datetime.strptime(date_part, "%a %b %d %Y %H:%M:%S")
        date_obj = date_obj.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=hours, minutes=minutes)))
        
        return date_obj
    else:
        raise ValueError("Invalid date format")

def handle_emergency():
    print("Emergency button clicked!")

def update_graph():
    try:
        # Fetch data from Firebase
        data = db.child("sensorData").get().val()
        if data:
            update_bpm_graph(data)
            update_heart_rate_graph(data)
            update_temperature_graph(data)
        else:
            print("No data found.")
    except Exception as e:
        print("An error occurred:", str(e))

    # Schedule this function to run again after a certain delay (e.g., 1000 ms or 1 second)
    root.after(1000, update_graph)

# Function to update BPM graph
def update_bpm_graph(data):
    ax_bpm.clear()
    dates = [parse_date_with_timezone(entry["Date"]) for entry in data.values()]
    bpm_values = [entry["BPM"] for entry in data.values()]
    ax_bpm.plot(dates, bpm_values, label='BPM', color='red')
    ax_bpm.set_xlabel('Date and Time')
    ax_bpm.set_ylabel('BPM')
    ax_bpm.set_title('BPM Monitoring')
    ax_bpm.legend()
    fig_bpm.autofmt_xdate()  # Rotate x-axis labels for better readability
    canvas_bpm.draw()

# Function to update Heart Rate graph
def update_heart_rate_graph(data):
    ax_heart_rate.clear()
    dates = [parse_date_with_timezone(entry["Date"]) for entry in data.values()]
    heart_rate_values = [entry["HeartRate"] for entry in data.values()]
    ax_heart_rate.plot(dates, heart_rate_values, label='Heart Rate', color='green')
    ax_heart_rate.set_xlabel('Date and Time')
    ax_heart_rate.set_ylabel('Heart Rate')
    ax_heart_rate.set_title('Heart Rate Monitoring')
    ax_heart_rate.legend()
    fig_heart_rate.autofmt_xdate()
    canvas_heart_rate.draw()

# Function to update Temperature graph
def update_temperature_graph(data):
    ax_temperature.clear()
    # Update the date format string for parsing
    dates = [parse_date_with_timezone(entry["Date"]) for entry in data.values()]
    temperature_values = [entry["temperature"] for entry in data.values()]
    ax_temperature.plot(dates, temperature_values, label='Temperature', color='purple')
    ax_temperature.set_xlabel('Date and Time')
    ax_temperature.set_ylabel('Temperature')
    ax_temperature.set_title('Temperature Monitoring')
    ax_temperature.legend()
    fig_temperature.autofmt_xdate()
    canvas_temperature.draw()


def create_emergency_message():
    emergency_window = tk.Toplevel(root)
    emergency_window.title("Emergency")
    center_window(emergency_window, 250, 100)  # Center the emergency window


    # Create a label with the emergency message
    message_label = tk.Label(emergency_window, text="Message Sent", font=('Arial', 16))
    message_label.pack(pady=10)

    # Function to handle the "OK" button press in the emergency window
    def handle_ok():
        # Close the emergency window
        emergency_window.destroy()

    # Create an "OK" button to close the emergency window
    ok_button = tk.Button(emergency_window, text="OK", bg="green", fg="white", font=('Arial', 14), command=handle_ok)
    ok_button.pack(pady=10)

def center_window(window, width, height):
    # Get the screen width and height
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Calculate the x and y coordinates to center the window
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    # Set the window's geometry to center it
    window.geometry(f"{width}x{height}+{x}+{y}")

def send_ifttt_alert(api_key, message):
    event_name = 'Send_data'  # Replace with the event name you set in IFTTT

    url = 'https://maker.ifttt.com/trigger/Send_data/json/with/key/b-F4U7NhssgKf42FkeqKxdSLYC5zTdTa31AS46cxJ8D'
    payload = {'value1': message}  # Use the 'message' parameter

    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print('Message sent successfully.')
    else:
        print(f'Error sending message. Status code: {response.status_code}')

# Function to publish an emergency message to the MQTT broker
def publish_emergency_message():
    emergency_message = "Emergency button pressed!"
    client.publish(emergency_topic, emergency_message)
    print(f"Published emergency message on topic '{emergency_topic}': {emergency_message}")

# Create main window

root.title("Smart Health Monitoring Dashboard")
root.geometry("1950x1400")  # Set window size
root.configure(bg="#f0f0f0")  # Set background color

# Common Heading for all Graphs
heading_frame = tk.Frame(root, bg="#4CAF50", height=100)  # Increased height for the heading
heading_frame.pack(fill=tk.X)

heading_label = tk.Label(heading_frame, text="Health Monitoring Data", fg="white", bg="#4CAF50", font=("Arial", 24))  # Larger font size
heading_label.pack(fill=tk.X, padx=40, pady=40)

# Content Frame
content_frame = tk.Frame(root, bg="#f0f0f0")
content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

# BPM monitoring tab
bpm_tab = ttk.Frame(content_frame, style="TFrame")
bpm_tab.pack(side=tk.LEFT, padx=20, pady=20, fill=tk.Y)

# Heart Rate monitoring tab
heart_rate_tab = ttk.Frame(content_frame, style="TFrame")
heart_rate_tab.pack(side=tk.LEFT, padx=20, pady=20, fill=tk.Y)

# Temperature monitoring tab
temperature_tab = ttk.Frame(content_frame, style="TFrame")
temperature_tab.pack(side=tk.LEFT, padx=20, pady=20, fill=tk.Y)

# Graph for BPM monitoring
fig_bpm = Figure(figsize=(6, 4), dpi=100)
ax_bpm = fig_bpm.add_subplot(1, 1, 1)
canvas_bpm = FigureCanvasTkAgg(fig_bpm, master=bpm_tab)
canvas_bpm.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Graph for Heart Rate monitoring
fig_heart_rate = Figure(figsize=(6, 4), dpi=100)
ax_heart_rate = fig_heart_rate.add_subplot(1, 1, 1)
canvas_heart_rate = FigureCanvasTkAgg(fig_heart_rate, master=heart_rate_tab)
canvas_heart_rate.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Graph for Temperature monitoring
fig_temperature = Figure(figsize=(6, 4), dpi=100)
ax_temperature = fig_temperature.add_subplot(1, 1, 1)
canvas_temperature = FigureCanvasTkAgg(fig_temperature, master=temperature_tab)
canvas_temperature.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

def handle_emergency():
    if __name__ == '__main__':
        api_key = 'b-F4U7NhssgKf42FkeqKxdSLYC5zTdTa31AS46cxJ8D'  # Replace with your actual IFTTT Webhooks API key
        message = 'Heartbeat not normal!'  # Set your desired message
        send_ifttt_alert(api_key, message)  # Call the function with both arguments
    publish_emergency_message()
    create_emergency_message()

# The common emergency button and text function (no need for multiple functions)
def create_common_emergency_button_and_text(parent_frame):
    
    emergency_frame.pack(fill=tk.X)
    
    # Text box with distinctive background color (moved below the graph)
   
    heart_rate_description.insert(tk.END, mqtt_recieve) 
    heart_rate_description.pack(pady=5, padx=5)

    emergency_button = tk.Button(emergency_frame, text="Emergency", bg="red", fg="white", font=('Arial', 14), command=handle_emergency)
    emergency_button.pack(pady=20)

# Creating common emergency button and text for all tabs
create_common_emergency_button_and_text(root)

# Start fetching data from Firebase and updating the graphs
update_graph()

# Start the main loop
root.mainloop()
