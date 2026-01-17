from . import pyvers1, _
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.InputBox import InputBox
from Screens.ChoiceBox import ChoiceBox
from Screens.LocationBox import LocationBox
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from skin import parseColor
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.config import config , ConfigSubsection, ConfigYesNo, ConfigInteger, ConfigSelection, NoSave, ConfigDirectory, ConfigSlider, ConfigSet
from Components.config import configfile,getConfigListEntry, ConfigText
from Components.ConfigList import ConfigListScreen, ConfigList
from Components.FileList import FileList
from Components.AVSwitch import AVSwitch
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List
from Components.MultiContent import MultiContentEntryText,MultiContentEntryPixmapAlphaTest
from Tools.Directories import *
from enigma import ePoint, eSize, eTimer, eLabel, eWidget,gFont,ePicLoad

from enigma import eServiceReference
from enigma import quitMainloop
from enigma import eListboxPythonMultiContent, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, gFont, eListbox#, getDesktop
from enigma import eConsoleAppContainer
import os
from os import listdir, path, chmod, remove, popen
from time import *
import urllib, socket
import ssl
if pyvers1==3:
    from urllib.parse import quote,quote_plus,urlparse,urlencode
    from urllib.request import urlopen, Request
    import http.client as httplib
    from urllib.error import HTTPError, URLError
else:
    from urllib import quote,quote_plus
    from urlparse import urlparse
    from urllib import urlencode

    from urllib2 import urlopen, Request, URLError,HTTPError
    import httplib
import uuid, random
#from urlparse import urlparse
import threading
from sqlite3 import dbapi2 as sqlite
try:
   from mutagen.easyid3 import EasyID3
   from mutagen.easymp4 import EasyMP4
   from mutagen.flac import FLAC
   from mutagen.id3 import ID3
   from mutagen.mp3 import MP3
   from mutagen.oggvorbis import OggVorbis
   mutagen=True
except:
   mutagen=None
try:
    import tarfile
except ImportError as e:
    tarfile = None

set_file='/etc/ConfFS/webradioFS_sets.db'
plugin_path = '/usr/lib/enigma2/python/Plugins/Extensions/webradioFS'

class read_settings1:
  def reading(self,sets_liste=None):
    if sets_liste:
        if "prog" in sets_liste:
            self.sets_prog={"version":0,"wbrmeld":"","hauptmenu": False,"DPKG":False,"exttmenu":True}
        if "grund" in sets_liste:    
            self.sets_grund={"picsearch":"var1","favpath":"/etc/ConfFS/","exitfrage":False,"stream_sort":1,"wbrbackuppath":"/media/hdd/","startstream1":0,"skin_ignore":False,"zs":False}
        if "opt" in sets_liste:
            self.sets_opt={"rec":False,"views":False,"expert":0,"scr":False,"lcr":False,"audiofiles":False,"tasten":False,"display":False,"sispmctl":False}
        if "rec" in sets_liste:
            self.sets_rec={"path":"/media/hdd/","split":True,"new_dir":True,"cover":True,"anzeige":True,"inclp_save":True,"caching":0,"rec_caching_dir":"/media/hdd/"}
        if "audiofiles" in sets_liste:
            self.sets_audiofiles={"audiopath":"/media/hdd/","subdirs":True,"autoplay":False,"sort":True,"save_random":True,"audio_listpos":False,"schleife":True,"audio_listnums":"0,0,0,0"}
        if "exp" in sets_liste:
            self.sets_exp={"reconnect":3,"versions_info":"True","timeout":10,"conwait":3,"logopath":"/etc/ConfFS/streamlogos/","coversafepath":"/etc/ConfFS/cover/",
                "FBts_liste":"0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24","al_vol_max":50,"ex_vol":0,"start_vol":0,"vol_auto_time":8,
                "picwords1":"","picwords2":"","picwords3":"","offtimer_time":120,"offtimer_art":0,"wbrfspvrpath":"/usr/share/enigma2/Picon/","min_bitrate":0,"debug":0,"stop_abschalt":False}
        if "scr" in sets_liste:
            self.sets_scr={"screensaver_art":"wechsel","color":"005B00","bgcolor":"000000","bgcolor_random":0,"slideshow_bgcolor":"000000","Keyword":"Hund",
                "slideshow_time":10,"slideshowpath":"/media/hdd/","slideshow_subdirs":True,"slideshow_space":0,"timeout":60,
                "wbrvideorecurr":30,"wbrvideopath":"/media/hdd/","wbrvideofile":"/","textfix":False,"colfromskin":True}
        if "view" in sets_liste:
            self.sets_view={"logos":True,"Listlogos":True,"font_size":22,"only_foto":False,
                "displayb":'0,1,2,30,250,4,Zeile2,,0,14,12,False',
                "l4l":"True,1,True,3,True,0,30,20,1,True,0,0,20,1,True,0,60,20,1,True,2,0,200,True,0,100,200,40,22,white"}
        if "sispmctl" in sets_liste:
                self.sets_sispmctl={"start":"2,2,2,2","exit":"2,2,2,2","ssr1":"2,2,2,2","ssr2":"2,2,2,2",
                 "nvers1":"Switching Version 1","vers1":"2,2,2,2","nvers2":"Switching Version 2","vers2":"2,2,2,2"}    
        all_sets=[]
        connection = sqlite.connect(set_file)
        connection.text_factory = str
        cursor = connection.cursor()
        for setx in sets_liste: 
          try:
            for key,var in vars(self)["sets_"+setx].items():
                cursor.execute('SELECT wert1 FROM settings WHERE nam1 = "%s" AND group1 = "%s";' % (key,setx))
                row = cursor.fetchone()
                if row is None:
                    uni=str(setx)+str(key)
                    cursor.execute("INSERT OR IGNORE INTO settings (group1,nam1,wert1,wert2) VALUES(?,?,?,?);",  (setx,key,str(var),uni))
                    connection.commit()
                else:
                    if len(str(row[0])):
                        try: 
                            vars(self)["sets_"+setx][key]=int(row[0]) 
                        except:
                            if row[0].strip() in ("False","false","None","none"):
                                vars(self)["sets_"+setx][key] = False
                            elif row[0].strip() in ("True","true"):
                                vars(self)["sets_"+setx][key] = True
                            else:
                                vars(self)["sets_"+setx][key] = row[0].strip()
            all_sets.append(vars(self)["sets_"+setx])
          except:
             continue
        cursor.close()
        connection.close()
        return  all_sets

class read_einzeln:
  def reading(self,names=None):
        if names:
            return_liste=[]
            connection = sqlite.connect(set_file)
            connection.text_factory = str
            cursor = connection.cursor()
            for einz in names:
                cursor.execute('SELECT wert1 FROM settings WHERE group1 = "%s" AND nam1 = "%s";' % (einz[0],einz[1]))
                row = cursor.fetchone()
                if row is None:
                    return_liste.append(None)
                else:
                    if len(str(row[0])):  
                        try: 
                            return_liste.append(int(row[0])) 
                        except:
                            if "expert" in einz:
                                if row[0].strip() in ("True","true"):
                                    return_liste.append(1)
                                elif row[0].strip() in ("False","false","None","none"):
                                    return_liste.append(0)
                            elif row[0].strip() in ("False","false","None","none"):
                                return_liste.append(False)
                            elif row[0].strip() in ("True","true"):
                                return_liste.append(True)
                            else:
                                return_liste.append(row[0].strip())
            cursor.close()
            connection.close()
            return  return_liste
