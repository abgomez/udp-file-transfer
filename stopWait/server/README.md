# server.py
## Description
The Server is the second component of our stop-and-wait protocol, like the client it send data through datagrams
each datagram (packet) consist of a header, sequence number, and message. Refer to [README](https://github.com/abgomez/udp-file-transfer/blob/master/stopWait/README.md)
for full detail regarding the function of each packet's seccions. The server implements a retransmit on duplicate 
this means that the server will send a response back to any type of messages duplicate or not.  

There are four types of messages that the server can send:
* DTA - send a data block to the client.
* ACK - acknowedlege a data block.
* FIN - tell you are done sending.
* ERR - report an error to the client.

Like the client the server also has a timeout which is used to identify if a connection is down, the server timeout if 5 seconds.
Every 5 second the server will check if it got soemthing new from the client or if it has soemthing new to send, 
since our server does not send on timeout nothing happens after the timeout, however if the timeout experies 5 consecutive times
then the server assumes that the client is down, and it sof-closes the connenction with the client. 

The server can not reboot, instead of shutingdown it simple resests all objects relates to the active connetion. 
This simulates a close function, if the client tries to communicate after the reset it will need to start a new request. 

### Functions
* processClientMessage: this function get all incomming packets; it identifies the type of packets and send the packet
to the appropiate function to be processed. 
* sendAck: the function sendAck does two things, the first one is to send back an ack for all packets, the second is to identify 
if the server got a valid packet. This means that if we got the next data block, if the server gets a valid packet then
it saves the data into a dictionary, if not the packet gets ignore .
* senNextBlock: the server will receive acknowledges from the client, the server needs to validate the ack and it needs to send
the next data block, if the server receives an old ack it just resend the previous data block. This function also identifies
when the transaccion is done. 
* openFile: opens input file, this is the file that the client requested. 
* cleanUp: since the server needs to be alive waiting for clients, we implemented a cleanup function which remove all objects
related to an unresponsive client. 

### Constraints
The server can only sends files of less than 10,000,000Mbytes

## How to use
To run the client is extremely easy, you just need to run: `python server.py`

## Running Example
On this example we will execute the server and client, the client will send a get response which the server will response
by sending data block each time it receives an ack. 

starting server
![StartingServer](https://github.com/abgomez/udp-file-transfer/tree/master/stopWait/images/serverStart.png)
sending data blocks to client
![SendData](https://github.com/abgomez/udp-file-transfer/tree/master/stopWait/images/sendData.png)
ending communication
![endCommunication](https://github.com/abgomez/udp-file-transfer/tree/master/stopWait/images/endCom.png)

## known bugs
I can tell that if my client or server receive a really late packet and if that packet has the same sequence as the packet that I'm currently waiting then they will duplicate some data blocks, nothing will fail but the final text will be incorrect.
