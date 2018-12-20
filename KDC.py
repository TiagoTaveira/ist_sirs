#!/usr/bin/env python3

from time import sleep
import secrets
import threading
import socket
import pickle
from pprint import pprint as pp
import ssl
import socketserver

### GLOBAL VARIABLES | CERTIFICATES ###

KDC_CERT = './certificates/KDC/kdc.crt'
KDC_PRIVATE_KEY = './certificates/KDC/kdc.key'
SERVER_CERT = "./certificates/mainServer/mainServer.crt"
ROOT_CA = "./certificates/rootCA/rootCA.pem"



class MySSLKDCServer(socketserver.TCPServer):

    def __init__(self, server_address, RequestHandlerClass, certfile, keyfile, ssl_version = ssl.PROTOCOL_TLS, bind_and_activate = True):
        socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)
        self.certfile = certfile
        self.keyfile = keyfile
        self.ssl_version = ssl_version

    def get_request(self):
        newsocket, from_addr = self.socket.accept()
        connstream = ssl.wrap_socket(newsocket, server_side = True, certfile = self.certfile, keyfile = self.keyfile, ssl_version = self.ssl_version)
        return connstream, from_addr

class ThreadedKDCServer(socketserver.ThreadingMixIn, MySSLKDCServer):
    pass

class ThreadedKDCServerHandler(socketserver.StreamRequestHandler):
    ''' Main class for the KDC.
        It is instantiated once and generates the rest of the connection threads.'''

    def handle(self):

        data = self.connection.recv(4096)

        receivedMsg = pickle.loads(data)

        #tracker ID and tracker authNr
        msg = self.generateSessionKey(receivedMsg[0], receivedMsg[1])

        pp(msg)

        # this package should go already encrypted with server's pubkey

        self.request.send(pickle.dumps(msg))
        self.request.close()



    def generateSessionKey(self, trackerID, authNr):
        #aqui temos a funcao que manda o pacote do protocolo para o tracker
        key = self.generateKey()
        sessionKey =  (trackerID, key, authNr)

        #TODO encrypt package with server pub key
        encryptedPkg = {}
        encryptedPkg["TrackerID"] = trackerID        # for example: TrackerID = T0123091u4
        encryptedPkg["SessionKey"] = sessionKey

        return encryptedPkg

    def generateKey(self):
        key = secrets.token_hex(16)
        return key



if __name__ == "__main__":

    print("Booting up the KDC ...\n")

    sleep(1)

    serverKDC = MySSLKDCServer(('localhost', 7845), ThreadedKDCServerHandler, KDC_CERT, KDC_PRIVATE_KEY)

    serverKDC_thread = threading.Thread(target=serverKDC.serve_forever)
    serverKDC_thread.daemon = True
    serverKDC_thread.start()

    print("KDC is ready to operate.\n")

    try:
        while(True):
            sleep(1)
    except KeyboardInterrupt:
        print("\nYou pressed CTRL+C. The KDC will close now...\n")
        serverKDC.shutdown()
