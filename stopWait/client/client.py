#! /bin/python

#Abel Gomez 80602216
#########################################################################################
#########################################################################################
# Program client.py                                                                     #
# Description: The client send UDP packets to server (localhost:50000), it implements   # 
#              a stop-and-wait protocol. The client resends packets on timeout          # 
#              The client has a verbose which prints to console all actions (off by def)#
# Options: get - gets a file from the server                                            #
#          put - puts a file into the server, the file must exists in current path      #
# How to use: python client.py -v -g file_name                                          #
#                                                                                       #
#  ----------------     Modification Log ----------------                               #
#  Date          Name            Description                                            #
# --------------------------------------------------------------------------------------#
# 02/22/18      Abel Gomez       Initial Creation                                       #
#########################################################################################
#########################################################################################

import sys, re, os, time
from socket import *
from select import *

#Global variables

serverAddr = ('localhost', 50000)                                 #default server address
pckType = bytearray()                                             #packet type: G,P,A,E,F,D
pckSeq = bytearray()                                              #sequence of active packet
clientSocket = socket(AF_INET, SOCK_DGRAM)                        #UDP socket to communicate
header = bytearray()                                              #packet's header
message = bytearray()                                             #packet's data block
blockSeq = bytearray()                                            #data block sequence (not in use)
#define types of packets
GET = 'G'                                                        
PUT = 'P'
ACK = 'A'
DTA = 'D'
FIN = 'F'
ERR = 'E'
mode = 'u'                                                        #client mode, can be get or put
fileName = ""                                                     #file to request
verbose = 0                                                       #verbose mode
activePacket = {}                                                 #track the last packet that we sent
                                                                  #index 0 = sequence No '0' or '1'
                                                                  #index 1 = last data block sent
pckDic = {}                                                       #dic. to hold data blocks
totalPacket = 0                                                   #total number of packets
lastPacket = '1'                                                  #identify last packet
resendCount = 0                                                   #count number of resends
sendTime = 0                                                      #time when you send a packet
recTime = 0                                                       #time when you receive a packet
RTT = 0                                                           #round trip time
initTime = 0                                                      #time when we send the first packet
endTime = 0                                                       #time when we receive the last packet
fileLen = 0                                                       #size of input file

#Function: sendAck
#Description: Acknowledge packets received from server, if we receive a valid packet we write it into output file
#             and we send and ack back to the server. If we received and invalid discard it. 
def sendAck():
    #global variables
    global activePacket
    global pckSeq
    global lastPacket
    global pckToServer
    global outFile
    global message
    global recTime
    global sendTime
    global RTT
    global blockSeq

    #figure out if we receive a valid packet
    if lastPacket == pckSeq: #if our current packet sequence if equal to our last packet then we got a duplicated
        if verbose: print "Invalid Packet"
    else:
        #log receive time
        recTime = time.time()
        if verbose: print "Packet received at %f" % recTime
        #log Round Trip Time for each packet
        RTT = recTime - sendTime
        if verbose: print "RTT: %f" %RTT

        #we got a valid packet, save data into output file
        outFile.write('%s' % message)
        lastPacket = pckSeq

        #send an ack to the server 
        header = bytearray([ACK, pckSeq]) # create header
        msg = bytearray("ack", 'utf-8') #create message
        pckToServer = header+blockSeq+msg #concatenate packet 
        clientSocket.sendto(pckToServer, serverAddr)
        if verbose: print "Packet to Server: %c%c%s%s" % (pckToServer[0], pckToServer[1], pckToServer[2:7], pckToServer[7:])

        #log send time
        sendTime = time.time()
        if verbose: print "Packet sent at %f" % sendTime

#Function: openFile
#Description: open the file that the user wants to send to the server. The File will be split in sections of
#             100 MB and they will be save into a dictionary. The total file size must be less than 100,000MB
#             the protocol can only handle upto 99999 packets
def openFile():
    #global variables
    global pckDic
    global totalPacket
    global inFile
    global fileLen

    #open file and calculate size
    inFile = open(fileName, 'r')
    text = inFile.read()
    textArray = bytearray(text, 'utf-8')
    fileLen = len(textArray)

    #if the size is greater than 100,000MB. Terminate execution.
    if fileLen > 100000:
        if verbose: print "ERROR File to big"
        sys.exit(1)

    #calculate how many packets are we going to need
    numberOfPackets = len(textArray)/100
    if len(textArray) % 100 == 0:
        totalPacket = numberOfPackets
    else:
        totalPacket = numberOfPackets + 1
    #print "TP: %d" % totalPacket
    
    #save file into dictionary
    stIndex = 0
    endIndex = 100
    seqNum = 1
    for packet in range(1, totalPacket): #for each block section
        if packet == 1:
            pckDic[seqNum] = textArray[0:endIndex]
        else:
            pckDic[seqNum] = textArray[stIndex:endIndex]
        seqNum += 1
        stIndex = endIndex
        endIndex += 100
    pckDic[seqNum] = textArray[stIndex:] #save the remaining

    
