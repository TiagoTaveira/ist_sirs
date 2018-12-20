#!/usr/bin/env python3

import socket
import socketserver
import time
import sys
import os
import threading
import pickle
from pprint import pprint as pp
import random
import math
import simplecrypt
import ssl
from Manager import Manager
import struct

### GLOBAL VARIABLES ###
MANAGERS_LIST = []
SESSION_KEYS = []            # holds the session keys with trackers

# List of dictionaries to hold the positions of every tracker, with format :
# {"TrackerID1": [[{GPS_COORD1}], [{GPSCOORD2}], ...,]},
# {"TrackerID2": [[{GPS_COORD1}], [{GPSCOORD2}], ...,]}

GPS_DATABASE = []
SERVER_CERT = "./certificates/mainServer/mainServer.crt"
SERVER_PRIVATE_KEY = "./certificates/mainServer/mainServer.key"
ROOT_CA = "./certificates/rootCA/rootCA.pem"
KDC_CERT = './certificates/KDC/kdc.crt'

# **************************************************** #
#               Connection Classes - TCP               #
# **************************************************** #

class MySSLManager(socketserver.TCPServer):
    def __init__(self, server_address, RequestHandlerClass, certfile, keyfile, ssl_version = ssl.PROTOCOL_TLS, bind_and_activate = True):
        socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)
        self.certfile = certfile
        self.keyfile = keyfile
        self.ssl_version = ssl_version

    def get_request(self):
        newsocket, from_addr = self.socket.accept()
        connstream = ssl.wrap_socket(newsocket, server_side = True, certfile = self.certfile, keyfile = self.keyfile, ssl_version = self.ssl_version)
        return connstream, from_addr

class ThreadedManager(socketserver.ThreadingMixIn, MySSLManager):
    pass

class ThreadedManagerHandler(socketserver.StreamRequestHandler):
    ''' Main class for the Manager.
        It is instantiated once and generates the rest of the connection threads.'''

    def handle(self):

        data = self.request.recv(4096)
        receivedDict = pickle.loads(data)

        if (receivedDict['OP'] == 'REGISTER'):
            self.processRegister(receivedDict)

        if (receivedDict['OP'] == 'LOGIN'):

            test = self.verifyLogin(receivedDict['user'], receivedDict['password'])

            if test == -1:
                dat = ("LOGIN FAILED", test)
                send_dat = pickle.dumps(dat)
                self.request.send(send_dat)
            else:
                dat = ("LOGIN CONFIRMED", test)
                send_dat = pickle.dumps(dat)
                self.request.send(send_dat)

        if (receivedDict['OP'] == 'GET CURRLOC'):
            #TODO what to send?
            pass
        if (receivedDict['OP'] == 'GET HISTLOC'):
            list = self.getGPSOfTracker(receivedDict['managerID'], receivedDict['trackerID'])

            msg = struct.pack('>I', len(pickle.dumps(list))) + pickle.dumps(list)
            self.request.sendall(msg)
            # for i in list:
            #     list_send = pickle.dumps(i)
            #     self.request.send(list_send)

        if (receivedDict['OP'] == 'Change Radius'):
            #TODO what to do ?
            pass

        if (receivedDict['OP'] == "GET TRACKERS"):
            list = self.getAllTrackersByManager(receivedDict['id'])
            data = pickle.dumps(list)
            self.request.send(data)
            pass

        if (receivedDict['OP'] == "NEW TRACKER"):
            # print("MANAGER ID {}".format(receivedDict['managerID']))
            # print("TRACKER ID {}".format(receivedDict['trackerID']))
            # print("AUTHNUM ID {}".format(receivedDict['authNum']))

            self.addTrackerToManager(receivedDict['managerID'], receivedDict['trackerID'], receivedDict['authNum'])


    def processRegister(self, receivedDict):
        '''Register a new user and return it's user id to the ManagerApp'''

        if (self.usernameExists(receivedDict['user'])):
            self.connection.send("INVALID USERNAME".encode())
        else:
            user = receivedDict['user']
            password = receivedDict['password']
            phone = receivedDict['phone']
            mail = receivedDict['mail']
            name = receivedDict['name']
            age = receivedDict['age']

            newManager = Manager(user, password, phone, mail, name, age)
            MANAGERS_LIST.append(newManager)

            data = newManager.getID()
            print("THIS IS THE MANAGER ID {}\n  ".format(data))

            self.connection.send(str(data).encode())

    def usernameExists(self, username):
        '''Check if the given username already exists in the database'''
        for t in MANAGERS_LIST:
            if(t.getUser() == username):
                return True
        return False

    def verifyLogin(self, user, password):
        '''Verify if the user login is legit'''

        for i in MANAGERS_LIST:
            print("user in list: {}\n".format(i.getUser()))
            print("input username : {}\n".format(user))
            print("password in list: {}\n".format(i.getPassword()))
            print("input password : {}\n".format(password))

            if(i.getUser() == user and i.getPassword() == password):
                return i.getID()
        return -1


    def getAllTrackersByManager(self, managerId):
        for i in MANAGERS_LIST:
            if(i.getID() == managerId):
                return i.getTrackers()

    def getGPSOfTracker(self, managerId, trackerId):
        list = []
        try:
            for ii in GPS_DATABASE:
                if(ii['TrackerID'] == trackerId):
                    list.append(ii['GPSList'])
            return list
        except:
            print("There has been an error while retrieving the GPS history of tracker " + str(trackerId) + "\n")

    # def removeTrackerFromManager(self, managerId, trackerId):
    #     for i in MANAGERS_LIST:
    #         if(i.getID() == int(managerId)):
    #             i.removeTracker(int(trackerId), int(authNum))
    #             break

    def addTrackerToManager(self, managerId, trackerId, authNum):
        try:
            for i in MANAGERS_LIST:
                if (i.getID() == int(managerId)):
                    i.addTracker(int(trackerId), int(authNum))
                    print("TRACKER ID " + str(trackerId) +  " ADDED TO MANAGER.\n")
                    break
        except Exception:
            print("The user with id " + str(managerId) + " doesn't exist.\n")


    def getManagerById(self, managerUser):
        for i in MANAGER_LIST:
            if (i.getUser() == managerUser):
                return i.getID()

