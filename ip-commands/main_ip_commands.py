# Version 1.0.0
# Copyright © 2021, Twilio
# Contains code © 2021, Tony Smith (@smittytone)
# Licence: MIT

import sys
from machine import UART, Pin, I2C
from utime import ticks_ms, sleep

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


# Functions

'''
Send an AT command - return True if we got an expected
response ('back'), otherwise False
'''
def send_at(cmd, back="OK", timeout=500):
    # Send the command and get the response (until timeout)
    buffer = send_at_get_resp(cmd, timeout)
    if len(buffer) > 0: return (back in buffer)
    return False

'''
Send an AT command - just return the response
'''
def send_at_get_resp(cmd, timeout=500):
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
            power_module()
            state = True
        sleep(4)
        count += 1
    return False

'''
Power the module on/off
'''
def power_module():
    pwr_key = Pin(14, Pin.OUT)
    pwr_key.value(1)
    sleep(1.5)
    pwr_key.value(0)

'''
Check we are attached
'''
def check_network():
    is_connected = False
    response = send_at_get_resp("AT+COPS?", 1000)
    line = split_msg(response, 1)
    if "+COPS:" in line:
        is_connected = (line.find(",") != -1)
        if is_connected:
            print("Network information:", line)
    return is_connected

'''
Attach to the network
'''
def configure_modem():
    # AT commands can be sent together, not one at a time.
    # Set the error reporting level, set SMS text mode, delete left-over SMS
    # select LTE-only mode, select Cat-M only mode, set the APN to 'super' for Super SIM
    send_at("AT+CMEE=2;+CMGF=1;+CMGD=,4;+CNMP=38;+CMNB=1;+CGDCONT=1,\"IP\",\"super\"")
    # Set SSL version, SSL no verify, set HTTPS request parameters
    send_at("AT+CSSLCFG=\"sslversion\",1,3;+SHSSL=1,\"\";+SHCONF=\"BODYLEN\",1024;+SHCONF=\"HEADERLEN\",350")
    print("Modem configured for Cat-M and Super SIM")

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
        # There's no active data connection so start one up
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
Start a UDP session
'''
def start_udp_session():
    send_at("AT+CASERVER=0,0,\"UDP\",6969")
    send_at("AT+CACFG=\"REMOTEADDR\",0,100.64.0.1,6969")

'''
Split a response from the modem into separate lines,
removing empty lines and returning what's left or,
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
Extract a comma-separated field value from a line
'''
def get_field_value(line, field_num):
    parts = line.split(",")
    if len(parts) > field_num:
        return parts[field_num]
    return ""

'''
Flash the Pico LED
'''
def led_blink(blinks):
    for i in range(0, blinks):
        led_off()
        time.sleep(0.25)
        led_on()
        time.sleep(0.25)

def led_on():
    led.value(1)

def led_off():
    led.value(0)

'''
Listen for IP commands
'''
def listen():
    # Try and open an IP connection
    if open_data_conn():
        # Success... start a UDP server
        start_udp_session()
        print("Listening for IP commands...")

        # Loop to listen for messages
        while True:
            # Check for data from the module
            buffer = read_buffer(5000)
            # Did we receive a Unsolicited Response Code (URC)?
            if len(buffer) > 0:
                lines = split_msg(buffer)
                for line in lines:
                    if "+CANEW:" in line:
                        # A UDP packet has been received, so get its data
                        resp = send_at_get_resp("AT+CARECV=0,100")
                        parts = split_msg(resp)
                        if len(parts) > 1:
                            # Split at the comma
                            cmd = get_field_value(parts[1], 1)
                            if cmd != "":
                                print("Command received:",cmd)
                                process_cmd(cmd)
                            break
    else:
        print("ERROR -- could not open data connection")

def process_cmd(line):
    val = ""
    cmd = line
    val_start = line.find("=")
    if val_start != -1:
        val = line[val_start + 1:]
        cmd = line[:val_start]
    cmd = cmd.upper()
    if cmd == "NUM" and len(val) < 5:
        process_command_num(val)
    elif cmd == "SEND":
        send_data("We can\'t wait to see what you build!")
    else:
        print("Command not recognized")

'''
Display the decimal value n after extracting n from the command string
'''
def process_command_num(value):
    print("Setting",value,"on the LED")
    try:
        # Extract the decimal value (string) from 'msg' and convert
        # to a hex integer for easy presentation of decimal digits
        hex_value = int(value, 16)
        display.set_number((hex_value & 0xF000) >> 12, 0)
        display.set_number((hex_value & 0x0F00) >> 8,  1)
        display.set_number((hex_value & 0x00F0) >> 4,  2)
        display.set_number((hex_value & 0x000F), 3).draw()
    except:
        print("Bad value:",value)

def send_data(data_string):
    length = len(data_string)
    if send_at("AT+CASEND=0," + str(length), ">"):
        # '>' is the prompt sent by the modem to signal that
        # it's waiting to receive the message text.
        # 'chr(26)' is the code for ctrl-z, which the modem
        # uses as an end-of-message marker
        send_at(data_string + chr(26))

'''
Runtime start
'''
# Set up the modem UART
modem = UART(0, 115200)

# Set up I2C and the display
i2c = I2C(1, scl=Pin(3), sda=Pin(2))
display = HT16K33Segment(i2c)
display.set_brightness(2)
display.set_glyph(64, 0).set_glyph(64, 1)
display.set_glyph(64, 2).set_glyph(64, 3).draw()

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
    listen()
else:
    # Error! Blink LED 5 times
    led_blink(5)
    led_off()