#Function: sendFirstMsg
#Description: The function sends the first message to the server, the client is the one that starts the
#             communication. It can send two types of messages get or put
def sendFirstMsg():
    #global variables
    global lastPacket 
    global pckToServer
    global activePacket
    global outFile
    global sendTime
    global initTime

    #identify intended mode, and define header
    if mode == 'g':
        header = bytearray([GET, '0'])
        outFile = open(fileName, 'w+') #open output file
        lastPacket = '0'
    else:
        header = bytearray([PUT, '0'])
        #setup variables to track active packets
        activePacket[0] = '0'
        activePacket[1] = 0
        openFile() #open input file

        
    #create first sequence, on this implementation the sequence number is not use, but it will help us to 
    #implement sliding window
    sequence = 00000
    sequenceSrt = "%05d" % sequence
    sequenceBlock = bytes(sequenceSrt)

    #concatenate and send final packet
    msgToServer = fileName
    pckToServer = header+sequenceBlock+msgToServer
    if verbose: print "Packet sent to Server: %c%c%s%s" % (pckToServer[0], pckToServer[1], pckToServer[2:7], pckToServer[7:])
    clientSocket.sendto(pckToServer, serverAddr)
    
    #log send time
    sendTime = time.time()
    if verbose: print "Packet sent at %f" % sendTime
    initTime = time.time()
    if verbose: print "First packet sent at %f" % initTime
    #sys.exit(1)


#Function: sendNextBlock
#Description: send the next data block to the server, after getting the server ack the client needs to figure out
#             which is the next data block that needs to be send.
def sendNextBlock():
    #global variables
    global pckDic
    global pckToServer
    global activePacket
    global totalPacket
    global sendTime
    global recTime
    global RTT
    global endTime
    global initTime
    global blockSeq

    if pckSeq == 'F': #ack of FIN exit client
        if verbose: print "FIN ack, finish communication"
        inFile.close()
        endTime = time.time()
        if verbose: print "Last packet received at %f" % endTime
        if verbose: print "FirstPackt sent at: %f, LastPacket received at: %f" % (initTime, endTime)
        if verbose: print "Throughput~: %dMBps" % (fileLen/(endTime-initTime))
        sys.exit(1)

    #identify we got the correct ack
    if pckSeq != activePacket[0]:
        if verbose: print "Incorrect acknowledge received"
    else:
        #the client sent all packets, send a FIN packet
        if activePacket[1] == totalPacket:
            header = bytearray([FIN, 'F'])
            sequence = "%05d" % totalPacket
            blockSeq = bytearray(sequence)
            pckToServer = header+blockSeq+bytearray("I'm Done", 'utf-8') #packet to indicate we finish
            if verbose: print "Packet sent to Server: %s" % (pckToServer)
            clientSocket.sendto(pckToServer, serverAddr)
            activePacket[1] = totalPacket

        #if we still have packet to send, create and send next packet
        else:
            #log time
            recTime = time.time()
            if verbose: print "Packet received at %f" % recTime
            RTT = recTime - sendTime
            if verbose: print "RTT: %f" %RTT
            
            #get next block and update track variables
            nextBlock = activePacket[1] + 1
            if activePacket[0] == '0':
                activePacket[0] = '1'
            else:
                activePacket[0] = '0'
            activePacket[1] = nextBlock

            #create and send packet
            header = bytearray([DTA, activePacket[0]])
            sequence = "%05d" % nextBlock
            blockSeq = bytearray(sequence)
            pckToServer = header+blockSeq+pckDic[nextBlock]
            if verbose: print "Packet sent to Server: %s" % (pckToServer)
            clientSocket.sendto(pckToServer, serverAddr)
            
            #log time
            sendTime = time.time()
            if verbose: print "Packet sent at %f" % sendTime
    
    
