#!/usr/bin/python3

'''
list of argument:
1. --> file name
2. --> server port
3. --> error rate

It can give timeout at first time, 
please run it more than one time till start communication

BUSE NUR SABAH - 150170002
05.23.21
'''

import sys 
import socket
import time as t
import random as rd

#packet types
HS = 0
ACK = 1
DATA = 2
FIN = 3 

timeOut = 0.0001 
bufferSize = 255


def threeWayHandShake(serverPort, fileName):
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.settimeout(timeOut)

    serverAddress = ("localhost",serverPort)

    bytesToSend = bytes(str(HS) + " " + str(len(fileName)) + " " + fileName, "utf-8")
    print("Sending... " + bytesToSend.decode())   
    UDPClientSocket.sendto(bytesToSend, serverAddress)

    try:
        bytesFromServer = UDPClientSocket.recvfrom(bufferSize)
        print("Receiving... " + bytesFromServer[0].decode())
        packetType, seqNum = bytesFromServer[0].decode().split() 
        if (packetType == str(ACK)):
            bytesToSend = bytes(str(ACK) + " " + seqNum, "utf-8")
            UDPClientSocket.sendto(bytesToSend, serverAddress)
            print("Sending... " + bytesToSend.decode())   

    except socket.timeout:
        print("timeout_1")
        UDPClientSocket.close()

    RDTProtocol(UDPClientSocket, serverAddress) # RDT can start 


def RDTProtocol(sock, serverAddress):
    print("\n\t************** RDT Protocol **************\n")

    sock.settimeout(timeOut)
    errRate = int(sys.argv[3])

    while(True): 
        try:
            bytesFromServer = sock.recvfrom(bufferSize)

            try:
                packetType, _, seqNum, _ = bytesFromServer[0].decode().split() 
            except:
                try:
                    packetType, _, seqNum = bytesFromServer[0].decode().split() 
                except:
                    packetType, seqNum = bytesFromServer[0].decode().split()


            if(packetType == str(DATA)):
                print("\nReceiving... " + bytesFromServer[0].decode())
                packet = bytes(str(ACK) + " " + str(seqNum), "utf-8")
                unreliableSend(packet, sock, serverAddress, errRate, "Acknowledge") # sending ACK 

            elif(packetType == str(FIN)):
                seqNum = int(seqNum)+1
                packet = bytes(str(ACK) + " " + str(seqNum), "utf-8")
                unreliableSend(packet, sock, serverAddress, errRate, "Acknowledge") # sending ACK 
                packet = bytes(str(FIN) + " " + str(seqNum), "utf-8")
                unreliableSend(packet, sock, serverAddress, errRate, "Finish") # sending FIN
            else: # packetType = ACK
                sock.close()

        except socket.timeout:
            print("timeout_2")

      
def unreliableSend(packet, sock, userIP, errRate, mes):  # errRate --> %1,5,10,20
   if errRate < rd.randint(0,100):
      print("Sending " + mes + "..." + packet.decode())
      sock.sendto(packet, userIP)

def main():
    fileName = str(sys.argv[1]) 
    serverPort = int(sys.argv[2])   

    threeWayHandShake(serverPort, fileName)
   
   
if __name__ == "__main__":
   main()