#////// planer
class read_plan:
    def reading(self,anfrage=None):
       if anfrage:
            return_liste=[]
            connection = sqlite.connect(set_file)
            connection.text_factory = str
            cursor = connection.cursor()
            cursor.execute('SELECT nam1,wert1,id FROM settings WHERE group1 = "plan" ;') 
            for row in cursor:
                  ut=row[0].split(":")
                  ut1=(int(ut[0]),int(ut[1]))
                  sets=row[1].split(";")
                  active=False
                  if len(sets)>1 and sets[1].strip() in ("True","true"):
                      active=True
                  art="select"
                  if len(sets)>2 and sets[2].strip() !="None":
                      art=sets[2]
                  repeat="daily"
                  if len(sets)>3 and sets[3].strip() !="None":repeat=sets[3]
                  datum=None
                  if len(sets)>4 and sets[4].strip() !="None":
                      datum=float(sets[4])
                  weekdays=None
                  if len(sets)>5 and sets[5].strip() !="None":
                      weekdays1=sets[5].split(",") 
                      weekdays=[]
                      for day in weekdays1:
                           d=False
                           if day=="True":
                               d=True
                           weekdays.append(d)
                  term1={"active":active,"streamid":int(sets[0]),"setid":row[2],"time":ut1,"art":art,"repeat":repeat,"datum":datum,"weekdays":weekdays}
                  for i in range(6, 10):
                      arg= None
                      if len(sets)>i and str(sets[i]) != "None":
                          arg= sets[i]
                      strarg="arg"+str(i)
                      term1.update({strarg:arg})
                  return_liste.append((None,row[0],active,term1))
            cursor.close()
            connection.close()
            return  return_liste

    def deling(self,pl_id=None):
       if pl_id:
                connection = sqlite.connect(set_file)
                connection.text_factory = str
                cursor = connection.cursor()
                cursor.execute('DELETE  FROM settings WHERE id = "%d"' % pl_id)
                cursor.close()
                connection.commit()

    def writing(self,pl_id=None,nam=None,wert=None):
           if pl_id and nam and wert:
                connection = sqlite.connect(set_file)
                connection.text_factory = str
                cursor = connection.cursor()
                if str(pl_id) != "neu":
                    wert2=str(nam)+str(pl_id)
                    cursor.execute('UPDATE OR IGNORE settings SET nam1=?,wert1=?,wert2=? WHERE id=?', (nam,wert,wert2,pl_id))
                else:
                    cursor.execute('SELECT max(id) from settings')
                    max1 = cursor.fetchone()
                    wert2=str(nam)+str(max1[0]+1)
                    cursor.execute('INSERT OR IGNORE INTO settings (group1,nam1,wert1,wert2) Values (?,?,?,?)', ("plan",nam,wert,wert2))
                cursor.close()
                connection.commit()
#////////// planer ende

fp=read_einzeln().reading((("grund","favpath"),("prog","DPKG")))


DPKG = fp[1]
if fp[0] and path.exists(fp[0]):
    myfav_path = fp[0]
else:
    myfav_path = '/etc/ConfFS/'
myfav_file = path.join(myfav_path,'webradioFS_favs.db')    

class StreamPlayer:
    def __init__(self, session, args = 0):
        self.is_playing = False
        self.session = session

    def __onStop(self):
        self.stop()

    def play(self, url):
        if self.is_playing:
            self.stop()
        try:
            serv = '4097:0:0:0:0:0:0:0:0:0:%s' % quote(url)
            esref = eServiceReference(serv)
            self.session.nav.playService(esref)
            self.is_playing = True
        except Exception as e:
            f=open("/tmp/webradioFS_debug.log","a")
            f.write(str(e)+"\n")
            f.close()

    def stop(self, text = ''):
        if self.is_playing:
            try:
                self.is_playing = False
                self.session.nav.stopService()
                self.exit()
            except TypeError as e:
                self.exit()

    def exit(self):
        self.stop()

class Streamlist:

    def streams(session, stream = None, typ = None,timeout1=10,etest=None):
        from .webradioFS import fontlist
        streamliste = []
        socket.setdefaulttimeout(timeout1)
        typ_check = 'mp3'
        status = 200
        reason = ''
        htyp = ''
        t_url = None
        conn = None
        typ7 = None
        typ1=typ
        if stream:
            read_timer = eTimer()
            try:
            #if 1==1:
                linex = None
                stream1 = stream
                request = Request(stream)
                request.add_header('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686; it-IT; rv:1.9.0.2')
                path = urlopen(request, None, 5)
                if fontlist[4]:
                    read_timer_conn = read_timer.timeout.connect(path.close)
                else:
                    read_timer.callback.append(path.close)
                p1 = path.info().get('content-type')
                p2 = path.geturl()
                if p2:
                    stream = p2
                #f7=open("/tmp/001","a")
                #p1.json()
                #out = path.info().json()
                out = dict(path.info())
                #f7.write(str(out)+"\n")
                #f7.write(str(path.info())+"\n")
                #f7.close()
                if pyvers1==3:
                    i1 = dict(path.info())
                else:
                    i1 = path.info().dict
                
                if 'content-type' in i1 and etest==None:
                    typ7 = i1['content-type']
                    if 'text' in typ7:
                        stream = stream1
                    elif typ7 == 'audio/x-scpls':
                        typ_check = 'pls'
                        typ = 'pls'
                    elif typ7 == 'audio/mpeg':
                        typ_check = 'mp3'
                        typ = 'mp3'
                    elif typ7 == 'audio/x-ms-wma':
                        typ_check = 'wma'
                        typ = 'wma'
                read_timer.startLongTimer(timeout1)
                linex2 = path.read(1000)
                #f7.write(str(linex2)+"\n")
                #f7.write(str(typ)+"\n")
                if etest:
                    f=open("/tmp/webradioFS_debug.log","a")
                    f.write("streamtest ==> "+str(stream)+"\n")
                    f.write(str(i1)+"\n")
                    f.close()
                if len(linex2):
                    linex = linex2.splitlines()#('\n')
                    #linex=None
                if linex and (typ == 'pls' or typ == 'm3u' or stream.endswith('pls') or stream.endswith('m3u')):
                    for x in linex:
                        str2=None
                        if len(x.strip()) > 1 and len(x.strip()) < 200:
                            if x.strip().startswith('http'):
                                str2=x.strip()
                            else:
                                try:
                                    zeile = x.split('=')
                                    if len(zeile) > 1 and len(x.strip()) < 200:
                                        if zeile[1].strip().startswith('http'):
                                            str2=zeile[1].strip()
                                except:
                                    pass
                            if str2:
                               if ".antenne.de/" in str2:
                                 str2=str2.replace("http:","https:")
                               streamliste.append(str2)
                if not len(streamliste):
                    streamliste = [stream, stream]
                if len(streamliste) == 1:
                    streamliste = [streamliste[0], streamliste[0]]
                return (streamliste, typ1, stream)
            except HTTPError as err:
                return (None, "st_l_a, "+str(err))
            except URLError as err:
                error = 'Error: '
                if hasattr(err, 'code'):
                    error += str(err.code)
                if hasattr(err, 'reason'):
                    error += str(err.reason)
                return (None, "st_l_b, "+error)
            except socket.timeout:
                return (None, "st_l_c, "+'timeout')
            except Exception as e:
                return (None, "st_l_d, "+str(e))
            #f7.write(str(streamliste)+"\n")
            return (None, 'unknown error')


