import time
import grovepi

# Connect the Grove Buzzer to digital port D4
buzzer = 4
grovepi.pinMode(buzzer, "OUTPUT")

# Buzz once
def buzz_success():
    """Quick buzz for a successful push-up."""
    start_time = time.monotonic()
    
    grovepi.digitalWrite(buzzer, 1)
    print("buzz_success(): Buzzer On")
    
    while time.monotonic() - start_time < 0.1:
        pass
        
    grovepi.digitalWrite(buzzer, 0)
    print("buzz_success(): Buzzer Off")

# Buzz twice consecutively
def buzz_failure():
    """Double quick buzz for an unsuccessful push-up."""
    for _ in range(2):
        start_time = time.monotonic()
        
        grovepi.digitalWrite(buzzer, 1)
        
        while time.monotonic() - start_time < 0.1:
            pass
            
        grovepi.digitalWrite(buzzer, 0)

# Long Buzz of 0.8 seconds
def buzz_complete():
    """Long buzz for the end of the session."""
    start_time = time.monotonic()
    
    grovepi.digitalWrite(buzzer, 1)

    while time.monotonic() - start_time < 0.8:
        pass
        
    grovepi.digitalWrite(buzzer, 0)
    
def buzz_off():
    grovepi.digitalWrite(buzzer, 0)
