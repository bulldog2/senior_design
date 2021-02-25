# send specific files over lora
# Currently working on parsing
# Import Python System Libraries
import time
# Import Blinka Libraries
import busio
from digitalio import DigitalInOut, Direction, Pull
import board

# Import RFM9x
import adafruit_rfm9x
import os

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)

# Configure LoRa Radio
CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 915.0)
rfm9x.tx_power = 23
# rmf9x.signal_bandwdith = 125000 # default is 125000 (Hz), 125000 is used in long range
                                  # Signal_bandwdith can be 7800, 10400, 15600, 20800, 31250, 41700, 62500, 125000, 250000
# rfm9x.coding_rate = 5 # Default is 5, can be 5,6,7,8
                        # Coding_rate (CR) can be be set higher for better noise tolerance, and lower for increased bit rate
# rfm9x.spreading_factor = 7 # default is 7, higher values increase the ability to distingish signal from noise
                             # lower values increase data transmission rate
prev_packet = None

# file setup
files = os.listdir("tx_dir") # get files from this directory
currentfile = files[0]
i = 0 # variable for listing files
receivedfile = "rfile.txt" # default file to write to
open("rx_dir/" + receivedfile,"w").close() # open file and close to clear it when program starts

# Chunk Setup
chunk_size = 240 # chunk size in bytes, set equal to maximum packet size
pkt_num = "00"
tx_reserve = "ff"
req_reserve = 0
pkt_num_int = 0
next_pkt_request = 0

# timing
rec_scan_timeout = 1 # Timeout for initial RX scan


print("Please Choose a Mode: \n RX=1\n TX=2\n")
choice = input("Enter Number:")

while int(choice) == 1: # RX Mode
    packet = None
    packet = rfm9x.receive(timeout=rec_scan_timeout) # wait 5 seconds for reciever timeout
    if packet is None: # idle RX mode
        print("Waiting for Packet")
    else: # data  RX mode
        # Parse Paket
        prev_packet = packet
        packet_text = str(prev_packet, "utf-8")
        pkt_rec = packet_text[0:2] # get first two bytes for packet number
        pkt_rec = int(pkt_rec,16)  # convert first two bytes to int
        tx_fill = packet_text[2:4] # Place holder
        tx_fill = int(tx_fill,16)  # place holder
        packet_text = packet_text[4:] # get data from packet
        
        # Write data to file
        print("Recieved Packet number: " + str(pkt_rec) + " Writing to " + receivedfile + " now")
        w = open("rx_dir/" + receivedfile, "a") # add to file
        w.write(packet_text)

        # Request Next Packet
        next_pkt_request = pkt_rec + 1 # integer
        next_pkt_request = hex(next_pkt_request)
        next_ptk_request = str(next_pkt_request)
        next_pkt_request = bytes(next_pkt_request,"utf-8")


        time.sleep(0.1) # Pause for 0.1 seconds

while int(choice) == 2: # TX Mode
    # List Files in Transmit Directory And ask user what file to send
    print("The current files in tx_dir/ are:")
    for x in range(len(files)): # show all files
        print(files[x])
    print("\n")
    currentfile = input("What file would you like to open? (include .txt)") # Aks User to Choos File

    filesize = os.stat("tx_dir/" + currentfile).st_size # get file size in bytes
    f = open("tx_dir/" + currentfile, "r") # open file

    # Send Multiple Packets
    sent_size = 0 # clear sent size
    chunk_number = 1 # clear chunk number
    pkt_num = "00" # start with packet number 0

    # Send file in chunks
    #while sent_size < filesize:
    while True:
        current_chunk = f.read(chunk_size) # read chunk of file
        print("Chunk " + str(chunk_number) + " contains:" + str(current_chunk)) # Print chunk of file
        tx_data = bytes(pkt_num + tx_reserve + current_chunk, "utf-8")
        rfm9x.send(tx_data)
        sent_size = sent_size + chunk_size
        chunk_number += 1

            # Send Next Packet
            packet = None
            tries = 0;
            while tries < 3 and packet is None: # try sending 3 times
                packet = rfm9x.receive(timeout = 5) # wati for the sender to send a request for next packet
                if packet is None:
                    print("No ACK, Resending packet number " + pkt_num)
                    rfm9x.send(tx_data)
                    tries += 1
                else:
                    packet_txt = str(packet,"utf-8")
                    if packet_txt == pkt_num:
                        print("Error in received pkt, resending")
                        rfm9x.send(tx_data)
                        tries += 1
                        packet = None
            if packet is None:
                print("No acknowledge recieved, canceling send")
                break
            #increment packet number
            pkt_num = int(pkt_num,16)
            pkt_num += 1
            pkt_num_int += 1
            pkt_num = hex(pkt_num)
            pkt_num = str(pkt_num)
            if len(pkt_num) < 4:
                pkt_num = "0" + pkt_num[2:]
            else:
                pkt_num = pkt_num[2:]
            print(pkt_num)
            #time.sleep(3) # pause for 1 sec

    #else:
    #    # Send contents with one packet
    #    print(currentfile + " is now being sent through LoRa\n")
    #    f = open("tx_dir/" + currentfile, 'r')
    #    tx_data = bytes(f.read(), "utf-8")
    #    rfm9x.send(tx_data)
    time.sleep(0.1)
