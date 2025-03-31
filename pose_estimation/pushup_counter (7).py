import cv2
import numpy as np
import mediapipe as mp
import pose_estimation as pm
import time
import paho.mqtt.client as mqtt
from firestore_manager import FirestoreManager
import os
import json
import pygame
import subprocess

# Global variables
count = 0                  # Number of successful pushups
direction = 0              # 0: going down, 1: going up
attempt_count = 0          # Number of total attempts
bad_form_images = []       # List to store paths of saved bad form images
current_attempt_saved = False  # Track if we've saved a bad form image for the current attempt
counting = False           # Whether we're in counting mode
ready_hold_time = None     # Time when ready position was first detected
last_status = None         # Last user status
timer_started = False      # Whether the session timer has started
timer_start_time = None    # When the timer started
mqtt_client = None         # MQTT client
firestore_mgr = None       # Firestore manager
abnormal = False
bad_form_detected = False
at_top = False
at_bottom = False

# Add this function to handle incoming messages
def on_message(client, userdata, message):
    global abnormal, current_attempt_saved, bad_form_detected, at_top, at_bottom, attempt_count, direction
    
    topic = message.topic
    payload = message.payload.decode("utf-8")
    
    if topic == "pushup/badposture":
        # Convert the payload to a boolean
        if payload == "Bad posture":
            abnormal = True
            bad_form_detected = True
            print(f"Received abnormal posture alert: {abnormal} current direction: {direction}")

        if payload == "Attempt counted":
            attempt_count += 1
            at_top = True
            print(f"Current attempt saved alert")
            print(f"Attempt Number: {attempt_count}")
            
        if payload == "Bottom reached":
            at_bottom = True

def setup_mqtt():
    """Initializes and returns an MQTT client."""
    global mqtt_client
    broker_address = "172.20.10.4"
    client = mqtt.Client("PushupCounter") # Create client with ID "PushupCounter"

    client.on_message = on_message
    
    try:
        client.connect(broker_address, 1883) # Connect to broker on standard port
        client.subscribe("pushup/badposture", qos=2)
        client.loop_start() # Start background thread to handle network traffic
        mqtt_client = client
        return True
    except Exception as e:
        print(f"MQTT connection error: {e}")
        return False

def setup_camera():
    """Initializes the video capture object."""
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)  # Keep resolution balanced for speed
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)  # Request 30 FPS (Mediapipe will process as fast as possible)
    return cap 
    
def detect_form_issues(elbow, shoulder, hip):
    """Detect specific form issues and returns the issue description if found."""
    error = "Unknown Error"

    if elbow > 90 and elbow < 145:
        error = "Elbow angle incorrect"
    elif hip < 145:
        error = "Hip angle incorrect - back not straight"
    elif (elbow > 90 and elbow < 145) and hip < 145:
        error = "Hip and Elbow error"

    return error

#Function to play Audio Recording
def play_sound(file_name):
    # Initialize the mixer module if not already done
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    try:
        pygame.mixer.music.load(f"{file_name}.mp3")  # use .wav if preferred
        pygame.mixer.music.play()
    except Exception as e:
        print(f"Error playing sound: {e}")

    
