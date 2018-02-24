#Abel Gomez 80602216
#########################################################################################
#########################################################################################
# Program server.py                                                                     #
# Description: The server responses datagram from a client; it implements               # 
#              a stop-and-wait protocol.                                                # 
#              The server implements a retransmit on duplicate policy                   # 
#              The server has a verbose mode which prints to console all actions        #
# How to use: python server.py                                                          #
#                                                                                       #
#  ----------------     Modification Log ----------------                               #
#  Date          Name            Description                                            #
# --------------------------------------------------------------------------------------#
# 02/22/18      Abel Gomez       Initial Creation                                       #
#########################################################################################
#########################################################################################

import sys, os
from socket import *
from select import select

serverAddr = ("", 50001)           # any addr, port 50,000
pckType = bytearray()              #packet type
pckSeq = bytearray()               #sequence to identify active packet
message = bytearray()              #message to send
sequenceBlock = bytearray()        #sequence number, this variables is not currently being use
totalPacket= 0                     #number of packets that we need to send to client.
packetDic = {}                     #directory to save all pcks from file
clientAddrPort = 50005             #dummy client port
lastPacket = '0'                   #identify which was the last sequence that we got
verbose = 1                        #verbose mode
fileName = ""                      #file to proces
activePacket = {}                  #dictionary to keep track of active packets
timeoutCount = 0                   #determine if client is down
GET = 'G'                          #macro definitions to identify packages
PUT = 'P'
ACK = 'A'
DTA = 'D'
FIN = 'F'
ERR = 'E'

#Function: cleanUp
#Description: It may be the case where the client is down and the server is no getting any response back
#             to avoid a infinite wait, the server will reset teh connection after 5 timeouts. 
def cleanUp():
        #global variables
        global inFile
        global outFile
        global fileName
        global lastPacket
        global activePacket
        global timeoutCount
        global pckType

        #do a clean up of all objects
        if pckType == ACK:
                inFile.close()
        elif pckType == DTA:
                outFile.close()
        fileName = ""
        lastPacket ='0'
        activePacket = {}
        timeoutCount = 0
        if verbose: print "Refresh, ready to receive"

#Function: openFile
#Description: open requested file, the server needs to identify which file the client requested
#             and it needs to process it to get all data blocks.
def openFile():
        #global variables
        global totalPacket
        global packetDic
        global pckSeq
        global inFile

        #verify files exists, if not send error packet to client
        if not os.path.exists(message):
                if verbose: print "ERROR: file requested by client do not exists"
                header = bytearray([ERR, '0'])
                msg = "incorrect file name my dear child"
                pckToClient = header+bytearray("00000", 'utf-8')+msg
                sock.sendto(pckToClient, clientAddrPort)
                return 0
        else:
                #open file
                inFile = open(message)
                text = inFile.read()
                textArray = bytearray(text, 'utf-8')

                #if file is bigger than 10,000,000Bytes, send error message
                #the protocol can not handle really big packets
                if len(textArray) > 10000000:
                    if verbose: print "ERROR: file bigger than maximum size"
                    header = bytearray([ERR, '0'])
                    msg = "incorrect file my dear child"
                    pckToClient = header+bytearray("00000", 'utf-8')+msg
                    sock.sendto(pckToClient, clientAddrPort)
                    return 0
                    
                #if the size fits the protocol, then split the file in 100 bytes  blocks
                numPcks = len(textArray)/100
                if (len(textArray) % 100) == 0:
                        totalPacket = numPcks
                else:
                        totalPacket = numPcks + 1

                #create directory and save data blocks
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
        
