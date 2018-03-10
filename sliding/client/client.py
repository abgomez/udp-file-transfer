#! /bin/python

#Abel Gomez 80602216
#########################################################################################
#########################################################################################
# Program client.py                                                                     #
# Description: The client send UDP packets to server (localhost:50000), it implements   # 
#              a sliding window protocol, with a default size of 5 and cumulative acks  #
#              The client resends packets on timeout.                                   # 
#              The client has a verbose which prints to console all actions (off by def)#
# Options: get - gets a file from the server                                            #
#          put - puts a file into the server, the file must exists in current path      #
# How to use: python client.py -v -g file_name                                          #
#                                                                                       #
#  ----------------     Modification Log ----------------                               #
#  Date          Name            Description                                            #
# --------------------------------------------------------------------------------------#
# 03/08/18      Abel Gomez       Initial Creation                                       #
#########################################################################################
#########################################################################################

import sys, re, os, time
from socket import *
from select import *

#Global variables
serverAddr = ('localhost', 50000)                                  #default server address
packetType = bytearray()                                           #packet type: G, P, A, E, F , D
packetSequence = bytearray()                                       #data block sequence
packetMessage = bytearray()                                        #message sent to server
packetToServer = bytearray()                                       #complete data sent to server
clientSocket = socket(AF_INET, SOCK_DGRAM)                         #UPD socket to communicate
resendCount = 0                                                    #count number of resends
verbose = 0                                                        #verbose mode
fileName = ""                                                      #file name, input or output
mode = 'u'                                                         #client mode: get or put
packetBuffer = {}                                                  #buffer to temporal save packets
packetDic = {}                                                     #packet dictionary, it saves all packets
sequence = 0                                                       #sequence used to send the first window
lastAck = 0                                                        #last acknowledge receive
finFlag = 0                                                        #flag to identify when a FIN packet is receive
windowSize = 5                                                     #default window size
packetWindow = {}                                                  #packet window, defualt size 5
lastReceive = 0                                                    #variable to identify which was the last data block received
totalPacket = 0                                                    #total number of packets to send

#define packet type
GET = 'G'
PUT = 'P'
ACK = 'A'
DTA = 'D'
FIN = 'F'
ERR = 'E'

#Function: closeConnection
#Description: terminate communication and do a clean up. 
#             we can not wait for ever for a response, if after 5 tries the server is not responding we close and finish 
#             all communication with the server.
def closeConnection():
    #global variables
    global packetToServer
    global activePacket
    global totalPacket
    global inFile

    #if we lost the server at the first packet, not big deal just terminate the client
    if packetToServer[0] == ord(GET) or packetToServer[0] == ord(PUT):
        print "Unable to reach server"
        print "Closing application...."
    #If we don't get the last ack, we assume that the server got the full file
    elif packetToServer[0] == ord(FIN):
        #we assume success
        print "Transfer has completed successfully"
    #If we stop in the middle of a get, we accept and incomplete file
    elif packetToServer[0] == ord(ACK):
        print "Weird something is wrong"
        print "File %s is incomplete" % fileName
        #write file
        outFile = open(fileName, 'w+')
        for key in packetDic.keys():
            outFile.write("%s" % packetDic[key])
        outFile.close()
        print "Incomplete file created in current directory: %s" % fileName
        outFile.close()
    #If we stop in the middle of a put, there is not much that we could do.
    #just report the percentage of packets sent
    elif packetToServer[0] == ord(DTA):
        print "Unable to rearch Server"
        print "Incomplete Transfer, %d packets of %d sent" % (lastReceive, totalPacket)
        inFile.close()