class wbrfs_message(Screen):
    def __init__(self, session):
        from .webradioFS import fontlist
        self.Faktor=1
        if fontlist[6]>1600:self.Faktor=1.5
        self.fonts=fontlist
        self.font_size=22
        self.max_size=(int(70*self.fonts[6]/100),self.fonts[7])
        tmpskin = open(fontlist[5]+"wbrfs_meld.xml")
        self.skin = tmpskin.read()
        tmpskin.close()
        Screen.__init__(self, session)
        if fontlist[9]:
             self.skinName = "wbrfs_message_e"
        else:
             self.skinName = "wbrfs_message"
        self.shown = False
        self['text'] = Label()
        self['titel'] = Label()
        self['time'] = Label()
        self['bgr'] = Label()
        self.mListe= MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
        self['list'] = self.mListe

    def start(self, text = 'unknown', titel = 'webradioFS', aktion = None, default = False, type1 = 'INFO', timeout = 0,sd=3,fonts1=None):
        self.instance.setZPosition(4)
        self['text'].instance.resize(eSize(*self.max_size))
        self['titel'].setText(' ' + titel)
        self['time'].setText(" 00 ")
        if timeout > 0:
            self['time'].setText(str(timeout))
        titelSize = self["titel"].getSize()
        titelSize = eSize(*titelSize)
        timeSize = self["time"].getSize()
        timeSize = eSize(*timeSize)
        self['time'].setText("")
        self['titel'].instance.resize(eSize(titelSize.width()+150, 50))
        self.back_color = parseColor('#000000')
        if type1 == 'INFO':
            self.back_color = parseColor('#006400')
        elif type1 == 'ERROR':
            self.back_color = parseColor('#8B0000')
        elif type1 == '??':
            self.back_color = parseColor('#8B6508')
        text=text+"\n."
        self['text'].setText(text)
        textSize = self["text"].getSize()
        textSize = (textSize[0]+70+int(20*self.Faktor), textSize[1]+int(20*self.Faktor))
        textSize2 = eSize(*textSize)
        self['text'].setText(text[:-1])
        self.aktion = aktion
        self.default = default
        breit=textSize2.width()+int(20*self.Faktor)
        high = textSize2.height()+80
        if breit < (titelSize.width()+int(100*self.Faktor)+timeSize.width()):
            breit=titelSize.width()+int(120*self.Faktor)+timeSize.width()+int(20*self.Faktor)
        self.liste = [(_('No'),None,False,type1)]
        if type1 == '??':
            self.liste = [(_('Yes'),aktion,True,type1),(_('No'),aktion,False,type1)]
        elif aktion:
            self.liste = [(_('Yes'), aktion,True,type1)]
        num = 0
        i_res=[]
        for x in self.liste:
                 m_res=[x]
                 if x and len(x):
                     txt= " "*4+str(x[0])
                     m_res.append(MultiContentEntryText(pos = (0, 0), size = (breit, self.fonts[2]+10), font=0,text = "",color=0xffffff,backcolor=0x8B6508,color_sel=0x000000,backcolor_sel = 0x000000))
                     if txt:m_res.append(MultiContentEntryText(pos = (10, 5), size = (breit-60, self.fonts[2]), font=0,text = txt,color=0xffffff,backcolor=0x8B6508,color_sel=0x000000,backcolor_sel = 0xffffff, flags = RT_HALIGN_LEFT | RT_VALIGN_CENTER))  #,color=0x000000,backcolor=0x00008B,color_sel=0xf47d19,backcolor_sel = 0x000000
                 i_res.append(m_res)
        if len(i_res):self.mListe.setList(i_res)
        if type1 == '??':
            self['list'].instance.setBackgroundColor(parseColor("#000000"))
            self['list'].instance.setItemHeight(int(self.font_size*self.Faktor)+5)
            self['list'].resize(eSize(breit-40, (self.fonts[2]+10)*len(self.liste)  ))
            self.mListe.l.setItemHeight(self.fonts[2]+10)
            if not self.fonts[4]:
               self.mListe.l.setFont(0, self.fonts[3])
            if default != True: num = 1
            vo=high +20
            self['list'].instance.move(ePoint(20, vo))
            self['list'].show()
            high = vo+10+int(80*self.Faktor)
        else:
            self['list'].hide()
        self['text'].instance.resize(textSize2)
        self.instance.resize(eSize(*(breit, high)))
        self.instance.move(ePoint((self.fonts[6]-breit)/2, (self.fonts[7]-high)/2))
        self.instance.setTitle(titel)
        self['time'].instance.move(ePoint(breit-timeSize.width()-int(40*self.Faktor), 10))
        self['bgr'].instance.resize(eSize(breit, high))
        self['bgr'].instance.setBackgroundColor(self.back_color)
        self['list'].moveToIndex(num)
        self.show()

    def set_c_count(self, c_time = None):
        if c_time:
            try:
                self['time'].setText(c_time)
            except:
                pass

    def stop(self):
        self.hide()
        try:
            return self['list'].getCurrent()[0]
        except:
            return(None)
    def move(self,index=None):
        try:
            if index:
                if index=="vor":
                    index=self['list'].instance.getCurrentIndex()+1
                    if index > len(self.liste)-1:
                        index=0
                elif index=="back":
                    index=self['list'].instance.getCurrentIndex()-1
                    if index <0:
                        index=len(self.liste)-1
                self['list'].instance.moveSelectionTo(index)
        except:
            pass


class write_settings():
  def __init__(self,li3=None):
      if li3:
          connection = sqlite.connect(set_file)
          connection.text_factory = str
          cursor = connection.cursor()
          for x in li3:
            if len(x):  
              name,sets=x
              if name and sets:    
                  for key,var in sets.items():
                      cursor.execute('SELECT id FROM settings WHERE nam1 = "%s" AND group1 = "%s";' % (key,name))
                      row = cursor.fetchone()
                      if row is None: 
                          wert2=name+key
                          cursor.execute("INSERT INTO settings (group1,nam1,wert1,wert2) VALUES(?,?,?,?);",  (name,key,str(var),wert2))
                      else:
                          cursor.execute('UPDATE settings SET wert1 = ? WHERE id = ?;',  (str(var),row[0]))
                      connection.commit()
          cursor.close()
          connection.close()


class BackupLocationBox(LocationBox):
    def __init__(self, session, text, filename, dir = None, minFree = None):
        inhibitDirs = ['/bin',
         '/boot',
         '/dev',
         '/lib',
         '/proc',
         '/sbin',
         '/sys',
         '/usr',
         '/var']
        LocationBox.__init__(self, session, text=text, filename=filename, currDir=dir, bookmarks=None, inhibitDirs=inhibitDirs, minFree=minFree)
        self.skinName = 'LocationBox'


class filemenu:
    def __init__(self, session):
        self.session = session
        self.settigspath = None
        self.num = None
        self.file = None
        self.msg=None
    def start(self,num = None):
        from .webradioFS import fontlist
        from .webradioFS import right_site
        right_site.hide()
        if num:
            self.num = num
        if self.num == 1:
            self.cBackup
        elif 3 < self.num < 6:
            self.restore()
        elif 1 < self.num < 4:
            self.backup()

    def backup(self):
        self.session.openWithCallback(self.callBackup, BackupLocationBox, _('Please select the backup path...'), '')

    def callBackup(self, path_b):
        if self.num and path_b is not None:
            if pathExists(path_b):
                if self.num == 2:
                    self.settigspath = path.join(path_b,'wbrFS_Favs.tar.gz')
                elif self.num == 3:
                    self.settigspath = path.join(path_b,'ConfFS_backup.tar.gz')
                if path.isfile(self.settigspath):
                    self.session.openWithCallback(self.callOverwriteBackup, MessageBox, _('Overwrite existing Backup?'), type=MessageBox.TYPE_YESNO)
                else:
                    self.callOverwriteBackup(True)
            else:
                self.err(_('Backup failed'))
        else:
            self.err(_('Backup failed'))

    def callOverwriteBackup(self, res):
        if res:
            self.cBackup()

    def cBackup(self, num = None):
        if num:
            self.num = num
        if self.num == 1:
            self.settigspath = '/etc/wbrFS_oldfav.tar.gz'
        if self.num and self.settigspath:
            mpath = '/etc/ConfFS/'
            if pathExists(mpath) is True:
                files = []
                if self.num == 2:
                        files.append(myfav_file)
                        files.append(set_file)
                else:
                        for file1 in listdir(mpath):
                            files.append('/etc/ConfFS/' + file1)
                comp = self.getCompressionMode(self.settigspath)
                if tarfile:
                    try:
                        f = tarfile.open(self.settigspath, 'w:%s' % comp)
                        for sourcefile in files:
                                if path.exists(sourcefile):
                                        f.add(sourcefile)
                        f.close()
                        self.session.open(MessageBox, _('Backup from settings successfully'), type=MessageBox.TYPE_INFO, timeout=15)
                    except Exception as e:
                        self.session.open(MessageBox, _('Backup-Error:')+str(e), type=MessageBox.TYPE_ERROR, timeout=15)
                else:
                    try:
                        tarFiles = ' '.join(files)
                        lines = popen('tar cv%sf %s %s' % (comp,self.settigspath, tarFiles)).readlines()
                        self.session.open(MessageBox, _('Settings were restored successfully'), type=MessageBox.TYPE_INFO, timeout=15)
                    except Exception as e:
                        self.session.open(MessageBox, _('Backup-Error:')+str(e), type=MessageBox.TYPE_ERROR, timeout=15)

    def getCompressionMode(self, tarname):
                isGz = tarname.endswith((".tar.gz", ".tgz"))
                isBz2 = tarname.endswith((".tar.bz2", ".tbz2"))
                if tarfile:
                        return 'gz' if isGz else 'bz2' if isBz2 else ''
                else:
                        return 'z' if isGz else 'j' if isBz2 else ''

    def restore(self):
        self.tarfile = 'wbrFS_Favs.tar.gz'
        if self.num == 5:
            self.tarfile = "ConfFS_backup.tar.gz"
        self.session.openWithCallback(self.callRestore, BackupLocationBox, _('Please select the restore path...'), '')

    def callRestore(self, path1):
        if self.tarfile and path1:
            self.settigspath = path.join(path1,self.tarfile)
            if self.tarfile == "ConfFS_backup.tar.gz" and not fileExists(self.settigspath):
                 self.settigspath = path.join(path1,'ConfFS.tar.gz')
            if path.isfile(self.settigspath):
                self.session.openWithCallback(self.callOverwriteSettings, MessageBox, _('Overwrite existing Files?'), type=MessageBox.TYPE_YESNO)
            else:
                self.err( _('File %s nonexistent.'))
        else:
            self.err(_('restore failed'))

    def callOverwriteSettings(self, res = None):
        if res:
                comp = self.getCompressionMode(self.settigspath)
                if tarfile:
                    try:
                        tarball = tarfile.open(self.settigspath, 'r:%s' % comp)
                        for file_ in tarball:
                                if not file_.name.startswith("/"):file_.name="/"+file_.name
                                if not path.isdir:remove(file_.name)
                                tarball.extract(file_)
                                try:
                                    chmod(file_.name, file_.mode)
                                except:
                                    pass
                        self.session.open(MessageBox, _('Settings were restored successfully')+"\n"+_('Please restart webradioFS') , type=MessageBox.TYPE_INFO, timeout=15)
                    except Exception as e:
                        self.session.open(MessageBox, _('Restore-Error:')+str(e), type=MessageBox.TYPE_ERROR, timeout=15)
                else:
                    try:
                        lines = popen('tar xv%sf %s -C /' % (comp, self.settigspath)).readlines()
                        self.session.open(MessageBox, _('Settings were restored successfully')+"\n"+_('Please restart webradioFS'), type=MessageBox.TYPE_INFO, timeout=15)
                    except Exception as e:
                        self.session.open(MessageBox, _('Restore-Error:')+str(e), type=MessageBox.TYPE_ERROR, timeout=15)

    def err(self, res):
        self.session.openWithCallback(self.r_site,MessageBox, res, type=MessageBox.TYPE_ERROR, timeout=20)

    def r_site(self,res=None):
            from .webradioFS import right_site
            right_site.show()

