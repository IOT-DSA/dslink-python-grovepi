'''
Copyright (C) 2015 Dexter Industries
Copyright (C) 2015 DGLogik

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''
import smbus
import time

import RPi.GPIO as GPIO

# This device has two I2C addresses.
DISPLAY_RGB_ADDR = 0x62
DISPLAY_TEXT_ADDR = 0x3e

# Use the bus that matches your Raspberry Pi's version
rev = GPIO.RPI_REVISION
if rev == 2 or rev == 3:
    bus = smbus.SMBus(1)
else:
    bus = smbus.SMBus(0)


def set_rgb(r, g, b):
    """
    Set the backlight's RGB colors.
    :param r: Red(0-255).
    :param g: Green(0-255).
    :param b: Blue(0-255).
    """
    bus.write_byte_data(DISPLAY_RGB_ADDR, 0, 0)
    bus.write_byte_data(DISPLAY_RGB_ADDR, 1, 0)
    bus.write_byte_data(DISPLAY_RGB_ADDR, 0x08, 0xaa)
    bus.write_byte_data(DISPLAY_RGB_ADDR, 4, r)
    bus.write_byte_data(DISPLAY_RGB_ADDR, 3, g)
    bus.write_byte_data(DISPLAY_RGB_ADDR, 2, b)


def text_command(cmd):
    """
    Send command to display.
    :param cmd: Command.
    """
    bus.write_byte_data(DISPLAY_TEXT_ADDR, 0x80, cmd)


def set_text(text):
    """
    Set the display's text, auto wrap or \n for newline.
    :param text: Text to display.
    """
    text = text.replace("\\n", "\n")
    text_command(0x01)  # Clear display.
    time.sleep(0.05)
    text_command(0x08 | 0x04)  # Display on, no cursor.
    text_command(0x28)  # 2 lines.
    time.sleep(0.05)
    count = 0
    row = 0
    for c in text:
        if c == '\n' or count == 16:
            count = 0
            row += 1
            if row == 2:
                break
            text_command(0xc0)
            if c == '\n':
                continue
        count += 1
        bus.write_byte_data(DISPLAY_TEXT_ADDR, 0x40, ord(c))
