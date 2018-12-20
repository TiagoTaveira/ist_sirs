#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 28 22:49:51 2018

@author: vascopombo
"""
import random
import datetime
 


class Tracker:
    
    #construtor
    def __init__(self):
        randomnr = random.getrandbits(16)
        
        
        #fazer check se o numero gerado automaticamente esta na lista de ids
        #se nao estiver podemos criar o tracker com o id. Podera ter que ser
        #feito no server

        self._id = randomnr        #id da pulseira
        self._symKeyMT = ""        #chave simetrica entre tracker e manager
        self._sessionKeyTS = ""    #chave de sessao para enviar os pacotes ao server
        self._isPaired = False     #boolean para so eparelhar a pulseira com um manager
        self._sos = False
        self._centerPoint = ('', '')
        self._centerPointX = 0
        self._centerPointY = 0
        self._pointX = 0
        self._pointY = 0
        self._radius = 0
        self._authNr = 0


#############################################################
###################     GETTERS      ########################
#############################################################
        
    def getRadius(self):
        return self._radius
    
    def getCenterPoint(self):
        return self._centerPoint
    
    def getID(self):
        return self._id
    
    def getCurrGPS(self): #funcao para gerar uma localizacao ao acaso
        lat = self._centerPoint[0]
        lon = self._centerPoint[1]
        
        latPoint = int(lat.split(".")[1])
        self._centerPointX = latPoint #usado para o calculo do check se esta no interior do circulo
        lonPoint = int(lon.split(".")[1])
        self._centerPointY = lonPoint #usado para o calculo do check se esta no interior do circulo
        
        
        
        latnr1 = lat.split(".")[0]
        latnr2 = random.randint(latPoint - int(self._radius), latPoint + int(self._radius))
        self._pointX = latnr2
        lat = str(latnr1) + "." + str(latnr2)
        
        lonnr1 = lon.split(".")[0]
        lonnr2 = random.randint(lonPoint - int(self._radius), lonPoint + int(self._radius))
        self._pointY = lonnr2
        lon = str(lonnr1) + "." + str(lonnr2)
        
        currGPSloc = (lat, lon)
        return currGPSloc
    
    def getCurrTime(self): #esta funcao retorna o tempo atual no formato abaixo especificado
        currTime = datetime.datetime.now().strftime("%d-%m-%Y | %H.%M.%S")
        return currTime
    
    def getsymKeyMT(self):
        return self._symKeyMT
    
    def getPairingStatus(self):
        return self._isPaired
    
    def getSessionKeyST(self):
        return self._sessionKeyTS
    
    def getSosStatus(self):
        return self._sos
    
    def getCenterPointX(self):
        return self._centerPointX
    
    def getCenterPointY(self):
        return self._centerPointY
    
    def getPointX(self):
        return self._pointX
    
    def getPointY(self):
        return self._pointY
    
    def getAuthNr(self):
        return self._authNr
    
#############################################################
###################     SETTERS      ########################
#############################################################
    
    
    def setsymKeyMT(self, newKey):
        self._symKeyMT = newKey
        
    def setSessionKeyTS(self, newKey):
        self._sessionKeyTS = newKey
        
    def pairTracker(self):
        self._isPaired = True
        
    def unpairTracker(self):
        self._isPaired = False
    
    def turnSosOn(self):
        self._sos = True
        
    def turnSosOff(self):
        self._sos = False
        
    def setRadius(self, radius):
        self._radius = radius
    
    def setCenterPoint(self, centerPoint):
        self._centerPoint = centerPoint
        
    def setAuthNr(self, nr):
        self._authNr = nr
            
  
    
#############################################################
###################     FUNCOES      ########################
#############################################################
        
        
    def gpsPackgBuilder(self): #cria o tuplo para retornar ao TrackerApp
        tupleTimeGPS = (self.getCurrTime(), self.getCurrGPS())
        return tupleTimeGPS