#Abel Gomez 80602216
#########################################################################################
#########################################################################################
# Program server.py                                                                     #
# Description: The server responses datagram from a client; it implements               # 
#              a sliding windows protocol.                                              # 
#              The server implements a retransmit on duplicate policy, it identifies    # 
#              if and ack or data block needs to be ignore due to old packets.          #
#              The server has a verbose mode which prints to console all actions        #
# How to use: python server.py                                                          #
#                                                                                       #
#  ----------------     Modification Log ----------------                               #
#  Date          Name            Description                                            #
# --------------------------------------------------------------------------------------#
# 03/08/18      Abel Gomez       Initial Creation                                       #
#########################################################################################
#########################################################################################

import sys, os
from socket import *
from select import select

serverAddr = ("", 50001)           # any addr, port 50,001
packetType = bytearray()           #packet type
packetSequence = bytearray()       #packet sequence
packetMessage = bytearray()        #message to send
totalPacket= 0                     #number of packets that we need to send to client.
packetDic = {}                     #dictionary to save all pcks from file
clientAddrPort = 50005             #dummy client port
verbose = 1                        #verbose mode
fileName = ""                      #file to proces
timeoutCount = 0                   #determine if client is down
windowSize = 5                     #window size, default 5
sequence = 0                       #sequence used to send the first window
packetWindow = {}                  #packet window, defualt size 5
lastReceive = 0                    #variable to identify which was the last data block received
lastAck = 0                        #last acknowledge receive
packetBuffer = {}                  #buffer to temporal save packets
finFlag = 0                        #flag to identify when a FIN packet is receive
GET = 'G'                          #macro definitions to identify packages
PUT = 'P'
ACK = 'A'
DTA = 'D'
FIN = 'F'
ERR = 'E'

#Function: cleanUp
#Description: It may be the case where the client is down and the server is no getting any response back
#             to avoid a infinite wait, the server will reset the connection after 5 timeouts. 
def cleanUp():
    global inFile
    global outFile
    global fileName
    global timeoutCount
    global packetType
    global finFlag
    global sequence
    global lastAck
    global packetBuffer
    global lastReceive
    global packetWindow
    global packetDic
    global packetSequence

    try:
        inFile.close()
    except:
        print "File not Open"

    fileName = ""
    lastAck = 0
    sequence = 0
    finFlag = 0
    packetBuffer = {}
    lastReceive = 0
    packetWindow = {}
    packetDic = {}
    timeoutCount = 0
    packetType = {}
    packetSequence = {}
    if verbose: print "Refresh, ready to receive"

#Function: sendAck
#Description: send an acknowledge after receiving a valid packet, a normal processing is follow if we get
#             the expected ack, if not the data is put into the buffer. acks are cumulative meaning that
#             we only acknowledge the last processed packet.
def sendAck():
     global packetBuffer
     global lastAck
     global packetSequence
     global packetMessage
     global packetDic
     global packetToServer
     global packetType
     global fileName

     #acknowledge the first PUT
     if packetType == PUT:
         fileName = packetMessage
         #create acknowledge
         packetType = bytearray(ACK, 'utf-8')
         packetSequence = bytearray('0'+',', 'utf-8')
         packetMessage = bytearray("ack", 'utf-8') 
         packetToClient = packetType+packetSequence+packetMessage

         sock.sendto(packetToClient, clientAddrPort)
         if verbose: print "Packet sent to client: %s" % packetToClient

     else:
      #identify if we got the expected packet
      nextPacket = lastAck + 1
      if int(packetSequence) == nextPacket:
          if not packetBuffer: #buffer empty process normaly
              #valid packet received, save data and send acknowledge
              packetDic[int(packetSequence)] = packetMessage
              lastAck = int(packetSequence)

              #create acknowledge
              packetType = bytearray(ACK, 'utf-8')
              sequenceStr = packetSequence+','
              packetSequence = bytearray(sequenceStr, 'utf-8')
              packetMessage = bytearray("ack", 'utf-8') 
              packetToClient = packetType+packetSequence+packetMessage

              sock.sendto(packetToClient, clientAddrPort)
              if verbose: print "Packet sent to client: %s" % packetToClient
          else: #we have packets in the buffer, figure out which ones
              #save packet into dic
              packetDic[int(packetSequence)] = packetMessage
  
              #save packets in the buffer and send acknowledge, ack are cumulative
              nextPacket = int(packetSequence) + 1
              #find if we have the packet in the buffer
              while True:
                  if nextPacket in packetBuffer:
                      packetDic[nextPacket] = packetBuffer[nextPacket]
                      del packetBuffer[nextPacket]
                      nextPacket += 1
                  #no more packet send ack of last packet
                  else:
                      #create acknowledge
                      packetType = bytearray(ACK, 'utf-8')
                      tempString = "%s" % (nextPacket - 1)
                      sequenceStr = tempString+','
                      packetSequence = bytearray(sequenceStr, 'utf-8')
                      packetMessage = bytearray("ack", 'utf-8') 
                      packetToClient = packetType+packetSequence+packetMessage
                      lastAck = nextPacket - 1
 
                      sock.sendto(packetToClient, clientAddrPort)
                      if verbose: print "Packet sent to client: %s" % packetToClient
                      break
      else:
     	  #save packets into buffer, packet might be delay
          packetBuffer[int(packetSequence)] = packetMessage

