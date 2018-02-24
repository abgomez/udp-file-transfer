# Stop-and-Wait Protocol
The following protocol is a simple example of a server and a client which communicate through datagrams.
Both client and server use a stop-and-wait protocol where the client retransmit on timeout and 
the server retransmit on duplicate. The datagram consist of a header, sequence number, and message, 
in this implementation the sequence number is not being use, however it is still included within the packet. 

## How it works
All communication is initialize by the client, the client decides the mode of operation which can be get or put. 
Both modes operate in the same way: the client sends the first message, the server sends a response back which can
be either an ack or data, then the client send the next message which can be an ack or data. The same dance continues
until one side finish to process the desired file.

As mentioned before the client implements a retransmit on timeout, this means that the client will resend the last packet 
if it doesn't receive a response back from the server within 5 second, if after 5 tries the client doesn't get a response
then ir assumes that the serve is down. The client can send the following packets:
* get - request to get a file.
* put - request to put a file.
* ack - acknoweldge.
* dta - data block.
* fin - finish processing.

The server implements a retransmit on duplicate, this means that our server will response to any packets that he may received.
the server also has a timeout of 5 seconds, if the server doesn't no receive a response after 5 times of the timeout it 
will assume that the client is down. The server can send the following packets:
* get - request to get a file.
* put - request to put a file.
* ack - acknoweldge.
* dta - data block.
* fin - finish processing.
* err - file not found

The following image displays the sequence and time of each interaction. 
![TimeLine Sequence](https://github.com/s18-nets/s18-nets-udp-file-transfer-abgomez/blob/master/stopWait/images/timeLine.PNG)

## Packet Structure 
### Packet's Header
The header consist of two bytes, the first byte defines the type of header, and the second defines if the received
packet is active or an old (delayed) packet. 

#### Type of packets
Header's first byte
* GET - get file from server
* PUT - put file on server
* ACK - acknowledge receive
* DTA - data block
* FIN - terminate communication
* ERR - error packet

#### Packet sequence
Header's second byte
* char - '0' or '1'

The second byte identifies if the packet is valid, the client and server keep track of the last packet that they sent.
If the last packet was a '0' then the next valid packet needs to be '1', if a zero is received then we assume the packet 
is invalid and we ignore it. 

##### known bugs
This configuration may lead to a bug when we deal with really old packets, we might have the case where and old packet
is really old and has a valid sequence number which could match with the expected packet. This will not cause a hard error 
but it will create duplicate information. 


### Sequence Number
Altough the stop-and-wait implementation does not use the sequence number, both client and server still add it to 
the final packet. The sequence number will be extremly useful, when implementing sliding windows. The sequence number can
go from 0 - 99,999 this implies that our protocol can not handle files of size
greater than 10,000,00 bytes

### Message
The last seccion of our packet is the message, this is the intended data that we want to send. 

### Format
Type | seq | Sequence Number | Message
---- | ----- | ------------ | ----------
1 bytes | 1 bytes | up to 5 bytes | up to 100 bytes

## State Machine
![State Machine](https://github.com/s18-nets/s18-nets-udp-file-transfer-abgomez/blob/master/stopWait/images/stateMachine.PNG)
