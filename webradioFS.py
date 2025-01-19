# -*- coding: utf-8 -*-
###############################################################################
# webradioFS von shadowrider
###############################################################################

from . import pyvers1, _
import codecs
import Screens.Standby
from Screens.Screen import Screen
from Screens.Standby import Standby,TryQuitMainloop
from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import InputBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MessageBox import MessageBox
from Screens.LocationBox import LocationBox
try:
    from Screens.HelpMenu import HelpableScreen,HelpMenu
    menu_ok=True
except:
    menu_ok=None
try:
    from Screens.VolumeControl import Volume
except:
    from Screens.Volume import Volume    
from Screens.InfoBarGenerics import InfoBarSeek, NumberZap
from Screens.InfoBarGenerics import InfoBarChannelSelection, InfoBarNotifications
from Screens.ChannelSelection import service_types_radio
from Screens import Standby

from ServiceReference import ServiceReference

from Components.VideoWindow import VideoWindow
from Components.AVSwitch import AVSwitch
from Components.ActionMap import NumberActionMap, HelpableActionMap
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from Components.Label import Label
from Components.Sources.List import List
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Components.config import *
from Components.Input import Input
from Components.ConfigList import ConfigListScreen, ConfigList
from Components.config import getConfigListEntry,ConfigInteger, ConfigYesNo, ConfigText, ConfigSelection, ConfigNumber, ConfigSubList, config, NoSave, configfile, ConfigSequence, ConfigSubsection,ConfigNothing,ConfigOnOff
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ServicePosition import ServicePositionGauge
from Components.SystemInfo import SystemInfo
from Components.Sources.ServiceList import ServiceList
from Components.Slider import Slider
from Components.VolumeControl import VolumeControl
#+++++++++++++++++++++++++++#

from enigma import eSlider,ePoint,eSize, eListbox, eTimer,ePicLoad
from enigma import getDesktop, quitMainloop, eActionMap
from enigma import eDVBVolumecontrol
from enigma import iPlayableService, iServiceInformation, eServiceReference,eServiceCenter, getBestPlayableServiceReference, iRdsDecoder
from enigma import eConsoleAppContainer
from enigma import eEPGCache, gFont,RT_HALIGN_LEFT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_WRAP
from enigma import eServiceCenter, iRdsDecoder,gRGB
try:
    from enigma import eWindowStyleManager
except:
    pass
from GlobalActions import globalActionMap
from Plugins.Plugin import PluginDescriptor

from Tools.LoadPixmap import LoadPixmap
from Tools.BoundFunction import boundFunction
from Tools import Notifications
from Tools.Directories import copyfile,resolveFilename, SCOPE_PLUGINS, fileExists, SCOPE_CURRENT_SKIN, SCOPE_SKIN_IMAGE ,pathExists
import threading, uuid
import fnmatch
from sqlite3 import dbapi2 as sqlite

from twisted.internet.reactor import callInThread
if pyvers1==3:
    from configparser import ConfigParser#py3
    from urllib.parse import quote,quote_plus,urlparse
    from requests import get, exceptions  #get, 
else:
    from ConfigParser import ConfigParser
    from urllib import quote,quote_plus
    from urlparse import urlparse
from skin import parseColor
import os, re, shutil,types 
import sys
import random
import time
import datetime
import base64
import codecs
import xml.etree.cElementTree
from xml.etree.cElementTree import fromstring, ElementTree

import socket 

from .wbrfs_funct import read_settings1
from .ext import ext_l4l
l4l_set=ext_l4l()

myname = "webradioFS"
myversion = "22.03"
wbrfs_saver=None
versiondat=(2025,18,1)

streamplayer=None
manuell=0
online=0
zs=False
starter_stream=None
def starter_set(akt="",wert=None):
    global starter_stream
    config.plugins.webradioFS = ConfigSubsection()
    config.plugins.webradioFS.wbrfsstartstream = ConfigText(default="pvr1,0")
    if akt=="read":
        starter_stream=config.plugins.webradioFS.wbrfsstartstream.value

    elif wert and akt=="write":
        config.plugins.webradioFS.wbrfsstartstream.setValue(wert)
        config.plugins.webradioFS.wbrfsstartstream.save()
        configfile.save()

startsets=read_settings1().reading(("exp",""))
sets_exp=startsets[0]
write_debug=sets_exp["debug"]

web_liste_streams=[]
web_liste_favs=[]
pic_urls=[]
pic_art="png"
right_site=None
listenbreite=600
skin_ignore=False 

rs=open("/var/webradioFS_debug.log","w")
rs.close()


extplayer=False
try:
    extplayer=config.plugins.serviceapp.servicemp3.replace.value
except:
   pass
###########################################
pcfs=False
sispmctl=False
l4l_info= {"Station":"","Fav":"","Bitrate":"","Genres":"","rec":0,"akt_txt":"","art":"Group","Logo":"","Len":0}
#######################################
saver_list=[("wechsel",_("rotation")),("big",_("only show big pictures")),("no big",_("show no big pictures")),("no picture",_("show no pictures")),("black",_("pure black")),("slideshow_sorted",_("slideshow sorted")),
            ("slideshow_random",_("slideshow random")),("theme_images",_("theme images")),("tv",_("TV")),("Play_Video",_("Play Video")),("Play_Video_sort",_("Play Video sorted")),
           ("Play_Video_rand",_("Play Video random")),("Show_logo",_("Show logo"))]

if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/picscreensaver"):
    saver_list.append(("picscreensaver","Plugin Pic Screensaver"))
    picscreensaver=True
else:
    saver_list.append(("not1","Pic Screensaver"+ _(" (not installed)")))
    picscreensaver=False
try:
    from Plugins.Extensions.PictureCenterFS.plugin import Pic_Thumb,Pic_Full_View3 as Pic_Full_View,PictureCenterFS7 as PictureCenter
    saver_list.append(("pcfs_slideshow",_("Start Plugin PictureCenterFS")))
    pcfs=True
    pcfs2=(23,_("Open PictureCenterFS"))
except:
      saver_list.append(("not2","PictureCenterFS"+ _(" (not installed)")))
      pcfs2=(23,_("None"))

if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/sispmctl"): 
        sispmctl=True

DPKG = False

import requests
def threadGetPage(url, success, fail, art):
    try:
        response = get(url)
        response.raise_for_status()
    except exceptions.RequestException as error:
        fail(error)
    else:
        if art==2:
            fh=open("/tmp/.wbrfs_pic","wb")
            fh.write(response.content)
            fh.close()
            success("ok")
        else:
            success(str(response.content))

def set_l4l():
  global L4LwbrFS
  global l4ls,l4lR,l4lsa,l4l
  try:
    from Plugins.Extensions.LCD4linux.module import L4Lelement
    L4LwbrFS = L4Lelement()
    l4l=True
  except:
    l4l=None
    L4LwbrFS = None
    l4ls=None
    l4lR=None
  if L4LwbrFS:
            l4lsa=("True","1","True","3","True","0","30","20","1","True","0","0","20","1","True","0","60","20","1","True","2","0","200","True","0","100","200","40","22","white")
            l4ls=sets_view["l4l"].split(",")
            if len(l4ls)<30: 
                i = 0
                set=[]
                while i < 30:
                   try:
                       set.append(l4ls[i])
                   except:
                       set.append(l4lsa[i])
                   i+=1
                l4ls=set
            l4lR=True
            if str(l4ls[0])=="False":
                L4LwbrFS = None

FBts_liste=[
  (0,_("Play")),(1,_("Exit")),(2,_("Exit")),(3,_("Stream-Tools")),(4,_("None")),
  (5,_("Chillen")),(6,_("Sleeptimer")),(7,_("Favoriten")),(8,_("None")),(9,_("Edit/Info")),
  (11,_("Played-Stream Info")),(12,_("Preview Favorit-File")),(13,_("Next Favorit-File")),(14,_("Stop Playing")),
  (15,_("Down")),(16,_("Up")),(17,_("Save Title-Info")),(18,_("Zap down")),(19,_("Zap up")),
  (20,_("TV or Video: prev")),(21,_("TV or Video: next")),(22,_("TV")),pcfs2,(24,_("Play my files")),(25,_("None"))] 
tasten_name=("ok","cancel","tv","red","red_long",
             "green","green_long","yellow","yellow_long","blue",
             "blue_long","info","prevBouquet","nextBouquet","halt",
             "down","up","text","zapdown","zapup",
             "rewind","fastfor","pvr","subtitle","play_records")


schwarz = 0x000000
weiss=0xFFFFFF
orange=0xf47d19
center=RT_HALIGN_CENTER | RT_VALIGN_CENTER
left=RT_HALIGN_LEFT | RT_VALIGN_CENTER
left_wrap=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP
admin=None
session = None
streamtitel = ""
streamplayer = None
satradio = None
onwbrScreenSaver = None
onwbrInfoScreen = None
a_schleife=None

ripper_installed=False
cover_save={"path":None,"titel":None,"cache":None}
plugin_path = "/usr/lib/enigma2/python/Plugins/Extensions/webradioFS"
def_pic="/usr/lib/enigma2/python/Plugins/Extensions/webradioFS/skin/images/wbrfsdef.png"
noCoverPixmap = LoadPixmap(cached=True, path=def_pic)
offtimer = "starten"
DWide = getDesktop(0).size().width()
DHoehe = getDesktop(0).size().height()
sd=0
if DWide < 730:
    skin_ext=plugin_path +"/skin/SD/"
    font=20
    sd=1
elif DWide < 1030:
    skin_ext=plugin_path +"/skin/XD/"
    font=20
    sd=2
elif DWide < 1300:
    skin_ext=plugin_path +"/skin/HD/"
    font=22
    sd=3
else:
    skin_ext=plugin_path +"/skin/fHD/"
    font=35
    sd=4
DHoehe = getDesktop(0).size().height()
wbrfs_no_scinned=True
skin_bcr=None
skin_lfr=None
font_scale=100
conf_font1=gFont("Regular",font)
conf_font2=gFont("Regular",font)
conf_item=font+3

fontlist=[font,font_scale,conf_item+5,conf_font1,DPKG,skin_ext,DWide,DHoehe,True,False]

class stylemanager():
    def __init__(self, *args, **kwargs):
        global font_scale
        global font
        global conf_font1
        global conf_font2
        global conf_item
        global wbrfs_no_scinned
        self.font = self.scale = self.c3 = self.c1_font = self.c2_font = None
        spath=resolveFilename(SCOPE_CURRENT_SKIN) + "skin.xml"
        skin_dir=os.path.dirname(spath)
        wbrfs_no_scinned=self.check_skinned(spath)
        s2path=None
        if pathExists(skin_dir+"/allScreens/"):
            s2path=skin_dir+"/allScreens/"
        elif pathExists(skin_dir+"/mySkin_off/"):
            s2path=skin_dir+"/mySkin_off/"
        if wbrfs_no_scinned and s2path:
                for file1 in os.listdir(s2path): 
                    if file1.endswith(".xml") and file1.startswith('skin_') and wbrfs_no_scinned:
                         wbrfs_no_scinned=self.check_skinned(s2path+file1)
                         if wbrfs_no_scinned is None:
                              break
        if wbrfs_no_scinned:
            if os.path.isfile("/etc/enigma2/skin_user.xml"):
                wbrfs_no_scinned=self.check_skinned("/etc/enigma2/skin_user.xml")
        if wbrfs_no_scinned:
            files=(resolveFilename(SCOPE_CURRENT_SKIN) + "skin_user_colors.xml",resolveFilename(SCOPE_CURRENT_SKIN) + "skin.xml","/etc/enigma2/skin_user.xml","/etc/enigma2/skin_user.xml")#,"/etc/enigma2/skin_user.xml")
            for x in files:
                if os.path.isfile(x):
                  if self.scale is None and self.font is None:
                    self.reading(x)
                  elif self.scale or self.font:
                    break
            if self.scale and self.font: 
                font_scale=int(self.scale)
                if self.font: self.font=int(self.font)*font_scale/100 #int(self.font*font_scale/100)
                conf_item = int(int(self.font)*font_scale/100)+3
            elif self.font: font=int(self.font)
            conf_font1=conf_font2=gFont("Regular",font)

            if self.c1_font:
                conf_font1 = gFont(self.c1_font[0],int(self.c1_font[1]))
            if self.c2_font:
                conf_font2 = gFont(self.c2_font[0],int(self.c2_font[1])) 
            if self.c3:
                conf_item = int(self.c3)
        fontlist=[font,font_scale,conf_item,conf_font1,DPKG,skin_ext,DWide,DHoehe,wbrfs_no_scinned]

    def check_skinned(self, skin_path):
            conf=None
            try:
                conf = xml.etree.cElementTree.parse(skin_path)
            except Exception as e:
                    pass
            sk1=True
            if conf:
              for x in conf.getroot():
                try:
                    if x.tag == "screen" and x.get("name") in ("wbrfs_cs","WebradioFSSetup_13","wbrfs_set_we","wbrfs_message"):
                        sk1= None
                        break
                except:
                    pass
            return sk1

    def reading(self, skin_path):
                  global camoskinned
                  global skin_bcr
                  global skin_lfr
                  conf=None
                  try:
                      conf = xml.etree.cElementTree.parse(skin_path)
                  except Exception as e:
                      pass
                  dict_col={}
                  bcr_farb=None
                  lfr_farb=None
                  if conf:
                   for x in conf.getroot():
                     try:   
                        if x.tag == "colors":
                               colors=x
                               for x in colors:
                                    if x.tag == "color" and x.get("value")[0]=="#":
                                        dict_col[x.get("name")]= x.get("value")
                        elif x.tag == "fonts":
                               fonts=x
                               for x in fonts:
                                        if x.tag == "font" and x.get("name")=="Regular":
                                            self.scale = int(x.get("scale"))
                        elif x.tag == "windowstyle" and x.get("id") == "0":
                                offset = eSize(20, 5)
                                windowstyle = x
                                for x in windowstyle:
                                        if self.font is None and x.tag == "title":
                                                font=x.get("font").split(";")
                                                self.font = int(font[1])
                                        elif x.tag == "color":
                                                colorType = x.get("name")
                                                farb=x.get("color")
                                                if colorType == "Background":
                                                     if farb[0] == "#":
                                                          skin_bcr= farb
                                                     else:
                                                         bcr_farb=farb
                                                elif colorType == "LabelForeground":
                                                     if farb[0] == "#":
                                                          skin_lfr= farb
                                                     else:
                                                         lfr_farb=farb
                        elif self.c1_font is None and self.c2_font is None and x.tag == "listboxcontent":
                                listboxcontent = x
                                for x in listboxcontent:
                                        if x.tag == "font":
                                                name = x.get("name")
                                                font2 = x.get("font")
                                                if name and font2:
                                                                if name == "config_description":
                                                                        self.c1_font= font2.split(";")
                                                                elif name == "config_value":
                                                                        self.c2_font= font2.split(";")
                                        elif x.tag == "value":
                                                name = x.get("name")
                                                value = x.get("value")
                                                if name and value:
                                                        if name == "config_item_height":
                                                                self.c3=int(value)
                     except:
                         if write_debug:
                             rs=open("/var/webradioFS_debug.log","a")
                             rs.write("parse-error(2) found in "+skin_path)
                             rs.close()
                  if bcr_farb and bcr_farb in dict_col:#.has_key(bcr_farb):
                           skin_bcr= dict_col[bcr_farb]
                  if lfr_farb and lfr_farb in dict_col:#.has_key(lfr_farb):
                          skin_lfr= dict_col[lfr_farb]  


from .wbrfsmenu import menu_13, groups_13
from .wbrfs_funct import wbrfs_message,StreamPlayer,Streamlist,load_rf,webradioFSdisplay13,wbrfs_filelist,webradioFSsetDisplay ,write_settings,read_einzeln,read_plan
skin_ignore=read_einzeln().reading((("grund","skin_ignore"),))[0] 

if fileExists("/etc/ConfFS/wbrfs_ignore_skin"):
     skin_ignore=True
if not skin_ignore:
     stylemanager()
fontlist=[font,font_scale,conf_item,conf_font1,DPKG,skin_ext,DWide,DHoehe,wbrfs_no_scinned,skin_ignore,conf_font2]

#################################
def mycmp(version1, version2):
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]
    return cmp(normalize(version1), normalize(version2))

auto_png_off=plugin_path+"/skin/images/autoplay_off.png"
auto_png_on=plugin_path+"/skin/images/autoplay.png"

class cache_list_menu(Screen):
    def __init__(self, session, cache_path,rec_path):
        song_liste=[]
        problemsender=0
        self.akt_save=None
        self.rec_path=rec_path
        if not self.rec_path.endswith("/"):
               self.rec_path=self.rec_path+"/"
        inc_list=[]
        if os.path.exists(cache_path+"incomplete/"):
            for name in os.listdir(cache_path+"incomplete/"):
                    if not name.startswith(" - .") and not name.startswith(" -"):
                         fullpath = cache_path+"incomplete/"+name
                         dtime=os.path.getmtime(fullpath)
                         inc_list.append((dtime,name))
        else:
           problemsender=1
        if len(inc_list):
          inc_list.sort(key=lambda x: x[0])
          now=inc_list[len(inc_list)-1][1]
          song_liste.append((_("now: ")+now,now,"incompl"))
        for name in os.listdir(cache_path):
                      pic=None
                      fullpath = cache_path+name
                      if not name.startswith(" - .") and not name.startswith(" -"):
                        if os.path.isfile(fullpath.replace(".mp3",".jpg")):
                          pic= fullpath.replace(".mp3",".jpg")
                        if not os.path.isdir(fullpath) and not name.endswith(".jpg"): 
                              song_liste.append((name,fullpath,"s",pic))
        if problemsender and len(song_liste):
                tr=_("Save not yet possible")+"-"+song_liste[0][0]
                song_liste=song_liste[1:]
                song_liste.insert(0,(tr,None,None,None))
        self.song_liste=song_liste
        Screen.__init__(self, session)
        tmpskin = open(skin_ext+"wbrFS_cs.xml")
        self.skin = tmpskin.read()
        tmpskin.close()
        if fontlist[9]:
            self.skinName = "wbrfs_cs_e"
        else:
            self.skin=self.skin.replace('backgroundColor="#000000"','')
            self.skin=self.skin.replace('foregroundColor="#ffffff"','')
            self.skinName = "wbrfs_cs"
        self['song_liste'] = List(song_liste)
        self['key_red'] = Label(_("Close"))
        self['key_green'] = Label(_("Save"))
        self['key_yellow'] = Label(_("Stop cache"))
        self.setTitle(_("Save from cache"))
        self["actions"] = ActionMap(["wbrfsKeyActions"],{"ok": self.saving,"cancel": self.exit,"red": self.exit,"yellow": self.stopping,"green": self.saving,})

    def saving(self):
        song_liste= self.song_liste
        cur = self['song_liste'].getCurrent()
        if cur and cur[2]:
          if cur[2]=="incompl":
              del song_liste[0]
              self['song_liste'].updateList(song_liste)
              self.akt_save=cur[1]
          else:
              if os.path.isfile(cur[1]):
                  copyfile(cur[1], self.rec_path+cur[0])
                  if cur[3]:copyfile(cur[3], sets_exp["coversafepath"]+cur[0].replace(".mp3",".jpg"))
              ind=song_liste.index(cur)
              del song_liste[ind]
              os.unlink(cur[1])
              if cur[3]:os.unlink(cur[3])
              self['song_liste'].updateList(song_liste)

    def stopping(self):
        self.close(("stopped",self.akt_save))

    def exit(self):
        self.close((None,self.akt_save))
#########################################################################################################        
u_times=[]
u_times=read_plan().reading("1")

class WebradioFSScreen_15(Screen, InfoBarSeek, HelpableScreen, InfoBarNotifications):
    def __init__(self,session,Stream=None,sets=None):
        self.session = session
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.org_vol=eDVBVolumecontrol.getInstance().getVolume()
        self.containerwbrfs_rec=None
        global sets_exp
        global ripper_installed
        global myfav_file
        global a_sort
        global a_schleife
        global u_dir
        global random_pic
        global subdirs_pic
        global melde_screen
        global right_site
        global streamplayer
        global fontlist
        global zs
        global sets_opt,sets_grund,sets_view,sets_scr,sets_rec,sets_audiofiles,sets_prog,sets_sismctl
        read_list=["grund","opt","rec","audiofiles","scr","sispmctl","prog","view"]
        sets2=read_settings1().reading(read_list)
        num1=0
        self.aktstop=0
        sets_grund=sets2[0]
        sets_opt=sets2[1]
        try:
            if str(sets_grund["zs"]).lower()=="true":
               zs=True
        except:
            pass
        if str(sets_opt["expert"]).lower()=="true":
               sets_opt["expert"]=1
        elif str(sets_opt["expert"]).lower()=="false":
               sets_opt["expert"]=0

        sets_rec=sets2[2]
        sets_audiofiles=sets2[3]
        sets_scr=sets2[4]
        sets_sismctl=sets2[5]
        sets_prog=sets2[6]
        sets_view=sets2[7]
        set_l4l()
        dspreads=read_einzeln().reading((("view","l4l"),("view","displayb")))
        sets=dspreads[1].split(',')
        self.display_on=True
        if sets[0]=='2':
            self.display_on=False
        self.new_imp=None
        self.connection=None
        self.genre_list=()
        self.alt_fsz=sets_view["font_size"]
        if os.path.exists(os.path.join(sets_grund["favpath"], "webradioFS_favs.db")) and os.path.getsize(os.path.join(sets_grund["favpath"], "webradioFS_favs.db"))>0:
            myfav_file= os.path.join(sets_grund["favpath"], "webradioFS_favs.db")
        else:
            myfav_file= "/etc/ConfFS/webradioFS_favs.db"
        self.connection = sqlite.connect(myfav_file)
        self.connection.text_factory = str

        if str(sets_audiofiles["sort"]) == "True":
             sets_audiofiles["sort"] = "random"
        elif str(sets_audiofiles["sort"]) == "False":
             sets_audiofiles["sort"] = "nix"
        a_sort=sets_audiofiles["sort"]
        a_schleife=None
        if "schleife" in sets_audiofiles:  
             a_schleife=sets_audiofiles["schleife"]
        if a_sort=="random":
                random_pic=plugin_path+"/skin/images/random.png"
        else:
                random_pic=plugin_path+"/skin/images/random_off.png"
        u_dir=sets_audiofiles["subdirs"]
        if u_dir:
                subdirs_pic=plugin_path+"/skin/images/subdirs.png"
        else:
                subdirs_pic=plugin_path+"/skin/images/subdirs_off.png"
        streamlist = []

        melde_screen=self.session.instantiateDialog(wbrfs_message)
        right_site = self.session.instantiateDialog(wbrFS_r_site15)
        right_site.show()
        self.rec_anzeige=sets_rec["anzeige"]
        if not sets_rec["path"].endswith("/"):
            sets_rec["path"]=sets_rec["path"]+"/"
        if not sets_rec["rec_caching_dir"].endswith("/"):
             sets_rec["rec_caching_dir"]=sets_rec["rec_caching_dir"]+"/"  
        if L4LwbrFS and l4ls[0]=="True":
            global l4lR
            try:
                if str2bool(l4ls[4]):
                    L4LwbrFS.add( "wbrFS.02.txt2",{"Typ":"txt","Align":"0","Pos":0,"Text":"webradioFS","Size":22,"Screen":l4ls[3],"Lcd":l4ls[1],"Mode":"OnMedia"} )
                if l4ls[23]=="True":
                   L4LwbrFS.add( "wbrFS.01.pic2",{"Typ":"pic","Align": str(l4ls[24]),"Pos":int(l4ls[25]),"File":"/tmp/.wbrfs_pic","Size":int(l4ls[26]),"Screen":l4ls[3],"Lcd":l4ls[1],"Mode":"OnMedia"} )
                if l4ls[2]=="True":
                    L4LwbrFS.setHoldKey(True)
                L4LwbrFS.setScreen(l4ls[3],l4ls[1],True)
            except:
               l4lR=None
        self.wecker=0
        if sispmctl: 
            if "0" in sets_sismctl["start"] or "1" in sets_sismctl["start"]:
                self.sispmctl_schalt(sets_sismctl["start"])
        from Screens.InfoBar import InfoBar
        if isinstance(InfoBar.instance, InfoBarChannelSelection): #, InfoBarChannelSelection 27.11.2016
            self.servicelist = InfoBar.instance.servicelist
        else:
            self.servicelist =None
        try:
            self.auto_play=sets_audiofiles["autoplay"]
        except:
            self.auto_play=False
        self.pcfs_run=False
        self.db_meld=""
        self.pause=None
        self.menu_history=(0,0,0)
        self.alt_fav_index=0
        self.akt_pl_num=0
        self.back=None
        self.m_back=None
        self.altmeld=None
        self.alttext=""
        self.alt_url=""
        self.alt_conf=None
        self.tv1 = None
        self.tv_ton=False
        self.video=None
        self.streamvor=" "
        self.streamnach=" "
        self.pl1="ok"
        self.ab_info=""
        self.display_art="liste"
        self.sorting=None
        self.indexer=0
        self.pvrstartstream=None
        self.hole_bild=None
        if not os.path.exists(sets_exp["logopath"]):  os.makedirs(sets_exp["logopath"])
        if not os.path.exists(sets_exp["logopath"]+"/byName"):  os.makedirs(sets_exp["logopath"]+"/byName")
        tmpskin = open(fontlist[5]+"webradioFS.xml")
        sk=tmpskin.read()
        if not fontlist[9] :
            sk=sk.replace('backgroundColor="#000000"','')
            sk=sk.replace('foregroundColor="#ffffff"','')
        self.skin = sk
        tmpskin.close()
        Screen.__init__(self, session)
        InfoBarNotifications.__init__(self)
        if fontlist[9]:
            self.skinName = "WebradioFSScreen_e"
        else:
           self.skinName = "WebradioFSScreen_16"
        streamplayer = StreamPlayer(session)
        HelpableScreen.__init__(self)
        self.versionstest=False
        self.versionsalter=0
        self.meld_timer=eTimer()
        self.meld_timer.callback.append(self.meldung_t_back)
        self.sets={
             "fav":"","fav_text":"","genre":"Genre:","genre_text":"","bitrat":"Bitrate:","bitrat_text":"", "typ":_("Typ:"),"typ_text":"",
             "name_text":"","logo":"","uploader":"","beschreibung":"","file":False, "autoplay":auto_png_off,"random":random_pic,"subdirs":subdirs_pic,
              }
        if self.auto_play:
                 self.sets["autoplay"]=auto_png_on
        else:
                 self.sets["autoplay"]=auto_png_off
        self["playtext"] = StaticText()
        if sets_exp["FBts_liste"]=="0, 1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22":
           sets_exp["FBts_liste"]="0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24"
           write_settings((("exp",sets_exp),))        
        self.FBts_liste=sets_exp["FBts_liste"].split(",")
# skin elemente fuer streamliste
        self.streamlist=[]
        self["streamlist"] = List(self.streamlist)
        self["dummy"] = Pixmap()
        self["green_pic"] = Pixmap()
        self["key_red"] = Label(_(FBts_liste[int(self.FBts_liste[3])][1]))
        self["key_green"] = Label(_(FBts_liste[int(self.FBts_liste[5])][1]))
        self["key_yellow"] = Label(_(FBts_liste[int(self.FBts_liste[7])][1]))
        self["key_blue"] = Label(_(FBts_liste[int(self.FBts_liste[9])][1]))
        self["rec_text_new"] = List([])
        self.alt_art=None
        self["rec_pic"] = Pixmap() 

# skin elemente fuer help-screens
        self["help"] = ScrollLabel("")
        self.update_txt=""
        self["buttons_abdeck"] = Label("")
        self["key_red2"] = Label(_("back")) #("")
        self["key_green2"] = Label(_("aktualisieren"))    
# ausblenden
        hide_list=(self["buttons_abdeck"],self["key_red2"],self["key_green2"],self["rec_pic"])
        for x in hide_list:
            x.hide()
        self.meldung1=None
        self.fav_stream=None
        self.record=None
        self.rec_path1=None
        self.rec_plan=False
        self.exit_art="nix"
        self.e_help="off"
        self.rec_timer = eTimer()
        self.cache_timer= eTimer()
        self.confail_timer=eTimer()
        self.reconnect=0
        self.fav_list=None
        self.cache_list=None
        self.listparas=None
        self.rec_set_list={'art':"endless", 'dauer':"0",'start_time':0,'rec_split':True,'rec_cover':True,'rec_new_dir':True,'rec_path':"/tmp",'rec_art':"endless",'pos_filter':None,'neg_filter':None}
        self.wbrfs_rec_BIN=None
        if fileExists("/usr/bin/streamripper"):
          if os.access("/usr/bin/streamripper", os.X_OK):
            ripper_installed=True
            try:
               self.wbrfs_rec_BIN = '/usr/bin/streamripper'
               self.rec_plan=False
               self.rec_timer = eTimer()
               self.containerwbrfs_rec = eConsoleAppContainer()
               if sets_prog["DPKG"]:
                   self.appClosed_conn = self.containerwbrfs_rec.appClosed.connect(self.rec_stop2)
                   self.dataAvail_conn = self.containerwbrfs_rec.dataAvail.connect(self.dataAvail)
                   self.rec_timer_conn = self.rec_timer.timeout.connect(self.rec_time)
                   self.cache_timer_conn = self.rec_timer.timeout.connect(self.check_cache)
               else:
                   self.containerwbrfs_rec.dataAvail.append(self.dataAvail)
                   self.containerwbrfs_rec.appClosed.append(self.rec_stop2)
                   self.rec_timer.timeout.get().append(self.rec_time)
                   self.cache_timer.timeout.get().append(self.check_cache)
               if self.containerwbrfs_rec.running():
                   self.playServiceStream("http://localhost:9555")
            except:
               pass

        self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
               {
                    iPlayableService.evUpdatedInfo: self.__evUpdatedInfo,
                    iPlayableService.evUpdatedEventInfo: self.__evUpdatedInfo,
                    iPlayableService.evStart: self.__serviceStarted,
                    iPlayableService.evEOF: self.aktual2,
                    iPlayableService.evUser+10: self.aktual2,
                    iPlayableService.evUser+12: self.__evPluginError,
                    iPlayableService.evTuneFailed: self.aktual2,
                    iPlayableService.evUpdatedRadioText: self.RadioText,
                    iPlayableService.evUpdatedRtpText: self.RTPText,
                })
        self.upadate_taste=None
        self.chill_taste=None
        self.gelbe_taste=None
        self.blaue_taste=None

        tast_l=(self["key_red"],self["key_green"],self["key_yellow"],self["key_blue"])
        farbtasten=[int(self.FBts_liste[3]), int(self.FBts_liste[5]), int(self.FBts_liste[7]), int(self.FBts_liste[9])]
        if 5 in farbtasten:
            self.chill_taste=tast_l[farbtasten.index(5)]
            self.chill_taste.setText(_("Chillen"))
        if 7 in farbtasten:
            self.gelbe_taste=tast_l[farbtasten.index(7)]
            self.gelbe_taste.setText(_(FBts_liste[int(self.FBts_liste[7])][1]))
        if 9 in farbtasten:
            self.blaue_taste=tast_l[farbtasten.index(9)]
            self.blaue_taste.setText(_(FBts_liste[int(self.FBts_liste[9])][1]))
        commados=(self.ok,self.exit_a,self.exit_c,self.red_button,self.red_button_long,
                  self.chillmodus,self.green,self.Favoriten_Wechsel,self.mach_nix,self.edit,
                  self.blue_long, self.info_check,self.Favoriten_rueck,self.Favoriten_vor,self.stop_stream,
                  self.downPressed,self.upPressed,self.textPressed,self.zap_down,self.zap_up,
                  self.live_tv_prev, self.live_tv_next,self.live_tv,self.slideshow,self.fileplay,self.mach_nix)

        self.tasten={}
        tnum=0
        for x in tasten_name:
            if tnum<len(self.FBts_liste) and tnum<len(FBts_liste):
                  lnum=int(self.FBts_liste[tnum])
                  if lnum<len(commados):
                      txt=_(FBts_liste[lnum][1])
                      if tnum==3:
                          self["key_red"].setText(txt)
                      if tnum==5:
                          self["key_green"].setText(txt)
                      if tnum==7:
                          self["key_yellow"].setText(txt)
                      if tnum==9:
                          self["key_blue"].setText(txt)
                      self.green_set=None
                      cm= commados[FBts_liste[lnum][0]]
                      if txt != _("None") and cm !=  self.mach_nix:
                          self.tasten[x] = (cm,txt)
                  tnum+=1

        tasten3={
             "record" : (self.rec_endless,_("Record On/Off")),
             "menu": (self.showMainMenu,_("Show Menu")),
             "audio": (self.setStandardVolume,_("set Standard Volume")),
             "pause": (self.playpause,_("Play/Pause")),
             "left": (self.pageUp,_("Page up")),
             "right": (self.pageDown,_("Page down")),
        }

        self.tasten.update(tasten3)
        if ripper_installed==True:
           tasten2={"record_extended" : (self.rec_menu,_("Record-Menu")),}
           self.tasten.update(tasten2)
        if menu_ok:
            self["helpActions"] = ActionMap( [ "HelpActions" ],{"displayHelp": self.showHelp,})
        self["wbrfsKeyActions"] = HelpableActionMap(self, "wbrfsKeyActions", self.tasten)
        self["GlobalwbrfsKeyActions"] = HelpableActionMap(self, "GlobalwbrfsKeyActions",
            {"wbrfs_power_up" : (self.power_key,_("Standby")),
             "wbrfs_power_long" : (self.power_key_long,_("Off")),
             "up" : (self.upPressed,_("Up")),
             "down" : (self.downPressed,_("Down")),
        }, -1)
        self["numberActions"] = NumberActionMap(["NumberActions"],
        {
          "0": self.keyNumberGlobal,
          "1": self.keyNumberGlobal,
          "2": self.keyNumberGlobal,
          "3": self.keyNumberGlobal,
          "4": self.keyNumberGlobal,
          "5": self.keyNumberGlobal,
          "6": self.keyNumberGlobal,
          "7": self.keyNumberGlobal,
          "8": self.keyNumberGlobal,
          "9": self.keyNumberGlobal,
        }, -1)
        self.favoritenlist=[]
        self.volctrl = eDVBVolumecontrol.getInstance()
        self.onClose.append(self.__onClose)
        self.errorzaehler=1
        self.ok_start=0
        self.akt_volume=None
        self.exit_time=0
        self.standby_aktion=None

        self.num = 0
        self.move=0
        self.check=None
        self.titeltext=""
        self.fav_index=0
        self.fav_name=""
        self.play_stream=None
        self.playlist2=None
        self.playlist2_ind=0
        self.akt_pl_list=[]
        self.stream_wechsel=0
        self.title2=""
        self.typ_failed=0
        self.akt_defekt=0
        self.stream_info="webradioFS"
        self.list_titel="webradioFS"
        self.alt_ind=None
        self.stream_urls=None
        self.stream_url=None
        self.rec_path=None
        self.red="start"
        self.menu_on=None
        self.rec_list=None
        self.rec_filename=None
        self.root_rec=None
####  timer  ################
        self.volume_timer= eTimer()
        self.wbrScreenSaverTimer = eTimer()
        self.display_timer = eTimer()
        self.plan_timer = eTimer()
        self.start_timer = eTimer()
        self.chsltitel_timer = eTimer()
        self.allstreams_index=0
        self.blocker=blocker()
        self.chsltitel_timer.timeout.get().append(self.sleep_chill_time)
        fontlist[4]=False
        self.chsltitel_timer.timeout.get().append(self.sleep_chill_time)
        self.volume_timer.timeout.get().append(self.set_volume)
        self.wbrScreenSaverTimer.timeout.get().append(self.wbrScreenSaverTimer_Timeout)
        self.display_timer.timeout.get().append(self.ondisplayFinished)
        self.plan_timer.timeout.get().append(self.planer)

        if sets_exp["stop_abschalt"]:
             self.blocker.start()
        self.startstream=sets_grund["startstream1"]
        self.startart= 0
        try:
            self.startart=int(self.startstream)
        except:
           pass


        if self.startart > -2:
          self.startstream="fav,0"
          starter_set("read")
          if starter_stream:
              self.startstream=str(starter_stream)
        self.planer_start()
        self.max1=0
        self.screensaver_off = 0
        self.vidTimer=None
        self.screenSaverScreen = None
        if sets_scr["timeout"]>0:
            self.ResetwbrScreenSaverTimer()
        if sets_exp["start_vol"]:
            self.start_volume(sets_exp["start_vol"])
        self.onlyPhoto=""
        if sets_view["only_foto"]:
                    self.onlyPhoto="&imgtype=photo"
        self.streamname=""
        self.configfile2=None
        self.einzelplay=0
        self.favoritenlist = []
        self.Dateiliste = []
        self.db_err=0   
        self.test=0
        self.Favoriten_einles()
        self.sel_stream=None
        self.onLayoutFinish.append(self.starters)
        self.s_stream=0
        self.suchstring=""
        self.anzeige_fav=""
        self.listbgr="#000000"
        self.onChangedEntry = []
        right_site.new_Bild()

    def fileplay(self):
            for fav in self.favoritenlist:
                if fav[1]==30:
                    self.Favoriten_Wechsel2(fav)
                    break 

    def planer(self):
        startstream=None
        on=1
        for x in self.utimers:
            if x == self.next_utime[1]:
              activ=True
              if not x[3]['active']:
                        activ=False
              if activ and x[3]['datum']:
                       if datetime.date.today() != datetime.date.fromtimestamp(x[3]['datum']):
                            activ=False
                            if datetime.date.today() > datetime.date.fromtimestamp(x[3]['datum']):
                                 d=read_plan().deling(x[3]['setid'])
              if activ and x[3]['weekdays']:
                        d=time.localtime(time.time())[6]
                        if not x[3]['weekdays'][d]:
                              activ=False
              if activ:
                if x[3]['art']=="select":
                    startstream=x[3]["streamid"]
                    if startstream:
                        for x in self.favoritenlist:
                                if x[1]==0:
                                   for x2 in x[2]:
                                     if int(x2[2]) == startstream:
                                       self.fav_index=self.favoritenlist.index(x)
                                       self.fav_stream=x2
                                       break
                        try:
                           if self.fav_stream or self.pvrstartstream:
                                self.favoriten()
                                if self["streamlist"].getCurrent():
                                    self.ok()
                        except:
                            fehler = (_("Failed to start automatically" ))
                            self["playtext"].setText(_("Planer-Error"))
                elif x[3]['art']=="off":
                     on=None
                     self.exit(True,1)   
                elif x[3]['art']=="off_to_standy":
                     on=None
                     self.exit_art=="standby"
                     self.power_key()        
            break
        if on and len(self.utimers)>1:self.planer_start()

    def planer_start(self):
            self.utimers=[]
            self.next_utime=None
            now = datetime.datetime.now()
            now2 = [x for x in localtime()] 
            startstream=None
            ut= u_times
            ut.sort(key=lambda x: x[1], reverse=False)
            for x in ut:
                if x[2] and not x[3]['art'].startswith("on"):
                   args=x[3]
                   z=x[1]
                   z2=x[2]
                   t=args['time']
                   now2 = [xl for xl in localtime()]
                   now2[3]=int(t[0])
                   now2[4]= int(t[1])
                   now2[5] = 0
                   t2=time.mktime(now2)
                   utime=datetime.datetime.fromtimestamp(t2)
                   if utime:
                        if utime>now: 
                            self.utimers.append((int(t2),z,z2,args))
                        else:
                            if args['art']=="select":
                                if self.startstream==0:startstream=args['streamid']
                            utime += datetime.timedelta(days=1)
                            t3=int(time.mktime(utime.timetuple()))
                            self.utimers.append((t3,z,z2,args))
            if len(self.utimers):
                zeit=time.time()
                self.utimers.sort(key=lambda x: x[1], reverse=False)
                for x in self.utimers:
                    if x[0] != None:
                        if x[0]>int(zeit):
                            self.next_utime=(int(x[0]-int(zeit)),x)
                            break
                if startstream:
                     self.startstream=startstream
                     if x[3]['art']=="select":self.next_utime=(1,self.utimers[0])
                if self.next_utime: 
                        self.plan_timer.startLongTimer(self.next_utime[0])

    def show_planer(self):
            termine=[]
            stream_liste=[]
            self.wbrScreenSaver_stop()
            if os.path.exists(myfav_file):
                connection = sqlite.connect(myfav_file)
                connection.text_factory = str
                cursor = connection.cursor()
                cursor.execute("select name, stream_id from streams;")
                for row in cursor:
                    stream_liste.append((row[1], row[0]))
            self.session.openWithCallback(self.planer_back,planer_list,stream_liste)

    def planer_back(self,back=None):
           self.planer_start()
           self.screensaver_off = 0
           self.ResetwbrScreenSaverTimer()
           from .plugin import make_autoT
           ppfs=make_autoT()

    def set_rec_text(self,txt=None,art=None):
       if txt and art:
           txt_list=[(txt,"")]
           if art != "titel": self.alt_art=(txt,art)
           self["rec_text_new"].style = art
           self["rec_text_new"].setList(txt_list)

    def set_streamlist(self,str_list,akt_stream="favs",sort=None,indexer=None):
          picpath=plugin_path +"/skin/images/"
          pngok = LoadPixmap(picpath+"pic_ok.png")
          pngerr = LoadPixmap(picpath+"pic_err.png")
          pngrec = LoadPixmap(picpath+"rec3.png")
          pngplay = LoadPixmap(picpath+"pic_play.png")
          pngdb = LoadPixmap(picpath+"pic_db.png")
          pngf = LoadPixmap(picpath+"pic_fav.png")
          pngsat = LoadPixmap(picpath+"pic_sat.png")
          pngsort = LoadPixmap(picpath+"pic_sort.png")
          pngsort0 = LoadPixmap(picpath+"pic_sort0.png")
          pngdir = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "extensions/directory.png"))
          pngup = LoadPixmap(picpath+"up.png")
          pngfile = LoadPixmap(picpath+"audiofile.png")
          res=[]
          num=1
          a_ind=None
          ind=1
          pngs=None
          for stream in str_list:
                self.ptr = None
                if indexer is None:
                   if (self.play_stream and self.play_stream["name"]== stream[0]) or (akt_stream and akt_stream==stream[1]): #"(m3u) "+self.play_stream["name"]== stream[0]:
                      a_ind = ind

                ind+=1
                try:
                    text3= ""
                    if akt_stream and akt_stream == "records":
                       text3= stream[1].strip()
                       png=pngrec
                    elif akt_stream and akt_stream=="favs":
                       text3= stream[0].lstrip()
                       if stream[1]>29:
                          png=pngdir
                       elif stream[0].startswith("PVR-"):
                          png=pngsat
                       else:
                           png=pngf
                    elif akt_stream and akt_stream=="db":
                          text3= _("Database:")+" "+text3
                          if a_ind != ind:
                              png=pngdb
                          else:
                              png=pngplay
                    elif sort: 
                          text3=stream[0]
                          a_ind=self["streamlist"].getIndex()+1
                          png=pngsort0
                          if (stream[7]=='radio' and akt_stream and stream[0]==akt_stream): #stream[1]==akt_stream and sort<2:
                              png=pngsort
                    elif str(stream[4]).isdigit() and int(stream[4]) < 1 and not stream[7].startswith("Dir"): 
                          text3=stream[0]
                          png=pngerr
                          if (stream[7] !='Files' and akt_stream and stream[0]==akt_stream) or (stream[7]=='Files' and akt_stream and stream[1]==akt_stream):
                              png=pngplay
                          elif str(stream[3]).isdigit() and int(stream[3]) >0:
                              png=pngerr
                          else:
                              png=pngok
                    else:
                        text3= stream[0]
                        if str(stream[4]) == "2" or str(stream[4]) == "6": 
                              zusatz=str(num)
                              if num<10: zusatz="  "+zusatz
                              text3=zusatz+" - " +text3
                              num+=1
                        elif str(stream[4]).isdigit() and int(stream[4]) == 10:
                            text3= stream[0]+" -> "+ str(stream[3])+"x "
                        if (stream[7] !='Files' and akt_stream and stream[0]==akt_stream) or (stream[7]=='Files' and akt_stream and stream[1]==akt_stream):
                              png=pngplay
                        elif str(stream[5]).isdigit() and int(stream[5])>0 and int(stream[5]) != 99:
                              png=pngerr
                        else:
                            if stream[7] == "pvr":
                                png=pngsat
                            elif stream[7] == "Files" and not stream[0].startswith("  -  "):
                                png=pngfile
                            elif stream[7] == "Dir":
                                png=pngdir
                            elif stream[7] == "Dir1":
                                png=pngup
                            elif stream[0].startswith("  -  "):
                                png=None
                            else:
                                png=pngdb

                    ptr=None
                    pngname = None
                    if len(text3) and str(akt_stream) !="db":
                      if ind<100 and len(stream)>7 and self.configfile2[0] !=_("PVR-Radio all"):   
                          if (stream[7] =="pvr" or stream[7] =="radio") and sets_view["logos"]==True and sets_view["Listlogos"]==True:
                            pngname1=None
                            pngname = "/usr/lib/enigma2/python/Plugins/Extensions/webradioFS/skin/images/wbrfsdeflogo.png"
                            if stream[9]>0 and sets_exp["logopath"] and len(sets_exp["logopath"]) and os.path.exists(sets_exp["logopath"]):
                                if os.path.join(sets_exp["logopath"],str(stream[9]) + ".png"):
                                    pngname1 = os.path.join(sets_exp["logopath"],str(stream[9]) + ".png")
                            if pngname1 is None or not os.path.exists(pngname1):
                                 if sets_exp["wbrfspvrpath"] and len(sets_exp["wbrfspvrpath"]) and os.path.exists(sets_exp["wbrfspvrpath"]):
                                       if stream[7] =="pvr":
                                           if len(stream[6]):pngname1=os.path.join(sets_exp["wbrfspvrpath"],stream[6].rstrip(':').replace(':','_')+ ".png")
                                       else:
                                            if len(stream[10]):pngname1=os.path.join(sets_exp["wbrfspvrpath"],stream[10].rstrip(':').replace(':','_'))# + ".png"
                                       if not pngname1 or not os.path.exists(pngname1):
                                           pngname1=os.path.join(sets_exp["wbrfspvrpath"],str(stream[0])+ ".png")    
                            if pngname1 is not None and os.path.exists(pngname1):
                                  pngname=pngname1
                                  if pngs is None:pngs=1
                      res.append((stream ,text3,png,stream[1],stream[0],pngname))
                except Exception as e:
                    if write_debug: 
                        d=debug("exception (01):\n"+str(e)+"\n"+str(stream))
          self.show_list=res
          self.indexer=None
          if a_ind is not None and a_ind-1 < len(str_list):
             self.indexer=a_ind-1
          elif indexer is not None and indexer-1 <len(str_list):
              self.indexer=indexer 
          if pngs is not None:
              self["streamlist"].style = "default"
          else:
              self["streamlist"].style = "default_without_picon"
          self["streamlist"].enableWrapAround = True
          self["streamlist"].setList(res)
          if pngs is not None:
              self.buildEntryComponent()
          else:
             if self.indexer is not None:self["streamlist"].setIndex(self.indexer)

    def buildEntryComponent(self):
        self.show_list2={}
        self.l_len=len(self.show_list)
        ida=0
        tp=os.path.join(sets_exp["logopath"],"byName")
        for x in self.show_list:
                         path1=None
                         tp1= os.path.normcase(tp+"/"+str(x[1])+".png")
                         if os.path.exists(tp1):
                                path1=tp1 
                         elif x[5] is not None and len(x[5]) and os.path.exists(x[5]):
                                path1=x[5]
                         if path1:
                            self.setLogoPic(path1,ida)
                         ida+=1

    def setLogoPic(self,pfad,ida):
                if (os.path.exists(os.path.normcase(pfad)) == True) and self.listparas:
                        vars(self)["picloads"+str(ida)] = ePicLoad()
                        if fontlist[4]:
                             vars(self)["picloads"+str(ida)+"_conn"]  = vars(self)["picloads"+str(ida)].PictureData.connect(boundFunction(self.finish_decode, ida))
                        else:
                            vars(self)["picloads"+str(ida)].PictureData.get().append(boundFunction(self.finish_decode, ida))
                        vars(self)["picloads"+str(ida)].setPara(self.listparas) 
                        vars(self)["picloads"+str(ida)].startDecode(os.path.normcase(pfad))

    def finish_decode(self,ida,info):
                ptr = vars(self)["picloads"+str(ida)].getData()
                if ptr != None and len(self.show_list)>ida:
                        x= self.show_list[ida]
                        self.show_list[ida]=(x[0],x[1],x[2],x[3],x[4],ptr)
                        if self.e_help =="off":
                          self["streamlist"].setList(self.show_list)
                          if self.indexer is not None:self["streamlist"].setIndex(self.indexer)
                        del vars(self)["picloads"+str(ida)]
                else:
                        del vars(self)["picloads"+str(ida)]

    def checkSkipShowHideLock(self):
        pass

    def showHelp(self):
        if menu_ok:
                right_site.hide()
                self.wbrScreenSaverTimer.stop()
                self.session.openWithCallback(self.callHelpAction, HelpMenu, self.helpList)

    def callHelpAction(self, *args):
        if menu_ok:
                right_site.show()
                self.ResetwbrScreenSaverTimer()
                if args:
                        (actionmap, context, action) = args
                        actionmap.action(context, action)

    def hideAfterResume(self):
        self.hide()

    def go_asd(self,ret=None,ret2=None):
      self.asd_timer.startLongTimer(2)

    def pageDown(self):
        try:
           self["streamlist"].pageDown()
        except:
           pass   
    def pageUp(self):
        try:self["streamlist"].pageUp()
        except:pass
    def downPressed(self):
        if self.tv1:
            self.live_tv()
        elif self.e_help=="ext_help":
           self["help"].pageDown()
        elif self.meldung1:
            melde_screen.move("back")
        else:
           self["streamlist"].selectNext()
           self.check_defekt()
    def upPressed(self):
        if self.tv1:
            self.live_tv()
        elif self.e_help=="ext_help":
            self["help"].pageUp()
        elif self.meldung1:
           melde_screen.move("vor")
        else:
            self["streamlist"].selectPrevious()
            self.check_defekt()
    def zap_down(self):
        if self.tv1:self.live_tv()
        self["streamlist"].selectNext()
        self.ok()
    def zap_up(self):
        if self.tv1:self.live_tv()
        self["streamlist"].selectPrevious()
        self.ok()

    def add_rem_m3u(self,add=None):
        if add:
           akt_stream=None
           if add=="add":     
                  n_list=[]
                  m3us=[]
                  n2_list=self.configfile2[2]
                  for x in n2_list:
                         if x[1].endswith("m3u"):
                              n_list.append([x[0],x[1],x[2],x[3],x[4],x[5],1,x[7]])
                              if os.path.exists(x[1]):
                                  liste2=playlist_read(x[1])
                                  if liste2 and len(liste2):
                                     for bx in liste2:
                                         if self.play_stream and bx[2]==self.play_stream["url"]:akt_stream=bx[2]
                                         n_list.append(["  -  "+bx[1],bx[2],bx[1],0,self.configfile2[1],0,1,"Files"])  
                         else:
                             if self.play_stream and str(x[1])==str(self.play_stream["url"]):akt_stream=str(x[1])
                             n_list.append(x)
                  if isinstance(self.configfile2, tuple): self.configfile2=list(self.configfile2)
                  self.configfile2[2]=n_list
           elif add=="remove":
                  n_list=[]
                  n2_list=self.configfile2[2]
                  for x in n2_list:
                         if not x[0].startswith("  -  "):
                             if self.play_stream and str(x[1])==str(self.play_stream["url"]):akt_stream=str(x[1])
                             n_list.append(x)
                         else:
                             if self.play_stream and x[1]==self.play_stream["url"]:self.auto_zap()
                  if isinstance(self.configfile2, tuple): self.configfile2=list(self.configfile2)
                  self.configfile2[2]=n_list
           self.playlist2= self.configfile2
           self.set_streamlist(self.configfile2[2],akt_stream,None,None)

    def auto_zap(self,ind=None):
        if not self.playlist2:
                  self.add_rem_m3u("add")
                  self.akt_pl_list=[]
        else:
          if self.auto_play:
            self.einzelplay=None
            if self.playlist2 and len(self.playlist2[2]):
              if ind and ind > len(self.playlist2[2])-1: ind=0
              re=1
              if ind or ind==0:
                  self.akt_pl_num=ind
              else:
                if len(self.akt_pl_list)>=len(self.playlist2[2])-1: 
                   self.akt_pl_list=[]
                   if not a_schleife:
                       re=None
                if re:
                  if a_sort=="random" and len(self.playlist2[2])>1:
                      self.akt_pl_num=random.randint(0,len(self.playlist2[2])-1)
                      if self.akt_pl_num in self.akt_pl_list:
                          self.auto_zap()
                          re=None
                  else:
                       self.akt_pl_num+=1
              try:
                  sel=self.playlist2[2][self.akt_pl_num]
              except:
                  sel=None
              if sel and (sel[1].endswith("m3u") or sel[7].endswith("Dir")):
                  self.auto_zap()
                  re=None
              if self.akt_pl_num > len(self.playlist2[2])-1:
                    if a_schleife:
                        self.akt_pl_list=[]
                        self.akt_pl_num = -1
                        self.auto_zap()
                    else:
                        re=None
                        self.set_streamlist(self.configfile2[2],"nix",None,None)
              if re:
                self.akt_pl_list.append(self.akt_pl_num)
                if self.playlist2[2][self.akt_pl_num]<1 and self.playlist2[2][self.akt_pl_num].endswith("m3u"):        
                              er=self.playlist2[2][self.akt_pl_num]
                              self.playlist2[2][self.akt_pl_num]=(er[0],er[1],er[2],er[3],er[4],er[5],1,er[7])
                              if os.path.exists(sel[1]):
                                  liste2=playlist_read(sel[1])
                                  if liste2 and len(liste2):
                                     listnew=self.playlist2[2]
                                     for x in liste2:
                                         listnew.append(["(m3u) "+x[1],x[2],x[1],0,er[4],0,1,"Files"])  
                                     try:
                                        self.playlist2[2].extend(listnew)
                                     except Exception as e:
                                         if write_debug: 
                                             d=debug("exception autoplay (02):\n"+str(e)+"\n")
                                     re=None
                                     self.set_streamlist(self.configfile2[2],'',None,self.akt_pl_num)
                                     self.auto_zap()        
                if re and sel:
                  if sel[5]>0:
                    if write_debug: 
                          d=debug("re and sel: fail"+"\n")
                    if len(self.playlist2[2])>1: self.auto_fail()
                  else:
                    if os.path.exists(sel[1]):
                      if write_debug and write_debug>1: 
                          d=debug("next file: "+str(sel[1])+"\n")
                      nam=os.path.basename(sel[1])
                      if L4LwbrFS: L4LwbrFS.delete( "wbrFS.02.pic1" )
                      typ=''
                      if self.playlist2[2][self.akt_pl_num][6]==1:
                          typ= 'from m3u'
                      self.play_stream={'sscr': 'default', 'genre2': "", 'zuv': 'unbekannt', 'name': nam, 'url': sel[1], 'bitrate': 0, 'volume': 0,'picon': 0, 'stream_id': 100, 'group1': 1, 'uploader': 'nn', 'descrip': '', 'genre': 'wbrfsfiles', 'rec': 0, 'typ': typ, 'defekt': 0, 'cache':0}
                      akt_stream=None
                      ind=None
                      try:
                              akt_stream=self.configfile2[2][self.akt_pl_num][1]
                      except Exception as e:
                              if write_debug: 
                                  d=debug("exception autoplay (01):\n"+str(e)+"\n")
                      if akt_stream:
                          self.set_streamlist(self.configfile2[2],akt_stream,None,None)
                          self.alt_ind=self.akt_pl_num
                          self.set_play_file_infos()
                          sref = eServiceReference(4097, 0, sel[1])
                          self.session.nav.playService(sref)
                      else:
                              if write_debug: 
                                  d=debug("exception (01):\n"+str(e)+"\n"+str(stream))
                    else:
                      self.auto_fail()
                else:
                   self.auto_zap()
              else:
                   self.set_streamlist(self.configfile2[2],"nix",None,0)
            else:
                self.meld_screen(_("files in folder/m3u not found"),"Info",20,"ERROR")

    def auto_fail(self):
                    try:  
                      fail=1
                      er=self.playlist2[2][self.akt_pl_num]
                      if er[7] not in ("Dir","Dir1") and not er[0].startswith("(m3u)"):
                          self.playlist2[2][self.akt_pl_num]=(er[0],er[1],er[2],er[3],er[4],1,er[6],er[7])
                      for x in self.playlist2[2]:
                           if x[5]<1:
                               fail=None
                               self.auto_zap()
                               break
                      if fail:
                          self.meld_screen(_("files in folder/m3u not found")+"\n"+str(self.playlist2[2][self.akt_pl_num][1]),"Info",20,"ERROR")
                    except Exception as e:
                              if write_debug: 
                                  d=debug("exception (01):\n"+str(e)+"\n"+str(stream))          

    def play_file(self,ind=None,wfile=None):
                  mcover=0
                  if wfile:
                      sel=wfile
                      self.anzeige_fav=_("Play file")
                  else:
                       sel=self.configfile2[2][ind]
                  if os.path.exists(sel[1]):
                     nam=os.path.basename(sel[1])
                     if L4LwbrFS: L4LwbrFS.delete( "wbrFS.02.pic1" )
                     self.play_stream={'sscr': 'default', 'genre2': "", 'zuv': 'unbekannt', 'name': nam, 'url': sel[1], 'bitrate': 0, 'volume': 0,'picon': 0, 'stream_id': 100, 'group1': 1, 'uploader': 'nn', 'descrip': '', 'genre': 'wbrfsfiles', 'rec': 0, 'typ': '', 'defekt': 0, 'cache': 0}
                     self.set_play_file_infos()
                     sind=None
                     if not wfile: 
                         self.playlist2_ind=self["streamlist"].getIndex()
                         sind=self.configfile2[2][self.playlist2_ind][1]
                     self.set_streamlist(self.configfile2[2],sind,None,self["streamlist"].getIndex())
                     sref = eServiceReference(4097, 0, sel[1])
                     self.session.nav.playService(sref)
                  else:
                     self.meld_screen(_("file not found"),"Info",20,"ERROR")

    def set_play_file_infos(self):
        kompl_path=self.play_stream["url"]
        dir2=os.path.dirname(kompl_path).split('/')
        if len(dir2)>2:
            dir2="... /"+dir2[-2]+"/"+dir2[-1]
        else:
            dir2=os.path.dirname(kompl_path)
        self.stream_info=self.play_stream["name"]
        self.streamname = dir2
        self.stream_info=dir2             
        self.fav_list=0
        self.display_art="normal"
        self.sets["bitrat"] = _("Len:")
        self.sets["bitrat_text"] = "0:00"
        ext=os.path.splitext(kompl_path)[1].replace(".","")
        self.sets["typ_text"] = ext
        if self.play_stream["typ"]=="from m3u":
            self.sets["typ_text"] = ext+" (m3u)"
        self.sets["fav"] = _("Dir:")
        self.sets["fav_text"]= dir2
        right_site.new_set(self.sets)
        mcover=0
        if os.path.exists(kompl_path):
                     pic_rumpf=kompl_path[:-3]
                     if L4LwbrFS: L4LwbrFS.delete( "wbrFS.02.pic1" )
                     if os.path.exists(pic_rumpf+"jpg"):
                                  copyfile(pic_rumpf+"jpg", "/tmp/.wbrfs_pic")
                                  mcover=1
                     elif os.path.exists(pic_rumpf+"png"):
                                  copyfile(pic_rumpf+"png", "/tmp/.wbrfs_pic")
                                  mcover=1
        self.play_stream["picon"]=mcover
        self.play_stream["typ"]= ext
        self.setTitle("webradioFS: "+_("My files")) 
        global web_liste_streams 
        web_liste_streams = self.configfile2[2]
        self.screensaver_off = 0
        self.ResetwbrScreenSaverTimer()

    def web_if_umschalt(self, stream):
        if self.tv1:self.live_tv()
        if stream is not None and (not self.record or self.rec_set_list["rec_art"]=="caching"):
                index=None
                for x in self.configfile2[2]:
                     if x[0]==stream or x[1]==stream:
                         found=True
                         if stream.endswith(".m3u"):
                             index=1
                             self.web_if_listplay((0,x[1]))
                         else:
                             index=self.configfile2[2].index(x)
                             self["streamlist"].setIndex(index)
                             self.ok()
                         break
                if not index and self.configfile2[1]>90:
                        self.web_if_fav_wechsel( _("My files"))

    def web_if_einzelplay (self, stream,back=1):
          count = 0
          playlist_aktiv=0
          if self.playlist2 and self.configfile2[2]==self.playlist2[2]: 
                for x in self.playlist2[2]:
                    if x[0] == stream[0]:
                        self.playlist2_ind=count
                        playlist_aktiv=1
                        self.ok()
                        break
                    count += 1
          if self.playlist2 and not playlist_aktiv:
              self.playlist2=None
              for x in self.configfile2[2]:
                        if x[0] == stream[0]:
                                self["streamlist"].setIndex(count)
                                self.playlist2_ind=count
                                playlist_aktiv=1
                                self.ok()
                                break
                        count += 1
          if not playlist_aktiv:
               self.auto_play=None
               self.sets["autoplay"]=auto_png_off
               back=None
               self.einzelplay=stream
               self.fav_name=_("My files")#+" - "
               
               self.play_file(None,stream)
          if back:
                  self.web_if_listplay((int(stream[4]),stream[3]),None,stream) 

    def web_if_fav_wechsel(self, fav):
        if self.tv1:self.live_tv()
        if fav is not None and (not self.record or self.rec_set_list["rec_art"]=="caching"):
                fav2=None
                for y in self.favoritenlist:
                    if y[0]==fav:
                        fav2=y
                if fav2:
                    self.fav_index=self.favoritenlist.index(fav2)
                    self.Favoriten_Wechsel2(fav2)

    def web_if_playdir(self, mdir=None):
        if mdir:
            index=None
            for x in self.configfile2[2]:
                   if x[1]==mdir:
                       index=self.configfile2[2].index(x)
            if index:
                self["streamlist"].setIndex(index)
                self.ok(None,None,auto=0)

    def web_if_playdir2(self, mdir=None):
        if mdir:
            index=None
            for x in self.configfile2[2]:    
                   if x[1]==mdir:
                       index=self.configfile2[2].index(x)
            if index:
                self["streamlist"].setIndex(index)
                self.ok(None,None,auto=1)

    def webrec(self):
        if l4l_info["rec"]==1:
             if self.record and self.cache_list != None and self.rec_set_list and self.rec_set_list["rec_art"]=="caching":     
                  self.cache_list="1"
                  self.check_cache()
             else:
                  self.rec_stop_a()
        elif l4l_info["rec"]==2:        
               self.caching_select()

        elif l4l_info["rec"]==0:
               self.rec_endless()

    def web_if_listplay(self, rfile=None,rdir=None,stream=None):
        if rfile:
                  listnew=[]
                  liste=None
                  self.akt_pl_num=0
                  b_dir=None
                  if rfile[0]==8:
                       mfile=rfile[1]
                       if rdir:
                          path1= rdir.split('/')
                          self.fav_name=_("Play from folder")+" ../"+path1[-2]
                       else:
                         if not rfile[1].endswith("m3u"):
                            path1= mfile.split('/')
                            self.fav_name="temp-"+_("Playlist")
                       num=8
                       if rfile[1].endswith("m3u"):
                           self.playlist_num=7
                           b_dir=os.path.dirname(rfile[1])
                           listnew.append([_("back"),b_dir,b_dir,0,0,0,0,"Dir1"])
                           self.fav_name=_("Files from")+"  "+os.path.basename(rfile[1])
                           num=7
                       else:
                           self.playlist_num=8
                           num=8   
                       self.pl_nums=0
                       self.auto_play=True
                       self.sets["autoplay"]=auto_png_on
                  else:
                      num=rfile[0]-1
                      self.pl_nums=sets_audiofiles["audio_listnums"].split(",")
                      self.playlist_num=num
                      if num==0:
                          mfile="/tmp/wbrfs_playlist"
                          self.fav_name=_("Playlist")+" tmp" 
                      else:
                          if sets_audiofiles["audio_listpos"] == True:
                              try:
                                  self.akt_pl_num=int(self.pl_nums[num-1])
                              except:
                                 pass
                          mfile="/etc/ConfFS/playlist"+str(num)+".m3u"
                          self.fav_name=_("Playlist")+" "+str(num)
                  if os.path.exists(mfile):
                     liste=playlist_read(mfile)
                  if liste and len(liste):
                    for x in liste:
                          if x[2].endswith(".m3u"):
                              if os.path.exists(x[2]):
                                  liste2=playlist_read(x[2])
                                  if liste2 and len(liste2):
                                     for x in liste2:
                                         listnew.append([x[1],x[2],x[3],0,90+num,0,str([x[0],x[1],x[2]]),"Files"])
                          else:
                              listnew.append([x[1],x[2],x[3],0,90+num,0,str([x[0],x[1],x[2]]),"Files"])
                  if len(listnew):
                       self.fav_stream_list=listnew
                       self.akt_pl_num=-1
                       self.set_rec_text(self.fav_name,"titel")
                       dir1=""
                       if len(self.configfile2)>5:dir1=self.configfile2[5]
                       self.configfile2=[self.fav_name,90+num,listnew,u_dir,a_sort,dir1]
                       self.playlist2=[self.fav_name,90+num,listnew,os.path.basename(mfile),a_sort]
                       if self.blaue_taste:self.blaue_taste.setText(_("Settings"))
                       if self.chill_taste:self.chill_taste.setText(_("Autoplay"))
                       self.red="play_all"
                       self["key_red2"].setText(_("Playlist"))
                       self.set_streamlist(self.configfile2[2],l4l_info["Station"],None,0)
                       self.playlist2_ind=0 
                       if stream:
                           self.web_if_einzelplay(stream,None)
                       else:
                           self.anzeige_fav=self.fav_name
                           self.auto_play=True
                           self.sets["autoplay"]=auto_png_on
                           self.auto_zap()
                  else:
                       self.meld_screen(os.path.splitext(os.path.basename(mfile))[0]+" "+_("contains no audio files\nor is incorrectly formatted"),"webradioFS - Info",20,"ERROR")

    def web_if_play_stop(self, st):
        if st:
           set_onwbrScreenSaver()
           self.stop_stream() 

    def web_if_exit(self):
        global onwbrScreenSaver
        onwbrScreenSaver = None
        self.exit(True,1)

    def keyNumberGlobal(self, number):
        if number is not None:
                if self.tv1:self.live_tv()
                if number==0:number =10
                index = number - 1
                if len(self.configfile2[2]) >= index+1:
                        self["streamlist"].setIndex(index)
                        self.ok()

    def mach_nix(self):
        pass

    def red_button_long(self):
        pass

    def blue_long(self):
        pass

    def createSummary(self):
        if self.display_on:return webradioFSdisplay13

    def selectionChanged(self):
        if onwbrScreenSaver == None:
            picon=def_pic
            if self.sets["logo"]:
               picon=self.sets["logo"]
            Zeile1=""
            Zeile3=""
            Zeile2=self.stream_info
            d_art="normal"
            if self.rec_anzeige==True and self.record:
                if l4l_info["rec"]==1:
                    Zeile2 = " *rec* "+ self.stream_info
                elif 1<l4l_info["rec"]<10:
                    Zeile2 = " *cache* "+ self.stream_info
            if self.display_art=="info": 
              d_art="info"
              Zeile2=self.ab_info
            elif self.configfile2:
                if self.e_help=="off":
                    if not self.playlist2 or self.configfile2[2]==self.playlist2[2]:
                           self["playtext"].setText(self.stream_info)
                if self.Dateiliste or self.configfile2[1]>29 and self.display_art != "normal":
                   self.wbrScreenSaver_stop()
                   self.display_art="fav"
                   picon=None
                   d_art="liste"
                   idx=self["streamlist"].getIndex()
                   try:
                     if idx > 0:
                       Zeile1= str(self.fav_stream_list[idx-1][0])
                     if idx+1 < len(self.fav_stream_list):
                       Zeile3= str(self.fav_stream_list[idx+1][0])
                     Zeile2=self["streamlist"].getCurrent()[0][0]
                   except:
                     pass
                elif self.fav_list:
                   self.display_art="fav"
                   d_art="liste"
                   idx=self["streamlist"].getIndex()
                   try:
                     if idx > 0:
                       Zeile1= str(self.favoritenlist[idx-1][0])
                     if idx+1 < len(self.favoritenlist):
                       Zeile3= str(self.favoritenlist[idx+1][0])
                     Zeile2=self["streamlist"].getCurrent()[0][0]
                   except:
                     pass
                elif self.configfile2[1] in [2,5,6,7]:
                      Zeile1 = "webradioFS - Database"
                      Zeile2=self.configfile2[0]
                elif self.display_art=="liste" and not self.sorting:
                   d_art="liste"
                   streamliste=[]
                   if self["streamlist"].getCurrent():
                       if self.sel_stream and self.sel_stream ==self.stream_info:
                           Zeile2=">>"+self.stream_info 
                       Zeile1 = self.streamvor
                       Zeile3 = self.streamnach
                       if L4LwbrFS and str2bool(l4ls[0]):
                          streamliste=[]
                          for x in self.fav_stream_list:
                                if x[0]==self["streamlist"].getCurrent()[0][0]:
                                   streamliste.append(">> "+x[0][0:20])
                                else:
                                  streamliste.append(" "*5+x[0])
                          txt = '\n'.join(x for x in streamliste)
                   else:
                       txt=_("Skin-Error or Favorites file faulty")
                       Zeile2=txt
                       Zeile1 = "webradioFS: error"
                       Zeile3 = "webradioFS: error" 
                       d_art="failed"
                       self.display_art="info2"
                       if L4LwbrFS:
                           L4LwbrFS.add( "wbrFS.05.box1",{"Typ":"box","PosX":0,"PosY":0,"Width":5000, "Height":600,"Color":"black" , "Screen":str(l4ls[3]),"Lcd":l4ls[1],"Mode":"OnMedia"} )
                           L4LwbrFS.add( "wbrFS.06.txt5",{"Typ":"txt","Align":"0","Width":500,"Pos":0,"Text":"\n"+txt+"\n","Size":str(l4ls[27]),"Color":str(l4ls[29]),"Screen":str(l4ls[3]),"Lines":20,"Lcd":l4ls[1],"Mode":"OnMedia"} )
                           if l4lR:L4LwbrFS.setScreen(l4ls[3],l4ls[1],True)
                       if not len(self.fav_stream_list):
                           meld=_("This Favorite-Group is empty")
                       else:
                           meld=_("Skin-Error or Favorites file faulty")+"\n"+_("Favorites file can be deleted and recreated in the menu Extras")
                       self.meld_screen(meld,"Info",20,"ERROR")
                       set_display(Zeile1,Zeile2,Zeile3)
                if d_art=="liste" and not self.sorting:
                   if L4LwbrFS and str2bool(l4ls[0]):
                       streamliste=[]
                       for x in self.fav_stream_list:
                            if self["streamlist"].getCurrent() and x[0]==self["streamlist"].getCurrent()[0][0]:
                               streamliste.append(">> "+x[0])#[0:20]
                            else:
                              streamliste.append(" "*5+x[0])
                       txt = '\n'.join(x for x in streamliste)
                       L4LwbrFS.add( "wbrFS.05.box1",{"Typ":"box","PosX":0,"PosY":0,"Width":5000, "Height":600,"Color":"black" , "Screen":str(l4ls[3]),"Lcd":l4ls[1],"Mode":"OnMedia"} )
                       L4LwbrFS.add( "wbrFS.06.txt5",{"Typ":"txt","Align":"0","Width":500,"Pos":0,"Text":txt,"Size":str(l4ls[27]),"Color":str(l4ls[29]),"Screen":str(l4ls[3]),"Lines":20,"Lcd":l4ls[1],"Mode":"OnMedia"} )
                       if l4lR:L4LwbrFS.setScreen(l4ls[3],l4ls[1],True)
                elif d_art != "failed":
                   if l4lR and L4LwbrFS and str2bool(l4ls[0]):
                       L4LwbrFS.delete("wbrFS.05.box1")
                       L4LwbrFS.delete("wbrFS.06.txt5")
                   Zeile1 = self.streamname
                   Zeile3 = "Fav.: "+self.anzeige_fav
                   set_display(Zeile1,Zeile2,Zeile3)
            if self.fav_list==2:d_art="fav"
            if self.upadate_taste:
                if self["streamlist"].getCurrent() and len(self["streamlist"].getCurrent()[0])>6 and self["streamlist"].getCurrent()[0][7]=='radio':
                          self.upadate_taste.setText(_("Stream Actions"))
            for cb in self.onChangedEntry:
                        cb(Zeile1,Zeile2,Zeile3,d_art,picon)

    def textPressed(self):
            if self.stream_info != "n/a" and self.stream_info != "":
                savepath=sets_exp["coversafepath"]
                info=titel_save(self.stream_info,savepath).inf
                self.meld_screen(info,"webradioFS - Info",20)

    def live_tv(self):
      if SystemInfo.get("NumVideoDecoders", 1) <2:	
        self.meld_screen(_("Sorry, live-TV not possible on this box"),"Info",20)
      else:        
        if self.tv1:
            self.tv1.stopService()
            self.session.deleteDialog(self.tv1)
            self.tv1 = None
            if self.tv_ton:
                self.ok()
            self.show()
            right_site.show()
            self.ResetwbrScreenSaverTimer()
        else:
                self.hide()
                right_site.hide()
                self.instance.clearBackgroundColor()
                self.wbrScreenSaverTimer.stop()
                self.tv1= self.session.instantiateDialog(webradioFS_video)
                self.tv1.start(self.oldService)

    def full_tv(self):
        if self.tv1 and not self.tv_ton:
            self.tv1.stopService()
            self.session.deleteDialog(self.tv1)
            self.tv_ton=True
            self.session.nav.playService(self.oldService)   
        else:
                self.tv1= self.session.instantiateDialog(webradioFS_video)
                self.tv1.start(self.oldService)

    def pvideo(self,vid=None):
      if SystemInfo.get("NumVideoDecoders", 1) <2:
           self.meld_screen(_("Sorry, Video-Screensaver not possible on this box"),"webradioFS - Info",20,"Info")
      else:
        if self.video:
            self.video.stopService()
            self.session.deleteDialog(self.video)
            if self.vidTimer:
                self.vidTimer.stop()
                self.vidTimer=None
            self.video = None
            self.ok()
            right_site.show()
            self.show()
            self.ResetwbrScreenSaverTimer()
        else:
            file1=None
            art=sets_scr["screensaver_art"]
            self.v_list=[]
            self.v_index=0
            self.vid_art="single"
            if vid:
                file1=vid
            elif art == "Play_Video":
                file1=sets_scr["wbrvideofile"]
            if file1 and fileExists(file1):
                    file1_pur=file1.split("/")[-1]
                    self.v_list.append((file1_pur,file1))
            else:
                file1=None
            if not file1:
                mpath=sets_scr["wbrvideopath"]
                if os.path.exists(mpath) is True:
                    vPattern = (".mpg",".mov",".mp4",".mkv",".avi",".ts",".mpeg",".mp2",".vob",".iso",".flv",".msts")
                    for file2 in os.listdir(mpath):
                       if file2.lower().endswith(vPattern): 
                                 self.v_list.append((file2,mpath+file2))
            if len(self.v_list):
                if art=="Play_Video_rand":
                   random.shuffle(self.v_list)
                self.v_list.sort(key=lambda x: "".join(x[0]).lower())
                if (vid or art == "Play_Video") and file1:
                        self.v_index=self.v_list.index((file1_pur,file1))
                elif art == "Play_Video_rand": 
                        self.v_index=random.randint(0, len(self.v_list)-1)
                        self.vid_art="random"
                elif art == "Play_Video_sort":
                        self.vid_art="sorted"
                if len(self.v_list)>self.v_index and fileExists(self.v_list[self.v_index][1]):
                    self.hide()
                    right_site.hide()
                    self.wbrScreenSaverTimer.stop()
                    if sets_scr["wbrvideorecurr"]>0:
                        self.vidTimer = eTimer()
                        if fontlist[4]:
                            self.vidTimer_conn = self.vidTimer.timeout.connect(self.v_restart)
                        else:
                            self.vidTimer.callback.append(self.v_restart)
                    self.vidstart()
                else:
                   txt=_("Screensaver-Video-File")+" "+ self.v_list[self.v_index][1]+" "+_("not exist")
                   self.ResetwbrScreenSaverTimer()
                   self.meld_screen(txt,"Info",20,"ERROR")
            else:
                   self.meld_screen("no video-files found (the setting is changed then please re-start)","Info",20,"ERROR")            

    def v_restart(self,next=None):
            self.v_index+=1
            if self.v_index>len(self.v_list)-1:self.v_index=0
            self.vidTimer.startLongTimer(sets_scr["wbrvideorecurr"])
            self.vidstart()

    def video_list(self):
            self.session.openWithCallback(self.video_list2, ChoiceBox, title=_("Select Group"), list=self.v_list)
    def video_list2(self,select):
            if select and select is not False:
                self.v_index=self.v_list.index(select)
                self.vidstart()
    def vidstart(self):
            right_site.hide()
            if fileExists(self.v_list[self.v_index][1]):
                if self.v_list[self.v_index][1].endswith(".ts"):
                    self.video3 = eServiceReference("1:0:0:0:0:0:0:0:0:0:" + self.v_list[self.v_index][1])
                else:
                    self.video3 = eServiceReference("4097:0:0:0:0:0:0:0:0:0:%s" % self.v_list[self.v_index][1])
                if self.video==None:
                    self.video= self.session.instantiateDialog(webradioFS_video)
                if sets_scr["wbrvideorecurr"]>0:
                    self.vidTimer.startLongTimer(sets_scr["wbrvideorecurr"])
                self.video.start(self.video3)
            else:
                self.v_restart()
    def live_tv_next(self):
        if self.video:
            self.v_restart("next")
        elif self.tv1:
           if self.servicelist is not None:
              if self.servicelist.inBouquet():
                prev = self.servicelist.getCurrentSelection()
                if prev:
                    prev = prev.toString()
                    while True:
                        if config.usage.quickzap_bouquet_change.value and self.servicelist.atEnd():
                            self.servicelist.nextBouquet()
                        else:
                            self.servicelist.moveDown()
                        cur = self.servicelist.getCurrentSelection()
                        if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
                               break
              else:
                   self.servicelist.moveDown()
              if self.isPlayable():
                   current = ServiceReference(self.servicelist.getCurrentSelection())
                   self.oldService=current.ref
                   self.tv1.start(self.oldService)
              else:
                   self.nextService()

    def live_tv_prev(self):
        if self.video:
            self.video_list()
        elif self.tv1:
                if self.servicelist is not None:
                        if self.servicelist.inBouquet():
                                prev = self.servicelist.getCurrentSelection()
                                if prev:
                                        prev = prev.toString()
                                        while True:
                                                if config.usage.quickzap_bouquet_change.value and self.servicelist.atBegin():
                                                        self.servicelist.prevBouquet()
                                                self.servicelist.moveUp()
                                                cur = self.servicelist.getCurrentSelection()
                                                if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
                                                        break
                        else:
                                self.servicelist.moveUp()
                        if self.isPlayable():
                                current = ServiceReference(self.servicelist.getCurrentSelection())
                                self.oldService=current.ref
                                self.tv1.start(self.oldService)
                        else:
                                self.prevService()

    def isPlayable(self):
        current = ServiceReference(self.servicelist.getCurrentSelection())
        return not (current.ref.flags & (eServiceReference.isMarker|eServiceReference.isDirectory))
#####################################################################################################
    def check_defekt(self):
        self.selk()
####################################################################################

    def selk(self):
     if self.e_help == "off": 
      if not self.auto_play and not self.tv1:self.ResetwbrScreenSaverTimer() # 
      if self["streamlist"].getCurrent():
        if self.configfile2[1] >29:
                  if self.display_art!="info":
                      self.display_art="liste"
                  self["key_red2"].setText(_("Playlists"))
                  if self.upadate_taste: self.red="play_all"
                  self.selectionChanged()
        elif self.fav_list:
            self.red="no"
            self["key_red2"].setText("")
            if self["streamlist"].getCurrent()[0][1]==0:
                self.red="del_group"
                self["key_red2"].setText(_("Group tools"))
            if self.display_art!="info":self.selectionChanged()
        else:
           if len(self["streamlist"].getCurrent()[0]) >3:
            if self.upadate_taste and self.configfile2[1]==0: 
               self.upadate_taste.setText("")
               self.red="play_false"
               if self.play_stream and self["streamlist"].getCurrent()[0][0]==self.play_stream["name"]:
                      self.upadate_taste.setText(_("Stream Actions"))
                      self.red="play_ok"
            if 1==1:
              self.streamvor=" "
              self.streamnach=" "
              self.setTitle("")
              self.setTitle(self["streamlist"].getCurrent()[0][0]+"  ("+self.configfile2[0]+")")
              self.stream_info= self["streamlist"].getCurrent()[0][0]
              idx=self["streamlist"].getIndex()
              if self.rec_list ==True:
                  liste=self.filelist
                  num=1
              else:
                  liste=self.fav_stream_list
                  num=0
              if idx > 0:
                self.streamvor= liste[idx-1][num]
              if idx+1 < len(liste):
                self.streamnach= liste[idx+1][num]
              if self.display_art!="info":
                self.display_art="liste"
                self.selectionChanged() 
        self.display_timer.start(15000)

    def importer(self):
          txt=_("function not exist")+",\n"
          self.meld_screen(txt,"webradioFS - Info",20)

    def ondisplayFinished(self):
           self.display_timer.stop()
           if sets_scr["timeout"] > 0:
               self.wbrScreenSaverTimer.startLongTimer(sets_scr["timeout"])
           if streamplayer.is_playing and self.configfile2[1]==0 :
               try:
                   self["streamlist"].setIndex(self.fav_stream_list.index((self.play_stream["name"],self.configfile2[1],self.play_stream["stream_id"],self.play_stream["defekt"],self.configfile2[1])))
                   self.streamname=self.play_stream["name"]
                   self.fav_name=self.anzeige_fav #self.play_fav
                   self.stream_info="webradioFS"
               except:
                   pass           
           elif self.configfile2[1] in (2,3,4,5,6,7) and self.play_stream:
                     self.streamname=self.play_stream["name"]+ _(", add to fav for all functions")
                     self.fav_name=self.anzeige_fav
           if self.display_art !="info":
               self.display_art="normal"
               self.selectionChanged()

## rip ###############################################
    def dataAvail(self, data):
        data2=data.lower()
        if (len(str(data2))<25 and data2.startswith("streamripper ")) or ("error" in data2 and not "terror" in data2):
            f=open("/var/webradioFS_debug.log","a")
            f.write(str(data)+"\n")
            f.close()
            self.rs_info2(data)
        else:
          if self.rec_set_list["rec_art"] !="caching":  
            if "re-connecting" in data:
                self.wbrfs_recClosed2("stopped")
                self.meld_screen(_("Recording stopped, interrupted stream"),"webradioFS - Info",20)
            elif self.rec_path1:
                if self.rec_path1:
                      directory= self.rec_path1+"incomplete/"
                else:
                      directory= self.rec_path+"incomplete/"
                try:
                    for name in os.listdir(directory):
                        delx=0
                        fullpath = os.path.join(directory,name)
                        name2=name
                        if os.path.isfile(fullpath):
                            if self.rec_set_list["neg_filter"]:
                                if re.search(self.rec_set_list["neg_filter"],name.lower()):
                                    delx=1 
                            if self.rec_set_list["pos_filter"]:
                                if not re.search(self.rec_set_list["pos_filter"],name.lower()):
                                              delx=1 
                            if delx==0:
                                    if name.startswith(" -"):
                                       dat=strftime("%d%m%Y_%H%M",localtime())
                                       name2=name.replace(" -","incompled_"+dat)
                                    if name.endswith(".jpg"):
                                        if self.rec_set_list["rec_cover"]:
                                           ret = copyfile(sets_exp["coversafepath"]+name, self.rec_path+"cover/"+name2)
                                    else:
                                        ret = copyfile(directory+name, self.rec_path+name2)
                            os.unlink(directory+name)
                except:
                    pass

    def rec_stop_a(self,answer =True):
        if answer:
           self.rec_stop()
           self.showConfigDone()
           if self.rec_set_list["rec_art"]=="caching":
                   self.wbrfs_recClosed2("no_save")
           elif answer=="streamswitch":
              self.meld_screen(_("Current record keeping?"),"webradioFS- "+_("query"),20,"??",self.rec_stop_b,True)
           elif sets_rec["inclp_save"]==0:
              self.meld_screen(_("Current record keeping?"),"webradioFS- "+_("query"),20,"??",self.rec_stop_b,True)
           elif sets_rec["inclp_save"]==1:
              self.wbrfs_recClosed2("save")
           elif sets_rec["inclp_save"]==2 :
              self.wbrfs_recClosed2("no_save")

    def rec_stop_b(self,val):
        if val is True:   
               self.wbrfs_recClosed2("save")
        else:
               self.wbrfs_recClosed2("no_save")

    def rec_stop(self):
         try:  
           if self.containerwbrfs_rec and self.containerwbrfs_rec.running():
               self.containerwbrfs_rec.sendCtrlC()
         except:
             pass

    def rec_stop2(self,ans=None):
        global l4l_info
        if ripper_installed==True and not self.cache_list:
           l4l_info["rec"]=0
           l4l_set.set_l4l_info(l4l_info)
           self.time_text=None
           self.record=None
           self.check_root_rec()
           self["rec_pic"].hide()
           self.set_rec_text(_("no recording is in progress or timer planned"),"default")
           if self.rec_timer.isActive():
                    self.rec_timer.stop()
           if self.stream_url: 
                    self.pl1=streamplayer.play(self.stream_url)
           else:
                   self.stop_stream()
        elif self.cache_list:
                 self.rec_cache()

    def rec_stop3(self,ans=None):
           self.time_text=0
           self.record=None
           self.check_root_rec()
           if self.stream_url: 
                    self.pl1=streamplayer.play(self.stream_url)
           else:
                   self.stop_stream()

    def rec_stop_c(self,val):
        if val is True: 
            self.rec_stop()
            self.rec_stop2(1)
            self.wbrfs_recClosed2("exit")

    def wbrfs_recClosed2(self, retval=None):
            global l4l_info
            cover_save=(None,None)
            self.rec_stop()
            l4l_info["rec"]=0
            l4l_set.set_l4l_info(l4l_info)
            if self.check:
                self.check=None
                self.showConfigDone()
            else:
              if retval and retval=="no_save" and self.rec_filename:  
                  try:
                      os.unlink(os.path.join(self.rec_path,self.rec_filename+".mp3"))
                      os.unlink(os.path.join(self.rec_path,self.rec_filename+".cue"))
                      self.meld_screen(_("recording has deleted"),"webradioFS - Info",20)
                  except:
                     self.meld_screen(_("error on delete"),"webradioFS - Info",20)
              elif retval and self.rec_filename:
                     self.meld_screen(_("recording has finished"),"webradioFS - Info",20)
              elif retval:
                if self.rec_set_list["rec_art"]=="caching":
                     cdr_dir=sets_rec["rec_caching_dir"]
                     if not cdr_dir.endswith("/"):cdr_dir=cdr_dir+"/"
                     cdr_dir=cdr_dir+"wbrfs_cache"
                     cdr=cdr_dir+"/incomplete"
                     try:
                       if os.path.exists(cdr):
                         for name in os.listdir(cdr):
                             if os.path.isfile(cdr+"/"+name):
                                   if retval == "save":
                                       name2=name
                                       if name.startswith(" - ."): 
                                           dat=strftime("%d%m%Y_%H%M",localtime())
                                           name2=name.replace(" - ",dat)
                                       copyfile(cdr+"/"+name, sets_rec["path"]+name2)
                                   os.unlink(cdr+"/"+name)
                       if os.path.exists(cdr_dir):
                         for name in os.listdir(cdr_dir):
                               if os.path.isfile(cdr_dir+"/"+name):
                                   if retval == "save":
                                     if self.cache_list and len(self.cache_list)>6:
                                         if self.cache_list.replace(" (1)","") == name.replace(" (1)",""):
                                             copyfile(cdr_dir+"/"+name, sets_rec["path"]+name)
                                   os.unlink(cdr_dir+"/"+name)

                     except Exception as e:
                         f=open("/var/webradioFS_debug.log","a")
                         f.write("record-error 2028:\n"+str(e)+"\n")
                         f.close()
                     if self.cache_list==None:
                         self.rec_set_list["rec_art"]="endless"
                         try:
                             if os.path.exists(cdr):os.rmdir(cdr)
                             os.rmdir(cdr_dir)
                         except Exception as e:
                             f=open("/var/webradioFS_debug.log","a")
                             f.write("record-error 2042:\n"+str(e)+"\n")
                             f.close()
                     else:
                         self.cache_list="0"
                         l4l_info["rec"]=0
                         l4l_set.set_l4l_info(l4l_info)
                else:
                  if self.rec_path:
                    save_dir=self.rec_path
                    if not self.rec_path.endswith("/"): save_dir=self.rec_path+"/"
                    if self.rec_path1:
                        directory= self.rec_path1
                    else:
                        directory= self.rec_path
                    if not  directory.endswith("/"):directory=directory+"/"
                    if os.path.exists(directory+"incomplete/"):
                      directory= directory+"incomplete/"
                      for name in os.listdir(directory):
                          fullpath = os.path.join(directory,name)
                          if os.path.isfile(fullpath):
                            if retval == "save":
                                name2=name
                                if name.startswith(" - ."):
                                   dat=strftime("%d%m%Y_%H%M",localtime())
                                   name2=name.replace(" - ",dat)
                                copyfile(directory+name, save_dir+"incomplete_"+name2)
                            os.unlink(directory+name)
                      self.meld_screen(_("recording has finished"),"webradioFS - Info",20)                            
                    else:
                        self.meld_screen(_("Directory incomplete not exist"),"webradioFS - Info",20)
                    try:
                        os.rmdir(directory)
                        if self.rec_path1: os.rmdir(self.rec_path1)
                    except:
                        pass
                self.record=None
                self.check_root_rec()
                if self.exit_art=="off":
                   self.exit(True,1)
                elif self.exit_art =="standby":
                   self.exit(True,"standby")
                else:
                    self.showConfigDone()

    def rec_endless(self):
        if sets_opt["rec"] and ripper_installed==True:
            if streamplayer.is_playing and self.play_stream and self.stream_url and len(self.stream_url) != 0 and int(self.play_stream["defekt"])==0:
              if self.cache_list != None:
                   self.caching_select()
              elif self.record:
                self.meld_screen(_("Do you really want to stop the recording?"),"webradioFS- "+_("query"),20,"??",self.rec_stop_a,False)
              elif not self.record and self.rec_timer.isActive():
                if self.configfile2[1]==0:
                    self.meld_screen(_("Discard scheduled timer?"),"webradioFS- "+_("query"),20,"??",self.rec_stop_c,True)
                else:
                    self.meld_screen(_("Record only from your Favorites"),"Info",20)
              else:
                 if self.configfile2[1]==0:
                      if self.stream_url and len(self.stream_url) != 0:
                           self.rec_set_list["rec_path"]=sets_rec["path"]
                           self.rec_set_list["rec_cover"]=sets_rec["cover"]
                           self.rec_set_list["rec_split"]= sets_rec["split"]
                           self.rec_set_list["rec_new_dir"]= sets_rec["new_dir"]
                           self.rec_set_list["rec_art"]="endless"
                           self.rec_set_list["rec_dauer"]= 0
                           self.time_text=0
                           self.rec_start()
                           self.showConfigDone()
                 else:
                     self.meld_screen(_("Record only from your Favorites"),"Info",20)
            else:
                self.meld_screen(_("No Stream running to be recorded!"),"Info",20,"ERROR")
        else:
             self.rs_info()

    def caching_select(self):
      root=self.check_root_rec()
      if root:
             self.rec_stopcache()
             self.meld_screen(('Stopped caching, error in GStreamer-modul'),"Info",0,"ERROR")
      else:
        if self.record and os.path.exists(self.rec_set_list["rec_path"]):
          search_path=self.rec_path
          if not self.root_rec or self.root_rec != "1":
                         self.check_root_rec()
          if self.root_rec and self.root_rec != "1":
                     search_path=self.root_rec
          if not search_path.endswith("/"):search_path=search_path+"/"
          if int(self.play_stream["cache"])==1:
              song_liste=[]
              for name in os.listdir(search_path+"incomplete/"):
                 if not name.startswith(" - ."):   
                    dtime=os.path.getmtime(search_path+"incomplete/"+name)
                    song_liste.append((dtime,name))
              if len(song_liste):
                  song_liste.sort(key=lambda x: x[0])
                  name=song_liste[len(song_liste)-1][1]
                  self.caching_select2(("einzel",name))
          elif self.cache_list != None:
              self.cache_list = None
              self.wbrScreenSaver_stop()
              self.session.openWithCallback(self.caching_select2,cache_list_menu,self.rec_set_list["rec_path"],sets_rec["path"])

    def caching_select2(self,answer=None):
        self.cache_list = "1"
        global l4l_info
        search_path=self.rec_path
        root=self.check_root_rec()
        if root:
             self.rec_stopcache()
             self.meld_screen(('Stopped caching, error in GStreamer-modul'),"Info",0,"ERROR")
        else:
          if not search_path.endswith("/"):search_path=search_path+"/"
          if answer[1] and (not answer[0] or answer[0]=="einzel"):
              song_liste=[]
              for name in os.listdir(search_path+"incomplete/"):
                    song_liste.append(name)
              if len(song_liste)==1:
                 if not name.strip().startswith(" -"):  
                   self.cache_list = answer[1]
                   l4l_info["rec"]=1
                   l4l_set.set_l4l_info(l4l_info)
                   txt= answer[1]
                   if len(answer[1])>50:
                       txt=answer[1][0:50]+"..."
                   self["rec_pic"].show()
                   recp = resolveFilename(SCOPE_CURRENT_SKIN, "/usr/lib/enigma2/python/Plugins/Extensions/webradioFS/skin/images/rec1.png")
                   self["rec_pic"].instance.setPixmap(LoadPixmap(recp))
                   self.set_rec_text(_("Saving") + ": "+txt,"cache")
             

          elif answer[0]=="stopped":
                    self.rec_stopcache()
          else:
              self.set_rec_text(_("press record for save a title"),"cache")
              self.showConfigDone()                 

    def rec_stopcachea(self,answer=False):
            if answer==True: 
               self.rec_stopcache()

    def rec_stopcache(self,answer=False):
           self.rec_stop()
           self["rec_pic"].hide()
           cover_save=(None,None)
           self.set_rec_text(_("no recording is in progress or timer planned"),"default")	
           self.cache_list=None

           if answer==False:
               self.menu_on=False
           self.display_art="normal"
           self.menu_back()
           self.rec_stop_a(True)

    def rec_time(self):
       if self.cache_list==None:
          if self.record:
              err=None
              root=self.check_root_rec()
              if root: err=1

              if self.time_text>0 and err:
                if err==1 or err==2:
                    self.wbrfs_recClosed2("stopped")
                    txt= _("Recording stopped, Error in system-modul GStreamer")+"\n"+_("show for update on your image")
                    self.meld_screen(txt,"webradioFS - Info",0,"ERROR")
              else:
                  self["rec_pic"].show()
                  recp = resolveFilename(SCOPE_CURRENT_SKIN, "/usr/lib/enigma2/python/Plugins/Extensions/webradioFS/skin/images/rec1.png")
                  self["rec_pic"].instance.setPixmap(LoadPixmap(recp))
                  if self.rec_set_list["rec_art"] !="caching":
                   if self.rec_set_list["rec_art"]=="endless":
                        self.time_text=int(self.time_text)+1
                        self.set_rec_text(_("record, len: ")+str(self.time_text-1)+ _(" min"),"record")
                   else:
                       if self.rec_set_list["rec_dauer"] > 1:
                          self.set_rec_text(_("Record, time remaining:")+" "+str(self.time_text)+ _(" min"),"record")
                          self.time_text=int(self.time_text)-1
                   self.rec_timer.startLongTimer(60)
          elif self.rec_plan:
                 recp = resolveFilename(SCOPE_CURRENT_SKIN, "/usr/lib/enigma2/python/Plugins/Extensions/webradioFS/skin/images/rec2.png")
                 self["rec_pic"].show()
                 self["rec_pic"].instance.setPixmap(LoadPixmap(recp))
                 if self.rec_set_list["rec_art"] == "only switch":
                     self.set_rec_text(_("stream switching is scheduled in:")+" "+str(self.time_text)+ _(" min"),"timer")
                 else:
                     self.set_rec_text(_("Recording is scheduled in")+" "+str(self.time_text)+ _(" min"),"timer")
                 self.time_text=self.time_text-1
                 if self.time_text<1:
                    if self.rec_set_list["rec_dauer"]:self.time_text=int(self.rec_set_list["rec_dauer"])
                    self.rec_plan=False
                 self.rec_timer.startLongTimer(60)
          else:
                  self.rec_start()

    def rec_set(self):
         if sets_opt["rec"] and ripper_installed==True:
             if self.record:
                 self.meld_screen(_("Do you really want to stop the recording?"),"webradioFS- "+_("query"),20,"??",self.rec_stop_a,True)
             elif self.rec_timer.isActive():
                 self.meld_screen(_("Discard scheduled timer?"),"webradioFS- "+_("query"),20,"??",self.rec_stop_c,True)
             else:
                 if len(self.fav_stream_list) and self.play_stream:
                   for x in self.fav_stream_list:
                            if x[0]==self.play_stream["name"]:
                                self.rec_id= self.fav_stream_list.index(x)+1
                   self.rec_id_nr=self.play_stream["stream_id"]
                   if self.configfile2[1]==0:
                     if self["streamlist"].getCurrent():
                         stream=[self.play_stream["name"],self.configfile2[0],self.play_stream["rec"]]
                         self.session.openWithCallback(self.rec_setCallback,rec_menu_13,stream,self.display_on,l4ls)
                   else:
                       self.meld_screen(_("Record only from your Favorites"),"Info",20)
         else:
             self.rs_info()

    def rec_setCallback(self, art=None,dauer=0,start_time=None,rec_split=None,subdir=None,rec_cover=False,rec_path="/tmp/",pos=None,neg=None):
            self.rec_set_list["rec_path"]=rec_path
            self.rec_set_list["rec_cover"]=rec_cover
            self.rec_set_list["rec_split"]= rec_split
            self.rec_set_list["rec_new_dir"]= subdir
            self.rec_set_list["rec_dauer"]= dauer
            self.rec_set_list["rec_art"]= art
            self.rec_set_list["pos_filter"]=pos
            self.rec_set_list["neg_filter"]=neg
            self.showConfigDone()
            self.rec_cover=rec_cover
            self.rec_path1=None
            if art:
                if art=="by minutes" and dauer != "0":
                   self.time_text=int(self.rec_set_list["rec_dauer"])
                   self.rec_start()
                elif art=="by time" and dauer >0 and start_time >0:
                   self.time_text=start_time 
                   self.rec_plan=True
                   self.rec_timer.start(1)
                elif art=="only switch" and start_time >0:
                   self.time_text=start_time 
                   self.rec_plan=True
                   self.rec_timer.start(1)
                elif art=="endless":
                   self.time_text=0
                   self.rec_start()

    def rec_start(self):
             if sets_opt["rec"]:   
                if self.rec_set_list["rec_path"]=='/tmp/webradio_record':
                   self.meld_screen(_("Warning! The recordings are saved to '/tmp' and can overload the memory, it is better in the settings of a directory to put on hdd or usb stick\nSave recordings to tmp really?"),"webradioFS- "+_("query"),20,"??",self.rec_start2,False)
                else:
                   self.rec_streamwechsel()

    def rec_streamwechsel(self):
          if onwbrScreenSaver: set_onwbrScreenSaver()
          if self.rec_set_list["rec_art"] !="endless":
               for x in self.favoritenlist:
                   if x[1]==0:
                       for x2 in x[2]:
                            if x2[2] == self.rec_id_nr:
                               self.fav_index=self.favoritenlist.index(x)
                               self.favoriten()
                               break
               try: 
                   self.keyNumberGlobal(self.rec_id)
               except:
                  pass
          if self.rec_set_list["rec_art"]!="caching":
            if self.rec_set_list["rec_art"] == "only switch":
                      self.set_rec_text(_("no recording is in progress or timer planned"),"default")
                      self["rec_pic"].hide()
                      self.showConfigDone()
            else:
                         self.rec_start2()

    def rec_cache(self):
      if self.wbrfs_rec_BIN:  
        self.record=None
        self.cache_timer.stop() 
        cdr_dir=sets_rec["rec_caching_dir"]
        if not cdr_dir.endswith("/"):cdr_dir=cdr_dir+"/"
        cdr_dir=cdr_dir+"wbrfs_cache"
        cdr=cdr_dir+"/incomplete"
        cover_save=(None,None)
        self.cache_list="1"
        if self.containerwbrfs_rec and self.containerwbrfs_rec.running():
               self.containerwbrfs_rec.sendCtrlC()
        else:
          self.check_root_rec()
          if os.path.exists(cdr):
                    for name in os.listdir(cdr):
                            os.unlink(cdr+"/"+name)
                    os.rmdir(cdr)
          if not self.record and self.configfile2[1]==0 and self.play_stream["typ"]!="pvr":
            if self.stream_url and len(self.stream_url) != 0:
                if not os.path.exists(cdr_dir):os.mkdir(cdr_dir)
                self.rec_set_list["rec_path"]=cdr_dir+"/"
                if not os.path.exists(self.rec_set_list["rec_path"]):os.mkdir(self.rec_set_list["rec_path"])
                self.cache_list="1"
                self.rec_set_list["rec_dauer"]=0
                self.rec_set_list["rec_art"]="caching"
                self.rec_set_list["rec_cover"]=sets_rec["cover"]
                self.rec_set_list["rec_split"]= True
                self.rec_set_list["rec_new_dir"]= False
                self.time_text=0
                self.rec_start2()
                if streamplayer.is_playing:
                    self.set_rec_text(_("start caching..."),"default")
                self.menu_on=False
                self["rec_pic"].hide()
                self.display_art="normal"
                self.menu_back()
          elif self.configfile2[1]!=0:
            self.meld_screen(_("Record only from your Favorites"),"Info",20)
          else:
            pass 

    def rec_start2(self):
                global l4l_info
                global cover_save
                self.rec_filename=None
                if sets_opt["rec"]:    
                    self.rec_path1=None
                    if self.rec_set_list["rec_art"]=="caching":
                         l4l_info["rec"]=int(sets_rec["caching"])+1
                    else:
                          l4l_info["rec"]=1
                    l4l_set.set_l4l_info(l4l_info)
                    if not os.path.exists(self.rec_set_list["rec_path"]):
                       if self.cache_list:
                           self.rec_stopcache()
                       self.meld_screen(_("Path")+"\n"+self.rec_set_list["rec_path"]+"\n"+_(" not exist!"),"webradioFS - Info",20,"ERROR")
                    elif int(self.play_stream["rec"])>0:
                       self.meld_screen(_("the sender does not allow recording"),"webradioFS - Info",20)
                    else:
                        recordingLength =  int(self.rec_set_list["rec_dauer"]) * 60
                        self.rec_path = self.rec_set_list["rec_path"].strip()
                        if not self.rec_path.endswith("/"):self.rec_path=self.rec_path+"/"
                        if self.rec_set_list["rec_new_dir"]:
                           str_verz=self.play_stream["name"].strip()#.replace("/","_")
                           entf1=(" ".join(re.findall(r"[A-Za-z0-9üäöÜÄÖß\-\+]*", str_verz))).replace("  "," ").replace("   "," ")
                           self.rec_path = self.rec_path+entf1.strip()
                        if not os.path.exists(self.rec_path):
                                os.mkdir(self.rec_path)
                        if os.path.exists(self.rec_path):
                            if self.rec_set_list["rec_art"] !="caching" and (self.rec_set_list["pos_filter"] or self.rec_set_list["neg_filter"]):
                                 self.rec_path1=self.rec_path+"tmp/"
                                 if not os.path.exists(self.rec_path1):
                                       os.mkdir(self.rec_path1)
                            args = " "
                            args+=self.stream_url.decode("utf-8", "ignore")
                            args+=' -s'
                            args+=' -r '
                            args+='9555'
                            if recordingLength > 0:
                                args+=' -l'
                                args+=" %d" % int(recordingLength)
                            if self.rec_set_list["rec_split"]==False:
                                self.rec_filename=self.play_stream["name"].replace(" ","_")+strftime('_%Y%m%d_%H_%M_%S', localtime())
                                args+=' -a '+self.rec_filename+' -A'
                            args+= ' --codeset-filesys=ISO-8859-15'
                            args+= ' --codeset-metadata=ISO-8859-15'
                            args+= ' --codeset-relay=ISO-8859-15'
                            args+= ' -u "WinampMPEG/5.0"'
                            if self.rec_path1:
                                args+=  ' -d "'+self.rec_path1+'"'
                                self.rec_check_path= self.rec_path1
                            else:
                                args+=  ' -d "'+self.rec_path+'"'
                                self.rec_check_path= self.rec_path
                            cmd = self.wbrfs_rec_BIN + args.encode('utf-8')
                            try:
                              if self.containerwbrfs_rec:   
                                 self.containerwbrfs_rec.execute(cmd)
                                 self.record=True
                                 self.root_rec=None
                                 if self.rec_set_list["rec_art"] !="caching":
                                      if sets_rec["cover"]:cover_save["cache"]=None
                                      self.rec_timer.start(1)
                                 else:
                                      if sets_rec["cover"]:
                                          cover_save["cache"]=True
                                          cover_save["path"]=self.rec_path
                                      if not self.cache_timer.isActive():self.cache_timer.startLongTimer(10)    
                                 self.showConfigDone()
                            except Exception as e:
                                 f=open("/var/webradioFS_debug.log","a")
                                 f.write("record-error:\n"+str(e)+"\n"+str(args)+"\n")
                                 f.close()
                                 self.meld_screen(('Record-Error, error-text in\n/var/webradioFS_debug.log'),"Info",0,"ERROR")
                        else:
                            self.meld_screen(('Record-Error, path not exist\n')+str(self.rec_path),"Info",0,"ERROR")

    def playServiceStream(self, url):
                self.session.nav.stopService()
                sref = eServiceReference(4097, 0, url)
                self.session.nav.playService(sref)

    def rs_info(self):
        arm=None
        if not sets_opt["rec"]:
           self.meld_screen(_("Functions for record not activated"),"webradioFS - Info",20)
        elif ripper_installed==True:
            rd = open("/proc/cpuinfo", "r").readlines()
            for line in rd:
                if line.startswith('model name') and 'ARM' in line:
                    arm=True        
            if arm and os.path.getsize('/usr/bin/streamripper')>100000:
                 self.rs_info2("error: failed version for ARM!")
            else:
                self.check="true"
                cmd = '/usr/bin/streamripper -v'
                self.containerwbrfs_rec.execute(cmd)
        else:
            self.rs_info2()

    def rs_info2(self,vers=None):
        if self.play_stream and vers and ("error" in vers and not "ARM" in vers):
                    rs_vers="\n!! webradioFS record-error !!\n"+str(self.play_stream["name"])+"\n"+ str(vers)+"\n"
                    self.meld_screen(rs_vers,"webradioFS record-error",0,"ERROR")
        else:
            l1_versb=" >> not exist or rights not 755!"
            l2_versb=" >> not exist or rights not 755!"
            rs_vers=" >> not exist or rights not 755!"
            t1a=0
            t1b=0
            t1c=0
            t2="ERROR"
            try:
              if vers:
                if "unexpected newline" in vers:
                    rs_vers=" >> " + "installed yes, can not read version\n"+vers
                    t1a=1
                elif "error" in vers and not "newline" in vers:
                    rs_vers="\n >> "+ str(vers)
                else:
                    vers= vers.replace('Streamripper','').strip()
                    if mycmp("1.64.6",vers) <=0:
                        rs_vers=vers+" >> ok"
                        t1a=1
                    else:
                        rs_vers=vers+" >> " + "must be at least" + " 1.64.6"
            except:
                pass
            for name in os.listdir('/usr/lib'):
               fullpath=os.path.join('/usr/lib', name)
               if os.path.isfile(fullpath):   
                  try:  
                    if 'libvorbis.so' in name:
                       l1_vers= str(name).replace('libvorbis.so.','').strip()
                       if t1b==1:
                           if mycmp(l1_versb.replace(" >> ok",""),l1_vers) < 0:
                               l1_versb=l1_vers+" >> ok"
                       else:
                           if mycmp("0.4.2",l1_vers) <= 0:
                               l1_versb=l1_vers+" >> ok"
                               t1b=1
                           else:
                               l1_versb=l1_vers+" >> " + "must be at least" + " 0.4.2"
                    elif 'libvorbisenc.so' in name:
                       l2_vers= str(name).replace('libvorbisenc.so.','').strip()
                       if t1c==1:
                           if mycmp(l2_versb.replace(" >> ok",""),l2_vers) < 0:
                               l2_versb=l2_vers+" >> ok"
                       else:
                           if mycmp("2.0.5",l2_vers) <= 0:
                               l2_versb=l2_vers+" >> ok"
                               t1c=1
                           else:
                               l2_versb=l2_vers+" >> " + "must be at least" + " 2.0.5" 
                  except Exception as e:
                      continue
            sr_vers_text= _("required modules for records")+"\n\n/usr/lib/libvorbis: "+l1_versb+"\n/usr/lib/libvorbisenc: "+l2_versb+"\n"+"/usr/bin/Streamripper: "+rs_vers
            if t1a+t1b+t1c==3:
                t2="INFO"
            self.meld_screen(sr_vers_text,"webradioFS Module-Info",0,t2)
#############################################################################
    def check_cache(self):
      if self.cache_list != None: 
       root=self.check_root_rec()
       free = 0
       s = os.statvfs(self.rec_path)
       free = (s.f_bavail * s.f_bsize) / 1048576 
       if free <20:
                    self.rec_stopcache()
                    self.meld_screen(_('Stopped caching, free menory in your cache-path < 20 MB'),"Info",0,"ERROR") 
       elif root:
             self.rec_stopcache()
             self.meld_screen(_('Stopped caching, Error in system-modul GStreamer')+"\n"+_("show for update on your image"),"Info",0,"ERROR")
       elif self.cache_list != None:
              global l4l_info 
              found=None
              if self.rec_path and os.path.exists(self.rec_path):
                canz=int(self.play_stream["cache"]) #3
                if int(self.play_stream["cache"])>0:canz=int(sets_rec["caching"])
                song_liste=[]
                pic_liste=[]
                search_path=self.rec_path
                if not search_path.endswith("/"):search_path=search_path+"/"
                if os.path.exists(search_path+"incomplete"):
                   inc_list=[]
                   for name in os.listdir(search_path+"incomplete/"):
                             fullpath = search_path+"incomplete/"+name
                             if len(self.cache_list)>6 and self.cache_list == name:
                                found=1
                             dtime=os.path.getmtime(fullpath)
                             if time.time()-20>dtime:
                                os.unlink(fullpath) 
                             else:    
                                 inc_list.append((dtime,fullpath))
                for name in os.listdir(self.rec_path):
                   try:   
                      fullpath = self.rec_path+name
                      if name.startswith(" - ."):
                           os.unlink(fullpath)
                      elif not os.path.isdir(fullpath): 
                          if len(self.cache_list)>6:
                               if self.cache_list == name:
                                    copyfile(fullpath, sets_rec["path"]+name)
                                    os.unlink(fullpath)
                               elif len(self.cache_list)>6 and self.cache_list == name.replace(" (1)",""):
                                    copyfile(fullpath, sets_rec["path"]+name)
                                    os.unlink(fullpath)
                          else:
                              if canz==1:
                                  if os.path.exists(fullpath):os.unlink(fullpath)
                              elif canz>1:
                                if os.path.exists(fullpath):  
                                  dtime=os.path.getmtime(fullpath)
                                  if not name.endswith(".jpg"):
                                     song_liste.append((dtime,fullpath,name))
                   except Exception as e:
                                  if write_debug: 
                                      d=debug("source:"+str(fullpath)+"\n"+"dest:"+str(sets_rec["path"]+name)+"\n"+str(e))
                                  self.rec_stopcache()
                                  self.meld_screen(('Stopped caching, error-text in /var/webradioFS_debug.log'),"Info",0,"ERROR")
                if not found:
                                    if len(self.cache_list)>6: self.cache_list="1"
                                    self["rec_pic"].show()
                                    recp = resolveFilename(SCOPE_CURRENT_SKIN, "/usr/lib/enigma2/python/Plugins/Extensions/webradioFS/skin/images/rc1.png")
                                    self["rec_pic"].instance.setPixmap(LoadPixmap(recp))
                                    self.set_rec_text(_("press record for save a title"),"cache")
                                    l4l_info["rec"]=int(sets_rec["caching"])+1
                                    l4l_set.set_l4l_info(l4l_info)
                danz= len(song_liste)
                if danz:
                  if danz > canz+1:
                    self.rec_stopcache()
                    txt=_("Stopped caching, can not delete files in the cache directory")
                    if write_debug: d=debug(txt)
                    self.meld_screen(txt,"Info",30,"ERROR")
                  else:
                    song_liste.sort(key=lambda x: x[0])
                    while len(song_liste) >canz:
                         try:
                             os.unlink(song_liste[0][1])
                             if os.path.isfile(song_liste[0][1].replace(".mp3",".jpg")): os.unlink(song_liste[0][1].replace(".mp3",".jpg"))
                         except:
                             continue
                         del song_liste[0]
              self.cache_timer.startLongTimer(10)
              if self.cache_list and len(self.cache_list)<6:
                if self.record:
                  self["rec_pic"].show()
                  recp = resolveFilename(SCOPE_CURRENT_SKIN, "/usr/lib/enigma2/python/Plugins/Extensions/webradioFS/skin/images/rc1.png")
                  self["rec_pic"].instance.setPixmap(LoadPixmap(recp))
                  self.set_rec_text(_("press record for save a title"),"cache")
                  l4l_info["rec"]=int(sets_rec["caching"])+1
                  l4l_set.set_l4l_info(l4l_info)
                else:                
                   self["rec_pic"].hide()
                   self.set_rec_text(_("start caching..."),"default")
       else:
              self.cache_timer.startLongTimer(60)
              self["rec_pic"].hide()
              self.set_rec_text(_("no recording is in progress or timer planned"),"default")

    def check_root_rec(self,del1=None):
        if not self.root_rec:
            f=open("/var/webradioFS_debug.log","a")
            try:
                self.root_rec="1"
                root_rec=None
                for root, dirs, files in os.walk('/home/root/'):
                    for name in dirs:
                        if name =="incomplete":
                            self.root_rec=root
                            root_rec=1
                            f.write("found in root: "+name+"\n")
                            break
                if root_rec and len(str(root))>11 and '/home/root/' in str(root):
                    f.write("found2 in root: "+name+"\n")
                    shutil.rmtree(r'%s' % root.replace("/incomplete",""))
                    return 1
                else:
                    return None
            except Exception as e:
                                  f.write("error on root_check\n")
                                  f.write(str(e)+"\n")
                                  self.rec_stopcache()
                                  self.meld_screen(('Stopped caching, error-text in /var/webradioFS_debug.log'),"Info",0,"ERROR")
            f.close()

    def __evUpdatedInfo(self):
       if Screens.Standby.inStandby:
           self.exit(True,1)
       elif self.display_art !="liste" and onwbrScreenSaver == None and onwbrInfoScreen== None and (streamplayer.is_playing or satradio) and self.play_stream["typ"]!="file" or self.configfile2[1] >29: # and self.configfile2[1] <30:	
           remaining=""
           if not satradio:
              self.new_event()
           else:
              self.no_cover1()

    def __serviceStarted(self):
        pass
    def RadioText(self):
        self.new_event("radiotext")
    def RTPText(self):
        self.new_event("rtptext")

    def new_event(self,remaining=""):
        global l4l_info
        if self.display_art !="liste" and onwbrScreenSaver == None:
            if self.configfile2[1] ==0 or self.configfile2[1] >29:
                currPlay = self.session.nav.getCurrentService()
                sTitle=""
                mcover=None
                sender=self.streamname
                typ1=None
                alt_st=l4l_info["Station"]    
                if self.play_stream and currPlay is not None:
                        sTitle = ""
                        ersatz= sender
                        if satradio:
                            if remaining=="radiotext":
                                typ1="pvr1"
                            elif remaining=="rtptext":
                                typ1="pvr2"
                        elif self.play_stream["genre"]=="wbrfsfiles":
                            mlen=0
                            typ1="file"
                            sender=""
                            tags=None
                            from .wbrfs_funct import tag_read
                            tags= tag_read().read_tags(self.play_stream["url"],mcover)
                            if tags:
                              if tags[6]:
                                 mlen=str(tags[6])
                              else:
                                try:
                                  sref = self.session.nav.getCurrentlyPlayingServiceReference()
                                  if sref and sref.toString().startswith("4097:"):
                                      service = self.session.nav.getCurrentService()
                                      seek = service and service.seek()
                                      if seek:
                                        len1 = seek.getLength()
                                        duration = len1[1]/90000
                                        mlen = "%d:%02d" % (duration/60,duration%60)
                                except:
                                  pass
                              if tags[0] and tags[0] != None and tags[0] != "None":
                                      mcover=tags[0]
                              if tags[2] != "n/a" and tags[1] != "n/a": 
                                  sTitle= tags[2]+": "+tags[1]
                              else:  
                                  sTitle=self.play_stream["name"] 
                            self.sets["bitrat_text"]= str(mlen)
                            if self.aktstop==0:right_site.new_set(self.sets)
                            l4l_info={"Station":self.play_stream["url"],"Fav":self.anzeige_fav,"Bitrate":self.sets["bitrat_text"],"Genres":"wbrfsfiles","Logo":"","rec":0,"akt_txt":self.play_stream["name"],"art":self.play_stream["typ"],"Len":mlen}  #play1[2]
                            l4l_set.set_l4l_info(l4l_info)
                        else:
                            typ1="stream"
                        if typ1 and typ1 !="file": 
                            sTitle = grab_text(self,typ1,ersatz)
                        if sTitle is None or not len(sTitle):
                            sTitle==ersatz
                        cover_save["titel"]=sTitle
                        if sTitle:sTitle=sTitle.strip()
                        if  self.db_err==2:
                           sTitle = self.db_meld
                        if sTitle and len(sTitle):  
                          l4l_info["akt_txt"]=sTitle
                          l4l_set.set_l4l_info(l4l_info)
                          if self.playlist2 and mcover:
                              if alt_st != l4l_info["Station"]: 
                                  pic_show(None,mcover)
                                  mcover=None
                          elif self.playlist2 and int(self.play_stream["picon"])>0:
                               pic_show()
                          else:
                               grab(sender,sTitle)
                          self.stream_info=sTitle
                          self.selectionChanged()
                        self.x()
                else:
                    sTitle=_("Stopped")
            elif self.sets["fav"] == _("DB: "): 
                   self.stream_info= self.play_stream["name"]+ _(", add to fav for all functions")
                   self.selectionChanged()

    def __evAudioDecodeError(self):
                currPlay = self.session.nav.getCurrentService()
                sAudioType = currPlay.info().getInfoString(iServiceInformation.sUser+10)
                self.meld_screen(_("can't decode %s streams!") % sAudioType,"Decode-Error",20,"ERROR")
    def __evPluginError(self):
                currPlay = self.session.nav.getCurrentService()
                message = currPlay.info().getInfoString(iServiceInformation.sUser+12)
                try:
                    message=message+"\nName: "+self.play_stream["name"]+"\nStream-Url: "+self.play_stream["url"]+"\n"
                except:
                    message=message
                self.meld_screen(message,"Info",30,"ERROR")

    def aktual2(self):
      if onwbrScreenSaver == None:
        if self.configfile2[1] >29:
            if self.auto_play:  
                self.auto_zap()
            else:
                self.stop_stream()
        elif self.rec_list != True:
            stoppen=1
            if self.pcfs_run==False:
                 if sets_exp["conwait"]:
                     if self.reconnect==0:
                         stoppen=0
                         if fontlist[4]:
                             self.confail_timer_conn = self.confail_timer.timeout.connect(self.new_event)
                         else:
                             self.confail_timer.callback.append(self.new_event)
                         self.confail_timer.startLongTimer(int(sets_exp["conwait"]))
                         self.reconnect=1
                     else:
                         stoppen=1
                 if sets_exp["reconnect"] and stoppen==1:
                     if self.reconnect <= sets_exp["reconnect"]:
                         stoppen=0
                         if fontlist[4]:
                             self.confail_timer_conn = self.confail_timer.timeout.connect(self.ok)
                         else:
                             self.confail_timer.callback.append(self.ok)
                         self.confail_timer.start(500)
                         self.reconnect+=1
                     else:
                        stoppen=1
                 if stoppen==1:
                    self.stop_stream()
                    if self.configfile2[1]==0:
                        if int(self.play_stream["defekt"])>0:
                            self.db("Update streams SET defekt=1 WHERE stream_id=%d;" % self.play_stream["stream_id"])
                        txt=self.play_stream["name"]+"\n"+_("Station is not currently accessible") 
                        self.meld_screen(txt,"Info",20,"ERROR") 
                    elif self.configfile2[1]>29:
                        pass 
                    else:
                        self.meld_screen("The resource requested is currently unavailable","Info",20,"ERROR")

    def no_cover1(self,result=None):
            if self.aktstop==0:right_site.new_Bild(9)

    def x(self):
        currPlay = self.session.nav.getCurrentService()
        if self["streamlist"].getCurrent() and self.stream_url:
          if currPlay and len(self["streamlist"].getCurrent()[0])>2:
            if self.configfile2[1]==0 and self.fav_name==self.configfile2[0]:
                if self.stream_wechsel==1:
                    if currPlay is not None:
                        stitle = currPlay.info().getInfoString(iServiceInformation.sTagTitle)
                    sAudioType = currPlay.info().getInfoString(iServiceInformation.sTagAudioCodec)
                    tst=sAudioType+stitle
                    if tst and tst !="" and self.typ_failed ==0:   
                        url = self.play_stream["url"] 
                        nam1 = self.play_stream["name"] 
                        if self.upadate_taste: self.upadate_taste.setText(_("Stream Actions"))
                        self.red="play_ok"
                        self.stream_wechsel=0
                        if self.play_stream["defekt"] >0:
                          try:
                            self.db("Update streams SET defekt=0 WHERE stream_id=%d;" % self.play_stream["stream_id"])
                            self.read_new()
                          except:
                            pass
          elif streamplayer.is_playing and self.errorzaehler<len(self.stream_urls)+1: 
                self.red="play_false"
                try:
                    self.stream_info= _("trying to establish connection") +" (" + str(self.errorzaehler)+" "+_("of")+" "+str(len(self.stream_urls))+")"
                    self.errorzaehler+=1
                    self.ok(None,self.errorzaehler)
                except:
                   self.favoriten()
          else:
                self.check_defekt()

    def red_button(self):
      self.ResetwbrScreenSaverTimer()
      self.m_back=None
      if self.e_help !="off":
          self.botton_on_off()
      if self.red=="start" and self["streamlist"]:
          try:
             if len(self["streamlist"].getCurrent()[0])>6 and self["streamlist"].getCurrent()[0][7]=='radio':
                  self.showStreamMenu(0)      
          except:
            pass
      elif self.rec_list:
          self.del_rec()
      elif self.meldung1:
            self.meldung_back(0)
      elif self.tv1 or self.video:
         pass
      elif self.red=="play_all":
           if self.configfile2[1]==31 or self.configfile2[1]>89:
               self.favoriten()
               self["key_red2"].setText(_("Playlist"))
           else:
               list=((_("Add files (selected folder) to tmp-list"),1),(_("Add files (selected folder+subfolder) to tmp-list"),2),
                    (_("Open Playlist Temp"),3),(_("Open Playlist 1"),4),(_("Open Playlist 2"),5),(_("Open Playlist 3"),6),(_("Open Playlist 4"),7),(_("Open Playlist 5"),8),(_("Clear Playlist Temp"),9))
               right_site.hide()
               self.session.openWithCallback(self.sel_playlist, ChoiceBox, title=_("Playlist menu"), list=list)
      elif self.red=="edit":
            self.edit()
      elif self.red=="del_group":
            self.groups_men()
      elif self.red=="no":
          if len(self["streamlist"].getCurrent()[0])>6 and self["streamlist"].getCurrent()[0][7]=='radio':
                  self.showStreamMenu(0)
          else:
              if self.display_art=="liste":
                  self.exit_a()
      elif self.red=="ex":
            self.exit_a()
      else: 
          if self.display_art=="liste":
              if len(self["streamlist"].getCurrent()[0])>6 and self["streamlist"].getCurrent()[0][7]=='radio':
                  self.showStreamMenu(0)
              else:
                  self.exit_a()
          elif len(self["streamlist"].getCurrent()[0])>3 and int(self["streamlist"].getCurrent()[0][3]) >0:
               self.aktual("aktual")
          elif self.configfile2[1]==0:
                  self.showStreamMenu(0)

    def sel_playlist(self,ret=None):
        right_site.show()
        if ret and ret is not False:
            ret=ret[1]-1
            if ret==0 or ret==1:
               if self["streamlist"].getCurrent()[0][7].startswith("Dir"):
                  dir1=str(self["streamlist"].getCurrent()[0][1])
               else:
                  dir1= self.configfile2[5]
               if ret==0:
                   listnew=file_list2([dir1],"all","playlist").Dateiliste
               else:
                   listnew=file_list2([dir1],None,"playlist").Dateiliste
               if len(listnew):
                   mfile="/tmp/wbrfs_playlist"
                   self.fav_stream_list=listnew
                   self.sets["fav_text"]=_("Playlist")
                   self.setTitle("webradioFS: "+_("Playlist"))
                   self.fav_stream_list=listnew
                   f2=open(mfile,"r")
                   einles = f2.readlines()
                   if len(einles): 
                      if len(einles[-1].strip()):
                        l_add="\n"
                      else:
                        l_add="#EXTM3U\n"
                   f2.close()
                   f2=open(mfile,"a")
                   for x in listnew:
                       if x[7]== "Files" and not x[0].endswith(".m3u"):
                           f2.write("#EXTINF:-1,"+x[0]+"\n"+x[1]+"\n")
                   f2.close()
                   self.web_if_listplay((0,mfile))
               else:
                   self.ok()
            elif ret==8:
               f2=open("/tmp/wbrfs_playlist","w+")
               f2.close()
            else:
               num=ret-1
               if num==0:
                     mfile="/tmp/wbrfs_playlist" 
               else:
                         mfile=mfile="/etc/ConfFS/playlist"+str(num)+".m3u"
               self.web_if_listplay((num,mfile))

    def start_volume(self,vol=0):
            if vol != 0: self.volctrl.setVolume(int(vol),int(vol))

    def starters(self):
       self.onLayoutFinish.remove(self.starters)
       self.listbgr="#000000"
       if skin_bcr:
            self.listbgr=skin_bcr
       sc = AVSwitch().getFramebufferScale()
       h1=70
       w1=120
       try:
           h1=self["dummy"].instance.size().height()
           w1=int(round((h1*3.2)+0.5))
       except:
           pass
       self.listparas=(w1, h1, sc[0], sc[1], False, 1, self.listbgr)
       self.set_rec_text(_("no recording is in progress or timer planned"),"default")
       self.instance.setZPosition(1)
       try:self["streamlist"].setZPosition(2)
       except:pass
       self.fav_index=0
       if len(self.favoritenlist) :
            right_site.new_set(self.sets)
            global l4l_info
            l4l_info["Fav"]=self.fav_name
            l4l_set.set_l4l_info(l4l_info)
            self.favoriten()
            right_site.show()
            self.fav_name= self.favoritenlist[0][0]
            self.sets["fav_text"]= self.fav_name
            if self.startart==-2:
               for x in self.favoritenlist:
                    if x[1]==30:
                        self.fav_index=self.favoritenlist.index(x)
                        self.favoriten()
            else:
             nstrs=str(self.startstream).split(",")
             strsart="fav"
             stsi=0
             err=None
             if len(nstrs)==1:
                  try:
                      if str(nstrs[0])!="0":
                          stsi=int(nstrs[0])
                          strsart="web"
                  except Exception as e:
                      err=e
             else:
                  try:
                       if str(nstrs[1])!="0":stsi=int(nstrs[1])
                       strsart=str(nstrs[0])
                  except Exception as e:
                      err=e
             if err:
               f=open("/tmp/webradioFS_debug.log","a")
               f.write(str(err)+"\n")
               f.close()
             if strsart=="fav":
                 self.fav_index=stsi
                 self.favoriten()
             elif strsart=="pvr1":
                for x in self.favoritenlist:
                  if x[0]=="PVR-Radio Favoriten":
                    self.fav_index=self.favoritenlist.index(x)
                    self.pvrstartstream=stsi+1 
             elif strsart=="pvr0":
                for x in self.favoritenlist:
                  if x[0]=="PVR-Radio all":
                    self.fav_index=self.favoritenlist.index(x)
                    self.pvrstartstream=stsi+1
             else: 
              if stsi>0 :
                    for x in self.favoritenlist:
                        if x[1]==0:
                           for x2 in x[2]:
                             if int(x2[2]) == stsi:
                               self.fav_index=self.favoritenlist.index(x)
                               self.fav_stream=x2
                               break
             try:
                 if self.fav_stream or self.pvrstartstream:
                        self.favoriten()
                        if self["streamlist"].getCurrent():
                            
                            self.ok()
             except:
                    fehler = (_("Failed to start automatically" ))
                    self["playtext"].setText(_("Startstream-Error"))
       if len(self.configfile2[2])<1:
           for x in self.favoritenlist:
                  if x[0]=="PVR-Radio all":
                    self.fav_index=self.favoritenlist.index(x)
                    self.favoriten()  
############################################################################
    def favoriten(self,wechsel=None):
       if not len(self.favoritenlist):
          self.Favoriten_einles()
       else:
         if not self.fav_index: self.fav_index=0
         self.sets["file"]=False
         self.rec_list = False
         if self.fav_index > 0:
             if self.fav_index > len(self.favoritenlist)-1: self.fav_index=0
         self.configfile2=self.favoritenlist[self.fav_index]
         self.toggel_screen()
         art=int(self.configfile2[1])
         self.fav_name= self.configfile2[0]
         self.set_rec_text(self.fav_name,"titel")
         if self.chill_taste: self.chill_taste.setText(_("Save stream"))
         if self.upadate_taste: self.upadate_taste.setText("")    
         next_menu=None
         global web_liste_favs
         if art==0 or art==1 or art>29 or admin:
            try:
                web_liste_favs[0]=self.fav_name
            except:
                web_liste_favs[0]=_("No group selected")
         else:
            web_liste_favs[0]=_("No group selected")
         if art==1 and self.blaue_taste: self.blaue_taste.setText(_("Add to fav"))
         if art==0 or art==8:
            self.red="start"
            self.fav_list=None
            if self.blaue_taste: self.blaue_taste.setText(_("Edit"))
            self.list_titel=_("Favoriten: ") + self.fav_name
            if self.chill_taste: self.chill_taste.setText(_("Chillen"))
            self.alt_conf=self.configfile2
         if self.chill_taste and  art==1:
             self.chill_taste.setText(_("Chillen"))
         elif art >1:
            if art in (10,11,12,21,22):
                self.fav_name= self.configfile2[0]
                if self.blaue_taste: 
                     self.blaue_taste.setText(_("Info"))
                if self.upadate_taste:
                    self.red="ex"
            elif art ==7:
                if self.blaue_taste: self.blaue_taste.setText(_("Genres"))
            else:
                if self.blaue_taste: self.blaue_taste.setText(_("Info"))
                self.set_rec_text(self.fav_name,"titel")
         self.list_titel=self.fav_name
         self.fav_stream_list=self.configfile2[2]
         listnew=self.configfile2[2]
         if art in (3,4,5,7,8):
              listnew.sort(key=lambda x: x[0].lower())
         elif art >89:
                  num=art-90
                  self.title2=_("Playlist")+" "+str(num)
                  self.setTitle(_("Playlist")+" "+str(num))
                  self.streamname = "Playlist"+" "+str(num)
                  self.sets["file"]=True
                  listnew=[]
                  if num==0:
                     mfile="/tmp/wbrfs_playlist" 
                  else:
                     mfile="/etc/ConfFS/playlist"+str(num)+".txt"
                  liste=playlist_read(mfile)
                  if len(liste):
                    for x in liste:
                          listnew.append((x[1],x[2],x[3],0,90+num,0,0,"Files"))
                  if len(listnew):
                       self.fav_stream_list=listnew
                       self.configfile2=(_("Playlist")+" "+str(num),90+num,listnew,u_dir,a_sort,self.configfile2[5])
                       if self.blaue_taste:self.blaue_taste.setText(_("Settings"))
                       if self.chill_taste:self.chill_taste.setText(_("Autoplay"))
                       self.red="play_all"
                       self["key_red2"].setText(_("Playlist"))
                       wechsel=None
         elif art >29:
                  listnew=file_list2([self.configfile2[2]],None).Dateiliste
                  if len(listnew):
                       self.title2=_("My files")
                       self.setTitle(_("My files"))
                       self.streamname = _("My files")
                       self.sets["file"]=True
                       self.fav_stream_list=listnew
                       self.configfile2=(_("My files"),30,listnew,u_dir,a_sort,self.configfile2[2])
                       if self.blaue_taste:self.blaue_taste.setText(_("Settings"))
                       if self.chill_taste:self.chill_taste.setText(_("Autoplay"))
                       self.red="play_all"
                       self["key_red2"].setText(_("Playlist"))
                       wechsel=None
                       if self.auto_play: self.auto_zap()
         elif art not in (2,6,22) and art != 6 and self.streamname != "records" and self.streamname != "favs":
              if sets_grund["stream_sort"]==1:
                   listnew.sort(key=lambda x: x[0].lower())
              elif sets_grund["stream_sort"]==2:
                    listnew.sort(key=lambda x: (x[5],x[0].lower()))
         global web_liste_streams 
         web_liste_streams=()
         if art==0 or art==1 or art>29:
             web_liste_streams = listnew 
         self.set_streamlist(listnew,l4l_info["Station"],None,0)
         if art==0 and not len(listnew):
               if self.blaue_taste:self.blaue_taste.setText(_("Add new"))
         try:
             if self.configfile2[1]==0 and not streamplayer.is_playing:
                 self.title2= self.configfile2[0]
         except:
             pass
         self.setTitle(self.configfile2[0])
         right_site.new_set(self.sets)
         self.toggel_screen()
         self.showConfigDone(menu=next_menu)
         if self.fav_list:
            self.fav_list=None
         if wechsel=="admin":
             self.admin_menu()
         if not wechsel:
             self.sel_Wechsel()

    def sel_Wechsel(self):
           index=0
           if self.configfile2[1]==0 and self.fav_stream:
               if self.fav_stream in self.fav_stream_list:
                   index=self.fav_stream_list.index(self.fav_stream)
                   self.indexer=index   
                   self["streamlist"].setIndex(index)
           self.setTitle(self.title2)
           self.streamvor=" "
           self.streamnach=" "
           if self["streamlist"].getCurrent() and self["streamlist"].getCurrent()[0][1] != "def":
               self.setTitle(self["streamlist"].getCurrent()[0][0]+"  ("+self.configfile2[0]+")")
               self.stream_info= self["streamlist"].getCurrent()[0][0]
               idx=index
               if idx != 0:
                   self.streamvor= self.fav_stream_list[idx-1][0]
               if idx+1 < len(self.fav_stream_list):
                   self.streamnach= self.fav_stream_list[idx+1][0]
               if self.display_art!="info":
                   self.display_art="liste"
                   self.selectionChanged() 
               self.display_timer.start(15000)

    def Favoriten_einles(self):
      stream_liste=[]
      if not os.path.exists(myfav_file) or os.path.getsize(myfav_file)<200:
          if not self.new_imp:
               self.new_imp=1
               from .wbrfs_funct import fav_import
               zahl=fav_import().imp2()
               self.read_new()
      else:
            stream_liste= self.getStreams(0)
            ext_list=[]
            self.favoritenlist=[]
            nums=[]
            list2=[]
            for x in fav_groups:
                if x[0] not in nums:
                    nums.append(x[0])
            for x in fav_groups:
               list3=[]
               if stream_liste and len(stream_liste):
                for x2 in stream_liste:
                   if x2[1] in nums:
                       if x2[1]==x[0]:
                           list3.append(x2)
                   else:
                           list3.append(x2)
               self.favoritenlist.append((x[1],0,list3))
            if len(list2):self.favoritenlist.append((_("not assigned"),0,list2))
            self.favoritenlist.sort(key=lambda x: x[0].lower())
            if sets_opt["audiofiles"]:
              self.favoritenlist.append((_("My files"),30,sets_audiofiles["audiopath"],False,a_sort,sets_audiofiles["audiopath"]))
              self.my_fav_list2= self.favoritenlist
            favs=[] 
            for x in ext_list:
               favs.append(x[0])
            if "m3u-Streams" not in favs:
              m3u_list=[]
              if os.path.exists('/etc/ConfFS/m3u'):
                 for x in os.listdir('/etc/ConfFS/m3u'):
                   if x.endswith(".m3u"):
                       f2=open('/etc/ConfFS/m3u/'+x)
                       f2.readlines
                       for x2 in f2:
                           if "http:" in x2:
                               type="mp3"
                               if "pls" in x2: type="pls"
                               m3u_list.append((x.replace(".m3u",""),0,0,0,1,"",x2.strip(),type,"",128,'m3u',"nn",0,"unknown",0,'m3u',0))
                       f2.close()
              if len(m3u_list): 
                m3u_list.sort(key=lambda x: x[0].lower())
                ext_list.append(("m3u-Streams",1,m3u_list))
            if _("PVR-Radio Favoriten") not in favs:
              satlist=[]
              s_type = service_types_radio
              s_type2 = "userbouquet.favourites.radio"
              serviceHandler = eServiceCenter.getInstance()
              services = serviceHandler.list(eServiceReference('%s FROM BOUQUET "%s" ORDER BY name'%(s_type, s_type2)))
              idbouquet = '%s ORDER BY name'%(s_type)
              channels = services and services.getContent("SN", True)
              for channel in channels:
                        name = channel[1].replace('\xc2\x86', '').replace('\xc2\x87', '')
                        ref= quote(channel[0], safe=' ~@%#$&()*!+=:;,.?/\'')
                        satlist.append((name,0,0,0,1,"",ref,"pvr","",0,"pvr","nn",0,"unknown",0,'pvr',0))

              if len(satlist):
                ext_list.append((_("PVR-Radio Favoriten"),1,satlist))
            if _("PVR-Radio all") not in favs:            
              satlist2=[]
              s_type = service_types_radio
              s_type2 = "bouquets.radio"
              idbouquet = '%s ORDER BY name'%(s_type)
              serviceHandler = eServiceCenter.getInstance()
              services = serviceHandler.list(eServiceReference(idbouquet))
              channels = services and services.getContent("SN", True)
              for channel in channels:
                        name = channel[1].replace('\xc2\x86', '').replace('\xc2\x87', '')
                        ref= quote(channel[0], safe=' ~@%#$&()*!+=:;,.?/\'')
                        satlist2.append((name,0,0,0,1,"",ref,"pvr","",0,"pvr","nn",0,"unknown",0,'pvr',0))

              if len(satlist2):
                ext_list.append((_("PVR-Radio all"),1,satlist2))
            ext_list.sort(key=lambda x: x[0].lower())
            self.favoritenlist.extend(ext_list)
            
            global web_liste_favs
            web_liste_favs=[]
            #if alle: self.favoritenlist.append(alle)
            web_liste_favs.append(_("No group selected"))
            for x in self.favoritenlist:
                    if x[1]==0 or x[1]==1 or x[1]>29:
                       web_liste_favs.append(x[0])
            web_liste_favs.insert(0,_("No group selected"))
            if not self.configfile2: self.fav_index=0

    def Favoriten_Wechsel(self):  #button yellow
      if not self.tv1 and not self.video and self.display_art!="info": # and not self.rec_list:
        self.wbrScreenSaver_stop()
        if self.configfile2[1]==0:
            try:
                self.alt_fav_index=self.favoritenlist.index(self.configfile2)
            except:
                pass                
        elif self.configfile2[1]==7:
             try:
                 self.allstreams_index=self["streamlist"].getIndex()
             except:
                 pass

        if self.blaue_taste: self.blaue_taste.setText("")
        self.fav_list=1 
        self.set_rec_text(_("My Favorites and database"),"titel")
        self["key_red"].hide()
        self["key_red2"].show()
        self.red="no"
        self["key_red2"].setText("")
        if self.chill_taste: self.chill_taste.setText("")
        if self.favoritenlist[0][1]==0:
             self["key_red2"].setText(_("Group tools"))
             self.red="del_group"
        self.fav_stream_list=self.favoritenlist
        self.display_art="liste"
        self.fav_list=1
        self.selectionChanged()
        self.set_streamlist(self.favoritenlist,"favs",None,0)
        
    def toggel_screen(self):
      if self.display_art!="info":  
        if not self.fav_list and int(self.configfile2[1])==0:
            if self.alt_art:self.set_rec_text(self.alt_art)
            self["key_red"].show()
            self["key_red2"].hide()
        elif not self.fav_list:
            self["key_red"].hide()
            self["key_red2"].show()

    def Favoriten_Wechsel2(self,result):
        if result and result != None:
            try:
                self.fav_index=self.favoritenlist.index(result)
            except:
                self.fav_index=0

            self.favoriten()    
            self.set_rec_text(result[0],"titel")
            global l4l_info
            l4l_info["liste"]=result[0]
            l4l_set.set_l4l_info(l4l_info)

        else:
            self.favoriten()

        self.toggel_screen()
        self.ResetwbrScreenSaverTimer()

    def Favoriten_vor(self):
        if self.tv1:self.live_tv()
        self.ResetwbrScreenSaverTimer()
        if len(self.favoritenlist) > 1:
             if self.fav_index < len(self.favoritenlist)-1 and self.fav_index < len(fav_groups)-1: 
                 self.fav_index=self.fav_index+1
             else:
                 self.fav_index=0
             self.favoriten()
             self.selectionChanged()
    def Favoriten_rueck(self):
        if self.tv1:self.live_tv()
        self.ResetwbrScreenSaverTimer()
        if len(self.favoritenlist) > 1:
             if self.fav_index > 0 and self.fav_index < len(fav_groups)-1: 
                 self.fav_index=self.fav_index-1
             else:
                 self.fav_index=len(fav_groups)-1
             self.favoriten()
             self.selectionChanged()    
    def Favoriten_is_genre(self,num):
         if num == 1:
            self.Favoriten_vor()
         elif num == 2:
            self.Favoriten_rueck()

    def play_sets(self,answer =True):
        right_site.show()
        self.sets["subdirs"]=subdirs_pic
        self.sets["random"]=random_pic
        right_site.new_set(self.sets)
        self.showConfigDone()

    def edit(self,answer =True):
       if self.configfile2[1] ==10:
          if self["streamlist"].getCurrent() is not None:
             selectedStream = self["streamlist"].getCurrent()[0]
             id1 = selectedStream[2]
       
             if len(self.configfile2[2])<2:
                self.del_fav_eintrag(10)
                self.read_new()
                self.admin_menu()
             else:
                 ind=self.configfile2[2].index(selectedStream)
                 del self.configfile2[2][ind]
                 self.favoriten(1) 
       elif self.configfile2[1]==1:
                   self.ok()
                   self.streamToFav()
       elif int(self.configfile2[1]) in (8,11,12,21,22):
                    self.title2="Info"
                    play=1
                    self.showInfo(play,self["streamlist"].getCurrent()[0][2])
       elif not len(self.configfile2[2]):
               self.new()
       elif self.configfile2[1]>29:
            right_site.hide()
            self.wbrScreenSaver_stop()
            self.session.openWithCallback(self.play_sets,play_settings)
       elif answer == True and not self.tv1 and not self.fav_list and not self.video and self.display_art!="info" and not self.rec_list:
           if self["streamlist"].getCurrent():# and self.configfile2[1] != 7: 
               play=0
               if streamplayer.is_playing and self.play_stream["name"] == self["streamlist"].getCurrent()[0][0]:
                   play=1

               if self.configfile2[1]==0: # and self.play_stream:
                   selectedStream = self["streamlist"].getCurrent()[0]
                   if selectedStream[0] != _("no stream exist, read from database (yellow)"):   
                      if self.wbrScreenSaverTimer.isActive():
                           self.wbrScreenSaverTimer.stop()
                      if isinstance(selectedStream, list) or isinstance(selectedStream, tuple):
                                                  self.aktstop=1
                                                  self.session.openWithCallback(self.read_new, Fav_edit_13,selectedStream[2],0)
               else:
                    self.title2="Info"
                    self.showInfo(play,self["streamlist"].getCurrent()[0][2])

    def streamToFav(self,ignore=None):
        stream=None
        if self["streamlist"].getCurrent() is not None and self["streamlist"].getCurrent()[0] is not None: # and (self.play_stream or "zeitweise" in self.play_stream  or int(self.configfile2[1]) in (10,11,12,21,22))
            if self.play_stream and self.play_stream["name"] == self["streamlist"].getCurrent()[0][0]:
                 stream=self.play_stream
            if stream:
                self.wbrScreenSaverTimer.stop()
                nlist=[]
                if 0 < len(fav_groups)<2:                        
                        grup=fav_groups[0][0]
                        if self.connection is not None:
                            cursor = self.connection.cursor()
                            if cursor:
                              try:
                                  if stream:
                                    cursor.execute("INSERT INTO streams (name, descrip, url, typ, genre2, defekt,bitrate,genre,volume,uploader,rec,zuv,picon,group1,sscr,cache) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);" ,(stream["name"],stream["descrip"],stream["url"],stream["typ"],stream["genre2"],0,int(stream["bitrate"]),stream["genre"],stream["volume"],stream["uploader"],int(stream["rec"]),stream["zuv"],int(stream["picon"]),grup,stream["sscr"],0))
                              except:
                                    self.meld_screen(_("Fav-File-Error! file not exist? file read-only?"),"webradioFS - Info",20,"ERROR")
                              cursor.execute("select name, group1,stream_id,defekt,sscr,pos,cache,bitrate,picon,url,typ from streams WHERE group1=1;")
                              for row in cursor:
                                  nlist.append([row[0], row[1], row[2], row[3],0, row[5],0,"radio",row[6],row[8],""])
                              self.connection.commit()
                              cursor.close()                                                                                                                                                               
                              self.meld_screen(_("Stream successfully saved"),"webradioFS - Info",5)
                              self.favoritenlist[0]=(fav_groups[0][1],0,nlist)
                else:
                        self.session.open(Fav_edit_13,stream,3)

    def new(self):
            self.wbrScreenSaver_stop()
            self.aktstop=1
            self.session.openWithCallback(self.read_new, Fav_edit_13,"",1)

    def read_g(self):
         g1_list=[]
         cursorg = self.connection.cursor()
         cursorg.execute('SELECT genre,genre2 from streams;')
         for row in cursorg:
             g1= (row[0].strip(),row[0].strip())
             g2= (row[1].strip(),row[1].strip())
             if len(row[0].strip()) and g1 not in g1_list: g1_list.append(g1)
             if len(row[1].strip()) and g2 not in g1_list: g1_list.append(g2)         
         cursorg.close()
         g1_list.sort()
         self.session.openWithCallback(self.read_g_streams, ChoiceBox, title=_('Select genre'), list=g1_list)

    def read_g_streams(self,gen=None):
       if gen and gen[0]:         
         g2_list=[]
         fav_nam=gen[0]
         cursorg = self.connection.cursor()
         cursorg.execute('select name, group1,stream_id,defekt,sscr,pos,cache,bitrate,picon,url,typ from streams WHERE genre = "%s" OR genre2 = "%s";'  %(gen[0],gen[0]))
         for row in cursorg:
                      g2_list.append([row[0], row[1], row[2], row[3],0, row[5],0,"radio",row[6],row[8],""])
         cursorg.close()
         if len(g2_list):
             for x in self.favoritenlist:
                    if x[1]==8:
                             ind=self.favoritenlist.index(x)
                             del self.favoritenlist[ind]

             bez= _("Genre: ")+fav_nam
             self.configfile2= ((bez,8,g2_list))
             if self.configfile2 not in self.favoritenlist:
                        self.favoritenlist.append(self.configfile2)
             self.list_titel=bez
             self.fav_index=self.favoritenlist.index(self.configfile2) 
             self.fav_name=bez
             self.stream_info= bez 
             if self.display_art!="info":self.selectionChanged() 
             self.display_timer.start(15000)
             self.favoriten()

    def read_new(self,neu=1):
         self.aktstop=0
         self.new_imp=None
         fav_nam=None
         self.fav_index=None
         if self.configfile2:
             if self.configfile2 in self.favoritenlist:
                  self.fav_index=self.favoritenlist.index(self.configfile2)
             fav_nam=self.configfile2[0]

             if self.configfile2[1]==0 and self.fav_index is not None:
                  nlist=[]
                  fav_nam=self.configfile2[0]
                  cursor = self.connection.cursor()
                  cursor.execute('SELECT group_id from groups WHERE group1 = "%s";'  %(fav_nam))
                  for row in cursor:
                      g_num=row[0]
                  cursor.execute("select name, group1,stream_id,defekt,sscr,pos,cache,bitrate,picon,url,typ from streams WHERE group1=1;")
                  for row in cursor:
                      nlist.append([row[0], row[1], row[2], row[3],0, row[5],0,"radio",row[6],row[8],""])
                  cursor.close()
                  if len(nlist):
                       self.favoritenlist[self.fav_index]=(fav_nam,0,nlist)

         if self.fav_index is None:self.fav_index=0
         if neu==1:   
            self.showConfigDone()
            if self.back !="genres": 
                self.Favoriten_einles()
                if fav_nam:
                  for fav in self.favoritenlist:
                    if fav[0]==fav_nam:
                        self.fav_index=self.favoritenlist.index(fav)

                if not self.fav_index:
                   self.fav_index=0
 
                self.favoriten(1)
         else:
                self.Favoriten_einles()
                if fav_nam:
                  for fav in self.favoritenlist:
                   if fav[0]==fav_nam:
                      self.fav_index=self.favoritenlist.index(fav)
                if self.fav_index:
                     self.favoriten()
                else:
                      if self.configfile2 and self.configfile2 in self.favoritenlist:
                           self.fav_index=self.favoritenlist.index(self.configfile2)
                           self.favoriten(1)
                      else:
                          self.fav_index=0
                          self.favoriten()

    def info_check(self):
       if not self.tv1 and not self.video and self.display_art!="info":
         if not self.fav_list and self["streamlist"].getCurrent() is not None and self.configfile2[1] != 7:
           if streamplayer.is_playing and self.play_stream["name"] == self["streamlist"].getCurrent()[0][0]:
             self.showInfo(1,self["streamlist"].getCurrent()[0][2])
           elif self.configfile2[1] >29:
               self.showInfo(0,self["streamlist"].getCurrent()[0][2])
           else:
             self.showInfo(0,self["streamlist"].getCurrent()[0][2])
######################################################################

    def record_ok(self,answer=None):
         if answer is None or answer is False:
             pass
         else:
            self.rec_stop_a("streamswitch")
    def playpause(self,mdir=None):
        if self.configfile2[1] > 29:
           if self.pause and self.alt_ind: 
              self.pause=None
              self.auto_play=1
              self.auto_zap(self.alt_ind+1)
           elif self.alt_ind and self.auto_play==1:
                  self.auto_play=0
                  self.pause=True
                  self.session.nav.stopService()
                  self.set_streamlist(self.configfile2[2],"stopped",None,self.alt_ind)
           else:
                    self.ok(None,None,auto=1)

    def ok(self,ret=None,errversuch=None,auto=None):
      global sets_audiofiles
      global l4l_info
      global web_liste_streams
      global satradio
      global streamplayer 
      global uploadinfo
      global L4LwbrFS
      if auto:
            self.auto_play=1
            self.sets["autoplay"]=auto_png_on
      meld=None
      self.display_timer.stop()
      ind=self["streamlist"].getIndex()
      try:
          self.confail_timer.stop()
          if fontlist[4]:
              self.confail_timer_conn = None
          else:
              self.confail_timer.callback.remove(self.new_event)
              self.confail_timer.callback.remove(self.ok)
          self.reconnect=0
      except:
          pass

      if not self.meldung1 and self.e_help !="off":
          pass

      elif self.sorting != None and self.configfile2[1] <30:
           self["playtext"].setText(_("Sort streams"))
           if self.sorting<0:
              self.sorting= self["streamlist"].getIndex()
              self.set_streamlist(self.configfile2[2],self["streamlist"].getCurrent()[0][0],1,self["streamlist"].getIndex())
           else:
              fav_stream_list=self.configfile2[2]
              str2=self.configfile2[2][self.sorting]
              fav_stream_list.pop(self.sorting)
              fav_stream_list.insert(ind, str2)
              alt= list(self.configfile2)
              i=0
              for x in fav_stream_list:
                x[5]=i
                i+=1
              alt[2]=fav_stream_list
              self.configfile2=alt
              self.sorting=(1-3)            
              self.set_streamlist(self.configfile2[2],None,2,self["streamlist"].getIndex())


      elif self.meldung1:
          meld=1
          self.meldung_back(2)
      elif self.configfile2[1] >29 and str(self["streamlist"].getCurrent()[0][1]).endswith(".m3u"):
               self.akt_pl_list=[]
               self.web_if_listplay((8,self["streamlist"].getCurrent()[0][1]))
        
      elif self.fav_list and self.fav_list !=2:
              self.alt_fav_index=None
              self.Favoriten_Wechsel2(self["streamlist"].getCurrent()[0])

      elif self.playlist2 and self.configfile2[1] >29 and self.configfile2[2]==self.playlist2[2] and not self["streamlist"].getCurrent()[0][7].startswith("Dir"):
             
             if self.rec_set_list["rec_art"]=="caching" and self.cache_list != None: 
                   self["rec_pic"].hide()
                   self.set_rec_text(_("no recording is in progress or timer planned"),"default")
                   self.record=None
                   self.rec_stopcache()
             if self.auto_play: 
                self.anzeige_fav=_("Playing from folder")
                ind=self["streamlist"].getIndex()
                self.auto_zap(ind)
             else:
               play1=self["streamlist"].getCurrent()[0]
               if L4LwbrFS: L4LwbrFS.delete( "wbrFS.02.pic1" )
               self.sets["file"]=True

               if not ret and not play1[7].startswith("Dir") and not self["streamlist"].getCurrent()[0][1].endswith(".m3u"):
                 if self.configfile2[0].startswith(_("Playlist")) and sets_audiofiles["audio_listpos"] == True:
                   if self.playlist_num<7:
                     self.pl_nums[self.playlist_num-1]=self.playlist2_ind
                     audio_nums = ','.join([str(i) for i in self.pl_nums]) 
                     
                     sets_audiofiles["audio_listnums"]= audio_nums
                     write_settings((("audiofiles",sets_audiofiles),))
                 name=play1[0]
                 if play1[1].endswith(".m3u"):
                      self.web_if_listplay((8,play1[1]))
                      name=play1[0]
                 else:
                   self.anzeige_fav=_("Play file")
                   self.play_file(ind)

      elif self.configfile2[1] >29:
           if self.rec_set_list["rec_art"]=="caching" and self.cache_list != None: 
                   self["rec_pic"].hide()
                   self.set_rec_text(_("no recording is in progress or timer planned"),"default")
                   self.record=None
                   self.rec_stop()
           if ret:
               path0=ret
           else:
               path0=self["streamlist"].getCurrent()[0][1]
           path1= path0.split('/')
           if L4LwbrFS: L4LwbrFS.delete( "wbrFS.02.pic1" )
           self.sets["file"]=True
           if not ret and not self["streamlist"].getCurrent()[0][7].startswith("Dir"):
               self.sets["file"]=True
               if self.auto_play:
                    self.anzeige_fav=_("Playing from folder")
                    self.auto_zap(ind)
               else:
                   self.anzeige_fav=_("Play file")
                   self.play_file(ind)
               self.ResetwbrScreenSaverTimer()

           elif ret or self["streamlist"].getCurrent()[0][7].startswith("Dir"):
                  rpath=self["streamlist"].getCurrent()[0][1]
                  if auto:
                      right_site.new_set(self.sets)
                      if self["streamlist"].getCurrent()[0][0].startswith(".."):
                          rpath=self["streamlist"].getCurrent()[0][2]
                      listnew=file_list2([rpath],u_dir).Dateiliste
                      self.akt_pl_num=0 

                      self.anzeige_fav=_("Playing from folder")+" - "+path1[-2]
                      if len(listnew)>1:
                        
                        l4l_info["Station"]=self.fav_name 
                        l4l_set.set_l4l_info(l4l_info)
                  else:
                      listnew=file_list2([rpath]).Dateiliste
                      self.fav_name=_("My files")
                  path='/'.join(path0.split('/')[:-2]) + '/'
                  if len(path1)>2:listnew.insert(0, (".." +path1[-3],path,path0,0,0,0,0,"Dir1"))
                  self.fav_stream_list=listnew
                  self.configfile2=(self.fav_name,30,listnew,u_dir,a_sort,path0)
                  self.configfile2=list(self.configfile2)
                  if not self.auto_play and not auto:self.display_art="liste"
                  self.fav_list=2
                  self.stream_info="../"+'/'.join(rpath.split('/')[-3:])
                  self.set_streamlist(self.configfile2[2],l4l_info["Station"],None,0)
                  self.anzeige_fav= self.configfile2[0]

                  if self.auto_play:
                      self.playlist2=None
                      self.auto_zap()
           if not self.playlist2 or self.configfile2[2]==self.playlist2[2]:
               self.setTitle("webradioFS: "+_("Playing from folder")+" - "+path1[-2]) 
           web_liste_streams = self.configfile2[2]

      elif self.fav_list:
          self.Favoriten_Wechsel2(self["streamlist"].getCurrent()[0])
        
      elif self.wecker==1:   #lauter werden stoppen
                self.wecker=2
                self.volume_timer.stop()
      elif self.record and self.cache_list == None :
           self.meld_screen(_("A recording is in progress or is planned, terminate recording for switch?"),"webradioFS- "+_("query"),20,"??",self.record_ok,False)
          
      elif self["streamlist"].getCurrent() is not None and len(self["streamlist"].getCurrent())>3:
        self.playlist2=None
        self.streamname=""
        self.stream_info=""
        self.display_art="normal"
        
        satradio=None
        if self.configfile2[1] != 3:
            self.red="no"
        logo=""
        genr=""
        errversuch=None
        type1=None
        self.anzeige_fav=self.fav_name
        self.fav_stream=self["streamlist"].getCurrent()[0]
        set_defekt=None
        self.stream_url=None
        self.display_timer.stop()
        #f7=open("/tmp/001","a")
        if int(self["streamlist"].getCurrent()[0][4]) in (7,8):
            pass
        else:
            
            if streamplayer.is_playing:
                streamplayer.stop()
            self.set_rec_text(_("no recording is in progress or timer planned"),"default")
            if self.fav_name==_("PVR-Radio all") or self.fav_name==_("PVR-Radio Favoriten"):
                if self.pvrstartstream!=None:
                    self["streamlist"].setIndex(self.pvrstartstream-1)
                    self.pvrstartstream=None
                self.play_stream={'sscr': 'default', 'genre2': 'Sat/Kabel/Antenne', 'zuv': 'unbekannt', 'name': self["streamlist"].getCurrent()[0][0], 'url': self["streamlist"].getCurrent()[0][6], 'bitrate': 0, 'picon': 0, 'volume': 0, 'stream_id': 3, 'group1': 1, 'uploader': 'nn', 'descrip': '', 'genre': 'PVR-Radio', 'rec': 0, 'typ': 'pvr', 'defekt': 0,'cache':0}
                if self.fav_name==_("PVR-Radio all"):
                     self.set_rec_text(_("All PVR-Stations"),"titel")
                else:
                     self.set_rec_text(_("PVR-Favorites"),"titel")
            
            elif self.fav_name.startswith("webradio-browser"):            
                 self.play_stream={'sscr': 'default', 'genre2': 'webradio-brwoser', 'zuv': 'unbekannt', 'name': self["streamlist"].getCurrent()[0][0], 'url': self["streamlist"].getCurrent()[0][11], 'bitrate': self["streamlist"].getCurrent()[0][13], 'picon': 0, 'volume': 0, 'stream_id': 3, 'group1': 1, 'uploader': 'nn', 'descrip': '', 'genre': 'imports', 'rec': 0, 'typ': self["streamlist"].getCurrent()[0][12], 'defekt': 0,'cache':0}
            else:
                self.play_stream=self.readSingleStreams(self["streamlist"].getCurrent()[0][2])
                #f7.write(str(self.play_stream)+"\n")

            if self.play_stream:
                  genr= self.play_stream["genre"].strip()
                  if len(self.play_stream["genre2"].strip()):
                     genr=genr+", "+self.play_stream["genre2"].strip()

            if self.play_stream:
                uploadinfo=None
                self["playtext"].setText(self.play_stream["name"])
                type1=self.play_stream["typ"]
                if type1=="": type="mp3"
                if type1=="pvr":
                    self.stream_urls= ((self.play_stream["url"],self.play_stream["url"]),type1,self.play_stream["url"])
                elif errversuch==None:
                    self.typ_failed=0
                    if type1 == "mms" or type1 == "wma":
                       stream_m=self.play_stream["url"]
                       self.stream_urls=((stream_m,stream_m),type1,stream_m)
                    else:
                       self.stream_urls= Streamlist().streams(self.play_stream["url"],type1,sets_exp["timeout"])
                       self.errorzaehler=0
                       #f7.write(str(self.stream_urls)+"\n")
                       if self.configfile2[1]==0:
                           if self.stream_urls:
                             if self.stream_urls[1] and type1 != self.stream_urls[1] and (type1=="pls" or type1=="m3u"):
                                self.meld_screen(_("Stream-Typ failed (not " + type1+"), Typ is: ")+self.stream_urls[1]+"\n"+_("edit setting?"),"webradioFS- "+_("query"),20,"??",self.edit,True)

                streamdef=0
                status=_("unknown error")
                if not self.stream_urls or not len(self.stream_urls):
                        self.red="play_false"
                        #f7.write("not len\n")
                        #if self.upadate_taste: self.upadate_taste.setText(_("update"))
                        self.stream_info=_("not url")
                        set_defekt=_("not url")
                        streamdef=1
                elif self.stream_urls and self.stream_urls[0]==None:
                    status=str(self.stream_urls[1])
                    if not len(status):status=""
                    if self.configfile2[1]==0 and streamdef==0:
                        if str(self.play_stream["defekt"]).isdigit() and int(self.play_stream["defekt"])>0:
                            self.db("Update streams SET defekt=1 WHERE stream_id=%d;" % self.play_stream["stream_id"])
                        txt=self.play_stream["name"]+"\n"+_("Station is not currently accessible") +"\n"+status
                        self.stream_info=_("url not readable")
                        set_defekt=_("url not readable")
                        streamdef=1

                elif self.stream_urls[1]=="timeout":
                     self.stream_info=_("url timeout")
                if self.stream_urls and self.stream_urls[0] and self.errorzaehler < len(self.stream_urls[0]):
                     if self.stream_urls[0][self.errorzaehler]:
                         self.stream_url = self.stream_urls[0][self.errorzaehler]
                else:
                   set_defekt=_("url not readable")
                if not set_defekt:
                  self.akt_defekt= self.play_stream["defekt"]
                  self.stream_wechsel=1
                  self.start1=1
                  if sets_view["logos"]==True and self.configfile2[1]==0 and type1 !="pvr":
                    if os.path.isfile(os.path.join(sets_exp["logopath"],"/byName/"+self.play_stream["name"] + ".png")):
                          logo =  os.path.join(sets_exp["logopath"],"/byName/"+self.play_stream["name"] + ".png")             
                    elif self.play_stream["picon"] >0 and os.path.exists(os.path.join(sets_exp["logopath"],"/big/"+str(self.play_stream["picon"])+".png")):
                          logo=os.path.join(sets_exp["logopath"],"big/"+str(self.play_stream["picon"])+".png")                    
                    elif self.play_stream["picon"] >0 and os.path.exists(os.path.join(sets_exp["logopath"],str(self.play_stream["picon"])+".png")):
                       logo=os.path.join(sets_exp["logopath"],str(self.play_stream["picon"])+".png")
                  if int(self.play_stream["volume"]) >0:self.start_volume(self.play_stream["volume"])
                  stream_name=self.play_stream["name"]
                  if len(stream_name)>60:
                    stream_name=stream_name[0:60]+"..."
                  self.ok_start=1
                  self.sel_stream=self.play_stream["name"]
                  if self.stream_url:
                        if type1=="pvr":
                            pos = self.stream_url.rfind(':')
                            try:
                                if sets_exp["wbrfspvrpath"] and len(sets_exp["wbrfspvrpath"]) and os.path.exists(sets_exp["wbrfspvrpath"]):
                                    pngname = os.path.join(sets_exp["wbrfspvrpath"],self.stream_url[:pos].rstrip(':').replace(':','_') + ".png")
                                    if fileExists(pngname):logo=pngname
                                else:
                                    for path in ['/usr/share/enigma2/picon','/etc/picon','/media/cf/picon','/media/usb/picon']:
                                        if os.path.exists(path):
                                            pngname = os.path.join(path,self.stream_url[:pos].rstrip(':').replace(':','_') + ".png")
                                            if fileExists(pngname):
                                                logo=pngname
                                                break
                            except: 
                                pass
                            
                            sat_stream = eServiceReference(self.stream_url)
                            self.session.nav.playService(sat_stream)
                            
                            satradio=True
                        else:
                            self.pl1=streamplayer.play(self.stream_url)

                  if satradio:
                     self.sets["fav"] =_("PVR:")
                  elif self.configfile2[1]==0:
                     self.sets["fav"] =_("Group:")
                     if "cache" in self.play_stream and int(self.play_stream["cache"])>0:
                         self.rec_cache()
                  self.sets["fav_text"] =self.fav_name.replace("PVR-Radio ","").lstrip()
                  kb_zusatz=""
                  if type1 != "pvr":
                      self.sets["bitrat_text"]=str(self.play_stream["bitrate"])+" kbit/s"
                      kb_zusatz=" kbit/s"
                      s_url=base64.standard_b64encode(self.play_stream["url"].encode())
                  genr= self.play_stream["genre"].strip()
                  if len(self.play_stream["genre2"].strip()):
                     genr=genr+", "+self.play_stream["genre2"].strip()
                  self.sets["bitrat"]=_("Bitrate:")
                  self.sets["genre_text"]=genr
                  self.sets["name_text"]=stream_name
                  self.sets["typ_text"]=self.play_stream["typ"]
                  self["playtext"].setText(self.play_stream["descrip"])
                  self.streamname=self.play_stream["name"]
                  self.stream_info=self.play_stream["name"]
                  self.set_streamlist(self.configfile2[2],self.streamname,None,self["streamlist"].getIndex())
                  self.setTitle(stream_name+" - "+ self.fav_name)
                  self.title2=stream_name+" - "+ self.fav_name
                  self.stream_info= self.play_stream["name"]
                  if self.display_art!="info":
                      self.display_art="normal"
                      self.selectionChanged()
                else:
                  if self.rec_list != True:  
                    self["playtext"].setText(_("Station is not currently accessible"))
                    txt=self.play_stream["name"]+"\n"+_("Station is not currently accessible1") +"\n"+status

        logo2="" 
        if logo:
            logo2=logo
        else:
          if self.play_stream and not satradio:
             lpa=str(sets_exp["logopath"])
             if os.path.exists(lpa):
                 if os.path.isfile(os.path.join(lpa,"byName",self.play_stream["name"] + ".png")):
                       logo2 = os.path.join(lpa,"byName",self.play_stream["name"] + ".png")             
                 elif os.path.exists(os.path.join(lpa,"big",str(self.play_stream["picon"])+".png")):
                       logo2 = os.path.join(lpa,"big",str(self.play_stream["picon"])+".png")
                 elif os.path.exists(os.path.join(lpa,str(self.play_stream["picon"])+".png")):
                      logo2=lpa+str(self.play_stream["picon"])+".png"
        if self.play_stream:l4l_info={"Station":self.play_stream["name"],"Fav":self.fav_name.lstrip(),"Bitrate":str(self.play_stream["bitrate"]),"Genres":genr,"Logo":logo2,"rec":0,"akt_txt":"","art":self.sets["fav"]}
        l4l_set.set_l4l_info(l4l_info)
        if L4LwbrFS and l4ls[0]=="True" and l4ls[19]=="True":
              if self.configfile2[1] >29:
                    L4LwbrFS.delete( "wbrFS.02.pic1" )
                    if int(l4ls[28])>0:
                        L4LwbrFS.add( "wbrFS.06.txt6",{"Typ":"txt","Align":str(l4ls[20]),"Width":500,"Pos":0,"color":str(l4ls[29]),"Text":_("my records"),"Size":str(l4ls[28]),"Screen":str(l4ls[3]),"Lines":1,"Lcd":l4ls[1],"Mode":"OnMedia"} )
                    L4LwbrFS.delete( "wbrFS.05.box1" )
                    L4LwbrFS.delete( "wbrFS.06.txt5" )
                    if l4ls[2]=="True":
                        L4LwbrFS.setHoldKey(True)
                    L4LwbrFS.setScreen(l4ls[3],l4ls[1],True)    
              else:
                try:
                    L4LwbrFS.delete( "wbrFS.05.box1" )
                    L4LwbrFS.delete( "wbrFS.06.txt5" )
                    if self.play_stream and self.play_stream["genre2"] == "files":
                        L4LwbrFS.delete( "wbrFS.06.txt6" )
                        L4LwbrFS.delete( "wbrFS.02.pic1" )
                    elif logo2:
                        L4LwbrFS.delete( "wbrFS.06.txt6" )
                        L4LwbrFS.add( "wbrFS.02.pic1",{"Typ":"pic","Transp":"True","Align": str(l4ls[20]),"Pos":int(l4ls[21]),"File":logo2,"Screen":l4ls[3],"Lcd":l4ls[1],"Size":l4ls[22],"Mode":"OnMedia"} )
                    else:
                        L4LwbrFS.delete( "wbrFS.02.pic1" )
                        if l4ls and int(l4ls[28])>0 and self.play_stream:
                          txt=self.play_stream["name"]
                          L4LwbrFS.add( "wbrFS.06.txt6",{"Typ":"txt","Align":str(l4ls[20]),"Width":500,"Pos":0,"Color":str(l4ls[29]),"Text":txt,"Size":str(l4ls[28]),"Screen":str(l4ls[3]),"Lines":1,"Lcd":l4ls[1],"Mode":"OnMedia"} )
                    if l4ls and l4ls[2]=="True":
                        L4LwbrFS.setHoldKey(True)
                    L4LwbrFS.setScreen(l4ls[3],l4ls[1],True)    
                except Exception as e:
                    L4LwbrFS=None
                    self.meld_screen(_("LCD4Linux-Version not compatible")+"\n(min = 4.x)","webradioFS - Info",20,"ERROR")

      if not sets_view["logos"]:
             logo2=None
      try:
              self.sets["logo"]=logo2
      except:
              pass

      if self.aktstop==0:right_site.new_set(self.sets)
      if not meld:
          if not self.playlist2: 
              self.new_event()
              self.ondisplayFinished()
              if not self.configfile2[1] in (7,3):self.showConfigDone()
      if self.versionsalter>1:
                self.veraltet2(True)

    def meld_screen(self,text="unknwown error",titel="Error",timeout=0,type1="INFO",aktion=None,default=True):
            self.meldung1=True
            self.mtitel=titel
            self.type1=type1
            if timeout>0:
                self.meldetimeout=timeout
                titel=str(titel)
                self.meld_timer.start(1000)
            self.stream_info_alt=self.stream_info
            self.stream_info=text.split("\n")[0]
            if not "info" in self.display_art:self.selectionChanged()
            self.meldung1=True
            melde_screen.start(text,titel,aktion,default,type1,timeout,sd,fontlist)
            

    def meldung_t_back(self):
          if self.meldetimeout>1:  
              self.meldetimeout-=1
              m1=melde_screen.set_c_count(str(self.meldetimeout))
              self.meld_timer.start(1000)
          else:
              self.meldung_back()

    def meldung_back(self,answer=0):
        m1=melde_screen.stop()
        self.meldung1=None
        if self.meld_timer.isActive():self.meld_timer.stop()
        self.stream_info=self.stream_info_alt
        if not "info" in self.display_art:self.selectionChanged()
        b1=None
        if m1 and len(m1) and m1[1] != 0:
                if m1[3]=="??":
                    b1=m1[1](m1[2])
                elif m1[2] == True: 
                    b1=m1[1]()
                else:
                   pass
  
        elif self.menu_on and self.m_back != None:
               self.m_back()
        if b1: b1  


    def back_s(self,art):
        self.back=None

    def exit_a1(self,ret=None):
            self.exit_a()
 
    def exit_a(self,ret=None):
        global wbrfs_saver
        if self.e_help=="ext_help":self.botton_on_off()
        if self.meldung1:
            meld=1
            self.meldung_back()
        elif not self.configfile2 or len(self.configfile2[2])<1:
            self.exit()

        elif self.display_art=="info2":
            self.meldung_back()
        elif self.m_back:
           self.menu_back(self.m_back)
        elif self.versionsalter>1:
            self.exit()
        elif self.e_help !="off":
            self.botton_on_off()
            if self.m_back != None:self.showMainMenu()
        elif wbrfs_saver:
            try:
                self.session.deleteDialog(wbrfs_saver)
            except:
                pass
            wbrfs_saver=None
            self.screensaver_off = 0
            self.ResetwbrScreenSaverTimer()
        elif self.sorting:
           self.sortStreams2()            
        elif self.tv1:
            self.live_tv()
        elif self.video:
            self.pvideo()
        elif self.configfile2 and self.configfile2[1] and int(self.configfile2[1]) in (10,11,12,21,22):
            if self.alt_conf: self.fav_index=self.favoritenlist.index(self.alt_conf)
            self.favoriten("admin")
       
        elif (self.configfile2 and self.configfile2[1] and self.configfile2[1] !=0) or self.fav_list==2:
                        self.sets["file"]=False
                        if self.aktstop==0:right_site.new_set(self.sets)

                        if self.alt_fav_index != None:
                                        self.fav_index=self.alt_fav_index
                                        self.favoriten(1)
                        elif self.fav_list:
                             if self.alt_conf:
                                        self.Favoriten_Wechsel2(self.alt_conf)
                        else:
                                        self.Favoriten_Wechsel()

        elif self.fav_list:
                        if self.alt_conf:
                                self.Favoriten_Wechsel2(self.alt_conf)
                        else:
                            self.read_new()
                            if self.alt_art:self.set_rec_text(self.alt_art)
                            self.Favoriten_Wechsel2(None)
        elif self.back:
             self.back_s(self.back)
        elif self.record and self.cache_list != None and self.rec_set_list and self.rec_set_list["rec_art"]=="caching":
              if len(self.cache_list)>6 :
                  self.cache_list="1"
                  self.check_cache()
              else:
                  self.rec_stop_a()
                  self.exit(True)
        elif self.record and self.cache_list == None:
           self.meld_screen(_("A recording is in progress or is planned, terminate recording and stop stream?"),"webradioFS- "+_("query"),20,"??",self.rec_stop_a,True)
        elif self.rec_timer.isActive():
           self.meld_screen(_("Discard scheduled timer?"),"webradioFS- "+_("query"),20,"??",self.rec_stop_c,True)
        else:
            if self.record and self.cache_list == None:
               self.meld_screen(_("Do you really want to stop the recording?"),"webradioFS- "+_("query"),20,"??",self.exit_a,True)
            else:
               self.exit_b(True)

    def exit_b(self,answer):
         if answer is None or answer is False:
            pass
         else:
             if sets_grund["exitfrage"] and (self.configfile2 and self.configfile2[1]<2):
                self.meld_screen(_("Exit the program?"),"webradioFS- "+_("query"),10,"??",self.exit_answer,True)
             else:
                self.exit(True)
    def exit_c(self):
         self.exit(True)
    def exit_answer(self,answer):
         if answer is None or answer is False:
             pass
         else:
             self.exit(True)

    def exit(self,answer=True,all_off=None):
        global wbrfs_saver
        global l4l_info
        global web_liste_favs
        global web_liste_streams

        save_startstream=None
        if str(sets_grund["startstream1"])== "0":
            save_startstream="fav"+","+str(self.fav_index)
        if str(sets_grund["startstream1"])== "-1" and self.play_stream:
                    if self.play_stream['typ'] =="pvr":
                      if self.fav_name=="PVR-Radio all":
                          save_startstream="pvr0"+","+str(self["streamlist"].getIndex())
                      else:
                          save_startstream="pvr1"+","+str(self["streamlist"].getIndex()) 
                    else:
                       save_startstream="web"+","+str(self.play_stream['stream_id'])

        if save_startstream:
                      starter_set("write",save_startstream)
        
        if all_off or ( not self.configfile2 or self.configfile2[1]<2 or self.configfile2[1]>29):
          if all_off:
             self.exit_art=all_off
          if answer== True:
            try:
                if self.containerwbrfs_rec and self.containerwbrfs_rec.running():
                    self.containerwbrfs_rec.sendCtrlC()
            except:
                pass            
            if self.record:
                   if all_off=="standby" or all_off=="off":
                       self.exit_art = all_off
                   self.wbrfs_recClosed2("no_save")

            else:
            
              streamplayer.stop()
              streamplayer.exit()
              if self.oldService is not None: self.session.nav.playService(self.oldService)
              if self.wbrScreenSaverTimer.isActive():
                  self.wbrScreenSaverTimer.stop()
              if wbrfs_saver:
                      self.session.deleteDialog(wbrfs_saver)
                      wbrfs_saver=None

              if sispmctl: 
                if "0" in sets_sismctl["exit"] or "1" in sets_sismctl["exit"]:
                    self.sispmctl_schalt(sets_sismctl["exit"])



              try:
                   if self.tv1: self.tv1=self.session.deleteDialog(self.tv1)
              except:
                  pass
              if self.video: self.video=None

              if melde_screen: self.session.deleteDialog(melde_screen)
              
              self.display_art="info"
              
              l4l_info= {"Station":"","Fav":"","Bitrate":"","Genres":"","rec":0,"akt_txt":"","art":"Group","Logo":"","Len":0}
              try:
                  if L4LwbrFS and l4ls[0]=="True": L4LwbrFS.setScreen(0)
                  if fileExists("/tmp/l4linfo"):os.remove("/tmp/l4linfo")
              except:
                  pass
              
              web_liste_favs=[]
               
              web_liste_streams = []
              try:self.session.deleteDialog(right_site)
              except: pass

              self.close(self.session)
        else:
             self.fav_index=0
             self.read_new(1)
             if self.m_back:
                self.menu_back(self.m_back)

    def __onClose(self):
              self.blocker.stop()
              self.volume_timer.stop()
              if self.connection: self.connection.close()
              try:
                 if self.containerwbrfs_rec:  
                   self.containerwbrfs_rec.sendCtrlC()
              except:
                   pass

              if L4LwbrFS: 
                  try:
                      
                      L4LwbrFS.delete("wbrFS" )
                      L4LwbrFS.setScreen("0")
                      L4LwbrFS.setHoldKey(False)
                      if l4lR:L4LwbrFS.setRefresh()
                  except:
                      pass
              try:
                  if fileExists("/tmp/.wbrfs_pic"): os.remove("/tmp/.wbrfs_pic")
              except:
                  pass    
              varis=("myname","myversion","wbrfs_saver","versiondat","php_num","streamplayer","hashwert","manuell","online","starter_stream","startsets","sets_exp","web_liste_streams",
                  "web_liste_favs","right_site","listenbreite,box","web1","web","vumodel","imagetyp","pcfs","sispmctl","l4l_info","saver_list","L4LwbrFS","FBts_liste",
                  "tasten_name","schwarz","weiss","orange","center","left","left_wrap","streamtitel","satradio","onwbrScreenSaver","onwbrInfoScreen","ripper_installed","plugin_path",
                  "def_pic","offtimer","DWide","DHoehe","skin_ext","send_para2","uploadinfo","auto_png_off","auto_png_on"
              )

              if self.oldService is not None: self.session.nav.playService(self.oldService)
              if self.org_vol != self.volctrl.getVolume():
                  eDVBVolumecontrol.getInstance().setVolume(self.org_vol,self.org_vol)
                  if self.org_vol>0:
                       if eDVBVolumecontrol.getInstance().isMuted():
                                globalActionMap.actions["volumeMute"]()
              if self.exit_art=="standby":
                 Notifications.AddNotification(Screens.Standby.Standby)
              if self.exit_art=="off":
                 Notifications.AddNotification(Screens.Standby.TryQuitMainloop, 1)


    def stop_stream(self):
      global streamplayer
      self.stream_url=None
      self.no_cover1(1)
      if not sets_audiofiles["autoplay"]:
          self.auto_play=None
          self.sets["autoplay"]=auto_png_off
      right_site.new_set(self.sets)
      if self.rec_set_list["rec_art"]=="caching":
           self.rec_stopcache()
      elif self.record:
           self.meld_screen(_("A recording is in progress or is planned, terminate recording and stop stream?"),"webradioFS- "+_("query"),20,"??",self.rec_stop_a,True)
      elif self.configfile2[1]>29:
           self.session.nav.stopService()
           if self.fav_list !=1: 
               self.set_streamlist(self.configfile2[2],"stopped",None,self["streamlist"].getIndex())
      else:
        if self.play_stream and (self.play_stream["typ"]=="pvr" or self.play_stream["typ"]=="file"):
           self.session.nav.stopService()
        elif streamplayer.is_playing:
            streamplayer.stop()
        if self.tv1: 
            self.session.nav.playService(self.oldService)
        else:
            self.ResetwbrScreenSaverTimer()
        self.red="no"
        if self.configfile2[1]==0 and self.upadate_taste: self.upadate_taste.setText("")
        self.stream_info=_("Stopped")
        self.set_streamlist(self.configfile2[2],"stopped",None,self["streamlist"].getIndex())  #,self["streamlist"].getIndex()
        if self.display_art!="info":self.selectionChanged()
        self.sets["skin_genres"]=""
        self.sets["skin_bitrate"]=""
        self.sets["skin_typ"]=""
        self.setTitle("webradioFS")
        self.sets["stream_name"]=("stream stopped")#
        right_site.new_set(self.sets)

    def schalt1(self):
        if sispmctl: 
            if "0" in sets_sismctl["vers1"] or "1" in sets_sismctl["vers1"]:
                self.sispmctl_schalt(sets_sismctl["vers1"])

    def schalt2(self):
        if sispmctl: 
            if "0" in sets_sismctl["vers2"] or "1" in sets_sismctl["vers2"]:
                self.sispmctl_schalt(sets_sismctl["vers2"])

    def sispmctl_schalt(self,sets1=None):
        if sispmctl and sets1:
            sets=""
            sispmctl_file=open("/tmp/sispmctlext.txt","w")
            for x in sets1:
                  sets=sets+str(x)+"\n"
            sispmctl_file.write(sets)
            sispmctl_file.close() 

    def showMainMenu(self):
      if self.e_help!="on" and not self.rec_list:  
        self.m_back=None
        self.wbrScreenSaver_stop()
        menu = []
        if self["streamlist"].getCurrent() is not None:
             selectedStream = self["streamlist"].getCurrent()[0]
             self.stream_name = selectedStream[0]
        else:
             selectedStream = None
        if self.configfile2[1] >29 and selectedStream:
            menu.append((_("Delete selected file"), self.del_rec,""))
        if sispmctl and sets_opt["sispmctl"]:
           if "0" in sets_sismctl["vers1"] or "1" in sets_sismctl["vers1"]:
               menu.append((sets_sismctl["nvers1"], self.schalt1,""))
           if "0" in sets_sismctl["vers2"] or "1" in sets_sismctl["vers2"]:
               menu.append((sets_sismctl["nvers2"], self.schalt2,""))
        if admin:
             menu.append((_("admin-tools"), self.admin_menu,_("fuer administrative Aufgaben"),self.showMainMenu))
        if extplayer:
             menu.append((_("Note on text from sender/pictures"), self.showTextinfo,_("Note on text from sender/pictures"),self.showMainMenu,"all"))
        if sets_opt["expert"]==0:
             menu.append((_("Settings-basics"), self.showConfig,_("Settings-basics"),self.showMainMenu,"all"))
        else:
             menu.append((_("Settings"), self.tools,_("edit settings, backup, restore,groups,import"),self.showMainMenu))
        if sets_opt["expert"]==1:
            menu.append((_("Additional functions on / off"), self.showConfig,_("Additional functions on / off"),self.tools,"moduls"))
        if sets_opt["expert"]>0:
            menu.append((_("Tools and extras"), self.extras,_("show saved titles and pictures, Backup, restore, reset picons, show new streams")))
        elif sets_opt["expert"]<2:        
            menu.append((_("I miss functions"), self.set_all_options,_("show all options")))

        if self.configfile2 and len(self.configfile2):
          if self.configfile2[1]==0: 
            if not self.fav_list and self["streamlist"].getCurrent():
                    menu.append((_("Stream Actions"), self.showStreamMenu,_("Selected Stream copy,move,edit,new,delete"),self.showMainMenu))
        if self.configfile2[1] <30: 
             menu.append((_("Group tools"), self.groups_men,_("add, delete groups")))    # % u"\u0026"
        menu.append((_("About"), self.showAbout,_("show info for plugin and contact"),self.showMainMenu))
        if sets_opt["expert"]>0:
            menu.append((_("Actions-Menu"), self.aktions_menu,_("Standby,Deepstandby,Chillmodus,Sleeptimer"),self.showMainMenu))
        if self.configfile2[1] <30 and sets_opt["rec"]:
            menu.append((_("Record-Menu"), self.rec_menu,_("Instant recording, recording with special settings, check modules"),self.showMainMenu))
        al=1
        for x in self.favoritenlist:
                   if x[1]==7 and len(x[2]): 
                        al=None
                        break 
        self.menu_history=(1,0,0)
        self.menuStart(menu,_("mainmenu"),None)

    def extras(self):
        menu = []
        menu.append((_("Import stream-file"), self.fav_importb,_("read and import streams from *imp-file in /tmp")))
        if os.path.exists(sets_exp["coversafepath"]):
            menu.append((_("Show Stored Titles List"), self.extended_help,_("Show the title stored"),self.extras,2))  
            menu.append((_("Show Stored Pictures"), self.show_pictures,_("Show the cover images stored"),self.extras))  #
            menu.append((_("Planer: ")+_("I make my radio day") , self.show_planer,_("I make my radio day"),self.extras))
        if pcfs:
            menu.append((_("Start PictureCenterFS"), self.slideshow,_("Start PictureCenterFS"),self.extras))
        menu.append((_('Backup webradioFS Favs and settings'), None,_("Save Favorites and settings"),None,2))
        menu.append((_('Backup ConfFS-Dir'), None,_("Save all files for webradioFS, PictureCenterFS, PlanerFS"),None,3))
        menu.append((_('Restore webradioFS Favs and settings'), None,_('Restore webradioFS Favs and settings'),None,4))
        menu.append((_('Restore ConfFS-Dir'), None,_("Restore all files for webradioFS, PictureCenterFS, PlanerFS"),None,5))
        menu.append((_('Delete Stream-Picons'), self.del_logos,_("Delete all Picons in /etc/ConfFS/streamlogos/ (e.g. for refresh)")))
        menu.append((_('Delete Favs-File and restart'), self.del_favs,_("Delete all your favorites and make new file")))
        self.menuStart(menu,_("Extras"),None,self.showMainMenu)    

    def rec_menu(self):
        menu = []
        menu.append((_("Check required Module"), self.rs_info,_("Check if the required modules are available")))
        menu.append((_("Install rec-Modules"), load_rf(self.session).run,_("Install rec-Modules")))   #stremrip-version usw
        if ripper_installed:
          if self.cache_list == None:
            menu.append((_("Instant recording, endless"), self.rec_endless,_("Run directly endlessly recording")))
            anz=" (5"
            if self.play_stream and self.play_stream["typ"]!="pvr" and int(self.play_stream["cache"])<1:
               self.play_stream["cache"]="5"
               menu.append((_("Cache to store later")+anz+" "+_("Tracks")+")", self.rec_cache,_("only works when the station clean title separation allows")))
          else:
              menu.append((_("Stop caching"), self.rec_stopcache,_("Stop caching")))        
          if len(self.fav_stream_list) and self.play_stream:
            menu.append((_("Timer and Record (set preferences)"), self.rec_set,_("Recording and switching timer, additional settings")))
        menu.append((_("Record-Settings"), self.showConfig,_("Record-Settings"),self.tools,"rec"))
        self.menuStart(menu,_("Record-Menu"),None,self.showMainMenu)

    def tools(self):
        menu = []
        menu.append((_("Settings-basics"), self.showConfig,_("Settings-basics"),self.tools,"all"))
        if sets_opt["expert"]==2:
            menu.append((_("Additional functions on / off"), self.showConfig,_("Additional functions on / off"),self.tools,"moduls"))        
        if sets_opt["scr"]:menu.append((_("Screensaver-Settings"), self.showConfig,_("Screensaver-Settings"),self.tools,"scr"))
        if sets_opt["display"]:menu.append((_("Display-Settings"), self.setDisplay,_("Display-Settings"),self.tools,None))
        if sets_opt["audiofiles"]:menu.append((_("File Play-Settings"), self.showConfig,_("File Play-Settings"),self.tools,"audiofiles"))
        if l4lR and sets_opt["lcr"]:
            menu.append((_("LCD4Linux Display-Settings"), self.showConfig,_("LCD4Linux Display-Settings"),self.tools,"l4l"))
        if ripper_installed==True and sets_opt["rec"]:
            menu.append((_("Record-Settings"), self.showConfig,_("Record-Settings"),self.tools,"rec"))
        if sets_opt["tasten"]:menu.append((_("RC-Buttons -Settings"), self.rc_tasten,_("RC-Buttons -Settings"),self.tools,None))
        if sd==4:
            txt= _("Font in setups too small? then change")
            if fileExists(skin_ext+"wbrFS_setup2.xml"):
              txt= _("Font in setups too big or crash on setup? then change")
            menu.append((_("Change setup xml"), self.change_setup_xml,txt,self.tools,None))        
        self.menuStart(menu,_("Tools"),None,self.showMainMenu)

    def showStreamMenu(self,akt=1):
        menu = []
        selectedStream = self["streamlist"].getCurrent()[0]
        self.stream_name = selectedStream[0]
        if len(self.configfile2[2]):
            trt=_("export")+" '"+self.fav_name+"' "+_("to")+" /tmp/webradioFS.exp"
            menu.append((trt, self.exportStreams,""))
        if os.path.exists("/tmp/webradioFS.imp"):
            menu.append((_("Import streams"), self.fav_importb,_("read and import streams from *imp file in /tmp")))
        if "m3u" not in self.fav_name:
            if sets_grund["stream_sort"]==2:
                menu.append((_("Sort streams"), self.sortStreams,_("Change order of streams"),self.extras))
            menu.append((_("show genres"), self.read_g,_("show streams with genre")))
            menu.append((_("Edit selected stream"), self.edit,_("Edit selected stream")))
            menu.append((_("Add new stream to favorites"), self.new,_("Add new stream to favorites")))
            menu.append((_("Autostart this Stream"), self.set_startstream,_("Set this stream for automatically play on plugin-start")))
            menu.append((_("Delete selected stream"), self.stream2deleteSelected,_("Delete selected stream")))
        if akt==1:
            self.menuStart(menu,_("Tools for selected Stream"),None,self.showMainMenu)
        else:
            self.menuStart(menu,_("Tools for selected Stream"),None)

    def aktions_menu(self):
        menu = []
        menu.append((_("Standby"), self.power_key,_("Standby")))
        menu.append((_("Deepstandby"), self.power_key_long,_("Deepstandby")))
        if offtimer == "chillen" or offtimer == "stoppen":
            menu.append((_("Stop Chill/Sleep"), self.chillmodus,_("Stop Chill/Sleep") ))
        else:
            menu.append((_("Chillen"), self.chillmodus,_("Chillen")))
            menu.append((_("Sleeptimer"), self.get_offtimer, _("Sleeptimer")))
        self.menuStart(menu,_("Actions-Menu"),None,self.showMainMenu)

    def menuStart(self,menu=None,titel=None,infos=None,back=None):
            if back: menu.insert(0,(_("back"), back,""))
            titel="webradioFS: "+titel
            self.menu_on=True
            self.selectionChanged()
            self.session.openWithCallback(self.menuCallback, menu_13, menu,titel,back,self.display_on,l4ls)

    def menuCallback(self,choice,back):
        if back and choice: self.m_back=back
        if L4LwbrFS:  
            L4LwbrFS.delete("wbrFS.07.box7")
            L4LwbrFS.delete("wbrFS.08.txt8")
            L4LwbrFS.setScreen(l4ls[3],l4ls[1],True)
        if choice and choice[1]:
            if len(choice)>3 and choice[3]:self.m_back=choice[3]
            if len(choice)>4 and choice[4] != None:
               choice[1](choice[4])
            else:
                choice[1]()
        else:
            self.menu_back(back)

    def menu_back(self,back=None):
        if L4LwbrFS:  
            L4LwbrFS.delete("wbrFS.07.box7")
            L4LwbrFS.delete("wbrFS.08.txt8")
            L4LwbrFS.setScreen(l4ls[3],l4ls[1],True)
        self.m_back=None
        if back:
            back()
        else:
            fsz=read_einzeln().reading((("view","font_size"),))[0]
            self.showConfigDone()
            
            if self.alt_fsz != fsz:
                self.alt_fsz= fsz
                self.favoriten()

    def change_setup_xml(self):
        if fontlist[4]:
              if fileExists(skin_ext+"wbrFS_setup_small.xml"):
                 os.rename(skin_ext+"wbrFS_setup.xml", skin_ext+"wbrFS_setup_big.xml")
                 os.rename(skin_ext+"wbrFS_setup_small.xml", skin_ext+"wbrFS_setup.xml")
              self.meld_screen(_("This image does not allow size for the ConfigListScreen, Font is from Image - I can not help unfortunateln\Please contact the skin developer"),"webradioFS - Info",20,"ERROR")
        else:
          if fileExists(skin_ext+"wbrFS_setup_small.xml"):
             os.rename(skin_ext+"wbrFS_setup.xml", skin_ext+"wbrFS_setup_big.xml")
             os.rename(skin_ext+"wbrFS_setup_small.xml", skin_ext+"wbrFS_setup.xml")
          else:
            os.rename(skin_ext+"wbrFS_setup.xml", skin_ext+"wbrFS_setup_small.xml")
            os.rename(skin_ext+"wbrFS_setup_big.xml", skin_ext+"wbrFS_setup.xml")

    def fav_importb(self):
        if os.path.exists("/tmp/webradioFS.imp"):
            from .wbrfs_funct import fav_import3
            zahl=fav_import3().imp2()
            if zahl:
                self.session.open(MessageBox, _('Import successfully')+"\n"+_('Please restart webradioFS') , type=MessageBox.TYPE_INFO, timeout=15)
            else:
               self.meld_screen( _("read-error from import-file"),"Info",20,"ERROR")
        else:
            self.meld_screen( _("import-file /tmp/webradioFS.imp not exist"),"Info",20,"ERROR")

    def patch_ow(self,nummer):
            newwrite=""
            start=0
            start2=1
            f=open("/usr/lib/enigma2/python/Plugins/Extensions/OpenWebif/controllers/views/main.tmpl","r")
            for x in f.readlines():
                 if not "webradioFS" in x:
                     newwrite+=x
                 if nummer==1:
                     if "#def extrasMenu" in x:
                         start=1
                     elif start==1 and "#end for" in x:
                         newwrite+="<li><a href='webradiofs' target='_blank'>webradioFS</a></li>\n"
                         start=2
            f.close()
            os.chdir("/usr/lib/enigma2/python/Plugins/Extensions/OpenWebif/controllers/views")
            try:
                os.remove("main.py")
                os.remove("main.pyo")
            except:
               pass
            os.system("cheetah-compile main")
            self.meld_screen( _("Patch finished.") +" "+_("Restart must be performed"),"webradioFS- "+_("query"),0,"??",self.patch_ow2,True)

    def patch_ow2(self, result):
          if result== True:
                self.volctrl.setVolume(self.org_vol,self.org_vol)
                quitMainloop(3)

    def set_startstream(self):
        global sets_grund
        if self.fav_name=="PVR-Radio all":
            w1="pvr0,"+str(self["streamlist"].getIndex())
        elif self.fav_name=="PVR-Radio all":
            w1="pvr1,"+str(self["streamlist"].getIndex())
        else:
            w1="web,"+str(self.play_stream["stream_id"])
        starter_set(akt="write",wert=w1)
        try:
            sets_grund["startstream1"]= self.play_stream["stream_id"]
            write_settings((("grund",sets_grund),))
        except:
           pass

    def groups_men(self):
        titel="webradioFS: "+_("Groups")
        self.menu_on=True
        self.session.openWithCallback(self.groupsCallback, groups_13, myfav_file,titel)

    def groupsCallback(self,group,groups):
        self.menu_on=False
        set_groups(groups)
        self.read_new()
        if not group:
             self.showMainMenu()
        else:
            for x in self.favoritenlist:
                 if x[0]==group:
                      self.fav_index=self.favoritenlist.index(x)
                      self.favoriten()
                      break

    def sortStreams(self):
        self.sorting= (1-3)
        self["playtext"].setText(_("Sort streams"))
        self.set_streamlist(self.configfile2[2],None,sort=1)

    def sortStreams2(self):
            for x in self.configfile2[2]:
                self.db("Update streams SET pos=%d WHERE stream_id=%d;" % (x[5],x[2]))
            self.sorting=None
            self.menu_back()
            self.favoriten()

    def setDisplay(self):
        right_site.hide()
        self.display_art="normal"
        self.session.openWithCallback(self.tools,webradioFSsetDisplay,fontlist)


    def del_favs(self):
        self.meld_screen(_("All stored streams are lost, sure?"),"webradioFS- "+_("query"),20,"??",self.del_favs2,False)

    def del_favs2(self,answer =None):
        if answer:  
          if os.path.isfile(myfav_file): os.unlink(myfav_file)
          self.session.open(TryQuitMainloop, 3)

    def del_logos(self):
        for x in os.listdir(sets_exp["logopath"]):
              if os.path.isfile(os.path.join(sets_exp["logopath"],x)): os.unlink(sets_exp["logopath"]+x)
        self.tools()

    def rc_tasten(self):
        self.session.openWithCallback(self.showConfigDone,WebradioFS_FB_Setup_13)

    def show_pictures(self):
         if pcfs==True:
             try:
                 path=sets_exp["coversafepath"]
                 self.wbrScreenSaver_stop()
                 right_site.hide()
                 self.session.openWithCallback(self.showConfigDone, Pic_Thumb,0,path) #,False
             except:
                 self.meld_screen(_("Plugin PictureCenterFS not installed or Path failed"),"webradioFS - Info",20,"ERROR")
                 self.extras()
         else:
             self.meld_screen(_("Plugin PictureCenterFS not installed or Path failed"),"webradioFS - Info",20,"ERROR")
             self.extras()

    def slideshow(self):
         if pcfs==True:
             try:
                 self.wbrScreenSaver_stop()
                 right_site.hide()
                 self.session.openWithCallback(self.showConfigDone, PictureCenter)
                 self.pcfs_run=True
             except:
                 self.meld_screen(_("Plugin PictureCenterFS not installed or Path failed"),"webradioFS - Info",20,"ERROR")
                 self.showConfigDone()


    def check_max(self):
                   connection2 = sqlite.connect(myfav_file)
                   connection2.text_factory = str
                   cursor = connection2.cursor()
                   cursor.execute("select COUNT(*) from streams")
                   (Anzahl,) = cursor.fetchone()
                   cursor.close()
                   connection2.close()
                   return Anzahl


    def answer2(self):
        pass



    def del_fav_eintrag(self,num):
               for x in self.favoritenlist:
                   if x[1]==num:
                       ind=self.favoritenlist.index(x)
                       del self.favoritenlist[ind]
                       break


##########################################################
########################################################
#####################################################
    def aktual_back(self,antwort):
           self.errorzaehler+=1
           if antwort== True:
              self.aktual()
           else:
              self.ok(None,self.errorzaehler)

    def aktual(self,stream_ok="nein",answer=None):
      if self.rec_list or satradio or self.configfile2[1]>29:
           self.showConfigDone()
      elif stream_ok != False:  
            if self.stream_urls and self.errorzaehler<len(self.stream_urls) and stream_ok != "aktual" and self["streamlist"].getCurrent()[0][1]==0:
                self.meld_screen(_('Connection attempt')+' '+str(self.errorzaehler+1)+' '+_('of')+' '+str(len(self.stream_urls))+' \n\n' + _('Stop trying to connect?\n(wait to check update from DB)') ,"webradioFS- "+_("query"),5,"??",self.aktual_back,False)
#            else:
#                if self["streamlist"].getCurrent() is not None:
#                  if self.configfile2[1] ==0:
#                    s=self.readSingleStreams(self["streamlist"].getCurrent()[0][2]) 
#                    if s and s["typ"] != "pvr" and stream_ok !="ja":
#                        liste=load_dats().reading("","",s["name"])
#                        if liste and liste[1] != s["url"] and liste[6]== 'VALID':
#                                  msg_text=_("neue URL aus DB erhalten")
#                                  self.db("Update streams SET defekt=0,url='%s',typ='%s',bitrate=%d WHERE stream_id=%d;" % (liste[1],liste[3],int(liste[4]),s["stream_id"]),None)
#                                  self.ok()
#                                  self.meld_screen(msg_text+"\n"+s["name"],"webradioFS - Info",20)
#                        elif self["streamlist"].getCurrent()[0][3]==0:
#                                 self.meld_screen("no new url for"+"\n"+s["name"],"webradioFS - Info",20)
#                        else:
#                                  self.db("Update streams SET defekt=1 WHERE stream_id=%d;" % s["stream_id"])
#                                  self.meld_screen(s["name"]+"\n"+"The resource requested is currently unavailable","Info",20,"ERROR")

    def db(self, db_string,akt=1):
        if self.connection is not None:
                        cursor = self.connection.cursor()
                        cursor.execute(db_string)
                        cursor.close()
                        self.connection.commit()
                        if akt: self.read_new()
    def set_start_edit(self, answer):
        if answer is True:
            self.edit()


    def get_offtimer(self):
            global offtimer
            offtimer_time = str(sets_exp["offtimer_time"])
            if self.wecker==0 :
                right_site.hide()
                self.session.openWithCallback(
                    self.exit_timer,
                    InputBox,
                    title = (_("Enter the minutes to shutdown:")),
                    text = offtimer_time,
                    maxSize = False,
                    type=Input.NUMBER
                )
                offtimer = "stoppen"
                if self.chill_taste: self.chill_taste.setText(_("Stop Sleeptimer"))
            else:
                if self.volume_timer.isActive():
                    self.volume_timer.stop()
                    self.wecker=0
                if self.chill_taste: self.chill_taste.setText(_("Start Sleeptimer"))
                offtimer = "starten"
        #else:
        #    self.meld_screen(_("Please set first volume parameters in the basic settings"),"webradioFS- "+_("Info"),20)
    def showAbout(self,akt=None,args=None):
        if self.e_help =="off":    
            self.display_art="info"
            self.ab_info="About"
            info=None
            self["key_red2"].setText(_("exit"))
            #self.versionstest=self.online_vers_check()
            aboutlist = []
            aboutlist.append(("webradioFS - Version "+myversion," "))
            aboutlist.append((" ",' '))


            aboutlist.append(('Autor: shadowrider',""))
            aboutlist.append(('website: github'," "))
            aboutlist.append((" "," "))
            aboutlist.append((" ",' '))
            #if self.versionstest and self.versionsalter<2:
            cursor = self.connection.cursor()
            cursor.execute("select COUNT(*) from streams;")
            row = cursor.fetchone()
            s_a=self.check_max()
            cursor.execute("select COUNT(*) from groups;")
            row = cursor.fetchone()
            s_g=row[0]
            row = cursor.fetchone()
            cursor.close()
            inf1=_("Your have")+" "+str(s_a)+" "+_("streams in")+" " +str(s_g)+" "+_("groups")
            aboutlist.append((inf1," "))

            self.wbrScreenSaver_stop()
            self.botton_on_off()
            self["streamlist"].style = "about"
            self["streamlist"].disable_callbacks = False
            self["streamlist"].setList(aboutlist)
            self["key_red2"].setText(_("back"))
            self.setTitle("webradioFS - "+_("About"))

           
    def set_update_txt(self,txt=""):
        if len(txt):
            self.update_txt=self.update_txt+txt+"\n"
            self["help"].setText(self.update_txt)
            d=debug(str(txt))



#### update ende ################################################
#################################################################

    def showInfo(self,played=0,id=None):
         if id:   
            self.display_art="info"
            s=None
            if self.configfile2[1] <30:
              s=self.readSingleStreams(id)
            else:
               s=self.play_stream
            t1=_("Info for selected stream:")
            if played==1: t1=_("Info for continuous stream:")
            self.text_list2=[]
            if s:
              self.text_list2.append((_("Streamname:"),s["name"]))
              
              if self.configfile2[1] <30:               
                gr=""
                for x in fav_groups:
                   if x[0]==s["group1"]:
                       gr= x[1] 
                self.text_list2.append((_("Group:"),gr))
                #self.text_list2.append((_("Uploader:"),s["uploader"]))
                self.text_list2.append((_("Description:"),s["descrip"]))
                self.text_list2.append((_("Bitrate:"),str(s["bitrate"])))
                self.text_list2.append((_("Genre(s):"),s["genre"]))
                self.text_list2.append((_("Stream-Typ:"),s["typ"]))
                if "cache" in s: self.text_list2.append((_("caching Tracks")+":",str(s["cache"])))
                if s["volume"]==0: 
                  volume=_("None")
                else:
                  volume=str(s["volume"])
                self.text_list2.append((_("Volume:"),volume) )
              if self.configfile2[1] <30: 
                  br=_("URL:")
              else:
                  br=_("Path:")
              self.text_list2.append((br,s["url"]))
            self.text_list2.append(("",""))

            if s and self.configfile2[1] <30:
              if str(s["defekt"]) != "0" and self.configfile2[1] <10:
                  self.text_list2.append((_("saved as defect"),""))

            if self.configfile2[1] ==0:
              currPlay = self.session.nav.getCurrentService()
              if currPlay:
                  self.text_list2.append((_("Organization:"),currPlay.info().getInfoString(iServiceInformation.sTagOrganization)))
                  self.text_list2.append((_("AudioCodec:"),currPlay.info().getInfoString(iServiceInformation.sTagAudioCodec)))
                  self.text_list2.append((_("ChannelMode:"),currPlay.info().getInfoString(iServiceInformation.sTagChannelMode)))
                  self.text_list2.append((_("Location:"),currPlay.info().getInfoString(iServiceInformation.sTagLocation)))
            elif self.configfile2[1] >29:
              currPlay = self.session.nav.getCurrentService()
              if currPlay:
                  self.text_list2.append((_("Tag Title:"),currPlay.info().getInfoString(iServiceInformation.sTagTitle)))
                  self.text_list2.append((_("Tag Album:"),currPlay.info().getInfoString(iServiceInformation.sTagAlbum)))
                  self.text_list2.append((("Tag Genre:"),currPlay.info().getInfoString(iServiceInformation.sTagGenre)))
                  self.text_list2.append((_("Tag Artist:"),currPlay.info().getInfoString(iServiceInformation.sTagArtist)))
                  self.text_list2.append((_("Tag Date:"),currPlay.info().getInfoString(iServiceInformation.sTagDate)))      
                  self.text_list2.append((_("Tag Comment:"),currPlay.info().getInfoString(iServiceInformation.sTagComment)))

            self.wbrScreenSaver_stop()
            self.botton_on_off()
            self["streamlist"].style = "info"
            self["streamlist"].disable_callbacks = False
            self["streamlist"].setList(self.text_list2)
            try:
                self["playtext"].setText(s["descrip"])
            except:
                self.meld_screen(_("Error in Stream-data, webradioFS.fav corrupted"),"webradioFS- "+_("ERROR"),30,"ERROR")
            self["key_red2"].setText(_("back"))

    def showConfig(self,abteil):
        self.wbrScreenSaver_stop()
        fav_datei=self.favoritenlist[self.fav_index]
        self.session.openWithCallback(self.showConfigDone, WebradioFSSetup_13,abteil)
    def set_all_options(self):
        sets_opt["expert"]=2
        write_settings((("opt",sets_opt),))
        self.showMainMenu()

    def showConfigDone(self,args=None,menu=None):
        if sets_exp["stop_abschalt"]:
             self.blocker.start()
        else:
             self.blocker.stop()
        if args==2:
             self.m_back=None
             self.meld_screen(_("No Pictures in Path"),_("ERROR"),20,"ERROR")
        elif self.tv1 == None and self.video==None:
            if self.menu_on and self.m_back != None:
               if menu=="tools":
                   if sets_opt["expert"]==0:
                       self.showMainMenu()
                   else:
                       self.tools()
               elif menu=="moduls":
                     self.showMainMenu()
               elif menu=="extras":
                   self.extras()
               elif menu=="aktions":
                  self.aktions_menu()
               elif menu=="admin":                  
                  self.admin_menu()

            else:
               self.screensaver_off = 0
               self.ResetwbrScreenSaverTimer()
            self.menu_on=None
            self.m_back=None
            try:right_site.show()
            except:pass

    def wbrScreenSaver_stop(self):
        if self.wbrScreenSaverTimer.isActive():
             if sispmctl:   
                if "0" in sets_sismctl["ssr2"] or "1" in sets_sismctl["ssr2"]:
                    sets=""
                    for x in sets_sismctl["ssr2"]:
                        sets=sets+str(x)+"\n"
                    sispmctl_file=open("/tmp/sispmctlext.txt","w")
                    sispmctl_file.write(sets)
                    sispmctl_file.close()
             self.wbrScreenSaverTimer.stop()
             self.screensaver_off = 1
    def wbrScreenSaverTimer_Timeout(self):
        global wbrfs_saver
        self.screensaver_off = 0
        playlist=None
        if self.wbrScreenSaverTimer.isActive():
            self.wbrScreenSaverTimer.stop()
        else:
             if sispmctl:   
                if "0" in sets_sismctl["ssr1"] or "1" in sets_sismctl["ssr1"]:
                    sets=""
                    sispmctl_file=open("/tmp/sispmctlext.txt","w")
                    for x in sets_sismctl["ssr1"]:
                        sets=sets+str(x)+"\n"
                    sispmctl_file=open("/tmp/sispmctlext.txt","w")
                    sispmctl_file.write(sets)
                    sispmctl_file.close()
        if onwbrInfoScreen and not self.tv1:
              self.ResetwbrScreenSaverTimer()
        elif (self.anzeige_fav==_("Play file") or satradio or streamplayer.is_playing or self.playlist2 or self.einzelplay) and self.stream_info !=_("trying to establish connection") and not self.tv1 and not self.video and not self.configfile2[1] in (7,3):
            rec_path=None
            rec_art=""
            if self.record and l4l_info["rec"]>0: 
                 rec_art=self.rec_set_list["rec_art"]
                 rec_path=self.rec_path
                 if self.rec_path1:
                      rec_path=self.rec_path1
            text =  _("Stopped") 
            text2= ""
          
            
            if self.playlist2 or (self["streamlist"].getCurrent() and self["streamlist"].getCurrent()[0]):
                if self.einzelplay or self.anzeige_fav==_("Play file"):
                      text = self.streamname
                      text2=_("Single-play")
                      pl1=[self.configfile2[2][self["streamlist"].getIndex()] ]
                      playlist=(self.configfile2[0],pl1,0)

                elif self.playlist2: 
                    playlist= (self.playlist2[0],self.playlist2[2],self.playlist2_ind)
                    text2=self.configfile2[0] 
                    if self.play_stream:text = self.play_stream["name"]


                else:                   
                   text =  _("Stopped") 
                   text2= ""
                   if len(self.fav_name) != 0: text2="Fav.: "+self.fav_name
                   if self.play_stream:text = self.play_stream["name"]
           
            art2=sets_scr["slideshowpath"]
            set1=0            
            picon=def_pic

            if self.sets["logo"]:
               picon=self.sets["logo"]
            logo=picon
            try:
                arts=self.play_stream["sscr"].split(",")
                art=arts[0]
                if art !="default" and len(arts)>1:
                     if len(arts[1]):art2=arts[1]
            except:
                arts=(None,None)
                art="default"
                art2=None
            if art=="default":
                set1=1
                art=sets_scr["screensaver_art"]
                arts=((sets_scr["screensaver_art"],None))
            
            
            if art == "pcfs_slideshow" and pcfs==True:
                   if os.path.exists(sets_scr["slideshowpath"]):
                       right_site.hide()
                       self.session.openWithCallback(self.showConfigDone, Pic_Full_View,art2,"saver")
                   else:
                       self.meld_screen(_("Path not exist"),_("ERROR"),20,"ERROR")
            elif art == "picscreensaver" and picscreensaver==True:
                   try:
                       from Plugins.Extensions.picscreensaver.plugin import picScreensaverScreen
                       right_site.hide()
                       self.session.openWithCallback(self.showConfigDone, picScreensaverScreen)
                   except:
                       pass


            elif art == "slideshow_random" or art == "slideshow_sorted":
              if os.path.exists(art2):  
                read_sub=sets_scr["slideshow_subdirs"] 
                #dpkg=sets_prog["DPKG"]
                filelist=file_list(art2,read_sub).Dateiliste                 
                if len(filelist)>1:
                    from .wbrfs_screensaver import wbrfs_diashow
                    if not wbrfs_saver:
                        
                        wbrfs_saver=self.session.instantiateDialog(wbrfs_diashow,filelist,art,sets_scr,fontlist[4])
                        wbrfs_saver.show()

                else:
                    self.meld_screen(_("no picture in path for slideshow")+"\n"+str(art2) ,"webradioFS- "+_("ERROR"),30,"ERROR")

            elif art =="theme_images":
                if sets_scr["Keyword"] != "":
                    right_site.hide()
                    self.session.openWithCallback(self.ResetwbrScreenSaverTimer,wbrScreenSaver_13, text,text2,rec_path,self.rec_set_list["rec_cover"],sets_scr["Keyword"],art,self.stream_info,logo,rec_art,self.display_on)
            elif art =="tv":
                 #right_site.hide()
                 if self.tv1==None:self.live_tv()
            elif art =="Play_Video":
                 vid=None
                 if set1==1:
                    vid=sets_scr["wbrvideofile"]
                 else:
                    if len(art2):vid=art2
                 if self.video==None:
                    self.pvideo(vid)
            elif art =="Play_Video_sort" or art =="Play_Video_rand": 
                 self.pvideo()
            else:
                coverpath=None
                right_site.hide()
                if cover_save["cache"] == None and l4l_info["rec"]: coverpath= cover_save["path"]
                self.session.openWithCallback(self.ResetwbrScreenSaverTimer,wbrScreenSaver_13, text,text2,rec_path,coverpath,"",art,self.stream_info,playlist,logo,rec_art,self.display_on,self.exit_time,self.standby_aktion)
            
        
    def ResetwbrScreenSaverTimer(self,exit_art="",num=None):
      #f=open("/tmp/exiter","a")
      #f.write(str(exit_art)+", "+str(num)+"\n")
      #f.close()
      if exit_art=="exit" and num and len(num) and num[7]=="Files":
               self.set_streamlist(self.configfile2[2],num[1],None,None)
      if right_site:right_site.show()
      if not self.tv1:  
#        if self.wecker==1:        
#                self.volume_timer.stop()
#                self.wecker=0
#                if self.chill_taste: self.chill_taste.setText(_("Chillen"))
#                offtimer = "starten"       
        if onwbrScreenSaver:
                set_onwbrScreenSaver()
        if sets_scr["timeout"] > 0 and self.screensaver_off == 0:
                t1=sets_scr["timeout"]
                if self.wbrScreenSaverTimer.isActive():
                    self.wbrScreenSaverTimer.stop()
                if len(self.favoritenlist):
                  if self.configfile2 and len(self.configfile2):  
                    if not satradio and self.configfile2[1] >0 and self.configfile2[1] <30:
                        t1=300
                self.wbrScreenSaverTimer.startLongTimer(t1)
        if exit_art != "":
            self.exit_art=exit_art
            if exit_art=="stop":
                  self.stop_stream()
            if exit_art=="sleep":
                #self.exit_art=
                #if self.standby_aktion==None or (self.standby_aktion != "chillen" and self.standby_aktion != "wecken"):
                    #self.volume_timer.stop()
                    #if self.standby_aktion !="chillen":
                        self.exit_art="standby"
                        self.wecker=2
                        self.vol_start()

            if exit_art=="record":
              self.rec_endless()
            if exit_art=="nummer":
              self.keyNumberGlobal(num)
            if exit_art=="record2":
              self.rec_menu()
            if self.record and exit_art=="stopped":
              if not self.rec_list: 
                  self.wbrfs_recClosed2("stopped")
              else:
                  self.rec_list=None
                  self.Favoriten_Wechsel2(None)
                  self.ok()    
            elif (self.record or self.rec_timer.isActive()) and exit_art =="off":
                self.power_key_long()
            elif (self.record or self.rec_timer.isActive()) and exit_art=="standby":
               self.power_key()
            elif exit_art!="record":
               self.exit_art_b(True)


    def exit_art_b(self,answer):
        if answer == True:
            try:
                if self.exit_art=="standby":
                   self.power_key()
                elif self.exit_art=="off":
                   self.power_key_long()
                elif self.exit_art=="stopped":
                  self.ok()
                elif self.exit_art=="ende":
                  self.exit_a()
 
            except:
                self.showConfigDone()


    def stream2deleteSelected(self):
        self.wbrScreenSaverTimer.stop()
        if self["streamlist"].getCurrent() is not None and "(db)" not in self.fav_name:
            selectedStream = self["streamlist"].getCurrent()[0]
            self.meld_screen(_("Delete this stream from Favorites") +"?\n\n%s" % selectedStream[0] ,"webradioFS- "+_("query"),5,"??",self.deluserIsSure,True)

    def deluserIsSure(self,answer):
        if answer is None:
            self.close
        if answer is False:
            self.close
        else:
            self.db("delete from streams where stream_id = %d" % (self["streamlist"].getCurrent()[0][2]))
        self.showConfigDone()
        self.read_new()
    
############################################################################### 
    def exit_timer(self, result):
        right_site.show()
        global offtimer
        if result:
            sets_exp["offtimer_time"]=result
            write_settings((("exp",sets_exp),))
            standby_time = int(result)*60
            self.exit_time=time.time()+standby_time
            self.ResetwbrScreenSaverTimer()
            self.akt_volume=int(self.volctrl.getVolume())
            vol_time = int(self.volctrl.getVolume())/5
            vol=5
            self.zeit = 1
            self.vorgtitle=self.getTitle()
            if sets_exp["vol_auto_time"] == 0:
                self.zeit = standby_time
                vol=self.akt_volume
            elif int(sets_exp["vol_auto_time"]) > 0 and standby_time > vol_time:                
                time1 = standby_time-vol_time*int(sets_exp["vol_auto_time"])
                if time1 >= 1: 
                    self.zeit = time1 
                else:
                    self.zeit = standby_time    
            self.vol_start(self.zeit,vol,"standby")
        else:
            offtimer = "starten"
            if self.chill_taste: self.chill_taste.setText(_("Chillen"))


    def green(self):  #green long
         global offtimer
         if self.e_help != "on" and not self.rec_list:  
            self.showConfigDone()
            if self.wecker==1 or self.standby_aktion:
                self.stop_sleep_chill()
            else:

                    self.get_offtimer()
                    if self.chill_taste: self.chill_taste.setText(_("Stop Chill/Sleep"))
                    offtimer = "stoppen"
         else:
            self.update()

    def stop_sleep_chill(self):
                self.volume_timer.stop()
                self.wecker=0
                if self.chill_taste: self.chill_taste.setText(_("Chillen"))
                self.standby_aktion=None
                self.setTitle(self.vorgtitle)
                offtimer = "starten"
                self.volctrl.setVolume(self.akt_volume,self.akt_volume)
                try:
                   self.chsltitel_timer.stop()
                except:
                   pass
                
    def sleep_chill_time(self):
        if self.standby_aktion:
          e_time=int(round((self.exit_time-time.time())/60))
          if self.standby_aktion== "chillen" and e_time<1:          
                self.setTitle(self.vorgtitle+ " ("+_("week up!")+")")
                self.volume=self.maxV
                self.standby_aktion="wecken"
                self.set_volume()
          elif self.exit_time:
             if not "min." in self.getTitle().lower():
                          self.vorgtitle= self.getTitle()
             if self.standby_aktion== "chillen":
                    self.setTitle(self.vorgtitle+ " ("+_("Chilling: still")+" "+ str(e_time)+" "+_("min.")+")" )
             else:
                     self.setTitle(self.vorgtitle+ " ("+_("Sleep in")+" "+ str(e_time)+" "+_("min.")+")" )
             self.chsltitel_timer.startLongTimer(10)

    def vol_start(self,zeit=sets_exp["vol_auto_time"],volume=30,aktion=None):
        global offtimer
        if aktion:
            self.standby_aktion= aktion
        self.sleep_chill_time()
        self.oldvol3 = self.volctrl.getVolume()

        if self.wecker==0 and zeit>0:
            self.volume_timer.stop()
            self.screensaver_off = 0
            self.showConfigDone()            
            self.volume=volume
            self.wecker=1
            self.zeit=zeit
            self.volume_timer.startLongTimer(zeit)

        elif self.wecker==2 or zeit == 0:
            self.wecker=0
            if self.standby_aktion=="wecken":
                pass
            elif self.standby_aktion=="standby":
                    if not onwbrScreenSaver:
                         self.power_key()
                    else:
                         offtimer = "starten"     
            elif self.standby_aktion=="exit":
                  if not onwbrScreenSaver:
                      self.power_key_long()
                  else:
                      offtimer = "starten"
            else:
                if self.chill_taste: self.chill_taste.setText(_("Chillen"))
                self.setTitle(self.vorgtitle)
                offtimer = "starten"
                self.standby_aktion= None



    def set_volume(self,args=None):
            if self.volume<5:
                self.volume=5
            oldvol2 = self.volctrl.getVolume()
            if oldvol2 < self.volume and self.standby_aktion=="wecken":
                VolumeControl.instance.volUp()
                self.volume_timer.startLongTimer(sets_exp["vol_auto_time"])
            elif oldvol2 > 5 and oldvol2 > self.volume and (self.standby_aktion=="standby" or self.standby_aktion=="exit" or self.standby_aktion=="chillen"):
                VolumeControl.instance.volDown()
                self.volume_timer.startLongTimer(sets_exp["vol_auto_time"])
            else:
                self.volume_timer.stop()
                
                #self.setTitle(self.vorgtitle)
                if self.standby_aktion !="chillen":
                    self.standby_aktion= None
                    self.setTitle(self.vorgtitle)
                    self.wecker=2
                    self.vol_start()


    def setStandardVolume(self):
        right_site.hide()
        self.session.openWithCallback(self.showConfigDone,volplusFS)

    def chillmodus(self,args=None):
      global offtimer
      if self.rec_list or (self.fav_list and self.configfile2[1] != 30):
          pass
      elif self.e_help=="on": 
          if self.versionsalter>1:
               self.exit()
          elif self.versionsalter>0:
             self.update()
      elif self.meldung1:
            self.meldung_back(True)
      elif self.tv1 or self.video:
          pass
      else:

        if self.configfile2[1] >29:
             if not isinstance(self.configfile2,types.ListType):
                  self.configfile2=list(self.configfile2)
             if self.auto_play:
                 self.auto_play=None
                 self.sets["autoplay"]=auto_png_off
                 self.add_rem_m3u("remove")
             else:
                 self.auto_play=True
                 self.sets["autoplay"]=auto_png_on
                 self.add_rem_m3u("add")
                 if not streamplayer.is_playing and not self["streamlist"].getCurrent()[0][7].startswith("Dir"):
                     self.ok()
             right_site.new_set(self.sets)



        else:
          #if not self.standby_aktion or self.standby_aktion =="chillen":  
            if self.wecker==1 or self.standby_aktion: #or offtimer == "chillen" or offtimer == "stoppen":
                self.stop_sleep_chill()

            else:           
                #if sets_exp["vol_auto_time"]>0: #sets_exp["ex_vol"]>0 and 
                    self.wbrScreenSaver_stop()
                    right_site.hide()
                    from .chset import wbrfs_set_we
                    self.session.openWithCallback(self.chill_back,wbrfs_set_we)
                #else:
                #    self.meld_screen(_("Please set first volume parameters in the basic settings"),"webradioFS- "+_("Info"),20)
      #f.close()

    def chill_back(self,zeitdiff,minV, maxV):
        right_site.show()
        self.vorgtitle=self.getTitle()
        
        global offtimer
        if zeitdiff ==0:
          self.showConfigDone(None,"aktions")
 
        else:    
           #self.chill_off_timer= eTimer()
           
           self.akt_volume=int(self.volctrl.getVolume())
           self.maxV=maxV
           if self.chill_taste: self.chill_taste.setText(_("Stop Chill/Sleep"))
           self.exit_time=time.time()+zeitdiff+30
           
           offtimer = "chillen"
           self.standby_aktion= "chillen"
           
           self.vol_start(sets_exp["vol_auto_time"],minV,"chillen")

#    def chill_off(self):
#        self.volume=self.maxV
#        self.standby_aktion="wecken"
#        self.set_volume()

    def power_key_long(self):
                self.exit_art ="off"
                self.exit(True,"off")
    def power_key(self):
            self.exit_art ="standby"
            self.exit(True,"standby")

    def exportStreams(self):
           if len(self.configfile2[2]):
              f=open("/tmp/webradioFS.exp","w")
              f.write("#export from webradioFS - Fav: "+self.fav_name+"\n")
              for x in self.configfile2[2]:
                  s=self.readSingleStreams(x[2])
                  
                  name1=s["name"]
                  url1=str(s["url"])
                  typ1=s["typ"]
                  btr1=s["bitrate"]

                  if (name1 and len(name1)) and (url1 and len(url1)) and (typ1 and len(typ1)):
                      name1= str(s["name"]).strip().replace("\n",", ").replace("{","").replace("}","")
                      descr1=str(s["descrip"]).strip().replace("\n",", ").replace("{","").replace("}","")
                      typ1=str(s["typ"]).strip().replace("\n",", ").replace("{","").replace("}","")
                      if not descr1 or not len(descr1): descr1=" "
                      if not btr1: btr1=0
                      f.write("{"+name1+"}{"+url1+"}{"+typ1+"}{"+descr1+"}{"+str(btr1)+"}\n")
              f.close()    


    def getStreams(self,art,con_check=0):
        global sets_prog
        con1=0
        stream_liste=[]
        groups=[]
        set_groups(groups)
        db=myfav_file
        dbTimer = eTimer()
        if os.path.exists(db) and os.path.getsize(db)>5000:
            try:
                cursor = self.connection.cursor()
                con1=1
            except:
                if db != "/etc/ConfFS/webradioFS_favs.db" and con_check == 0:
                   dbTimer = eTimer()
                   if fontlist[4]:
                             dbTimer_conn = dbTimer.timeout.connect(self.getStreams,1)
                   else:
                       dbTimer.callback.append(self.getStreams,1)
                   dbTimer.startLongTimer(120)
#                else:
                   
#                   self.fav_import2(None,3)

            if con1==1:
                try:
                    try:
                        cursor.execute("select sscr from streams;")
                    except:
                       cursor.execute("ALTER TABLE streams ADD COLUMN 'sscr' TEXT DEFAULT 'default'" )
                    try:
                        cursor.execute("select pos from streams;")
                    except:
                       cursor.execute("ALTER TABLE streams ADD COLUMN 'pos' INTEGER DEFAULT 1000" )
                    try:
                        cursor.execute("select cache from streams;")
                    except:
                       cursor.execute("ALTER TABLE streams ADD COLUMN 'cache' INTEGER DEFAULT 0" )
                except:
                   pass
                cursor.execute("select * from groups;")
                del_row=None
                for row in cursor:
                        if not str(row[1]).startswith("wbrfs"):
                            groups.append(row)

                if len(groups):       
                    cursor.execute("select name, group1,stream_id,defekt,sscr,pos,cache,bitrate,picon,url,typ from streams;")
                    failed=[]
                    for row in cursor:
                        try:
                           test1=int(row[3])+int(row[2])+int(row[5])+int(row[7])
                           pvr_pic=""
                           if row[10]=="pvr":
                              pos = row[9].rfind(':')
                              pvr_pic=row[9][:pos].rstrip(':').replace(':','_') + ".png"
                           stream_liste.append([row[0], row[1], row[2], row[3],art, row[5],0,"radio",row[6],row[8],pvr_pic])
                        except:
                           failed.append(row[2])
                    if len(failed):           
                        for x in failed:
                            cursor.execute("delete from streams where stream_id = %d" % x)

                playlists=[]
                try:
                    cursor.execute("select * from playlists;")
                    for row in cursor:
                            playlists.append(row)                
                except:
                    cursor.execute('CREATE TABLE IF NOT EXISTS playlists (ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,dir TEXT NOT NULL,subdirs INTEGER,random INTEGER, autoplay INTEGER,sscr TEXT );')

                self.connection.commit()
                cursor.close()
                if len(stream_liste):
                    return stream_liste

        if con1==1:
            set_groups(groups)
            dbTimer = None
            return stream_liste    


    def readSingleStreams(self,id=None):
           single_stream=None
           if id and (self.configfile2[1] ==0 or self.configfile2[1] ==8):
                cursor = self.connection.cursor()
                cursor.execute("select name, descrip, url, typ, genre2, defekt,bitrate,genre,volume,uploader,rec,zuv,picon,group1,stream_id,sscr,cache from streams WHERE stream_id=%d;" % id)
                for row in cursor:
                        try:
                           r=int(row[5])+row[6] 
                           single_stream={"name":row[0], "descrip":row[1], "url":row[2], "typ":row[3], "genre2":row[4], "defekt":row[5],"bitrate":row[6],"genre":row[7],"volume":row[8],"uploader":row[9],"rec":row[10],"zuv":row[11],"picon":row[12],"group1":row[13],"stream_id":row[14],"sscr":row[15],"cache":row[16]}
                        except:
                           cursor.execute("delete from streams where stream_id = %d" % row[14])
                cursor.close()
                self.connection.commit()
           else:
                s=self["streamlist"].getCurrent()[0]
                if len(s)>12:
                    s_id= -1
                    s_check=0
                    if admin and int(self.configfile2[1]) in (9,10,11,12,21,22):
                        s_id=s[2]
                        s_check=s[13]
                    single_stream={"name":s[0], "descrip":s[5], "url":s[6], "typ":s[7], "genre2":s[8], "defekt":s[3],"bitrate":s[9],"genre":s[10],"volume":0,"uploader":s[11],"rec":s[12],"zuv":s_check,"picon":s[2],"group1":self.configfile2[1],"stream_id":s_id,"sscr":"default","cache":0}
           return single_stream



    def showTextinfo(self,ch=None):
             txt=_("Media player setting may interfere with viewing station text and images")+"\n"
             txt+=_("to change it, please change over:")+"\n"
             txt+=_("Menu->Settings->System->Media Playback = original")
             self.meld_screen(txt,"webradioFS - Info")
#    def veraltet2(self,veraltet=False):
#            if veraltet:
#                self.db_meld=_("Please install new Version, old version are no longer supported") +"\n"+"Update?\n"
                #self.meld_screen(self.db_meld,"webradioFS- "+_("Info"),20,"ERROR")
#                self.meld_screen(self.db_meld,"webradioFS- "+_("query"),20,"??",self.update,False)

    def extended_help(self,num):
            text=""
            file1=os.path.join(sets_exp["coversafepath"],'titel_list.txt' )
            if num==2:
              self.title1="webradioFS - "+_("Titles") 
            if os.path.exists(file1):
                fp = open(file1)
                text = fp.read()
                fp.close()

            if not len(text.strip()): text = "Sorry, title file is missing or corrupted"         

            self["help"].setText(text)
            self.setTitle(self.title1)
            self.botton_on_off("ext_help")
####################################################################################
    def botton_on_off(self,art=None):
            global wbrfs_saver
            if self.e_help != "off":
                     self.e_help="off"
                     self["key_red2"].hide() 
                     self["key_green2"].hide()                     
                     self["help"].setZPosition(0)
                     self["buttons_abdeck"].hide()
                     self["playtext"].setText("webradioFS") 
                     self.set_streamlist(self.configfile2[2],l4l_info["Station"],None,self.akt_pl_num)
                     self["key_red"].show() 
                     self["key_green"].show()
                     self["green_pic"].show()
                     self.display_art="normal"
                     self.selectionChanged()
                     if self["streamlist"].getCurrent(): 
                         self.setTitle(self["streamlist"].getCurrent()[0][0]+"  ("+self.configfile2[0]+")")
                     
                     try:
                         self.session.deleteDialog(wbrfs_saver)
                     except:
                         pass
                     wbrfs_saver=None
                     self.screensaver_off = 0
                     self.ResetwbrScreenSaverTimer()                                         

            else:
               if self.rec_list: 
                  self["green_pic"].hide()
                  self["key_red2"].setText(_("Delete"))
               else:  
                 if art == "ext_help":    
                     self.e_help="ext_help"
                     self["help"].setZPosition(5)
                     self["green_pic"].hide()
                 else:
                     self.e_help="on"
                     if self.versionsalter>0: 
                         self["key_green2"].show()
                     else:
                         self["green_pic"].hide()                 

               self["key_green"].hide()
               self["rec_pic"].hide()                     
               self["key_red"].hide()
               self["buttons_abdeck"].show()
               self["key_red2"].setText(_("Back"))
               self["key_red2"].show()
 

############################################################################### 
          

    def zs2(self,answer=None):
          if answer != None:  
            global my_settings
            if answer==True:
               sets_grund["zs"]= True
               write_settings((("grund",sets_grund),))

            else:
               self.exit()
    def del_rec(self):
           if self["streamlist"].getCurrent():
                  text1=_("Selceted File is:")+"\n"+self["streamlist"].getCurrent()[0][0]+"\n\n"+_("Do you really want to delete this file?")+"\n\n"
                  self.meld_screen(text=text1 ,titel="webradioFS- "+_("query"),aktion=self.del_rec2,default=False,type1="??",timeout=20)

    def del_rec2(self,answer):
            if answer:	
                try:
                    os.remove(self["streamlist"].getCurrent()[0][1])
                    self.ok(self.configfile2[5])
                except OSError as e:
                        txt= 'error: \n%s' % e
                        self.meld_screen(txt ,"webradioFS- "+_("ERROR"),20,"ERROR")

###############################################################################        
class Fav_edit_13(Screen, ConfigListScreen):
    def __init__(self, session,stream,neu=0,infos=("","","","","")):
        tmpskin = open(fontlist[5]+"wbrFS_setup.xml")
        self.skin = tmpskin.read()
        tmpskin.close()
        if fontlist[5]==plugin_path +"/skin/SD/": 
            right_site.hide()
      
        self.groups=[]
        for x in fav_groups:
             self.groups.append(str(x[1]))
        self.connection = sqlite.connect(myfav_file)
        self.connection.text_factory = str
        self.cursor = self.connection.cursor()
        self.groups.append(_("None"))
        self.neu=neu
        sd={"name":"new","description":"description","url":'http://',"typ":"mp3","bitrate":0,"genre":' ',"genre2":' ',"volume":0,"defekt":0,"uploader":"","id":0,"err":0,"rec":0,"zuverl":"","picon":0,"group":self.groups[0],"sscr":"default","vid":"all_sorted","cache":0}
        titel1=" webradioFS - " + _("Add New Stream")
        self.stream=stream
        self.ziel=None
        self.meldung1=None
        self.stream_id=None
        self.g_list=[]
      
        self.g_list.append(("",""))
        self.g_list.append((" "," "))
        self.les_err=0
        if self.neu == 0 or self.neu == 3:
            if self.neu == 0:
                titel1=" webradioFS - " + _("Stream edit")
                try:
                    self.cursor.execute("select name, descrip, url, typ, genre2, defekt,bitrate,genre,volume,uploader,rec,zuv,picon,group1,stream_id,sscr,cache from 'streams' WHERE stream_id=%d;" % stream)
                    for row in self.cursor:
                        stream={"name":row[0], "descrip":row[1], "url":row[2], "typ":row[3], "genre2":row[4], "defekt":row[5],"bitrate":row[6],"genre":row[7],"volume":row[8],"uploader":row[9],"rec":row[10],"zuv":row[11],"picon":row[12],"group1":row[13],"stream_id":row[14],"sscr":row[15],"cache":row[16]}
                    self.stream_id=stream["stream_id"]
                except Exception as e:
                    self.les_err=1
            if self.neu == 3:
                titel1=" webradioFS - " + _("Add Stream")
            sd["name"] =stream["name"]
            sd["description"] =stream["descrip"]
            sd["url"]=stream["url"]
            sd["genre"]=stream["genre"]
            sd["genre2"]=stream["genre2"]
            sd["bitrate"]=int(stream["bitrate"])
            sd["defekt"]=int(stream["defekt"])
            sd["typ"]=stream["typ"]
            sd["volume"]=stream["volume"]
            sd["rec"]=int(stream["rec"])
            sd["zuverl"]=stream["zuv"]
            sd["uploader"]=stream["uploader"]
            sd["picon"]=int(stream["picon"])
            sd["sscr"]= stream["sscr"]#.split(",")[0]
            sd["cache"]= int(stream["cache"])
            try:
                sd["vid"]= stream["sscr"].split(",")[1]
            except:
                sd["vid"]="tmp"
            for x in fav_groups:
                 if stream["group1"]==_("None"):
                      sd["group"]=self.groups[0]
                 if x[0]==stream["group1"]:
                      sd["group"]=x[1]
        self.zuverl=sd["zuverl"]
        self.rec=sd["rec"]
        self.defekt=sd["defekt"]
        self.uploader=sd["uploader"]
        self.picon=sd["picon"]
        sscr_list=saver_list
        sscr_list.append(("default",_("default")))
        self.conf_stream=NoSave(ConfigText(default=sd["name"], visible_width = 50, fixed_size = False)) #self.stream
        self.conf_group=NoSave(ConfigSelection(choices =self.groups, default = sd["group"]))
        self.conf_sscr=NoSave(ConfigSelection(choices = sscr_list, default = str(sd["sscr"]).split(",")[0] ))
        self.conf_wbrvideofile = NoSave(ConfigText(default= sd["vid"], fixed_size = False))
        self.conf_pic_dir = NoSave(ConfigText(default= sd["vid"], fixed_size = False))
        self.conf_url=NoSave(ConfigText(default=sd["url"], fixed_size = False))
        self.conf_desc=NoSave(ConfigText(default=sd["description"], fixed_size = False))
        self.conf_typ=NoSave(ConfigSelection(choices = [("mp3", "mp3"), ("pls", "pls"), ("m3u", "m3u"), ("ogg", "ogg"), ("aac", "aac"), ("mms", "mms"), ("wma", "wma")], default = sd["typ"]))
        self.conf_genre2=NoSave(ConfigText(default=sd["genre2"], fixed_size = False))
        self.conf_genre=NoSave(ConfigText(default=sd["genre"], fixed_size = False))
        self.conf_bitrate=NoSave(ConfigInteger(default=int(sd["bitrate"]), limits = (10, 1000)))
        self.conf_cache=NoSave(ConfigInteger(default=int(sd["cache"]), limits = (0, 9)))
        self.conf_volume=NoSave(ConfigInteger(default=int(sd["volume"]), limits = (0, 100)))
        Screen.__init__(self, session)
        if fontlist[9]:
                    self.skinName = "WebradioFSSetup_e"
        else:        
            self.skin=self.skin.replace('backgroundColor="#000000"','')
            self.skin=self.skin.replace('foregroundColor="#ffffff"','')
            self.skinName = "WebradioFSSetup_13"
        self["rec_txt"] = Label(_("Stream edit"))
        self["playtext"] = StaticText("")
        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("Save"))
        self["key_yellow"] = Label(_("New group"))
        self["key_blue"] = Label("")
        if self.stream_id:self["key_blue"].setText(_("Delete"))
        self["green_pic"] = Pixmap()

        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
        {
            "green": self.save,
            "ok": self.ok_button,
            "red": self.exit,
            "cancel": self.exit,
            "yellow": self.new_group,
            "blue": self.dele,
        }, -2)
        self.setTitle(titel1)
        webradioFSConfigList = []
        self.configparser = ConfigParser()
        ConfigListScreen.__init__(self, [], session = session, on_change = self.load_list)
        self["config"].onSelectionChanged.append(self.setHelp)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self.onLayoutFinish.remove(self.layoutFinished)
        self.instance.setZPosition(2)
        if fontlist[8] or fontlist[9]:
          try:
            if not self.fontlist[4]:
                self['config'].instance.setFont(fontlist[3])
                self['config'].instance.setItemHeight(fontlist[2])
            else:
                    from skin import parseFont
                    stylemgr = eWindowStyleManager.getInstance()
                    skinned = eWindowStyleSkinned()
                    eListboxPythonConfigContent.setDescriptionFont(parseFont(conf_font2, ((1,1),(1,1))))
                    eListboxPythonConfigContent.setValueFont(parseFont(conf_font2, ((1,1),(1,1))))
                    eListboxPythonConfigContent.setItemHeight(conf_item)
                    stylemgr.setStyle(0, styleskinned)
          except Exception as e:
                                 f=open("/var/webradioFS_debug.log","a")
                                 f.write("set-fontin setup2:\n"+str(e)+"\n")
                                 f.close()
        self.load_list()

    def load_list(self,g=None):
        webradioFSConfigList=[]
        webradioFSConfigList.append(getConfigListEntry(_("Name/Title:"), self.conf_stream))
        webradioFSConfigList.append(getConfigListEntry(_("Group:"), self.conf_group))
        if self.neu != 3:webradioFSConfigList.append(getConfigListEntry(_("URL:"), self.conf_url))
        webradioFSConfigList.append(getConfigListEntry(_("Genre:"), self.conf_genre))
        webradioFSConfigList.append(getConfigListEntry(_("Genre 2 (optional):"), self.conf_genre2))
        webradioFSConfigList.append(getConfigListEntry(_("Bitrate:"), self.conf_bitrate))
        webradioFSConfigList.append(getConfigListEntry(_("Typ (mp3, pls, ogg....):"), self.conf_typ))
        webradioFSConfigList.append(getConfigListEntry(_("Volume:"), self.conf_volume))
        webradioFSConfigList.append(getConfigListEntry(_("Screensaver:"), self.conf_sscr))
        webradioFSConfigList.append(getConfigListEntry(_("Automatically caching Tracks"),self.conf_cache))
        if self.conf_sscr.value=="Play_Video":
                webradioFSConfigList.append(getConfigListEntry(_("Screensaver Video:"), self.conf_wbrvideofile))        
        elif self.conf_sscr.value=="slideshow_sorted" or self.conf_sscr.value=="slideshow_random":
                webradioFSConfigList.append(getConfigListEntry(_("Picture path:"), self.conf_pic_dir))
        webradioFSConfigList.append(getConfigListEntry(_("Description:"), ))
        webradioFSConfigList.append(getConfigListEntry("", self.conf_desc))
        self["config"].setList(webradioFSConfigList)


    def setHelp(self):
            self.cur = self["config"].getCurrent()
            self["key_yellow"].setText(" ")
            if self.cur[0]==_("Group:"):
               self["playtext"].setText(_("Left/Right for select")+"\n"+_("Yellow for new group"))
               self["key_yellow"].setText(_("New group"))
            elif self.cur[0]==_("URL:"):            
                 self["key_yellow"].setText("")
                 self["playtext"].setText(_("Press OK for edit"))
            elif self.cur[0]==_("Name/Title:") or self.cur[0]==_("Genre 2 (optional):"):
               self["playtext"].setText(_("Press OK for edit") )
            elif self.cur[1]== self.conf_typ:
               self["playtext"].setText(_("Left/Right for select") )
            elif self.cur[1]== self.conf_sscr:
               self["playtext"].setText(_("Left/Right for select") )
            else:
                self["playtext"].setText(self.cur[0])

    def add_g(self,g=None):
         if g:  
           self.cursor.execute('INSERT INTO groups (group1) VALUES("%s");'  %g)
           self.connection.commit()
           self.groups.append(str(g))
           self.conf_group.value=str(g)
    def meld_screen(self,text,titel,timeout=0,type1="INFO",aktion=None,default=True):
            text_len=len(text.split("\n"))
            melde_screen.start(text,titel,aktion,default,type1,timeout,sd)
            self.meldung1=True       
    def meldung_back(self,answer=0):
        m1=melde_screen.stop()
        self.meldung1=None
        b1=None
        if m1 and len(m1) and m1[1] != 0:
                if m1[3]=="??":
                    b1=m1[1](m1[2])
                elif m1[2] == True: 
                    b1=m1[1]()
        if b1: b1

    def new_group(self):
           self.cur = self["config"].getCurrent()
           if self.cur[0]==_("Group:"):
               right_site.hide()
               self.session.openWithCallback(self.new_groupFinished,VirtualKeyBoard, title=_("enter name for new group"), text="")

    def new_groupFinished(self,ret):
          right_site.show()
          if ret:
             if ret in self.groups: 
                self.meld_screen(_("Group exist"),"webradioFS - Info",0,"ERROR")
             else:
                self.add_g(ret)

    def path_wahl(self):
        right_site.hide()
        savepath="/"
        if len(self.conf_pic_dir.value)>1:savepath=self.conf_pic_dir.value
        text= _("Please select Path")
        self.session.openWithCallback(self.path_wahl2,SaveLocationBox,text,"","/",ConfigLocations(default=[savepath]))

    def path_wahl2(self,res):
        right_site.show()
        if res:
           self.conf_pic_dir.value=res

    def ok_button(self):
        if self.meldung1: 
            self.meldung_back()
        else:
            self.cur = self["config"].getCurrent()
            self.cur = self.cur and self.cur[1]
            if self.cur == self.conf_typ:
                list = [("mp3", "mp3"), ("pls", "pls"), ("m3u", "m3u"), ("ogg", "ogg"), ("aac", "aac"), ("mms", "mms"), ("wma", "wma"), ("mpd", "mpd")]
                self.session.openWithCallback(self.list_wahl, ChoiceBox, title=_("Select typ"), list=list)
            elif self.cur == self.conf_wbrvideofile:
                self.session.openWithCallback(self.vid_wahl,wbrfs_filelist)
            elif self.cur == self.conf_pic_dir:
                self.path_wahl()
            else:
                self.texteingabe()

    def texteingabeFinished(self, ret):
                right_site.show()
                if ret is not None:
                    if self.cur == self.conf_stream:
                        self.conf_stream.value = ret
                    elif self.cur == self.conf_url:
                        self.conf_url.value = ret
                    elif self.cur == self.conf_desc:
                        self.conf_desc.value = ret
                    elif self.cur == self.conf_genre2:
                        self.conf_genre2.value = ret
                    elif self.cur == self.conf_genre:
                       self.conf_genre.value = ret 

    def texteingabe(self):
                right_site.hide()
                titel=None
                if self.cur == self.conf_stream:
                        text1=self.conf_stream.value
                        titel=_("Stream-Name")
                elif self.cur == self.conf_url:
                        text1=self.conf_url.value 
                        titel=_("Stream-URL")
                elif self.cur == self.conf_desc:
                        text1=self.conf_desc.value
                        titel=_("Stream-description")
                elif self.cur == self.conf_genre2:
                        text1=self.conf_genre2.value
                        titel=_("Genre 2")
                elif self.cur == self.conf_genre:
                        text1=self.conf_genre.value
                        titel=_("Genre 2")
                if titel:
                    self.session.openWithCallback(self.texteingabeFinished,VirtualKeyBoard, title=titel, text=text1) 

    def vid_wahl(self, *args):
        if args:
           self.conf_wbrvideofile.value=args[0]

    def list_wahl(self,auswahl):
       if auswahl is not None:
          if self.cur == self.conf_typ:
                   self.conf_typ.value=auswahl[1]

    def save(self):
       if self.meldung1: 
            self.meldung_back()
       else:
         if self.conf_sscr.value=="Play_Video":
             if self.conf_wbrvideofile.value !="no path select in settings":
                  self.saver=self.conf_sscr.value+","+self.conf_wbrvideofile.value
             else:
                  self.saver="default"
         elif self.conf_sscr.value=="slideshow_sorted" or self.conf_sscr.value=="slideshow_random":
             if self.conf_pic_dir.value !="no path select in settings":
                  self.saver=self.conf_sscr.value+","+self.conf_pic_dir.value
             else:
                  self.saver="default"
         else:
             self.saver=self.conf_sscr.value
         self.g_n=None
         self.nstream_id=None
         self.cursor.execute('select group_id from groups WHERE group1="%s";' % str(self.conf_group.value))
         row = self.cursor.fetchone()
         if row:self.g_n=row[0]
         if not self.g_n:
             self.meld_screen(_("Please select Group"),"webradioFS - Info",0,"ERROR")
         else:
             try:  
                 self.cursor.execute('SELECT COUNT (*) from streams where name = "%s" and group1 = "%s";' % (self.conf_stream.value,self.g_n))
                 data=self.cursor.fetchone()
             except:
                data=[0]
             if data[0]>0:
                    self.cursor.execute('SELECT stream_id from streams where name = "%s" and group1 = "%s";' % (self.conf_stream.value,self.g_n))
                    row = self.cursor.fetchone()
                    if row:self.nstream_id=row[0]
                    
                    self.meld_screen(_("Streamname in this group exist, overwrite?"),"webradioFS- "+_("query"),0,"??",self.save2,True)
             else: 
                    if self.stream_id:
                       self.save2(True)
                    else:
                        self.save3()

    def save2(self,answer):
        if answer:
            s_id= self.stream_id
            iddel=None
            if self.nstream_id and self.stream_id != self.nstream_id:
                s_id=self.nstream_id
                iddel=1
            self.cursor.execute("UPDATE OR IGNORE streams SET name=?,descrip=?,url=?,typ=?,genre2=?,defekt=?,bitrate=?,genre=?,volume=?,uploader=?,rec=?,zuv=?,picon=?,group1=?,sscr=?,cache=? where stream_id = ?", (str(self.conf_stream.value),str(self.conf_desc.value),str(self.conf_url.value),self.conf_typ.value,self.conf_genre2.value,self.defekt,self.conf_bitrate.value,self.conf_genre.value,self.conf_volume.value,self.uploader,self.rec,self.zuverl,self.picon,self.g_n,self.saver,self.conf_cache.value,s_id))
            if iddel and self.stream_id:
                 self.cursor.execute("delete from streams where stream_id = %d" % (self.stream_id))
            self.db2()
        else:
            self.save3()
    def save3(self):
        self.cursor.execute("INSERT INTO streams (name, descrip, url, typ, genre2, defekt,bitrate,genre,volume,uploader,rec,zuv,picon,group1,sscr,cache) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);" ,(self.conf_stream.value,self.conf_desc.value,self.conf_url.value,self.conf_typ.value,self.conf_genre2.value,0,self.conf_bitrate.value,self.conf_genre.value,self.conf_volume.value,self.uploader,self.rec,self.zuverl,int(self.picon),self.g_n,self.saver,int(self.conf_cache.value)))
        self.db2()
    def db2(self):
        self.connection.commit()
        self.cursor.close()
        self.connection.close()
        right_site.show()
        self.close(1)
    def dele(self):
        if self.stream_id:
           self.meld_screen(_("Stream delete?"),"webradioFS- "+_("query"),0,"??",self.dele2,False)
    def dele2(self,ret):
        if ret and self.stream_id:
            self.cursor.execute("delete from streams where stream_id = %d" % (self.stream_id))
            self.db2()
    def exit(self):
        if self.les_err==1:
            self.db2()
        elif self.meldung1: 
            self.meldung_back()
        else:
            right_site.show()
            self.close(0)


class WebradioFSSetup_13(Screen, ConfigListScreen):
    def __init__(self, session,abteil,infos=("","","","","")):
        tmpskin = open(fontlist[5]+"wbrFS_setup.xml")
        self.skin = tmpskin.read()
        tmpskin.close()
        if skin_ext==plugin_path +"/skin/SD/": 
            right_site.hide()
        self.stream_sort= NoSave(ConfigSelection(choices = [(0,_("None")),(1,_("alphabetically")),(2,_("by user"))],default=sets_grund["stream_sort"]))
        self.hauptmenu = NoSave(ConfigYesNo(default = sets_prog["hauptmenu"]))
        self.exttmenu = NoSave(ConfigYesNo(default = sets_prog["exttmenu"]))
        self.stream_sort = NoSave(ConfigSelection(default=sets_grund["stream_sort"], choices = [(0,_("None")),(1,_("alphabetically")),(2,_("by user"))]))
        self.wbrbackuppath = NoSave(ConfigDirectory(default = sets_grund["wbrbackuppath"]) )
        self.exitfrage = NoSave(ConfigYesNo(default = sets_grund["exitfrage"]))
        self.skin_ignore = NoSave(ConfigYesNo(default = sets_grund["skin_ignore"]))
        self.picsearch = NoSave(ConfigSelection(default=sets_grund["picsearch"], choices = [("off",_("off")),("var1",_("Variante 1")),("var2",_("Variante 2")),("var3",_("Variante 3"))]))
        self.logos = NoSave(ConfigYesNo(default = sets_view["logos"]))
        self.Listlogos = NoSave(ConfigYesNo(default = sets_view["Listlogos"]))
        self.favpath = NoSave(ConfigDirectory(default = sets_grund["favpath"]))
        self.coversafepath = NoSave(ConfigDirectory(default = sets_exp["coversafepath"]))
        self.logopath = NoSave(ConfigDirectory(default = sets_exp["logopath"]))
        self.wbrfspvrpath = NoSave(ConfigDirectory(default = sets_exp["wbrfspvrpath"]))
        self.timeout = NoSave(ConfigInteger(default=sets_exp["timeout"], limits = (3, 60)))
        self.reconnect = NoSave(ConfigInteger(default=sets_exp["reconnect"], limits = (0, 99)))
        self.conwait = NoSave(ConfigInteger(default=sets_exp["conwait"], limits = (0, 99)))
        self.vol_auto_time = NoSave(ConfigInteger(default=sets_exp["vol_auto_time"], limits = (0, 600)))
        self.start_vol = NoSave(ConfigInteger(default = sets_exp["start_vol"], limits = (0, 100)))
        self.al_vol_max = NoSave(ConfigInteger(default = sets_exp["al_vol_max"], limits = (5, 100)) )
        self.offtimer_time = NoSave(ConfigInteger(default=sets_exp["offtimer_time"], limits = (0, 120)))
        self.offtimer_art = NoSave(ConfigSelection(default=sets_exp["offtimer_art"], choices = [(0,"Standby"),(1,"DeepStandby")]) )
        self.debug = NoSave(ConfigSelection(default=sets_exp["debug"], choices = [(0,"min"),(1,"on error"),(2,"max")]) )
        vi=sets_exp["versions_info"]
        if str(sets_exp["versions_info"]) != "True" and str(sets_exp["versions_info"]) != "False":
          vi=True
        self.stop_abschalt = NoSave(ConfigYesNo(default = sets_exp["stop_abschalt"]))
        self.pw1= [(str(sets_exp["picwords1"]),str(sets_exp["picwords1"]))]
        self.pw2= [(str(sets_exp["picwords2"]),str(sets_exp["picwords2"]))]
        self.pw3= [(str(sets_exp["picwords3"]),str(sets_exp["picwords3"]))]
        self.picwords1 = NoSave(ConfigSelection(default = self.pw1[0][0], choices = self.pw1))
        self.picwords2 = NoSave(ConfigSelection(default = self.pw2[0][0], choices = self.pw2))
        self.picwords3 = NoSave(ConfigSelection(default = self.pw3[0][0], choices = self.pw3))
        self.wbrSSfoto = NoSave(ConfigYesNo(default = sets_view["only_foto"]))

#if abteil=="opt":
        ansicht=sets_opt["expert"]
        if ansicht==True:
                 ansicht=1
        elif ansicht==False:
                 ansicht=0 
        self.opt_expert = NoSave(ConfigSelection(default=ansicht, choices = [(0,_("simple")),(2,_("Show all options"))]) ) #,(1,_("Individually adjustable"))
        self.opt_views = NoSave(ConfigYesNo(default = sets_opt["views"]))
        self.opt_scr = NoSave(ConfigYesNo(default = sets_opt["scr"]))
        self.opt_lcr = NoSave(ConfigYesNo(default = sets_opt["lcr"]))
        self.opt_display = NoSave(ConfigYesNo(default = sets_opt["display"]))
        self.opt_rec = NoSave(ConfigYesNo(default = sets_opt["rec"]))
        self.opt_audfile = NoSave(ConfigYesNo(default = sets_opt["audiofiles"]))
        self.opt_tasten = NoSave(ConfigYesNo(default = sets_opt["tasten"]))
        self.opt_sispmctl = NoSave(ConfigYesNo(default = sets_opt["sispmctl"]))
#elif abteil=="scr":
        self.wbrSScolor = NoSave(ConfigText(default = str(sets_scr["color"]), fixed_size = False))
        self.wbrSSbgcolor= NoSave(ConfigText(default = str(sets_scr["bgcolor"]), fixed_size = False))
        self.wbrSSbgcolor_random = NoSave(ConfigSelection(default=sets_scr["bgcolor_random"], choices = [(0,_("not random color")),(1,_("random color for labels")),(2,_("random color for background")),(3,_("random color for labels and background"))]))
        self.slideshow_bgcolor = NoSave(ConfigText(default = str(sets_scr["slideshow_bgcolor"]), fixed_size = False) )
        self.wbrvideofile = NoSave(ConfigText(default = sets_scr["wbrvideofile"]))
        self.wbrvideopath = NoSave(ConfigDirectory(default = sets_scr["wbrvideopath"]))
        self.wbrvideorecurr = NoSave(ConfigInteger(default = sets_scr["wbrvideorecurr"], limits = (0, 20000)))
        self.wbrScreenSaver = NoSave(ConfigInteger(default=sets_scr["timeout"], limits = (0, 999)) )
        self.slideshow_time = NoSave(ConfigInteger(default=sets_scr["slideshow_time"], limits = (0, 600)))
        self.wbrslideshowpath = NoSave(ConfigDirectory(default = sets_scr["slideshowpath"]))
        self.slideshow_subdirs = NoSave(ConfigYesNo(default = sets_scr["slideshow_subdirs"]))
        self.wbrSStextfix = NoSave(ConfigYesNo(default = sets_scr["textfix"]))
        self.colfromskin = NoSave(ConfigYesNo(default = sets_scr["colfromskin"]))
        self.slideshow_space = NoSave(ConfigInteger(default=sets_scr["slideshow_space"], limits = (0, 500)))
        self.wbrSSKeyword = NoSave(ConfigText(default = sets_scr["Keyword"], fixed_size = False))
        self.screensaver_art = NoSave(ConfigSelection(default=sets_scr["screensaver_art"], choices = saver_list))
        if (not pcfs and self.screensaver_art.value=="pcFS-slideshow") or (not picscreensaver and self.screensaver_art.value=="picscreensaver"): 
                  self.screensaver_art.value="wechsel" 
#elif abteil=="rec":
        self.fake_entry = NoSave(ConfigNothing())
        self.rec_path = NoSave(ConfigDirectory(default = sets_rec["path"]))
        self.rec_split = NoSave(ConfigYesNo(default = sets_rec["split"]))
        self.rec_caching_dir = NoSave(ConfigDirectory(default = sets_rec["rec_caching_dir"]))
        self.rec_new_dir = NoSave(ConfigYesNo(default = sets_rec["new_dir"]))
        self.rec_cover = NoSave(ConfigYesNo(default = sets_rec["cover"]))
        self.rec_anzeige = NoSave(ConfigYesNo(default = sets_rec["anzeige"]))
        self.inclp_save = NoSave(ConfigSelection(default=sets_rec["inclp_save"], choices = [(0,_("always ask")),(1,_("always store")),(2,_("never store"))]))
#elif abteil=="audiofiles": #"playlists":
        self.audiopath = NoSave(ConfigDirectory(default = sets_audiofiles["audiopath"]))
        self.audio_subdirs = NoSave(ConfigYesNo(default = sets_audiofiles["subdirs"]))
        self.audio_autoplay = NoSave(ConfigYesNo(default = sets_audiofiles["autoplay"]))
        self.audio_schleife = NoSave(ConfigYesNo(default = sets_audiofiles["schleife"]))
        self.audio_sort= NoSave(ConfigSelection(choices = [("random", _("Random")), ("byFolder", _("by Folder")), ("randByFolder", _("Random by Folder")), ("alphabetically", _("alphabetically")), ("nix", _("Not sort"))], default = sets_audiofiles["sort"]))
        self.audio_save_random= NoSave(ConfigYesNo(default = sets_audiofiles["save_random"]))
        self.audio_listpos= NoSave(ConfigYesNo(default = sets_audiofiles["audio_listpos"]))
#sispmctl
        if sispmctl and sets_sismctl["start"]:
          self.sismctl_start = NoSave(ConfigSequence(seperator = ",",limits=[(0,2),(0,2),(0,2),(0,2)],default = sets_sismctl["start"]))
          self.sismctl_exit = NoSave(ConfigSequence(seperator = ",",limits=[(0,2),(0,2),(0,2),(0,2)],default = sets_sismctl["exit"]))
          self.sismctl_ssr1 = NoSave(ConfigSequence(seperator = ",",limits=[(0,2),(0,2),(0,2),(0,2)],default = sets_sismctl["ssr1"]))
          self.sismctl_ssr2 = NoSave(ConfigSequence(seperator = ",",limits=[(0,2),(0,2),(0,2),(0,2)],default = sets_sismctl["ssr2"]))
          self.sismctl_nvers1 = NoSave(ConfigText(default = sets_sismctl["nvers1"]))
          self.sismctl_vers1 = NoSave(ConfigSequence(seperator = ",",limits=[(0,2),(0,2),(0,2),(0,2)],default = sets_sismctl["vers1"]))
          self.sismctl_nvers2 = NoSave(ConfigText(default = sets_sismctl["nvers2"]))
          self.sismctl_vers2 = NoSave(ConfigSequence(seperator = ",",limits=[(0,2),(0,2),(0,2),(0,2)],default = sets_sismctl["vers2"]))


        if l4lR and abteil=="l4l":
            lcd_sets=sets_view["l4l"].split(",")
            self.logo=plugin_path+"/skin/images/webradiofs.png"
            if len(lcd_sets)<30: 
                   i = 0
                   set=[]
                   while i < 30:
                        try:
                            set.append(lcd_sets[i])
                        except:
                            set.append(l4lsa[i])
                        i+=1    
                   lcd_sets=set 
            self.lcd_on = NoSave(ConfigYesNo(default=str2bool(lcd_sets[0])))
            self.lcd_nr = NoSave(ConfigInteger(default = int(lcd_sets[1]), limits = (0, 10)))
            from Plugins.Extensions.LCD4linux.module import L4Lelement
            L4LwbrFS = L4Lelement()
            display_size=L4LwbrFS.getResolution(self.lcd_nr.value)[0]
            AlignType = [(0, _("left")), (1, _("center")), (2, _("right")), ("5%", _("5%")), ("10%", _("10%")), ("15%", _("15%")), ("20%", _("20%")), ("25%", _("25%")), ("30%", _("30%")), ("35%", _("35%")), ("40%", _("40%")), ("45%", _("45%")), ("50%", _("50%")), ("55%", _("55%")), ("60%", _("60%")), ("65%", _("65%")), ("70%", _("70%")), ("75%", _("75%")), ("80%", _("80%")), ("85%", _("85%")), ("90%", _("90%")), ("95%", _("95%"))]
            self.lcd_stop = NoSave(ConfigYesNo(default=str2bool(lcd_sets[2])))
            self.lcd_screen = NoSave(ConfigInteger(default = int(lcd_sets[3]), limits = (0, 300)))
            self.lcd_txt2 = NoSave(ConfigYesNo(default=str2bool(lcd_sets[4])))
            self.lcd_txt2_align = NoSave(ConfigSelection(choices = AlignType, default=lcd_sets[5] ))
            self.lcd_txt2_pos = NoSave(ConfigInteger(default = int(lcd_sets[6]), limits = (0, 1024)))			
            self.lcd_txt2_size = NoSave(ConfigInteger(default = int(lcd_sets[7]), limits = (10, 300)))			
            self.lcd_txt2_lines = NoSave(ConfigInteger(default = int(lcd_sets[8]), limits = (0, 5)))			
            self.lcd_txt1 = NoSave(ConfigYesNo(default=str2bool(lcd_sets[9])))
            self.lcd_txt1_align = NoSave(ConfigSelection(default=lcd_sets[10], choices = AlignType))
            self.lcd_txt1_pos = NoSave(ConfigInteger(default = int(lcd_sets[11]), limits = (0, 1024)))			
            self.lcd_txt1_size = NoSave(ConfigInteger(default = int(lcd_sets[12]), limits = (10, 300)))			
            self.lcd_txt1_lines = NoSave(ConfigInteger(default = int(lcd_sets[13]), limits = (0, 5)))
            self.lcd_txt3 = NoSave(ConfigYesNo(default=str2bool(lcd_sets[14])))
            self.lcd_txt3_align = NoSave(ConfigSelection(default=lcd_sets[15], choices = AlignType))
            self.lcd_txt3_pos = NoSave(ConfigInteger(default = int(lcd_sets[16]), limits = (0, 1024)))			
            self.lcd_txt3_size = NoSave(ConfigInteger(default = int(lcd_sets[17]), limits = (10, 300)))			
            self.lcd_txt3_lines = NoSave(ConfigInteger(default = int(lcd_sets[18]), limits = (0, 5)))
            self.lcd_logo = NoSave(ConfigYesNo(default=str2bool(lcd_sets[19])))
            self.lcd_logo_align = NoSave(ConfigSelection(default=lcd_sets[20], choices = AlignType))			
            self.lcd_logo_pos = NoSave(ConfigInteger(default = int(lcd_sets[21]), limits = (0, 1024)))
            self.lcd_logo_size = NoSave(ConfigInteger(default = int(lcd_sets[22]), limits = (0, 500)))			
            self.lcd_cover = NoSave(ConfigYesNo(default=str2bool(lcd_sets[23])))			
            self.lcd_cover_align = NoSave(ConfigSelection(default=lcd_sets[24], choices = AlignType))
            self.lcd_cover_pos = NoSave(ConfigInteger(default = int(lcd_sets[25]), limits = (0, 1024)))			
            self.lcd_cover_size = NoSave(ConfigInteger(default = int(lcd_sets[26]), limits = (0, 1024)))
            self.lcd_list_size = NoSave(ConfigInteger(default = int(lcd_sets[27]), limits = (0, 300)))
            self.lcd_pic_ers_size = NoSave(ConfigInteger(default = int(lcd_sets[28]), limits = (0, 300)))
            Farbe = [("black", _("black")), ("white", _("white")), 

                ("gray", _("gray")), ("silver", _("silver")), ("slategray", _("slategray")),
                ("aquamarine", _("aquamarine")),
                ("yellow", _("yellow")), ("greenyellow", _("greenyellow")), ("gold", _("gold")),
                ("red", _("red")), ("tomato", _("tomato")), ("darkred", _("darkred")), ("indianred", _("indianred")), ("orange", _("orange")), ("darkorange", _("darkorange")), ("orangered", _("orangered")),
                ("green", _("green")), ("lawngreen", _("lawngreen")), ("darkgreen", _("darkgreen")), ("lime", _("lime")), ("lightgreen", _("lightgreen")),
                ("blue", _("blue")), ("blueviolet", _("blueviolet")), ("indigo", _("indigo")), ("darkblue", _("darkblue")), ("cadetblue", _("cadetblue")), ("cornflowerblue", _("cornflowerblue")), ("lightblue", _("lightblue")),
                ("magenta", _("magenta")), ("violet", _("violet")), ("darkorchid", _("darkorchid")), ("deeppink", _("deeppink")), ("cyan", _("cyan")),
                ("brown", _("brown")), ("sandybrown", _("sandybrown")), ("moccasin", _("moccasin")), ("rosybrown", _("rosybrown")), ("olive", _("olive")),
                ]     
            self.lcd_txt_color = NoSave(ConfigSelection(choices = Farbe, default=str(lcd_sets[29]) ))

        Screen.__init__(self, session)
        if fontlist[9]:
                    self.skinName = "WebradioFSSetup_e"
        else:
            self.skin=self.skin.replace('backgroundColor="#000000"','')
            self.skin=self.skin.replace('foregroundColor="#ffffff"','')
            self.skinName = "WebradioFSSetup_13"
        self.abteil=abteil
        self.infos=infos
        self.stream_liste=[]
        dfe="0"
        if sets_grund["startstream1"]== -1:
            dfe= "-1"
        if sets_grund["startstream1"]== -2:
            dfe= "-2"
        if os.path.exists(myfav_file):
                connection = sqlite.connect(myfav_file)
                connection.text_factory = str
                cursor = connection.cursor()
                cursor.execute("select name, stream_id,defekt from streams;")
                for row in cursor:
                    if row[2]==0:
                            self.stream_liste.append((row[1], row[0]))
                            if sets_grund["startstream1"]>0:
                                if int(row[1]) == sets_grund["startstream1"]:
                                    dfe=row[1]
                cursor.close()
                connection.commit()
        self.stream_liste.sort(key=lambda x: x[1].lower())
        self.stream_liste.insert(0,("0",_("None")))
        self.stream_liste.insert(1,("-1",_("Remember last used")))
        if sets_opt["audiofiles"]:
            self.stream_liste.insert(2,("-2",_("My files")))
        self.startstream_tmp = NoSave(ConfigSelection(default=dfe, choices =self.stream_liste))
        self.volctrl = eDVBVolumecontrol.getInstance()
        if self.al_vol_max.value==5:
            self.al_vol_max.value=self.volctrl.getVolume()

        found=0
        for x in saver_list:
            if sets_scr["screensaver_art"]==x[0]:
                  found=1
        if found==0:
            sets_scr["screensaver_art"]="wechsel"
        self.oldpath=self.favpath.value
        self.onChangedEntry = [ ]
        
        self["rec_txt"] = Label("")
        self["playtext"] = StaticText("")
        self["green_pic"] = Pixmap() 
        ConfigListScreen.__init__(self, [], session = session, on_change = self.reloadList)     #, on_change = self.reloadList
        self["config"].onSelectionChanged.append(self.setHelp)
        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("Save"))
        self["key_yellow"] = Label("")
        self["key_blue"] = Label("")
        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
        {
            "green": self.check,
            "ok": self.press_ok,
            "red": self.cancel,
            "cancel": self.cancel
        }, -2)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self.onLayoutFinish.remove(self.layoutFinished)
        self.instance.setZPosition(2)
        if fontlist[8] or fontlist[9]:
          try:
            if not fontlist[4]: 
                self['config'].instance.setFont(fontlist[3])
                self['config'].instance.setItemHeight(fontlist[2]) 
            else:
                    from skin import parseFont
                    stylemgr = eWindowStyleManager.getInstance()
                    skinned = eWindowStyleSkinned()
                    eListboxPythonConfigContent.setDescriptionFont(parseFont(conf_font1, ((1,1),(1,1))))
                    eListboxPythonConfigContent.setValueFont(parseFont(conf_font2, ((1,1),(1,1))))
                    eListboxPythonConfigContent.setItemHeight(conf_item)
                    stylemgr.setStyle(0, styleskinned)
          except:
                pass
        self.refresh()
        self.reloadList()
        self.setTitle(_("webradioFS - Settings"))

    def startstream(self):
                l=[]
                for x in self.stream_liste:
                  l.append((x[1],x[0]))
                right_site.hide()
                self.session.openWithCallback(self.startsel,ChoiceBox,_("Select Stream for automatic start"),list = (l))

    def startsel(self,ret):
        right_site.show()
        if ret:
           w1="web,"+str(ret[1])
           if int(ret[1])<1:
              w1=ret[1]+","+str(ret[0])
           starter_set(akt="write",wert=w1)
           self.startstream_tmp.setValue(ret[1])
           self.refresh()

    def refresh(self,meld=None):
        self.list = []
        self["key_blue"].setText("")
        if self.abteil=="all":
            self["rec_txt"].setText(_("Settings-basics"))
            self.list.extend((
              getConfigListEntry(_("Scope of possible options / settings"), self.opt_expert),   #getConfigListEntry(_("Enable Expert settings"), self.opt_expert),
              getConfigListEntry((" "),),
              getConfigListEntry(_("start stream automatically:"), self.startstream_tmp),
              getConfigListEntry(_("Picture search"), self.picsearch),
              getConfigListEntry(_("Show webradioFS in mainmenu:"),self.hauptmenu),
              getConfigListEntry(_("Ignore skin:"),self.skin_ignore),
              ))
            if self.opt_expert.value>0:
                  self.list.extend((
                      getConfigListEntry(_("Show webradioFS in extensionsmenu:"),self.exttmenu),
                  ))
            if self.opt_expert.value>0:
              self.list.extend((
                getConfigListEntry((" "),),
                getConfigListEntry((">> "+_("View")+" <<"),),
                ))
              if self.picsearch.value != "off":  
                self.list.extend((
                  getConfigListEntry(_("Images Additional search word")+" [OK]", self.picwords1),
                  getConfigListEntry(_("Images Additional search word at the end")+" [OK]", self.picwords2),
                  getConfigListEntry(_("Exclude search word")+" [OK]", self.picwords3),
                ))
              self.list.extend((
                  getConfigListEntry(_("Sorting Stream List:"), self.stream_sort),
                  getConfigListEntry(_("Picons for Streams:"), self.logos),   
                  getConfigListEntry(_("Picons in List:"), self.Listlogos),
                  ))
            if self.opt_expert.value>0:
              self.list.extend((
                getConfigListEntry((" "),),
                getConfigListEntry((">> "+_("Path-options")+" <<"),),
                getConfigListEntry(_("File path for Favorites:"), self.favpath),
                getConfigListEntry(_("File path for Picons:"), self.logopath),
                getConfigListEntry(_("File path for PVR-logos:"), self.wbrfspvrpath),
                getConfigListEntry(_("Storage path for cover and title:"),self.coversafepath),
                getConfigListEntry(_("Path for record"),self.rec_path),
                ))
            if self.opt_expert.value>0:
              self.list.extend((
                getConfigListEntry((" "),),
                getConfigListEntry((">> "+_("Volume-options")+" <<"),),
                getConfigListEntry(_("Volume on start:")+ " (0=off)", self.start_vol),
                getConfigListEntry(_("Time for auto-volume steps (0=off):"), self.vol_auto_time),
                getConfigListEntry(_("max Volume on chill-end:"),self.al_vol_max),
                getConfigListEntry((" "),),
                getConfigListEntry((">> "+_("other")+" <<"),),
                getConfigListEntry(_("Blocking inactivity off timer (system):"), self.stop_abschalt),
                getConfigListEntry(_("Timeout for connection attempt:"), self.timeout),
                getConfigListEntry(_("Timeout for stream termination:"), self.conwait),
                getConfigListEntry(_("Number of connection attempts:"), self.reconnect),
                getConfigListEntry(_("Off Timer (minutes):"), self.offtimer_time),
                getConfigListEntry(_("Result for Off-Timer (Standby/Deepstandby):"), self.offtimer_art),
                getConfigListEntry(_("Question before exiting?"),self.exitfrage),
                getConfigListEntry(_("Write debug:"), self.debug),
                ))
            if sispmctl and self.opt_sispmctl.value:
              self.list.extend((            
                getConfigListEntry((" "),),
                getConfigListEntry(_("sispmctl Menu Name 1:"),self.sismctl_nvers1),
                getConfigListEntry(_("sispmctl Switching Menu 1:"),self.sismctl_vers1),
                getConfigListEntry(_("sispmctl Menu Name 2:"),self.sismctl_nvers2),
                getConfigListEntry(_("sispmctl Switching Menu 2:"),self.sismctl_vers2),
                getConfigListEntry((" "),),
                getConfigListEntry(_("Set sispmctl on start:"),self.sismctl_start),
                getConfigListEntry(_("Set sispmctl on exit:"),self.sismctl_exit),
                getConfigListEntry(_("Set sispmctl when saver on:"),self.sismctl_ssr1),
                getConfigListEntry(_("Set sispmctl when saver off:"),self.sismctl_ssr2),
                ))
        elif self.abteil=="audiofiles":
                if self.audio_save_random==True:
                   self.audio_sort.value=False
                self.list.extend((
                    getConfigListEntry(_("default directory")+_(" (Press OK)"), self.audiopath),
                    getConfigListEntry(_("Play files from sub-dirs"), self.audio_subdirs),
                    getConfigListEntry(_("Play random"), self.audio_sort),
                    getConfigListEntry(_("Auto play"), self.audio_autoplay),
                    getConfigListEntry(_("Auto play endless"), self.audio_schleife),
                    getConfigListEntry(_("Save list in random order"), self.audio_save_random),
                    getConfigListEntry(_("Save position in list"), self.audio_listpos),
                ))
        elif self.abteil=="moduls":
                self["rec_txt"].setText(_("Additional functions on / off"))
                self.list.extend((
                  getConfigListEntry(_("Enable Screensaver options menu"), self.opt_scr),
                  getConfigListEntry(_("Enable display settings menu"), self.opt_display),
                  getConfigListEntry(_("Enable record functions menu"), self.opt_rec),
                  getConfigListEntry(_("Enable Audio-file playing menu"), self.opt_audfile),
                  getConfigListEntry(_("Enable change assignment of keys menu"), self.opt_tasten),
                  getConfigListEntry(_("Enable sispmctl settings menu"), self.opt_sispmctl),
                ))
                if l4l:
                    self.list.append(getConfigListEntry(_("Enable external display settings menu"), self.opt_lcr))
        elif self.abteil=="scr":
          self["rec_txt"].setText(_("Screensaver-Settings"))
          art= self.screensaver_art.value
          if self.screensaver_art.value.startswith("not"):
                   self.screensaver_art.value="wechsel"
          self.list.append(getConfigListEntry(_("Screensaver-Art:")+_(" (Press OK)"), self.screensaver_art))
          if not art.startswith("not"):    
              self.list.append(getConfigListEntry(_("Time (sec) to screen saver:"), self.wbrScreenSaver))
              if 1==1:          
                if art=="Play_Video_sort" or art=="Play_Video_rand":
                   self.list.append(getConfigListEntry(_("Video Path:")+_(" (Press OK)"), self.wbrvideopath))
                elif art=="Play_Video":
                   self.list.append(getConfigListEntry(_("Video File:"), self.wbrvideofile))
                if art.startswith("Play_Video"):
                   self.list.append(getConfigListEntry(_("Second to recurrence:"), self.wbrvideorecurr))
                elif art !="black" and art !="pcfs_slideshow" and art !="sispmctl" and art != "picscreensaver" and art != "tv":
                  self.list.append(getConfigListEntry(_("Fixed position for text and cover"), self.wbrSStextfix))
                  self.list.append(getConfigListEntry(_("Colors from skin"), self.colfromskin))
                  if self.colfromskin.value != True:
                      self.list.append(getConfigListEntry(_("Color screensaver labels")+_(" (Press OK)"), self.wbrSScolor))
                      self.list.append(getConfigListEntry(_("Color screensaver background")+_(" (Press OK)"), self.wbrSSbgcolor))
                      self.list.append(getConfigListEntry(_("Color random"), self.wbrSSbgcolor_random))        
                  if self.screensaver_art.value=="slideshow_sorted" or self.screensaver_art.value=="slideshow_random":
                      self.list.extend((
                        getConfigListEntry(_("backround color:"), self.slideshow_bgcolor),
                        getConfigListEntry(_("Slideshow Path:"), self.wbrslideshowpath),
                        getConfigListEntry(_("Text-space:"), self.slideshow_space),            
                        getConfigListEntry(_("Show subdirs:"), self.slideshow_subdirs),
                        getConfigListEntry(_("Toggle-Time:"), self.slideshow_time),         
                        ))
                  else:
                    if self.screensaver_art.value !="no picture":
                        if self.screensaver_art.value =="theme_images":
                            self.list.append(getConfigListEntry(_("Keyword(s) for Picture:"), self.wbrSSKeyword))                    
                elif self.screensaver_art.value=="pcfs_slideshow":
                  self.list.append(getConfigListEntry(_("Slideshow Path:"), self.wbrslideshowpath))
        elif self.abteil=="rec":
            self["rec_txt"].setText(_("Record-Settings"))
            self.list.extend((
                getConfigListEntry("<< "+_("Set caching individually in stream settings")+" >>",self.fake_entry),
                getConfigListEntry(_("Path for record"),self.rec_path),
                getConfigListEntry(_("Path for caching"),self.rec_caching_dir), 
                getConfigListEntry(_("Show *rec* when record"), self.rec_anzeige),
                getConfigListEntry(_("Make subdir for record"), self.rec_new_dir),
                getConfigListEntry(_("Split recording with event"), self.rec_split),
                getConfigListEntry(_("Save on recording a found image automatically"), self.rec_cover),
                getConfigListEntry(_("store recordings of incompleteness"), self.inclp_save),
                ))
        elif l4lR and self.abteil=="l4l":
            self["rec_txt"].setText(_("LCD4linux-Settings")+" ("+_("for external display")+")")       #str(self.lcd_txt1_lines.value)
            self.logo=plugin_path+"/skin/images/webradiofs.png"
            self.list.extend((
                getConfigListEntry(_("LCD4linux-Settings")+":",),
                getConfigListEntry(_("Show on LCD"),self.lcd_on),
                getConfigListEntry(_("Set LCD"),self.lcd_nr),
                getConfigListEntry(_("Stop screen toggle"),self.lcd_stop),
                getConfigListEntry(_("Set screen"),self.lcd_screen),
                getConfigListEntry("",),
                getConfigListEntry(_("Show infotext"),self.lcd_txt2),
                getConfigListEntry(_("Align"),self.lcd_txt2_align),
                getConfigListEntry(_("Position"),self.lcd_txt2_pos),
                getConfigListEntry(_("Size"),self.lcd_txt2_size),
                getConfigListEntry(_("Lines"),self.lcd_txt2_lines),
                getConfigListEntry("",),
                getConfigListEntry(_("Show Station-Name"),self.lcd_txt1),
                getConfigListEntry(_("Align"),self.lcd_txt1_align),
                getConfigListEntry(_("Position"),self.lcd_txt1_pos),
                getConfigListEntry(_("Size"),self.lcd_txt1_size),
                getConfigListEntry(_("Lines"),self.lcd_txt1_lines),
                getConfigListEntry("",),
                getConfigListEntry(_("Show Fav-group name"),self.lcd_txt3),
                getConfigListEntry(_("Align"),self.lcd_txt3_align),
                getConfigListEntry(_("Position"),self.lcd_txt3_pos),
                getConfigListEntry(_("Size"),self.lcd_txt3_size),
                getConfigListEntry(_("Lines"),self.lcd_txt3_lines),
                getConfigListEntry("",),
                getConfigListEntry(_("Show logo"),self.lcd_logo),
                getConfigListEntry(_("Align"),self.lcd_logo_align),
                getConfigListEntry(_("Position"),self.lcd_logo_pos),
                getConfigListEntry(_("Size"),self.lcd_logo_size),
                getConfigListEntry("",),
                getConfigListEntry(_("Show picture/cover"),self.lcd_cover),
                getConfigListEntry(_("Align"),self.lcd_cover_align),
                getConfigListEntry(_("Position"),self.lcd_cover_pos),
                getConfigListEntry(_("Size"),self.lcd_cover_size),
                getConfigListEntry("",),
                getConfigListEntry(_("Text-Size in list"),self.lcd_list_size),
                getConfigListEntry(_("Text-Size if no logo"),self.lcd_pic_ers_size),
                getConfigListEntry(_("Text-color"),self.lcd_txt_color),
                ))
        self["config"].setList(self.list)

    def meld_screen(self,text,titel,timeout=0,type1="INFO",aktion=None,default=True):
            self.mtitel=titel
            self.type1=type1
            self.stream_info=type1+": "+text.split("\n")[0]
            melde_screen.start(text,titel,aktion,default,type1,timeout,sd)
            self.meldung1=True

    def meldung_back(self,answer=0):
        m1=melde_screen.stop()
        self.meldung1=None
        b1=None
        if m1 and len(m1) and m1[1] != 0:
                if self.type1=="??":
                    b1=m1[1](m1[2])
                elif m1[2] == True: 
                    b1=m1[1]()
        self.stream_info=self.orig_stream_info
        self.selectionChanged()
        if b1: b1

    def setHelp(self):
               self.cur = self["config"].getCurrent()
               cur = self.cur and self.cur[1]
               if self.abteil=="moduls":
                    self["playtext"].setText(_("When activated: set the options for this in the settings!\nWhen deactivated: the settings remain active!"))
               elif cur==self.startstream_tmp:
                  self["playtext"].setText(_("Press OK for select"))
               elif cur==self.screensaver_art or cur==self.wbrvideopath:
                  self["playtext"].setText(_("Video or live TV are not available on all boxes") )
               elif cur== self.wbrScreenSaver:
                  self["playtext"].setText(_("000 = off") )
               elif cur== self.stop_abschalt:
                   self["playtext"].setText(_("When activated: block automatic shutdown from system when inactive") )
               else:
                 self["playtext"].setText(str(self["config"].getCurrent()[0]))

    def reloadList(self):
        if l4lR and self.abteil=="l4l":
          try:  
            if self.lcd_on.value==True:
                L4LwbrFS.delete("wbrFS.02.pic1")
                L4LwbrFS.delete("wbrFS.01.txt1")
                L4LwbrFS.delete("wbrFS.03.txt3")
                L4LwbrFS.delete("wbrFS.02.txt2")
                L4LwbrFS.delete("wbrFS.01.pic2")
                L4LwbrFS.delete("wbrFS.05.box1")
                L4LwbrFS.delete("wbrFS.06.txt5")
                L4LwbrFS.delete("wbrFS.07.box7")
                L4LwbrFS.delete("wbrFS.08.txt8")
                lcd=str(self.lcd_nr.value)
                screen=str(self.lcd_screen.value)
                col=self.lcd_txt_color.value
                if self.lcd_logo.value==True:L4LwbrFS.add( "wbrFS.02.pic1",{"Typ":"pic","Transp":"True","Align": str(self.lcd_logo_align.value) ,"Pos":self.lcd_logo_pos.value,"File":self.logo,"Size":self.lcd_logo_size.value,"Screen":screen,"Lcd":lcd,"Mode":"OnMedia"} )
                if self.lcd_txt1.value==True:L4LwbrFS.add( "wbrFS.01.txt1",{"Typ":"txt","Align": str(self.lcd_txt1_align.value),"Color":col ,"Text":"Station","Pos":self.lcd_txt1_pos.value,"Size":self.lcd_txt1_size.value,"Lines":self.lcd_txt1_lines.value,"Screen":screen,"Lcd":lcd,"Mode":"OnMedia"} )
                if self.lcd_txt3.value==True:L4LwbrFS.add( "wbrFS.03.txt3",{"Typ":"txt","Align": str(self.lcd_txt3_align.value),"Color":col ,"Text":"Fav-Group","Pos":self.lcd_txt3_pos.value,"Size":self.lcd_txt3_size.value,"Lines":self.lcd_txt3_lines.value,"Screen":screen,"Lcd":lcd,"Mode":"OnMedia"} )                
                if self.lcd_txt2.value==True:L4LwbrFS.add( "wbrFS.02.txt2",{"Typ":"txt","Align": str(self.lcd_txt2_align.value),"Color":col ,"Text":"Infotext","Pos":self.lcd_txt2_pos.value,"Size":self.lcd_txt2_size.value,"Lines":self.lcd_txt2_lines.value,"Screen":screen,"Lcd":lcd,"Mode":"OnMedia"} )                
                if self.lcd_cover.value==True:L4LwbrFS.add( "wbrFS.01.pic2",{"Typ":"pic","Align": str(self.lcd_cover_align.value) ,"Pos":self.lcd_cover_pos.value,"File":self.logo,"Size":self.lcd_cover_size.value,"Screen":screen,"Lcd":lcd,"Mode":"OnMedia"} )
                L4LwbrFS.setScreen(str(self.lcd_screen.value),str(self.lcd_nr.value),True)
                L4LwbrFS.setHoldKey(True)
                self.refresh()
          except:
             pass
        else:
          try:
            if not self.cur[0] in (_("Color screensaver labels")+_(" (Press OK)"),_("Color screensaver background")+_(" (Press OK)"),_("backround color:")):
               self.refresh()
               self["config"].setList(self.list)
          except:
              pass

    def check(self):
            self.check2()

    def check2(self,args=None):
        right_site.show()
        try:
            if self.abteil=="all":
                path=self.coversafepath.value
                if path is not None:
                    if not path.endswith('/'):
                        path=path+'/'
                    if not path.startswith('/'):
                        path='/'+path
                    if not os.path.exists(path):
                        os.makedirs(path)
            self.save()
        except OSError:
            self.session.open(MessageBox, _("Sorry your path destination is not writeable.\nPlease choose an other one."), type = MessageBox.TYPE_INFO)

    def save(self):
      sets=None
      global sets_opt
      global sets_scr
      global sets_rec
      global sets_audiofiles
      global sets_grund,sets_view,sets_prog,sets_exp,sets_opt,sets_rec
      if self.abteil=="all":
            if self.opt_expert.value>1:
                sets_opt={"rec":True,"views":True,"expert":2,"scr":True,"lcr":True,"audiofiles":True,"display":True,
                         "tasten":True,"sispmctl":True}
                write_settings((("opt",sets_opt),))
            elif self.opt_expert.value<1:
                sets_opt={"rec":False,"views":False,"expert":0,"scr":False,"lcr":False,"audiofiles":False,"display":False,
                         "tasten":False,"sispmctl":False}
            else:
                sets_opt["expert"]=1
            sets_prog["hauptmenu"]=self.hauptmenu.value
            sets_prog["exttmenu"]=self.exttmenu.value
            sets_rec["path"]= self.rec_path.value
            sets_grund={"picsearch":self.picsearch.value,"favpath":self.favpath.value,"exitfrage":self.exitfrage.value,
            "stream_sort":self.stream_sort.value,"wbrbackuppath":self.wbrbackuppath.value,"startstream1":self.startstream_tmp.value,"skin_ignore":self.skin_ignore.value}
            sets_exp={"reconnect":self.reconnect.value,"versions_info":False,"timeout":self.timeout.value,"conwait":self.conwait.value,
                   "logopath":self.logopath.value,"coversafepath":self.coversafepath.value,"debug":self.debug.value,
                   "FBts_liste":sets_exp["FBts_liste"],"al_vol_max":self.al_vol_max.value,"start_vol":self.start_vol.value,"vol_auto_time":self.vol_auto_time.value,
                   "picwords1":self.picwords1.value,"picwords2":self.picwords2.value,"picwords3":self.picwords3.value,"offtimer_time":self.offtimer_time.value,
                   "offtimer_art":self.offtimer_art.value,"wbrfspvrpath":self.wbrfspvrpath.value,"min_bitrate":0,"stop_abschalt":self.stop_abschalt.value}
            sets_view={"logos":self.logos.value,"Listlogos":self.Listlogos.value,"only_foto":self.wbrSSfoto.value,"displayb":sets_view["displayb"],"l4l":sets_view["l4l"]}
            write_settings((("opt",sets_opt),("grund",sets_grund),("prog",sets_prog),("exp",sets_exp),("view",sets_view),("rec",sets_rec)))
      elif self.abteil=="moduls":
            sets_opt={"rec":self.opt_rec.value,"views":sets_opt["views"],"expert":sets_opt["expert"],"scr":self.opt_scr.value,"lcr":self.opt_lcr.value,"audiofiles":self.opt_audfile.value,"display":self.opt_display.value,
                         "tasten":self.opt_tasten.value,"sispmctl":self.opt_sispmctl.value}
            write_settings((("opt",sets_opt),))
      elif self.abteil=="scr":
               sets_scr={"screensaver_art":self.screensaver_art.value,"color":self.wbrSScolor.value,"foto":False,"bgcolor":self.wbrSSbgcolor.value,
               "bgcolor_random":self.wbrSSbgcolor_random.value,"slideshow_bgcolor":self.slideshow_bgcolor.value,"Keyword":self.wbrSSKeyword.value,
               "slideshow_time":self.slideshow_time.value,"slideshowpath":self.wbrslideshowpath.value,"slideshow_subdirs":self.slideshow_subdirs.value,
               "slideshow_space":self.slideshow_space.value,"timeout":self.wbrScreenSaver.value,"wbrvideorecurr":self.wbrvideorecurr.value,
               "wbrvideopath":self.wbrvideopath.value,"wbrvideofile":self.wbrvideofile.value,"textfix":self.wbrSStextfix.value,"colfromskin":self.colfromskin.value}
               write_settings( ( ("scr",sets_scr), ) )
      elif self.abteil=="rec":
               sets_rec={"path":self.rec_path.value,"split":self.rec_split.value,"new_dir":self.rec_new_dir.value,"cover":self.rec_cover.value,"anzeige":self.rec_anzeige.value,"inclp_save":self.inclp_save.value,"rec_caching_dir":self.rec_caching_dir.value}
               write_settings((("rec",sets_rec),))
      elif self.abteil=="opt":
               sets_opt={"rec":self.opt_rec.value,"views":sets_opt["views"],"expert":sets_opt["expert"],"scr":self.opt_scr.value,"lcr":self.opt_lcr.value,"audiofiles":self.opt_audfile.value,"display":self.opt_display.value,
                         "tasten":self.opt_tasten.value,"sispmctl":self.opt_sispmctl.value}
               write_settings((("opt",sets_opt),))
      elif self.abteil=="audiofiles":
               sets_audiofiles={"audiopath":self.audiopath.value,"subdirs":self.audio_subdirs.value,"autoplay":self.audio_autoplay.value,"sort":self.audio_sort.value,
                     "audio_listpos":self.audio_listpos.value,"save_random":self.audio_save_random.value,"audio_listnums":sets_audiofiles["audio_listnums"],"schleife":self.audio_schleife.value}
               write_settings((("audiofiles",sets_audiofiles),))
      elif self.abteil=="l4l":
        save_list=[]
        for x in self["config"].list:
            if len(x)>1:save_list.append(x[1].value)
        sv1 = ','.join(str(i) for i in save_list)
        sets_view["l4l"]= sv1
        write_settings((("view",sets_view),))
      alles_gut=0
      if myfav_file !=self.favpath.value+ "webradioFS_favs.db":
              try:
                if not os.path.exists(self.favpath.value+ "webradioFS_favs.db"):
                    copyfile(myfav_file, self.favpath.value+ "webradioFS_favs.db")
                restart=1
              except:
                self.favpath.value = self.oldpath
                self.session.open(MessageBox, _("can not copy Fav-File on new path"), type = MessageBox.TYPE_INFO)
      testcol= self.test_col()
      if self.screensaver_art.value.startswith("not"):
           self.session.openWithCallback(self.refresh, MessageBox, _("Plugin for screensaver not installed"), MessageBox.TYPE_INFO)
      elif testcol:
           self.session.openWithCallback(self.refresh, MessageBox, _("Sorry, color-Code is failed, settig default"), type = MessageBox.TYPE_INFO)
      else:
            alles_gut=1
      right_site.show()
      self.close(True,"tools")

    def leer(self):
        pass

    def press_ok(self):
        testcol = 0
        try:
                self["config"].getCurrent()[1].help_window.instance.hide()
        except:
               pass
        self.cur = self["config"].getCurrent()
        if self.cur[1] in(self.coversafepath,self.wbrfspvrpath,self.wbrslideshowpath,self.rec_path,self.wbrvideopath,self.favpath,self.logopath,self.audiopath,self.rec_caching_dir):
            self.path_wahl()
        elif self.cur[1] == self.screensaver_art:
                tmp_list=[]
                for x in saver_list:
                    tmp_list.append((x[1],x[0]))
                right_site.hide()
                self.session.openWithCallback(self.list_sel,  ChoiceBox, title=_("webradioFS - select screensaver"), list=tmp_list)
        elif self.cur[1] in (self.picwords1,self.picwords2,self.picwords3,self.wbrSSKeyword,self.slideshow_bgcolor):
            self.texteingabe()
        elif self.cur[1] in (self.wbrSScolor,self.wbrSSbgcolor):
            testcol= self.test_col()
            if testcol:
                self.session.openWithCallback(self.refresh, MessageBox, _("Sorry, color-Code is failed, settig default"), type = MessageBox.TYPE_INFO)
            else:
                from .wbrfscol import wbrfs_col_13
                self.session.openWithCallback(self.set_text_col,wbrfs_col_13,self.wbrSScolor.value,self.wbrSSbgcolor.value,self.infos)
        elif self.cur[1] == self.startstream_tmp:
                self.startstream()
        elif self.cur[1] == self.wbrvideofile:
                self.session.openWithCallback(self.texteingabeFinished,wbrfs_filelist)

    def set_text_col(self, text_col=None,back_col=None):
        if back_col and text_col:
            self.wbrSScolor.value=text_col
            self.wbrSSbgcolor.value=back_col

    def test_col(self):
            col_sets2=(self.wbrSScolor,self.wbrSSbgcolor,self.slideshow_bgcolor)
            col1=("ffffff","000000","000000")
            num=0
            col_err=0
            for x in col_sets2:
                try:
                    cl=gRGB(int(str(x.value), 0x10))
                except:
                    x.value = col1[num]
                    col_err=1
                num+=1
            return col_err

    def list_sel(self,auswahl):
            right_site.show()
            if auswahl is not None and not auswahl[1].startswith("not"):
                   self.screensaver_art.value=str(auswahl[1])
                   self.refresh()

    def texteingabe(self):
             right_site.hide()
             titel=None
             if self.cur[1] in (self.picwords3,self.wbrSSKeyword,self.slideshow_bgcolor,self.picwords1,self.picwords2):
                text1=self.cur[1].value
                titel=self.cur[0]
             if titel:
                    self.session.openWithCallback(self.texteingabeFinished,VirtualKeyBoard, title=titel, text=text1) #, maxSize=max_laenge, type=typ1)

    def texteingabeFinished(self, ret):
                right_site.show()
                if ret is not None:
                    if self.cur[1] ==  self.slideshow_bgcolor:
                        if "#" in ret[0]: ret=ret.replace("#","")
                        if len(ret)==6 or len(ret)==8:
                            self.slideshow_bgcolor.value=ret
                        else:
                            self.session.open(MessageBox, _("Input failed, color sample for with: ffffff, for black: 000000"), MessageBox.TYPE_ERROR)
                    else:
                        if self.cur[1]==self.picwords1:
                            self.pw1= [(ret,ret)]
                            self.picwords1 = NoSave(ConfigSelection(default = ret, choices = self.pw1))
                        elif self.cur[1]==self.picwords2:
                            self.pw2= [(ret,ret)]
                            self.picwords2 = NoSave(ConfigSelection(default = ret, choices = self.pw2))
                        elif self.cur[1]==self.picwords3:
                            self.pw3= [(ret,ret)]
                            self.picwords3 = NoSave(ConfigSelection(default = ret, choices = self.pw3))
                        self.cur[1].value = ret
                        self.refresh()

    def callAuswahl(self,path):
        right_site.show()
        if path is not None:
            if os.path.exists(path):
                    if self["config"].getCurrent()[1] != self.favpath:
                        self["config"].getCurrent()[1].value=path
                    else:    
                        try:
                            if self["config"].getCurrent()[1] == self.favpath:
                                if fileExists(path+"/webradioFS_favs.db"):
                                    self["config"].getCurrent()[1].value=path
                                else:
                                    self.tmp_path=path
                                    self.session.openWithCallback(self.u_path,MessageBox, _("Create a new subdirectory?"), MessageBox.TYPE_YESNO)
                            else:
                                self.tmp_path=path
                                self.session.openWithCallback(self.u_path,MessageBox, _("Create a new subdirectory?"), MessageBox.TYPE_YESNO)
                        except:
                            err=1
                            self.session.open(MessageBox, _("Path")+"\n"+path+"\n "+_("not writable!"), MessageBox.TYPE_ERROR)

    def u_path(self,answer):
        if answer == True:
            self.session.openWithCallback(self.u_path2, InputBox, title=_("Name for new subdirectory"), text="webradioFS", maxSize=False, type=Input.TEXT)
        else:
            self.u_path2()

    def u_path2(self,answer=None):
        if answer and len(answer):
            if not os.path.exists(self.tmp_path+answer):
                os.mkdir(self.tmp_path+answer)
            if not self.tmp_path.endswith("/"):self.tmp_path=self.tmp_path+"/"
            self.tmp_path=self.tmp_path+answer
        self["config"].getCurrent()[1].value=self.tmp_path#+"/"
        if not fileExists(self.tmp_path+"/webradioFS_favs.db") and self["config"].getCurrent()[1] == self.favpath:
                 ret = copyfile(self.oldpath+"webradioFS_favs.db", self.tmp_path +"/webradioFS_favs.db")

    def path_wahl(self):
        text= _("Please select Path")
        if self["config"].getCurrent()[1] == self.favpath:
            savepath=self.favpath.value
            text= _("Please select Save-Path for favorites...")
        elif self["config"].getCurrent()[1] == self.coversafepath:
           savepath=self.coversafepath.value
           text=_("Please select Save-Path for cover and titles...")
        elif self["config"].getCurrent()[1] == self.logopath:
           savepath=self.logopath.value
           text=_("Please select path for stream-logos...")
        elif self["config"].getCurrent()[1] == self.wbrfspvrpath:
           savepath=self.wbrfspvrpath.value
           text=_("Please select your image picon-path...")
        elif self["config"].getCurrent()[1] == self.audiopath:
           savepath=self.audiopath.value
           text=_("Please select startpath for audiofiles...")
        elif self["config"].getCurrent()[1] == self.rec_caching_dir:
           savepath=self.rec_caching_dir.value
           text=_("Please select path for caching...")
        right_site.hide()
        self.session.openWithCallback(self.callAuswahl,SaveLocationBox,text,"","/",ConfigLocations(default=[self["config"].getCurrent()[1].value]))

    def cancel(self):
                for x in self["config"].list:
                    try:
                        x[1].cancel()
                    except:
                        pass
                right_site.show()
                if self.abteil=="moduls":
                     self.close(False,"moduls")
                else:
                     self.close(False,"tools")


class WebradioFS_FB_Setup_13(Screen, ConfigListScreen):
    def __init__(self, session):
        tmpskin = open(fontlist[5]+"wbrFS_setup.xml")
        self.skin = tmpskin.read()
        tmpskin.close()
        if skin_ext==plugin_path +"/skin/SD/": 
            right_site.hide()
        self.FBts= NoSave(ConfigSet(default=sets_exp["FBts_liste"].split(","),choices=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23.24]))
        self.t_liste= sets_exp["FBts_liste"].split(",")
        self["rec_txt"] = Label("webradioFS - " +_("RemoteControl-Settings"))
        self["playtext"] = StaticText("")
        self["green_pic"] = Pixmap()
        Screen.__init__(self, session)
        if fontlist[9]:
                    self.skinName = "WebradioFSSetup_e"
        else:
            self.skin=self.skin.replace('backgroundColor="#000000"','')
            self.skin=self.skin.replace('foregroundColor="#ffffff"','')
            self.skinName = "WebradioFSSetup_13"
        ConfigListScreen.__init__(self, [], session = session)
        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("Save"))
        self["pic_red"] = Pixmap()
        self["pic_green"] = Pixmap()
        self["pic_yellow"] = Pixmap()
        self["pic_blue"] = Pixmap()
        self["pic_blue"].hide()
        self["key_yellow"] = Label("Set defaults")
        self["key_blue"] = Label("")
        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
        {
            "green": self.save,
            "ok": self.auswahl,
            "red": self.cancel,
            "cancel": self.cancel,
            "yellow": self.defaults
        }, -2)
        self.setTitle("webradioFS - " +_("RemoteControl-Settings"))
        FB_conf = []
        tnum=0
        for x in tasten_name:
            if tnum<len(self.t_liste) and tnum<len(FBts_liste):
               lnum=int(self.t_liste[tnum])
               vars(self)[x] = NoSave(ConfigSelection(default = lnum, choices = FBts_liste))
               FB_conf.append(getConfigListEntry(_(x), vars(self)[x]))
            else:
               vars(self)[x] = NoSave(ConfigSelection(default = 0, choices = FBts_liste))
               FB_conf.append(getConfigListEntry(_(x), vars(self)[x]))
            tnum+=1
        ConfigListScreen.__init__(self, FB_conf, session)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self.onLayoutFinish.remove(self.layoutFinished)
        self.instance.setZPosition(2)
        if fontlist[8] or fontlist[9]:
          try:
            if not fontlist[4]:
                self['config'].instance.setFont(fontlist[3])
                self['config'].instance.setItemHeight(conf_item)
            else:
                    from skin import parseFont
                    stylemgr = eWindowStyleManager.getInstance()
                    skinned = eWindowStyleSkinned()
                    eListboxPythonConfigContent.setDescriptionFont(parseFont(conf_font1, ((1,1),(1,1))))
                    eListboxPythonConfigContent.setValueFont(parseFont(conf_font2, ((1,1),(1,1))))
                    eListboxPythonConfigContent.setItemHeight(conf_item)
                    stylemgr.setStyle(0, styleskinned)
          except:
              pass

    def auswahl(self): 
                list7=[]
                for x in FBts_liste:
                    list7.append((_(x[1]),x[0]))
                self.session.openWithCallback(self.auswahlFinished, ChoiceBox, title=_("fb"), list=list7)

    def auswahlFinished(self, ret):
         if ret is not None and len(ret)==2:
             self["config"].getCurrent()[1].value=ret[1]

    def defaults(self):
        FB_conf = []
        xnr=0
        for x in self["config"].list:
           x[1].value=xnr
           FB_conf.append(x)
           xnr=xnr+1
        FBts=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]
        self["config"].setList(FB_conf)

    def save(self):
        save_list=[]
        for x in self["config"].list:
             save_list.append(x[1].value)
        sv1 = ','.join(str(i) for i in save_list)
        global sets_exp
        sets_exp["FBts_liste"]=sv1
        write_settings((("exp",sets_exp),))

    def save2(self,answer):
        if answer == True:
           self.session.open(TryQuitMainloop, 3)
        else:
           self.close(False,"tools")

    def cancel(self):
        self.close(False,"tools")


class SaveLocationBox(LocationBox):
        def __init__(self, session, text, filename, dir,  save_path, minFree = None):
                inhibitDirs = ["/bin", "/boot", "/dev", "/lib", "/proc", "/sbin", "/sys"]   #, "/var"
                LocationBox.__init__(self, session, text = text, currDir = dir, bookmarks = None, editDir = False, inhibitDirs = inhibitDirs, minFree = minFree)
                self.skinName = "LocationBox"


class wbrScreenSaver_13(Screen, HelpableScreen, InfoBarNotifications):
    def __init__(self, session, text="", text2="",record=None,rec_cover=False,thema="",art=None,titel="webradioFS",playlist=None,logo=None,rec_art=None,display_on=True,exit_art=None,standby_aktion=None):
        right_site.hide()
        global onwbrScreenSaver
        if fileExists("/etc/ConfFS/wbrfs_usersaver.xml"): 
            tmpskin = "/etc/ConfFS/wbrfs_usersaver.xml"
        else:        
            tmpskin = open(skin_ext+"wbrFS_screensaver.xml")
        self.skin = tmpskin.read()

        tmpskin.close()
        self.onlyPhoto=""
        self.display_on=display_on
        if sets_view["only_foto"]:
                    self.onlyPhoto="&imgtype=photo"
        self.bildthema=thema
        self.logo=logo
        self.rec_cover= rec_cover
        self.record2= record
        self.rec_art=rec_art

        self.sender = text
        self.streamname= text+"    "
        self.Fav=text2
        self.playlist=playlist
        self.num=1    
        try:
            if self.playlist:
                self.sender=self.playlist[0]
                self.num= self.playlist[2]+1
        except:
            self.playlist=None
        self.alttext=""
        self.alt_url=""
        if not onwbrScreenSaver: set_onwbrScreenSaver()
        HelpableScreen.__init__(self)
        self.title2 = self.sender
        self.stitle=text
        self.session = session
        self.tv = None
        Screen.__init__(self, session)
        if fontlist[9]:
                    self.skinName = "wbrScreenSaver_e"
        else:        
            self.skinName = "wbrScreenSaver_13"
        InfoBarNotifications.__init__(self)
        self["display_station"] = Label(self.sender)
        self["display_nplaying"] = Label("")
        self["display_time"] = Label("")
        self["background"] = Label("")
        self["background1"] = Label("")
        self["cover"] = Cover()
        self["cover2"] = Cover()
        self.display_text="webradioFS" +"  --  "+str(self.sender )
        self.cover_time=0
        self.timewidget =""

        self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
                        {
                                iPlayableService.evUpdatedInfo: self.__mevUpdatedInfo,
                                iPlayableService.evStart: self.__serviceStarted,
                                iPlayableService.evUpdatedRadioText: self.RadioText,
                                iPlayableService.evUpdatedRtpText: self.RTPText,
                                iPlayableService.evEOF: self.__stream_stopped,
                                iPlayableService.evUser+10: self.__stream_stopped,
                                iPlayableService.evTuneFailed: self.__stream_stopped,
                                iPlayableService.evUser+11: self.__stream_stopped,
                                iPlayableService.evUser+12: self.__stream_stopped
                        })

        self.tasten={ 
             "ok": (self.exit,_("Stop Screensaver")),
             "cancel": (self.exit, _("Stop Screensaver")),
             "right": (self.nextcover,_("Toggle Picture")),
             "left": (self.prevcover,_("Toggle Picture")),
             "green": (self.change_keyword,_("change keyword for Picture")),
             "red": (self.cover_save,_("Save Picture")),  #"green": (self.titel_save, _("Start Sleeptimer")),
             "yellow": (self.set_random,_("set random color")),
             "text" :  (self.titel_save,_("Save Title-Info")),
             "blue": (self.blue, _("Set Saver-Type")),
             "down": (self.exit,_("Stop Screensaver")),
             "up": (self.exit,_("Stop Screensaver")),
             "tv": (self.tv_key, _("Exit prog")),
             "halt": (self.stop_key, _("Stop and exit")),
             "zapdown": (self.play_next, _("Play next")),
             }
        if ripper_installed==True and not playlist:
           tasten2={
             "record" : (self.rec_menu,_("Record On/Off")),
             "record_extended" : (self.rec_menu2,_("Record-Menu")),
           }
           self.tasten.update(tasten2)
        self["numberActions"] = NumberActionMap(["NumberActions"],
                {
                        "0": self.keyNumberGlobal,
                        "1": self.keyNumberGlobal,
                        "2": self.keyNumberGlobal,
                        "3": self.keyNumberGlobal,
                        "4": self.keyNumberGlobal,
                        "5": self.keyNumberGlobal,
                        "6": self.keyNumberGlobal,
                        "7": self.keyNumberGlobal,
                        "8": self.keyNumberGlobal,
                        "9": self.keyNumberGlobal,
                        }, -1)
        self["wbrfsKeyActions"] = HelpableActionMap(self, "wbrfsKeyActions", self.tasten, -2)
        self["GlobalwbrfsKeyActions"] = HelpableActionMap(self, "GlobalwbrfsKeyActions",
            {"wbrfs_power_up" : (self.power_key,_("Standby")),
             "wbrfs_power_long" : (self.power_key_long,_("Off")),
        }, -1)
        if art:
            self.saver_art=art
        else:
            self.saver_art=sets_scr["screensaver_art"]
        self.zeige_bilder=True
        self.lcd_bilder=False
        self.mypicture=None
        self.cover_ok=0
        if self.saver_art=="no picture" or self.saver_art=="black" or self.saver_art =="Show_logo":
            self.zeige_bilder=False
        else:
            if fileExists("/tmp/mywbrfs_pic"):
                self.mypicture=os.popen("md5sum "+"/tmp/mywbrfs_pic").read()
                try:
                     os.remove("/tmp/.wbrfs_pic")
                     copyfile("/tmp/mywbrfs_pic","/tmp/.wbrfs_pic")
                     self.cover_ok=1
                except:
                     pass
        if l4lR and l4ls[0] =="True" and l4ls[23] =="True" : self.lcd_bilder=True   
        if sets_grund["picsearch"]=="off":
            self.zeige_bilder=False
        self.onClose.append(self.__onClose)
        self.hole_bild=None
        self.pic_restrict=None
        self.picturesize=""
        self.big_cover=0
        self.url_list=[]
        self.st_color=None
        self.bg_color=None
        try:
            self.st_color=gRGB(int(str(sets_scr["color"]), 0x10))
        except:
           pass
        try:
            self.bg_color=gRGB(int(str(sets_scr["bgcolor"]), 0x10))
        except:
           pass
        self.random_color=str(sets_scr["bgcolor_random"])
        try:
           self.wbrSStextfix=sets_scr["textfix"]
        except:
           self.wbrSStextfix=False 
        self.newstart=True
        self.colfromskin=sets_scr["colfromskin"]
        self.onLayoutFinish.append(self.startRun)
        self.moveTimer = eTimer()
        self.warte_timer = eTimer()
        self.timetext_s=""
        if exit_art>0 and standby_aktion != "wecken":
             self.exiter_timer = eTimer()
             if fontlist[4]:
                  self.exiter_timer_conn = self.exiter_timer.timeout.connect(self.exiterTimer_Timeout)
             else:
                 self.exiter_timer.timeout.get().append(self.exiterTimer_Timeout)
             self.exit_time=int(round((exit_art-time.time())/60))
             self.standby_aktion=standby_aktion
             self.sctext=None
             if self.standby_aktion== "chillen":
                         self.sctext= " ("+_("Chilling: still")+" "
             else:
                     self.sctext= " ("+_("Sleep in")+" "
             if self.sctext:self.timetext_s= self.sctext+str(self.exit_time)+" min.)"
             self.exiter_timer.startLongTimer(60)    
        if fontlist[4]:
             self.moveTimer_conn = self.moveTimer.timeout.connect(self.moveTimer_Timeout)
             self.warte_timer_conn = self.warte_timer.timeout.connect(self.coverDownloadFinished)
        else:
            self.moveTimer.timeout.get().append(self.moveTimer_Timeout)
            self.warte_timer.timeout.get().append(self.coverDownloadFinished)
        self.moveTimer.stop()
        self.warte_timer.stop()
        self.onChangedEntry = []
        self.selectionChanged()

    def exiterTimer_Timeout(self):
            if self.exit_time>1:
                self.exit_time=self.exit_time-1
                if self.sctext:
                     self.timetext_s= self.sctext+str(self.exit_time)+" min.)"
                self.exiter_timer.startLongTimer(60)
            else:
                if self.standby_aktion== "chillen":
                    self.exit2()
                else:
                    self.exit_sleep()

    def createSummary(self):
        if self.display_on:return webradioFSdisplay13

    def selectionChanged(self):
                Zeile2 = self.stitle
                Zeile1 = self.sender
                Zeile3 = self.Fav
                set_display(Zeile1,Zeile2,Zeile3)
                for cb in self.onChangedEntry:
                        cb(Zeile1,Zeile2,Zeile3,"normal",self.logo) 

    def __serviceStarted(self):
        if not onwbrScreenSaver or onwbrScreenSaver=="off":
               self.exit()
        elif self.playlist:
            self.newbild()

    def __mevUpdatedInfo(self):
            if not onwbrScreenSaver or onwbrScreenSaver=="off":
               self.exit()
            elif not satradio and not streamplayer.is_playing and not self.playlist:
                self.close("stopped")
            elif onwbrScreenSaver:    
                self.newbild()
            elif not self.playlist:
                 self.exit()

    def RadioText(self):
        self.newbild("radiotext")
    def RTPText(self):
        self.newbild("rtptext")
    def newbild(self,remaining=None):
                self.t_name=""
                self.stitle = ""
                sender=self.sender
                socket.setdefaulttimeout(20)
                self.newstart=True
                mcover=None
                global l4l_info
                currPlay = self.session.nav.getCurrentService()
                if currPlay is not None:
                        self.t_name=""
                        if remaining:
                            if remaining=="radiotext":
                                typ1="pvr1"
                            elif remaining=="rtptext":
                                typ1="pvr2"
                            self.stitle = grab_text(self,typ1,self.sender)
                            if self.stitle is None:
                                self.stitle=self.sender
                        elif self.playlist:
                            Title1 = currPlay.info().getInfoString(iServiceInformation.sTagTitle).replace("_"," ")#.strip()
                            sArtist = currPlay.info().getInfoString(iServiceInformation.sTagArtist)
                            tags=None
                            from .wbrfs_funct import tag_read
                            tags= tag_read().read_tags(self.playlist[1][self.num-1][1])
                            r=0
                            if tags:
                              if tags[0]:#mcover=tags[0]
                                  coverArtFile = file("/tmp/.wbrfs_pic", 'wb')
                                  coverArtFile.write(tags[0])
                                  coverArtFile.close()
                                  mcover=1
                              else:
                                  pic_rumpf=self.playlist[1][self.num-1][1][:-3]
                                  if os.path.exists(pic_rumpf+"jpg"):
                                      copyfile(pic_rumpf+"jpg", "/tmp/.wbrfs_pic")
                                      mcover=1
                                  elif os.path.exists(pic_rumpf+"png"):
                                      copyfile(pic_rumpf+"png", "/tmp/.wbrfs_pic")
                                      mcover=1   
                              if tags[2] != "n/a" and tags[1] != "n/a": 
                                  self.stitle= tags[2]+": "+tags[1]
                              elif len(sArtist) and len(Title1): 
                                  self.stitle= sArtist+": "+Title1
                              else:  
                                  self.stitle=self.streamname
                              try:
                                  service = self.session.nav.getCurrentService()
                                  seek = service and service.seek()
                                  if seek:
                                     len1 = seek.getLength()
                                     duration = len1[1]/90000
                                     r = "%d:%02d" % (duration/60,duration%60)
                              except:
                                     r=0
                            l4l_info["Genres"]=self.streamname
                            l4l_info["akt_txt"]=self.stitle
                            l4l_info["Station"]=self.playlist[1][self.num-1][2]
                            l4l_info["Len"]=r
                            l4l_set.set_l4l_info(l4l_info)
                        else:
                            self.stitle = currPlay.info().getInfoString(iServiceInformation.sTagTitle).replace("_"," ")
                        if self.stitle is None or len(str(self.stitle))<2:
                              self.stitle = sender
                        self.t_name=""
                        if self.stitle and len(self.stitle.strip()):
                            if self.alttext !=self.stitle:
                                l4l_info["akt_txt"]=self.stitle
                                l4l_set.set_l4l_info(l4l_info)
                                self.alttext=self.stitle
                                title = "%s" % self.stitle
                                self["display_nplaying"].setText(title)
                                self.selectionChanged()
                                if self.zeige_bilder or self.lcd_bilder:
                                  if mcover:
                                      self.coverDownloadFinished(None,None)
                                  elif not mcover and not fileExists("/tmp/mywbrfs_pic"): 
                                    if self.saver_art=="theme_images" and self.bildthema !="" and len(self.url_list)>0:
                                        self.cover_load(1)
                                    else:
                                      if self.saver_art=="theme_images" and self.bildthema !="":
                                          typ=2
                                          self.t_name=self.bildthema.lower()
                                          if len(self.url_list)>0:
                                               self.cover_load(1)
                                      elif (len(self.stitle)):
                                        typ=1
                                        self.t_name=self.stitle
                                      if len (self.t_name.strip()) and self.hole_bild==None:
                                            self.t_name=self.t_name.replace(":","").replace("-"," ").replace("("," ").replace(")"," ").split()
                                            self.t_name='+'.join(self.t_name)
                                            url=None
                                            url=Codierung(self.t_name,self.streamname,typ)#.encode("latin","ignore")
                                            if url:
                                                    user_agent = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3'
                                                    headers = { 'User-Agent' : user_agent }
                                                    if pyvers1==2:
                                                        getPage(url, timeout=10, headers=headers).addCallback(self.GoogleImageCallback).addErrback(self.no_cover) 
                                                    else:
                                                        callInThread(threadGetPage, url, self.GoogleImageCallback, self.no_cover,1)
                                            else:                           
                                               self.no_cover()
                                      else:
                                          self.no_cover()
                        else:
                              self.stitle = self.streamname
                              self.no_cover()

    def GoogleImageCallback(self, result=None):
         if self.zeige_bilder or self.lcd_bilder and not fileExists("/tmp/mywbrfs_pic"):
            self.url_list=[]
            i=3
            if result:    
                self.url_list=[]
                self.url_index=0
                startPos=0
                anz=5
                if self.saver_art=="theme_images": anz=20
                if sets_grund["picsearch"] !="var3":
                    if sets_grund["picsearch"]=="var1":
                         begr=('src="','</div>')
                    if sets_grund["picsearch"]=="var2":
                         begr=("murl&quot;:&quot;","&amp;")
                    founds=1
                    laenge=len(result)
                    while founds and startPos < laenge and i<anz: 
                        url1=''
                        bfoundPos = result.find(begr[0],startPos)
                        if bfoundPos == -1:
                                anz=100
                                break
                        bfoundPos2 = result.find(begr[1],bfoundPos+1)
                        if bfoundPos != -1 and bfoundPos2 != -1:
                            if sets_grund["picsearch"]=="var1":
                                url1 = result[bfoundPos+5:bfoundPos2-9]
                            else:
                                url = result[bfoundPos:bfoundPos2].lower()
                                cfound1 = url.find("http")
                                if ".jpg" in url:
                                   cfound2 = url.find(".jpg")
                                   url1= url[cfound1:cfound2+4]
                                elif ".png" in url:
                                   cfound2 = url.find(".png")
                                   url1= url[cfound1:cfound2+4]
                                elif ".jpeg" in url:
                                    cfound2 = url.find(".jpeg")
                                    url1= url[cfound1:cfound2+5]
                        else:
                            break
                        if not len(url1) or "blogspot" in url1:
                                url1=''
                        else:
                                url1 = url1.replace("&amp;","&").replace("%25","%")
                                if url1 not in self.url_list and url1.startswith('http'):
                                    self.url_list.append(url1)
                                    i+=1
                        startPos=bfoundPos2+10
                elif sets_grund["picsearch"]=="var3":
                    bfoundPos = result.find('artworkUrl100')
                    if bfoundPos != -1:
                        bfoundPos2 = result.find(', "',bfoundPos+1)
                        if bfoundPos != -1 and bfoundPos2 != -1:
                            url1 = result[bfoundPos+16:bfoundPos2-1]
                            if url1 != '' and url1 not in self.url_list and url1.startswith('http'):
                              self.url_list.append(url1)
            if len(self.url_list)>0:
                    self.cover_load()
                    self.hole_bild=None
            else:
                self.no_cover()

    def cover_load(self,num=0):
            if (self.zeige_bilder or self.lcd_bilder) and not fileExists("/tmp/mywbrfs_pic"):    
                if len(self.url_list)>0:
                    self.cover_ok=1
                    self.url_index=self.url_index + num
                    if self.url_index > len(self.url_list)-1:
                       self.url_index=0
                    elif self.url_index < 0:
                       self.url_index=len(self.url_list)-1
                    url=self.url_list[self.url_index]
                    response = requests.head(url)
                    callInThread(threadGetPage, url, self.coverDownloadFinished, self.coverDownloadFailed,2)
                else:
                    self.no_cover()

    def nextcover(self):
        if self.zeige_bilder and not fileExists("/tmp/mywbrfs_pic"):
            self.newstart=True
            self.cover_load(1)

    def prevcover(self):
        if self.zeige_bilder and not fileExists("/tmp/mywbrfs_pic"):
            self.newstart=True
            self.cover_load(-1)

    def coverDownloadFailed(self, error=None):
          if (self.zeige_bilder or self.lcd_bilder) and not fileExists("/tmp/mywbrfs_pic"):   
             try:
                 del self.url_list[self.url_index]
                 self.url_index=0
                 self.cover_load()
             except:
                 self.no_cover()

    def no_cover(self):
          if (self.zeige_bilder or self.lcd_bilder) and not fileExists("/tmp/mywbrfs_pic"):   
               self.hole_bild=None
               self.cover_ok=0
               copyfile(def_pic, "/tmp/.wbrfs_pic")
               self.coverDownloadFinished(None,None)

    def coverDownloadFinished(self,result=None,scover=True):
            self.cover_ok=1
            global L4LwbrFS
            if fileExists("/tmp/.wbrfs_pic"):
                 self.cover_time=time.localtime() 
                 if scover and self.zeige_bilder and self.rec_cover:
                     try:
                             copyfile("/tmp/.wbrfs_pic", self.rec_cover+self.stitle+".jpg")#+"cover/"
                     except:
                         pass
                 if self.lcd_bilder:
                       try:
                           L4LwbrFS.add( "wbrFS.01.pic2",{"Typ":"pic","Align": str(l4ls[24]),"Pos":int(l4ls[25]),"File":"/tmp/.wbrfs_pic","Size":int(l4ls[26]),"Screen":l4ls[3],"Lcd":l4ls[1],"Mode":"OnMedia"} )
                           L4LwbrFS.setScreen(l4ls[3],l4ls[1],True)
                           if l4ls[2]=="True":
                               L4LwbrFS.setHoldKey(True)
                       except:
                           L4LwbrFS=None
                           self.session.open(MessageBox,_("LCD4Linux-Version not compatible")+"\n(min = 4.x)", MessageBox.TYPE_ERROR)
                 if fileExists("/tmp/mywbrfs_pic"):
                     md_file=os.popen("md5sum "+"/tmp/mywbrfs_pic").read()
                     if md_file != self.mypicture:
                         os.remove("/tmp/.wbrfs_pic")
                         copyfile("/tmp/mywbrfs_pic","/tmp/.wbrfs_pic")
                         self.mypicture=md_file
                         self.cover_ok=1
                 if self.cover_ok:
                     self["cover"].updateIcon()
                     if self.saver_art !="no big":self["cover2"].updateIcon()
                 else:
                     self["cover"].updateIcon(9)    
            else:
                 self["cover"].updateIcon(9)
                 self.cover_ok=0

    def cover_save(self):
        right_site.hide()
        if fileExists("/tmp/.wbrfs_pic") and (self.zeige_bilder or self.lcd_bilder):
            self.session.openWithCallback(self.cover_save2,VirtualKeyBoard,title = _("Edit cover-save-name:"), text = self.t_name.replace(' ','_'))

    def cover_save2(self,name):
        right_site.show()
        if name is not None and len(name):   
          try:
             safepath=sets_exp["coversafepath"]
             if not os.path.exists(safepath):
                 os.mkdir(safepath)
             infile=open("/tmp/.wbrfs_pic").read()
             f2=open(safepath+name+".jpg","w")
             f2.write(infile)
             f2.close()
             infile=None
             self.session.open(MessageBox,_("Cover saved"), MessageBox.TYPE_INFO,timeout=3)
          except:
             self.session.open(MessageBox,_("Error, Cover no saved"), MessageBox.TYPE_ERROR,timeout=3)

    def titel_save(self):
        if self.stitle != "webradioFS" and self.stitle != "":   
                savepath=sets_exp["coversafepath"]
                info=titel_save(self.stitle,savepath).inf
                self.session.open(MessageBox,info, MessageBox.TYPE_ERROR,timeout=3)

    def startRun(self):
        self.tfColor=None
        self.tfsColor=None
        self.tfOffset=None
        self.bgcolor1=None
        self.tbTr=None
        if self.colfromskin != True:
          if self["display_nplaying"].skinAttributes:
            for (attrib, value) in self["display_nplaying"].skinAttributes:
                        if (attrib == 'foregroundColor') and value[0]=="#":
                                self.tfColor = value
                        elif (attrib == 'transparent') and value[0]=="#":
                                self.tbTr = value
                        elif (attrib == 'shadowColor') and value[0]=="#":
                                self.tsColor = value
                        elif attrib == "shadowOffset":
                               self.tfOffset = value 
          if self["background1"].skinAttributes:
                for (attrib, value) in self["background1"].skinAttributes:
                    if (attrib == 'backgroundColor' and value[0]=="#"):
                        self.bgcolor1=value
        else:
           self.random_color=0
        self.instance.setZPosition(5)
        if self.zeige_bilder or self.saver_art=="Show_logo":
            self.groesse2=self["cover2"].instance.size().width()
            if self.saver_art !="no big":self["cover2"].updateIcon()
            self["cover2"].hide()
            self.groesse1=self["cover"].instance.size().width()
        else:
            self.groesse1=20
        self.textbreite=self["display_station"].instance.size().width()
        self.texthoehe=self["display_station"].instance.size().height()
        if self.saver_art=="theme_images" and self.bildthema =="":
              self.change_keyword()
        elif self.saver_art=="black":
               self.moveTimer.stop()
               self["cover"].hide()
               self["display_time"].hide()
               self["display_station"].hide()
               self["display_nplaying"].hide()
        else:
            if self.zeige_bilder:self["cover"].updateIcon()
            tage = [_('Monday'),_('Tuesday'),_('Wednesday'),_('Thursday'),_('Friday'),_('Saturday'),_('Sunday')]
            diezeit = time.localtime(time.time())
            self.TagesZahl = tage[diezeit[6]]
            if self.colfromskin != True:
              try:
                if self.tfsColor:
                      self["display_nplaying"].instance.setShadowColor(parseColor("#000000"))
                      self["display_station"].instance.setShadowColor(parseColor("#000000"))
                      self["display_time"].instance.setShadowColor(parseColor("#000000"))
                if self.tbTr is not None:
                      self["display_nplaying"].instance.setTransparent(0)
                      self["display_station"].instance.setTransparent(0)
                      self["display_time"].instance.setTransparent(0)
                if self.st_color:
                    self["display_nplaying"].instance.setForegroundColor(self.st_color)
                    self["display_station"].instance.setForegroundColor(self.st_color)
                    self["display_time"].instance.setForegroundColor(self.st_color)
                if self.bg_color:
                    self["display_nplaying"].instance.setBackgroundColor(self.bg_color)
                    self["display_station"].instance.setBackgroundColor(self.bg_color)
                    self["display_time"].instance.setBackgroundColor(self.bg_color)
                    self["background1"].instance.setBackgroundColor(self.bg_color)
                    self["background1"].instance.setForegroundColor(self.bg_color)
              except:
                pass
            self.moveTimer.start(5)
        self.__mevUpdatedInfo()

    def set_logo(self):
                                  self["cover"].updateIcon(4,self.logo)
                                  self["cover"].show()    

    def blue(self):
         saver_list=[(_("rotation"),"wechsel"),(_("only show big pictures"),"big"),(_("show no pictures"),"no picture"),(_("show no big pictures"),"no big"),(_("pure black"),"black"),(_("theme images"),"theme_images"),(_("Show logo"),"Show_logo")]
         self.session.openWithCallback(self.blue2,ChoiceBox,_("Select Screensaver-Art"),saver_list)

    def blue2(self,result=None):
        if result:
           self.saver_art=result[1]
           self.zeige_bilder=True
           if self.saver_art in ("no picture","black","Show_logo") :self.zeige_bilder=None
           self.startRun()

    def change_keyword(self):
        if self.zeige_bilder:
          if self.bildthema != "":
           self.session.openWithCallback(self.new_keyword, InputBox, title=_("change Keyword for Picture"), text=self.bildthema, maxSize=False, type=Input.TEXT)
          else:
            self.session.open(MessageBox,_("First select Screensaver-Art")+": "+_("theme images") , MessageBox.TYPE_INFO,timeout=3)

    def set_random(self):
        text=None
        if self.random_color == "0":
           self.random_color = "1"
           text=_("random color for labels")
        elif self.random_color == "1":
           self.random_color = "2"
           text=_("random color for background")
        elif self.random_color == "2":
           self.random_color = "3"
           text=_("random color for labels and background")
        elif self.random_color == "3":
           self.random_color = "0"
           text=_("not random color")
        self.bg_color_b=self.bg_color
        if str(self.bg_color)[0]=="#": self.bg_color_b=parseColor(self.bg_color)
        self.st_color_b=self.st_color
        if str(self.st_color)[0]=="#": self.st_color_b=parseColor(self.st_color)
        self["display_nplaying"].instance.setBackgroundColor(self.bg_color_b)
        self["display_station"].instance.setBackgroundColor(self.bg_color_b)
        self["display_time"].instance.setBackgroundColor(self.bg_color_b)
        if self.st_color and (self.random_color == "0" or self.random_color == "2"):
           self["display_nplaying"].instance.setForegroundColor(self.st_color_b)
           self["display_station"].instance.setForegroundColor(self.st_color_b)
           self["display_time"].instance.setForegroundColor(self.st_color_b)
        if self.bg_color and (self.random_color == "0" or self.random_color == "1"):
           self["background1"].instance.setBackgroundColor(self.bg_color_b)
           self["background1"].instance.setForegroundColor(self.bg_color_b)
        if text:self.session.open(MessageBox,text, MessageBox.TYPE_INFO,timeout=3)

    def new_keyword(self,ret):
           if ret:
               self.url_list=[]
               self.bildthema=ret
               self.startRun()

    def moveTimer_Timeout(self):
      r_color=int(self.random_color)
      if r_color>0:    
          RGB=None
          tf=None
          tfs=None
          if r_color>1:
            a=0
            b=255
            if r_color !=3 and self.tfColor and self.tfColor[0] == '#':
                COL = self.tfColor[1:]
                RGB0 = (int(COL[:2], 16), int(COL[2:4], 16), int(COL[4:6], 16))
                if(RGB0[0]+RGB0[1]+RGB0[2])/3  >110:
                    b=80
                else:
                    a=170
            RGB=(random.randint(a,b),random.randint(a,b),random.randint(a,b))
            bg_farbe='#%02x%02x%02x' % (RGB[0], RGB[1], RGB[2])
            self["background1"].instance.setBackgroundColor(parseColor(bg_farbe))
            self["background1"].instance.setForegroundColor(parseColor(bg_farbe))
            self["display_nplaying"].instance.setBackgroundColor(parseColor(bg_farbe))
            self["display_station"].instance.setBackgroundColor(parseColor(bg_farbe))
            self["display_time"].instance.setBackgroundColor(parseColor(bg_farbe))
          elif self.tfColor and self.tfColor[0] == '#':
              COL = self.tfColor[1:]
          RGB = (int(COL[:2], 16), int(COL[2:4], 16), int(COL[4:6], 16))
          bg_farbe='#%02x%02x%02x' % (RGB[0], RGB[1], RGB[2])
          if r_color ==1 or r_color ==3:
              a=0
              b=255
              if RGB:
                  rgb_r=(RGB[0]+RGB[1]+RGB[2])/3
                  if rgb_r > 95 and rgb_r < 130:
                       a=0
                       b=50
                  elif rgb_r <96:
                       a=127+ ((RGB[0]+RGB[1]+RGB[2])/3)
                       if a+50 <255: 
                           b=a+50
                       tfs=parseColor("#000000")
                  else:
                      b=255- ((RGB[0]+RGB[1]+RGB[2])/3)
                      if b-50 >0: 
                           a=b-50
                      tfs=parseColor(bg_farbe)
              RGB2=(random.randint(a,b),random.randint(a,b),random.randint(a,b))
              txt_farbe='#%02x%02x%02x' % (RGB2[0], RGB2[1], RGB2[2])
              self["display_nplaying"].instance.setForegroundColor(parseColor(txt_farbe))
              self["display_station"].instance.setForegroundColor(parseColor(txt_farbe))
              self["display_time"].instance.setForegroundColor(parseColor(txt_farbe))
              if tfs and self.tfsColor:
                         self["display_nplaying"].setShadowColor(tfs)
                         self["display_station"].setShadowColor(tfs)
                         self["display_time"].setShadowColor(tfs)
      if not satradio and not streamplayer.is_playing  and not self.playlist:
                self.close("stopped")
      else:
        self["cover"].hide()
        self["cover2"].hide()
        if (self.saver_art=="big" or self.saver_art=="theme_images") and self.cover_ok>0:
             self.big_cover=3
        else:
            uhrzeit = strftime("%H:%M",localtime())+self.timetext_s
            self.timewidget = "\n"+self.TagesZahl +", " + strftime("%d.%m.%Y",localtime()) 
            t00=""
            if not self.playlist:
                if l4l_info["rec"]==1:
                     t00=" **"+_("caching")+" ..."
                elif l4l_info["rec"]==2:
                     t00=" **"+_("recording in progress")+" ..."
            text01=uhrzeit+t00+self.timewidget
            self["display_time"].setText(text01)
            titeltext = uhrzeit + "\n" + self.title2
        if self.saver_art=="no big" or not self.zeige_bilder: self.big_cover=0
        if self.saver_art=="Show_logo":
               self.set_logo()
        if DWide == 720:
                x = random.randint(10, 482)
                y = random.randint(0, 338)
                if self.zeige_bilder or self.saver_art=="Show_logo":
                    x = random.randint(self.groesse1, 482)
                    self["cover"].move(ePoint(x-self.groesse1-20,y))
                    self["cover"].show()
                if not self.wbrSStextfix or self.wbrSStextfix=="False":
                    self["display_station"].move(ePoint(x,y+self.texthoehe*2))
                    self["display_nplaying"].move(ePoint(x,y+self.texthoehe*3))
                    self["display_time"].move(ePoint(x,y))
        else:
                if self.big_cover>1 and self.zeige_bilder and self.cover_ok>0: # and self.coverbig==2:
                    x = random.randint(10, int(DWide-self.groesse2-10))
                    y = random.randint(30, int(self.groesse2/2+120))
                    self.big_cover=0
                    self["display_time"].hide()
                    self["display_station"].hide()
                    self["display_nplaying"].hide()
                    self["cover2"].move(ePoint(x,y))  
                    self["cover2"].show()
                else:
                    if self.zeige_bilder or self.saver_art=="Show_logo":
                        if self.zeige_bilder and self.cover_ok: self.big_cover+=1
                        self["cover"].show()
                    self["display_time"].show()
                    self["display_station"].show()
                    self["display_nplaying"].show()
                    if not self.wbrSStextfix or self.wbrSStextfix=="False":
                        y = random.randint(5, int(DHoehe-(self.groesse1+5)))
                        x = random.randint(5, int(DWide-(self.groesse1+self.textbreite)))
                        if self.zeige_bilder or self.saver_art=="Show_logo":
                            x = random.randint(110, int(DWide-self.groesse1-self.textbreite))
                            self["cover"].move(ePoint(x-10,y+5))
                        self["display_nplaying"].move(ePoint(x+self.groesse1+5,y+self.texthoehe*3))
                        self["display_station"].move(ePoint(x+self.groesse1+5,y+self.texthoehe*2))
                        self["display_time"].move(ePoint(x+self.groesse1+5,y+10))
        self.moveTimer.startLongTimer(10)

    def __onClose(self):
        if fileExists("/tmp/mywbrfs_pic"):os.remove("/tmp/mywbrfs_pic")
        if self.tv:self.tv=None
        try:
            del self.picload
        except:
           pass
        if self.moveTimer.isActive(): self.moveTimer.stop()
        if fileExists("/tmp/.wbrfs_pic"): os.remove("/tmp/.wbrfs_pic")

    def play_next(self):
        if self.playlist:
               failed=0
               file_list=self.playlist[1]
               for x in file_list:
                   if x[0].strip()==self.streamname.strip():
                       self.num=(file_list.index(x))+1
               if len(file_list)>1:
                 if a_sort=="random":
                   self.num=random.randint(1,len(file_list))
                 else:
                   self.num=self.num+1
                 if self.num > len(file_list):self.num=1
                 if file_list[self.num-1][7] =="Dir":
                   self.num=self.num+1
                 if self.num > len(file_list):self.num=1
                 if not os.path.exists(self.playlist[1][self.num-1][1]):
                        del file_list[self.num-1]
                        self.playlist=(self.playlist[0],file_list,self.playlist[2])
                        failed=1
                 else:
                     d1=os.path.dirname(self.playlist[1][self.num-1][1])
                     dir2=d1.split('/')
                     if len(dir2)>2:
                              dir2=".../"+dir2[-2]+"/"+dir2[-1]
                     else:
                              dir2=d1
                     self.streamname = self.playlist[1][self.num-1][0] #.replace("-"," ")
                     self.sender=dir2
                     self.display_text="webradioFS" +"  --  "+file_list[self.num-1][0]#[:4]
                     self.session.nav.stopService()
               else:
                 self.num=1
                 self.streamname = self.playlist[1][0][0] #.replace("-"," ")
                 self.sender=self.streamname
                 self["display_station"].setText(self.playlist[0])
               if failed:
                   self.__stream_stopped()
               else:
                   self["display_station"].setText(self.playlist[0])
                   self.display_text="webradioFS" +"  --  "+self.playlist[1][self.num-1][0]
                   sref = eServiceReference(4097, 0, self.playlist[1][self.num-1][1])
                   self.session.nav.playService(sref)

    def __stream_stopped(self):
            if onwbrScreenSaver and onwbrScreenSaver=="off":
               self.exit()
            if self.Fav==_("Single-play from webif"):
                      self.einzelplay=0
                      self.close("stopped")
            elif self.playlist:
                 self.play_next()
            elif onwbrScreenSaver:
                self.close("stopped")
            else:
                self.close("exit")

    def stop_key(self):
            self.close("stop")
    def power_key_long(self):
            self.close("off")
    def power_key(self):
            self.close("standby")
    def tv_key(self):
            self.close("ende")
    def rec_menu(self):
            self.close("record")
    def rec_menu2(self):
            self.close("record2")
    def exit(self):
         if self.playlist:
            self.close("exit",self.playlist[1][self.num-1])
         else:
            self.close("exit")
    def exit2(self):
            self.close()
    def exit_sleep(self):
            self.close("sleep")
    def keyNumberGlobal(self, number):
        if number is not None:
                self.close("nummer",number)


class titel_save():
     def __init__(self, text,savepath):   
           try:
             if not os.path.exists(savepath):
                 os.mkdir(savepath)
             if not fileExists(savepath+'titel_list.txt'):
                 f=open(savepath+'titel_list.txt','w')
             else:
                f=open(savepath+'titel_list.txt','a')
             f.write(text+"\n")
             f.close()
             self.inf=_("Title saved in titel_list.txt")
           except:
             self.inf=_("Error, Title no saved")


class file_list:
    def __init__(self, path,subdirs=False,art=None):
                self.Dateiliste = []
                self.Dateiliste2 = []
                sys.setrecursionlimit(5000)
                startDir = path
                directories = [startDir]
                subdirs1=subdirs
                z=1
                while len(directories)>0:
                    directory = directories.pop()
                    if os.path.isdir(directory) and z<4999:
                        z+=1
                        try:
                            for name in os.listdir(directory):
                                fullpath = os.path.join(directory,name)
                                if not name.startswith(".") and not fullpath.startswith("."):
                                    if os.path.isfile(fullpath) and os.path.getsize(fullpath)>0:
                                        if art==None:
                                            if name.lower().endswith((".jpg","jpeg","jpe","bmp", "png")) and not name.startswith("."):
                                                self.Dateiliste2.append((fullpath,name,"all",True,"file"))
                                        if art=="rec":
                                            if name.lower().endswith((".mp3")) and not name.startswith("."):
                                                self.Dateiliste2.append((fullpath,name,"all",True,"file"))
                                    elif os.path.isdir(fullpath):
                                        if subdirs1==True:
                                            directories.append(fullpath)
                                        elif subdirs1=="True2":
                                            self.Dateiliste.append((fullpath+"/",name,"all",True,"dir",True))
                        except IOError:
                            pass
                if len(self.Dateiliste):self.Dateiliste.sort(key=lambda x: "".join(x[1]).lower())
                if len(self.Dateiliste2):
                    self.Dateiliste2.sort(key=lambda x: "".join(x[1]).lower())
                    self.Dateiliste.extend(self.Dateiliste2)


class rec_menu_13(Screen, ConfigListScreen):
        def __init__(self, session,stream,n=None,t=None):
                if skin_ext==plugin_path +"/skin/SD/":
                    right_site.hide()
                tmpskin = open(skin_ext+"wbrFS_setup.xml")
                self.skin = tmpskin.read()
                tmpskin.close()
                self.onChangedEntry = []

                self.stream=stream
                self.list = []
                self.now = [x for x in localtime()]
                def_Start_Time=time.mktime(self.now)
                if int(self.stream[2])>0:
                    self.timed = NoSave(ConfigSelection(choices = [("only switch",_("only switch"))]))
                else:
                    self.timed = NoSave(ConfigSelection(choices = [("only switch",_("only switch")),("endless",_("record endless")),("by minutes",_("record by minutes")),("by time",_("record by time"))], default = "only switch"))
                self.minutes = NoSave(ConfigInteger(default=0, limits = (0, 9999)))
                self.startTime=NoSave(ConfigClock(default =def_Start_Time))
                self.endTime=NoSave(ConfigClock(default =def_Start_Time))
                self.subdir= NoSave(ConfigYesNo(default = sets_rec["new_dir"]))
                self.rec_split= NoSave(ConfigYesNo(default = sets_rec["split"]))
                self.rec_cover= NoSave(ConfigYesNo(default = sets_rec["cover"]))
                self.rec_path= NoSave(ConfigDirectory(default = sets_rec["path"]))
                self.pos_filter= NoSave(ConfigText(default="", fixed_size = False))
                self.neg_filter= NoSave(ConfigText(default="", fixed_size = False))
                Screen.__init__(self, session)
                if fontlist[9]:
                    self.skinName = "WebradioFSSetup_e"
                else:
                     self.skin=self.skin.replace('backgroundColor="#000000"','')
                     self.skin=self.skin.replace('foregroundColor="#ffffff"','')
                     self.skinName = "WebradioFSSetup_13"
                self.refresh()
                ConfigListScreen.__init__(self, self.list, on_change = self.reloadList)
                self["green_pic"] = Pixmap()
                self["rec_txt"] = Label(_("temporary Record-Settings"))
                self["playtext"] = StaticText("")
                self["key_red"] = Label(_("Cancel"))
                self["pic_red"] = Pixmap()
                self["key_green"] = Label(_("Start"))
                self["pic_green"] = Pixmap()
                self["key_yellow"] = Label("")
                self["pic_yellow"] = Pixmap()
                self["key_blue"] = Label("")
                self["pic_blue"] = Pixmap()
                self["actions"] = ActionMap(["wbrfsKeyActions"],
                        {
                                "cancel": self.Cancel,
                                "red": self.Cancel,
                                "green": self.send,
                                "ok": self.press_ok,
                                "contextMenu": self.press_help,
                        }, -2
                        )
                self.setTitle("webradioFS: " +_("temporary Record-Settings"))
                self.onLayoutFinish.append(self.layoutFinished)

        def layoutFinished(self):
            self.onLayoutFinish.remove(self.layoutFinished)
            self.instance.setZPosition(2)
            if fontlist[8] or fontlist[9]:
              try:
                if not fontlist[4]: 
                    self['config'].instance.setFont(fontlist[3])#(conf_font1)
                    self['config'].instance.setItemHeight(fontlist[2]) 
                else:
                    from skin import parseFont
                    stylemgr = eWindowStyleManager.getInstance()
                    skinned = eWindowStyleSkinned()
                    eListboxPythonConfigContent.setDescriptionFont(parseFont(conf_font1, ((1,1),(1,1))))
                    eListboxPythonConfigContent.setValueFont(parseFont(conf_font2, ((1,1),(1,1))))
                    eListboxPythonConfigContent.setItemHeight(conf_item)
                    stylemgr.setStyle(0, styleskinned)
              except:
                  pass
            self.reloadList()

        def reloadList(self):
                self.refresh()
                self["config"].setList(self.list)

        def refresh(self):
                list=[]
                list.append(getConfigListEntry(_("These settings are only for this one recording!"), ))
                list.append(getConfigListEntry(_("(Help press for explanations)"), ))
                list.append(getConfigListEntry(_(" "), ))          
                list.append(getConfigListEntry(_("Stream-Name: ")+self.stream[0], ))

                if int(self.stream[2])>0:
                    list.append(getConfigListEntry(_("the sender does not allow recording"), ))
                list.append(getConfigListEntry(_(" "), ))
                list.append(getConfigListEntry(_("timing art"), self.timed))

                if self.timed.value == "by minutes" :
                        list.append(getConfigListEntry(_("Recording len (minutes)"),self.minutes))

                elif self.timed.value == "by time" or self.timed.value == "only switch" :
                        list.append(getConfigListEntry( _("Start-time:"),self.startTime))
                if self.timed.value == "by time":
                        list.append(getConfigListEntry( _("End-time:"),self.endTime))
                if self.timed.value != "only switch":
                        list.extend((
                             getConfigListEntry(_("Path for record"), self.rec_path),
                             getConfigListEntry(_("Make subdir for record"), self.subdir),
                             getConfigListEntry(_("Split recording with event"), self.rec_split),
                                                ))
                        if self.rec_split.value:
                          list.extend((
                             getConfigListEntry(_(" "), ),
                             getConfigListEntry(_("experimental:"), ),
                             getConfigListEntry(_("Recording when in title"), self.pos_filter),
                             getConfigListEntry(_("Not recording when in title"), self.neg_filter),
                                                ))
                self.list=list

        def press_help(self):
            help_text=None
            self.cur = self["config"].getCurrent()
            if self.cur[1] == self.timed:
               help_text=_("Select a recording mode")
            elif self.cur[1] == self.minutes:
               help_text=_("Begin recording immediately, recording time specify in minutes")
            elif self.cur[1] == self.startTime:
               help_text=_("Recording / switching at a certain time, edit start time")
            if self.cur[1] == self.endTime:
               help_text=_("Time, when to stop recording")
            if self.cur[1] == self.rec_path:
               help_text=_("edit the recording directory")
            if self.cur[1] == self.subdir:
               help_text=_("Creating a subdirectory for Stream")
            if self.cur[1] == self.rec_split:
               help_text=_("Split recordings by title")
            if self.cur[1] == self.pos_filter:
               help_text=_("Record only if at least one of the words in the title")
            if self.cur[1] == self.neg_filter:
               help_text=_("Not record if at least one of the words in the title")
            if help_text:
                self.session.open(MessageBox, help_text,MessageBox.TYPE_INFO)

        def press_ok(self):
            self.cur = self["config"].getCurrent()
            if self.cur[1] == self.rec_path:
                 self.path_wahl()
            elif self.cur[1] == self.pos_filter:
                 right_site.hide()
                 self.session.openWithCallback(self.texteingabeFinished,VirtualKeyBoard, title=_("Recording when in title")+_(" (separate with commas)"))
            elif self.cur[1] == self.neg_filter:
                 right_site.hide()
                 self.session.openWithCallback(self.texteingabeFinished,VirtualKeyBoard, title=_("Not recording when in title")+_(" (separate with commas)"))
            else:
                 self.send()

        def texteingabeFinished(self, ret):
                right_site.show()
                if ret is not None:
                    if self.cur[1] == self.pos_filter:
                        self.pos_filter.value = ret
                    elif self.cur[1] == self.neg_filter:
                        self.neg_filter.value = ret

        def callAuswahl(self,path):
            right_site.show()
            if path is not None:
                if os.path.exists(path):
                     self["config"].getCurrent()[1].value=path

        def path_wahl(self):
            savepath=sets_exp["coversafepath"]
            right_site.hide()
            self.session.openWithCallback(
                self.callAuswahl,
                SaveLocationBox,_("Please select Save-Path for cover and titles..."),"","/",ConfigLocations(default=[savepath]))

        def send(self):
            diff_min=self.minutes.value
            diff2=0
            add=0
            add2=0
            pos=None
            neg=None
            if self.pos_filter.value != "":
                pos = self.pos_filter.value.lower().split(",")
            if self.neg_filter.value != "":
                neg = self.neg_filter.value.lower().replace(",","|")
            if self.timed.value == "by time" and self.endTime.value != self.startTime: 
                self.now = [x for x in localtime()]
                if self.now[3] > self.startTime.value[0]:add=24
                if self.startTime.value[0]>self.endTime.value[0]:add2=24
                diff2 = (self.startTime.value[0]+add-self.now [3])*60+self.startTime.value[1]-self.now [4]
                diff_min = (self.endTime.value[0]+add2-self.startTime.value[0])*60+self.endTime.value[1]-self.startTime.value[1]
            elif self.timed.value == "only switch": 
                self.now = [x for x in localtime()]
                if self.now [3]>self.startTime.value[0]:add=24
                diff2 = (self.startTime.value[0]+add-self.now [3])*60+self.startTime.value[1]-self.now [4]
                diff_min = 0
            right_site.show()
            self.close(self.timed.value,diff_min,diff2,self.rec_split.value,self.subdir.value,self.rec_cover.value,self.rec_path.value,pos,neg) 

        def Cancel(self):
            right_site.show()
            self.close(None)


class webradioFS_video(Screen):
        skin = """
                <screen backgroundColor="transparent" flags="wfNoBorder" position="0,0" size="%d,%d" title="webradioFS video">
                <widget backgroundColor="black" name="video1"  position="0,0" size="%d,%d" />
                </screen>""" % (300,300,300,300) #(DWide,DHoehe,DWide,DHoehe)

        def __init__(self, session):
                Screen.__init__(self, session)
                self["video1"] = VideoWindow(decoder = 1,fb_width=DWide, fb_height=DHoehe)

        def start(self,Service):
                self.serv=Service
                self.playService()
                try:
                        self["video1"].instance.setOverscan(False)
                except:
                        pass    

        def playService(self):
                ref = self.serv
                try:
                        self.vid_serv = eServiceCenter.getInstance().play(ref)
                        self.vid_serv.start()
                except:
                        pass

        def stopService(self):
                if self.vid_serv and self.vid_serv is not None:
                        self.vid_serv.stop()


class volplusFS(Screen):
     def __init__(self, session):
         self.skin = "<screen position=\"center,center\" size=\"640,300\" > \
           <widget name=\"lab1\" position=\"0,10\" halign=\"center\" size=\"640,60\" zPosition=\"1\" font=\"Regular;30\" valign=\"top\" transparent=\"1\" /> \
           <widget name=\"lab2\" position=\"0,60\" halign=\"center\" size=\"640,30\" zPosition=\"1\" font=\"Regular;24\" valign=\"top\" transparent=\"1\" /> \
           <widget name=\"lab3\" position=\"0,90\" halign=\"center\" size=\"640,30\" zPosition=\"1\" font=\"Regular;24\" valign=\"top\" transparent=\"1\" /> \
           <widget name=\"lab4\" position=\"0,200\" halign=\"center\" size=\"640,30\" zPosition=\"1\" font=\"Regular;24\" valign=\"top\" transparent=\"1\" /> \
           <widget name=\"lab5\" position=\"20,150\" halign=\"center\" size=\"20,20\" zPosition=\"1\" font=\"Regular;22\" valign=\"top\" transparent=\"1\" /> \
           <widget name=\"lab6\" position=\"585,150\" halign=\"center\" size=\"45,20\" zPosition=\"1\" font=\"Regular;22\" valign=\"top\" transparent=\"1\" /> \
           <widget name=\"slid\" position=\"40,150\" size=\"550,20\" zPosition=\"2\"/> \
           </screen>"
         Screen.__init__(self, session)
         self["slid"] = Slider(0,100)
         self["lab1"] = Label(_("Change the Box-Volume"))
         self["lab2"] = Label(_("down or left for lower"))
         self["lab3"] = Label(_("up or right for higher"))
         self["lab4"] = Label(_("Exit or OK for exit"))
         self["lab5"] = Label("0")
         self["lab6"] = Label(str(eDVBVolumecontrol.getInstance().getVolume()))
         self["actions"] = ActionMap(["OkCancelActions","DirectionActions"],
             {
                 "right": self.vol_up,
                 "left": self.vol_down,
                 "up": self.vol_up,
                 "down": self.vol_down,
                 "ok": self.cancel,
                 "cancel": self.cancel,
             }, -1)
         self.onLayoutFinish.append(self.setSlider)

     def setSlider(self):
         self["slid"].setValue(eDVBVolumecontrol.getInstance().getVolume())

     def vol_up(self):
             VolumeControl.instance.volUp()
             self["slid"].setValue(eDVBVolumecontrol.getInstance().getVolume())
             self["lab6"].setText(str(eDVBVolumecontrol.getInstance().getVolume()))

     def vol_down(self):
             VolumeControl.instance.volDown()
             self["slid"].setValue(eDVBVolumecontrol.getInstance().getVolume())
             self["lab6"].setText(str(eDVBVolumecontrol.getInstance().getVolume()))

     def cancel(self):
               self.close()  


class file_list2:
    def __init__(self, path,all=None,playlist=None,search=None):
                self.Dateiliste = []
                self.Dateiliste2 = []
                sys.setrecursionlimit(50000)
                add=0
                num=30
                if playlist==90:num=90
                startDir = path
                if os.path.isdir(sets_rec["path"]) and [sets_audiofiles["audiopath"]] == startDir: add=1
                typ_list=("mp3","ogg","aac","mms","wma","wav","flac","m4a","m3u")
                directories = startDir
                z=0
                fi_num=0
                self.fi_liste=[]
                while len(directories)>0:
                    directory = directories.pop()
                    if os.path.isdir(directory) and z<49999:
                        z+=1
                        try:
                          for name in os.listdir(directory):
                            fullpath=""
                            if name and not name.startswith(".") and not name.startswith("@"):
                                fullpath = os.path.join(directory,name)
                                if os.path.isfile(fullpath) and os.path.getsize(fullpath)>0:
                                   if name.lower().endswith(typ_list): 
                                        if not search or search in name.lower():
                                            name2=fullpath.split('/')[-1]
                                            if all == "fi2":
                                                 self.Dateiliste2.append((name,fullpath))
                                                 fi_num+=1
                                            elif all != "fo": self.Dateiliste2.append((name,fullpath,name2,0,num,0,0,"Files"))
                                elif os.path.isdir(fullpath):
                                      if search and all != "fi" and all != "fi2":
                                            if search in name.lower():
                                                name2=fullpath.split('/')[-1]
                                                self.Dateiliste.append((name,fullpath+"/",name2,0,num,0,0,"Dir"))
                                      if all and (u_dir or search):	
                                            directories.append(fullpath)
                                            if all == "fi2":
                                                 if a_sort == "byFolder":
                                                     self.Dateiliste2.sort(key=lambda x: "".join(x[0]).lower())
                                                 elif a_sort == "randByFolder":
                                                     random.shuffle(self.Dateiliste2)
                                                 self.fi_liste.extend(self.Dateiliste2)
                                                 self.Dateiliste2=[]
                                            
                                      elif not all:
                                                name=fullpath.split('/')[-1]
                                                self.Dateiliste.append((name,fullpath+"/",name,0,num,0,0,"Dir")) 
                        except:
                            pass
                if all == "fi2":
                    if fi_num:
                        if not len(self.fi_liste):
                            if a_sort == "byFolder":
                                self.Dateiliste2.sort(key=lambda x: "".join(x[0]).lower())
                            elif a_sort == "randByFolder":
                                random.shuffle(self.Dateiliste2)
                            self.fi_liste=self.Dateiliste2
                        self.Dateiliste=self.fi_liste
                    else:
                        self.Dateiliste=()
                else:
                    self.Dateiliste.sort(key=lambda x: "".join(x[0]).lower())
                    self.Dateiliste2.sort(key=lambda x: "".join(x[0]).lower())
                    if all and all != "fi": self.Dateiliste.sort(key=lambda x: "".join(x[1]).lower())
                    if add and not playlist: self.Dateiliste.insert(0,(_("My records"),sets_rec["path"],_("My records"),0,30,0,0,"Dir"))
                    self.Dateiliste.extend(self.Dateiliste2)


class play_settings(Screen, ConfigListScreen):
        def __init__(self, session):
                tmpskin = open(skin_ext+"wbrfs_playsets.xml")
                self.skin = tmpskin.read()
                tmpskin.close()
                self.fest = NoSave(ConfigYesNo(default = False))
                self.random= NoSave(ConfigSelection(choices = [("random", _("Random")), ("byFolder", _("by Folder")), ("randByFolder", _("Random by Folder")), ("alphabetically", _("alphabetically")), ("nix", _("Not sort"))], default = a_sort))
                self.subdirs= NoSave(ConfigYesNo(default = u_dir))
                self.audio_schleife = NoSave(ConfigYesNo(default = a_schleife))
                Screen.__init__(self, session)
                if fontlist[9]:
                    self.skinName = "play_settings_e"
                else:
                    self.skin=self.skin.replace('backgroundColor="#000000"','')
                    self.skin=self.skin.replace('foregroundColor="#ffffff"','')
                    self.skinName = "play_settings"
                self.refresh()
                ConfigListScreen.__init__(self, self.list, on_change = self.reloadList)
                self["key_red"] = Label(_("Cancel"))
                self["pic_red"] = Pixmap()
                self["key_green"] = Label(_("OK"))
                self["pic_green"] = Pixmap()
                self["button_backround"] = Label()
                self["actions"] = ActionMap(["wbrfsKeyActions"],
                        {
                                "cancel": self.Cancel,
                                "red": self.Cancel,
                                "green": self.press_ok,
                                "ok": self.press_ok,
                        }, -2
                )
                self.onLayoutFinish.append(self.layoutFinished)
                self.setTitle("webradioFS: " +_("Play settings"))

        def layoutFinished(self):
            self.onLayoutFinish.remove(self.layoutFinished)
            if fontlist[8] or fontlist[9]:
              try:
                if not fontlist[4]: # and not my_settings['big_setup']:
                    self['config'].instance.setFont(fontlist[3])#(gFont("Regular",fontlist[0]))
                    self['config'].instance.setItemHeight(fontlist[2]) #(int((font+10)*font_scale))
                else:
                    from skin import parseFont
                    stylemgr = eWindowStyleManager.getInstance()
                    skinned = eWindowStyleSkinned()
                    eListboxPythonConfigContent.setDescriptionFont(parseFont(conf_font1, ((1,1),(1,1))))
                    eListboxPythonConfigContent.setValueFont(parseFont(conf_font2, ((1,1),(1,1))))
                    eListboxPythonConfigContent.setItemHeight(conf_item)
                    stylemgr.setStyle(0, styleskinned)
              except:
                  pass 
            self.reloadList()

        def reloadList(self):
                self.refresh()
                self["config"].setList(self.list)

        def refresh(self):
                list=[]
                list.append(getConfigListEntry(_("Set permanently"),self.fest))
                list.append(getConfigListEntry(_("Play random"),self.random ))
                list.append(getConfigListEntry(_("Play files from sub-dirs"), self.subdirs))
                list.append(getConfigListEntry(_("Auto play endless"), self.audio_schleife))
                self.list=list

        def press_ok(self):
            global a_sort
            global a_schleife
            global random_pic
            global u_dir
            global subdirs_pic
            global sets_audiofiles
            a_sort=self.random.value
            if self.random.value=="random":
                random_pic=plugin_path+"/skin/images/random.png"	
            else:
                random_pic=plugin_path+"/skin/images/random_off.png"   
            a_schleife=self.audio_schleife.value
            u_dir=self.subdirs.value
            if self.subdirs.value:
                subdirs_pic=plugin_path+"/skin/images/subdirs.png"
            else:
                subdirs_pic=plugin_path+"/skin/images/subdirs_off.png"
            if self.fest.value:
               sets_audiofiles=read_settings1().reading(("audiofiles",""))[0]
               sets_audiofiles={"audiopath":sets_audiofiles["audiopath"],"subdirs":self.subdirs.value,"autoplay":sets_audiofiles["autoplay"],"sort":self.random.value,
                     "audio_listpos":sets_audiofiles["audio_listpos"],"save_random":sets_audiofiles["save_random"],"audio_listnums":sets_audiofiles["audio_listnums"],"schleife":self.audio_schleife.value}
               write_settings((("audiofiles",sets_audiofiles),))                
            self.close()
        def Cancel(self):
            self.close()

class wbrFS_r_site15(Screen):
        tmpskin = open(fontlist[5]+"wbrFS_r_site.xml")        
        skin = tmpskin.read()
        tmpskin.close()
        if not fontlist[9]:
            skin=skin.replace('backgroundColor="#000000"','')
            skin=skin.replace('foregroundColor="#ffffff"','')
        def __init__(self, session):
                self.session = session
                self["fav_name"] = Label()
                self["zeile1"] = Label()
                self["zeile1b"] = Label()
                self["zeile2"] = Label()
                self["zeile2b"] = Label()
                self["zeile3"] = Label()
                self["zeile3b"] = Label()
                self["zeile4"] = Label()
                self["zeile4b"] = Label()
                

                self["picture"] = Cover()
                self["picture"].updateIcon(9)

                self["playline2"] = ServicePositionGauge(self.session.nav)
                self["playline2"].hide()
                self["random"] = Pixmap()
                self["subdirs"] = Pixmap()
                self["auto"] = Pixmap()
                Screen.__init__(self, session)
                if fontlist[9]:
                    self.skinName = "wbrFS_r_site_e"
                else:
                    self.skinName = "wbrFS_r_site15"
                self["streamlogo"] = Pixmap()
                self.ersmal=1
                self.onShown.append(self.new_set)
                self.onLayoutFinish.append(self.pic_size)

        def pic_size(self):
            if self.ersmal:
                self.instance.setZPosition(3)
                self.p_widht=self["streamlogo"].instance.size().width()
                self.logo_pos=(self["streamlogo"].instance.position().x(), self["streamlogo"].instance.position().y())
                self.ersmal=None
                self.picload = ePicLoad()
                if fontlist[4]:
                   self.picload_conn = self.picload.PictureData.connect(self.set_logo)
                else:
                    self.picload.PictureData.get().append(self.set_logo)
                sc = AVSwitch().getFramebufferScale()
                self.picload.setPara((self["streamlogo"].instance.size().width(), self["streamlogo"].instance.size().height(), sc[0], sc[1], False, 1, '#FF000000'))

        def new_set(self,sets):
             if not sets:
                 self._exit()
             elif not onwbrScreenSaver:   
                self.sets=sets
                self.set()

        def new_Bild(self,pic=1):
              if not onwbrScreenSaver:   
                if L4LwbrFS and l4ls[23]=="True": # and l4ls[0]=="True" and l4ls[23]=="True":
                       L4LwbrFS.add( "wbrFS.01.pic2",{"Typ":"pic","Align": str(l4ls[24]),"Pos":int(l4ls[25]),"File":"/tmp/.wbrfs_pic","Size":int(l4ls[26]),"Screen":l4ls[3],"Lcd":l4ls[1],"Mode":"OnMedia"} )
                       if l4lR:L4LwbrFS.setScreen(l4ls[3],l4ls[1],True)
                try:
                    if pic==1:
                        self["picture"].updateIcon()
                    else:
                        self["picture"].updateIcon(9)
                except:
                    pass

        def set_logo(self, picInfo=None):
                  ptr = self.picload.getData()
                  if ptr != None:
                      self["streamlogo"].instance.setPixmap(ptr)

        def set(self):
            try:
              if not onwbrScreenSaver:  
                self["streamlogo"].show()
                self["zeile1"].setText(self.sets["fav"])
                self["zeile1b"].setText(self.sets["fav_text"].replace("&amp;","&"))
                self["zeile2"].setText(self.sets["bitrat"])
                self["zeile2b"].setText(self.sets["bitrat_text"])
                self["zeile3"].setText(self.sets["typ"])
                self["zeile3b"].setText(str(self.sets["typ_text"]))

                if self.sets["file"]:
                    self["streamlogo"].hide()
                    self["fav_name"].hide()
                    self["zeile4"].hide()
                    self["zeile4b"].hide()
                    self["playline2"].show()
                    self["random"].show()
                    self["subdirs"].show()
                    self["auto"].show()
                    self["auto"].instance.setPixmapFromFile(self.sets["autoplay"])
                    self["random"].instance.setPixmapFromFile(self.sets["random"])
                    self["subdirs"].instance.setPixmapFromFile(self.sets["subdirs"])
                else:
                    
                    self["playline2"].hide()
                    self["random"].hide()
                    self["subdirs"].hide()
                    self["auto"].hide()
                    self["zeile4"].show()
                    self["zeile4b"].show()
                    self["zeile4"].setText(self.sets["genre"])
                    self["zeile4b"].setText(str(self.sets["genre_text"].replace("&amp;","&")))
                    if self.sets["logo"]:
                         self["streamlogo"].show()
                         self["fav_name"].hide()
                         logo_pic=LoadPixmap(self.sets["logo"])
                         if logo_pic:
                             self.picload.startDecode(self.sets["logo"])
                         else:
                             self["streamlogo"].hide()
                             self["fav_name"].setText(self.sets["name_text"])
                             self["fav_name"].show()
                    else:
                         self["streamlogo"].hide()
                         self["fav_name"].setText(self.sets["name_text"])
                         self["fav_name"].show()
            except:
                pass

def playlist_read(playlist):
       f2=open(playlist,"r")
       line = f2.readline()
       pl=[]
       s=[None,None,None,None]
       title=None
       for line in f2:
         try:  
           line=line.strip()
           if line=="#EXTM3U" or not len(line):
              pass
           elif line.startswith('#EXTINF:'):
               sp1=line.split('#EXTINF:')[1].split(',',1)
               if len(sp1)==2:
                   length=sp1[0]
                   title=sp1[1]
                   s=[length,getEncodedString(title),None,None]
           elif not line.startswith(("#","http","www","rtsp")):
               if not title:
                  title= os.path.splitext(os.path.basename(line))[0]
                  s=[-1,getEncodedString(title),None,None]
               s[3]=getEncodedString(line)
               title=None
               if line.startswith("../"):
                   fpath2=os.path.dirname(os.path.abspath(playlist))
                   while line.startswith("../"):
                          dir2=fpath2.split('/')
                          fpath2=os.path.join(*dir2[:-1])
                          line=line[3:]
                   s[2]= os.path.join(fpath2,line)#.decode("cp1252").encode("utf-8")
               elif not line.startswith("/"):
                   s[2]=os.path.join(os.path.dirname(playlist),line)#.decode("cp1252").encode("utf-8")
               else:
                   s[2]=line#.decode("cp1252").encode("utf-8")
               if s[2]:
                   if not s[2].startswith("/"):
                       s[2]="/"+s[2]
                   s[2]=getEncodedString(s[2])
                   s[3]=getEncodedString(s[3])
                   pl.append(s)
         except:
            pass
       f2.close()
       return pl

def getEncodedString(value):
        returnValue = ""
        try:
                returnValue = value.encode("utf-8", 'ignore')
        except UnicodeDecodeError:
                try:
                        returnValue = value.encode("iso8859-1", 'ignore')
                except UnicodeDecodeError:
                        try:
                                returnValue = value.decode("cp1252").encode("utf-8")
                        except UnicodeDecodeError:
                                returnValue = "n/a"
        return returnValue

def str2bool(v=None):
  if v:
      return v.lower() in ("yes", "true")

def set_onwbrScreenSaver():
        global  onwbrScreenSaver
        if onwbrScreenSaver:
                onwbrScreenSaver = None
        else:
                onwbrScreenSaver = True

def set_groups(groups1):
        global  fav_groups
        fav_groups= groups1
        fav_groups.sort(key=lambda x: x[1].lower())

def set_display(Zeile1,Zeile2,Zeile3):
              if L4LwbrFS:     
                   if str2bool(l4ls[9]):
                       L4LwbrFS.add('wbrFS.01.txt1', {'Typ': 'txt',
                        'Align': str(l4ls[10]),
                        'Color': l4ls[29],
                        'Text': Zeile1,
                        'Pos': int(l4ls[11]),
                        'Size': int(l4ls[12]),
                        'Lines': int(l4ls[13]),
                        'Screen': l4ls[3],
                        'Lcd': l4ls[1],
                        'Mode': 'OnMedia'})
                   if str2bool(l4ls[14]):
                       L4LwbrFS.add('wbrFS.03.txt3', {'Typ': 'txt',
                        'Align': str(l4ls[15]),
                        'Color': l4ls[29],
                        'Text': Zeile3,
                        'Pos': int(l4ls[16]),
                        'Size': int(l4ls[17]),
                        'Lines': int(l4ls[18]),
                        'Screen': l4ls[3],
                        'Lcd': l4ls[1],
                        'Mode': 'OnMedia'})
                   if str2bool(l4ls[4]):
                       L4LwbrFS.add('wbrFS.02.txt2', {'Typ': 'txt',
                        'Align': str(l4ls[5]),
                        'Color': l4ls[29],
                        'Text': Zeile2,
                        'Pos': int(l4ls[6]),
                        'Size': int(l4ls[7]),
                        'Lines': int(l4ls[8]),
                        'Screen': l4ls[3],
                        'Lcd': l4ls[1],
                        'Mode': 'OnMedia'})


class Cover(Pixmap):
        def __init__(self):
                Pixmap.__init__(self)
                self.picload = ePicLoad()
                if fontlist[4]:
                   self.picload_conn = self.picload.PictureData.connect(self.paintIconPixmapCB)
                else:
                    self.picload.PictureData.get().append(self.paintIconPixmapCB)
                self.noCoverFile = def_pic
                self.updateIcon()

        def applySkin(self, desktop, screen):
                from Tools.LoadPixmap import LoadPixmap
                noCoverFile = None
                if self.skinAttributes is not None:
                        for (attrib, value) in self.skinAttributes:
                                if attrib == "pixmap":
                                        noCoverFile = value
                                        break
                if noCoverFile is None:
                        noCoverFile = def_pic
                return Pixmap.applySkin(self, desktop, screen)

        def onShow(self):
                Pixmap.onShow(self)
                sc = AVSwitch().getFramebufferScale()
                self.picload.setPara((self.instance.size().width(), self.instance.size().height(), sc[0], sc[1], False, 1, 'transparent'))

        def paintIconPixmapCB(self, picInfo=None):
          ptr = self.picload.getData()
          if ptr != None:
              self.instance.setPixmap(ptr)

        def updateIcon(self,Numx=2,file1=None):
          if self.instance:  
            sc = AVSwitch().getFramebufferScale()
            self.picload.setPara((self.instance.size().width(), self.instance.size().height(), sc[0], sc[1], False, 1, 'transparent'))     #
            if Numx ==4 and file1:
               if fileExists(file1):
                   self.instance.setPixmap(LoadPixmap(file1))
            else:
                picfile=None
                if fileExists("/tmp/.wbrfs_pic"):
                    picfile="/tmp/.wbrfs_pic"
                if Numx<9 and picfile:
                    try:
                        self.picload.startDecode("/tmp/.wbrfs_pic")
                    except:
                        self.instance.setPixmap(noCoverPixmap)
                else:
                   self.instance.setPixmap(noCoverPixmap)

def Codierung(text1="",sender="",typ=1):
        text2=""
        front=""
        rear=""
        weg_list= ':";()@+*-/.'
        if len(text1 and sets_exp):
            text1=text1.strip('\t\n\r').lower()
            if sender.lower()in text1:
                text1=text1.replace(sender.lower(),"")
            for x in weg_list:
                if x in text1:
                    text1=text1.replace(x, ' ')
            if len(sets_exp["picwords3"].strip()) and typ==1:
                if "," in sets_exp["picwords3"]:
                     excludes=sets_exp["picwords3"].split(",")
                else:
                     excludes=sets_exp["picwords3"].split(" ")
                for x in excludes:
                    if x.lower() in text1:
                         text1.replace(x.lower()," ")
            text2=text1
        if len(text2):
            if len(sets_exp["picwords1"].strip()) and typ==1:
                    if "," in sets_exp["picwords1"]:
                         front=sets_exp["picwords1"].split(",")
                    else:
                         front=sets_exp["picwords1"].split(" ")
                         front=' '.join(front)
            if len(sets_exp["picwords2"].strip()) and typ==1:
                    if "," in sets_exp["picwords2"]:
                         rear=sets_exp["picwords2"].split(",")
                    else:
                         rear=sets_exp["picwords2"].split(" ")
                         rear=' '.join(rear)
            text2=front+" "+text2+" "+rear
        elif len(sender):
                text2=sender
        text3=""
        text2=front+text2.replace("+"," ")+rear
        tSplit=text2.split(" ")
        text3='+'.join(x for x in tSplit if len(x.strip()))
        text3=  quote_plus(text3).strip()
        text3=text3.replace("+","%20")
        url=None
        if len(text3):
          if sets_grund["picsearch"]=="var1":
            url = "https://www.google.com/search?q=%s&tbm=isch&tbs=isz:l&client=firefox-b-d" % text3
          elif sets_grund["picsearch"]=="var2":
            url = "https://www.bing.com/images/search?q=%s&FORM=HDRSC2&qft=+filterui:photo-photo+filterui:aspect-tall&form=IRFLTR" % text3
          elif sets_grund["picsearch"]=="var3":
            url = "https://itunes.apple.com/search?term=%s&limit=25" % (text3)
        if url: url=url.replace("%2B","+")
        return url 

def grab_text(self,typ1=None,ersatz =""):
        if typ1:   
                mysTitle=ersatz
                mysTitle2=None
                currPlay = self.session.nav.getCurrentService()
                info = currPlay and currPlay.info()
                if currPlay is not None:
                        if typ1=="pvr1":
                                decoder = currPlay and currPlay.rdsDecoder()
                                mysTitle2 = decoder and decoder.getText(iRdsDecoder.RadioText) 
                        elif typ1=="pvr2":
                                decoder = currPlay and currPlay.rdsDecoder()
                                mysTitle2 = decoder and decoder.getText(iRdsDecoder.RtpText)                
                        elif typ1=="file":
                                mysTitle2 = info.getInfoString(iServiceInformation.sTagTitle).replace("_"," ")
                                sArtist = info.getInfoString(iServiceInformation.sTagArtist)
                                if len(sArtist):
                                        mysTitle2= sArtist+" "+mysTitle2
                        else:    
                                infs=info.getInfoString(iServiceInformation.sTagTitle)
                                if infs and infs is not None and len(infs)>2:
                                        mysTitle2 = infs
                if mysTitle2 and mysTitle2 is not None and len(mysTitle2)>2:
                     mysTitle=mysTitle2
                return(mysTitle)

def grab(sender="",sTitle=None):
        url=None
        if sTitle and len(sTitle.strip()):
                sTitle=sTitle.replace(":","").replace("-"," ").replace("("," ").replace(")"," ").split()
                sTitle='+'.join(sTitle)
                url=Codierung(sTitle,sender)#.encode("latin","ignore")
                #f=open("/tmp/001","w")
                #f.write(str(url)+"\n")
                #f.close()
                if url:  
                                user_agent = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3'
                                headers = { 'User-Agent' : user_agent }
                                if pyvers1==2:
                                     getPage(url, timeout=10, headers=headers).addCallback(grab2).addErrback(grab_err)  
                                else:
                                    callInThread(threadGetPage, url, grab2, grab_err,1)


def grab2(result):
          url1=None
          global pic_urls
          pic_urls=[]
          if result and len(result):
            
             startPos=10 
             anz=0
             if sets_grund["picsearch"] !="var3":
                    if sets_grund["picsearch"]=="var1":
                         begr=('src="','</div>')
                    if sets_grund["picsearch"]=="var2":
                         #begr=("murl","md5")
                         begr=("murl&quot;:&quot;","&amp;")
                    while startPos<len(result) and anz<10: 
                        bfoundPos = result.find(begr[0],startPos)
                        if bfoundPos == -1:
                                anz=100
                                break
                        bfoundPos2 = result.find(begr[1],bfoundPos)
                        if bfoundPos != -1 and bfoundPos2 != -1:
                            if sets_grund["picsearch"]=="var1":
                                url1 = result[bfoundPos+5:bfoundPos2-9]
                                url1 = url1.replace("%25","%")
                            else:
                                url = result[bfoundPos:bfoundPos2].lower()
                                cfound1 = url.find("http")
                                if ".jpg" in url:
                                   cfound2 = url.find(".jpg")
                                   url1= url[cfound1:cfound2+4]
                                elif ".png" in url:
                                   cfound2 = url.find(".png")
                                   url1= url[cfound1:cfound2+4]
                                elif ".jpeg" in url:
                                    cfound2 = url.find(".jpeg")
                                    url1= url[cfound1:cfound2+5]
                        else:
                             break
                        if not len(url1) or "blogspot" in url1 or "logos.tmdb" in url1:
                                url1=''
                        else:
                             if not url1 in pic_urls:   
                                if url1.startswith('http'):
                                    url1 = url1.replace("&amp;","&").replace("%25","%")
                                    pic_urls.append(url1)
                                    anz+=1
                        startPos=bfoundPos2+10
             elif sets_grund["picsearch"]=="var3": 
                bfoundPos = result.find('artworkUrl100')
                if bfoundPos != -1:
                    bfoundPos2 = result.find(', "',bfoundPos+1)
                    if bfoundPos != -1 and bfoundPos2 != -1:
                        url = result[bfoundPos+16:bfoundPos2-1]
                        if (url.startswith('http://') or url.startswith('https://')) and url.lower().endswith((".jpg",".jpeg")):
                          pic_urls.append(url)
          if len(pic_urls):
             pic_next()
          else:
              grab_err(None)

def pic_next():
         global pic_urls
         if len(pic_urls):    
             url3=pic_urls.pop(0)
             callInThread(threadGetPage, url3, pic_show, grab_err,2)
             #img_data = requests.get(url3).content
             #with open("/tmp/.wbrfs_pic", 'wb') as f:
             #    f.write(img_data)
             #pic_show("ok")
         else:
             grab_err()

def pic_next_err(*args):
    if len(pic_urls):
       pic_next()
    else:
       grab_err()

def grab_err(result=None):
    global pic_urls
    pic_urls=[]
    if write_debug>1: 
           if not result:
               d=debug("found pic failed")
           else:
               d=debug("found pic failed2\n"+str(result)+"\n")
    copyfile(def_pic, "/tmp/.wbrfs_pic")
    pic_show("noPic")

def pic_show(result=None,pic=None):
                p=1
                if pic:
                        coverArtFile = file("/tmp/.wbrfs_pic", 'wb')
                        coverArtFile.write(pic)
                        coverArtFile.close()
                elif result != "noPic":                   
                        if sets_rec["cover"]:  
                                if l4l_info["rec"] and result != "noPic" and onwbrScreenSaver == None:
                                        sp=sets_exp["coversafepath"]
                                        if cover_save["cache"]:
                                                for name in os.listdir(cover_save["path"]+"incomplete/"):
                                                        if not name.startswith(" - ."):     
                                                                pname=name.replace(".mp3",".jpg")	        
                                                                copyfile("/tmp/.wbrfs_pic",cover_save["path"]+pname)
                                        else:
                                                if cover_save["titel"]:
                                                        copyfile("/tmp/.wbrfs_pic",sets_exp["coversafepath"]+cover_save["titel"]+".jpg")
                else:
                    p=None
                if onwbrScreenSaver == None:right_site.new_Bild(p) 


class planer_list(Screen):
        def __init__(self, session, stream_liste=[]):
                self.termin_liste=[] #pliste
                self.streamliste=stream_liste
                Screen.__init__(self, session)
                tmpskin = open(fontlist[5]+"wbrFS_planer.xml")
                self.skin = tmpskin.read()
                tmpskin.close()
                if fontlist[9]:
                    self.skinName = "wbrFS_planer_e"
                else:
                     self.skin=self.skin.replace('backgroundColor="#000000"','')
                     self.skin=self.skin.replace('foregroundColor="#ffffff"','')
                     self.skinName = "wbrFS_planer"
                self['termine'] = List(self.termin_liste)
                self["termine"].enableWrapAround = True
        
                self['key_red'] = Label(_("Close"))
                self['key_green'] = Label(_("Edit"))
                self['key_yellow'] = Label(_("Delete"))
                self['key_blue'] = Label(_("Add new"))

                self.setTitle(_("I make my radio day"))
                self["actions"] = ActionMap(["wbrfsKeyActions"],
                        {
                                "ok": self.edit,
                                "cancel": self.exit,
                                "red": self.exit,
                                "yellow": self.dele,
                                "green": self.edit,
                                "blue": self.new,
                        })
                self.onLayoutFinish.append(self.layoutFinished)
                self.edit_back(2)

        def layoutFinished(self):
            self.onLayoutFinish.remove(self.layoutFinished)
            if fontlist[8] or fontlist[9]:
              try:
                if not fontlist[4]:
                    self['config'].instance.setFont(fontlist[3])
                    self['config'].instance.setItemHeight(fontlist[2])
                else:
                    from skin import parseFont
                    stylemgr = eWindowStyleManager.getInstance()
                    skinned = eWindowStyleSkinned()
                    eListboxPythonConfigContent.setDescriptionFont(parseFont(conf_font1, ((1,1),(1,1))))
                    eListboxPythonConfigContent.setValueFont(parseFont(conf_font2, ((1,1),(1,1))))
                    eListboxPythonConfigContent.setItemHeight(conf_item)
                    stylemgr.setStyle(0, styleskinned)
              except:
                  pass

        def edit(self):
                self.session.openWithCallback(self.edit_back, planer_edit, self["termine"].getCurrent(),self.streamliste)

        def new(self):
                self.session.openWithCallback(self.edit_back, planer_edit, "neu",self.streamliste)

        def edit_back(self,backs=1):
          right_site.show()
          if backs==2:
            global u_times
            self.termin_liste=[]
            u_times=read_plan().reading("1")
            ut= u_times
            ut.sort(key=lambda x: x[1], reverse=False)
            for x in u_times:
                art=_("Deactivated")
                if x[2]:
                    art=_("active")
                if x[3]['art'] == "select":
                   stream_id=x[3]["streamid"]
                   for x2 in self.streamliste:
                        if int(x2[0]) == stream_id:
                             stream=x2
                             break
                elif x[3]['art']=="off":
                     stream=(0,_("Exit webradioFS"))   
                elif x[3]['art']=="off_to_standy":
                     stream=(0,_("Exit webradioFS and standby"))                
                elif x[3]['art']=="on":
                     stream=(0,_("Start webradioFS"))
                elif x[3]['art']=="on_from_standby":
                     stream=(0,_("Start webradioFS from standby"))
                self.termin_liste.append((x[1],stream[1],art,stream[0],x,x[3]['setid']))
            self['termine'].setList(self.termin_liste)

        def dele(self):
             try:   
                pl_id=int(self["termine"].getCurrent()[5])
                d=read_plan().deling(pl_id)
                self.edit_back(2)
             except Exception as e:
                    f2=open("/var/webradioFS_debug.log","a")
                    f2.write(str(e)+"\n")
                    f2.write(str(self["termine"].getCurrent()[5])+"\n")
                    f.close()

        def exit(self):
                self.close()


class planer_edit(Screen, ConfigListScreen):
        def __init__(self, session,term,streamliste):
                if fontlist[5]==plugin_path +"/skin/SD/": 
                    right_site.hide()
                self.term=term
                self.streamliste=streamliste
                tmpskin = open(fontlist[5]+"wbrFS_setup.xml")
                self.skin = tmpskin.read()
                tmpskin.close()
                self.onChangedEntry = []
                now = [xl for xl in localtime()]
                tz1=now
                self.pl_id="neu"
                aktiv=True
                aktion="select"
                sender=self.streamliste[0][0]
                repeat="daily"
                stime=[tz1[3],tz1[4]]
                datum=time.time()
                weed=(True,True,True,True,True,True,True)
                if term and str(term) != "neu":
                      stime=term[4][3]['time']
                      sender=term[4][3]['streamid']
                      self.pl_id=term[4][3]['setid']
                      aktiv=term[4][2]
                      if term[4][3]['art']:aktion=term[4][3]['art']
                      if term[4][3]['repeat']:repeat=term[4][3]['repeat']
                      if term[4][3]['datum']:datum=term[4][3]['datum']
                      if term[4][3]['weekdays']:
                          weed=term[4][3]['weekdays']#.split(",")
                tz1[3]=int(stime[0])
                tz1[4]=int(stime[1])
                stime2=time.mktime(tz1)
                self.startTime=NoSave(ConfigClock(default =stime2))
                self.repeat = NoSave(ConfigSelection(default=repeat,choices = [("daily",_("Daily")),("once",_("Once only")),("weekdays",_("By weekday"))]))
                self.datum= NoSave(ConfigDateTime(default=datum, formatstring =  _("%A, %d.%m %Y"), increment = 86400))
                self.aktiv = NoSave(ConfigYesNo(default = aktiv))
                self.aktion = NoSave(ConfigSelection(default=aktion,choices = [("select",_("Select station")),("on",_("Start webradioFS")),("on_from_standby",_("Start webradioFS from standby")),("off",_("Exit webradioFS")),("off_to_standy",_("Exit webradioFS and standby"))]))
                self.sender= NoSave(ConfigSelection(default=sender,choices = self.streamliste))
                self.mo = NoSave(ConfigYesNo(default = weed[0]))
                self.di = NoSave(ConfigYesNo(default = weed[1]))
                self.mi = NoSave(ConfigYesNo(default = weed[2]))
                self.do = NoSave(ConfigYesNo(default = weed[3]))
                self.fr = NoSave(ConfigYesNo(default = weed[4]))
                self.sa = NoSave(ConfigYesNo(default = weed[5]))
                self.so = NoSave(ConfigYesNo(default = weed[6]))
                Screen.__init__(self, session)
                if fontlist[9]:
                    self.skinName = "WebradioFSSetup_e"
                else:
                   self.skin=self.skin.replace('backgroundColor="#000000"','')
                   self.skin=self.skin.replace('foregroundColor="#ffffff"','')
                   self.skinName = "WebradioFSSetup_13"
                self.refresh()
                ConfigListScreen.__init__(self, self.list, on_change = self.reloadList)
                self["green_pic"] = Pixmap()
                self["rec_txt"] = Label(_("Edit this termin"))
                self["playtext"] = StaticText("")
                self["key_red"] = Label(_("Cancel"))
                self["pic_red"] = Pixmap()
                self["key_green"] = Label(_("Save"))
                self["pic_green"] = Pixmap()
                self["key_yellow"] = Label("")
                self["pic_yellow"] = Pixmap()
                self["key_blue"] = Label("")
                self["pic_blue"] = Pixmap()
                self["actions"] = ActionMap(["wbrfsKeyActions"],
                        {
                                "cancel": self.Cancel,
                                "red": self.Cancel,
                                "green": self.save,
                                "ok": self.press_ok,
                        }, -2
                )
                self.setTitle("webradioFS: " +_("Edit this termin"))
                self.onLayoutFinish.append(self.layoutFinished)

        def layoutFinished(self):
            self.onLayoutFinish.remove(self.layoutFinished)
            self.instance.setZPosition(2)
            self.reloadList()

        def reloadList(self):
                self.refresh()
                self["config"].setList(self.list)

        def refresh(self):
                list=[]
                list.append(getConfigListEntry( _("Active:"),self.aktiv))
                list.append(getConfigListEntry( _("Action:"),self.aktion))
                if self.aktion.value=="select":
                     list.append(getConfigListEntry(_("Station:"),self.sender ))
                list.append(getConfigListEntry( _("Time for action:"),self.startTime))
                list.append(getConfigListEntry( _("Repeat:"),self.repeat))
                if self.repeat.value=="once":
                    list.append(getConfigListEntry( _("Date:"),self.datum))
                elif self.repeat.value=="weekdays":
                    list.append(getConfigListEntry( _("Monday")+":",self.mo))
                    list.append(getConfigListEntry( _("Tuesday")+":",self.di))
                    list.append(getConfigListEntry( _("Wednesday")+":",self.mi))
                    list.append(getConfigListEntry( _("Thursday")+":",self.do))
                    list.append(getConfigListEntry( _("Friday")+":",self.fr))
                    list.append(getConfigListEntry( _("Saturday")+":",self.sa))
                    list.append(getConfigListEntry( _("Sunday")+":",self.so))
                self.list=list

        def press_ok(self):
                if self["config"].getCurrent()[1]==self.sender:
                    l=[]
                    for x in self.streamliste:
                        l.append((x[1],x[0]))
                    self.session.openWithCallback(self.press_ok_back, ChoiceBox, title=_("Select station"), list=(l))
        def press_ok_back(self,ret):
                if ret:
                   self.sender.setValue(ret[1])
        def Cancel(self):
            self.close(1)
        def save(self):
                err=None
                nam='%0.2d:%0.2d' % (self.startTime.value[0],self.startTime.value[1])
                weedk='None'
                datumr='None'
                if self.repeat.value=="weekdays":
                    wds=(self.mo.value,self.di.value,self.mi.value,self.do.value,self.fr.value,self.sa.value,self.so.value)
                    weedk=(','.join(str(x) for x in wds))
                if self.repeat.value=="once":
                    if datetime.date.today() > datetime.date.fromtimestamp(self.datum.value):
                          err=1
                          self.session.open(MessageBox, _("Appointment can not start in the past"),MessageBox.TYPE_ERROR)
                    else:
                        datumr=str(self.datum.value)
                wert=';'.join((str(self.sender.value),str(self.aktiv.value),self.aktion.value,self.repeat.value,datumr,weedk))
                if not err:
                    d=read_plan().writing(self.pl_id,nam,wert)
                    self.close(2)

def debug(result=None):
        if result:
                lines=""
                if fileExists("/var/webradioFS_debug.log"):
                  f=open("/var/webradioFS_debug.log","r")
                  lines= f.readlines()
                  f.close()
                f=open("/var/webradioFS_debug.log","w")
                if len(lines)>200:
                        lines=lines[53:]
                else:
                   lines=lines[3:]
                f.write("log from webradioFS, Version "+myversion+"\n")
                for x in lines:
                        f.write(x)   
                f.write("-->"+result.strip()+"\n")
                f.close() 


class blocker():
    def __init__(self):
                self.blocktimer = None
    def set(self):
             self.blocktimer = eTimer()
             if fontlist[4]:
                     self.blocktimer_conn = self.blocktimer.timeout.connect(self.press)
             else:
                    self.blocktimer.timeout.get().append(self.press)
             self.blocktimer.startLongTimer(600)       
    def start(self):
        if self.blocktimer:
             self.blocktimer.startLongTimer(600)
        else:
             self.set()     
    def press(self):
            self.blocktimer.stop()
            amap = eActionMap.getInstance()
            amap.keyPressed("dreambox remote control (native)", 385, 0)
            amap.keyPressed("dreambox remote control (native)", 385, 1)
            self.blocktimer.startLongTimer(600)
    def stop(self): 
             if self.blocktimer:
                 self.blocktimer.stop()
                 self.blocktimer=None