#Function: openFile
#Description: open requested file, the server needs to identify which file the client requested
#             and it needs to process it to get all data blocks.
def openFile():
        #global variables
        global packetMessage
        global totalPacket
        global packetDic
        global inFile
        global fileName

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
                fileName = packetMessage
                inFile = open(packetMessage)
                text = inFile.read()
                textArray = bytearray(text, 'utf-8')

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
#             a full windows needs to be transit all time
#             a few cases can ocurr during transfer
#                  normal processing: we got an expected ack, send next packet in the window
#                  duplicate ack: assume lost packet resend last packet sent
#                  old ack: acks are cumulative, old acks are ignored since we already got a most recent ack
#                  ahead ack: this mean that the ack received is greater than the expected ack. we need send the 
#                             necessary packets to keep a full window in transit.
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

     #if we got a get request, open file and send first block
     if packetType == GET: 
         if openFile():
             #send first window, window size = 5
             sequence = 1
             #sequenceStr = "%s" % sequence
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
             lastReceive = int(packetSequence) #save last receive ack

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
                 for index in range(windowSize-1): #windowSize - 1, we don't want to go over the window
                     packetWindow[index] = packetWindow[index+1]
                 packetWindow[windowSize-1] = 'F' #update last item

             #we already sent all packets
             elif int(packetSequence)+(windowSize-1) > totalPacket:
                 if verbose: print "We already sent all packets, do nothing"
                 #update window
                 for index in range(windowSize-1): #windowSize - 1, we don't want to go over the window
                     packetWindow[index] = packetWindow[index+1]
                 packetWindow[windowSize-1] = 0 #update the last item to zero, meaning we have nothing else to send

             #we still have data to send
             else:    
                 #send next block
                 lastPacketSent = packetWindow[windowSize-1]

                 #create packet
                 packetType = bytearray(DTA, 'utf-8')
                 sequenceStr = "%s" % (lastPacketSent + 1)
                 packetSequence = bytearray(sequenceStr+',', 'utf-8')
                 packetMessage = packetDic[lastPacketSent+1]
                 packetToClient = packetType+packetSequence+packetMessage

                 sock.sendto(packetToClient, clientAddrPort)
                 if verbose: print "Packet To client:  %s" % packetToClient

                 #update window
                 for index in range(windowSize-1):
                     packetWindow[index] = packetWindow[index+1]
                 packetWindow[windowSize-1] = lastPacketSent+1


         #we got a delayed ack, but we already sent the data to the client. do nothing
         elif lastReceive > int(packetSequence):
             if verbose: print "Assume Delayed Packet, do nothing" 

         #drop packet resend last
         elif int(packetSequence) == lastReceive:
             if int(packetSequence) == totalPacket: #sent FIN data
                 #create packet
                 packetType = bytearray(FIN, 'utf-8')
                 packetSequence = bytearray('0'+',', 'utf-8')
                 packetMessage = bytearray("Last packet", 'utf-8')
             else:
                 #create packet
                 packetType = bytearray(DTA, 'utf-8')
                 sequenceStr = "%s" % (lastReceive + 1)
                 packetSequence = bytearray(sequenceStr+',', 'utf-8')
                 packetMessage = packetDic[lastReceive+1]

             packetToClient = packetType+packetSequence+packetMessage

             sock.sendto(packetToClient, clientAddrPort)
             if verbose: print "Packet To client:  %s" % packetToClient
             if verbose: print "Window: %s" % packetWindow

         #we got a cumulative ack
         else:
             sequenceRec = int(packetSequence)
             packetDiff = 0                    #this difference will help us to identify how many packets do we need to send
             windowIndex = 0
             lastReceive = int(packetSequence) #update last ack receive

             #update window to always have a full window in transit
             for index in range(windowSize):
                 if packetWindow[index] == sequenceRec:
                     packetDiff = index       #the client received, this many packets
             windowIndex = packetDiff
             if windowIndex == (windowSize-1):
                 tmpWindowIndex = 0
             else:
                 tmpWindowIndex = windowSize - (windowIndex + 1)
             lastPacketSent = packetWindow[windowSize-1]

             #the last packet sent was a FIN, meaning we already sent all packets. do nothing
             if lastPacketSent == 'F':
                 if verbose: print "We are done, just ignore the ack"
 
             else:
                 #update window
                 #tempDiff = packetDifff
                 loopRange = windowSize - (windowIndex+1)
                 for index in range(loopRange):
                     if windowIndex <= (windowSize - 2): #we don't want to go over the window size
                         windowIndex += 1
                     packetWindow[index] = packetWindow[windowIndex]

                 if verbose: print "Window: %s" % packetWindow

                 #create next set of packets
                 nextPacket = lastPacketSent + 1
                 for packet in range(packetDiff+1):
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
                     #send the necessary packets to have a full window in transit
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
        global resendCount
        global finFlag

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
        if verbose:
            print "Packet type: %c" % packetType
            print "Packet sequence: %s" % packetSequence 
            print "Message: %s" % packetMessage
        timeoutCount = 0
        
        #identify packet type
        if packetType == GET or packetType == ACK:
                sendNextBlock()
        elif packetType == PUT or packetType == DTA:
               sendAck() 
        elif packetType == FIN:
            print "End of File, creating local copy....."
            finFlag = 1
    
    

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
        if finFlag == 1:
            #write file
            outFile = open(fileName, 'w+')
            for key in packetDic.keys():
                outFile.write("%s" % packetDic[key])
            outFile.close()
            print "File created in current directory: %s" % fileName
        print "timeout: no events"
        timeoutCount += 1
    for sock in readRdySet:
        readSockFunc[sock](sock)
