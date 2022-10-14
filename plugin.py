# -*- coding: utf-8 -*-
###############################################################################
# webradioFS von shadowrider
# VU+ Edition
# Chrashlogs, Vorschlaege, Beschwerden usw. bitte an plugins (at) fs-plugins.de
#
# This plugin is licensed under the Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0). 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to CreativeCommons, 559 Nathan Abbott Way, Stanford, California 94305, USA
#
# In addition, this plugin may only be distributed and executed on
# hardware which is licensed by Vu+ and E2 
###############################################################################
from . import _
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import InfoBar
from Components.PluginComponent import plugins
from Components.PluginList import PluginList
from enigma import getDesktop
import Screens.Standby
from Tools import Notifications
from Screens import Standby
from Screens.MessageBox import MessageBox
from enigma import eTimer
from enigma import gFont 
import os
import time
import datetime
session = None
running=False
rs=open("/var/webradioFS_debug.log","a")
rs.close()
npicon='skin/images/webradiofs.png'


DPKG = False
first=1
#if os.path.exists("/etc/image-version"): 
#                fm=os.popen("cat /etc/image-version")
#                lines=fm.read()


standbycheck = eTimer()
try:
     if getDesktop(0).size().width() > 1280:
        npicon='skin/images/webradioFSfhd.png'
except:
    pass

sets_prog={"Version":"0","eidie":"first","wbrmeld":"","hauptmenu":False,"DPKG":DPKG}
if not os.path.exists("/etc/ConfFS/"):os.mkdir("/etc/ConfFS/")
set_file='/etc/ConfFS/webradioFS_sets.db'

oldid="first"
favpath=None
autoTimes=[]
new_set=None
if not os.path.isfile(set_file):
    f=open(set_file,"w")
    f.close()
    new_set=1
    if os.path.isfile("/etc/wbrfsid"):
            f=open("/etc/wbrfsid","r")
            oldid=f.read().rstrip()
            if not len(oldid): 
                 oldid="first"
            f.close()
if os.path.getsize(set_file)<10:new_set=1
os.chmod('/etc/ConfFS/webradioFS_sets.db', 0644)


import sqlite3
connection = sqlite3.connect(set_file)
connection.text_factory = str
wbrfscursor = connection.cursor()

try:
    wbrfscursor.execute('SELECT COUNT(*) FROM settings WHERE wert2=?', ("progversion"))
except Exception, e:
    if not new_set and "no such table: settings" in str(e):
         wbrfscursor.execute('ALTER TABLE settings2 RENAME TO settings;')
    else:
      if new_set:
        wbrfscursor.execute('CREATE TABLE IF NOT EXISTS settings (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, group1 TEXT, nam1 TEXT, wert1 TEXT, wert2 TEXT NOT NULL UNIQUE)')    

      else:
        wbrfscursor.execute('CREATE TABLE IF NOT EXISTS settings2 (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, group1 TEXT, nam1 TEXT, wert1 TEXT, wert2 TEXT NOT NULL UNIQUE)')
        wbrfscursor.execute('SELECT group1,nam1,wert1 from settings')
#f=open("/tmp/db1","w")
        uniq_tb=[]
        dats=[]
        for row in wbrfscursor:
            uniq=str(row[0])+str(row[1])
            if uniq not in uniq_tb:
                uniq_tb.append(uniq)
                dats.append((row[0],row[1],row[2],uniq))
        for x in dats:
             wbrfscursor.execute("INSERT OR IGNORE INTO settings2 (group1,nam1,wert1,wert2) VALUES(?,?,?,?)",  (x[0],x[1],x[2],x[3])) 
        connection.commit()
        wbrfscursor.execute('DROP TABLE settings;')
        wbrfscursor.execute('ALTER TABLE settings2 RENAME TO settings;')
    connection.commit()

