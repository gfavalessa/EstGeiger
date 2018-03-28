#   MicroPython Geiger Counter Main Code for Esp32 board (ThingSpeak IoT Cloud)
#
#   This code interacts with the RadiationD-v1.1 (CAJOE) Geiger counter board
#   and reports readings in CPM (Counts Per Minute), showing the  information
#   in a oled display and send the data to ThingSpeak IoT Cloud (MQTT).
#
#   Author: Gabriel F. Fraga
#   27 Mar 2018

import utime
import machine
import ssd1306
import network
from umqtt.robust import MQTTClient
import uos
import gc
from machine import Pin


# WiFi connection information
wifiSSID = "batnet"             # EDIT - enter name of WiFi connection point
wifiPassword = "naotemsenha"    # EDIT - enter WiFi password

# Turn off the WiFi Access Point
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)

# Connect the ESP32 device to the WiFi network
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(wifiSSID, wifiPassword)

# Wait until the ESP32 is connected to the WiFi network
maxAttempts = 20
attemptCount = 0
while not wifi.isconnected() and attemptCount < maxAttempts:
    attemptCount += 1
    utime.sleep(1)
    print('did not connect...trying again')

# Create a random MQTT clientID
randomNum = int.from_bytes(uos.urandom(3), 'little')
myMqttClient = bytes("client_" + str(randomNum), 'utf-8')

# Connect to Thingspeak MQTT broker
# Connection uses unsecure TCP (port 1883)
#
# Steps to change to a secure connection (encrypted) using TLS
#   a) change port below to "port=8883
#   b) add parameter "ssl=True"
#   NOTE:  TLS uses about 9k bytes of the heap. That is a lot.
#          (about 1/4 of the micropython heap on the ESP8266 platform)

thingspeakUrl = b"mqtt.thingspeak.com"
thingspeakUserId = b"gfavalessaf"           # EDIT - enter Thingspeak User ID
thingspeakMqttApiKey = b"XO5VTN0FLOTMA3DV"  # EDIT - enter Thingspeak MQTT API Key
client = MQTTClient(client_id=myMqttClient,
                    server=thingspeakUrl,
                    user=thingspeakUserId,
                    password=thingspeakMqttApiKey,
                    port=1883)

client.connect()

# Publish free heap to Thingspeak using MQTT
thingspeakChannelId = b"442333"                     # EDIT - enter Thingspeak Channel ID
thingspeakChannelWriteApiKey = b"DYUTUVNWIG514ICS"  # EDIT - enter Thingspeak Write API Key
publishPeriodInSec = 30


# Variables used in GeigerCounter algorithm
LOG_PERIOD = 30000
MAX_PERIOD = 60000
multiplier = MAX_PERIOD / LOG_PERIOD
previousMillis = 0
cpm = 0
interruptCounter = 0

# Callback function for interrupt counter
def counter_callback(pin):
    global interruptCounter
    interruptCounter = interruptCounter + 1

# Setup the oled
#i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21))
#oled = ssd1306.SSD1306_I2C(128, 64, i2c)
#oled.fill(0)
#oled.text('Welcome', 30, 20)
#oled.show()

# Setup interrupt
p0 = Pin(34, Pin.IN)
p0.irq(trigger=Pin.IRQ_FALLING, handler=counter_callback)


# Program Main Loop
while True:
    # Display cpm counter
    cpm = interruptCounter * multiplier
    print("CPM:", cpm)
    #    oled.fill(0)
    #oled.text('Geiger Counter', 10, 0)
    #oled.text('CPM: ', 30, 20)
    #oled.text(str(cpm), 70, 20)
    #oled.show()
    interruptCounter = 0

    freeHeapInBytes = gc.mem_free()
    credentials = bytes("channels/{:s}/publish/{:s}".format(thingspeakChannelId, thingspeakChannelWriteApiKey), 'utf-8')
    payload = bytes("field1={:.2f}\n".format(cpm), 'utf-8')
    client.publish(credentials, payload)
    utime.sleep(publishPeriodInSec)

client.disconnect()

