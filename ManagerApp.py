#!/usr/bin/env python3

#imports
import socket
import pickle
import secrets
import random
from simplecrypt import encrypt, decrypt
import getpass
import ssl
import os
from pprint import pprint as pp
import binascii
from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto import Random
from time import sleep
import struct

KDC_CERT = './certificates/KDC/kdc.crt'
SERVER_CERT = "./certificates/mainServer/mainServer.crt"
ROOT_CA = "./certificates/rootCA/rootCA.pem"

userKeys = []
INITIAL_VALUE = ''          # 16 bytes long
KEY = ''                    # 16 bytes long
PORT = ''                   # port given by user input @ start of program

key_bytes = 32



###   Encryption of PWs   ###

# Takes as input a 32-byte key and an arbitrary-length plaintext and returns a
# the ciphtertext. "iv" stands for initialization vector.
def encryptPW(key, password):
    assert len(key) == key_bytes

    # Choose a random, 16-byte IV. --> INITIAL_VALUE
    # Convert the IV to a Python integer.
    iv_int = int(binascii.hexlify(INITIAL_VALUE), 16)

    # Create a new Counter object with IV = iv_int.
    ctr = Counter.new(AES.block_size * 8, initial_value = iv_int)

    # Create AES-CTR cipher.
    aes = AES.new(key, AES.MODE_CTR, counter = ctr)

    # Encrypt and return IV and ciphertext.
    ciphertext = aes.encrypt(password)
    return ciphertext


# Takes as input a 32-byte key, a 16-byte IV, and a ciphertext, and outputs the
# corresponding plaintext.
def decryptPW(key, ciphertext):
    assert len(key) == key_bytes

    # Initialize counter for decryption. iv should be the same as the output of
    # encrypt().
    iv_int = int(INITIAL_VALUE.encode('hex'), 16)
    ctr = Counter.new(AES.block_size * 8, initial_value=iv_int)

    # Create AES-CTR cipher.
    aes = AES.new(key, AES.MODE_CTR, counter=ctr)

    # Decrypt and return the plaintext.
    plaintext = aes.decrypt(ciphertext)
    return plaintext

#--Other Methods--#

def checkUser(string):
    if string == "0":
        print("Returning to MainMenu...")
        mainMenu()
    elif string == "":
        return False
    else:
        return True

def checkPass(string):
    if string == "0":
        print("Returning to MainMenu...")
        mainMenu()
    elif len(string) < 8:
        return False
    else:
        return True

def checkPhone(string):
    if string == "0":
        print("Returning to MainMenu...")
        mainMenu()
    elif len(string) != 9 or string.isdigit()==False:
        return False
    else:
        return True

def checkMail(string):
    if string == "0":
        print("Returning to MainMenu...")
        mainMenu()
    elif string == "":
        return False
    else:
        return True

def checkName(string):
    if string == "0":
        print("Returning to MainMenu...")
        mainMenu()
    elif string == "":
        return False
    else:
        return True

def checkAge(string):
    if string == "0":
        print("Returning to MainMenu...")
        mainMenu()
    elif string== "" or string.isdigit() == False or int(string) < 18:
        return False
    else:
        return True

def generateGPS(): #funcao para gerar uma localizacao ao acaso
    latnr1 = random.randint(-90, 90)
    latnr2 = random.randint(1000, 99999)
    lat = str(latnr1) + "." + str(latnr2)

    lonnr1 = random.randint(-180, 180)
    lonnr2 = random.randint(1000, 99999)
    lon = str(lonnr1) + "." + str(lonnr2)

    currGPSloc = (lat, lon)
    return currGPSloc



#--menus--#

def mainMenu():
    print("        Main Menu        ")
    print(' -------------------------------')
    print('|                               |')
    print('|     1. Create a Manager       |')
    print('|     2. Login                  |')
    print('|     3. Exit                   |')
    print('|                               |')
    print(' -------------------------------')

    ipt = input("Choose an option: ")
    if ipt == "1":
        createManagerMenu()
        # mainMenu()
    elif ipt == "2":
        loginHandler()
    elif ipt == "3":
        exit()
    else:
        print("ERROR: Invalid input. Input must be 1, 2 or 3.")
        mainMenu()


