"""
Example for using the RFM9x Radio with Raspberry Pi.

Learn Guide: https://learn.adafruit.com/lora-and-lorawan-for-raspberry-pi
Author: Brent Rubell for Adafruit Industries

This code is tested and works
"""
# Import Python System Libraries
import time
# Import Blinka Libraries
import busio
from digitalio import DigitalInOut, Direction, Pull
import board
# Import the SSD1306 module.
import adafruit_ssd1306
# Import RFM9x
import adafruit_rfm9x

# set up temp monitor
from gpiozero import CPUTemperature
#enable temp readings
from gpiozero import CPUTemperature

# Button A
btnA = DigitalInOut(board.D13)
btnA.direction = Direction.INPUT
btnA.pull = Pull.UP

# Button B
btnB = DigitalInOut(board.D19)
btnB.direction = Direction.INPUT
btnB.pull = Pull.UP

# Button C
btnC = DigitalInOut(board.D26)
btnC.direction = Direction.INPUT
btnC.pull = Pull.UP

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)

# 128x32 OLED Display
reset_pin = DigitalInOut(board.D4)
display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, reset=reset_pin)
# Clear the display.
display.fill(0)
display.show()
width = display.width
height = display.height

# Configure LoRa Radio
CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 915.0)
rfm9x.tx_power = 23
prev_packet = None

#promt user for log file name, overwrite for now so that we don't have to clear the log
logFile = "log.csv" #default
#logFile = input("File to save data to: ")
log = open(logFile, 'a') # w = overwrite file, a = append
log.write("#message,#date,#time,#distance (m),#temp (C),#RSSI (dBm)\n") # column label header if overwriting
print("Logging data to " + logFile + "..." ) # tell user what program is doing
distance = 0 # dummy value since not logging distance in this program

while True:
    packet = None
    display.fill(0) #draw a box to clear the image
    display.text('RasPi LoRa', 35, 0, 1)

    # check for packet rx
    packet = rfm9x.receive()
    if packet is None:
        display.show()
        display.text('- Waiting for PKT -', 15, 20, 1)
    else:
        try: # try to log everything as long as packet can be decoded (fully recieved)
             display.text('- PKT Received -', 15, 20, 1) # print to OLED display
            prev_packet = packet
            packet_text = str(prev_packet, "utf-8") 
            print("Recieved: " + packet_text + " with RSSI= " + str(rfm9x.last_rssi)) # print to cli 

            # get log data
            cpu = CPUTemperature()
            temp = str(cpu.temperature)
            message = str("Trial on: ")
            dateYMD = strftime("%Y-%m-%d")
            timeHMS = strftime("%H:%M:%S")

            # Write log data to log
            print("Writing to log.csv") # print to cli
            log.write("{0},{1},{2},{3},{4},{5}\n".format(message,dateYMD,timeHMS, str(distance), temp,str(rfm9x.last_rssi)))
            time.sleep(1)
        except UnicodeDecodeError: # if the packet is not able to be decode
            print("Packet error")
            display.text('PKT Error', 15, 20, 1)
            message = str("Packet Error: ")
            dateYMD = strftime("%Y-%m-%d")
            timeHMS = strftime("%H:%M:%S")
            log.write("{0},{1},{2},{3},{4},{5}\n".format(message,dateYMD,timeHMS, str(distance),temp,str(rfm9x.last_rssi)))
            time.sleep(1)
            continue

    if not btnA.value:
        # Send Button A
        display.fill(0)
        button_a_data = bytes("Button A!\r\n","utf-8")
        rfm9x.send(button_a_data)
        display.text('Sent Button A!', 25, 15, 1)
    elif not btnB.value:
        # Send Button B
        display.fill(0)
        button_b_data = bytes("Button B!\r\n","utf-8")
        rfm9x.send(button_b_data)
        display.text('Sent Button B!', 25, 15, 1)
    elif not btnC.value:
        # Send Button C
        display.fill(0)
        button_c_data = bytes("Button C!\r\n","utf-8")
        rfm9x.send(button_c_data)
        display.text('Sent Button C!', 25, 15, 1)


    display.show()
    time.sleep(0.1)
