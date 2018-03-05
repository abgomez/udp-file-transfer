import sys, os
from socket import *
from select import select

serverAddr = ("", 50001)           # any addr, port 50,001
packetType = bytearray()              #packet type
packetSequence = bytearray()               #sequence to identify active packet
packetMessage = bytearray()              #message to send
sequenceBlock = bytearray()        #sequence number, this variables is not currently being use
totalPacket= 0                     #number of packets that we need to send to client.
packetDic = {}                     #directory to save all pcks from file
clientAddrPort = 50005             #dummy client port
lastPacket = '0'                   #identify which was the last sequence that we got
verbose = 1                        #verbose mode
fileName = ""                      #file to proces
activePacket = {}                  #dictionary to keep track of active packets
timeoutCount = 0                   #determine if client is down
windowSize = 5
sequence = 0
packetWindow = {}
lastReceive = 0
GET = 'G'                          #macro definitions to identify packages
PUT = 'P'
ACK = 'A'
DTA = 'D'
FIN = 'F'
ERR = 'E'

#Function: openFile
#Description: open requested file, the server needs to identify which file the client requested
#             and it needs to process it to get all data blocks.
def openFile():
        #global variables
        global packetMessage
        global totalPacket
        global packetDic
        #global pckSeq
        global inFile

        #verify files exists, if not send error packet to client
        if not os.path.exists(packetMessage):
                packetType = bytearray(ERR, 'utf-8') 
                packetSequence = bytearray('0'+',', 'utf-8')
                packetMessage = bytearray("incorrect file name my dear child", 'utf-8')
                packetToClient = packetType+packetSequence+packetMessage
                sock.sendto(packetToClient, clientAddrPort)
                if verbose: print "ERROR: file requested by client do not exists"
                return 0
        else:
                #open file
                inFile = open(packetMessage)
                text = inFile.read()
                textArray = bytearray(text, 'utf-8')

                #if file is bigger than 10,000,000Bytes, send error message
                #the protocol can not handle really big packets
                #if len(textArray) > 10000000:
                #    if verbose: print "ERROR: file bigger than maximum size"
                #    header = bytearray([ERR, '0'])
                #    msg = "incorrect file my dear child"
                #    pckToClient = header+bytearray("00000", 'utf-8')+msg
                #    sock.sendto(pckToClient, clientAddrPort)
                #    return 0
                    
                #split file in 100 bytes  blocks
                numPcks = len(textArray)/100
                if (len(textArray) % 100) == 0:
                        totalPacket = numPcks
                else:
                        totalPacket = numPcks + 1

                #create dictionary and save data blocks
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
     global packetType 
     global windowSize
     global sequence
     global packetWindow
     global packetMessage
     global packetSequence
     global totalPacket
     global lastReceive
     global lastAckRec
     global tmpWindowIndex

     global activePacket
     global sequenceBlock
     global nextBlock

     #if we got a get request, open file and send first block
     if packetType == GET: 
         if openFile():
             #send first window, window size = 5
             sequence = 1
             sequenceStr = "%s" % sequence
             windowIndex = 0
             for index in range(windowSize):
                 #create packet
                 packetType = bytearray(DTA, 'utf-8')
                 sequenceStr = "%s" % sequence
                 packetSequence = bytearray(sequenceStr+',', 'utf-8')
                 packetMessage = packetDic[sequence]
                 packetToClient = packetType+packetSequence+packetMessage

                 #update window and sequence
                 packetWindow[windowIndex] = sequence
                 sequence += 1
                 windowIndex += 1

                 sock.sendto(packetToClient, clientAddrPort)
                 if verbose: print "Packet To client:  %s" % packetToClient

     #if we got an ack, then we need to send the next block or the FIN packet
     elif packetType == ACK:
         if verbose: print "Window: %s" % packetWindow
         #figure out if we got the expected  ack 
         if int(packetSequence) == packetWindow[0]:
             lastReceive = int(packetSequence)
             #figure out if we finish
             if int(packetSequence)+(windowSize-1) == totalPacket:
                 #create packet
                 packetType = bytearray(FIN, 'utf-8')
                 packetSequence = bytearray('0'+',', 'utf-8')
                 packetMessage = bytearray("Last packet", 'utf-8')
                 packetToClient = packetType+packetSequence+packetMessage

                 sock.sendto(packetToClient, clientAddrPort)
                 if verbose: print "Packet To client:  %s" % packetToClient

                 #update window
                 for index in range(windowSize-1):
                     packetWindow[index] = packetWindow[index+1]
                 packetWindow[windowSize-1] = 'F'

             elif int(packetSequence)+(windowSize-1) > totalPacket:
                 if verbose: print "We already sent all packets, do nothing"
                 #update window
                 for index in range(windowSize-1):
                     packetWindow[index] = packetWindow[index+1]
                 packetWindow[windowSize-1] = 0
             else:    
                 #send next block
                 lastPacketSent = packetWindow[4]
                 print "sequence: %d " % (lastPacketSent + 1)
                 #print "sequence: %d " % sequence
                 #nextBlock = sequence + 1

                 #create packet
                 packetType = bytearray(DTA, 'utf-8')
                 sequenceStr = "%s" % (lastPacketSent + 1)
                 #sequenceStr = "%s" % sequence 
                 packetSequence = bytearray(sequenceStr+',', 'utf-8')
                 packetMessage = packetDic[sequence]
                 packetToClient = packetType+packetSequence+packetMessage

                 sock.sendto(packetToClient, clientAddrPort)
                 if verbose: print "Packet To client:  %s" % packetToClient
                 #sequence = nextBlock

                 #update window
                 for index in range(windowSize-1):
                     packetWindow[index] = packetWindow[index+1]
                 packetWindow[windowSize-1] = lastPacketSent+1
                 #packetWindow[windowSize-1] = sequence

                 sequence += 1
         elif lastReceive > int(packetSequence):
             if verbose: print "Assume Delayed Packet, do nothing" 
         elif int(packetSequence) == lastReceive:
             print "TDO" #TODO

         #we got a cumulative ack
         else:
             sequenceRec = int(packetSequence)
             packetDiff = 0                    #this difference will help us to identify how many packets do we need to send
             windowIndex = 0
             lastReceive = int(packetSequence)

             #update widow to always have 5 packets in transit
             for index in range(windowSize):
                 if packetWindow[index] == sequenceRec:
                     packetDiff = index       #the client received, this many packets
             windowIndex = packetDiff
             if windowIndex == 4:
                 tmpWindowIndex = 0
             else:
                 tmpWindowIndex = windowSize - (windowIndex + 1)
             #packetDiff = windowSize - (packetDiff + 1)
             #packetDiff = indowSize - (packetDiff + 1)
             lastPacketSent = packetWindow[4]
             if lastPacketSent == 'F':
                 if verbose: print "We are done, just ignore the ack"
 
             else:
                 print "window index: %d" % windowIndex
                 print "difference: %d" % packetDiff
                 print "lastPacket: %d" % lastPacketSent

                 #update window
                 #tempDiff = packetDifff
                 loopRange = windowSize - (windowIndex+1)
                 for index in range(loopRange):
                     if windowIndex <= 3:
                         windowIndex += 1
                     packetWindow[index] = packetWindow[windowIndex]

                 if verbose: print "Window: %s" % packetWindow

                 #create next set of packets
                 nextPacket = lastPacketSent + 1
                 for packet in range(packetDiff+1):

                 #figure out if we finish
  #               if (nextPacket + windowSize) >= totalPacket:
  #                   #create packet
  #                   packetType = bytearray(FIN, 'utf-8')
  #                   packetSequence = bytearray('0'+',', 'utf-8')
