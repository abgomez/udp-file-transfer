# udp demo simple select server -- Adrian Veliz, modified from code by
# Eric Freudenthal
import os
import socket
from socket import AF_INET, SOCK_DGRAM
from select import select

# default params
upperServerAddr = ("", 50001)   # any addr, port 50,000
# Global variables
pckType = bytearray()
pckSeq = bytearray()
message = bytearray()
totalPck = 0  # number of packets that we need to send to client.
packetDic = {}  # directory to save all pcks from file
clientAddrPort = 50005
clientDic = {}
# packets
LAST_PACKET = 0x47
MID_PACKET = 0x44
# file not found
ERROR_FNF_PACKET = 0x81
ERROR_PACKET = 0x82


def createOrGetClientEntry(client):
    key = client[0]+","+client[1]
    if key not in clientDic:
        clientDic[key] = {
            'timeout': 100,
            'seq': 0
        }
    return clientDic


def sendData():
    global totalPck
    global packetDic
    global pckSeq
    if pckSeq == 0:
        # verify files exists
        if not os.path.exists(message):
            print "ERROR: file requested by client do not exists"
            print "SENT ERROR MESSAGE"  # NEED TO IMPLEMENT ERROR PACKET
            # send error message to client when file does not exist
            header = bytearray([ERROR_FNF_PACKET, 99])
            sock.sendto(header, clientAddrPort)
            return
        else:
            inFile = open(message)
            text = inFile.read()
            textArray = bytearray(text, 'utf-8')
            numPcks = len(textArray)/100
            if (len(textArray) % 100) == 0:
                totalPck = numPcks
            else:
                totalPck = numPcks + 1
            # print totalPck
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
            # print seqNum
            # print "%s" % packetDic[80]
            # print "%s" % packetDic[81]

    # sent response to client,
    # check if we are done, if not send next packet
    # TODO: why is the clientAddrPort hard coded should it get it
    # from the connection

    if pckSeq == totalPck:
        header = bytearray([LAST_PACKET, 99])
        msg = bytearray("I'm Done", 'utf-8')
        pckToClient = header+msg
        sock.sendto(pckToClient, clientAddrPort)
    else:
        pckSeq += 1
        header = bytearray([MID_PACKET, pckSeq])
        pckToClient = header+packetDic[pckSeq]
        sock.sendto(pckToClient, clientAddrPort)


def processMsg(sock):
    global pckType
    global pckSeq
    global message
    global clientAddrPort
    packet, clientAddrPort = sock.recvfrom(2048)
    # ADD VERBOSE IF
    # client = createOrGetClientEntry(clientAddrPort)
    print "from %s: rec'd '%c%d%s'" % (
        repr(clientAddrPort), packet[0], ord(packet[1]), packet[2:]
    )

    # strip packet
    pckType = packet[0]
    pckSeq = ord(packet[1])
    message = packet[2:]
    # REMOVE PRINTS BEOFR SUBMIT
    print "packet type: %c" % pckType
    print "packet seq: %d" % pckSeq
    print "message: %s" % message

    # identify packet type
    if pckType == 'G' or pckType == 'A':
        sendData()
        # if pckSeq == '0':
        # sendAck()
        # else:
        #        sendNxtBlock()
    else:
        print "no implemented yet"


# def uppercase(sock):
# message, clientAddrPort = sock.recvfrom(2048)
# print "from %s: rec'd '%s'" % (repr(clientAddrPort), message)
# modifiedMessage = "ok"#message.upper()
# sock.sendto(modifiedMessage, clientAddrPort)

upperServerSocket = socket.socket(AF_INET, SOCK_DGRAM)
upperServerSocket.bind(upperServerAddr)
upperServerSocket.setblocking(False)

readSockFunc = {}               # dictionaries from socket to function
writeSockFunc = {}
errorSockFunc = {}
timeout = 5                     # seconds

readSockFunc[upperServerSocket] = processMsg

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