def createManagerMenu():
    print("\n       Create Menu      ")
    print("\n**To return to the Main Menu type 0 anytime**\n")

    user = input("Please choose a username: ")
    while checkUser(user) == False:
        print("Invalid input. Can't Be Empty!!")
        user = input("Please choose a username: ")
    password = getpass.getpass("Please insert a password: ")
    while checkPass(password) == False:
        print("Invalid input. Must have at least 8 chars!!")
        password = getpass.getpass("Please insert a password: ")
    phone = input("Please insert a phone number: ")
    while checkPhone(phone) == False:
        print("Invalid input. Must have 9 digits!!")
        phone = input("Please insert a phone number: ")
    mail = input("Please insert your email: ")
    while checkMail(mail) == False:
        print("Invalid input. Can't be empty!!")
        mail = input("Please insert your email: ")
    name = input("Please insert your name: ")
    while checkName(name) == False:
        print("Invalid input. Can't be empty!!")
        name = input("Please insert your name: ")
    age = input("Please insert your Age: ")
    while checkAge(age) == False:
        print("Invalid input. You must be 18+!!")
        age = input("Please insert your Age: ")

    data = {}
    data['OP'] = "REGISTER"
    data['user'] = user

    data['password'] = encryptPW(KEY, password)
    data['phone'] = phone
    data['mail'] = mail
    data['name'] = name
    data['age'] = age

    s = openSock()
    dataToSend = pickle.dumps(data)
    s.send(dataToSend)

    receive = s.recv(4096)

    if(receive.decode() == "INVALID USERNAME"):
        #TODO volta a pedir o registo
        print("\nTHIS USERNAME IS ALREADY TAKEN! TRY AGAIN...\n")
        closeSock(s)
        mainMenu()
    else:
        manID = receive.decode()
        key = generateKey()

        userKeys.append((str(manID),key))
        loginMenu(user, manID)

def loginHandler():

    username_ipt = input("Please enter your username: ")
    password_ipt = getpass.getpass("Please enter your password: ")

    s = openSock()
    data = {}
    data['OP'] = "LOGIN"
    data['user'] = username_ipt


    data['password'] = encryptPW(KEY, password_ipt)

    dataToSend = pickle.dumps(data)

    s.send(dataToSend)

    aux = s.recv(4096)

    dat = pickle.loads(aux)

    confirmation = dat[0]
    id = dat[1]

    if confirmation == "LOGIN CONFIRMED":
        print("\nLOGIN SUCCESSFUL!\n")
        loginMenu(username_ipt, id)
    else:
        print("\nLOGIN FAILED!\n")
        mainMenu()

def loginMenu(username, id):
    print("        " + username +" Menu        ")
    print(' -------------------------------')
    print('|                               |')
    print('|     1. Pair a new Tracker     |')
    print('|     2. List My Trackers       |')
    print('|     3. Select Tracker         |')
    print('|     4. Back                   |')
    print('|                               |')
    print(' -------------------------------')

    userInput = input("Choose an option: ")
    if userInput == "1":
        connectToTracker(id)
        mainMenu()
    elif userInput == "2":
        s = openSock()
        data = {}
        data['OP'] = "GET TRACKERS"
        data['id'] = id

        dataToSend = pickle.dumps(data)
        s.send(dataToSend)

        rec = s.recv(4096)
        list = pickle.loads(rec)

        pp(list)
        closeSock(s)
        loginMenu(username, id)

    elif userInput == "3":
        print("\nTo go back type 0 \n")
        s = openSock()
        data = {}
        data['OP'] = "GET TRACKERS"
        data['id'] = id
        dataToSend = pickle.dumps(data)

        s.send(dataToSend)
        rec = s.recv(4096)
        list = pickle.loads(rec)
        print(list)

        trackID = input("\nInsert a Tracker ID from the list above: ")
        if trackID == "0":
            print("Returning to Menu...")
            closeSock(s)
            loginMenu(username, id)
        while int(trackID) not in list:
            print("Invalid ID. Please Insert an ID from the list.")
            trackID = input("Insert a Tracker ID from the list above: ")
        trackerMenu(trackID, id, username)
    elif userInput  == "4":
        mainMenu()
    else:
        print("ERROR: Invalid input. Input must be 1, 2, 3 or 4.")
        loginMenu(username, id)


def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data