class load_rf:
    def __init__(self, session):
        self.session = session
        self.arm=None
        self.ok=1
        rd = open("/proc/cpuinfo", "r").readlines()
        for line in rd:
            if line.startswith('model name') and 'ARM' in line:
                self.arm=True 

    def run(self):
        self.install=None
        from .webradioFS import fontlist
        self.container=eConsoleAppContainer()
        if fontlist[4]:
            self.dataAvail_conn = self.container.dataAvail.connect(self.read_data)
        else:
            self.container.dataAvail.append(self.read_data)
        self.container.execute("opkg install %s" % "streamripper")

    def read_data(self, retval):
        if not fileExists('/usr/bin/streamripper'):
            if retval:
              f=open("/var/webradioFS_debug.log","a")
              f.write(">> install record module\nfile not exist, system-message:\n"+str(retval)+"\n")
              f.close()
            self.run2()
        else:
            if self.arm and path.getsize('/usr/bin/streamripper')>100000:
                  f=open("/var/webradioFS_debug.log","a")
                  f.write(">> install record module\nfailed Version for ARM-Box\n")
                  f.close()
                  self.run2()
            else:
                self.f()

    def run2(self):
        if self.arm:
             self.s('/strf/strr_arm', '/usr/bin/streamripper')
        else:
            self.s('/strf/strr', '/usr/bin/streamripper')
        self.s('/strf/slv1', '/usr/lib/libvorbis.so.0.4.3')
        self.s('/strf/slv2', '/usr/lib/libvorbisenc.so.2.0.6')
        self.f()

    def s(self, url, file1):
       pass

    def f(self):
        from .webradioFS import right_site
        self.r_s= right_site
        self.r_s.hide()
        if fileExists('/usr/bin/streamripper') and os.stat('/usr/bin/streamripper').st_size:
             self.session.openWithCallback(self.f2, MessageBox, _('Installation finished.') + ' ' + _('Restart must be performed'), MessageBox.TYPE_YESNO, timeout=10)
        else:
           self.session.openWithCallback(self.f3, MessageBox, _('Installation failed.') + ' ' + _(', error-text in\n/var/webradioFS_debug.log'),type=MessageBox.TYPE_INFO, timeout=15)
    def f2(self, result):
        self.r_s.show()
        if result:
            quitMainloop(3)
    def f3(self, result=None):
         self.r_s.show()


class wbrfs_filelist(Screen):
    skin = '<screen name="wbrfs_filelist" position="center,center" size="560,270" title="webradioFS-select screensaver video" >\n\t\t<ePixmap position="0,230" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />\n\t\t<ePixmap position="140,230" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />\n\t\t<widget name="key_red" position="0,230" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />\n\t\t<widget name="key_green" position="140,230" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />\n                <widget name="filelist" position="5,5" zPosition="2" size="550,230" scrollbarMode="showOnDemand" />\n                </screen>'

    def __init__(self, session):
        Screen.__init__(self, session)
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions', 'DirectionActions'], {'cancel': self.KeyExit,
         'red': self.KeyExit,
         'green': self.KeyOk,
         'ok': self.KeyOk}, -1)
        self['key_red'] = Label(_('Close'))
        self['key_green'] = Label(_('set selcted'))
        self.filelist = FileList('/', matchingPattern='(?i)^.*\\.(ts|mpg|mp4|avi|flv|mpeg|iso|mkv|vob|mov|mp2)')
        self['filelist'] = self.filelist

    def KeyOk(self):
        if self.filelist.canDescent():
            self.filelist.descent()
        else:
            self.close(self.filelist.getCurrentDirectory() + self.filelist.getFilename())

    def KeyExit(self):
        self.close(None)


