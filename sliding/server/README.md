# server.py

## Description

The server is the second component of our sliding window protocol, like the client it sends data through datagrams each
datagram (packet) consist of a three sections: type, sequence+',', and message. Refer to the description of ***** for
full detail regarding the function of each section. The server implements a retransmit on duplicate this means that the 
server will send a response back to any type of messages, regarding duplicates or old packets the server will identify
if it really needs to resend the packet or if it can ignore it. 

There are four types of messages that the server can send:
* DTA - send data block to client.
* ACK - acknowledge a data block.
* FIN - tell you are done sending.
* ERR - report an error to the client.

Like the client the server also has a default timeout of 5 seconds which is used to identify if a connection is down. 
Every 5 seconds the server will check if it got something new from the client or if it has something new to send, since
our does not resend on timeout, no actual work is done after the timeout. However if the timeout experies 5 consecutive times
then the server assumes that the client is down, and it sof-closes the connection.

The server can not reboot, instead of shutingdown it simple resets all objects related to the active connection.
This simulates a close function, if the client wants to communicate after the reset it will need to start a new request.

## Functions.
#### processClientMessage

This function get all incoming packets; it identifies the type of packets and send the packet to the appropriate function to be processed. 
It also strips the sequence from the packet, the sequence number is delimiter by a ','. 

#### sendNextBlock

The client sends acks for each data block that it receives, the server needs to identify which block it needs to 
send next or if FIN packet is required. A full windows needs to be transit all time, to acomplish this the server needs to 
process the following cases separate.
* normal processing: we got an expected ack, send next packet in the window
* duplicate ack: assume lost packet resend last packet sent
* old ack: acks are cumulative, old acks are ignored since we already got a most recent ack
* ahead ack: this mean that the ack received is greater than the expected ack. we need send the 
* necessary packets to keep a full window in transit.

#### openFile

Function to open requested file, the server needs to identify which file the client has requested. If the file does not
exists and ERR packer is sent.

#### senAck

Send an acknowledge after receiving a valid packet, a normal processing is follow if we get the expected ack, 
if not the data block is save into the buffer. Acks are cumulative meaning that we only acknowledge the last processed packet.

#### cleanUp

Reset current connection objects, the client is not responding we assume is down and we need to reset our connection. 

## Constraints

TODO

## How to use

To run the server is extremely easy, you just need to run `python server.py`

## Examples

On this example we will execute the server and client, the client will send a get response which the server will 
response by sending data block each time it receives an ack. The window size used for this example is 5.

* starting server

IMAGE OF SERVER START UP

* sending data blocks to client

IMAGE OF SERVER SENDING DATA BLOCKS

* ending communication.

IMAGE OF SERVER ENDING COMMUNICATION

