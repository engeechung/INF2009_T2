import RPi.GPIO as GPIO
import time
import threading
import paho.mqtt.client as mqtt

# Define GPIO pins for the HC-SR04P
TRIG = 23  # GPIO23 (Pin 16)
ECHO = 24  # GPIO24 (Pin 18)

# MQTT Settings
BROKER = "172.20.10.4"
TOPIC = "pushup/badposture"
mqtt_client = mqtt.Client("Pi3Publisher")
mqtt_client.connect(BROKER, 1883)
mqtt_client.loop_start()

# Global Variables
pushup_enabled = False
pushup_thread = None
baseline_top_distance = None
baseline_bottom_distance = None
TOLERANCE = 5
MAX_DISTANCE = 300
MIN_DISTANCE = 0

# Add these constants at the top with other global variables
DIRECTION_CHANGE_THRESHOLD = 2  # Minimum cm change to count as direction change
CONSECUTIVE_WRONG_READINGS = 3  # Number of consecutive readings needed to confirm direction change

# Add these variables with other global variables
current_direction = None
previous_direction = None
consecutive_wrong_down = 0  # Track consecutive wrong readings when going down
consecutive_wrong_up = 0    # Track consecutive wrong readings when going up

# Flags for tracking push-up state
pushup_in_progress = False
bad_posture_flag = False
pushup_depth_reached = False
reached_top = False

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def get_distance():
    """Measure distance using ultrasonic sensor."""
    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # 10µs pulse
    GPIO.output(TRIG, False)

    # Wait for echo response
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()

    # Calculate distance
    pulse_duration = pulse_end - pulse_start
    distance = (pulse_duration * 34300) / 2  # Speed of sound is 343 m/s

    return round(distance, 2)
    
def current_direction_subscribe(x):
    global current_direction, reached_top
    current_direction = x
    if x == "down":
        reached_top = False
    
def record_baseline_top():
    """Stores top (apex) position of push-up."""
    global baseline_top_distance
    while True:
        distance = get_distance()
        if MIN_DISTANCE < distance < MAX_DISTANCE:
            baseline_top_distance = distance
            print(f"Baseline Top Distance: {baseline_top_distance} cm")
            break
            
def record_baseline_bottom():
    """Stores bottom position of push-up."""
    global baseline_bottom_distance
    while True:
        distance = get_distance()
        if MIN_DISTANCE < distance < 10:
            baseline_bottom_distance = distance
            print(f"Baseline Bottom Distance: {baseline_bottom_distance} cm")
            break
            
def reset_baseline():
    """Resets baseline values."""
    global baseline_top_distance, baseline_bottom_distance
    baseline_top_distance = None
    baseline_bottom_distance = None
    time.sleep(0.01)
    
def check_pushup():
    global pushup_enabled, current_direction, previous_direction, bad_posture_flag
    global consecutive_wrong_down, consecutive_wrong_up, reached_top
    
    previous_distance = None
    
    while pushup_enabled:
        distance = get_distance()
        
        # Skip invalid readings
        if distance <= MIN_DISTANCE or distance >= MAX_DISTANCE:
            time.sleep(0.05)
            continue
            
        # Skip first reading
        if previous_distance is None:
            previous_distance = distance
            time.sleep(0.05)
            continue
        
        print(f"Distance: {distance} cm, Baseline Top: {baseline_top_distance} cm")
        # --- Reset after reaching top again ---
        if reached_top == False:
            if abs(distance - baseline_top_distance) <= TOLERANCE and current_direction == "up":
                reached_top = True
                mqtt_client.publish(TOPIC, "Attempt counted")
                print("Attempt counted")
                
        if abs(distance - baseline_bottom_distance) <= TOLERANCE and current_direction == "down":
            print("User at bottom")
            mqtt_client.publish(TOPIC, "Bottom reached")
        
        # Calculate the difference
        diff = distance - previous_distance
        
        if current_direction == "down":
            # When going down, distance should DECREASE (negative diff)
            # If it's increasing by more than threshold, that's wrong
            if diff > DIRECTION_CHANGE_THRESHOLD:
                consecutive_wrong_down += 1
                if consecutive_wrong_down >= CONSECUTIVE_WRONG_READINGS:
                    print("Bad posture: Moving up while supposed to be going down")
                    mqtt_client.publish(TOPIC, "Bad posture")
                    consecutive_wrong_down = 0  # Reset after alerting
            else:
                consecutive_wrong_down = 0  # Reset counter when movement is correct
                
        elif current_direction == "up":
            # When going up, distance should INCREASE (positive diff)
            # If it's decreasing by more than threshold, that's wrong
            if diff < -DIRECTION_CHANGE_THRESHOLD:
                consecutive_wrong_up += 1
                if consecutive_wrong_up >= CONSECUTIVE_WRONG_READINGS:
                    print("Bad posture: Moving down while supposed to be going up")
                    mqtt_client.publish(TOPIC, "Bad posture")
                    consecutive_wrong_up = 0  # Reset after alerting
            else:
                consecutive_wrong_up = 0  # Reset counter when movement is correct
            
        previous_distance = distance
        previous_direction = current_direction
        time.sleep(0.15)  # Slightly longer delay to reduce noise
        
def start_pushup_monitoring():
    """Starts monitoring push-ups in a separate thread."""
    global pushup_enabled, pushup_thread
    if not pushup_enabled:
        pushup_enabled = True
        pushup_thread = threading.Thread(target=check_pushup, daemon=True)
        pushup_thread.start()
        print("Push-up monitoring started.")

def stop_pushup_monitoring():
    """Stops monitoring push-ups."""
    global pushup_enabled
    pushup_enabled = False
    print("Push-up monitoring stopped.")
