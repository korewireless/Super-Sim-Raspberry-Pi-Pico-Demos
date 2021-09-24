# Version 1.0.0
# Copyright © 2021, Twilio
# Licence: MIT

from machine import UART, Pin, I2C
from utime import ticks_ms, sleep
import json

class MCP9808:
    """
    A simple driver for the I2C-connected MCP9808 temperature sensor.
    This release supports MicroPython.
    """

    # *********** PRIVATE PROPERTIES **********

    i2c = None
    address = 0x18

    # *********** CONSTRUCTOR **********

    def __init__(self, i2c, i2c_address=0x18):
        assert 0x00 <= i2c_address < 0x80, "ERROR - Invalid I2C address in MCP9808()"
        self.i2c = i2c
        self.address = i2c_address

    # *********** PUBLIC METHODS **********

    def read_temp(self):
        # Read sensor and return its value in degrees celsius.
        temp_bytes = self.i2c.readfrom_mem(self.address, 0x05, 2)
        # Scale and convert to signed value.
        temp_raw = (temp_bytes[0] << 8) | temp_bytes[1]
        temp_cel = (temp_raw & 0x0FFF) / 16.0
        if temp_raw & 0x1000: temp_cel -= 256.0
        return temp_cel

class HT16K33:
    """
    A simple, generic driver for the I2C-connected Holtek HT16K33 controller chip.
    This release supports MicroPython and CircuitPython

    Version:    3.0.2
    Bus:        I2C
    Author:     Tony Smith (@smittytone)
    License:    MIT
    Copyright:  2020
    """

    # *********** CONSTANTS **********

    HT16K33_GENERIC_DISPLAY_ON = 0x81
    HT16K33_GENERIC_DISPLAY_OFF = 0x80
    HT16K33_GENERIC_SYSTEM_ON = 0x21
    HT16K33_GENERIC_SYSTEM_OFF = 0x20
    HT16K33_GENERIC_DISPLAY_ADDRESS = 0x00
    HT16K33_GENERIC_CMD_BRIGHTNESS = 0xE0
    HT16K33_GENERIC_CMD_BLINK = 0x81

    # *********** PRIVATE PROPERTIES **********

    i2c = None
    address = 0
    brightness = 15
    flash_rate = 0

    # *********** CONSTRUCTOR **********

    def __init__(self, i2c, i2c_address):
        assert 0x00 <= i2c_address < 0x80, "ERROR - Invalid I2C address in HT16K33()"
        self.i2c = i2c
        self.address = i2c_address
        self.power_on()

    # *********** PUBLIC METHODS **********

    def set_blink_rate(self, rate=0):
        """
        Set the display's flash rate.

        Only four values (in Hz) are permitted: 0, 2, 1, and 0,5.

        Args:
            rate (int): The chosen flash rate. Default: 0Hz (no flash).
        """
        assert rate in (0, 0.5, 1, 2), "ERROR - Invalid blink rate set in set_blink_rate()"
        self.blink_rate = rate & 0x03
        self._write_cmd(self.HT16K33_GENERIC_CMD_BLINK | rate << 1)

    def set_brightness(self, brightness=15):
        """
        Set the display's brightness (ie. duty cycle).

        Brightness values range from 0 (dim, but not off) to 15 (max. brightness).

        Args:
            brightness (int): The chosen flash rate. Default: 15 (100%).
        """
        if brightness < 0 or brightness > 15: brightness = 15
        self.brightness = brightness
        self._write_cmd(self.HT16K33_GENERIC_CMD_BRIGHTNESS | brightness)

    def draw(self):
        """
        Writes the current display buffer to the display itself.

        Call this method after updating the buffer to update
        the LED itself.
        """
        self._render()

    def update(self):
        """
        Alternative for draw() for backwards compatibility
        """
        self._render()

    def clear(self):
        """
        Clear the buffer.

        Returns:
            The instance (self)
        """
        for i in range(0, len(self.buffer)): self.buffer[i] = 0x00
        return self

    def power_on(self):
        """
        Power on the controller and display.
        """
        self._write_cmd(self.HT16K33_GENERIC_SYSTEM_ON)
        self._write_cmd(self.HT16K33_GENERIC_DISPLAY_ON)

    def power_off(self):
        """
        Power on the controller and display.
        """
        self._write_cmd(self.HT16K33_GENERIC_DISPLAY_OFF)
        self._write_cmd(self.HT16K33_GENERIC_SYSTEM_OFF)

    # ********** PRIVATE METHODS **********

    def _render(self):
        """
        Write the display buffer out to I2C
        """
        buffer = bytearray(len(self.buffer) + 1)
        buffer[1:] = self.buffer
        buffer[0] = 0x00
        self.i2c.writeto(self.address, bytes(buffer))

    def _write_cmd(self, byte):
        """
        Writes a single command to the HT16K33. A private method.
        """
        self.i2c.writeto(self.address, bytes([byte]))