class webradioFSdisplay13(Screen):
    def __init__(self, session, parent):
        from .webradioFS import fontlist
        skincontent = ''
        self.scroll_line = 'Zeile2'
        self.zeit = None
        self.art = 0
        self.zeils = 1
        self.scroll_text = ''
        self.dp_text = ''
        self.picon=None
        self.picload = None
        reads=read_einzeln().reading((("view","l4l"),("view","displayb")))
        lcd_sets=reads[0].split(',')
        sets=reads[1].split(',')
        self.pic_set=[]
        self.pic_what=1

        if len(sets) < 29:
          if len(sets) % 6 > 0:
            sets = [0,1,1,30,250,4,'Zeile2','',0,14,12,False]
        else:
           if len(sets)>29: self.pic_what=int(sets[29])
           for x in sets[24:29]:
                self.pic_set.append(x)
        sets0 = []
        try:
            for x in sets[0:6]:
                sets0.append(int(x))
        except:
            sets = [0,1,1,30,250,4,'Zeile2','',0,14,12,False]
            sets0 = (0, 1, 1, 30, 250, 4)
        vo = 0
        while len(sets) < 24:
            vo = vo + 14
            sets.extend(('Zeile2','',vo,14,12,False))
        sets_z = (sets[6:12], sets[12:18], sets[18:24])
        self.art = sets0[0]
        self.zeils = sets0[1]
        self.scroll_line_nr = sets0[2]
        self.scroll = sets0[3]
        self.picload = ePicLoad()
        if fontlist[4]:
                   self.picload_conn = self.picload.PictureData.connect(self.paintIconPixmapCB)
        else:
                    self.picload.PictureData.get().append(self.paintIconPixmapCB)
        z_list = ['Zeile1', 'Zeile2', 'Zeile3']
        if self.art == 0:
            self.label_list = []
            self.label_pos=[]
            num = 1
            alt = ''
            for x in sets_z:
                if alt != x[0].strip():
                    alt = x[0].strip()
                    if len(x) and len(alt) and num < self.zeils + 1:
                        sl = x[0][-1:]
                        if num == self.scroll_line_nr:
                            self.scroll_line = x[0]
                        if len(x[0].strip()) and (x[0].startswith('Zeile') or x[0].startswith('time')):
                            self.label_list.append((x[0].strip(), x[1].strip(),int(x[2].strip())))
                            self.label_pos.append(int(x[2].strip()))
                            wrap = 0
                            try:
                                if x[5] == "True":
                                    wrap = 1
                            except:
                                pass
                            if wrap:
                               skincontent += '<widget source="' + x[0] + '"  position="' + str(sets0[5]) + ',' + str(x[2]) + '" size="' + str(sets0[4]) + ',' + str(x[3]) + '"  render="Label" font="Regular;' + str(x[4]) + '"  />  '
                            else:
                                skincontent += '<widget source="' + x[0] + '"  position="' + str(sets0[5]) + ',' + str(x[2]) + '" size="' + str(sets0[4]) + ',' + str(x[3]) + '"  render="Label" font="Regular;' + str(x[4]) + '" noWrap="1" />  '
                            num += 1
            if self.pic_set and self.pic_set[0]=="True":
                skincontent += '<widget  name="picon"  position="' + str(self.pic_set[1]) + ',' + str(self.pic_set[2]) + '" size="' + str(self.pic_set[3]) + ',' + str(self.pic_set[4]) + '" alphatest="blend" />  '
            self.skin = '<screen name="webradioFSdisplay13" position="0,0" size="' + str(sets0[4]) + ',800" >' + skincontent + '</screen>'
            self.zeils = len(self.label_list)
            self.label_pos.sort()
        else:
            self.label_pos=None
            if self.art == 3 and path.exists("/etc/ConfFS/wbrFS_display.xml"):
                tmpskin = open('/etc/ConfFS/wbrFS_display.xml')
            elif self.art == 4:
                tmpskin = open(plugin_path + '/skin/wbrFS_display2.xml')            
            else:
                tmpskin = open(plugin_path + '/skin/wbrFS_display.xml')
            self.skin = tmpskin.read()
            tmpskin.close()
            self.label2_list = [0, 1, 2]
            if self.art == 3:
              i=0
              for x in sets_z:
                      if x[0].strip()=='':
                         self.label2_list[i] = 3
                      else:
                         self.label2_list[i] =int( x[0].strip().replace("Zeile","")) -1
                      i+=1
            self.scroll_line = 'Zeile' + str(self.scroll_line_nr)
        Screen.__init__(self, session, parent=parent)
        if self.art == 0:
            self.skinName = "webradioFSdisplay_e"+strftime('%Y%m%d', localtime())
        elif self.art == 3:
            self.skinName = "webradioFSdisplay_b"+strftime('%Y%m%d', localtime())
        else:
            self.skinName = "webradioFSdisplay13"
        self['picon'] = Pixmap()
        self['Zeile2'] = StaticText('webradioFS')
        self['Zeile1'] = StaticText('')
        self['Zeile3'] = StaticText('')
        self['Zeile0'] = StaticText('')
        self['time'] = StaticText('')
        self.pos = 0
        self.left=0
        self.display_text = 'webradioFS'
        self.opicon=None
        self.onShow.append(self.addWatcher)
        self.onHide.append(self.removeWatcher)
        self.display_text = 'webradioFS'
        self.scrollTimer = None
        self.althash=None
        self.scrollTimer = eTimer()
        self.zeitTimer = eTimer()
        self.picon_show=False
        self.paras=None
        self.picon_show=True
        if fontlist[4]:
             self.scrollTimer_conn = self.scrollTimer.timeout.connect(self.scroll_Timeout)
             self.zeitTimer_conn = self.zeitTimer.timeout.connect(self.zeit_Timeout)
        else:
            self.scrollTimer.timeout.get().append(self.scroll_Timeout)
            self.zeitTimer.timeout.get().append(self.zeit_Timeout)

    def addWatcher(self):
        self.parent.onChangedEntry.append(self.selectionChanged)
        self.parent.selectionChanged()

    def removeWatcher(self):
        self.parent.onChangedEntry.remove(self.selectionChanged)

    def paintIconPixmapCB(self, picInfo=None):
           if self.picload:
                ptr = self.picload.getData()
                if ptr != None:
                        self['picon'].instance.setPixmap(ptr)
                        self['picon'].show()

    def updateIcon(self,file1=None):
               if self.picload and fileExists(file1):
                   if self.paras==None:
                        self.paras=self['picon'].instance.size()
                        sc = AVSwitch().getFramebufferScale()
                        self.picload.setPara((self['picon'].instance.size().width(), self['picon'].instance.size().height(), sc[0], sc[1], False, 1, "#00000000"))
                   self.picload.startDecode(file1)

    def selectionChanged(self, Zeile1 = '', Zeile2 = 'webradioFS', Zeile3 = '', display_art = 'normal', picon = None):
      if self.art != 2:
        self.pos = 0
        if Zeile1==_("webradioFS-Menu"):display_art = 'liste'
        if display_art != 'liste':
           self['picon'].show()
           if self.pic_what==1:
              if self.picload and self.picon_show and self.picon != picon :
                  self.picon=picon
                  if picon and self.picon_show:
                      if path.isfile(str(picon)):
                          self.updateIcon(picon)
                  else:
                      self['picon'].hide()
        else:
            self['picon'].hide()
        if self.scrollTimer.isActive():
                    self.scrollTimer.stop()
        if Zeile1 != None:
          if int(self.art) == 0:
            if display_art != 'liste':
                for x in self.label_list:
                    text2 = ''
                    if len(x[0]):
                        if x[0] == 'time':
                            self.zeit = (x[0], '', 0)
                            if len(x[1]) and x[1] != 'time':
                                self.zeit = (x[0], vars()[x[1]], 0)
                            text1 = '*x*'
                        else:
                            text1 = vars()[x[0]]
                        if len(x[1]):
                            if x[1] == 'time':
                                self.zeit = (x[0], text1, 1)
                                text2 = '%s%s' % ('   ', '*x*')
                            else:
                                text2 = '%s%s' % ('   ', vars()[x[1]])
                        if self.scroll_line == x[0]:
                            if not len(self.dp_text):
                                self[x[0]].setText(text1.replace('*x*', strftime('%H:%M', localtime())) + text2.replace('*x*', strftime('%H:%M', localtime())))
                            self.scroll_text = '%s%s' % (text1, text2)
                        else:
                            self[x[0]].setText(text1.replace('*x*', strftime('%H:%M', localtime())) + text2.replace('*x*', strftime('%H:%M', localtime())))
            else:
                if self.zeils == 1 or self.zeils == 2:
                    self[self.label_list[0][0]].setText(Zeile2)
                    if self.zeils == 2:
                        self[self.label_list[1][0]].setText(Zeile3)
                else:
                    if self.label_pos:
                        text_liste=(Zeile1,Zeile2,Zeile3)
                        for y in self.label_list:
                           ind= self.label_pos.index(y[2])
                           self[y[0]].setText(text_liste[ind])
                    else:
                        self[self.label_list[0][0]].setText(Zeile1)
                        self[self.label_list[1][0]].setText(Zeile2)
                        self[self.label_list[2][0]].setText(Zeile3)
          else: 
              sc_l = (Zeile1, Zeile2, Zeile3,'')
              if display_art != 'liste':
                self['Zeile1'].setText(sc_l[self.label2_list[0]])
                self['Zeile2'].setText(sc_l[self.label2_list[1]])
                self['Zeile3'].setText(sc_l[self.label2_list[2]])
              else:
                self['Zeile3'].text = Zeile3
                self['Zeile1'].text = Zeile1
                self['Zeile2'].text = Zeile2
              self.scroll_text = sc_l[self.label2_list[self.scroll_line_nr-1]]
          try:
              self.display_text = self.scroll_text
              self.dp_text = self.scroll_text
          except:
              pass
          if not self.zeitTimer.isActive():
                self.zeit_Timeout()
          if display_art != 'liste':
            self[self.scroll_line].text = self.scroll_text
            if self.scroll > 0:
              if display_art != 'liste':
                if self.scroll_line_nr > 0 and len(self.dp_text):
                    self.scroll_size=400
                    if not self.scrollTimer.isActive():
                        self.scroll_Timeout()
            else:
              self[self.scroll_line].text = self.scroll_text
          else:
            self.zeit=None 

    def zeit_Timeout(self):
      if self.zeit:  
        time1 = strftime('%H:%M', localtime())
        t1 = ''
        if self.zeit[2] == 0:
            if len(self.zeit[1]):
                t1 = '%s%s' % ('   ', self.zeit[1])
            self[self.zeit[0]].setText(time1 + t1)
        else:
            if len(self.zeit[1]):
                t1 = '%s%s' % (self.zeit[1], '   ')
            self[self.zeit[0]].setText(t1 + time1)
      if self.picload and self.picon_show and self.pic_what==2:
           if fileExists("/tmp/.wbrfs_pic"):
              if self.opicon:
                  self.updateIcon("/tmp/.wbrfs_pic")
                  self.opicon=None
              else:
                pichash = popen("md5sum "+"/tmp/.wbrfs_pic").read()
                if pichash != self.althash:   
                   self.althash=pichash
                   self.updateIcon("/tmp/.wbrfs_pic")
      self.zeitTimer.startLongTimer(1)

    def scroll_Timeout(self):
        self.left=self.left+1
        if self.left>self.scroll_size or self.left<1:
             self.left=self.scroll_size
        self[self.scroll_line].text = self.dp_text
        if self.scroll > 0:
            anz = 1
            if len(self.dp_text) and ord(self.dp_text[0]) > 127:
                anz = 2
            self.dp_text = self.dp_text[anz:len(self.dp_text)]
            if len(self.dp_text) < 20:
                self.dp_text = '%s%s%s' % (self.dp_text, '     ', self.display_text)
            if '*x*' in self.dp_text:
                self.dp_text = self.dp_text.replace('*x*', strftime('%H:%M', localtime()))
            self.scrollTimer.start(int(self.scroll) * 30)


