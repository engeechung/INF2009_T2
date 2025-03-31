import time, sys, threading

# Global variables for timer and count
time_remaining = 60
pushup_count = 0
is_counting_down = False
special_message = None  # Holds (message1, message2)
special_message_active = False
display_lock = threading.Lock() # Prevents display conflicts

if sys.platform == 'uwp':
    import winrt_smbus as smbus
    bus = smbus.SMBus(1)
else:
    import smbus
    import RPi.GPIO as GPIO
    rev = GPIO.RPI_REVISION
    if rev == 2 or rev == 3:
        bus = smbus.SMBus(1)
    else:
        bus = smbus.SMBus(0)

# I2C addresses
DISPLAY_RGB_ADDR = 0x62
DISPLAY_TEXT_ADDR = 0x3e

# Set backlight color
def setRGB(r, g, b):
    bus.write_byte_data(DISPLAY_RGB_ADDR, 0, 0)
    bus.write_byte_data(DISPLAY_RGB_ADDR, 1, 0)
    bus.write_byte_data(DISPLAY_RGB_ADDR, 0x08, 0xaa)
    bus.write_byte_data(DISPLAY_RGB_ADDR, 4, r)
    bus.write_byte_data(DISPLAY_RGB_ADDR, 3, g)
    bus.write_byte_data(DISPLAY_RGB_ADDR, 2, b)

# Send command to display
def textCommand(cmd):
    bus.write_byte_data(DISPLAY_TEXT_ADDR, 0x80, cmd)

# Display text
def setText(text):
    textCommand(0x01)  # Clear display
    time.sleep(0.05)
    textCommand(0x08 | 0x04)  # Display ON, no cursor
    textCommand(0x28)  # 2-line display mode
    time.sleep(0.05)
    count, row = 0, 0
    for c in text:
        if c == '\n' or count == 16:
            count, row = 0, row + 1
            if row == 2:
                break
            textCommand(0xc0)  # Move to second line
            if c == '\n':
                continue
        count += 1
        bus.write_byte_data(DISPLAY_TEXT_ADDR, 0x40, ord(c))
        
# Function to reset and turn off the display
def reset_display():
    global is_counting_down, time_remaining
    
    is_counting_down = False
    time_remaining = 0
    
    setRGB(0, 0, 0)
    textCommand(0x01)

# Function to display the default message
def display_default():
    setRGB(200, 160, 30)
    setText("Enter Push-up\nPosition.")
    
# Function to display the no-user detected
def display_nouserdetected():
    setRGB(250, 20, 20)
    setText("No user\ndetected!")

# Function to display the ready message
def display_ready():
    global pushup_count, time_remaining
    setRGB(0, 255, 0)
    text = f"Time:{time_remaining}|\nCount:{pushup_count}|Ready"
    setText(text)

# Function to start countdown
def start_timer():
    global time_remaining, is_counting_down, pushup_count
    is_counting_down = True
    message1 = ""
    message2 = ""

    def timer_loop():
        global time_remaining, special_message, special_message_active
        while time_remaining > 0:
            with display_lock:
                if special_message_active and special_message:
                    message1, message2 = special_message
                    text = f"Time:{time_remaining}|{message1}\nCount:{pushup_count}|{message2}"
                else:
                    text = f"Time:{time_remaining}|\nCount:{pushup_count}|"
            setText(text)
            time.sleep(1)
            time_remaining -= 1
        is_counting_down = False

    # Run timer in a separate thread
    timer_thread = threading.Thread(target=timer_loop)
    timer_thread.start()

    # Final message + Reset values when timer ends
    if time_remaining == 0:
        message1 = "End of"
        message2 = "Time!"
        text = f"Time: {time_remaining} | {message1}\nCount: {pushup_count} | {message2}"
        setText(text)

    time_remaining = 60
    pushup_count = 0
    is_counting_down = False
    special_message = None
    special_message_active = False

# Function to update push-up count
def count_pushup(count):
    global pushup_count, special_message, special_message_active
    
    if count == 1:
        pushup_count += 1
        message1 = ""
        message2 = "Good!"
    elif count == 0:
        message1 = "Back Not"
        message2 = "Straight"
    elif count == 2:
        message1 = "Arms Not"
        message2 = "Straight"
        
    # Update special message
    special_message = (message1, message2)
    special_message_active = True
    
    # Ensure display updates don't clash with timer thread
    with display_lock:
        text = f"Time:{time_remaining}|{message1}\nCount:{pushup_count}|{message2}"
        setText(text)
    
    # Ensures display updates instantly
    time.sleep(0.01)