class HT16K33Segment(HT16K33):
    """
    Micro/Circuit Python class for the Adafruit 0.56-in 4-digit,
    7-segment LED matrix backpack and equivalent Featherwing.

    Version:    3.0.2
    Bus:        I2C
    Author:     Tony Smith (@smittytone)
    License:    MIT
    Copyright:  2020
    """

    # *********** CONSTANTS **********

    HT16K33_SEGMENT_COLON_ROW = 0x04
    HT16K33_SEGMENT_MINUS_CHAR = 0x10
    HT16K33_SEGMENT_DEGREE_CHAR = 0x11
    HT16K33_SEGMENT_SPACE_CHAR = 0x00

    # The positions of the segments within the buffer
    POS = (0, 2, 6, 8)

    # Bytearray of the key alphanumeric characters we can show:
    # 0-9, A-F, minus, degree
    CHARSET = b'\x3F\x06\x5B\x4F\x66\x6D\x7D\x07\x7F\x6F\x5F\x7C\x58\x5E\x7B\x71\x40\x63'

    # *********** CONSTRUCTOR **********

    def __init__(self, i2c, i2c_address=0x70):
        self.buffer = bytearray(16)
        super(HT16K33Segment, self).__init__(i2c, i2c_address)

    # *********** PUBLIC METHODS **********

    def set_colon(self, is_set=True):
        """
        Set or unset the display's central colon symbol.

        This method updates the display buffer, but does not send the buffer to the display itself.
        Call 'update()' to render the buffer on the display.

        Args:
            isSet (bool): Whether the colon is lit (True) or not (False). Default: True.

        Returns:
            The instance (self)
        """
        self.buffer[self.HT16K33_SEGMENT_COLON_ROW] = 0x02 if is_set is True else 0x00
        return self

    def set_glyph(self, glyph, digit=0, has_dot=False):
        """
        Present a user-defined character glyph at the specified digit.

        Glyph values are 8-bit integers representing a pattern of set LED segments.
        The value is calculated by setting the bit(s) representing the segment(s) you want illuminated.
        Bit-to-segment mapping runs clockwise from the top around the outside of the matrix; the inner segment is bit 6:

                0
                _
            5 |   | 1
              |   |
                - <----- 6
            4 |   | 2
              | _ |
                3

        This method updates the display buffer, but does not send the buffer to the display itself.
        Call 'update()' to render the buffer on the display.

        Args:
            glyph (int):   The glyph pattern.
            digit (int):   The digit to show the glyph. Default: 0 (leftmost digit).
            has_dot (bool): Whether the decimal point to the right of the digit should be lit. Default: False.

        Returns:
            The instance (self)
        """
        assert 0 <= digit < 4, "ERROR - Invalid digit (0-3) set in set_glyph()"
        assert 0 <= glyph < 0xFF, "ERROR - Invalid glyph (0x00-0xFF) set in set_glyph()"
        self.buffer[self.POS[digit]] = glyph
        if has_dot is True: self.buffer[self.POS[digit]] |= 0x80
        return self

    def set_number(self, number, digit=0, has_dot=False):
        """
        Present single decimal value (0-9) at the specified digit.

        This method updates the display buffer, but does not send the buffer to the display itself.
        Call 'update()' to render the buffer on the display.

        Args:
            number (int):  The number to show.
            digit (int):   The digit to show the number. Default: 0 (leftmost digit).
            has_dot (bool): Whether the decimal point to the right of the digit should be lit. Default: False.

        Returns:
            The instance (self)
        """
        assert 0 <= digit < 4, "ERROR - Invalid digit (0-3) set in set_number()"
        assert 0 <= number < 10, "ERROR - Invalid value (0-9) set in set_number()"
        return self.set_character(str(number), digit, has_dot)

    def set_character(self, char, digit=0, has_dot=False):
        """
        Present single alphanumeric character at the specified digit.

        Only characters from the class' character set are available:
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, a, b, c, d ,e, f, -.
        Other characters can be defined and presented using 'set_glyph()'.

        This method updates the display buffer, but does not send the buffer to the display itself.
        Call 'update()' to render the buffer on the display.

        Args:
            char (string):  The character to show.
            digit (int):    The digit to show the number. Default: 0 (leftmost digit).
            has_dot (bool): Whether the decimal point to the right of the digit should be lit. Default: False.

        Returns:
            The instance (self)
        """
        assert 0 <= digit < 4, "ERROR - Invalid digit set in set_character()"
        char = char.lower()
        char_val = 0xFF
        if char == "deg":
            char_val = HT16K33_SEGMENT_DEGREE_CHAR
        elif char == '-':
            char_val = self.HT16K33_SEGMENT_MINUS_CHAR
        elif char == ' ':
            char_val = self.HT16K33_SEGMENT_SPACE_CHAR
        elif char in 'abcdef':
            char_val = ord(char) - 87
        elif char in '0123456789':
            char_val = ord(char) - 48
        assert char_val != 0xFF, "ERROR - Invalid char string set in set_character()"
        self.buffer[self.POS[digit]] = self.CHARSET[char_val]
        if has_dot is True: self.buffer[self.POS[digit]] |= 0x80
        return self