#   aenderungen auch in func beim read aendern!!
setsb=(
          ("prog","version","0"),("prog","wbrmeld",""),("prog","eidie",oldid),("prog","hauptmenu","False"),("prog","DPKG",DPKG),("prog","exttmenu","True"),
          ("grund","picsearch","var1"),("grund","favpath","/etc/ConfFS/"),("grund","exitfrage","False"),("grund","nickname","nn"),
          ("grund","stream_sort",1),("grund","wbrbackuppath","/media/hdd/"),("grund","startstream1","0"),
          ("opt","rec","False"),("opt","views","False"),("opt","expert",0),("opt","scr","False"),("opt","lcr","False"),("opt","audiofiles","False"),("opt","tasten","False"),("opt","display","False"),("opt","sispmctl","False"),
          ("exp","reconnect","3"),("exp","versions_info","True"),("exp","timeout","10"),("exp","conwait","3"),("exp","logopath","/etc/ConfFS/streamlogos/"),("exp","coversafepath","/etc/ConfFS/cover/"),
          ("exp","FBts_liste","0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24"),("exp","al_vol_max","50"),("exp","ex_vol","0"),("exp","start_vol","0"),("exp","vol_auto_time","8"),("exp","debug","1"),
          ("exp","picwords1",""),("exp","picwords2",""),("exp","picwords3",""),("exp","offtimer_time","120"),("exp","offtimer_art","0"),("exp","wbrfspvrpath","/usr/share/enigma2/Picon/"),("exp","min_bitrate","0"),
          ("rec","path","/media/hdd/"),("rec","split","True"),("rec","new_dir","True"),("rec","cover","True"),("rec","anzeige","True"),("rec","inclp_save","True"),("rec","caching","0"),("rec","rec_caching_dir","/media/hdd/"),
          ("scr","screensaver_art","wechsel"),("scr","color","005B00"),("scr","bgcolor","000000"),("scr","bgcolor_random","0"),("scr","slideshow_bgcolor","000000"),("scr","Keyword","Hund"),
          ("scr","slideshow_time","10"),("scr","slideshowpath","/media/hdd/"),("scr","slideshow_subdirs","True"),("scr","slideshow_space","0"),("scr","timeout","60"),
          ("scr","wbrvideorecurr","30"),("scr","wbrvideopath","/media/hdd/"),("scr","wbrvideofile","/"),("scr","textfix","False"),
          ("view","logos","True"),("view","font_size","22"),("view","only_foto","False"),("view","Listlogos","True"),
          ("view","displayb",'0,1,2,30,250,4,Zeile2,,0,14,12,False'),
          ("view","l4l","True,1,True,3,True,0,30,20,1,True,0,0,20,1,True,0,60,20,1,True,2,0,200,True,0,100,200,40,22,white"),
          ("audiofiles","audiopath","/media/hdd/"),("audiofiles","subdirs","True"),("audiofiles","autoplay","False"),("audiofiles","sort","True"),("audiofiles","save_random","True"),("audiofiles","schleife","True"),("audiofiles","audio_listpos","True"),
          ("sispmctl","start","2,2,2,2"),("sispmctl","exit","2,2,2,2"),("sispmctl","ssr1","2,2,2,2"),("sispmctl","ssr2","2,2,2,2"),
          ("sispmctl","nvers1","Switching Version 1"),("sispmctl","vers1","2,2,2,2"),("sispmctl","nvers2","Switching Version 2"),("sispmctl","vers2","2,2,2,2"),
           )

for x in setsb:
             uni=x[0]+x[1]
             wbrfscursor.execute("INSERT OR IGNORE INTO settings (group1,nam1,wert1,wert2) VALUES(?,?,?,?);",  (x[0],x[1],x[2],uni)) 

setsb=None

wbrfscursor.execute('SELECT wert1 FROM settings WHERE nam1 = "%s";' % ("hauptmenu"))
row = wbrfscursor.fetchone()
sets_prog["hauptmenu"]=row[0]
wbrfscursor.execute('SELECT wert1 FROM settings WHERE nam1 = "%s";' % ("favpath"))
row3 = wbrfscursor.fetchone()
favpath=row3[0]
try:
    os.chmod(os.path.join(favpath,"webradioFS_favs.db"), 0644)
except:
    pass

wbrfscursor.execute('SELECT wert1 FROM settings WHERE nam1 = "DPKG";')
row = wbrfscursor.fetchone()
if row is None:
		wbrfscursor.execute("INSERT INTO settings (group1,nam1,wert1) VALUES(?,?,?);",  ("prog","DPKG",DPKG))
else: 
                wbrfscursor.execute('UPDATE settings SET wert1 = "%s" WHERE nam1 = "DPKG" AND group1 = "prog";' % (str(DPKG)))
wbrfscursor.execute('SELECT wert1 FROM settings WHERE nam1 = "exttmenu";')
row2 = wbrfscursor.fetchone()
if row2 is None:
		sets_prog["exttmenu"]=True
                wbrfscursor.execute("INSERT INTO settings (group1,nam1,wert1) VALUES(?,?,?);",  ("prog","exttmenu","True"))
else:
        sets_prog["exttmenu"]=row2[0]

wbrfscursor.execute('SELECT wert1 FROM settings WHERE nam1 = "eidie";')
global first, eidie
row4 = wbrfscursor.fetchone()
if row4 is None:
		first=1
else:
    eidie=row4[0]
    if row4[0] == "first" or row4[0] == "aktiviert":
            first=1
    #        wbrfscursor.execute('UPDATE settings SET wert1 = "aktiviert" WHERE nam1 = "eidie" AND group1 = "grund";')
    else:
        first=None
connection.commit()
import webradioFS
wbrfscursor.close()
connection.close()