class webradioFSsetDisplay(Screen, ConfigListScreen):
    def __init__(self, session,fonts=None):
        from .webradioFS import fontlist
        tmpskin = open(fontlist[5]+"wbrFS_setup.xml")
        self.skin = tmpskin.read()
        tmpskin.close()
        self.fonts=fontlist
        self.m_sets={
             "art":0,"zeilen":1,"scroll_line":2,"scroll_speed":3,"len":250,"hp":4, 
             "l1t":"Zeile2","l1t2":"","l1p":0,"l1h":14,"l1f":12,"l1z":False,
             "l2t":"Zeile2","l2t2":"","l2p":0,"l2h":14,"l2f":12,"l2z":False,
             "l3t":"Zeile2","l3t2":"","l3p":0,"l3h":14,"l3f":12,"l3z":False,
             "pic_on":False,"pic_pos_l":0,"pic_pos_h":0,"pic_size_b":0,"pic_size_h":0,"what":1,
              }
        sets=read_einzeln().reading((("view","displayb"),))[0].split(',')
        i=0
        keys=("art","zeilen","scroll_line","scroll_speed","len","hp","l1t","l1t2","l1p","l1h",
              "l1f","l1z","l2t","l2t2","l2p","l2h","l2f","l2z","l3t","l3t2",
              "l3p","l3h","l3f","l3z","pic_on","pic_pos_l","pic_pos_h","pic_size_b","pic_size_h","what")
        for x in sets:
               if x == "True":
                  self.m_sets[keys[i]]=True
               elif x == "False":
                  self.m_sets[keys[i]]=False
               else:
                   self.m_sets[keys[i]]=x
               i+=1
        self.art = NoSave(ConfigSelection(default=int(self.m_sets["art"]), choices=[(0, _('by settings')), (1, _('by xml-file')), (3, "/etc/ConfFS/wbrFS_display.xml"), (4, _("single-line")),(2, _('deactivated'))]))
        self.zeilen = NoSave(ConfigInteger(int(self.m_sets["zeilen"]), (1, 3)))
        self.scroll_line = NoSave(ConfigInteger(int(self.m_sets["scroll_line"]), (0, 3)))
        self.scroll_speed = NoSave(ConfigInteger(int(self.m_sets["scroll_speed"]), (0, 99)))
        self.len1 = NoSave(ConfigInteger(int(self.m_sets["len"]), (0, 999)))
        self.hp = NoSave(ConfigInteger(int(self.m_sets["hp"]), (0, 99)))
        self.pic_on = NoSave(ConfigYesNo(default=self.m_sets["pic_on"]))
        self.pic_what = NoSave(ConfigSelection(default=int(self.m_sets["what"]), choices=[(1, _('Show logo')), (2, _('Show pictures'))]))
        self.pic_pos_l = NoSave(ConfigInteger(int(self.m_sets["pic_pos_l"]), (0, 999)))
        self.pic_pos_o = NoSave(ConfigInteger(int(self.m_sets["pic_pos_h"]), (0, 999)))
        self.pic_size_b = NoSave(ConfigInteger(int(self.m_sets["pic_size_b"]), (0, 999)))
        self.pic_size_h = NoSave(ConfigInteger(int(self.m_sets["pic_size_h"]), (0, 999)))
        self.txt_choices2= [('Zeile1', _('Station-Name')),('Zeile2', _('information transmitted')),('Zeile3', _('Favorite name')),('', '')]
        self.txt_choices1= [('Zeile1', _('Station-Name')),('Zeile2', _('information transmitted')),('Zeile3', _('Favorite name')),('time', _('time')),('', '')]
        self.choices_test=('Zeile1','Zeile2','Zeile3')
        r11=self.m_sets["l1t"]
        r12=self.m_sets["l2t"]
        r13=self.m_sets["l3t"]
        if int(self.m_sets["art"])>2: 
            self.txt_choices = self.txt_choices2
            if r11 not in self.choices_test:r11=''
            if r12 not in self.choices_test:r12=''
            if r13 not in self.choices_test:r13=''
        else: 
            self.txt_choices = self.txt_choices1
        self.l1t = NoSave(ConfigSelection(default=r11, choices=self.txt_choices))
        self.l1t2 = NoSave(ConfigSelection(default=self.m_sets["l1t2"], choices=self.txt_choices1))
        self.l1p = NoSave(ConfigInteger(int(self.m_sets["l1p"]), (0, 999)))
        self.l1h = NoSave(ConfigInteger(int(self.m_sets["l1h"]), (0, 999)))
        self.l1f = NoSave(ConfigInteger(int(self.m_sets["l1f"]), (0, 99)))
        self.l1z = NoSave(ConfigYesNo(default=self.m_sets["l1z"]))
        self.l2t = NoSave(ConfigSelection(default=r12, choices=self.txt_choices))
        self.l2t2 = NoSave(ConfigSelection(default=self.m_sets["l2t2"], choices=self.txt_choices1))
        self.l2p = NoSave(ConfigInteger(int(self.m_sets["l2p"]), (0, 999)))
        self.l2h = NoSave(ConfigInteger(int(self.m_sets["l2h"]), (0, 999)))
        self.l2f = NoSave(ConfigInteger(int(self.m_sets["l2f"]), (0, 99)))
        if str(self.m_sets["l2z"]) !="True" and str(self.m_sets["l2z"]) !="False":
            self.m_sets["l2z"]=False 
        self.l2z = NoSave(ConfigYesNo(default=self.m_sets["l2z"]))
        self.l3t = NoSave(ConfigSelection(default=r13, choices=self.txt_choices))
        self.l3t2 = NoSave(ConfigSelection(default=self.m_sets["l3t2"], choices=self.txt_choices1))
        self.l3p = NoSave(ConfigInteger(int(self.m_sets["l3p"]), (0, 999)))
        self.l3h = NoSave(ConfigInteger(int(self.m_sets["l3h"]), (0, 999)))
        self.l3f = NoSave(ConfigInteger(int(self.m_sets["l3f"]), (0, 99)))
        self.l3z = NoSave(ConfigYesNo(default=self.m_sets["l3z"]))
        Screen.__init__(self, session)
        if fontlist[9]:
            self.skinName = "WebradioFSSetup_13_e"
        else:
            self.skin=self.skin.replace('backgroundColor="#000000"','')
            self.skin=self.skin.replace('foregroundColor="#ffffff"','')
            self.skinName = "WebradioFSSetup_13"
        self.onChangedEntry = []
        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("Save"))
        self["balken"] = Label("")
        self["key_yellow"] = Label("")
        self["key_blue"] = Label(_("Standards"))
        self["rec_txt"] = Label(_('Display Settings'))
        self["playtext"] = StaticText("")
        self["green_pic"] = Pixmap()
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'ok': self.saveConfig,
         'cancel': self.exit,
         'red': self.exit,
         'blue': self.standards,
         'green': self.saveConfig}, -1)
        ConfigListScreen.__init__(self, [], on_change=self.reloadList)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self.onLayoutFinish.remove(self.layoutFinished)
        if self.fonts[8] or self.fonts[9]:
          try:
            if not self.fonts[4]:
                self['config'].instance.setFont(self.fonts[3])
                self['config'].instance.setItemHeight(self.fonts[2])
            else:
                    from skin import parseFont
                    stylemgr = eWindowStyleManager.getInstance()
                    skinned = eWindowStyleSkinned()
                    eListboxPythonConfigContent.setDescriptionFont(parseFont(self.fonts[3], ((1,1),(1,1))))
                    eListboxPythonConfigContent.setValueFont(parseFont(self.fonts[3], ((1,1),(1,1))))
                    eListboxPythonConfigContent.setItemHeight(self.fonts[2])
                    stylemgr.setStyle(0, styleskinned)
          except:
              pass
        self.refresh()

    def refresh(self):
        if self.art.value ==3:
            if self.l1t.value not in self.choices_test: self.l1t.value=''
            if self.l2t.value not in self.choices_test: self.l2t.value=''
            if self.l3t.value not in self.choices_test: self.l3t.value=''
            self.l1t = NoSave(ConfigSelection(default=self.l1t.value, choices=self.txt_choices2))
            self.l2t = NoSave(ConfigSelection(default=self.l2t.value, choices=self.txt_choices2))
            self.l3t = NoSave(ConfigSelection(default=self.l3t.value, choices=self.txt_choices2))        
        else:
                self.l1t = NoSave(ConfigSelection(default=self.l1t.value, choices=self.txt_choices1))
                self.l2t = NoSave(ConfigSelection(default=self.l2t.value, choices=self.txt_choices1))
                self.l3t = NoSave(ConfigSelection(default=self.l3t.value, choices=self.txt_choices1))
        self.instance.setZPosition(2)
        timDisplConfigList = []
        timDisplConfigList.extend((getConfigListEntry(_('Type of setting:'), self.art),))
        timDisplConfigList.extend((getConfigListEntry("-- "+_('No effect on displays white LCD4Linux!')+" --"),))
        if self.art.value == 2:
            timDisplConfigList.extend((getConfigListEntry(_('Nothing is displayed in VFD(text) displays')),))
        else:
            if self.art.value == 0:
                timDisplConfigList.extend((getConfigListEntry("-- "+_('Skin and xml file have no effect!')+" --"),))
                timDisplConfigList.extend((getConfigListEntry(_('Number of lines:'), self.zeilen),))
            if self.art.value !=4:
                timDisplConfigList.extend((getConfigListEntry(_('Scroll-line:') + '(0-3)', self.scroll_line),))
            timDisplConfigList.extend((getConfigListEntry(_('Scroll-Speed:') + ' (0-99)', self.scroll_speed),))
            if self.art.value ==3:
                timDisplConfigList.extend((getConfigListEntry(_('Line') + ' 1: '),
                     getConfigListEntry(_('Text'), self.l1t),
                     getConfigListEntry(_('Line') + ' 2: '),
                     getConfigListEntry(_('Text'), self.l2t),
                     getConfigListEntry(_('Line') + ' 3: '),
                     getConfigListEntry(_('Text'), self.l3t),
                ))
            if self.art.value == 0:
                timDisplConfigList.extend((getConfigListEntry(_('Display-Len:') + ' (0-999)', self.len1), 
                                           getConfigListEntry(_('Distance from the left:') + '(0-99)', self.hp),
                                           getConfigListEntry(_('Show logos/pics'), self.pic_on), 
                                           getConfigListEntry('')))
                if self.pic_on.value != False:
                  timDisplConfigList.extend(
                    (
                    getConfigListEntry(_('Logo/Picture Settings')),
                    getConfigListEntry(_('What show'),self.pic_what),
                    getConfigListEntry(_('Logo/Picture Pos. left'),self.pic_pos_l),
                    getConfigListEntry(_('Logo/Picture Pos. top'), self.pic_pos_o),
                    getConfigListEntry(_('Logo/Picture widht'), self.pic_size_b),
                    getConfigListEntry(_('Logo/Picture high'), self.pic_size_h),
                    getConfigListEntry('')
                    ))
                timDisplConfigList.extend((getConfigListEntry(_('Line') + ' 1: '),
                 getConfigListEntry(_('Text'), self.l1t),
                 getConfigListEntry(_('add more text'), self.l1t2),
                 getConfigListEntry(_('Distance from the top') + '(0-999)', self.l1p),
                 getConfigListEntry(_('height') + '(0-999)', self.l1h),
                 getConfigListEntry(_('Font-Size') + '(0-99)', self.l1f),
                 getConfigListEntry(_('line breaks'), self.l1z)))
                if self.zeilen.value > 1:
                    timDisplConfigList.extend((getConfigListEntry(''),
                     getConfigListEntry(_('Line') + ' 2: '),
                     getConfigListEntry(_('Text'), self.l2t),
                     getConfigListEntry(_('add more text'), self.l2t2),
                     getConfigListEntry(_('Distance from the top') + '(0-999)', self.l2p),
                     getConfigListEntry(_('height') + '(0-999)', self.l2h),
                     getConfigListEntry(_('Font-Size') + '(0-99)', self.l2f),
                     getConfigListEntry(_('line breaks'), self.l2z)))
                if self.zeilen.value > 2:
                    timDisplConfigList.extend((getConfigListEntry(''),
                     getConfigListEntry(_('Line') + ' 3: '),
                     getConfigListEntry(_('Text'), self.l3t),
                     getConfigListEntry(_('add more text'), self.l3t2),
                     getConfigListEntry(_('Distance from the top') + '(0-999)', self.l3p),
                     getConfigListEntry(_('height') + '(0-999)', self.l3h),
                     getConfigListEntry(_('Font-Size') + '(0-99)', self.l3f),
                     getConfigListEntry(_('line breaks'), self.l3z)))
            else:
                if self.art.value !=4:
                   timDisplConfigList.extend((getConfigListEntry(_('What show'),self.pic_what),))
                timDisplConfigList.extend((getConfigListEntry(_('make all other settings in the xml-file!')),))
        self["config"].setList(timDisplConfigList)

    def standards(self):
          standards_list=[(_("VFD-Display"),1),(_("Grafik-Display"),2),(_("Grafik-Display 480x320"),3)]
          self.session.openWithCallback(self.sel_standards,ChoiceBox,_("Select Standards"),standards_list)

    def sel_standards(self,answer=None):
         if answer:  
           self.save_list=None
           if answer[1]==1:
               self.save_list='0,1,2,30,250,4,Zeile2,,0,14,12,False'
           elif answer[1]==2:
               self.save_list="0,3,3,30,999,4,time,,0,44,42,False,Zeile1,,100,44,42,False,Zeile2,,180,44,42,False,True,200,0,80,80,2"
           elif answer[1]==3:
               self.save_list="0,3,3,30,480,10,time,,5,50,48,False,Zeile1,,60,50,44,False,Zeile2,,110,50,42,False,True,20,180,440,120,2"
           if self.save_list:
              self.session.openWithCallback(self.sav_standards,MessageBox, _('Save Standard-Settings?'), type=MessageBox.TYPE_YESNO)

    def sav_standards(self,answer=None):
        if answer:
           self.saving(self.save_list)

    def reloadList(self):
        self.refresh()

    def saveConfig(self):
        set_list = (self.art,
         self.zeilen,
         self.scroll_line,
         self.scroll_speed,
         self.len1,
         self.hp,
         self.l1t,
         self.l1t2,
         self.l1p,
         self.l1h,
         self.l1f,
         self.l1z,
         self.l2t,
         self.l2t2,
         self.l2p,
         self.l2h,
         self.l2f,
         self.l2z,
         self.l3t,
         self.l3t2,
         self.l3p,
         self.l3h,
         self.l3f,
         self.l3z,
         self.pic_on,
         self.pic_pos_l,
         self.pic_pos_o,
         self.pic_size_b,
         self.pic_size_h,
         self.pic_what
         )
        save_list = ''
        err = 0
        if self.art.value == 0:
            if len(self.l1t.value) + len(self.l2t.value) + len(self.l3t.value) < 1:
                err = 1
            elif self.zeilen.value == 3 and (len(self.l3t.value) < 1 or len(self.l2t.value) < 1 or len(self.l1t.value) < 1):
                err = 1
            elif self.zeilen.value == 2 and (len(self.l2t.value) < 1 or len(self.l1t.value) < 1):
                err = 1
            elif len(self.l1t.value) == 1:
                err = 1
        if err == 1:
            self.session.open(MessageBox, _('Line without text can not be saved'), type=MessageBox.TYPE_ERROR)
        else:
            for x in set_list:
                if len(save_list):
                    save_list = save_list + ','
                save_list = save_list + str(x.value)
        if len(save_list):
            self.saving(save_list)

    def saving(self,save_list):
        if self.art.value ==3:
                if not path.exists("/etc/ConfFS/wbrFS_display.xml"):
                    ret = copyfile(plugin_path+"/skin/wbrFS_display.xml","/etc/ConfFS/wbrFS_display.xml")
        if len(save_list):
          connection = sqlite.connect(set_file)
          connection.text_factory = str
          cursor = connection.cursor()
          cursor.execute('SELECT id FROM settings WHERE nam1 = "%s" AND group1 = "%s";' % ("displayb","view"))
          row = cursor.fetchone()
          if row is None: 
                    cursor.execute("INSERT INTO settings (group1,nam1,wert1) VALUES(?,?,?);",  ("view","displayb",save_list))
          else:
                cursor.execute('UPDATE settings SET wert1 = ? WHERE id = ?;',  (save_list,row[0]))
          connection.commit()
          cursor.close()
          connection.close()
          self.session.open(MessageBox, _('Close and restart webradioFS for activate settings'), type=MessageBox.TYPE_INFO)
          self.close()

    def exit(self):
        self.close()