'''
Send an AT command - return True if we got an expected
response ('back'), otherwise False
'''
def send_at(cmd, back="OK", timeout=1000):
    # Send the command and get the response (until timeout)
    buffer = send_at_get_resp(cmd, timeout)
    return (len(buffer) > 0 and back in buffer)

'''
Send an AT command - just return the response
'''
def send_at_get_resp(cmd, timeout=1000):
    # Send the AT command
    modem.write((cmd + "\r\n").encode())

    # Read and return the response (until timeout)
    return read_buffer(timeout)

'''
Read in the buffer by sampling the UART until timeout
'''
def read_buffer(timeout):
    buffer = bytes()
    now = ticks_ms()
    while (ticks_ms() - now) < timeout and len(buffer) < 1025:
        if modem.any():
            buffer += modem.read(1)
    return buffer.decode()

'''
Module startup detection
Send a command to see if the modem is powered up
'''
def boot_modem():
    state = False
    count = 0
    while count < 20:
        if send_at("ATE1"):
            print("The modem is ready")
            return True
        if not state:
            print("Powering the modem")
            module_power()
            state = True
        sleep(4)
        count += 1
    return False

'''
Power the module on/off
'''
def module_power():
    pwr_key = Pin(14, Pin.OUT)
    pwr_key.value(1)
    sleep(1.5)
    pwr_key.value(0)

'''
Configure the modem
'''
def configure_modem():
    # AT commands can be sent together, not just one at a time.
    # Set the error reporting level, set SMS text mode, delete left-over SMS
    # select LTE-only mode, select Cat-M only mode, set the APN to 'super' for Super SIM
    send_at("AT+CMEE=2;+CMGF=1;+CMGD=,4;+CNMP=38;+CMNB=1;+CGDCONT=1,\"IP\",\"super\"")
    # Set SSL no verify, set HTTPS request parameters
    send_at("AT+SHSSL=1,\"\";+SHCONF=\"BODYLEN\",1024;+SHCONF=\"HEADERLEN\",350")
    print("Modem configured for Cat-M and Super SIM")

'''
Check we are attached
'''
def check_network():
    is_connected = False
    response = send_at_get_resp("AT+COPS?")
    line = split_msg(response, 1)
    if "+COPS:" in line:
        is_connected = (line.find(",") != -1)
        if is_connected: print("Network information:", line)
    return is_connected

'''
Open/close a data connection to the server
'''
def open_data_conn():
    # Activate a data connection using PDP 0,
    # but first check it's not already open
    response = send_at_get_resp("AT+CNACT?")
    line = split_msg(response, 1)
    status = get_field_value(line, 1)

    if status == "0":
        # Inactive data connection so start one up
        success = send_at("AT+CNACT=0,1", "ACTIVE", 2000)
    elif status in ("1", "2"):
        # Active or operating data connection
        success = True

    print("Data connection", "active" if success else "inactive")
    return success

def close_data_conn():
    # Just close the connection down
    send_at("AT+CNACT=0,0")
    print("Data connection inactive")

