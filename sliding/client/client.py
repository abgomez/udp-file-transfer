import sys, re, os, time
from socket import *
from select import *

#Global variables
serverAddr = ('localhost', 50001)
packetType = bytearray()
packetSequence = bytearray()
packetMessage = bytearray()
clientSocket = socket(AF_INET, SOCK_DGRAM)
resendCount = 0
verbose = 0
fileName = ""
mode = 'u'
packetBuffer = {}
packetDic = {}
sequence = 0
lastAck = 0

#define packet type
GET = 'G'
PUT = 'P'
ACK = 'A'
DTA = 'D'
FIN = 'F'
ERR = 'E'

def sendAck():
    #global variables
    global sequence
    global packetBuffer
    global lastAck
    global packetSequence
    global packetMessage
    global packetDic
    
    #identify if we got the expected packet
    nextPacket = lastAck + 1
    print "lastAck %d" % lastAck
    if int(packetSequence) == nextPacket:
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
    #resendCount = 0

    #identify what we got and process each packet properly
    if packetType == DTA:
        sendAck()
    elif packetType == FIN:
        print "End of file, creating local copy....." 
        print "File created in current directory: %s" % fileName
        
        #write file
        outFile = open(fileName, 'w+')
        for key in packetDic.keys():
            outFile.write("%s" % packetDic[key])
        outFile.close()
        #endTime = time.time()
        #if verbose: print "Last packet received at %f" % endTime
        #if verbose: print "FirstPackt sent at: %f, LastPacket received at: %f" % (initTime, endTime)
        #if verbose: print "Throughput~: %dMBps" % (os.path.getsize(fileName)/(endTime-initTime))
        #outFile.close()
        #sys.exit(1)
    elif packetType == ACK:
        print "TODO" #sendNextBlock()
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
            #resend last packet on timeout
            #clientSocket.sendto(pckToServer, serverAddr)
            #resendCount += 1
            if verbose: print "resend count: %d" % resendCount
        #if verbose: print "Packet to Server on resend: %c%c%s" % (pckToServer[0], pckToServer[1], pckToServer[2:])

    #Figure out what we got
    for sock in readRdySet:
        readSockFunc[sock](sock)
