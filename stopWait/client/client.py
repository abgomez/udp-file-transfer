#! /bin/python

#Abel Gomez 80602216
#02/10/2018
#Client.py, is a program which silumates the communication between a server and a client.
#It uses datagrams to transfer data to the server. It has two main fucntions: get and put.
#The function get request a file from the server, the file is saved in a local copy.
#    Errors: If the files doesn't exists the server will send an error message.
#The function put sends a request to the server to save a new file or an existing file. 
#Parameters: server address,  following the following format: host:port
#If a package is lost or delayed the client will implement a retransmit-on-timeout policy. 

import sys, re, os
from socket import *
from select import *

#Default params
serverAddr = ('localhost', 50000)

#Global variables
#socket to communicate
clientSocket = socket(AF_INET, SOCK_DGRAM)
#define header attributes.
pckType = 0x20
packSeq = 0x00

#display correct usage of parameters
def usage():
    print """usage: %s \n
    Option                         Default             Description
    [--serverAddr host:port]       localhost:50001     Server name and port
    [--put or -p file Name]                            File name to send, must exists on current directory
    [--get or -g file Name]                            File name to get from server
    [--help or -h]                                     Print usage """% sys.argv[0]
    sys.exit(1)

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
        elif sw == "--get" or sw == "-g":
            fileName = args[0]; del args[0]
        elif sw =="--help" or sw == "-h":
            usage();
        else:
            print "unexpected parameter %s" % args[0]
            usage();
except Exception as e: 
    print "Error parsing arguments %s" % (e)
    usage()
    
def processMsg(sock):
    returnMsg, serverAddrPort = sock.recvfrom(2048)
    print "Return Msg: %s" % (repr(returnMsg))
    sock.sendto(message, serverAddr)

message = "hello from client"
readSockFunc = {}
writeSockFunc = {}
errorSockFunc = {}
timeout = 5
readSockFunc[clientSocket] = processMsg 

clientSocket.sendto(message, serverAddr)
print "ready to communicate"
while 1:
    readRdySet, writeRdySet, errorRdySet = select(readSockFunc.keys(), writeSockFunc.keys(), errorSockFunc.keys(), timeout)
    if not readRdySet and not writeRdySet and not errorRdySet:
        print "timeout: no events"
    for sock in readRdySet:
        readSockFunc[sock](sock)
#clientSocket.sendto(message, serverAddr)
#returnMsg, serverAddrPort = clientSocket.recvfrom(2048)
#print "Return Msg: %s" % (repr(returnMsg))
