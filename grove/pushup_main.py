"""Main File for At Home ELISS Push-up Machine
   MQTT Subscriber (Raspberry Pi 3 B+ [Bullseye OS] & GrovePi+)
   Sensors: Ultrasonic Ranger, Buzzer, LCD RGB Backlight, Red LED, Green LED"""

"""Instructions for setting up Pi 3 & GrovePi+ (to be moved to GitHub readme.md)
   Pi 3 B+ to be imaged with raspios_oldstable_armhf-2023-05-03
   https://downloads.raspberrypi.com/raspios_oldstable_armhf/images/
   Due to GrovePi+ constraints, imaged username must be 'pi'.
   
   Pi 3 B+ to be set up with the following commands:
   sudo apt update
   curl -kL dexterindustries.com/update_grovepi | bash
   https://www.dexterindustries.com/GrovePi/get-started-with-the-grovepi/setting-software/
"""

import paho.mqtt.client as mqtt
import time
import buzzer as buzzer
import ranger_280325 as ranger
import backlight as backlight
import led as led

# Broker's (PI) static IP
BROKER = "172.20.10.4"
TOPIC = "pushup/status"
DIRECTION_TOPIC = "pushup/direction"

current_direction = None

# Function to connect to MQTT topic
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    
    # Clear retained message
    client.publish(TOPIC, payload="", retain=True)
    
    client.subscribe(TOPIC)
    client.subscribe(DIRECTION_TOPIC)
    
# Function to receive message from MQTT publisher
def on_message(client, userdata, message):
    payload = message.payload.decode()
    topic = message.topic
    global current_direction
    
    print(f"\nReceived: {payload}")
    
    if topic == DIRECTION_TOPIC:
        ranger.current_direction_subscribe(payload)
    
    if payload == "No user detected":
        backlight.display_nouserdetected()
        print(f"{payload}: Backlight Display No User Detected\n")
        
    elif payload == "User detected":
        backlight.display_default()
        print(f"{payload}: Backlight Display Default\n")
        
    elif payload == "User in position":
        backlight.display_ready()
        print(f"{payload}: Backlight Display Ready")
        ranger.record_baseline_top()
        print(f"{payload}: Baseline Top Recorded\n")
        
    elif payload == "Start":
        backlight.start_timer()
        print(f"{payload}: Timer Started")
        ranger.record_baseline_bottom()
        print(f"{payload}: Baseline Bottom Recorded")
        ranger.start_pushup_monitoring()
        print(f"{payload}: Start pushup monitoring\n")
        
    elif payload == "Push up counted":
        backlight.count_pushup(1)
        print(f"{payload}: Push up counted")
        buzzer.buzz_success()
        print(f"{payload}: Buzz Success")
        buzzer.buzz_off()
        led.led_success()
        print(f"{payload}: LED Success\n")
        
    elif payload == "Straighten Back":
        backlight.count_pushup(0)
        print(f"{payload}: Push up not counted")
        led.led_failure()
        print(f"{payload}: LED Failure\n")
        
    elif payload == "Straighten Arms":
        backlight.count_pushup(2)
        print(f"{payload}: Push up not counted")
        led.led_failure()
        print(f"{payload}: LED Failure\n")
        
    elif payload == "End":
        ranger.stop_pushup_monitoring()
        print(f"{payload}: Stop pushup monitoring")
        buzzer.buzz_off()
        print(f"{payload}: Buzz End\n")


# MQTT Client connectivity        
client = mqtt.Client("Pi3Subscriber")
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, 1883)

client.loop_forever()
