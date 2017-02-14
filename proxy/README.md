# nets-udp-proxy

## udpProxy.py
UDP Proxy
~~~
          Option                                   Default     Description
         [--clientPort <port#>]                      50000     Client port number
         [--serverAddr host:port]          localhost:50001     Server port number

         [--byteRate <bytes-per-second>]             10000     Byterate at which to forward messages
         [--propLat <latency_secs>]                   0.01     Propogational Latency
         [--qCap <queue-capacity>]                       4     Maximium number of messages to queue

         [--pDelay <prob-delayed-msg>]                 0.0     Probability message delayed
             [--delayMin <sec>] [--delayMax <sec>      1.0       w/ uniform distribution
         [--pDrop <prob-drop-msg]                      0.0     Probability of message being dropped
         [--pDup <prob-dup-msg]                        0.0     Probability of a msg duplication 

         [--verbose]                                    off    Verbose Mode
         [--help]                                              Display help message
~~~

## udpClient.py
~~~
Optional parameter --serverAddr <host:port> (default localhost:50000)
~~~

## udpServer.py
~~~
Optional paramter --serverPort <port> (default 50001)
~~~
