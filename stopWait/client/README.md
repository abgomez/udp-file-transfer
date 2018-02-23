# client.py

## Description
This program is the client side of a UPD protocol, the client starts the 
communication to the server(local, 50000). It implements a stop-and-wait 
protocol where it only send packets when it receives the response from the server. 
The client can operate in two modes get an put.
* get - gets a file from the server.
* put - puts a file on the server. 

The client uses UDP packets to send and receive information; these packets 
consist of one header, a sequence number, and the intended message. 
On this implementation of stop-and-wait, the sequence is not being used 
but it is included in the packet becuase it will help us when implementing sliding windows.

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
The client can only sends files of less than 10,000,000Mbytes

## Functions
### sendFirstMsg: 
The Function sends the intial communication to the server, it identifies 
the type of header the user wants to sends. 
The Function also creates the packet and the first sequence to send. 
### processMsg:
This function processes all incoming messages from the server, 
it will identify the type of message and it call other functions to create and send a properly response.  
### sendNextBlock:
The Function identifies if the client received the corect ack from the server, if it got it then it 
send to the server the next block.
### sendAck:
The Function response to a data block sent by the server, it first identifies if the client got the right block.  
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

The first image shows that we don't have a file call declaration2.txt, we will run our client and we will ask for that file to the
server. 
![alt text](https://github.com/abgomez/udp-file-transfer/blob/master/stopWait/images/Capture.PNG "Image1")

To get the file declaration2.txt:` python client.py -v -g declaration2.txt `

The following images shows a snippet of our client running:
![alt text](https://github.com/abgomez/udp-file-transfer/blob/master/stopWait/images/getRunning.PNG "Image2")

At the end we got the file declaration2.txt and we saved a local into the client. 

## Proxy Results
Script | Round Trip Time | Throughput | Log
------------ | ------------- | ------------- | -------------
p1.sh | Content from cell 2 | something | [p1.log](https://github.com/abgomez/udp-file-transfer/tree/master/stopWait/logs/p1.log) 
p2.sh | Content from cell 2 | something | [p2.log](https://github.com/abgomez/udp-file-transfer/tree/master/stopWait/logs/p2.log) 
p3.sh | Content from cell 2 | something | [p3.log](https://github.com/abgomez/udp-file-transfer/tree/master/stopWait/logs/p3.log) 


## Known bugs
I couldn't replicate the situation for my bug, however after looking at the TCP documentation 
I can tell that if my client or server receive a really late packet and if that packet has the same sequence
as the packet that I'm currently waiting then I will duplicate some data blocks, nothing will fail
but the final text will be incorrect. 