#kik                     packetMessage = bytearray("Last packet", 'utf-8')
#                     packetToClient = packetType+packetSequence+packetMessage
#
#                     sock.sendto(packetToClient, clientAddrPort)
#                     if verbose: print "Packet To client:  %s" % packetToClient
#
                 #    #update window 
                 #    packetWindow[tmpWindowIndex] = 'F'
                 #    tmpWindowIndex += 1
                 #    if verbose: print "Window: %s" % packetWindow

                 #else:
                     #figure out if we finish
                     if nextPacket > totalPacket:
                         #create packet
                         packetType = bytearray(FIN, 'utf-8')
                         packetSequence = bytearray('0'+',', 'utf-8')
                         packetMessage = bytearray("Last packet", 'utf-8')
                         packetToClient = packetType+packetSequence+packetMessage

                         sock.sendto(packetToClient, clientAddrPort)
                         if verbose: print "Packet To client:  %s" % packetToClient
                         if verbose: print "Window: %s" % packetWindow

                         #update window 
                         packetWindow[tmpWindowIndex] = 'F'
                         tmpWindowIndex += 1
                         nextPacket += 1
                         if verbose: print "Window: %s" % packetWindow
                     else:
                         #create packet
                         packetType = bytearray(DTA, 'utf-8')
                         sequenceStr = "%s" % nextPacket
                         packetSequence = bytearray(sequenceStr+',', 'utf-8')
                         packetMessage = packetDic[nextPacket]
                         packetToClient = packetType+packetSequence+packetMessage

                         #update window 
                         packetWindow[tmpWindowIndex] = nextPacket
                         tmpWindowIndex += 1
                         nextPacket += 1

                         sock.sendto(packetToClient, clientAddrPort)
                         if verbose: print "Packet To client:  %s" % packetToClient
                         if verbose: print "Window: %s" % packetWindow
              
         
            
        #       if verbose: print "Incorrect acknowledge received"
        #        #send previous block
        #        #the server retransmit on duplicate, this mean that it responses to all packets
        #        header = bytearray([DTA, activePacket[0]])
        #        sequence = "%05d" % nextBlock
        #        sequenceBlock = bytearray(sequence)
        #        pckToClient = header+sequenceBlock+packetDic[activePacket[1]]
        #        sock.sendto(pckToClient, clientAddrPort)
        #    else:
        #        #figure out if we finish
        #        if activePacket[1] == totalPacket:
        #            header = bytearray([FIN, 'F'])
        #            pckToClient = header+bytearray("00000", 'utf-8')+bytearray("I'm Done", 'utf-8')
        #            if verbose: print "Packet sent to Client: %c%c%s" % (pckToClient[0], pckToClient[1], pckToClient[2:])
        #            sock.sendto(pckToClient, clientAddrPort) #            activePacket[1] = totalPacket #        #if still more packets, send next one and update active packet
        #        else:
        #            nextBlock = activePacket[1] + 1
        #            if activePacket[0] == '0':
        #                activePacket[0] = '1'
        #            else:
        #                activePacket[0] = '0'
        #            activePacket[1] = nextBlock
        #            #create header
        #            header = bytearray([DTA, activePacket[0]])
        #            sequence = "%05d" % nextBlock #the sequence number is useless on this protocol
        #            sequenceBlock = bytearray(sequence)
        #            pckToClient = header+sequenceBlock+packetDic[nextBlock]
        #            if verbose: print "Packet sent to Client: %c%c%s" % (pckToClient[0], pckToClient[1], pckToClient[2:])
        #            sock.sendto(pckToClient, clientAddrPort)

