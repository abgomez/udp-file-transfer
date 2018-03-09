import sys, re, os, time
from socket import *
from select import *

#Global variables
serverAddr = ('localhost', 50000)
packetType = bytearray()
packetSequence = bytearray()
packetMessage = bytearray()
packetToServer = bytearray()
clientSocket = socket(AF_INET, SOCK_DGRAM)
resendCount = 0
verbose = 0
fileName = ""
mode = 'u'
packetBuffer = {}
packetDic = {}
sequence = 0
lastAck = 0
finFlag = 0
windowSize = 5
packetWindow = {}
lastReceive = 0

#define packet type
GET = 'G'
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
        if not os.path.exists(fileName):
                if verbose: print "ERROR: file requested by client do not exists"
                sys.exit(1)
        else:
                #open file
                inFile = open(fileName)
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

     print packetSequence

     #if we got  the first response from the server send the initial set of packets
     if int(packetSequence) == 0: 
         print "inside if"
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
                 packetToServer = packetType+packetSequence+packetMessage

                 #update window and sequence
                 packetWindow[windowIndex] = sequence
                 sequence += 1
                 windowIndex += 1

                 clientSocket.sendto(packetToServer, serverAddr)
                 if verbose: print "Packet To Server:  %s" % packetToServer
                 print "afer open"

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
                 print "sequence: %d " % (lastPacketSent + 1)
                 #print "sequence: %d " % sequence
                 #nextBlock = sequence + 1

                 #create packet
                 packetType = bytearray(DTA, 'utf-8')
                 sequenceStr = "%s" % (lastPacketSent + 1)
                 #sequenceStr = "%s" % sequence 
                 packetSequence = bytearray(sequenceStr+',', 'utf-8')
                 packetMessage = packetDic[sequence]
                 packetToServer = packetType+packetSequence+packetMessage

                 clientSocket.sendto(packetToServer, serverAddr)
                 if verbose: print "Packet To Server:  %s" % packetToServer
                 #sequence = nextBlock

                 #update window
                 for index in range(windowSize-1):
                     packetWindow[index] = packetWindow[index+1]
                 packetWindow[windowSize-1] = lastPacketSent+1
                 #packetWindow[windowSize-1] = sequence

                 sequence += 1

         #we got a delayed ack, but we already sent the data to the client. do nothing
         elif lastReceive > int(packetSequence):
             if verbose: print "Assume Delayed Packet, do nothing" 

         #drop packet resend last
         elif int(packetSequence) == lastReceive:
             #create packet
             packetType = bytearray(DTA, 'utf-8')
             sequenceStr = "%s" % (lastReceive + 1)
             packetSequence = bytearray(sequenceStr+',', 'utf-8')
             packetMessage = packetDic[lastReceive+1]
             packetToServer = packetType+packetSequence+packetMessage

             clientSocket.sendto(packetToServer, serverAddr)
             if verbose: print "Packet To Server:  %s" % packetToServer
             if verbose: print "Window: %s" % packetWindow
             #print "TDO" #TODO

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
             #packetDiff = windowSize - (packetDiff + 1)
             #packetDiff = indowSize - (packetDiff + 1)
             lastPacketSent = packetWindow[windowSize-1]

             #the last packet sent was a FIN, meaning we already sent all packets. do nothing
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
                     if windowIndex <= (windowSize - 2): #we don't want to go over the window size
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

def sendAck():
    #global variables
    global sequence
    global packetBuffer
    global lastAck
    global packetSequence
    global packetMessage
    global packetDic
    global packetBuffer
    global packetToServer
    
    #identify if we got the expected packet
    nextPacket = lastAck + 1
    print "lastAck %d" % lastAck
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
                    packetToServer = packetType+packetSequence+packetMessage
                    lastAck = nextPacket - 1
 
                    clientSocket.sendto(packetToServer, serverAddr)
                    if verbose: print "Packet sent to server: %s" % packetToServer
                    break
            #while !packetBuffer:
            #    for key in packetBuffer.keys():
            #        if key == nextPacket:
            #            packetDic[nextPacket] = packetBuffer[nextBuffer]
            #            del packetBuffer[key]
            #    #continue looking for more packets
            #    nextPacket += 1
            
    else:
	#save packets into buffer, put packet might be delay
        print "here in buffer"
        print "received packet %s" %packetSequence
        print "expected packet %d" % nextPacket
        packetBuffer[int(packetSequence)] = packetMessage