'''
Start/end an HTTP session
'''
def start_session(server):
    # Deal with an existing session if there is one
    if send_at("AT+SHSTATE?", "1"):
        print("Closing existing HTTP session")
        send_at("AT+SHDISC")

    # Configure a session with the server...
    send_at("AT+SHCONF=\"URL\",\"" + server + "\"")

    # ...and open it
    resp = send_at_get_resp("AT+SHCONN", 2000)
    # The above command may take a while to return, so
    # continue to check the UART until we have a response,
    # or 90s passes (timeout)
    now = ticks_ms()
    while ((ticks_ms() - now) < 90000):
        #if len(resp) > 0: print(resp)
        if "OK" in resp: return True
        if "ERROR" in resp: return False
        resp = read_buffer(1000)
    return False

def end_session():
    # Break the link to the server
    send_at("AT+SHDISC")
    print("HTTP session closed")

'''
Set a standard request header
'''
def set_request_header():
    global req_head_set

    # Check state variable to see if we need to
    # set the standard request header
    if not req_head_set:
        send_at("AT+SHCHEAD")
        send_at("AT+SHAHEAD=\"Content-Type\",\"application/x-www-form-urlencoded\";+SHAHEAD=\"User-Agent\",\"twilio-pi-pico/1.0.0\"")
        send_at("AT+SHAHEAD=\"Cache-control\",\"no-cache\";+SHAHEAD=\"Connection\",\"keep-alive\";+SHAHEAD=\"Accept\",\"*/*\"")
        req_head_set = True

'''
Set request body
'''
def set_request_body(body):
    send_at("AT+SHCPARA;+SHPARA=\"data\",\"" + body + "\"")

'''
Make a GET, POST requests to the specified server
'''
def get_data(server, path):
    return issue_request(server, path, None, "GET")

def send_data(server, path, data):
    return issue_request(server, path, data, "POST")

def issue_request(server, path, body, verb):
    result = ""

    # Check the request verb
    code = 0
    verbs = ["GET", "PUT", "POST", "PATCH", "HEAD"]
    if verb.upper() in verbs:
        code = verbs.index(verb) + 1
    else:
        print("ERROR -- Unknown request verb specified")
        return ""

    # Attempt to open a data session
    if start_session(server):
        print("HTTP session open")
        # Issue the request...
        set_request_header()
        print("HTTP request verb code:",code)
        if body != None: set_request_body(body)
        response = send_at_get_resp("AT+SHREQ=\"" + path + "\"," + str(code))
        start = ticks_ms()
        while ((ticks_ms() - start) < 90000):
            if "+SHREQ:" in response: break
            response = read_buffer(1000)

        # ...and process the response
        lines = split_msg(response)
        for line in lines:
            if len(line) == 0: continue
            if "+SHREQ:" in line:
                status_code = get_field_value(line, 1)
                if int(status_code) > 299:
                    print("ERROR -- HTTP status code",status_code)
                    break

                # Get the data from the modem
                data_length = get_field_value(line, 2)
                if data_length == "0": break
                response = send_at_get_resp("AT+SHREAD=0," + data_length)

                # The JSON data may be multi-line so store everything in the
                # response that comes after (and including) the first '{'
                pos = response.find("{")
                if pos != -1: result = response[pos:]
        end_session()
    else:
        print("ERROR -- Could not connect to server")
    return result

'''
Flash the Pico LED
'''
def led_blink(blinks):
    for i in range(0, blinks):
        led_off()
        sleep(0.25)
        led_on()
        sleep(0.25)

def led_on():
    led.value(1)

def led_off():
    led.value(0)

'''
Split a response from the modem into separate lines,
removing empty lines and returning all that's left or,
if 'want_line' has a non-default value, return that one line
'''
def split_msg(msg, want_line=999):
    lines = msg.split("\r\n")
    results = []
    for i in range(0, len(lines)):
        if i == want_line:
            return lines[i]
        if len(lines[i]) > 0:
            results.append(lines[i])
    return results

'''
Extract the SMS index from a modem response line
'''
def get_sms_number(line):
    return get_field_value(line, 1)

'''
Extract a comma-separated field value from a line
'''
def get_field_value(line, field_num):
    parts = line.split(",")
    if len(parts) > field_num:
        return parts[field_num]
    return ""

'''
Blink the LED n times after extracting n from the command string
'''
def process_command_led(msg):
    blinks = msg[4:]
    print("Blinking LED",blinks,"time(s)")
    try:
        led_blink(int(blinks))
    except:
        print("BAD COMMAND:",blinks)

