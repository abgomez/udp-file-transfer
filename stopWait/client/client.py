#! /bin/python

#Abel Gomez 80602216
#02/10/2018
#Client.py, is a program which silumates the communication between a server and a client.
#It uses datagrams to transfer data to the server. It has two main fucntions: get and put.
#The function get request a file from the server, the file is saved in a local copy.
#    Errors: If the files doesn't exists the server will send an error message.
#The function put sends a request to the server to save a new file or an existing file. 
#Parameters: server address,  following the following format: host:port
#If a package is lost or delayed the client will implement a retransmit-on-timeout policy. 

import sys, re, os
from socket import *
from select import *

#Global variables

serverAddr = ('localhost', 50000)                                 #default server address
lastPacket = 0
#define header attributes.
pckType = bytearray()                                                    #packet type
pckSeq = bytearray()                                                       #sequence number
clientSocket = socket(AF_INET, SOCK_DGRAM)                        #socket to communicate
packet = bytearray()                                              #packet to send
header = bytearray()                                              #packet's header
message = bytearray()                                             #packet's data block
mode = 'u'                                                        #client mode, can be get or put
connection = 0                                                    #identify connection status
                                                                  #values: 0 = not active, 1 = active
verbose = 0                                                       #verbose mode
fileName = ""                                                     #file to request
pckDic = {}                                                       #dictionary to save data blocks
totalPck = 0
GET = 'G'
PUT = 'P'
ACK = 'A'
DTA = 'D'
FIN = 'F'
ERR = 'E'
#packetToServer = bytearray()

def sendAck():
    global pckDic
    global pckSeq
    global lastPacket
    global pckToServer

    #figure out if we receive a valid packet        
    expectedPck = lastPacket + 1
    if expectedPck == pckSeq:

        #send ack for all packages
        header = bytearray([ACK, pckSeq])
        msgToServer = bytearray("ack", 'utf-8')
        pckToServer = header+msgToServer
        if verbose: print "Packet to Server: %c%d%s" % (pckToServer[0], pckToServer[1], pckToServer[2:])
        #clientSocket.sendto(pckToServer, serverAddr)
    
    #figure out if we receive a valid packet        
    #expectedPck = lastPacket + 1
        print "ex: %d" % expectedPck
        print "las: %d" % lastPacket
    #if expectedPck == pckSeq:
        pckDic[pckSeq] = message
        lastPacket = pckSeq
        clientSocket.sendto(pckToServer, serverAddr)
        if verbose: print "key: %d, message: %s" % (pckSeq, pckDic[pckSeq])
    else:
        if verbose: print "Invalid packet, do nothing"
    
def sendFirstMsg():
    global lastPacket 
    global pckToServer

    if mode == 'g':
        header = bytearray([GET, 0])
        #msgToServer = fileName
       # pckToServer = header+msgToServer
       # if verbose: print "Full packet: %c%d%s" % (pckToServer[0], pckToServer[1], pckToServer[2:])
       # clientSocket.sendto(pckToServer, serverAddr)
       # lastPacket = 0
        #sys.exit(1)
    else:
        header = bytearray([PUT, 0])
        #msgToServer = fileName

    msgToServer = fileName
    pckToServer = header+msgToServer
    if verbose: print "Full packet: %c%d%s" % (pckToServer[0], pckToServer[1], pckToServer[2:])
    clientSocket.sendto(pckToServer, serverAddr)
    lastPacket = 0


#display correct usage of parameters
def usage():
    print """usage: %s \n
    Option                         Default             Description
    [--serverAddr host:port]       localhost:50001     Server name and port
    [--put or -p file Name]                            File name to send, must exists on current directory
    [--get or -g file Name]                            File name to get from server
    [--verbose or -v]              off                 Verbose Mode
    [--help or -h]                                     Print usage """% sys.argv[0]
    sys.exit(1)

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
    
#function procHeader, this function will create the header of all messages.
#the header is define by two bytes, the first byte is the type: get, put, ack, data, finish, and error.
#the second byte is the sequence of data or ack. all other types have a 0 sequence.
#the header will help us to identify the kind of message that we receive or send from/to the server.
#both values packet type and sequence are represented as hexadecimal.
def procHeader():
    #we want to update global variables
    global pckType
    global header

    #if connection is zero we are sending the first request
    if connection == 0:
        if mode == 'g': 
            pckType = 0x47
        elif mode == 'p':
            pckType = 0x50
    else: 
        if mode == 'g':
            pckType = 0x41 #send ack, type A
       # if 1==2:#lastPck():
       #     pckType = 0x46
       # else:
       #     if mode == 'g': 
                #pckType = 0x41
       #     elif mode == 'p':
       #         pckType = 0x44
            
    #transform type and header into an array of bytes
    header = bytearray([pckType, pckSeq])
    if verbose: print "packet's header, type: %c, seq: %d" % (header[0], header[1])