# **************************************************** #
#               Connection Classes - UDP               #
# **************************************************** #

class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass

class ThreadedUDPHandler(socketserver.BaseRequestHandler):
    ''' Class that handles UDP requests for the server.
        It is instantiated once per connection to the server.'''

    def handle(self):
        # receive GPS location
        dataReceived = self.request[0]
        gpsData = pickle.loads(dataReceived)
        print("RECEIVING GPS LOCATION FROM TRACKER : {}\n".format(gpsData['TrackerID']) )

        sessionKeyToUse = self.getSessionKey(gpsData['TrackerID'])
        try:
            decryptedInfoForServer = simplecrypt.decrypt(sessionKeyToUse, gpsData['MSG'])

            # Store the GPS location to associated ID
            dataToStore = {}
            dataToStore['TrackerID'] = gpsData['TrackerID']
            dataToStore['GPSList'] = [decryptedInfoForServer]
            dataToStore['SOS'] = gpsData['SOS']
            dataToStore['TimeStamp'] = gpsData['TimeStamp']

            GPS_DATABASE.append(dataToStore)

        except simplecrypt.DecryptionException:
            print("Unable to decrypt information. Are you the real tracker @ " + str(self.client_address[0]) + ":" + str(self.client_address[1]) + "??\n")

        # TODO sort for timestamps
        # TODO process if SOS == True
        # TODO remove tracker if disconnects or something
        # TODO update session key

    def getSessionKey(self, trackerId):
        for d in SESSION_KEYS:
            if(d['TrackerID'] == trackerId):
                return d['SessionKey'][1]

        return -1



# **************************************************** #
#   Connection classes - Main Server & KDC connector   #
# **************************************************** #

class MySSLMainServer(socketserver.TCPServer):
    def __init__(self, server_address, RequestHandlerClass, certfile, keyfile, ssl_version = ssl.PROTOCOL_TLS, bind_and_activate = True):
        socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)
        self.certfile = certfile
        self.keyfile = keyfile
        self.ssl_version = ssl_version

    def get_request(self):
        newsocket, from_addr = self.socket.accept()
        connstream = ssl.wrap_socket(newsocket, server_side = True, certfile = self.certfile, keyfile = self.keyfile, ssl_version = self.ssl_version)
        return connstream, from_addr

class ThreadedMainServer(socketserver.ThreadingMixIn, MySSLMainServer):
    pass



