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

serverAddr = ('localhost', 50001)                                 #default server address
#lastPacket = 0
#define header attributes.
pckType = bytearray()                                                    #packet type
pckSeq = bytearray()                                                       #sequence number
clientSocket = socket(AF_INET, SOCK_DGRAM)                        #socket to communicate
packet = bytearray()                                              #packet to send
header = bytearray()                                              #packet's header
message = bytearray()                                             #packet's data block
#mode = 'u'                                                        #client mode, can be get or put
connection = 0                                                    #identify connection status
                                                                  #values: 0 = not active, 1 = active
#verbose = 0                                                       #verbose mode
#fileName = ""                                                     #file to request
#pckDic = {}                                                       #dictionary to save data blocks
#totalPck = 0
GET = 'G'
PUT = 'P'
ACK = 'A'
DTA = 'D'
FIN = 'F'
ERR = 'E'
#packetToServer = bytearray()

#valid variables that i already check
mode = 'u'                                                        #client mode, can be get or put
fileName = ""                                                     #file to request
verbose = 0                                                       #verbose mode
activePacket = {}                                                 #track the last packet that we sent
                                                                  #index 0 = sequence No '0' or '1'
                                                                  #index 1 = last data block sent
pckDic = {}                                                      #dic to hold data blocks
totalPacket = 0                                                   #total number of packets
lastPacket = '1'

def sendAck():
    global activePacket
    global pckSeq
    global lastPacket
    global pckToServer
    global outFile

    #figure out if we receive a valid packet
    if lastPacket == pckSeq:
            if verbose: print "Invalid Packet"
    else:
            outFile.write('%s' % message)
            lastPacket = pckSeq
            #send ack 
            header = bytearray([ACK, pckSeq])
            msg = bytearray("ack", 'utf-8')
            pckToServer = header+msg
            clientSocket.sendto(pckToServer, serverAddr)
    #sys.exit(1)

def openFile():
    global pckDic
    global totalPacket

    inFile = open(fileName, 'r')
    text = inFile.read()
    textArray = bytearray(text, 'utf-8')
    numberOfPackets = len(textArray)/100
    if len(textArray) % 100 == 0:
        totalPacket = numberOfPackets
    else:
        totalPacket = numberOfPackets + 1
    print "TP: %d" % totalPacket
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

def sendFirstMsg():
    global lastPacket 
    global pckToServer
    global activePacket
    global outFile

    if mode == 'g':
        header = bytearray([GET, '0'])
        outFile = open(fileName, 'w+')
        lastPacket = '0'
    else:
        header = bytearray([PUT, '0'])
        activePacket[0] = '0'
        activePacket[1] = 0
        openFile()

    msgToServer = fileName
    pckToServer = header+msgToServer
    if verbose: print "Packet sent to Server: %c%c%s" % (pckToServer[0], pckToServer[1], pckToServer[2:])
    clientSocket.sendto(pckToServer, serverAddr)


def sendNextBlock():
    global pckDic
    global pckToServer
    global activePacket
    global totalPacket

    if pckSeq == 'F': #ack of FIN exit client
        if verbose: print "FIN ack, finish communication"
        #inFile.close()
        sys.exit(1)
    if pckSeq != activePacket[0]:
        if verbose: print "Incorrect acknowledge received"
    else:
        if activePacket[1] == totalPacket:
            header = bytearray([FIN, 'F'])
            pckToServer = header+bytearray("I'm Done", 'utf-8')
            if verbose: print "Packet sent to Server: %c%c%s" % (pckToServer[0], pckToServer[1], pckToServer[2:])
            clientSocket.sendto(pckToServer, serverAddr)
            activePacket[1] = totalPacket
        else:
            nextBlock = activePacket[1] + 1
            #print "NB: %d" % nextBlock 
            if activePacket[0] == '0':
                activePacket[0] = '1'
            else:
                activePacket[0] = '0'
            activePacket[1] = nextBlock
            #create header
            header = bytearray([DTA, activePacket[0]])
            pckToServer = header+pckDic[nextBlock]
            if verbose: print "Packet sent to Server: %c%c%s" % (pckToServer[0], pckToServer[1], pckToServer[2:])
            clientSocket.sendto(pckToServer, serverAddr)
    
def processMsg(sock):
    global pckSeq
    global pckType
    global message
    global lastPacket
    global pckDic
    
    #retreive packet from server
    returnMsg, serverAddrPort = sock.recvfrom(2048)
    if verbose: print "Packet received from server: %s, seq: %c" % (returnMsg[2:], ord(returnMsg[1]))
    
    #strip packet
    pckType = returnMsg[0]
    pckSeq = returnMsg[1]
    message = returnMsg[2:] 

    if pckType == DTA:
        sendAck()
    elif pckType == FIN:
        print "End of file, creating local copy....." 
        print "File created in current directory: %s" % fileName
        outFile.close()
        sys.exit(1)
    elif pckType == ACK:
        sendNextBlock()

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
    
###Main logic start here###
#verify parms
if mode == 'u':
    print "Incorrect use of client, you need to use get or put function"
    usage()
    sys.exit(1)
    
print "ready to communicate"
sendFirstMsg()
readSockFunc = {}
writeSockFunc = {}
errorSockFunc = {}
timeout =  5
readSockFunc[clientSocket] = processMsg 

#clientSocket.sendto(message, serverAddr)
#print "ready to communicate"
while True:
    readRdySet, writeRdySet, errorRdySet = select(readSockFunc.keys(), writeSockFunc.keys(), errorSockFunc.keys(), timeout)
    if not readRdySet and not writeRdySet and not errorRdySet:
        print "timeout: no events"
        #ADD LOGIC TO KILL CLIENT AFTER X TIMES OF RESEND
        clientSocket.sendto(pckToServer, serverAddr)
        if verbose: print "Packet to Server on resend: %c%c%s" % (pckToServer[0], pckToServer[1], pckToServer[2:])
    for sock in readRdySet:
        readSockFunc[sock](sock)