def save_bad_form(img, issue_type, attempt_num):
    """Save images of bad form for later review."""

    if issue_type is not None:

        # Create directory if it doesn't exist
        os.makedirs("bad_form", exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"bad_form/attempt_{attempt_num + 1}_{issue_type}_{timestamp}.jpg"
        
        # Save the image
        cv2.imwrite(filename, img)
        print(f"Saved bad form image: {filename}")

        bad_form_images.append(filename)
        
        return filename
    
    
def update_count(elbow, shoulder, hip, img):
    """Determines the feedback message and updates the count based on the angles.
    Also detects form issues and uploads to Firestore if necessary."""
    global count, direction, attempt_count, timer_started
    global timer_start_time, bad_form_images, current_attempt_saved, mqtt_client
    global abnormal, current_attempt_saved, bad_form_detected, at_top, at_bottom

    current_time = time.time()

    if (hip < 145 or hip > 185) and current_attempt_saved == False:
        print(f"HIP error")
        subprocess.call(['espeak', 'Straighten Back'])
        current_attempt_saved = True
        form_issue = "Back error"
        save_bad_form(img, form_issue, attempt_count)
        bad_form_detected = True

    #Check going DOWN
    if direction == 0:
        
        #Start timer
        if not timer_started and mqtt_client and elbow <= 90:
            timer_started = True
            timer_start_time = current_time
            direction = 1
            mqtt_client.publish("pushup/status", "Start", qos=2)
            mqtt_client.publish("pushup/direction", "up", qos=2)
            print("Timer started! 60 seconds countdown begins.")
            
        #User reach bottom and elbow <= 90
        if timer_started and at_bottom == True and elbow <= 90:
            direction = 1
            mqtt_client.publish("pushup/direction", "up", qos=2)
            at_bottom = False
            
        #User start going up before reach bottom and elbow <= 90
        if abnormal:
            print(f"DOWN Abnormal: {abnormal}")
            abnormal = False
            direction = 1
            bad_form_detected = True
            mqtt_client.publish("pushup/direction", "up", qos=2) #Set direction to UP
            
            if current_attempt_saved == False:
                current_attempt_saved = True
                form_issue = detect_form_issues(elbow, shoulder, hip)
                save_bad_form(img, form_issue, attempt_count)
            
        return

    #Check going UP
    if direction == 1:
        #print(f"In UP Block abnormal posture: {abnormal}, current direction: {direction}, bad form detected: {bad_form_detected}")
        
        if at_top == True:
            
            print(f"Elbow: {elbow} and bad form detected: {bad_form_detected}")
            
            #Bad form detected during attempt
            if bad_form_detected:
                subprocess.call(['espeak', 'No Count'])
                print(f"No Count")
                direction = 0
                at_top = False
                current_attempt_saved = False
                bad_form_detected = False
                mqtt_client.publish("pushup/direction", "down", qos=2)
                return   
            
            #Reached Top with elbow > 145 and Proper form
            if elbow > 145 and not bad_form_detected:
                count += 1
                subprocess.call(['espeak', str(count)])
                mqtt_client.publish("pushup/direction", "down", qos=2)
                mqtt_client.publish("pushup/status", "Push up counted", qos=2)
                print(f"Count: {count}")
                direction = 0
                at_top = False
                current_attempt_saved = False
                bad_form_detected = False
                
                return    

        #Go down before reaching top and elbow < 145
        if abnormal:
            print(f"UP Abnormal: {abnormal}")
            direction = 0
            at_top = False
            current_attempt_saved = False
            bad_form_detected = False
            subprocess.call(['espeak', 'No Count'])
            print(f"No Count")
            mqtt_client.publish("pushup/direction", "down", qos=2)
            abnormal = False
            if current_attempt_saved == False:
                #current_attempt_saved = True
                form_issue = detect_form_issues(elbow, shoulder, hip)
                save_bad_form(img, form_issue, attempt_count)
            
            return
        
def check_valid_pose(lmList):
    """Checks if a valid person pose is detected."""
    valid_pose = False
    if len(lmList) >= 25:  # Make sure we have enough landmarks
        key_points = [11, 13, 15, 23, 25]  # Shoulder, elbow, wrist, hip, knee
        if all(point < len(lmList) for point in key_points):
            valid_pose = True
    return valid_pose


def check_ready_position(elbow, shoulder, hip):
    """Checks if person is in the UP position and ready to start counting."""
    global ready_hold_time, counting, mqtt_client, attempt_count

    in_up_position = (elbow > 145 and shoulder > 40 and hip > 145)
        
    if in_up_position:
        # Start or continue the ready timer
        if ready_hold_time is None:
            ready_hold_time = time.time()

        # If held for 1.5 seconds, start counting
        elif time.time() - ready_hold_time > 1.5 and not counting:
            print("You may start!")
            subprocess.call(['espeak', 'You May Start'])
            # Publish MQTT message when user is in position
            if mqtt_client:
                mqtt_client.publish("pushup/status", "User in position", qos=2)
                print("Published: User in position")

            counting = True
            return True  # Return ready_hold_time, counting=True
    else:
        ready_hold_time = None
        print("Get in UP Position")
    
    return False
    
#Check if user exist
def check_user(lmList):
    """Checks if a valid person pose is detected."""
    global last_status, mqtt_client, timer_started, timer_start_time, counting, count, direction, bad_form_images, attempt_count, ready_hold_time, current_attempt_saved, at_top, bad_form_detected, abnormal

    valid_user = False
    if len(lmList) >= 25:  # Make sure we have enough landmarks
        key_points = [11, 13, 15, 23, 25]  # Shoulder, elbow, wrist, hip, knee
        if all(point < len(lmList) for point in key_points):
            valid_user = True   

    # Track status change
    current_status = "User detected" if valid_user else "No user detected"
    status_changed = (last_status is None or current_status != last_status)

    # Only publish when status actually changes
    if mqtt_client and status_changed:
        # Clear any queued messages by sending with higher QoS
        mqtt_client.publish("pushup/status", current_status, qos=2)
        print(f"Status CHANGED to: {current_status}")

    if not valid_user:
        
        mqtt_client.publish("pushup/status", "End", qos=2)
        
        #Send to firebase
        if bad_form_images:
            session_stats = {
                "timestamp": time.time(),
                "total_pushups": count,
                "total_attempts": attempt_count,
                "success_rate": (count / max(1, attempt_count)) * 100,
                "session_duration": 60  # seconds
            }    
            
            upload_results = firestore_mgr.send_to_firebase(
                bad_form_images=bad_form_images,
                session_stats=session_stats
            )
            print(f"Upload results: {upload_results['images_uploaded']} images uploaded")
        
        # Reset timer and session variables
        timer_started = False
        timer_start_time = None
        counting = False
        count = 0
        attempt_count = 0
        direction = 0
        bad_form_images = []
        ready_hold_time = None
        current_attempt_saved = False
        at_top = False
        bad_form_detected = False
        abnormal = False

    last_status = current_status
    return valid_user
    
    
def check_60s(current_time):
    """Check if 60 seconds have elapsed and handle session end if needed."""
    global timer_started, timer_start_time, bad_form_images, count, attempt_count
    global ready_hold_time, current_attempt_saved, mqtt_client, counting, direction
    global firestore_mgr

    if timer_started:
        elapsed_time = current_time - timer_start_time
        remaining_time = max(0, 60 - elapsed_time)
        #print(f"Remaining time: {remaining_time}")

        if remaining_time <= 0:
            subprocess.call(['espeak', 'Times Up'])
            mqtt_client.publish("pushup/status", "End", qos=2)
            
            # Prepare session stats
            session_stats = {
                "timestamp": time.time(),
                "total_pushups": count,
                "total_attempts": attempt_count,
                "success_rate": (count / max(1, attempt_count)) * 100,
                "session_duration": 60  # seconds
            }    

            # Send bad form images to Firebase
            if bad_form_images:
                upload_results = firestore_mgr.send_to_firebase(
                    bad_form_images=bad_form_images,
                    session_stats=session_stats
                )
                print(f"Upload results: {upload_results['images_uploaded']} images uploaded")

            # Reset timer and session variables
            timer_started = False
            timer_start_time = None
            counting = False
            count = 0
            attempt_count = 0
            direction = 0
            bad_form_images = []
            ready_hold_time = None
            current_attempt_saved = False
            at_top = False
            bad_form_detected = False
            abnormal = False
        return
        
        
def calculate_fps(prev_time):
    """Calculate frames per second."""
    cur_time = time.time()
    fps = 1 / (cur_time - prev_time)
    print(f"FPS: {fps:.2f}")
    return cur_time, fps
    

def main():
    global count, direction, attempt_count, bad_form_images, current_attempt_saved
    global counting, ready_hold_time, last_upload_time, last_status
    global timer_started, timer_start_time, mqtt_client, firestore_mgr

    # Initialize variables
    count = 0
    direction = 0
    attempt_count = 0
    bad_form_images = []
    current_attempt_saved = False
    counting = False
    ready_hold_time = None
    last_upload_time = None
    last_status = None
    timer_started = False
    timer_start_time = None
    abnormal = False
    bad_form_detected = False
    at_top = False

    #Setup
    cap = setup_camera()
    detector = pm.poseDetector()
    setup_mqtt() #Set up mqtt
    firestore_mgr = FirestoreManager(credential_path="firebase-credentials.json") # Initialize Firestore manager

    # Ensure bad_form directory exists
    os.makedirs("bad_form", exist_ok=True)

    prev_time = time.time()  # Initialize FPS timer
    
    while cap.isOpened():
        ret, img = cap.read()
        if not ret:
            break

        current_time = time.time()
        img = detector.findPose(img, False)
        lmList = detector.findPosition(img, False)

        valid_user = check_user(lmList) #Check if user exist

        if not valid_user:
            continue

        # Get key angles
        elbow = detector.findAngle(img, 11, 13, 15)
        shoulder = detector.findAngle(img, 13, 11, 23)
        hip = detector.findAngle(img, 11, 23, 25)

        # Check if person is in UP position (starting position)
        if valid_user and not counting:
            position_ready = check_ready_position(elbow, shoulder, hip)

        # If counting is active, perform pushup detection
        if counting:
            update_count(elbow, shoulder, hip, img.copy())
            check_60s(current_time)
            
        # FPS Calculation
        #prev_time, fps = calculate_fps(prev_time)
        
        cv2.imshow('Pushup Counter', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
