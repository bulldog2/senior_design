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

pkt_num = "0x00" # packet number in hex as a string, sent as string through LoRa
pkt_num_int = 0
next_pkt_request = 0

header = None # holds packet number, size defined by header_size  
data = None # holds data, size us up to chunk_size
# => tx_data = header + data

max_pkt_size = 250 # maximum amount of bytes that can be send in a packet, it is 251B
header_size  =   2 # Size of header that holds packet number, 2 bytes gives up to 256 packets
                   # each bytes gives one character for hex
chunk_size   = max_pkt_size - header_size # chunk size in Bytes, maximum size of data

print("Please Choose a Mode: \n RX=1\n TX=2\n")
choice = input("Enter Number:")


while int(choice) == 1: # RX Mode
    packet = None
    print("Waiting to recieve for 5 seconds")
    packet = rfm9x.receive(timeout=5) # wait 5 seconds for reciever timeout
    if packet is None: # idle RX mode
        print("Waiting for Packet")
    else: # data  RX mode
        # Parse Paket
        prev_packet = packet
        packet_text = str(prev_packet, "utf-8")
        pkt_rec = packet_text[0:header_size] # get first two bytes for packet number
        pkt_rec = int(pkt_rec,16)  # convert first two bytes to int
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
        # End of RX mode

######### Transmit Mode
while int(choice) == 2: # TX Mode
    # List Files in Transmit Directory And ask user what fil to send
    print("The current files in tx_dir/ are:")
    for x in range(len(files)): # show all files
        print(files[x])
    print("\n")
    currentfile = input("What file would you like to open? (include .txt)") # Aks User to Choos File

    file_size = os.stat("tx_dir/" + currentfile).st_size # get file size in bytes
    f = open("tx_dir/" + currentfile, "r") # open file

    sent_size = 0 # clear sent size
    chunk_number = 1 # clear chunk number
    pkt_num = "00" # start with packet number 0

    print(" The rest of this program is under construction")
    ############ Summary of File sending ######################
    # Start sending packets
    # While (sent size is less than file size)
        # Control structure for handling single packet
            # Listen for ACKS, resend if necacary
            # send next packet
        # Increment packet number
        # Increase sent size
    # Go back to start of TX and ask for next file to send
    ###########################################################

    # While (sent size is less than file sive)
    while sent_size < file_size:
        # get data from chunk of file
        print("Getting Chunk, beginning packet sending shortly ")
        data = f.read(chunk_size) # read chunk of file for data
        header = pkt_num # get header from pkt_num
        tx_data = header + data # add header and data
        print("The full packet (tx_data) is: " + tx_data)

        # Send 1 packet and check for ACK, resend if necasary
        packet = None # Clear packet in order to check for one.
        tries = 0; # clear tries for next send
        #packet = True # Uncomment to skip the following loop.
        while tries < 3 and packet is None: # try sending 3 times
            print("    Checking for ACK, pausing for 5 seconds")
            rec_packet = rfm9x.receive(timeout = 5) # Wait for 5 seconds for receiever to request packet
            if rec_packet is None: # If no packet received
                print("No ACK, Resending packet number " + pkt_num)
                rfm9x.send(tx_data) # send packet again
                tries += 1 # incement tries
            else: # IF a packet is received
                packet_txt = str(rec_packet,"utf-8") #convert packet to string, should have two characters
                if packet_txt == pkt_num: # if the received packet is equal to packet_num
                    print("Error in received pkt, resending")
                    rfm9x.send(tx_data) # send packet gain
                    tries += 1
                    packet = None # empty packet to start try loop again
                else: # If the packet is not equal to pkt_num, assume receiver wants next packet for now
                    continue # do nothing
            # go back to start of try sending 3 times unless the packet =/= pkt_num

        # If no ACK is recieved from reciever after 3 attempts
        if packet is None:
            print("No acknowledge recieved, canceling send")
            break # Exits  [while sent_size < file_size:] and leads to the restart of TX mode

        # At this point it is assumed that the paket was correctly sent and recieved

        # Increment pkt_num with string format for next packet
        print("pkt_num is currently " + pkt_num)
        # Set up numbers for sending next packet
        #pkt_num = hex(pkt_num)  # Convert pkt_num from string to hex
        pkt_num = int(pkt_num,16)  # Convert pkt_num from hex    to int
        pkt_num += 1  # Incrmnt pkt_num
        pkt_num = "0x{:02x}".format(pkt_num) # Force two hex digits, IDK how this works, found on https://stackoverflow.com/questions/11676864/how-can-i-format-an-integer-to-a-two-digit-hex
        print("pkt_num is now " + pkt_num[-2:]) # print last two characters (hex Digits) from pkt_num

        # Increase sent size (assume packet was sent for now)
        sent_size = sent_size + chunk_size 
        time.sleep(1)
        # Go back to     while sent_size < file_size:

    # At this Point, the file should be either sent or too many failed attempts to send it occured
    time.sleep(1) # Pause for 1 second, go back to asking user for file to send

''' 
        #current_chunk = f.read(chunk_size) # read chunk of file
        #print("Chunk " + str(chunk_number) + " contains:" + str(current_chunk)) # Print chunk of file
        #tx_data = bytes(pkt_num + tx_reserve + current_chunk, "utf-8")
        rfm9x.send(tx_data)
        sent_size = sent_size + chunk_size
        chunk_number += 1

    # Send Packets and check for ACK
    packet = None # Clear packet in order to check for one.
    tries = 0;
    while tries < 3 and packet is None: # try sending 3 times
        packet = rfm9x.receive(timeout = 5) # Wait for 5 seconds for receiever to request packet
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

    # If no ACK is recieved from reciever after 3 attempts
    if packet is None:
        print("No acknowledge recieved, canceling send")
        break # Exit TX Mode
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
    # End of TX mode
'''

# End Idle Mode (optional if a break in the TX mode
while True:
     print("An ERROR has occured, please restart program")
     time.sleep(5)
