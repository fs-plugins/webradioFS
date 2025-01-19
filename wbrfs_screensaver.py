# -*- coding: utf-8 -*-
#import codecs
#import Screens.Standby
from Screens.Screen import Screen
#from Screens.Standby import Standby,TryQuitMainloop
#from Screens.InfoBarGenerics import InfoBarShowHide
#from Screens.ChoiceBox import ChoiceBox
#from Screens.InputBox import InputBox
#from Screens.VirtualKeyBoard import VirtualKeyBoard
#from Screens.MessageBox import MessageBox
#from Screens.LocationBox import LocationBox
#from Screens.HelpMenu import HelpableScreen
#from Screens.Volume import Volume
#from Screens.InfoBarGenerics import NumberZap
#from Screens.InfoBarGenerics import InfoBarChannelSelection#, InfoBarNotifications
#from Screens.ChannelSelection import service_types_radio
#from Screens import Standby
#from Screens.EventView import  EventViewEPGSelect
#from Screens.EpgSelection import EPGSelection
#from Screens.ChannelSelection import ChannelSelection
#from Screens.PictureInPicture import PictureInPicture

#from ServiceReference import ServiceReference




#from Components.VideoWindow import VideoWindow
from Components.AVSwitch import AVSwitch
##from Components.ActionMap import NumberActionMap, HelpableActionMap
#from Components.ActionMap import ActionMap
#from Components.ScrollLabel import ScrollLabel
from Components.Label import Label
#from Components.Sources.List import List
#from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
#from Components.MultiContent import MultiContentEntryText,MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap
#from Components.config import *
#from Components.Input import Input
#from Components.ConfigList import ConfigListScreen, ConfigList
#from Components.config import getConfigListEntry,ConfigInteger, ConfigYesNo, ConfigSelection, ConfigNumber, ConfigSubList, config, NoSave, configfile, ConfigSequence
#from Components.ServiceEventTracker import ServiceEventTracker
#from Components.ServicePosition import ServicePositionGauge
#from Components.PluginComponent import plugins
#from Components.VolumeControl import VolumeControl
#from Components.SystemInfo import SystemInfo
#from Components.Sources.ServiceList import ServiceList
#from Components.Slider import Slider
#+++++++++++++++++++++++++++#


from enigma import ePoint,eSize, eListbox, eTimer,ePicLoad
from enigma import getDesktop
#from enigma import eDVBVolumecontrol
#from enigma import iPlayableService, iServiceInformation, eServiceReference,eServiceCenter, getBestPlayableServiceReference, iRdsDecoder
#from enigma import eConsoleAppContainer
#from enigma import eEPGCache, gFont,RT_HALIGN_LEFT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_WRAP
#from enigma import eServiceCenter, iRdsDecoder 


#from GlobalActions import globalActionMap
#from Plugins.Plugin import PluginDescriptor

from Tools.LoadPixmap import LoadPixmap
#from Tools import Notifications
#from Tools.Directories import copyfile,resolveFilename, SCOPE_PLUGINS, fileExists, SCOPE_CURRENT_SKIN, SCOPE_SKIN_IMAGE
#import threading, uuid
#import fnmatch

#import os, re
#import sys
import random
#from time import *
#import time
#import datetime
#import base64
#import codecs