#Function: processMsg
#Description: process incoming packets, the client can receive acks, data, fin or error packets from the server
#             we need to identify which packet the server sent and we need to process it properly.
def processMsg(sock):
    #global variables
    global pckSeq
    global lastPacket
    global pckDic
    global message
    global resendCount
    global endTime
    global initTime
    global blockSeq
    global fileLen
    
    #retreive packet from server
    returnMsg, serverAddrPort = sock.recvfrom(2048)
    if verbose: print "Packet received from server: %s, seq: %c" % (returnMsg[2:], ord(returnMsg[1]))
    
    #strip packet
    pckType = returnMsg[0]
    pckSeq = returnMsg[1]
    blockSeq = returnMsg[2:7] #this sequence is not being use but we still need to handle it
    message = returnMsg[7:] 
    resendCount = 0

    #identify what we got and process each packet properly
    if pckType == DTA:
        sendAck()
    elif pckType == FIN:
        print "End of file, creating local copy....." 
        print "File created in current directory: %s" % fileName
        endTime = time.time()
        if verbose: print "Last packet received at %f" % endTime
        if verbose: print "FirstPackt sent at: %f, LastPacket received at: %f" % (initTime, endTime)
        if verbose: print "Throughput~: %dMBps" % (os.path.getsize(fileName)/(endTime-initTime))
        outFile.close()
        sys.exit(1)
    elif pckType == ACK:
        sendNextBlock()
    elif pckType == ERR:
        print "Requested File not found or File to big"
        print "Please select a valid file"
        sys.exit(1)

        
#Function: usage
#Description: display correct usage of parameters
def usage():
    print """usage: %s \n
    Option                         Default             Description
    [--serverAddr host:port]       localhost:50001     Server name and port
    [--put or -p file Name]                            File name to send, must exists on current directory
    [--get or -g file Name]                            File name to get from server
    [--verbose or -v]              off                 Verbose Mode
    [--help or -h]                                     Print usage """% sys.argv[0]
    sys.exit(1)
    
#Function: closeConnection
#Description: terminate communication and do a clean up. 
#             we can not wait for ever for a response, if after 5 tries the server is not responding we close and finish 
#             all communication with the server.
def closeConnection():
    #global variables
    global pckToServer
    global activePacket
    global totalPacket

    #if we lost the server at the first packet, not big deal just terminate the client
    if pckToServer[0] == ord(GET) or pckToServer[0] == ord(PUT):
        print "Unable to reach server"
        print "Closing application"
        if pckToServer[0] == ord(GET):
            outFile.close()
        else:
            inFile.close()
    #If we don't get the last ack, we assume that the server got the full file
    elif pckToServer[0] == ord(FIN):
        #we assume success
        print "Transfer has completed successfully"
    #If we stop in the middle of a get, we accept and incomplete file
    elif pckToServer[0] == ord(ACK):
        print "Weird something is wrong"
        print "File %s is incomplete" % fileName
        outFile.close()
    #If we stop in the middle of a put, there is not much that we could do.
    #just report the percentage of packets sent
    elif pckToServer[0] == ord(DTA):
        print "Unable to rearch Server"
        print "Incomplete Transfer, %d packets of %d sent" % (activePacket[1], totalPacket)
        inFile.close()

#Check for any user parameters
try:
    args = sys.argv[1:]
    while args:
        sw = args[0]; del args[0]
        if sw == "--serverAddr":
            addr, port = re.split(":", args[0]); del args[0]
            serverAddr = (addr, int(port))
        elif sw == "--put" or sw == "-p":
            fileName = args[0]; del args[0]
            #check file exists
            if not os.path.exists(fileName):
                print "Input File does not exists in current directory: %s" % fileName
                sys.exit(1)
            else:
                mode = 'p'
        elif sw == "--get" or sw == "-g":
            fileName = args[0]; del args[0]
            mode = 'g'
        elif sw =="--help" or sw == "-h":
            usage();
        elif sw =="--verbose" or sw =="-v":
            verbose = 1
        else:
            print "unexpected parameter %s" % args[0]
            usage();
except Exception as e: 
    print "Error parsing arguments %s" % (e)
    usage()
    
###Main logic start here###
#verify parms
if mode == 'u':
    print "Incorrect use of client, you need to use get or put function"
    usage()
    sys.exit(1)
    
print "ready to communicate"
#send first message
sendFirstMsg() 

#setup to actively listen to any interaction between client and server 
readSockFunc = {}
writeSockFunc = {}
errorSockFunc = {}
timeout =  5
readSockFunc[clientSocket] = processMsg 

#print "ready to communicate"
while True:
    #detect whenever we have something to read, the server may send a packet at any given time
    readRdySet, writeRdySet, errorRdySet = select(readSockFunc.keys(), writeSockFunc.keys(), errorSockFunc.keys(), timeout)
    if not readRdySet and not writeRdySet and not errorRdySet:
        print "timeout: no events"
        #the client will try to resend the last packet upto 5 times, if we reach the fifth try without a reponse
        #we assume that the server is down.
        if resendCount == 5:
            closeConnection()
            sys.exit(1)
        else:
            #resend last packet on timeout
            clientSocket.sendto(pckToServer, serverAddr)
            resendCount += 1
            if verbose: print "resend count: %d" % resendCount
        if verbose: print "Packet to Server on resend: %c%c%s" % (pckToServer[0], pckToServer[1], pckToServer[2:])

    #Figure out what we got
    for sock in readRdySet:
        readSockFunc[sock](sock)