class ThreadedMainServerHandler(socketserver.StreamRequestHandler):
    ''' Main class for the server.
        It is instantiated once and generates the rest of the connection threads.'''

    def handle(self):

        data = self.connection.recv(4096)
        receivedDict = pickle.loads(data)

        if (receivedDict['ID'] == 'Tracker'):

            # call function to handle and establish the session key
            self.handleSessionKey(receivedDict['MSG'])


    def handleSessionKey(self, seshKeyDictionary):

        trackerID = seshKeyDictionary['SessionKey'][0]
        seshKey = seshKeyDictionary['SessionKey'][1]
        authNumber = seshKeyDictionary['SessionKey'][2]
        # try:
        for i in MANAGERS_LIST:
            for j in i.getAuthNumbers():
                # print("j[0] = {} --> {}".format(j[0], type(j[0])))
                # print("trackerID = {} --> {}".format(trackerID, type(trackerID)))
                # print("j[1] = {} --> {}".format(j[1], type(j[1])))
                # print("authnumber = {} --> {}".format(authNumber, type(authNumber)))

                if(str(j[0]) == str(trackerID) and str(j[1]) == str(authNumber)):

                    # Generating challenge random number, to prove identity
                    randNumGenerated = random.random() * 10000
                    aux_dec, aux_int = math.modf(randNumGenerated)

                    randNum = int(aux_int)
                    self.request.send(str(randNumGenerated).encode())

                    try:
                        confirmation = self.request.recv(4096)
                        if (int(confirmation.decode()) == randNum - 7):
                            SESSION_KEYS.append(seshKeyDictionary)
                            pp(SESSION_KEYS)
                            okString = "OK TO SEND GPS"
                            self.request.send(okString.encode())
                        else:
                            raise ConnectionRefusedError()

                    except ConnectionRefusedError:
                        print("FAILED CHALLENGE | Server could not verify Tracker's identity\n")

                # else:
                #     raise AssertionError()
        # except AssertionError:
        #     print("FAILED RANDOM NUMBER | Server could not verify Tracker's identity\n")

# **************************************************** #
#                   General Functions                  #
# **************************************************** #


def initAllServers(host, portTCP, portUDP, portMain):

    serverTCP = MySSLManager((host, portTCP), ThreadedManagerHandler, SERVER_CERT, SERVER_PRIVATE_KEY)

    serverUDP = ThreadedUDPServer((host, portUDP), ThreadedUDPHandler)

    serverMain = MySSLMainServer((host, portMain), ThreadedMainServerHandler, SERVER_CERT, SERVER_PRIVATE_KEY)

    ipTCP, portTCP = serverTCP.server_address
    ipUDP, portUDP = serverUDP.server_address
    ipMain, portMain = serverMain.server_address

    serverTCP_thread = threading.Thread(target=serverTCP.serve_forever)
    serverUDP_thread = threading.Thread(target=serverUDP.serve_forever)
    serverMain_thread = threading.Thread(target=serverMain.serve_forever)

    serverTCP_thread.daemon = True
    serverUDP_thread.daemon = True
    serverMain_thread.daemon = True

    serverTCP_thread.start()
    serverUDP_thread.start()
    serverMain_thread.start()

    print("----- Server MANAGER running in thread " +  serverTCP_thread.name + " @ address " + str(ipTCP) + " : " + str(portTCP) + " -----\n")
    print("----- Server TRACKER running in thread " +  serverUDP_thread.name + " @ address " + str(ipUDP) + " : " + str(portUDP) + " -----\n")
    print("-------- MAIN server running in thread " + serverMain_thread.name + " @ address " + str(ipMain) + " : " + str(portMain) + " -----\n")

    return serverTCP, serverUDP, serverMain


if __name__ == "__main__":

    print("Server is booting...")
    print("Port 9999 is reserved for server purposes, please don't use it.")
    time.sleep(1)

    while True:              # keep looping until `break` statement is reached
        print("\n")
        portNumManager = input("What port do you want the server to listen to Managers?   ")
        portNumTracker = input("What port do you want the server to listen to Trackers?   ")
        print("\n")   # <-- only one input line

        try:                 # get ready to catch exceptions inside here
            PORT_MANAGER = int(portNumManager)
            PORT_TRACKER = int(portNumTracker)

            if not ((1024 < PORT_MANAGER < 65000) and
                    (1024 < PORT_TRACKER < 65000) and
                    (PORT_MANAGER != PORT_TRACKER) and
                    (PORT_MANAGER != 9999 and PORT_TRACKER != 9999)):

                raise ValueError()


        except ValueError:      # <-- exception. handle it. loops because of while True
            print("One of the port numbers inserted is invalid. Insert a number between 1025 and 64999.")
        else:                # <-- no exception. break
            break



    HOST = "localhost"

    serverTCP, serverUDP, serverMain = initAllServers(HOST, PORT_MANAGER, PORT_TRACKER, 9999)
    try:
        while(True):
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nYou pressed CTRL+C. The SERVER will close now...\n")
        serverTCP.shutdown()
        serverUDP.shutdown()
        serverMain.shutdown()
