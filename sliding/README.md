# Sliding Window Protocol

The Following protocol is a simple example of a server and a client which communicate through datagrams. 
Both the client and the server use a sliding window protocol where the client retransmit on timeout while 
the server retransmit on duplicate. The datagram consist of a header, a sequence number and a message.

## How it works

All communication is initialize by the client, the client decides the mode of operation which can be
get or put. Both modes operate in the same way; the client sends the first message, the servers sends
a response back which can be either an ack or data, then the client send the next which message which can
be an ack or data. The same dance continues until one side finish to process the desired file.
In the Sliding windows protocol, data blocks are send on groups of packets, this group of packets are called
window, the default size is 5 meaning that the server or client can send up to 5 packets at the same time.

As mention before the client implements a retransmit on timeout, this means that the client will resend the
last packet that it previously sent. The retransmission on timeout is handle by a timeout of 5 seconds if 
the timeout experies the client will try to resend the last packet sent, if after 5 tries the client does not
get a response then it assumes that the server is down.

The server implements a retransmit on duplicate, this means that our server will response to any packets that it
might receive. Since the sliding windows protocol implements a window, the server needs to identify what is consider
a duplicate packet. A packet is consider duplicate if we got the same packet twice in a row. The server also has 
a timeout 5 seconds and it will also try up to 5 resends before given up.

The protocol implements sliding window, this means that both client and server need to process the packets accordingly.
Client and Server are able to send datablocks, while sending the datablocks a few cases can ocurr during transfer
* normal processing: we got an expected ack, send next data block in the window
* duplicate ack: assume lost packet resend last data block sent
* old ack: acks are cumulative, old acks are ignored since we already got a most recent ack
* ahead ack: this mean that the ack received is greater than the expected ack. we need send the necessary packets to keep a full window in transit.

In case of sending acks the cases are simpler, 
* expected data block received: if your buffer is not empty process the data blocks in the buffer and send cumuliative ack. if the buffer is empty send ack.
* unexpected data block receive: put it in the buffer and wait for the correct data block.

The following image displays the sequence and time of each interaction. It also represents the different states
of our protocol. 

![TimeLine Sequence](time line)

## Packet Structure

### Format

Type | Sequence | Delimiter | Message
---- | ----- | ---------- | ----------------
1 bytes | 1:* bytes | , | up to 100 bytes

#### Type

Packet's first byte, this byte represents the type of packet. Our protocol allows 6 types
* GET - get file from server
* PUT - put file on server
* ACK - acknowledge receive
* DTA - data block
* FIN - terminate communication
* ERR - error packet

#### Sequence

The sequence represents the incremental order of data blocks, the sequence starts at the second byte and theoretically
it does not have a limit (the latter statement was not tested). 

#### Delimiter

Delimiter is the first byte after the sequence number, since we don't know how many packets we are sending
we need to be able to identify where the sequence number ends the character ',' is used for this purpose. 
Both client and server look for the first ',' after the second byte to identify where the sequence ends. 

#### Message

The last Seccion of our packets is the message, the message has a limit of 100 bytes. 
