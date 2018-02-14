# udp demo simple select server -- Adrian Veliz, modified from code by Eric Freudenthal
import sys, os
from socket import *
from select import select
from enum import Enum

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
        
def sendData():
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
                    #print seqNum
                    #print "%s" % packetDic[80]
                    #print "%s" % packetDic[81]

        #sent response to client,
        #check if we are done, if not send next packet
        if pckSeq == totalPck:
                header = bytearray([0x46, 99])
                msg = bytearray("I'm Done", 'utf-8')
                pckToClient = header+msg
                sock.sendto(pckToClient, clientAddrPort)
        else:
                pckSeq += 1
                header = bytearray([0x44, pckSeq])
                pckToClient = header+packetDic[pckSeq]
                sock.sendto(pckToClient, clientAddrPort)

def sendAck():
        global totalPck
        global packetDic
        global pckSeq
        #send ack for all packages
        header = bytearray([0x41, pckSeq])
        msg = bytearray("ack", 'utf-8')
        pckToClient = header+msg
        sock.sendto(pckToClient, clientAddrPort)
        if pckType == 'D': #save packet to dictionary
                #figure out if we receive a valid packet
                expectedPacket = lastPacket + 1
                if expectedPacket == pckSeq:
                        packetDic[pckSeq] = message
                else:
                        print "Duplicate Packat Discarded"
        for key in packetDic.keys():
                print "key: %d, message: %s" % (key, packetDic[key])

        
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
                print "Packet: %c%d%s" % (clientPacket[0], ord(clientPacket[1]), clientPacket[2:])

        #save las packet sequence
        lastPacket = pckSeq
        
        #strip packet
        pckType = clientPacket[0]
        pckSeq = ord(clientPacket[1]) #convert sequence to number
        message = clientPacket[2:]
        if verbose:
            print "Packet type: %c" % pckType
            print "Packet seq: %d" % pckSeq
            print "Message: %s" % message
        
        #identify packet type
        if pckType ==  GET or pckType == ACK:
                sendData()
        elif pckType == PUT or pckType == DTA or pckType == FIN:
               sendAck() 
    
    
	
#### Main Logic starts here ###
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(upperServerAddr)
serverSocket.setblocking(False)

readSockFunc = {}               # dictionaries from socket to function 
writeSockFunc = {}
errorSockFunc = {}
timeout =  10                    # seconds

readSockFunc[serverSocket] = processClientMessage

##TODO functionality to change timeout on fly
print "ready to receive"
while True:
	readRdySet, writeRdySet, errorRdySet = select(readSockFunc.keys(),
                                                      writeSockFunc.keys(), 
                                                      errorSockFunc.keys(),
                                                      timeout)
        if not readRdySet and not writeRdySet and not errorRdySet:
                print "timeout: no events"
	for sock in readRdySet:
                readSockFunc[sock](sock)

