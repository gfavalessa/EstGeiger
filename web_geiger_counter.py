#   MicroPython Geiger Counter Main Code for Esp32 board (WebServer)
#
#   This code interacts with the RadiationD-v1.1 (CAJOE) Geiger counter board
#   and reports readings in CPM (Counts Per Minute),
#   showing the information in a oled display and in a web browser.
#
#   Author: Gabriel F. Fraga
#   03 Mar 2018

import network
import utime
import socket
import machine
import ssd1306
from machine import Pin

# Used variables
LOG_PERIOD = 10000
MAX_PERIOD = 60000
multiplier = MAX_PERIOD / LOG_PERIOD
previousMillis = 0
cpm = 0
interruptCounter = 0


# Callback function for interrupt counter
def counter_callback(pin):
    global interruptCounter
    interruptCounter = interruptCounter + 1

# Connection
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Connect to your network
utime.sleep(1)
wlan.connect('batnet', 'naotemsenha')
utime.sleep(1)

#HTML to send to browsers
html = """<!DOCTYPE html>
<html>
<head> <title>Geiger Counter</title> </head>
<body> <h1>Geiger Counter - Micropython (ESP32)</h1>
<table border="1"> <tr><th>Counter</th><th>Value</th></tr> %s </table>
</body>
</html>
"""

# Setup the oled
i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
oled.fill(0)
oled.text('Welcome', 30, 20)
oled.show()

# Setup interrupt
p0 = Pin(34, Pin.IN)
p0.irq(trigger=Pin.IRQ_FALLING, handler=counter_callback)

startMillis = utime.ticks_ms()

#Setup Socket WebServer
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

# Program Main Loop
while True:
    # Connect and show the ip address
    cl, address = s.accept()
    print("Got a connection from %s" % str(address))
    cl_file = cl.makefile('rwb', 0)

    # Display cpm counter
    currentMillis = utime.ticks_diff(utime.ticks_ms(), startMillis)
    if currentMillis - previousMillis > LOG_PERIOD:
        previousMillis = currentMillis
        cpm = interruptCounter * multiplier
        print("CPM:", cpm)
        oled.fill(0)
        oled.text('Geiger Counter', 10, 0)
        oled.text('CPM: ', 30, 20)
        oled.text(str(cpm), 70, 20)
        oled.show()
        interruptCounter = 0

    while True:
        line = cl_file.readline()
        if not line or line == b'\r\n':
            break

    rows = ['<tr><td>%s</td><td>%d</td></tr>' % ("CPM", cpm)]
    response = html % '\n'.join(rows)
    cl.send(response)
    cl.close()
