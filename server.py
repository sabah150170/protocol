#!/usr/bin/python3

'''
list of argument:
1. --> server port
2. --> window size
3. --> error rate

BUSE NUR SABAH - 150170002
05.23.21
'''

import sys 
import socket
import datetime
import time as t
import random as rd
import threading 

#packet types
HS = 0
ACK = 1
DATA = 2
FIN = 3 

timeOut = 0.0001 #microsecond
bufferSize = 255

event = threading.Event()
lock = threading.Lock()

class Data:
    def __init__(self):
    	self.lastIndex = 0
    	self.iter_start = 0
    	self.iter_end = 0  
    	self.N = 0
    	self.counter = 0
    	self.flag = True
    	self.arr = dict([])


def checkFile(fileName):
	try:
		openFile = open(fileName, 'r')
	except:
		return None
	openFile.close()
	return "OK"

def getFile(fileName, novel):
	lock.acquire()
	try:
		openFile = open(fileName, 'r')
		Lines = iter(openFile.readlines())
		i = 0
		while(True):
			try:
				novel.arr[i]= [next(Lines), 0.0, 0.0, False] # index:seqNum --> data, sending time, receiving time, ack or not
			except StopIteration:
				break
			i = i+1
		openFile.close()
		novel.lastIndex=(i-1)
	except:
		novel.lastIndex=0
	lock.release()

def socketConnection(serverport):
	UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) #create socket UDP
	UDPServerSocket.bind(('', serverport))

	novel = Data()

	print("\n\t************** 3-way Handshake **************\n")

	while(True): #listen for incoming datagrams
		UDPServerSocket.settimeout(None)

		bytesFromClient = UDPServerSocket.recvfrom(bufferSize)
		print("   \nReceiving... " + bytesFromClient[0].decode())

		try:
			packetType, _, fileName = bytesFromClient[0].decode().split() # spilit(" ")
			clientAddress = bytesFromClient[1] # such as ('127.0.0.1', 51782) tuple
		except:
			pass

		t_read = threading.Thread(target=getFile, args=(fileName, novel,))
		t_read.start()

		if (packetType == str(HS)): # 3-way handshake
			UDPServerSocket.settimeout(timeOut)
			m = checkFile(fileName)
			if (m == "OK"):
				seqNumSend = 0
				bytesToSend = bytes(str(ACK) + " " + str(seqNumSend), "utf-8") # ACK respect to filename req 
				UDPServerSocket.sendto(bytesToSend, clientAddress) #sending a reply to client
				print("Sending... " + bytesToSend.decode())   
							
				try:
					bytesFromClient = UDPServerSocket.recvfrom(bufferSize)
					packetType, seqNumRec = bytesFromClient[0].decode().split() 
					if (packetType == str(ACK) and str(seqNumSend) == seqNumRec):
						print("Receiving... " + bytesFromClient[0].decode())
						RDTProtocol(novel, UDPServerSocket, clientAddress)
						break
				except socket.timeout:
					print("timeout_1")
				#except Exception as e:
								#print("error1", e)

def resending(sock, novel, userIP, errRate):
	while(True and novel.flag):
		i = novel.iter_start
		while(i<novel.iter_end):
			if(novel.arr[i][1] != 0.0):
				lock.acquire() 
				if(novel.arr[i][3] == False):
					if((t.time()-novel.arr[i][1]) > timeOut and novel.arr[i][3] == False):
						packet = bytes(str(DATA) + " " + str(len(novel.arr[i][0])) + " " + str(i) + " " + novel.arr[i][0], "utf-8") # packetType, length, seqNum, data
						novel.arr[i][1] = unreliableSend(packet, sock, userIP, errRate,  "Resending Data..." )
				lock.release()
			i = i+1
				
def get_ack(sock, novel):
	sock.settimeout(None)
	while(True and novel.flag):
		bytesFromClient = sock.recvfrom(bufferSize)
		ct = t.time()
		packetType, seqNum = bytesFromClient[0].decode().split() #ACK
		if(packetType == str(ACK)):
			if(ct-novel.arr[int(seqNum)][1]<=timeOut and novel.arr[int(seqNum)][3]==False):
				lock.acquire()
				if(not novel.flag):
					break
				novel.arr[int(seqNum)][3] = True	
				print("\tReceiving Ackowledge... " + bytesFromClient[0].decode() + " \n")
				novel.counter += 1
				lock.release()

def RDTProtocol(novel, sock, userIP):

	print("\n\t************** RDT Protocol **************\n")

	print(novel.lastIndex)

	errRate = int(sys.argv[3]) 
	N = int(sys.argv[2]) # window size of the SRP --> 1,10,50,100

	novel.iter_start = 0
	novel.iter_end = N
	novel.N = N

	t_listen = threading.Thread(target=get_ack, args=(sock, novel, ))
	t_resend = threading.Thread(target=resending, args=(sock, novel, userIP, errRate, ))
	t_listen.start()

	#starting...
	lock.acquire()
	for i in range(novel.iter_start, novel.iter_end):
		packet = bytes(str(DATA) + " " + str(len(novel.arr[i][0])) + " " + str(i) + " " + novel.arr[i][0], "utf-8") # packetType, length, seqNum, data
		novel.arr[i][1] = unreliableSend(packet, sock, userIP, errRate, "Sending Data..." )
	lock.release()

	t_resend.start()

	while (True):
		lock.acquire()
		try:
			if(novel.arr[novel.iter_start][3]==True): 
				novel.iter_start += 1
				packet = bytes(str(DATA) + " " + str(len(novel.arr[novel.iter_end][0])) + " " + str(novel.iter_end) + " " + novel.arr[novel.iter_end][0], "utf-8") # packetType, length, seqNum, data
				novel.arr[novel.iter_end][1] = unreliableSend(packet, sock, userIP, errRate, "Sending Data...") #new sending, error can be occured here because of out of list
				novel.iter_end += 1
		except: # out of list
			lock.release()
			break; # no sending new line anymore
		lock.release()

	while(True):
		if(novel.counter == novel.iter_end):
			novel.flag = False # to terminate other threads
			close(novel.lastIndex, sock, userIP, errRate)
			break

			
# x = lastfile's seqNum, server send Fin with seqNum=x and get ACK with seqNum=x+1; client send Fin with seqNum=x+1 and get ACK with seqNum=x+2, 
def close(lastSending, sock, clientAddress, errRate):  
	sock.settimeout(timeOut)

	packet = bytes(str(FIN) + " " + str(lastSending), "utf-8")  

	_ = unreliableSend(packet, sock, clientAddress, errRate, "Finish ")
	while(True):
		try:
			bytesFromClient = sock.recvfrom(bufferSize)
			packetType, seqNum = bytesFromClient[0].decode().split() 
			if(packetType == str(ACK) and seqNum == lastSending+1):
				print("   \nReceiving Acknowledge... " + bytesFromClient[0].decode())
			elif(packetType == str(FIN) and seqNum == lastSending+1):
				print("   \nReceiving Finish... " + bytesFromClient[0].decode())
				packet = bytes(str(FIN) + " " +lastSending, "utf-8")  
				_ = unreliableSend(packet, sock, clientAddress, errRate, "Acknowledge ")
				break

		except socket.timeout:
			print("timeout_2")
	
	sock.close()

						
def unreliableSend(packet, sock, userIP, errRate, mes):  # errRate --> %1,5,10,20
	if errRate < rd.randint(0,100):
		print(mes + packet.decode())
		sock.sendto(packet, userIP)
	return t.time()			

def main():         
	serverport = int(sys.argv[1])  
	socketConnection(serverport)
			
if __name__ == "__main__":
	main()