########################################################
class wbrfs_diashow(Screen):
    def __init__(self, session,filelist,art,sets,dpkg):
        self.filelist=filelist
        if art=="slideshow_random": 
            self.art='Random'
            random.shuffle(self.filelist)
        else:
            self.art='Sorted'
            self.filelist.sort(key=lambda x: "".join(x[1]).lower())
        self.index=0 #index
        self.akt_index=0 #index

        self.textcolor = str(sets["color"])
        if not self.textcolor.startswith("#"):
                    self.textcolor="#"+ self.textcolor #"#FFFFFF"
        if len(self.textcolor) != 7 and len(self.textcolor) != 9: self.textcolor = "#FFFFFF"

        self.bgcolor = str(sets["bgcolor"])
        if not self.bgcolor.startswith("#"):
                    self.bgcolor="#"+ self.bgcolor #"#FFFFFF"
        if len(self.bgcolor) != 7 and len(self.bgcolor) != 9: self.textcolor = "#000000"

        self.slidetime= sets["slideshow_time"]
        self.txt= False #i_line
        space = sets["slideshow_space"]
        #self.sTitle=""
        self.slideshow=1
        #self.onChangedEntry = []
        #self.selectionChanged() 

        size_w = getDesktop(0).size().width()
        size_h = getDesktop(0).size().height()
        self.skin = "<screen position=\"0,0\" zPosition=\"5\" size=\"" + str(size_w) + "," + str(size_h) + "\" flags=\"wfNoBorder\" > \
            <eLabel position=\"0,0\" size=\""+ str(size_w) + "," + str(size_h) + "\" backgroundColor=\""+ self.bgcolor +"\" /><widget name=\"pic\" zPosition=\"1\" position=\"" + str(space) + "," + str(space) + "\" size=\"" + str(size_w-(space*2)) + "," + str(size_h-(space*2)) + "\" alphatest=\"on\" /> \
            <widget name=\"point\" position=\""+ str(space+5) + "," + str(space+2) + "\" size=\"20,20\" zPosition=\"1\" pixmap=\"skin_default/icons/record.png\" alphatest=\"on\" /> \
            <widget name=\"play_icon\" position=\""+ str(space+25) + "," + str(space+2) + "\" size=\"20,20\" zPosition=\"1\" pixmap=\"skin_default/icons/ico_mp_play.png\"  alphatest=\"on\" /> \
            <widget name=\"pause_icon\" position=\""+ str(space+25) + "," + str(space+2) + "\" size=\"20,20\" zPosition=\"1\" pixmap=\"skin_default/icons/ico_mp_pause.png\"  alphatest=\"on\" /> \
            <widget name=\"rs\" position=\""+ str(space+50) + "," + str(space+2) + "\" size=\"20,20\" zPosition=\"1\" font=\"Regular;20\" halign=\"left\" foregroundColor=\"" + self.textcolor + "\" transparent=\"1\" /> \
            <widget source=\"file\" render=\"Label\" position=\""+ str(space+70) + "," + str(space) + "\" zPosition=\"1\" size=\""+ str(size_w-(space*2)-50) + ",25\" font=\"Regular;20\" halign=\"left\" foregroundColor=\"" + self.textcolor + "\"  noWrap=\"1\" transparent=\"1\" /> </screen>"

        Screen.__init__(self, session)

        self["rs"] = Label(self.art[0])
        self["point"] = Pixmap()
        self["pic"] = Pixmap()
        self["play_icon"] = Pixmap()
        self["pause_icon"] = Pixmap()
        self["pause_icon"].hide()
        self.or_index=None
        self.old_index=None
        self.pause=0
        self.load=False
        #self.txt = False

        self["file"] = StaticText(_("please wait, loading picture..."))
        self.currPic = []
        self.alt_pic=None
        self.shownow = True
        self.maxentry = len(self.filelist)-1
        #if  len(self.filelist) <1:
        #    self.close(2)
        #else:
            #self.maxentry = len(self.filelist)-1

        #if self.art=="Random":
        #        self.index = random.randint(0, self.maxentry)
        self.picload = ePicLoad()
        #self.picload.PictureData.get().append(self.finish_decode)
        self.slideTimer = eTimer()
        if dpkg:
                   self.picload_conn = self.picload.PictureData.connect(self.finish_decode)
                   self.slideTimer_conn = self.slideTimer.timeout.connect(self.slidePic)
        else:
                    self.picload.PictureData.get().append(self.finish_decode)
                    self.slideTimer.callback.append(self.slidePic)
        #if self.maxentry >= 0:
        self.onLayoutFinish.append(self.setPicloadConf)

    def setPicloadConf(self):
        self.instance.setZPosition(5)
        sc = AVSwitch().getFramebufferScale() #getScale()
        self.picload.setPara([self["pic"].instance.size().width(), self["pic"].instance.size().height(), sc[0], sc[0], False, 1, self.bgcolor])
        if self.txt == False:
            self["file"].setText("")
        self.start_decode()

    def ShowPicture(self):
        if self.shownow and len(self.currPic):
                    self.shownow = False
                    if self.txt == True: self["file"].setText(self.currPic[0])
                    self.lastindex = self.currPic[1]
                    self.source_typ=self.currPic[0].split(".")[-1]
                    self.akt_index=self.index
                    self["pic"].instance.setPixmap(self.currPic[2])
                    self.currPic = []
                    if self.maxentry > 0:
                            self.next()
                    self.start_decode()

    def finish_decode(self, picInfo=""):
        self["point"].hide()
        self.load=False
        ptr = self.picload.getData()
        if ptr != None:
            text = ""
            try:
                text = picInfo.split('\n',1)
                text_name= text[0].split('/')[-1]
                text = "(" + str(self.index+1) + "/" + str(self.maxentry+1) + ") " + text_name
            except:
                pass
            self.currPic = []
            self.currPic.append(text)
            self.currPic.append(self.index)
            self.currPic.append(ptr)
            #self.currPic.append("original")
            self.ShowPicture()

    def start_decode(self):
                self.lastindex=self.index
                pic=self.filelist[self.index][0]
                self.picload.startDecode(pic)
                self["point"].show()
                self.load=True
                if self.slideshow ==1 and self.pause==0:
                        self["play_icon"].show()
                        self.slideTimer.start(self.slidetime*1000)
    def next(self):
                #if self.art=="Random" and self.slideshow==1:
                #    self.index = random.randint(0, self.maxentry)
                #else:
                self.index += 1    
                if self.index > self.maxentry: 	self.index = 0

    def prev(self):
        self.index = self.akt_index-1
        if self.index < 0:
            self.index = self.maxentry

    def slidePic(self):
        if self.slideshow==1 and self.pause==0: self["play_icon"].show()
        self.shownow = True
        self.ShowPicture()

    def PlayPause(self):
        if self.slideTimer.isActive():  #pause start
            self.old_index= self.akt_index
            self.slideTimer.stop()
            self["play_icon"].hide()
            self["pause_icon"].show()
            self.pause=1
        else:
             self.Pause_end()

    def Pause_end(self):
            #if not self.slideTimer.isActive():self.slideTimer.start(self.slidetime*1000)
            if self.art=="random":
                self.txt = False
                self["file"].setText("")
            if self.old_index: self.index = self.old_index
            self.old_index=None
            self["play_icon"].show()
            self["pause_icon"].hide()
            self.slideshow=1
            self.pause=0
            self.go_Pic(self.index)

    def Slide_stop(self):
        self.slideTimer.stop()
        self.old_index=None
        self["play_icon"].hide()
        self["pause_icon"].hide()
        self.slideshow=0

    def prevPic(self):
        if self.load==False:
            if self.slideTimer.isActive():self.PlayPause()
            self.currPic = []
            self.prev()
            self.start_decode()
            self.shownow = True

    def nextPic(self):
        if self.load==False:
            if self.slideTimer.isActive():self.PlayPause()
            self.shownow = True
            self.ShowPicture()

    def go_Pic(self,index=0):
        #self.picload.startDecode(self.filelist[index][0])
        self.next()
        self.shownow = True
        self.start_decode()

    def faster(self):
                if self.slidetime > 2:
                    self.slidetime = self.slidetime-1
                    self.slidetime_msg()

    def slower(self):
                self.slidetime = self.slidetime+1
                self.slidetime_msg()

    def slidetime_msg(self):
                sl_text=_("Slide Time has been changed to")+" "+str(self.slidetime)+" "+_("seconds")
                self.session.open(MessageBox,sl_text, MessageBox.TYPE_INFO, timeout = 3)
                #self.meld_screen(sl_text,"webradioFS - Info",None,20)

    def toggle_art(self):
        if self.art == "Random":
            self.art = "Sorted"
            self.filelist.sort(key=lambda x: "".join(x[1]).lower())
        else:
            self.art = "Random"
            random.shuffle(self.filelist)
            self["rs"].setText(self.art[0])


    def Exit(self):
        del self.picload
        self.close() 