#procPckData, this function will create the body of our packet. The client is able to send three types of packages
#if in get mode, it will send an ack for each message received.
#if inf put mode, it could send a data packet with the file information, or it could send a finish packet.
#the client can also send the initial request.
def procPckData():    
    #we want to update global variables
    global message
    #local variable
    msg = ""
    #The first message is always the file name
    if connection == 0:
        msg = fileName
    else:
        if mode == 'g':
            msg = "ack"
    #if mode == 'g':
    #    if connection == 0:
    #        msg = fileName
    #    else:
    #        msg = "ack"
    print mode
    message = bytearray(msg, 'utf-8')
    if verbose: print "packet's message: %s" % message

#function sendMsg, this function will be on charge of sending all message to the server.
#the function will check the mode and connection status, based on those values it will initialize a new connection
#or it will continue with the current conection.
def sendMsg():
    #we want to update global variables
    global packet
    global connection

    #process header
    procHeader()
    #process message
    procPckData()
    #concatenate header and message
    packet = header+message
    if verbose: print "Full packet: %c%d%s" % (packet[0], packet[1], packet[2:])
    
    #send message to server
    clientSocket.sendto(packet, serverAddr)
    connection = 1
    
def sendNextBlock():
    global totalPacket
    global pckDic
    global pckSeq
    global pckToServer
    global lastPacket

    if pckSeq == 0:
        header = bytearray([DTA, 1])
        inFile = open(fileName)
        text = inFile.read()
        textArray = bytearray(text, 'utf-8')
        numberOfPackets = len(textArray)/100
        if len(textArray) % 100 == 0:
            totalPacket = numberOfPackets
        else:
            totalPacket = numberOfPackets + 1
        stIndex = 0
        endIndex = 100
        seqNum = 1
        for packet in range(1, totalPacket):
            if packet == 1:
                pckDic[seqNum] = textArray[0:endIndex]
            else:
                pckDic[seqNum] = textArray[stIndex:endIndex]
            seqNum += 1
            stIndex = endIndex
            endIndex += 100
        pckDic[seqNum] = textArray[stIndex:]
        pckToServer = header+pckDic[1]
        lastPacket = 1
        clientSocket.sendto(pckToServer, serverAddr)
        print "printat se 0 pack: %s" % pckToServer
    elif pckSeq == totalPacket:
        header = bytearray([FIN, 255])
        msg = bytearray("I'm Done", 'utf-8')
        pckToServer = header+msg
        clientSocket.sendto(pckToServer, serverAddr)
    elif pckSeq == 255:
        sys.exit(1)
    else:
        expectedPck = lastPacket
        print "ex: %d" % expectedPck
        print "la: %d"  % lastPacket
        if expectedPck == pckSeq:
            pckSeq +=1
            header = bytearray([DTA, pckSeq])
            pckToServer = header+pckDic[pckSeq]
            print "print pack: %s, exp %d" % (pckToServer, expectedPck)
            lastPacket = pckSeq
            clientSocket.sendto(pckToServer, serverAddr)

def processMsg(sock):
    global pckSeq
    global pckType
    global message
    global lastPacket
    global pckDic
    
    #retreive packet from server
    returnMsg, serverAddrPort = sock.recvfrom(2048)
    if verbose: print "Packet received from server: %s, seq: %d" % (returnMsg[2:], ord(returnMsg[1]))
    
    #strip packet
    pckType = returnMsg[0]
    pckSeq = ord(returnMsg[1])
    message = returnMsg[2:] 

    #save last packet sequence
    #lastPacket = pckSeq

    if pckType == DTA:
        sendAck()
    elif pckType == FIN:
        print "End of file, creating local copy....." 
        outFile = open(fileName, 'w+')
        for line in pckDic.keys():
            outFile.write('%s' % pckDic[line])
        print "FIle created in current directory: %s" % fileName
        sys.exit(1)
    elif pckType == ACK:
        sendNextBlock()

    
###Main logic start here###
#verify parms
if mode == 'u':
    print "Incorrect use of client, you need to use get or put function"
    usage()
    sys.exit(1)
    
sendFirstMsg()
#############test logic
#message = "hello from client"
readSockFunc = {}
writeSockFunc = {}
errorSockFunc = {}
timeout =  .1
readSockFunc[clientSocket] = processMsg 

#clientSocket.sendto(message, serverAddr)
print "ready to communicate"
while 1:
    readRdySet, writeRdySet, errorRdySet = select(readSockFunc.keys(), writeSockFunc.keys(), errorSockFunc.keys(), timeout)
    if not readRdySet and not writeRdySet and not errorRdySet:
        print "timeout: no events"
        #ADD LOGIC TO KILL CLIENT AFTER X TIMES OF RESEND
        clientSocket.sendto(pckToServer, serverAddr)
        if verbose: print "Packet to Server on resend: %c%d%s" % (pckToServer[0], pckToServer[1], pckToServer[2:])
    for sock in readRdySet:
        readSockFunc[sock](sock)
#clientSocket.sendto(message, serverAddr)
#returnMsg, serverAddrPort = clientSocket.recvfrom(2048)
#print "Return Msg: %s" % (repr(returnMsg))
