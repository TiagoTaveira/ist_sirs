#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 28 23:31:12 2018

@author: vascopombo
"""
#############################################################
###################    IMPORTS    ###########################
#############################################################


import Tracker                      # ficheiro Tracker.py
import socket
import pickle                       # enviar data pelos sockets
from time import sleep
import simplecrypt
from pprint import pprint as pp
import math
import ssl
import sys

# os certificados do servidor e do kdc já vêm "instalados de fábrica" no tracker

SERVER_CERT = "./certificates/mainServer/mainServer.crt"
KDC_CERT = './certificates/KDC/kdc.crt'
ROOT_CA = './certificates/rootCA/rootCA.pem'

#############################################################
################   CONNECTION FUNCTIONS    ##################
#############################################################

def connectToManager(tracker): #TCP connection para ser bidireccional

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #criacao da socket TCP
    port = 9993
    host = 'localhost'

    address = (host, port)
    client.connect(address)



    msg = str(tracker.getID())          #mensagem a enviar ao server com o ID do tracker para ele meter na lista de trackers dele
    client.send(msg.encode())

    datakey = client.recv(4096)            #recebe a chave simetrica que o manager cria
    tracker.setsymKeyMT(datakey.decode())

    dataRadius = client.recv(4096)
    tracker.setRadius(dataRadius.decode())

    dataTuple = pickle.loads(client.recv(4096))
    tracker.setCenterPoint(dataTuple[0]) #this has de center point

    tracker.setAuthNr(dataTuple[1]) #this has the authNr



    tracker.pairTracker()         #muda o boolean do tracker de False para True para nao emparelhar com mais managers

    # client.close()


#############################################################
################    NEEDHAM-SCHROEDER     ###################
#############################################################

def connectToKDC(tracker):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock = ssl.wrap_socket(client, ca_certs = ROOT_CA, cert_reqs = ssl.CERT_REQUIRED, ssl_version = ssl.PROTOCOL_TLS)

    host = 'localhost'
    sock.connect((host, 7845))

    msg = (str(tracker.getID()), str(tracker.getAuthNr()))      # Send this tracker's id to KDC
    print("SENDING THIS TO KDC {}\n".format(msg))
    sock.send(pickle.dumps(msg))

    response = sock.recv(4096)    # Receive the ***encrypted*** package, to send to the server

    responseDec = pickle.loads(response)
    tracker.setSessionKeyTS(responseDec["SessionKey"][1])
    pp(responseDec)

    connectToServerForSKPropagation(responseDec)            #this is the dictionary with the session key
    sock.close()
    createTrackerMenu(tracker)


def connectToServerForSKPropagation(newData):

    # TODO
    # if (tracker.getPairingStatus() and not(tracker.getSessionKeyST() == '')):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssl_sock = ssl.wrap_socket(client, ca_certs = ROOT_CA, cert_reqs = ssl.CERT_REQUIRED, ssl_version = ssl.PROTOCOL_TLS)

    port = 9999
    host = 'localhost'
    address = (host, port)

    ssl_sock.connect(address)

    data = {}
    data['ID'] = "Tracker"

    # TODO encriptar data['MSG'] com a pub do servidor
    data['MSG'] = newData     # this MSG is encrypted with the server's pubkey

    # envia tuplo com session key e tracker id. Encriptado com a chave pub do server
    dataToSend = pickle.dumps(data)
    ssl_sock.send(dataToSend)
    try:
        aux = ssl_sock.recv(4096)
        aux_dec, aux_int = math.modf(float(aux.decode()))
        randNum = int(aux_int)

        checkId = randNum - 7

        ssl_sock.send(str(checkId).encode())
    except ValueError:
        print("\nNot yet paired with a manager. Please pair with a manager and then generate a session key.\n")

    try:
        confirmation = ssl_sock.recv(4096)
        if(confirmation.decode() == "OK TO SEND GPS"):
            print("\nSession Key established with success!\n")
            ssl_sock.close()
        else:
            raise ConnectionRefusedError()

    except ConnectionRefusedError:
        print("\nFailed to establish a Session Key with the Main Server.\n")
        ssl_sock.close()

#############################################################
################    OTHER FUNCTIONS     #####################
#############################################################


def startSendingGPS(tracker):
    try:
        if (tracker.getPairingStatus() and not(tracker.getSessionKeyST() == '')):
            port = input("What is the port number to send the GPS coordinates to?   ")
             #nao envia localizacao se o tracker ainda nao estiver emparelhado com um manager
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            host = 'localhost'
            address = (host, int(port))

            trackerId = str(tracker.getID())
            symKey = tracker.getsymKeyMT()
            sessionKey = tracker.getSessionKeyST()

            send_dict = {}
            send_dict["TrackerID"] = trackerId

            print("Starting to send GPS Location to Server...\n")
            sleep(1)

            while True:

                # tuple with timestamp of GPS coordinates and the actual coordinates --> (time, GPSCoord)
                tupleTimeGPS = tracker.gpsPackgBuilder()
                print("\nGPS LOCATION ==> {}\n".format(tupleTimeGPS))
                # encrypting only the GPSCoord
                print("Encrypting GPS Coordinates with symmetric key ...\n")
                encryptedGPS = simplecrypt.encrypt(symKey, pickle.dumps(tupleTimeGPS))

                checkIfSOS(tracker)
                sosStatus = tracker.getSosStatus()

                msg = {}
                msg['GPS Time'] = tupleTimeGPS[0]
                msg['GPSCoord'] = encryptedGPS

                print("Encrypting whole package with session key ...\n")
                encryptedMessage = simplecrypt.encrypt(sessionKey, pickle.dumps(msg))

                send_dict["MSG"] = encryptedMessage
                send_dict["SOS"] = sosStatus
                send_dict["TimeStamp"] = tupleTimeGPS[0]

                encryptedPackage = pickle.dumps(send_dict)
                client.sendto(encryptedPackage, address)
        else:
            raise ValueError()
    except (ValueError, AssertionError):
        print("\nYou must pair with a Manager first and then generate a SessionKey...\n")
        createTrackerMenu(tracker)


def checkIfSOS(tracker):
    radius = int(tracker.getRadius())
    if (((tracker.getPointX() - tracker.getCenterPointX())^2) + ((tracker.getPointY() - tracker.getCenterPointY())^2)  > radius^2):
        tracker.turnSosOn()
    else:
        tracker.turnSosOff()

def emparelhaComManager(tracker):
    print("Checking if the tracker is already paired with another Manager...")
    sleep(1)
    if not tracker.getPairingStatus():
        print("Pairing with Manager\n")
        sleep(1)
        connectToManager(tracker)
        sleep(1)
        print("Pairing Finished!\n")
        sleep(1)
    else:
        print("Unfortunetely the tracker is already paired with another Manager.\n")
    createTrackerMenu(tracker)


#############################################################
############   PARTE GRAFICA DOS MENUS    ###################
#############################################################


#menu principal da Tracker App
def inicialMenu():

    print("        Tracker Main Menu        ")
    print(' -------------------------------')
    print('|                               |')
    print('|     1. Create a Tracker       |')
    print('|     2. Exit                   |')
    print('|                               |')
    print(' -------------------------------')

    userinput = input("please enter an Option: ")
    if userinput == "1":
        createTracker()
    elif userinput == "2":
        exit()

def createTracker():
    print("Creating a Tracker...")
    t = Tracker.Tracker()
    sleep(1)

    print("Tracker created with the following ID: ", t.getID())
    sleep(1)
    createTrackerMenu(t)

def createTrackerMenu(t):

    print("        Tracker Options Menu     ")
    print(' -------------------------------')
    print('|                               |')
    print('|     1. Pair With Manager      |')
    print('|     2. Generate Session Key   |')
    print('|     3. Start Sending Location |')
    print('|     4. Go Back                |')
    print('|                               |')
    print(' -------------------------------')

    userinput = input("please enter an Option: ")
    if userinput == "1":
        emparelhaComManager(t)
    elif userinput == "2":
        connectToKDC(t)
    elif userinput == "3":
        startSendingGPS(t)
    elif userinput == "4":
        # TODO this is not working
        inicialMenu()

#############################################################
###################   MAIN DA APP   #########################
#############################################################


if __name__ == "__main__":
    try:
        inicialMenu()
    except KeyboardInterrupt:
        print("\nYou pressed CTRL+C. The application will shutdown now...\n")
        print("Cancelling GPS signal...")
        sleep(1)
        sys.exit(0)
