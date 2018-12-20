import socket
import pickle
import secrets
import random
from simplecrypt import encrypt
import getpass
import itertools
import ssl


class Manager:
    counter = 1
 #--Contructor--#
    def __init__(self, username, password, phone, email, name, age):

        self._username = username
        self._password = password
        self._phone = phone
        self._email = email
        self._name = name
        self._age = age
        self._trackerList = []
        self._authNumbers = []
        self._id = Manager.counter
        Manager.counter += 1


#-getters--#
    def getID(self):
        return self._id

    def getUser(self):
        return self._username

    def getPassword(self):
        return self._password

    def getPhone(self):
        return self._phone

    def getEmail(self):
        return self._email

    def getName(self):
        return self._name

    def getAge(self):
        return self._age

    def getTrackers(self):
        return self._trackerList

    def getAuthNumbers(self):
        return self._authNumbers


#--setters--#

    def setUser(self, newUser):
        self._username = newUser
        return self._username

    def setPassword(self, newPass):
        self._password = newPass
        return self._password

    def setPhone(self, newPhone):
        self._phone = newPhone

    def setEmail(self, newMail):
        self._email = newMail

    def setName(self, newName):
        self._name = newName

    def setAge(self, newAge):
        self._age = newAge


#--Other Methods--#

    def addTracker(self, trackerId, authNum):
        self._trackerList.append(trackerId)
        self.addAuthNumbers(trackerId, authNum)

    def removeTracker(self, id, authNum):
        self._trackerList.remove(id)
        self.removeAuthNumbers(trackedId, authNum)

    def addAuthNumbers(self, trackerId, authNum):
        print("Adding authnumber to MANAGER\n")
        self._authNumbers.append((trackerId, authNum))

    def removeAuthNumbers(self, trackerId, authNum):
        for i in self._authNumbers:
            if (i[0] == trackerId):
                self._authNumbers.remove(i)

    def generateGPS(self): #funcao para gerar uma localizacao ao acaso
        latnr1 = random.randint(-90, 90)
        latnr2 = random.randint(1000, 99999)
        lat = str(latnr1) + "." + str(latnr2)

        lonnr1 = random.randint(-180, 180)
        lonnr2 = random.randint(1000, 99999)
        lon = str(lonnr1) + "." + str(lonnr2)

        currGPSloc = (lat, lon)
        return currGPSloc