from webradioFS import myversion
########################################################
def menu(menuid, **kwargs):
	if menuid == "mainmenu":
		return [("webradioFS", main, "webradioFS", None)]
	return []

def running_set(session):
    global running
    if running:
       running=False
       global webradiofs
       webradiofs=None
    else:
       running=True   

def standbycheck2():
     if Standby.inStandby and running:
             standbycheck.stop()
             abschalt()

def deak1(ans):
      if ans==True:
          countrys(("deakt","deakt"))
      
      else:
           main(session)      
def countrys(land):
    global first
    
    if land:   
      try:  
       if land[1].startswith("#"):
           main(session)
       elif land[1]=="skip":      
          f_start(session)              
       elif land[1]=="deaktivate":
            session.openWithCallback(deak1, MessageBox, _("reactivate not possible, really switch off permanently?")+"\n", type = MessageBox.TYPE_YESNO)

       elif land[0]:
        first=None
        if land[1]=="deakt":
            zahl=1
        else:
            import urllib2,urllib
            parameters = {'anfrage' : "sender", 'land' : str(land[0]).strip()}
            data = urllib.urlencode(parameters)
            f =  urllib2.urlopen("https://www.fs-plugins.de/wbr2FS/dlp/wbrfsreads2.php", data,timeout=20).readlines()
            from wbrfs_funct import fav_import3
            zahl=fav_import3().imp2(f)
        if zahl:
            connection = sqlite3.connect(set_file)
            connection.text_factory = str
            wbrfscursor = connection.cursor()
            wbrfscursor.execute('UPDATE settings SET wert1 = "aktiviert2" WHERE nam1 = "eidie" AND group1 = "prog";')
            connection.commit()
            wbrfscursor.close()
            connection.close()
        f_start(session)
       else:
        first=None
        f_start(session)
      except:
        Notifications.AddNotification(MessageBox, _("webradioFS-db unfortunately not available at the moment")+"\n", type=MessageBox.TYPE_INFO)
        f_start(session)

    else:
        first=None
        main(session)

def main(session, **kwargs):
  fr1=1
  if first:
    try:
      import urllib2
      from Screens.ChoiceBox import ChoiceBox
      request = urllib2.Request("https://www.fs-plugins.de/wbr2FS/dlp/first3.php")
      f =  urllib2.urlopen(request,timeout=10).readlines()
      c_land=[]
      dat1="0"
      laender="0"
      anzahl="0"
      if len(f)>10:
        for x in f:
                x=str(x).strip()
                if x.startswith("dat_"): 
                    dat1=x.replace("dat_","")
                elif x.startswith("lander_"): 
                   laender=x.replace("lander_","")
                elif x.startswith("streams_"): 
                    anzahl=x.replace("streams_","")
                elif x.startswith("x"): 
                    c_land.append((x.replace("x",""),"#"+x))
                else:
                    c_land.append((x,x))
        info="-> Info: "+dat1 + " / " + laender + " genres" + " / " + str(anzahl) + " streams"   
        c_land.insert(0, (info,"#"+info) )
        c_land.insert(0, (_("deactivate permanently"),"deaktivate") )
        c_land.insert(0, (_("skip function"),"skip") )
        session.openWithCallback(countrys, ChoiceBox, title=_('select preferred country'), list=c_land)
      else:
         f_start(session)
    except:
      f_start(session)
  else:
      f_start(session)

def f_start(session):
  #if fr1==2:
    if os.path.isfile(set_file):
       if not running and not Standby.inStandby:
            if DPKG:
               standbycheck_conn = standbycheck.timeout.connect(standbycheck2)
            else:
               standbycheck.callback.append(standbycheck2)
            standbycheck.start(600)
            running_set(session)
            global webradiofs
            reload(webradioFS)
            from webradioFS import WebradioFSScreen_15#,start
            webradiofs=session.openWithCallback(running_set,WebradioFSScreen_15)
    else:        
	     Notifications.AddNotification(MessageBox, _("Settings have been deleted, please restart your stb!")+"\n", type=MessageBox.TYPE_ERROR)


def autostarter():
         if session and not running:   
            run=1
            if Standby.inStandby:
                 if autoTimes[0][1]=="on_from_standby":
                     Standby.inStandby.Power()
                     autostarter2()
            else:
                autostarter2()

def autostarter2():
          if not running and not Standby.inStandby:      
                autostart_timer.stop()
                running_set(session)
                global webradiofs
                reload(webradioFS)
                from webradioFS import WebradioFSScreen_15#,start
                webradiofs=session.openWithCallback(running_set,WebradioFSScreen_15)
                make_autoT()
          else:           
                autostart_timer.start(10)