#Function: sendNextBlock
#Description: send next block or FIN packet
#             the client sends acks for each data block that it receives 
#             the server needs to identify which block it needs to send next or if FIN packet is required
def sendNextBlock():
        #global variables
        global activePacket
        global sequenceBlock
        global nextBlock

        #if we got a get request, open file and send first block
        if pckType == GET: 
            if openFile():
                #send first data block
                header = bytearray([DTA, '1'])
                pckToClient = header+bytearray("00001", 'utf-8')+packetDic[1]
                sock.sendto(pckToClient, clientAddrPort)
                if verbose: print "key: %c, message: %s" % (pckSeq, packetDic[1])

                #identify active packet
                activePacket[0] = '1'
                activePacket[1] = 1

        #if we got an ack, then we need to send the next block or the FIN packet
        elif pckType == ACK:
            #figure out if we got a valid ack 
            if pckSeq != activePacket[0]:
                if verbose: print "Incorrect acknowledge received"
                #send previous block
                #the server retransmit on duplicate, this mean that it responses to all packets
                header = bytearray([DTA, activePacket[0]])
                sequence = "%05d" % nextBlock
                sequenceBlock = bytearray(sequence)
                pckToClient = header+sequenceBlock+packetDic[activePacket[1]]
                sock.sendto(pckToClient, clientAddrPort)
            else:
                #figure out if we finish
                if activePacket[1] == totalPacket:
                    header = bytearray([FIN, 'F'])
                    pckToClient = header+bytearray("00000", 'utf-8')+bytearray("I'm Done", 'utf-8')
                    if verbose: print "Packet sent to Client: %c%c%s" % (pckToClient[0], pckToClient[1], pckToClient[2:])
                    sock.sendto(pckToClient, clientAddrPort)
                    activePacket[1] = totalPacket
                #if still more packets, send next one and update active packet
                else:
                    nextBlock = activePacket[1] + 1
                    if activePacket[0] == '0':
                        activePacket[0] = '1'
                    else:
                        activePacket[0] = '0'
                    activePacket[1] = nextBlock
                    #create header
                    header = bytearray([DTA, activePacket[0]])
                    sequence = "%05d" % nextBlock #the sequence number is useless on this protocol
                    sequenceBlock = bytearray(sequence)
                    pckToClient = header+sequenceBlock+packetDic[nextBlock]
                    if verbose: print "Packet sent to Client: %c%c%s" % (pckToClient[0], pckToClient[1], pckToClient[2:])
                    sock.sendto(pckToClient, clientAddrPort)

                    
#Function: sendAck
#Description: the server ack any packet that it receives, this due to the policy retransmist on duplicate
#             this function ack all data blocks
def sendAck():
        #global variables
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

        #if we got the first request, open output file
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
                    lastPacket = pckSeq
        
#Function: processClientMessage
#Description: the function will handle all incoming packages
#             It identifies the type of packet that the client sent, and it process the different responses
def processClientMessage(sock):
        #Global variables to control de sequence of packages
        global pckType
        global pckSeq
        global message
        global clientAddrPort
        global timeoutCount
        global sequenceBlock

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
        timeoutCount = 0
        
        #identify packet type
        if pckType == GET or pckType == ACK:
                sendNextBlock()
        elif pckType == PUT or pckType == DTA or pckType == FIN:
               sendAck() 
    
    
	
#### Main Logic starts here ###
#define server to connect
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(serverAddr)
serverSocket.setblocking(False)

readSockFunc = {}               # dictionaries from socket to function 
writeSockFunc = {}
errorSockFunc = {}
timeout =  5                    # seconds

readSockFunc[serverSocket] = processClientMessage

print "ready to receive"
while True:
	readRdySet, writeRdySet, errorRdySet = select(readSockFunc.keys(),
                                                      writeSockFunc.keys(), 
                                                      errorSockFunc.keys(),
                                                      timeout)
        if not readRdySet and not writeRdySet and not errorRdySet:
                #if we reach the a fifth time without a client's reponse
                #assume client is down.
                if timeoutCount == 5:
                        cleanUp()
                print "timeout: no events"
                timeoutCount += 1
	for sock in readRdySet:
                readSockFunc[sock](sock)
