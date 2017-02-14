# nets-udp-file-transfer


## General description
Implement a stop-and-wait file transfer protocol of your own design
that utilizes UDP as its transport.

### Undergraduates: only need to implement "get"

Client syntax: get *filename*

### Graduate students: must implement both "get" and "put"

Client syntax:
* get *filename*
* put *filename*

## Requirements:
* Your server should be a separate program from the client.  
* Your protocol can only send messages of length no
longer than 100 bytes
* Teams are permitted: Up to two students.  Each must be responsible for
implementing and documenting either the client or server.
* Your implementation must be able to successfully transfer large
binary files (at least 1MB) even when the UDP proxy delays and drops some of the datagrams. 
* The client and server should do "something reasonable" when the
protocol is unable to successfully transfer a file. 
* Your implimentation should indicate relevant stats such as measured RTT and throughput.  
* Your report should
 * describe the prototcol
 * indicate and analyze its performance for each of the following
   proxy configurations (scripts are in the proxy subdir):

| Script | Throughput |  PropDelay | QueueCap | pDrop | pDelay |
|--------|------------|------------|----------|-------|--------|
| p1.sh  | 10,000 B/s | 0.05s      | 3        | 0.0   | 0.0    |
| p2.sh  | 10,000 B/s | 0.05s      | 3        | 0.1   | 0.0    |
| p1.sh  | 10,000 B/s | 0.05s      | 3        | 0.0   | 0.1    |


## Part 1: Stop and Wait

Your solution should be in the stopWait subdir and implement a stop
and wait protocol.   Your client should be in its 
client subdir.  Your server should be in its server subdir.  Each
should be documented (an empty README is provided).


## Part 2: Sliding window

Your solution should be in the sliding subdir.  Your client should be in its
client subdir.  Your server should be in its server subdir.  Each
should be documented (an empty README is provided).


# UDP Proxy
A UDP Proxy and demo udp client & server are in the proxy subdir.