class tag_read:
    def read_tags(self,au_path=None,mcover=None):
            mtags=None
            if au_path:
                           maudio = None
                           mtitle = "n/a"
                           mgenre = "n/a"
                           martist = "n/a"
                           malbum = "n/a"
                           mdate = "n/a"
                           mlength = 0
                           mpathname=au_path
                           if mutagen:
                                if mpathname.lower().endswith(".mp3"):
                                    if not mcover:
                                        try:
                                            maudio = ID3(mpathname)
                                            apicframes = maudio.getall("APIC")
                                            if len(apicframes) >= 1:
                                                mcover=apicframes[0].data
                                        except:
                                            maudio = None
                                    try: maudio = MP3(mpathname, ID3 = EasyID3)
                                    except: maudio = None
                                elif mpathname.lower().endswith(".flac"):
                                    try: maudio = FLAC(mpathname)
                                    except: maudio = None
                                elif mpathname.lower().endswith(".m4a") or mpathname.lower().endswith(".mp4"):
                                    try: maudio = EasyMP4(mpathname)
                                    except: maudio = None
                                elif mpathname.lower().endswith(".ogg"):
                                    try: maudio = OggVorbis(mpathname)
                                    except: maudio = None
                                mfilename = path.splitext(path.basename(mpathname))[0]
                                if maudio:
                                    mtitle = self.getEncodedString(maudio.get('title', [mfilename])[0])
                                    malbum = self.getEncodedString(maudio.get('album', ['n/a'])[0])
                                    mgenre = self.getEncodedString(maudio.get('genre', ['n/a'])[0])
                                    martist = self.getEncodedString(maudio.get('artist', ['n/a'])[0])
                                    mdate = self.getEncodedString(maudio.get('date', ['n/a'])[0])
                                    try:
                                        mlen = int(maudio.info.length)
                                        mlength = str(datetime_timedelta(seconds=mlen)).encode("utf-8", 'ignore')
                                        if mlen < 3600:
                                            mlength = mlength[-5:]
                                    except:
                                        mlength = 0
                                mtags= (mcover,mtitle,martist,malbum,mgenre,mdate,mlength)
            return mtags

    def getEncodedString(self,value):
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


