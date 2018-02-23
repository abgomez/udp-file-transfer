# udp demo simple select server -- Adrian Veliz, modified from code by Eric Freudenthal
import sys, os
from socket import *
from select import select
#from enum import Enum

# default params
upperServerAddr = ("", 50001)   # any addr, port 50,000
#Global variables
pckType = bytearray()
pckSeq = bytearray()
message = bytearray()
sequenceBlock = bytearray()
totalPacket= 0                                           #number of packets that we need to send to client.
packetDic = {}                                         #directory to save all pcks from file
clientAddrPort = 50005
lastPacket = '0'
verbose = 1                                                      #verbose mode
fileName = ""
activePacket = {}
timeoutCount = 0                                                 #determine if client is dead
GET = 'G'                                                        #macro definitions to identify packages
PUT = 'P'
ACK = 'A'
DTA = 'D'
FIN = 'F'
ERR = 'E'

def cleanUp():
        global inFile
        global outFile
        global fileName
        global lastPacket
        global activePacket
        global timeoutCount
        global pckType

        if pckType == ACK:
                inFile.close()
        elif pckType == DTA:
                outFile.close()
        fileName = ""
        lastPacket ='0'
        activePacket = {}
        timeoutCount = 0
        if verbose: print "Refresh, ready to receive"
        #sys.exit(1)

def openFile():
        global totalPacket
        global packetDic
        global pckSeq
        global inFile

        #verify files exists
        if not os.path.exists(message):
                if verbose: print "ERROR: file requested by client do not exists"
                header = bytearray([ERR, '0'])
                msg = "incorrect file name my dear child"
                pckToClient = header+bytearray("00000", 'utf-8')+msg
                sock.sendto(pckToClient, clientAddrPort)
                return 0
        else:
                inFile = open(message)
                text = inFile.read()
                textArray = bytearray(text, 'utf-8')
                if len(textArray) > 10000000:
                    if verbose: print "ERROR: file bigger than maximum size"
                    header = bytearray([ERR, '0'])
                    msg = "incorrect file my dear child"
                    pckToClient = header+bytearray("00000", 'utf-8')+msg
                    sock.sendto(pckToClient, clientAddrPort)
                    return 0
                numPcks = len(textArray)/100
                if (len(textArray) % 100) == 0:
                        totalPacket = numPcks
                else:
                        totalPacket = numPcks + 1
                #print totalPck
                stIndex = 0
                endIndex = 100
                seqNum = 1
                for packet in range(1, totalPacket):
                        if packet == 1:
                                packetDic[seqNum] = textArray[0:endIndex]
                        else:
                                packetDic[seqNum] = textArray[stIndex:endIndex]
                        seqNum += 1
                        stIndex = endIndex
                        endIndex += 100
                packetDic[seqNum] = textArray[stIndex:]
                return 1
        
def sendNextBlock():
        global activePacket
        global sequenceBlock
        global nextBlock

        if pckType == GET: 
            if openFile():
                header = bytearray([DTA, '1'])
                pckToClient = header+bytearray("00001", 'utf-8')+packetDic[1]
                sock.sendto(pckToClient, clientAddrPort)
                if verbose: print "key: %c, message: %s" % (pckSeq, packetDic[1])
                activePacket[0] = '1'
                activePacket[1] = 1
        elif pckType == ACK:
            if pckSeq != activePacket[0]:
                if verbose: print "Incorrect acknowledge received"
                #send previous block
                #create header
                header = bytearray([DTA, activePacket[0]])
                sequence = "%05d" % nextBlock
                sequenceBlock = bytearray(sequence)
                pckToClient = header+sequenceBlock+packetDic[activePacket[1]]
                sock.sendto(pckToClient, clientAddrPort)
            else:
                if activePacket[1] == totalPacket:
                    header = bytearray([FIN, 'F'])
                    pckToClient = header+bytearray("00000", 'utf-8')+bytearray("I'm Done", 'utf-8')
                    if verbose: print "Packet sent to Client: %c%c%s" % (pckToClient[0], pckToClient[1], pckToClient[2:])
                    sock.sendto(pckToClient, clientAddrPort)
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
                    sequence = "%05d" % nextBlock
                    sequenceBlock = bytearray(sequence)
                    pckToClient = header+sequenceBlock+packetDic[nextBlock]
                    if verbose: print "Packet sent to Client: %c%c%s" % (pckToClient[0], pckToClient[1], pckToClient[2:])
                    sock.sendto(pckToClient, clientAddrPort)

def sendAck():
        global totalPck
        global packetDic
        global pckSeq
        global lastPacket
        global fileName
        global activePacket
        global outFile
        global sequenceBlock

        #send ack for all packages
        header = bytearray([ACK, pckSeq])
        msg = bytearray("ack", 'utf-8')
        pckToClient = header+sequenceBlock+msg
        sock.sendto(pckToClient, clientAddrPort)

        if pckType == PUT:
                if fileName == "": #if fileName is empty then we got the first request, if not do nothing
                    fileName = message
                    outFile = open(fileName, 'w+')
                    print outFile
                    lastPacket = '0'
        elif pckType == DTA: #save packet to dictionary
                #figure out if we receive a valid packet
                if lastPacket == pckSeq:
                        if verbose: print "Invalid Packet"
                else:
                        outFile.write('%s' % message)
                        lastPacket = pckSeq
        elif pckType == FIN:
                print "lP: %c" % lastPacket
                if lastPacket != pckSeq: #if the server gets the FIN for first time, if not ignore
                    print "File Created on current Directory %s" % fileName
                    outFile.close()
                    fileName = ""
                    #print "File Created on current Directory %s" % fileName
                    #cleanUp()
                    lastPacket = pckSeq
        
#processClientMessage, the function will handle all incoming packages
#It identifies the type of packet that the client sent, and it process the different responses
def processClientMessage(sock):
        #Global variables to control de sequence of packages
        global pckType
        global pckSeq
        global message
        global clientAddrPort
        global timeoutCount
        global sequenceBlock
        #global lastPacket

        #get client's packet
        clientPacket, clientAddrPort = sock.recvfrom(2048)
        global resendCount
        if verbose:
                print "From: %s " % (repr(clientAddrPort)) 

        #strip packet
        pckType = clientPacket[0]
        pckSeq = clientPacket[1]
        sequenceBlock = clientPacket[2:7]
        message = clientPacket[7:]
        if verbose:
            print "Packet type: %c" % pckType
            print "Packet seq: %c" % pckSeq
            print "Block seq: %s" % sequenceBlock
            print "Message: %s" % message
            #sys.exit(1) 
        timeoutCount = 0
        
        #identify packet type
        if pckType == GET or pckType == ACK:
                sendNextBlock()
        elif pckType == PUT or pckType == DTA or pckType == FIN:
               sendAck() 
    
    
	
#### Main Logic starts here ###
#define server to connect
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(upperServerAddr)
serverSocket.setblocking(False)

readSockFunc = {}               # dictionaries from socket to function 
writeSockFunc = {}
errorSockFunc = {}
timeout =  5                    # seconds

readSockFunc[serverSocket] = processClientMessage

##TODO functionality to change timeout on fly
print "ready to receive"
while True:
	readRdySet, writeRdySet, errorRdySet = select(readSockFunc.keys(),
                                                      writeSockFunc.keys(), 
                                                      errorSockFunc.keys(),
                                                      timeout)
        if not readRdySet and not writeRdySet and not errorRdySet:
                if timeoutCount == 5:
                        cleanUp()
                print "timeout: no events"
                timeoutCount += 1
	for sock in readRdySet:
                readSockFunc[sock](sock)