#Function: processClientMessage
#Description: the function will handle all incoming packages
#             It identifies the type of packet that the client sent, and it process the different responses
def processClientMessage(sock):
        #Global variables to control de sequence of packages
        global packetType
        global packetSequence 
        global packetMessage
        global clientAddrPort
        global timeoutCount
        global sequenceBlock
        global resendCount

        #get client's packet
        clientPacket, clientAddrPort = sock.recvfrom(2048)
        if verbose: print "From: %s " % (repr(clientAddrPort)) 
        if verbose: print "Packet: %s " % clientPacket

        #strip packet
        packetType = clientPacket[0]
        #figure out sequence number, remove packet type. we know our sequence starts at index 1
        tempString = "%s" % clientPacket[1:] 
        sequenceIndex = tempString.find(',') # identify where the sequence ends
        packetSequence = tempString[0:sequenceIndex]
        packetMessage = tempString[sequenceIndex+1:]
        #pckSeq = clientPacket[1]
        #sequenceBlock = clientPacket[2:7]
        #message = clientPacket[7:]
        if verbose:
            print "Packet type: %c" % packetType
            print "Packet sequence: %s" % packetSequence 
            print "Message: %s" % packetMessage
        #timeoutCount = 0
        
        #identify packet type
        if packetType == GET or packetType == ACK:
                #if packetType == GET:
                #    if not os.path.exists(packetMessage):
                #        packetType = bytearray(ERR, 'utf-8') 
                #        packetSequence = bytearray('0'+',', 'utf-8')
                #        packetMessage = bytearray("ERROR: file requested by client do not exists", 'utf-8')
                #        packetToClient = packetType+packetSequence+packetMessage
                #        sock.sendto(packetToClient, clientAddrPort)
                #        #TODO cleanUP
                #    else:
                #        openFile()
                #else
                sendNextBlock()
        elif packetType == PUT or packetType == DTA or packetType == FIN:
               print "TODO" #sendAck() 
    
    

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
                        print "TODO" #cleanUp()
                print "timeout: no events"
                timeoutCount += 1
	for sock in readRdySet:
                readSockFunc[sock](sock)