'''
Display the decimal value n after extracting n from the command string
'''
def process_command_num(msg):
    value = msg[4:]
    print("Setting",value,"on the LED")
    try:
        # Extract the decimal value (string) from 'msg' and convert
        # to a hex integer for easy presentation of decimal digits
        hex_value = int(value, 16)
        display.set_number((hex_value & 0xF000) >> 12, 0)
        display.set_number((hex_value & 0x0F00) >>  8, 1)
        display.set_number((hex_value & 0x00F0) >>  4, 2)
        display.set_number((hex_value & 0x000F), 3).update()
    except:
        print("BAD COMMAND:",value)

'''
Get a temperature reading and send it back as an SMS
'''
def process_command_tmp():
    print("Sending a temperature reading")
    celsius_temp = "{:.2f}".format(sensor.read_temp())
    if send_at("AT+CMGS=\"000\"", ">"):
        # '>' is the prompt sent by the modem to signal that
        # it's waiting to receive the message text.
        # 'chr(26)' is the code for ctrl-z, which the modem
        # uses as an end-of-message marker
        r = send_at_get_resp(celsius_temp + chr(26))
    # Display the temperature on the LED
    digit = 0
    previous_char = ""
    for temp_char in celsius_temp:
        if temp_char == "." and 0 < digit < 3:
            # Set the decimal point -- but only if we're not
            # at the last digit to be shown
            display.set_character(previous_char, digit - 1, True)
        else:
            # Set the current digit
            display.set_character(temp_char, digit)
            previous_char = temp_char
            digit += 1
        if digit == 3: break
    # Add a final 'c' and update the display
    display.set_character('c', 3).update()

'''
Make a request to a sample server
'''
def process_command_get():
    print("Requesting data...")
    server = "YOUR_BEECEPTOR_URL"
    endpoint_path = "/api/v1/status"
    process_request(server, endpoint_path)

def process_command_post():
    print("Sending data...")
    server = "YOUR_BEECEPTOR_URL"
    endpoint_path = "/api/v1/logs"
    process_request(server, endpoint_path, "{:.2f}".format(sensor.read_temp()))

def process_request(server, path, data=None):
    # Attempt to open a data connection
    if open_data_conn():
        if data is not None:
            result = send_data(server, path, data)
        else:
            result = get_data(server, path)

        if len(result) > 0:
            # Decode the received JSON
            try:
                response = json.loads(result)
                # Extract an integer value and show it on the display
                if "status" in response:
                    process_command_num("NUM=" + str(response["status"]))
            except:
                print("ERROR -- No JSON data received. Raw:\n",result)
        else:
            print("ERROR -- No JSON data received")

        # Close the open connection
        close_data_conn()

'''
Listen for incoming SMS Commands
'''
def listen():
    print("Listening for Commands...")
    while True:
        # Did we receive a Unsolicited Response Code (URC)?
        buffer = read_buffer(5000)
        if len(buffer) > 0:
            lines = split_msg(buffer)
            for line in lines:
                if "+CMTI:" in line:
                    # We received an SMS, so get it...
                    num = get_sms_number(line)
                    msg = send_at_get_resp("AT+CMGR=" + num, 2000)

                    # ...and process it for commands
                    cmd = split_msg(msg, 2).upper()
                    if cmd.startswith("LED="):
                        process_command_led(cmd)
                    elif cmd.startswith("NUM="):
                        process_command_num(cmd)
                    elif cmd.startswith("TMP"):
                        process_command_tmp()
                    elif cmd.startswith("GET"):
                        process_command_get()
                    elif cmd.startswith("POST"):
                        process_command_post()
                    else:
                        print("UNKNOWN COMMAND:",cmd)
                    # Delete all SMS now we're done with them
                    send_at("AT+CMGD=,4")

# Globals
req_head_set = False

# Set up the modem UART
modem = UART(0, 115200)

# Set up I2C and the display
i2c = I2C(1, scl=Pin(3), sda=Pin(2))
display = HT16K33Segment(i2c)
display.set_brightness(2)
display.clear().draw()

# Set up the MCP9808 sensor
sensor = MCP9808(i2c=i2c)

# Set the LED and turn it off
led = Pin(25, Pin.OUT)
led_off()

# Start the modem
if boot_modem():
    configure_modem()

    # Check we're attached
    state = True
    while not check_network():
        if state:
            led_on()
        else:
            led_off()
        state = not state

    # Light the LED
    led_on()

    # Begin listening for commands
    listen()
else:
    # Error! Blink LED 5 times
    led_blink(5)
    led_off()
