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
totalPck= 0                                           #number of packets that we need to send to client.
packetDic = {}                                         #directory to save all pcks from file
clientAddrPort = 50005
lastPacket = 0
verbose = 1                                                      #verbose mode
GET = 'G'                                                        #macro definitions to identify packages
PUT = 'P'
ACK = 'A'
DTA = 'D'
FIN = 'F'
ERR = 'E'
        
def sendNextBlock():
        global totalPck
        global packetDic
        global pckSeq
        if pckSeq == 0:
            #verify files exists
            if not os.path.exists(message):
                    print "ERROR: file requested by client do not exists"
                    print "SENT ERROR MESSAGE" #NEED TO IMPLEMENT ERROR PACKET
            else:
                    inFile = open(message)
                    text = inFile.read()
                    textArray = bytearray(text, 'utf-8')
                    numPcks = len(textArray)/100
                    if (len(textArray) % 100) == 0:
                            totalPck = numPcks
                    else:
                            totalPck = numPcks + 1
                    #print totalPck
                    stIndex = 0
                    endIndex = 100
                    seqNum = 1
                    for packet in range(1, totalPck):
                            if packet == 1:
                                    packetDic[seqNum] = textArray[0:endIndex]
                            else:
                                    packetDic[seqNum] = textArray[stIndex:endIndex]
                            seqNum += 1
                            stIndex = endIndex
                            endIndex += 100
                    packetDic[seqNum] = textArray[stIndex:]

        #sent response to client,
        #check if we are done, if not send next packet
        if pckSeq == totalPck:
                header = bytearray([FIN, 255]) #bytes only allow a range of 0 <= x < 256
                msg = bytearray("I'm Done", 'utf-8')
                pckToClient = header+msg
                sock.sendto(pckToClient, clientAddrPort)
        else:
                pckSeq += 1
                header = bytearray([DTA, pckSeq])
                pckToClient = header+packetDic[pckSeq]
                sock.sendto(pckToClient, clientAddrPort)
                if verbose: print "key: %d, message: %s" % (pckSeq, packetDic[pckSeq])

def sendAck():
        global totalPck
        global packetDic
        global pckSeq
        global lastPacket
        global fileName

        #send ack for all packages
        header = bytearray([ACK, pckSeq])
        msg = bytearray("ack", 'utf-8')
        pckToClient = header+msg
        sock.sendto(pckToClient, clientAddrPort)
        
        print "SEQ %d" % pckSeq
        print "last %d" % lastPacket


        if pckType == PUT:
                fileName = message
        elif pckType == DTA: #save packet to dictionary
                #figure out if we receive a valid packet
                expectedPacket = lastPacket + 1
                if expectedPacket == pckSeq:
                        packetDic[pckSeq] = message
                        #save las packet sequence
                        lastPacket = pckSeq
                else:
                        if verbose: print "Invalid Packet Discarded"
                #if verbose: print "key: %d, message: %s" % (pckSeq, packetDic[pckSeq])
        elif pckType == FIN:
                if lastPacket == 255:
                        if verbose: print "Invalid Packet Discarded"
                else:
                        outFile = open(fileName, 'w+')
                        for line in packetDic.keys():
                                outFile.write('%s' % packetDic[line])
                        lastPacket = pckSeq


        
#processClientMessage, the function will handle all incoming packages
#It identifies the type of packet that the client sent, and it process the different responses
def processClientMessage(sock):
        #Global variables to control de sequence of packages
        global pckType
        global pckSeq
        global message
        global clientAddrPort
        global lastPacket

        #get client's packet
        clientPacket, clientAddrPort = sock.recvfrom(2048)
        if verbose:
                print "From: %s " % (repr(clientAddrPort)) 

        #strip packet
        pckType = clientPacket[0]
        pckSeq = ord(clientPacket[1]) #convert sequence to number
        message = clientPacket[2:]
        if verbose:
            print "Packet type: %c" % pckType
            print "Packet seq: %d" % pckSeq
            print "Message: %s" % message
        
        #identify packet type
        if pckType == GET or pckType == ACK:
                #sys.exit(1)
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
while 1:
	readRdySet, writeRdySet, errorRdySet = select(readSockFunc.keys(),
                                                      writeSockFunc.keys(), 
                                                      errorSockFunc.keys(),
                                                      timeout)
        if not readRdySet and not writeRdySet and not errorRdySet:
                print "timeout: no events"
	for sock in readRdySet:
                readSockFunc[sock](sock)

