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
then the server assumes that the clien is down, and it sof. closes the connenction with the client. 

The server can not reboot, instead of shutingdown it simple resests all objects relates to the active connetion. 
This simulates a close function, if the client tries to communicate after the reset it will need to start a new request. 