class fav_import:
    def imp2(self, t = None, version = None, php_num=None,num=None):
        from .webradioFS import fontlist
        startsets=read_settings1().reading(("prog",""))#[0]
        sets_prog=startsets[0]
        z = None
        from sqlite3 import dbapi2 as sqlite
        db_exists = False
        if path.exists(myfav_file) and path.getsize(myfav_file) > 5300:
            db_exists = True
        else:
          connection = sqlite.connect(myfav_file)
          connection.text_factory = str
          cursor = connection.cursor()
          if not db_exists:
            if not t:
                cursor.execute('CREATE TABLE IF NOT EXISTS streams (stream_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, descrip TEXT, url TEXT, typ TEXT, genre2 TEXT, defekt INTEGER, bitrate INTEGER, genre TEXT, volume INTEGER, uploader TEXT, rec INTEGER, zuv TEXT, picon INTEGER, group1 INTEGER, sscr TEXT);')
                cursor.execute('CREATE TABLE IF NOT EXISTS groups (group_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, group1 TEXT NOT NULL UNIQUE);')
                cursor.execute('INSERT OR IGNORE INTO groups (group1) VALUES("Standard");')
                connection.commit()
          cursor.close()
          connection.close()
          return z

class fav_import3:
    def imp2(self,dats=None):
        z = None
        from sqlite3 import dbapi2 as sqlite
        db_exists = False
        connection = sqlite.connect(myfav_file)
        connection.text_factory = str
        cursor = connection.cursor()
        if path.exists(myfav_file) and path.getsize(myfav_file) > 5300:
            db_exists = True
        if not db_exists:
            if not t:
                cursor.execute('CREATE TABLE IF NOT EXISTS streams (stream_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, descrip TEXT, url TEXT, typ TEXT, genre2 TEXT, defekt INTEGER, bitrate INTEGER, genre TEXT, volume INTEGER, uploader TEXT, rec INTEGER, zuv TEXT, picon INTEGER, group1 INTEGER, sscr TEXT);')
                cursor.execute('CREATE TABLE IF NOT EXISTS groups (group_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, group1 TEXT NOT NULL UNIQUE);')
                cursor.execute('INSERT OR IGNORE INTO groups (group1) VALUES("Standard");')
                connection.commit()
        liste = []
        if dats:
             liste = dats
             if liste[0].startswith("error"):
                                f2=open("/tmp/webradioFS_debug.log","a")
                                f2.write("exception (01):\n"+liste[0]+"\n")
                                f2.close()
                                liste=None
        elif os.path.exists("/tmp/webradioFS.imp"):
            liste = open("/tmp/webradioFS.imp", "r").readlines()
        n="import"
        if liste and len(liste):
            if liste[0].startswith("#group:"):
                grn=liste[0].split(":")
                n=grn[1].strip()
            gnum=None
            try:
                cursor.execute('INSERT INTO groups (group1) VALUES("%s");' %n )
                connection.commit()
            except:
                pass
            cursor.execute("select * from groups;")
            for row in cursor:
                if str(row[1])==n:
                    gnum=row[0]
            if gnum != None and str(gnum) != "None":
                cursor.execute("delete from streams where group1 = %d" % (int(gnum)))
            try:
                for x in liste:
                    if not x.startswith("#"):
                        
                        name1=None
                        genre=""
                        genre2=""
                        url1=None
                        typ1=None
                        descrip1=" "
                        bitr=0
                        new=x.replace("{","").split("}")
                        if gnum and len(new)>2:
                            if new[0] and new[1] and new[2]:   
                               if len(str(new[0])):name1=str(new[0]).strip().replace("\n",",")
                               if len(str(new[1])):url1=str(new[1]).strip()
                               if len(str(new[2])):typ1=str(new[2]).strip().replace("\n",",") 
                               if len(new)>3:
                                   if len(str(new[3])):descrip1=str(new[3]).strip().replace("\n",",")
                                   try:
                                       bitr=int(new[4])
                                   except:
                                       pass
                                   if len(new)>5 and str(new[5]).strip() != "-":
                                       genre=str(new[5]).strip().replace("\n",",")
                                       if len(new)>6 and str(new[6]).strip() != "-":
                                           genre2=str(new[6]).strip().replace("\n",",")
                        if (name1 and len(name1)) and (url1 and len(url1)) and (typ1 and len(typ1)):
                                cursor.execute('INSERT INTO streams (name, descrip, url, typ, genre2, defekt,bitrate,genre,volume,uploader,rec,zuv,picon,group1,sscr) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);', 
                                  (name1,descrip1,url1,typ1,genre2,0,bitr,genre,0,"",0,0,0,gnum,'default'))
                                z=1
            except Exception as e:
                                f2=open("/tmp/webradioFS_debug.log","a")
                                f2.write("exception (01):\n"+str(e)+"\n"+str(x)+"\n")
                                f2.close()
        connection.commit()
        cursor.close()
        connection.close()
        if os.path.exists("/tmp/webradioFS.imp"):
            os.remove("/tmp/webradioFS.imp")
        return z