def make_autoT():
		autostart_timer.stop()
                global autoTimes
                now = datetime.datetime.now()
		new_autotimes=[]
		from wbrfs_funct import read_plan
		u_times=read_plan().reading("1")
                #f=open("/tmp/start","w")
                for x in u_times:
		    #f.write(str(x)+"\n")
                    args=x[3]
                    active=True
                    if not args['active']:
                        activ=False
                    if active and args['datum']:
                       if datetime.date.today() <> datetime.date.fromtimestamp(args['datum']):
                            active=False
                            if datetime.date.today() > datetime.date.fromtimestamp(args['datum']):
                                 d=read_plan().deling(args['setid'])
                    if active and args['weekdays']:
                        d=time.localtime(time.time())[6]
                        if not args['weekdays'][d]:
                              active=False
                    if active:    
                        if args['art'] and args['art'].startswith("on"):
			
                            now2 = [xl for xl in time.localtime()]
			    now2[3] = args['time'][0]
			    now2[4] = args['time'][1]
			    now2[5] = 0
			    t2=time.mktime(now2)
			    utime=datetime.datetime.fromtimestamp(t2)                        
			    if utime<now: 
				utime += datetime.timedelta(days=1)
			    t3=int(time.mktime(utime.timetuple()))
			    new_autotimes.append((int(t3-time.time()),args['art']))
		#f.close()
                autoTimes=new_autotimes
		if len(autoTimes):
			autoTimes.sort(key=lambda x: x[0], reverse=False)
			autostart_timer.startLongTimer(autoTimes[0][0])

autostart_timer=eTimer()
autostart_timer.timeout.get().append(autostarter)
#if len(autoTimes):
make_autoT()

def restarter2():
        if session and not running:    
            standbycheck.start(600)
            running_set(session)
            global webradiofs
            reload(webradioFS)
            from webradioFS import WebradioFSScreen_15 #,start
            webradiofs=session.openWithCallback(running_set,WebradioFSScreen_15)

#def ende(session):        
#        running_set(session)
        #from webradioFS import ex_right_site
        #try:t=ex_right_site(session,True)        
        #except:pass
def umschalt(stream=None):
    if stream and running:
        webradiofs.web_if_umschalt(stream)
        
def webrec():
        webradiofs.webrec()        
def playdir(mdir=None):
    if mdir and running:        
        webradiofs.web_if_playdir(mdir)        
def playdir2(mdir=None):
    if mdir and running:        
        webradiofs.web_if_playdir2(mdir)
def einzelplay(stream=None):        
    if stream and running:
        webradiofs.web_if_einzelplay(stream)
def fav_wechsel(fav=None):
    if fav and running and fav != "-":
        webradiofs.web_if_fav_wechsel(fav)
def list_play(dfile=None,rdir=None,auto=1):
    if dfile and running:
        webradiofs.web_if_listplay(dfile)
def play_stop(st=None):
    if st and running:
        webradiofs.web_if_play_stop(st)        
def abschalt():        
      if running:  
        standbycheck.stop()
        webradiofs.web_if_exit()


def standby_toggle(session): 
    Standby.inStandby.Power()
       

def Plugins(path,**kwargs):
    global plugin_path
    plugin_path = path
    list=[PluginDescriptor(name="webradioFS",description=_("Radio"),where = [PluginDescriptor.WHERE_PLUGINMENU],icon = npicon, needsRestart = False,fnc = main)]
    if str(sets_prog["hauptmenu"])=="True":
            list.append(PluginDescriptor(name="webradioFS", where = [PluginDescriptor.WHERE_MENU], fnc=menu))
    if str(sets_prog["exttmenu"])=="True":
            list.append(PluginDescriptor(name="webradioFS", where = [PluginDescriptor.WHERE_EXTENSIONSMENU],icon = npicon, needsRestart = False,fnc = main))
    list.append(PluginDescriptor(name="webradioFS", description="webradioFS",	where = [PluginDescriptor.WHERE_SESSIONSTART,	PluginDescriptor.WHERE_AUTOSTART], fnc = autostart))
    return list
	
	
def autostart(reason, **kwargs):
	if kwargs.has_key("session"):
		global session
		session=kwargs["session"]
		global webradiofs
		webradiofs=None
	if reason == 0 and kwargs.has_key("session"):
		from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
		from webradioFSSite import webradioFSweb
		from twisted.web import static
		root = static.File("/usr/lib/enigma2/python/Plugins/Extensions/webradioFS")
		root.putChild("", webradioFSweb())
		if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web/external.xml"):
			try:
				addExternalChild( ("webradiofs", root, "webradiofs", myversion, True) )
			except:
				addExternalChild( ("webradiofs", root) )
		if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/OpenWebif/pluginshook.src"):
			try:
				addExternalChild( ("webradiofs", root, "webradiofs", myversion) )
			except:
				pass


   																																													