def trackerMenu(tid, id, username):
    print("        " + tid +" Menu        ")
    print(' -------------------------------')
    print('|                               |')
    print('|     1. Get Current Location   |')
    print('|     2. Get Location History   |')
    print('|     3. Change Radius          |')
    print('|     4. Back                   |')
    print('|                               |')
    print(' -------------------------------')

    userInput = input("Choose an option: ")

    if userInput == "1":
        s = openSock()
        data = {}
        data['OP'] = "GET CURRLOC"
        data['trackerID'] = tid
        data['managerID'] = id

        dataToSend = pickle.dumps(data)
        s.send(dataToSend)

        rec = s.recv(4096)
        list = pickle.loads(rec)

        #TODO decrypt the location
        trackerMenu(tid, id, username)

    elif userInput == "2":
        s = openSock()
        data = {}
        data['OP'] = "GET HISTLOC"
        data['trackerID'] = tid
        data['managerID'] = id
        dataToSend = pickle.dumps(data)
        s.send(dataToSend)

        dataReceived = []

        # Read message length and unpack it into an integer
        raw_msglen = recvall(s, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        dataReceived = recvall(s, msglen)


        list = pickle.loads(dataReceived)
        newlist= []

        # get the symmetric key for this userId
        for i in userKeys:
            if i[0] == str(id):
                encryptKey = i[1]
                break

        print("\nDecrypting past GPS locations of tracker " + str(tid) + " .\nPlease wait...\n")

        for j in list:
            pseudoDecrDict = pickle.loads(j[0])       #gives only "GPSCoord" encrypted
            decryptedGPS = decrypt(encryptKey, pseudoDecrDict['GPSCoord'])
            newlist.append(pickle.loads(decryptedGPS))
        pp(newlist)
        trackerMenu(tid, id, username)

    elif userInput == "3":
        radius = input("Insert the new radius: ")
        # TODO change radius on demand
        trackerMenu(tid, id, username)
    elif userInput == "4":
        print("Returning to Menu...")
        loginMenu(username, id)
    else:
        print("ERROR: Invalid input. Input must be 1, 2 or 3.")
        loginMenu(username, id)

#--SymmetricKey--#

def generateKey():
    key = secrets.token_hex(32)
    return key


# Nominal way to generate a fresh key. This calls the system's random number generator (RNG).
def generatePassKey():
    '''Random key for AES'''
    key = Random.new().read(key_bytes)
    return key



#--Connection--#

def connectToTracker(id):
    print("\nSearching for TRACKER to pair with...\n")
    tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = 'localhost'
    port = 9993
    address = (host, port)

    tracker_socket.bind(address)

    tracker_socket.listen(5)

    clientTracker, addr = tracker_socket.accept()
    data = clientTracker.recv(4096)
    tid = data.decode()
    authNr = random.getrandbits(16)             # this random number is for the server to autenticate the tracker

    # Opening socket to communicate with Main Server
    s = openSock()

    idSent = {}
    idSent['OP'] = "NEW TRACKER"
    idSent['managerID'] = id
    idSent['trackerID'] = tid
    idSent['authNum'] = authNr

    sendId = pickle.dumps(idSent)
    s.send(sendId)
    closeSock(s)


    print("Tracker ID {}".format(data.decode()))

    for i in userKeys:
        if i[0] == str(id):
            key = i[1]
            break
    msg1 = key
    clientTracker.send(msg1.encode())
    msg2 = input("Define Radius for this Tracker: ")
    clientTracker.send(msg2.encode())
    msgGPS = generateGPS()
    msg3 = (msgGPS, authNr)
    clientTracker.send(pickle.dumps(msg3))
    sleep(2)
    print("\nTRACKER #{} successfuly paired!\n".format(tid))
    clientTracker.close()
    tracker_socket.close()

#--Main--#
def openSock():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock = ssl.wrap_socket(client, ca_certs=ROOT_CA, cert_reqs=ssl.CERT_REQUIRED, ssl_version=ssl.PROTOCOL_TLS)

    host = 'localhost'
    address = (host, PORT)
    sock.connect(address)

    return sock

def closeSock(sock):
    sock.close()

if __name__ == "__main__":

    while True:              # keep looping until `break` statement is reached
        print("\n")
        PORT = input("What is the port number that you wish to connect to?   ")
        print("\n")   # <-- only one input line

        try:                 # get ready to catch exceptions inside here
            PORT = int(PORT)
            if not ((1024 < PORT < 65000) and
                    (1024 < PORT < 65000) and
                    (PORT != 9999)):

                raise ValueError()

        except ValueError:      # <-- exception. handle it. loops because of while True
            print("The port number inserted is invalid. Insert a number between 1025 and 64999.")
        else:                # <-- no exception. break
            break


    KEY = generatePassKey()
    INITIAL_VALUE = Random.new().read(AES.block_size)
    try:
        mainMenu()
    except KeyboardInterrupt:
        print("\nYou pressed CTRL+C. The application will close now...\n")
        sleep(1)
