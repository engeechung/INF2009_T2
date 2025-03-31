import time
from grovepi import *

# Define LED ports
green_led = 2  # Green LED (D2)
red_led = 3    # Red LED (D3)

# Set pin modes
pinMode(green_led, "OUTPUT")
pinMode(red_led, "OUTPUT")

# Light up green LED
def led_success():
    """Lights up the success LED briefly"""
    start_time = time.monotonic()
    digitalWrite(green_led, 1)
    #print("Debug: Green LED (D2) On")
    
    while time.monotonic() - start_time < 0.5:
        pass
        
    digitalWrite(green_led, 0)
    #print("Debug: Green LED (D2) Off")

# Light up red LED
def led_failure():
    """Lights up the failure LED briefly"""
    start_time = time.monotonic()
    
    digitalWrite(red_led, 1)
    #print("Debug: Red LED (D3) On")
    
    while time.monotonic() - start_time < 0.5:
        pass
        
    digitalWrite(red_led, 0)
    #print("Debug: Red LED (D3) Off")

# Ensure LEDs are off before exiting
digitalWrite(green_led, 0)
digitalWrite(red_led, 0)