#Function: processMsg
#Description: process incoming packets, the client can receive acks, data, fin or error packets from the server
#             we need to identify which packet the server sent and we need to process it properly.
def processMessage(sock):
    #global variables
    global packetType 
    global packetSequence
    global packetMessage
    global lastPacket
    global pckDic
    global message
    global resendCount
    global endTime
    global initTime
    global blockSeq
    global fileLen
    global packetDic
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
    #pckSeq = returnMsg[1]
    #blockSeq = returnMsg[2:7] #this sequence is not being use but we still need to handle it
    #message = returnMsg[7:] 
    resendCount = 0

    #identify what we got and process each packet properly
    if packetType == DTA:
        #if finFlag == 1:
        #    if int(packetSequence) == finalPacket:
        #        #write file
        #        outFile = open(fileName, 'w+')
        #        for key in packetDic.keys():
        #            outFile.write("%s" % packetDic[key])
        #        outFile.close()
        #else:
            sendAck()
    elif packetType == FIN:
        print "End of file, creating local copy....." 
        #print "File created in current directory: %s" % fileName
        finFlag = 1
        
        #write file
        #outFile = open(fileName, 'w+')
        #for key in packetDic.keys():
        #    outFile.write("%s" % packetDic[key])
        #outFile.close()
        #endTime = time.time()
        #if verbose: print "Last packet received at %f" % endTime
        #if verbose: print "FirstPackt sent at: %f, LastPacket received at: %f" % (initTime, endTime)
        #if verbose: print "Throughput~: %dMBps" % (os.path.getsize(fileName)/(endTime-initTime))
        #outFile.close()
        #sys.exit(1)
    elif packetType == ACK:
        sendNextBlock()
    elif packetType == ERR:
        print "Requested File not found or File to big"
        print "Please select a valid file"
        sys.exit(1)

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
        if verbose: print "Packet sent to server: %s" % packetToServer
        #print "Packet Type: %c" % packetToServer[0]
        #print "Packet Sequence: %s" % packetToServer[1:3]
        #print "Packet Message: %s" % packetToServer[3:] 
        #test = "%s" % packetToServer[1:]
        #print test
        #index = test.find(',')
        #print "Packet Sequence: %s" % test[0:index]
        #print "Packet Message: %s" % test[index+1:] 
        #stringSequence = test[0:index]
        #numberTest = 1
        #sumTest = int(stringSequence)+numberTest
        #print "%d" % sumTest
        #print "%s" % sumTest
    elif mode == 'p':
        packetType = bytearray(PUT, 'utf-8')
        packetSequence = bytearray('0'+',', 'utf-8')
        packetMessage = bytearray(fileName, 'utf-8')	
        packetToServer = packetType+packetSequence+packetMessage
        if verbose: print "Packet sent to server: %s" % packetToServer
    clientSocket.sendto(packetToServer, serverAddr)
    #exit(1)

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

#verify parms
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
            #closeConnection()
            sys.exit(1)
        else:
            if finFlag == 1:
                #write file
                outFile = open(fileName, 'w+')
                for key in packetDic.keys():
                    outFile.write("%s" % packetDic[key])
                outFile.close()
                print "File created in current directory: %s" % fileName
                sys.exit(1)
            else:
                if mode == 'p':
                    if lastReceive + 1 > totalPacket:
                        if verbose: print "Transfer completed successfully"
                        sys.exit(1)
                    else:
                        #create packet
                        packetType = bytearray(DTA, 'utf-8')
                        sequenceStr = "%s" % (lastReceive + 1)
                        packetSequence = bytearray(sequenceStr+',', 'utf-8')
                        packetMessage = packetDic[lastReceive+1]
                        packetToServer = packetType+packetSequence+packetMessage

                        clientSocket.sendto(packetToServer, serverAddr)
                        if verbose: print "Packet To Server:  %s" % packetToServer
                else:
                    #resend last packet on timeout
                    clientSocket.sendto(packetToServer, serverAddr)
                    if verbose: print "Packet to Server on resend: %s" % packetToServer

                resendCount += 1
                if verbose: print "resend count: %d" % resendCount

    #Figure out what we got
    for sock in readRdySet:
        readSockFunc[sock](sock)
