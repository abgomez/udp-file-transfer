# client.py

## Description
This program is the client side of a UPD protocol, the client starts the 
communication to the server(local, 50000). It implements a sliding windows 
protocol where it only send packets when it receives the response from the server. 
The client can operate in two modes get an put.
* get - gets a file from the server.
* put - puts a file on the server. 

The client uses UDP packets to send and receive information; these packets 
consist of three sections: type, sequence number, and the intended message. 
The client also implements a retransmit on timeout; this means that if the 
client doesn't receive a packet from the server within 5 seconds it will resend the last packet.

The client can receive or send the following type of packets:
GET, PUT, DATA, FIN, ERROR, and ACK. 

Internal Functions:
* sendFirstMsg
* processMsg
* sendNextBlock
* sendAck
* openFile
* closeConnection

#### Constraints:
TODO

## Functions
### sendFirstMsg: 
The Function sends the intial communication to the server, it identifies 
the type of packets the user wants to sends.  
### processMessage:
This function processes all incoming messages from the server, 
it will identify the type of message and it call other functions to create and send a properly response.  
the function also strips the sequence number which is delimiter by','
### sendNextBlock:
The server sends acks for each data block that it receives, the client needs to identify which data block it needs 
to send next or if FIN packet is required. A full windows needs to be transit all time, to acomplish this 
the client needs to process the following cases separate.
* normal processing: we got an expected ack, send next packet in the window
* duplicate ack: assume lost packet resend last packet sent
* old ack: acks are cumulative, old acks are ignored since we already got a most recent ack
* ahead ack: this mean that the ack received is greater than the expected ack. we need send the
* necessary packets to keep a full window in transit.
### sendAck:
Send an acknowledge after receiving a valid packet, a normal processing is follow if we get the expected ack, 
if not the data block is save into the buffer. Acks are cumulative meaning that we only acknowledge the last processed packet..  
### openFile:
Opens input file, the contet of this file is send to the server. 
### closeConnection:
If something went wrong we want to terminate the client and display error messages. 

## How to run the client. 
The clien accepts arguments which need to be passed at the momment of execution. 

To run the client in get mode: ` python client.py -v -g filename `

To run the client in put mode: ` python client.py -v -p filename `

Regarding the put mode the file must existing in the current directory.  

## Running Example:
We execute the client in get mode, At the end of execution the client displays the file that was created and 
real time regarding the send and receive of each packet. 

The first image shows that we don't have a file call declaration.txt, we will run our client and we will ask for that file to the
server. 
![alt text](https://github.com/s18-nets/s18-nets-udp-file-transfer-abgomez/blob/master/stopWait/images/list.PNG "list")

To get the file declaration.txt:` python client.py -v -g declaration.txt `

The following images shows a snippet of our client running:
![alt text](https://github.com/s18-nets/s18-nets-udp-file-transfer-abgomez/blob/master/stopWait/images/getRunning.PNG "Image2")

At the end we got the file declaration.txt, we saved a local into the client, and the client displayed some information
regarding the exchange of data. 

![alt text](https://github.com/s18-nets/s18-nets-udp-file-transfer-abgomez/blob/master/stopWait/images/list2.PNG "list2")
![alt text](https://github.com/s18-nets/s18-nets-udp-file-transfer-abgomez/blob/master/stopWait/images/finishGet.PNG "Final")

## Proxy Results
### get mode results
Script | Total Round Trip Time | Throughput | Log
------------ | ------------- | ------------- | -------------
p1.sh |  ~ 9s | 440 bytes/s | [getP1.log](https://github.com/s18-nets/s18-nets-udp-file-transfer-abgomez/tree/master/stopWait/client/logs/getP1.log) 
p2.sh | ~104s | 39 bytes/s | [getP2.log](https://github.com/s18-nets/s18-nets-udp-file-transfer-abgomez/tree/master/stopWait/client/logs/getP2.log) 
p3.sh | ~24s | 168 bytes/s | [getP3.log](https://github.com/s18-nets/s18-nets-udp-file-transfer-abgomez/tree/master/stopWait/client/logs/getP3.log) 

### put mode results
Script | Total Round Trip Time | Throughput | Log
------------ | ------------- | ------------- | -------------
p1.sh | ~9s | 858 bytes/s | [putP1.log](https://github.com/s18-nets/s18-nets-udp-file-transfer-abgomez/tree/master/stopWait/client/logs/putP1.log) 
p2.sh | ~99s | 81 bytes/s| [putP2.log](https://github.com/s18-nets/s18-nets-udp-file-transfer-abgomez/tree/master/stopWait/client/logs/putP2.log) 
p3.sh | ~29s | 274 bytes/s | [putP3.log](https://github.com/s18-nets/s18-nets-udp-file-transfer-abgomez/tree/master/stopWait/client/logs/putP3.log) 

## Testing
I tested the client by doing several runs, first without the proxy and eventually I ran all three scripts provided by Dr. Freudenthal. 
The client was tested with two files: [declaration.txt](https://github.com/s18-nets/s18-nets-udp-file-transfer-abgomez/blob/master/stopWait/client/declaration.txt) and [bigFile.txt](https://github.com/s18-nets/s18-nets-udp-file-transfer-abgomez/blob/master/stopWait/client/bigFile.txt) 

To verify the successful execution I compared the files size and I check the modification date.  
