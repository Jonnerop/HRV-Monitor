from machine import Pin, ADC, I2C, PWM
from fifo import Fifo
from piotimer import Piotimer
import micropython
from time import ticks_ms, sleep, localtime
import time
from ssd1306 import SSD1306_I2C
import framebuf, array, utime, json
import math
from kubios_class_2 import Kubios
micropython.alloc_emergency_exception_buf(200)

# Class to handle ADC operations using interrupts
class Isr_adc:
    def __init__(self):
        self.adc = ADC(26)
        self.fifo = Fifo(500, typecode = 'i')

    def handler(self, timer_id):
        self.fifo.put(self.adc.read_u16())

isr_adc = Isr_adc()

# UI elements
option = 0
oled_width = 128
oled_height = 64
menu_options = []
fb = framebuf.FrameBuffer(bytearray(oled_width * oled_height // 8), oled_width, oled_height, framebuf.MONO_VLSB)

# LED setup
led_pins = [20, 21, 22]
leds = [PWM(Pin(pin, Pin.OUT)) for pin in led_pins]
for led in leds:
    led.freq(500) # PWM frequency fo the LEDs
    
# Funtion for displaying the starting screen
def introduction(fb):
    fb.fill(0)
    fb.rect(0, 0, oled_width, oled_height, 1) # Draw a rectangle border around the edge
    fb.text("Cardio", 47, 8, 1)
    fb.text("Pulse PRO", 47, 20, 1)
    vertical_offset = 5 # Set a vertical offset for adjusting the waveform position
    
    # Define points for a sample waveform to be displayed on the screen
    points = [
        (0, 32 + vertical_offset), (20, 32 + vertical_offset), (25, 22 + vertical_offset), 
        (30, 42 + vertical_offset), (35, 12 + vertical_offset), (40, 52 + vertical_offset), 
        (45, 32 + vertical_offset), (128, 32 + vertical_offset)
    ]
    
    # Draw lines between consecutive points in the list to create the waveform
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        fb.line(x1, y1, x2, y2, 1)
    
    display.oled.blit(fb, 0, 0)
    display.oled.show()

# Function for LED blink when peak is found
def blink_led():
    for led in leds:
        led.duty_u16(500) # Set the brightness of the LEDs
    time.sleep_ms(200)
    for led in leds:
        led.duty_u16(0)

# Class to handle rotary encoder input
class Encoder:
    def __init__(self, rotary_a, rotary_b, rotary_push):
        self.rot_a = Pin(rotary_a, mode = Pin.IN, pull = Pin.PULL_UP)
        self.rot_b = Pin(rotary_b, mode = Pin.IN, pull = Pin.PULL_UP)
        self.rot_push = Pin(rotary_push,  mode = Pin.IN, pull = Pin.PULL_UP)
        self.rot_a.irq(handler = self.rotary_handler, trigger = Pin.IRQ_RISING, hard = True)
        self.rot_push.irq(handler = self.rotary_push, trigger = Pin.IRQ_RISING, hard = True)
        self.turn_fifo = Fifo(500, typecode = 'i')
        self.push_tick = 0

    def rotary_push(self, pin):
        # Debounce and handle button push
        current_tick = time.ticks_ms()
        debounce_interval = 300
        if current_tick - self.push_tick > debounce_interval:
            self.turn_fifo.put(0)
            self.push_tick = current_tick

    def rotary_handler(self, pin):
        # Determine rotation direction
        if self.rot_b.value():
            self.turn_fifo.put(-1)
        else:
            self.turn_fifo.put(1)

# Class for OLED display operations
class Display:
    def __init__(self):
        self.I2C = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
        self.oled = SSD1306_I2C(oled_width, oled_height, self.I2C)

    def show_menu(self, option):
        # Show menu options on the screen and highlight the current selection
        self.oled.fill(0)
        start_y = 0
        line_height = 14 # The amount pixels reserved for each line of text
        for i, choice in enumerate(menu_options):
            if i == option:
                text = f">{choice}"
            else:
                text = f" {choice} "
            self.oled.text(text, 0, start_y + line_height * i, 1)
        self.oled.show()

    def display_message(self, message):
        # Display a single message on the display
        self.oled.fill(0)
        self.oled.text(message, 0, 30, 1)
        self.oled.show()
        
    def add(self, message):
        # Add additional messages to the display
        self.oled.text(message, 0, 50, 1)
        self.oled.show()

def basic_hr(mode):
    # Basic heart rate measurement routine
    display.display_message('Press to start')
    while encoder.rot_push.value() == 1:
        pass
    
    sleep(0.5)
    # A periodic timer to trigger ADC reads
    timer = Piotimer(mode=Piotimer.PERIODIC, freq=250, callback=isr_adc.handler)
    display.oled.fill(0)
    number = 0
    result = 0
    counting = False
    sum_result = 0
    previous_result = 75
    times_ms = [0]
    average_lastfive = 0
    x_coord = 0
    y_coord = 64

    while True:
        # Process ADC data from FIFO
        if isr_adc.fifo.has_data():
            sample = isr_adc.fifo.get() 
            number += 1
            
            if encoder.rot_push.value() == 0 and mode == 1:
                # Measure and calculate the average HR
                average = sum_result / result
                print('Average was ', round(average), ' bpm')
                timer.deinit()
                average = sum_result / result
                display.display_message(f'Average: {average:.0f} bpm')
                display.add('Press for menu')
                sleep(0.5)
                while encoder.rot_push.value() == 1:
                    pass
                sleep(0.2)
                return
            
            if mode == 2 and number == 7500: # 250 * 30, 30 seconds
                # Calculate heart rate variability metrics
                timer.deinit()
                date = get_date()
                ppi_values = times_ms[1:]
                average_ppi = calc_mean_ppi(ppi_values)
                mean_hr = calc_mean_hr(average_ppi)
                sdnn = calc_sdnn(ppi_values, average_ppi)
                rmssd = calc_rmssd(ppi_values)
                display_hrv_metrics(display.oled, date, average_ppi, mean_hr, sdnn, rmssd)
                stats = {
                    'date': date,
                    'average_ppi': average_ppi,
                    'mean_hr': mean_hr,
                    'sdnn': sdnn,
                    'rmssd': rmssd,
                    'sns': None,
                    'pns': None
                    }

                while encoder.rot_push.value() == 1:
                    pass
                sleep(0.2)
                add_history(stats)
                return
            
            if mode == 3 and number == 7500: # 250 * 30, 30 seconds
                # Fetch advanced HRV data from Kubios
                timer.deinit()
                display.display_message('Fetching Kubios data')
                ppi_values = times_ms[1:]
                average_ppi = calc_mean_ppi(ppi_values)
                stats = kubios.json(ppi_values)
                
                if stats is None:
                    display.display_message('Fetching failed')
                    display.add('Press for menu')
                elif stats is not None:
                    date = stats['date'].split('-')
                    hours = int(date[2][3:5]) + 3 # Adjust hour for time zone difference
                    if hours > 23:
                        hours -= 24
                    # Reformat the date and time into 'DD.MM.YYYY HH:MM'
                    stats['date'] = f"{date[2][:2]}.{date[1]}.{date[0]} {hours}:{date[2][6:8]}"
                    stats['average_ppi'] = average_ppi
                    display_hrv_metrics(display.oled, stats['date'], stats['average_ppi'], int(stats['mean_hr']), int(stats['sdnn']), int(stats['rmssd']), float(f"{stats['sns']:.3f}"), float(f"{stats['pns']:.3f}"))
                    while encoder.rot_push.value() == 1:
                        pass
                    add_history(stats)
                    display.display_message('Sending MQTT')
                    if kubios.publish(stats):
                        display.display_message('MQTT sent')
                        sleep(2)
                        return
                    else:
                        display.display_message('MQTT failed')
                        sleep(2)
                        return

                while encoder.rot_push.value() == 1:
                    pass
                sleep(0.2)
                return
            
            # Periodic display updates in heart rate mode
            if number % 1250 == 0 and result > 0 and mode == 1: # 250 * 5, 5 seconds
                average = sum_result / result
                display.display_message(f'{average:.0f} bpm')
                display.add('Press to stop')
                
            # Initialize thresholds for heart beat detection  
            if number == 1:
                previous_peak = number
                threshold = 0.95 * sample
                display.display_message('Measuring...')
             
             # Adjust threshold based on min/max every 250 samples, 1 second
            if number % 250 == 0:
                min_value = min(isr_adc.fifo.data)
                max_value = max(isr_adc.fifo.data)
                threshold = min_value + (0.9 * (max_value - min_value))
            
            # Detect heart beats
            if sample > threshold:
                counting = True
                current_peak = number
            
            # Check if the current sample is below threshold and counting is active
            elif sample < threshold and counting:
                interval = current_peak - previous_peak # Calculate the time interval between the current peak and the previous peak
                previous_peak = current_peak
                if interval > 0:
                    hr = round(60 / (interval / 250)) # Calculate heart rate based on the interval with sample rate of 250Hz
                    check = hr - previous_result
                    if 30 <= hr <= 230 and -20 < check < 20: # Check if the calculated heart rate is within the acceptable range
                        times_ms.append(4 * interval)
                        sum_result += hr # Add the valid heart rate to the sum for averaging
                        result += 1
                        if result == 3:
                            previous_result = sum_result / result
                        print(f'HR: {hr} bpm')
                        blink_led() # Trigger an LED blink as a physical indicator of heart rate detection
                        counting = False
            
            if mode == 2 or mode == 3 and number >= 245:
                average_lastfive += sample
            
            if number == 250: # 250, 1 seconds
                display.oled.fill(0)
            
            # Updates and plots a normalized signal on the OLED display when conditions are met
            if number % 5 == 0 and (mode == 2 or mode == 3) and number >= 250:
                average_lastfive /= 5
                area = max_value - min_value
                lastfive_area = (average_lastfive - min_value) / area
                y_coord = round((1 - lastfive_area) * 45) + 10 # Set Y-coordinate on OLED based on adjusted value
                display.oled.pixel(x_coord, y_coord, 1)
                x_coord += 1
                if x_coord == 127: # Reset X to 0 and clear the display if at the end
                    x_coord = 0
                    display.oled.fill(0)

                average_lastfive = 0
            
            if number % 25 == 0 and (mode == 2 or mode == 3):
                display.oled.show()
                    
def calc_mean_ppi(ppi_values):
    # Calculate the mean of PPI (Peak-to-Peak Interval) values
    if not ppi_values:
        raise ValueError("List of PPI values is empty.")
    total_ppi = sum(ppi_values)
    average_ppi = total_ppi / len(ppi_values)
    return round(average_ppi)

def calc_mean_hr(average_ppi):
    # Calculate mean heart rate from average PPI
    if average_ppi <= 0:
        raise ValueError("Average PPI must be greater than zero to calculate heart rate.")
    ms_per_minute = 60000
    mean_hr = ms_per_minute / average_ppi
    return round(mean_hr)

def calc_rmssd(ppi_values):
    # Calculate successive differences between adjacent PPI values
    if len(ppi_values) < 2:
        raise ValueError("At least two PPI values are required to calculate RMSSD.")
    differences = [ppi_values[i+1] - ppi_values[i] for i in range(len(ppi_values) - 1)]
    squared_differences = [diff ** 2 for diff in differences]
    mean_squared_differences = sum(squared_differences) / len(squared_differences)
    rmssd = math.sqrt(mean_squared_differences)
    return round(rmssd)

def calc_sdnn(ppi_values, average_ppi):
    # Calculate SDNN (Standard Deviation of NN intervals)
    if len(ppi_values) < 2:
        raise ValueError("At least two PPI values are required to calculate SDNN.")
    variance = sum((ppi_value - average_ppi) ** 2 for ppi_value in ppi_values) / (len(ppi_values) - 1)
    sdnn = math.sqrt(variance) 
    return round(sdnn)

def get_date():
    # Format the current date and time for display
    date = utime.localtime(utime.time())
    month = date[1]
    day = date[2]
    if date[2] < 10:
        day = f'0{date[2]}'
    if date[1] < 10:
        month = f'0{date[1]}'
    date = (f'{str(day)}.{str(month)}.{str(date[0])} {str(date[3])}:{str(date[4])}')
    return date

def display_hrv_metrics(oled, date, average_ppi, mean_hr, sdnn, rmssd, sns=None, pns=None):
    # Display heart rate variability metrics on the OLED
    oled.fill(0)
    date_time_string = date
    oled.text(date_time_string, 0, 0)

    oled.text(f'MEAN PPI: {average_ppi}ms', 0, 9)
    oled.text(f'MEAN HR: {mean_hr:.0f}bpm', 0, 18)
    oled.text(f'SDNN: {sdnn:.0f}ms', 0, 27)
    oled.text(f'RMSSD: {rmssd:.0f}ms', 0, 36)
    if sns is not None and pns is not None:
        oled.text(f'SNS: {sns:.3f}', 0, 45)
        oled.text(f'PNS: {pns:.3f}', 0, 54)
    oled.show()

def open_history():
    # Function to read the history of HRV measurements from a file and display it
    try:
        # Try to open history file in read mode
        file = open('history.txt', 'r')
        file.read() # Read contents to ensure it's not empty
        file.close()
    except OSError:
        # If file does not exist create it and close it
        file = open('history.txt', 'w')
        file.close()
    
    # Reopen file with read to load history data
    file = open('history.txt', 'r')
    data = file.read()
    history = data.split(';') # Split data into individual entries
    history = history[:-1] # Remove the last empty entry from split
    for i in range (len(history)):
        history[i] = json.loads(history[i]) # Convert string back to dictionary
    
    file.close()
    global menu_options
    
    # Update UI to display history entries or show a message if no history is found
    if len(history) == 0:
        display.display_message('No history found')
        sleep(2)
        return
    
    else:
        print(len(history))
        print(history)
        menu_options = []
        for stat in history:
            text = stat['date'].split(' ')
            text = f'{text[0][:-4]} {text[1]}'
            menu_options.append(text)
        menu_options.append('Back to menu')
    
    option = 0
    display.show_menu(option)
    
    while True:
        # Navigate through history entries using the rotary encoder
        if encoder.turn_fifo.has_data():
            increment = encoder.turn_fifo.get()
            new_option = option - increment  
            if 0 <= new_option < len(menu_options):
                option = new_option
        display.show_menu(option)
        
        if encoder.rot_push.value() == 0:
            # Select a history entry and display its details
            if not option == len(history):
                display_hrv_metrics(display.oled, history[option]['date'], history[option]['average_ppi'], history[option]['mean_hr'], history[option]['sdnn'], history[option]['rmssd'], history[option]['sns'], history[option]['pns'])
                sleep(0.2)
                while encoder.rot_push.value() == 1:
                    pass
                sleep(0.2)
            else:
                sleep(0.2)
                break
        
def add_history(stats):
    # Function to add a new HRV measurement to the history file
    try:
        file = open('history.txt', 'a')
        empty = False
        file.close()
    except OSError:
        # Create file if it does not exist
        file = open('history.txt', 'w')
        empty = True
        file.close()
    
    if not empty:
        file = open('history.txt', 'r')
        lines = file.read()
        history = lines.split(';')
        file.close()
        history = history[:-1] # Remove last empty entry
    else:
        history = []
    
    # Maintain a limit of 4 history entries and remove the oldest if limit is exceeded
    if len(history) == 4:
        history = history[1:]
    
    # Append the new stats as a JSON string
    history.append(json.dumps(stats))
    
    # Write the updated history back to the file
    with open('history.txt', 'w') as file:
        pass
    
    with open('history.txt', 'a') as file:
        for data in history:
            file.write(data)
            file.write(';')
            
    display.display_message('Added to history')
    file.close()
    sleep(2)
    return

#Main

# Objects
encoder = Encoder(10, 11, 12)
display = Display()
kubios = Kubios()

# Start by opening introduction screen
introduction(fb)
while encoder.rot_push.value() == 1:
    pass
sleep(0.2)
display.show_menu(option)

# Main program loop
while True:
    # Reset the menu items and handle rotary input
    menu_options = ["1. Measure HR", "2. Analysis", "3. Kubios", "4. History"]
    
    if encoder.turn_fifo.has_data():
        increment = encoder.turn_fifo.get() # Get the amount of encoder turns
        new_option = option - increment # Calculate the new menu option index based on the encoder's increment
        if 0 <= new_option < len(menu_options):
            option = new_option   
    display.show_menu(option)
    
    # Handle selections and navigate through options
    if encoder.rot_push.value() == 0:
        selected_message = f"{menu_options[option]}"
        display.display_message(selected_message)
        sleep(1.5)
        if option == 0:
            basic_hr(1)

        elif option == 1:
            basic_hr(2)

        elif option == 2:
            basic_hr(3)

        elif option == 3:
            open_history()