#Function: openFile
#Description: open requested file
def openFile():
    #global variables
    global packetMessage
    global totalPacket
    global packetDic
    global inFile

    #verify files exists, if not send error packet to client
    if not os.path.exists(fileName):
        if verbose: print "ERROR: file requested by client do not exists"
        sys.exit(1)
    else:
        #open file
        inFile = open(fileName)
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
#             the sliding windows always tries to keep a full window in transit.
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

     #global activePacket
     #global sequenceBlock
     #global nextBlock


     #if we got  the first response from the server send the initial set of packets
     if int(packetSequence) == 0: 
         if openFile():
             #send first window, default window size = 5
             sequence = 1
             windowIndex = 0
             for index in range(windowSize):
                 #create packet
                 packetType = bytearray(DTA, 'utf-8')
                 sequenceStr = "%s" % sequence
                 packetSequence = bytearray(sequenceStr+',', 'utf-8')
                 packetMessage = packetDic[sequence]
                 packetToServer = packetType+packetSequence+packetMessage

                 #update window and sequence
                 packetWindow[windowIndex] = sequence
                 sequence += 1
                 windowIndex += 1

                 clientSocket.sendto(packetToServer, serverAddr)
                 if verbose: print "Packet To Server:  %s" % packetToServer

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
                 packetToServer = packetType+packetSequence+packetMessage

                 clientSocket.sendto(packetToServer, serverAddr)
                 if verbose: print "Packet To Server:  %s" % packetToServer

                 #update window
                 for index in range(windowSize-1): #windowSize - 1, we don't want to go over the window
                     packetWindow[index] = packetWindow[index+1]
                 packetWindow[windowSize-1] = 'F' #update last item

             #we already sent all packets, ignore ack and update window
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
                 packetToServer = packetType+packetSequence+packetMessage

                 clientSocket.sendto(packetToServer, serverAddr)
                 if verbose: print "Packet To Server:  %s" % packetToServer

                 #update window
                 for index in range(windowSize-1):
                     packetWindow[index] = packetWindow[index+1]
                 packetWindow[windowSize-1] = lastPacketSent+1


         #we got a delayed ack, but we already sent the data to the client. do nothing. acks are cumulative
         elif lastReceive > int(packetSequence):
             if verbose: print "Assume Delayed Packet, do nothing" 

         #lost packet resend last, no need to update window
         elif int(packetSequence) == lastReceive:
             if int(packetSequence) == totalPacket: #send FIN
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
             packetToServer = packetType+packetSequence+packetMessage

             clientSocket.sendto(packetToServer, serverAddr)
             if verbose: print "Packet To Server:  %s" % packetToServer
             if verbose: print "Window: %s" % packetWindow

         #we got a cumulative ack
         else:
             sequenceRec = int(packetSequence) #figure out which ack within the window we got
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
             lastPacketSent = packetWindow[windowSize-1] #what was the last packet that we sent

             #the last packet sent was a FIN, meaning we already sent all packets. do nothing
             if lastPacketSent == 'F':
                 if verbose: print "We are done, just ignore the ack"
 
             else:
                 #update window
                 loopRange = windowSize - (windowIndex+1)
                 for index in range(loopRange):
                     if windowIndex <= (windowSize - 2): #we don't want to go over the window size
                         windowIndex += 1
                     packetWindow[index] = packetWindow[windowIndex]

                 if verbose: print "Window: %s" % packetWindow

                 #create next set of packets
                 nextPacket = lastPacketSent + 1
                 for packet in range(packetDiff+1): #we don't know how many we need to send
                     if nextPacket > totalPacket: #we are done, send FIN packet
                         #create packet
                         packetType = bytearray(FIN, 'utf-8')
                         packetSequence = bytearray('0'+',', 'utf-8')
                         packetMessage = bytearray("Last packet", 'utf-8')
                         packetToServer = packetType+packetSequence+packetMessage

                         clientSocket.sendto(packetToServer, serverAddr)
                         if verbose: print "Packet To Server:  %s" % packetToServer
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
                         packetToServer = packetType+packetSequence+packetMessage

                         #update window 
                         packetWindow[tmpWindowIndex] = nextPacket
                         tmpWindowIndex += 1
                         nextPacket += 1

                         clientSocket.sendto(packetToServer, serverAddr)
                         if verbose: print "Packet To Server:  %s" % packetToServer
                         if verbose: print "Window: %s" % packetWindow

#Function: sendAck
#Description: send an acknowledge after receiving a valid packet, a normal processing is follow if we get
#             the expected ack, if not the data is put into the buffer. acks are cumulative meaning that
#             we only acknowledge the last processed packet.
def sendAck():
    #global variables
    #global sequence
    global packetBuffer
    global lastAck
    global packetSequence
    global packetMessage
    global packetDic
    #global packetBuffer
    global packetToServer
    
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
            packetToServer = packetType+packetSequence+packetMessage

            clientSocket.sendto(packetToServer, serverAddr)
            if verbose: print "Packet sent to server: %s" % packetToServer
        else: #we have packets in the buffer, figure out which ones
            #save packet into dic
            packetDic[int(packetSequence)] = packetMessage
  
            #save packets in dictionary and send acknowledge, acks are cumulative
            nextPacket = int(packetSequence) + 1
            #find if we have the packet in the buffer
            while True:
                if nextPacket in packetBuffer:
                    packetDic[nextPacket] = packetBuffer[nextPacket]
                    del packetBuffer[nextPacket]
                    nextPacket += 1
                    #print packetDic
                #no more packet send ack of last packet
                else:
                    #create acknowledge
                    packetType = bytearray(ACK, 'utf-8')
                    tempString = "%s" % (nextPacket - 1)
                    sequenceStr = tempString+','
                    packetSequence = bytearray(sequenceStr, 'utf-8')
                    packetMessage = bytearray("ack", 'utf-8') 
                    packetToServer = packetType+packetSequence+packetMessage
                    lastAck = nextPacket - 1
 
                    clientSocket.sendto(packetToServer, serverAddr)
                    if verbose: print "Packet sent to server: %s" % packetToServer
                    break
    #not the expected ack, save packet into buffer
    else:
	#save packets into buffer, put packet might be delay
        packetBuffer[int(packetSequence)] = packetMessage


