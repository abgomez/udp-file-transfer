#!/bin/bash
python udpProxy.py --clientPort 50000 --serverAddr localhost:50001 --byteRate 10000 --propLat .05 --qCap 3 --pDrop 0.0 --pDelay 0.1 --verbose
