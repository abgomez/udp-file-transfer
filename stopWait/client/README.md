#client.py


##Description
This program is the client side of a UPD protocol, the client starts the
communication to the server(local, 50000). It implements a stop-and-wait
protocol where it only send packets when it receives the response from 
the server. The client can operate in two modes get an put.
*get - gets a file from the server.
*put - puts a file on the server. 

The client uses UDP packets to send and receive information; these packets
consist of one header, a sequence number, and the intended message.
On this implementation of stop-and-wait, the sequence is not being used
but it is included in the packet becuase it will help us when implementing
sliding windows.

The client also implements a retransmit on timeout; this means that if the
client doesn't receive a packet from the server within 5 seconds it will
resend the last packet.

The client can receive or send the following type of packets:
GET, PUT, DATA, FIN, ERROR, and ACK. 

Internal Functions:
*sendFirstMsg
*processMsg
*sendNextBlock
*sendAck
*openFile
*closeConnection