#Function: processMsg
#Description: process incoming packets, the client can receive acks, data, fin or error packets from the server
#             we need to identify which packet the server sent and we need to process it properly.
def processMessage(sock):
    #global variables
    global packetType 
    global packetSequence
    global packetMessage
    #global lastPacket
    #global pckDic
    #global message
    global resendCount
    global endTime
    global initTime
    #global blockSeq
    #global fileLen
    #global packetDic
    global finFlag
    
    #retreive packet from server
    serverPacket, serverAddrPort = sock.recvfrom(2048)
    if verbose: print "Packet received from server: %s" % serverPacket
    
    #strip packet
    packetType = serverPacket[0]
    #figure our sequence number, remove packet type. we know our sequence starts at index 1
    tempString = "%s" % serverPacket[1:]
    sequenceIndex = tempString.find(',') #identify where the sequence ends
    packetSequence = tempString[0:sequenceIndex]
    packetMessage = tempString[sequenceIndex+1:]
    if verbose:
        print "Packet Type: %c" % packetType
        print "Packet sequence: %s" % packetSequence
        print "Message: %s" % packetMessage
    resendCount = 0

    #identify what we got and process each packet properly
    if packetType == DTA:
            sendAck()
    elif packetType == FIN:
        print "End of file, creating local copy....." 
        finFlag = 1
    elif packetType == ACK:
        sendNextBlock()
    elif packetType == ERR:
        print "Requested File not found"
        print "Please select a valid file"
        sys.exit(1)

#Function: sendFirstMsg
#Description: The function sends the first message to the server, the client is the one that starts the
#             communication. It can send two types of messages get or put
def sendFirstMessage():
    #global variables
    global packetType
    global packetSequence
    global packetMessage
    global packetToServer

    #build packet 
    if mode == 'g':
        packetType = bytearray(GET, 'utf-8')
        packetSequence = bytearray('0'+',', 'utf-8')
        packetMessage = bytearray(fileName, 'utf-8')	
        packetToServer = packetType+packetSequence+packetMessage
    elif mode == 'p':
        packetType = bytearray(PUT, 'utf-8')
        packetSequence = bytearray('0'+',', 'utf-8')
        packetMessage = bytearray(fileName, 'utf-8')	
        packetToServer = packetType+packetSequence+packetMessage
    if verbose: print "Packet sent to server: %s" % packetToServer
    clientSocket.sendto(packetToServer, serverAddr)

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

                                     #### Main Logic ####
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

#verify correct use of client
if mode == 'u':
    print "Incorrect use of client, you need to use get or put function"
    usage()
    sys.exit(1)

print "ready to communicate"
sendFirstMessage()

#setup to actively listen to any interaction client and server
readSockFunc = {}
writeSockFunc = {}
errorSockFunc = {}
timeout = 5             #seconds
readSockFunc[clientSocket] = processMessage

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
            #since the server sends a window of packets, we don't know if more packets are on the way
            # if we already got the FIN packet, we can safely assume the server sent all packets
            if finFlag == 1:
                #write file
                outFile = open(fileName, 'w+')
                for key in packetDic.keys():
                    outFile.write("%s" % packetDic[key])
                outFile.close()
                print "File created in current directory: %s" % fileName
                sys.exit(1)
            else:
                #working with sliding windows we need to figure out what was the last packet that we sent
                # this last packet will be different on put or get mode
                if mode == 'p':
                    if lastReceive == 0:
                        #resend last packet on timeout
                        clientSocket.sendto(packetToServer, serverAddr)
                        if verbose: print "Packet to Server on resend: %s" % packetToServer
                    elif lastReceive + 1 > totalPacket:
                        if verbose: print "Transfer completed successfully"
                        sys.exit(1)
                    else: #get the last packet that we receive and send the next
                        #create packet
                        packetType = bytearray(DTA, 'utf-8')
                        sequenceStr = "%s" % (lastReceive + 1)
                        packetSequence = bytearray(sequenceStr+',', 'utf-8')
                        packetMessage = packetDic[lastReceive+1]
                        packetToServer = packetType+packetSequence+packetMessage

                        clientSocket.sendto(packetToServer, serverAddr)
                        if verbose: print "Packet To Server:  %s" % packetToServer

                #working on get mode, just send the last ack
                else:
                    #resend last packet on timeout
                    clientSocket.sendto(packetToServer, serverAddr)
                    if verbose: print "Packet to Server on resend: %s" % packetToServer

                resendCount += 1
                if verbose: print "resend count: %d" % resendCount

    #Figure out what we got
    for sock in readRdySet:
        readSockFunc[sock](sock)
