# -*- coding: utf-8 -*-
from . import _
from __init__ import _
from twisted.web import resource, http
from Screens.InfoBar import InfoBar
import Screens.Standby
from Screens.Standby import inStandby
from Components.PluginComponent import plugins
from Components.VolumeControl import VolumeControl
#from Components.Network import iNetwork
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import copyfile, resolveFilename, SCOPE_CURRENT_SKIN
from Components.VolumeControl import VolumeControl
from enigma import eDVBVolumecontrol
from enigma import eTimer
import random
import os
import urllib, urllib2

from webradioFS import WebradioFSScreen_15
from wbrfs_funct import read_einzeln
import webradioFS

fp=read_einzeln().reading((("audiofiles","audiopath"),("audiofiles","save_random"),("opt","audiofiles"),("prog","DPKG")))

audiopath=fp[0]  #sets2["audiopath"]
save_random=fp[1]   #sets2["audio_save_random"]
audiofiles=fp[2]
try:
    DPKG= fp[3]
except:
    DPKG= False
from webradioFS import file_list2

from plugin import myversion#,running
plugin_run=False



########################################################
import os, os.path
#######################################
def playlist_read(playlist):
       f2=open(playlist,"r")
       line = f2.readline()
       if not line.startswith('#EXTM3U'):
           return []
       pl=[]
       s=[None,None,None]                                
       for line in f2:
           line=line.strip()
           if line.startswith('#EXTINF:'):                                       
               length,title=line.split('#EXTINF:')[1].split(',',1)
               s=[length,title,None]
           elif (len(line) != 0):
               s[2]=line
               pl.append(s)
       f2.close()
       return pl
def run_webradioFS(session=None):
                 from plugin import restarter2
                 webradiofs=restarter2()

class webradioFSweb(resource.Resource):
	title = "webradioFS Webinterface"
 	isLeaf = True
        RestartGUI = False
	def __init__(self):
		resource.Resource.__init__(self)
                self.volctrl = eDVBVolumecontrol.getInstance()
		self.com_vol=int(self.volctrl.getVolume())
                self.stream=None
		self.fav=None
		self.search_on=None
		self.fav_list=()
		self.findliste=()
		self.sel_fav=""
		self.liste1=()
		self.list_play=""
		self.add=""
		self.entf=""
		self.playlist="0"
		self.playlistfile="/tmp/wbrfs_playlist"
		self.plugin_run=False
		self.l4l_info=None
		self.akt_time="20"
		self.alt_com=""
		self.searchdir=audiopath #None
		self.search_art="fi"
		self.pl_num="x"
		self.check_timer = eTimer()
		if DPKG:
                   self.check_timer_conn = self.check_timer.timeout.connect(self.action)
                else:
                   self.check_timer.callback.append(self.action)

		f=open("/tmp/wbrfs_playlist","a")
                f.close()
		for i in range(5):
		    f=open("/etc/ConfFS/playlist"+str(i+1)+".m3u","a")
                    f.close()		
	def render_GET(self, request):
		return self.action(request)
	def render_POST(self, request):
		return self.action(request)


	def vol_set(self,vol):
            self.com_vol=vol
            self.akt_volume=int(self.volctrl.getVolume())
            if vol=="mute":
               VolumeControl.instance.volMute()
            elif vol=="minus":
                VolumeControl.instance.volDown()
            elif vol=="plus":
                VolumeControl.instance.volUp()




	def action(self, req=None):
                self.check_timer.stop()
                from plugin import running
                if req:  
                  req.setHeader('Content-type', 'text/html')
		  req.setHeader('charset', 'UTF-8')
		  arg_check=len(req.args)

		  if arg_check>0:
                    command = req.args.get("cmd",None)
                    post_stream = req.args.get("stream",None)
                    post_playdir = req.args.get("playdir",None)
                    post_fav = req.args.get("fav",None)
                    post_add = req.args.get("add",None)
                    post_entf = req.args.get("entf",None)
                    post_list_play = req.args.get("list_play",None)
                    post_play_list= req.args.get("list_num",None)
                    post_vol0 = req.args.get("vol0.y",None)
                    post_volm = req.args.get("volm.y",None)
                    post_volp = req.args.get("volp.y",None)
                    post_search = req.args.get("search",None)
                    post_search_stop = req.args.get("search_stop",None)
                    post_clear = req.args.get("clear",None)
                    post_search_on = req.args.get("search_on",None)
                    post_einzel = req.args.get("einzelstream",None)
                    
                    if post_play_list is not None:
                       self.playlist=str(post_play_list[0])

                    if self.playlist=="0":
                      self.playlistfile="/tmp/wbrfs_playlist"
                    elif self.playlist==7:                    
                         pass #post_list_play=8
                    else:
                      self.playlistfile="/etc/ConfFS/playlist"+self.playlist+".m3u"                
                

                    self.fav=None
                    if post_vol0 is not None:
                       self.vol_set("mute")
                    elif post_volm is not None:
                       self.vol_set("minus")
                    elif post_volp is not None:
                       self.vol_set("plus")
                    elif post_einzel is not None:
                         if self.sel_fav == _("Playing from *.m3u") or self.l4l_info.get("Fav","")=="Playlist 8":
                             se=post_einzel[0].split(";.;")
                         else:
                             se=urllib.unquote(post_einzel[0]).split(";.;")
                         from plugin import einzelplay
                         t=einzelplay(se)
                    elif post_search_on is not None: 
                        if self.search_on:
                            self.search_on=None
                            self.findliste=()
                        else:
                            self.search_on=1
                    elif post_playdir is not None: 
                         from plugin import playdir
                         t=playdir(post_playdir[0])
                    elif post_stream is not None: 
                        if post_stream[0].endswith("/"):    
                            from plugin import playdir2
                            t=playdir2(post_stream[0])
                        elif post_stream[0].endswith(".m3u"):
                            self.fav = _("Playing from *.m3u")
                            self.playlistfile=post_stream[0]
                            from plugin import list_play
                            t=list_play((8,post_stream[0]))
                        else:
                            from plugin import umschalt
                            t=umschalt(urllib2.unquote(post_stream[0]))
                            self.stream=post_stream[0]
                            if post_stream[0].startswith("/"):
                                self.searchdir=os.path.os.path.dirname(post_stream[0])
                            elif post_stream[0].startswith(".."):
                                self.searchdir=audiopath
                    elif post_list_play is not None:
                        if str(post_list_play[0])=="stop":
                           from plugin import play_stop
                           t=play_stop(1)
                        elif str(post_list_play[0])=="rec":
                           from plugin import webrec
                           t=webrec()
                        else:
                            from plugin import list_play
                            t=list_play((int(post_list_play[0]),self.playlistfile))
                            self.akt_Play_nr=int(post_list_play[0])
                        #self.akt_time="5"
                    elif post_fav is not None:
                      #if self.fav !=post_fav[0]:
                        if self.sel_fav and (self.sel_fav == _("Playing from *.m3u") or self.l4l_info.get("Fav","")=="Playlist 8"):
                          from plugin import fav_wechsel
                          t=fav_wechsel(post_fav[0])
                          self.search=0
                        elif post_fav[0] != _("Search"):
                          from plugin import fav_wechsel
                          t=fav_wechsel(post_fav[0])
                          self.search=0
                        else:
                            self.search=1
                        self.fav=str(post_fav[0])

                    elif post_add is not None:                   
                            l_add=None
                            f2=open(self.playlistfile,"r")
                            einles = f2.readlines()
                            if len(einles): 
                                if len(einles[-1].strip()):
                                    l_add="\n"
                            else:
                                l_add="#EXTM3U\n"
                            f2.close()
                            self.add=post_add
                            f2=open(self.playlistfile,"a")
                            if l_add:f2.write(l_add)
                            if post_add[0]=="all2":
                               if str(save_random)=="True" or save_random=="random":
                                   random.shuffle(self.findliste)
                               for x in self.findliste:
                                    if not x[0].endswith(".m3u"):
                                        f2.write("#EXTINF:-1,"+x[0].decode("utf-8").encode("cp1252")+"\n"+x[1].decode("utf-8").encode("cp1252")+"\n")
                            elif post_add[0]=="all":
                               if str(save_random)=="True" or save_random=="random":
                                   random.shuffle(self.liste1)
                               for x in self.liste1:
                                   if x[7]== "Files" and not x[0].endswith(".m3u"):
                                       f2.write("#EXTINF:-1,"+x[0]+"\n"+x[1]+"\n")
                                       #f2.write(x[0]+";.;"+x[1]+";.;"+x[7]+"\n")

                            else:
                                se=urllib.unquote(post_add[0]).split(";.;")
                                if len(se)==3:
                                    if se[2].lower()=="files":
                                        if not se[0].endswith(".m3u"):
                                            f2.write("#EXTINF:-1,"+se[0].decode("utf-8").encode("cp1252")+"\n"+se[1].decode("utf-8").encode("cp1252")+"\n")
                                    else:
                                       nliste= file_list2([se[1]],"fi2").Dateiliste
                                       if str(save_random)=="True" or save_random=="random":
                                           random.shuffle(nliste)
                                       for r in nliste:
                                           if not r[0].endswith(".m3u"):
                                               f2.write("#EXTINF:-1,"+r[0].decode("utf-8").encode("cp1252")+"\n"+r[1].decode("utf-8").encode("cp1252")+"\n")
                                #f2.write(post_add[0].strip()+"\n")
                            f2.close()        
                            #self.akt_time="5"
                    elif post_entf is not None:                    
                        if os.path.isfile(self.playlistfile):          
                            if post_entf[0]=="1":
                                f2=open(self.playlistfile,"w+")
                                f2.close()
                            else:
                                rplaylist=playlist_read(self.playlistfile)
                                f2=open(self.playlistfile,"w+")
                                f2.write("#EXTM3U")                                
                                for x in rplaylist:
                                        if str(x) != str(post_entf[0]):
                                            f2.write('\n#EXTINF: '+x[0]+", "+x[1]+"\n"+x[2])    #.decode("cp1252").encode("utf-8")
                                f2.close()
                                try:
                                    if self.sel_fav.startswith(_("Playlist")):
                                        from plugin import list_play
                                        t=list_play((self.akt_Play_nr,self.playlistfile))
                                except:
                                    pass    
                    elif post_clear is not None:
                         self.findliste=()
                     #self.akt_time="5"
                    elif post_search_stop is not None:
			pass

                    elif post_search is not None:
                         art = req.args.get("art",None)[0]
                         self.search_art=art
                         sdir = urllib.unquote(req.args.get("sdir",None)[0])
                         text=req.args.get("searchtxt",None)[0]
                         if art and sdir and text and len(text.strip()):
                             text = text.strip().lower()
                             self.findliste= file_list2([sdir],art,1,text).Dateiliste

                    elif command is not None and command[0] is not None:
                        self.akt_time="5"
                        if command[0] ==  "starten":
                            if not running:   
                                self.plugin_run=True
                                run_webradioFS(self)
                                #command=None
                        elif command[0] ==  "stoppen":
		                self.plugin_run=False
		                self.l4l_info=None
		                self.search_on=None
                                from plugin import abschalt
                                t=abschalt()
                        elif command[0] ==  "box_on":
		            if Screens.Standby.inStandby:   
                                self.l4l_info=None
                                from plugin import standby_toggle
                                t=standby_toggle(self)
                        elif command[0] ==  "play_in_standby":
		            if Screens.Standby.inStandby:   
                                self.l4l_info=None
                                from plugin import play_in_standby
                                t=play_in_standby(self)
                        else:
                            pass
                    
                    #if arg_check>0:
                    self.akt_time="5"
		  else:
		    self.check_timer.startLongTimer(20)

                logo=None
		stream=None
		Webradiofs_l4l=None
                if running:
                  
                  self.fav_list=webradioFS.web_liste_favs
                  self.liste1=webradioFS.web_liste_streams
                  try:
	              from Plugins.Extensions.webradioFS.ext import ext_l4l
	              WebradiofsOK = True
	              Webradiofs_l4l = ext_l4l() 
	              if  self.l4l_info != Webradiofs_l4l.get_l4l_info():
                           self.l4l_info = Webradiofs_l4l.get_l4l_info()
                           self.akt_time="5"
                  except:
	                
                        WebradiofsOK = False
	                self.l4l_info=None

                  if WebradiofsOK == True:
                    if self.l4l_info.get("Logo","") and os.path.isfile(self.l4l_info.get("Logo","")):
		        logo = self.l4l_info.get("Logo","")
                        ret = copyfile(logo,"/usr/lib/enigma2/python/Plugins/Extensions/webradioFS/data/logo.png" )
                    if self.l4l_info.get("Station","") != "":
                        stream= self.l4l_info.get("Station","")
                    text=self.l4l_info.get("akt_txt","")
                vctrl = VolumeControl.instance.volctrl.getVolume()
                mute=   VolumeControl.instance.volctrl.isMuted()

                breite=1
                html = "<html>"
		html += "<head>\n"
		html += "<meta http-equiv=\"Content-Language\" content=\"de\">\n"
		html += "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\n"
		html += "<meta http-equiv=\"cache-control\" content=\"no-cache\" />\n"
		html += "<meta http-equiv=\"pragma\" content=\"no-cache\" />\n"
		html += "<meta http-equiv=\"expires\" content=\"0\">\n"
		html += '<meta http-equiv=\"refresh\" content=\"'+self.akt_time+'\">\n'
		html += '<meta name="viewport"  content="width=device-width, initial-scale=1" >\n'      #
                html += '<link rel=\"shortcut icon\" type=\"/web-data/image/x-icon\" href=\"/webradiofs/skin/images/favicon.ico\">' 
		html += "<title>webradioFS-webinterface</title>\n"
                html += '<style type="text/css">\n'
                html += 'div.line {\n'
                html += 'border:0;background-image: url("/webradiofs/skin/images/webif_line.png");background-repeat: no-repeat; '
                html += 'width: '+str(640/breite)+'px;height: 10;'
                html += '}\n'
                html += 'div.fsb {\n'
                html += 'position: relative;left: 420px;top: -23px;border:1px solid #000;background-color:#8A8A8A;width:150px;height:6px;padding:1px;}\n'
                html += 'div.fortschritt {\n'
                if mute:
                    html += 'background-color:#696969;height:6px;width:'+str(vctrl/breite)+'%;}\n'
                else:
                    html += 'background-color:#00CD00;height:6px;width:'+str(vctrl/breite)+'%;}\n'
                html += "</style>\n"
                html += "<script language=\"JavaScript\">\n"
                html += 'function load () { \n'
                html += 'window.location.replace("../webradiofs");\n'
                html += 'window.location.href="../webradiofs";\n'
                html += '}\n'
                html += '</script>\n'                
		html += "</head>\n"
		if self.akt_time=="5":
                    self.akt_time="20"
                    html += '<body onload="load()" bgcolor=\"#666666\" text=\"#FFFFFF\">\n'
                else:
                    html += '<body bgcolor=\"#666666\" text=\"#FFFFFF\">\n'
####################### erster block
		html += '<div style=\"width:100%; \">\n'
                html += '<div style=\"background-repeat:repeat-y;width:600px; background-image: url(/webradiofs/skin/images/webif_bgr.png)\">\n'   #width:600
                
                html += '<table width=600px><tr>'
                html += '<td colspan="3" style="text-align: center;"><br><img border=\"0\" src=\"/webradiofs/skin/images/webif.png\" ></td></tr><tr>\n'
                html += '<td width=200px style="padding-left: 10px;"><a style="font-size:1.2em;color:#6495ED" ">  </a></td>'                
                html += '<td width=200px style="text-align: center; vertical-align:bottom;font-size:1em;color:#FFFFFF">\n'
                html += '<b><i>Version: %s</i></b></td>\n'    % (myversion)
                html += '</tr></table>'                
                #html += '<div width='+str(640/breite)+'px style=\"padding-top:2px;padding-bottom:2px;\"><img border=\"0\" src=\"/webradiofs/skin/images/webif_line.png\" ></div>'
                html += '<div class="line"></div>'
                html += '</div>'
########################
                html += '<div style=\"font-size:1.4em;width:600px;text-align:center;background-repeat:repeat-y;background-image: url(/webradiofs/skin/images/webif_bgr.png)\">\n'
                if Screens.Standby.inStandby: 
                    html += '<span><b>%s</b></span><br><br>\n'    % ("Box in standby....")
                    html += "<form autocomplete=\"off\" method=\"GET\">"
                    html += "<input type=\"hidden\" name=\"cmd\" value=\"box_on\">"
                    html += '<input type="button" aria-label='+_("toggle standby")+' style=\"width:'+str(314/breite)+'px; height:54;font-size:1.4em;background-image: url(/webradiofs/skin/images/button_green.png)\" value=\"%s\" onclick=\"this.form.submit(); \">' % _("toggle standby")                   
                    html += '</form><span><br></span>'
                    html += '<div class="line">'
                    html += '</div>'                    
                else:
                   

          ####unter 1  schalter        
                    html += '<div style=\"padding-top:3px;height:64px;vertical-align:middle;padding-left:10px;float:left;width:350px\">\n'    #Inhalt der linken Spalte</div>
                    html += "<form autocomplete=\"off\" method=\"GET\">\n"
		    if not running:
                        html += "<input type=\"hidden\" name=\"cmd\" aria-label=\"Starten\" value=\"starten\">\n"
                        html += '<input type="button" aria-label='+_("start webradioFS")+' style=\"width:313px; height:54;font-size:1.4em;background-image: url(/webradiofs/skin/images/button_green.png)\" value=\"%s\" onclick=\"this.form.submit(); \">\n' % _("start webradioFS")                 
                    elif running:
                        html += "<input type=\"hidden\" name=\"cmd\" value=\"stoppen\">\n"
		        html += '<input type="button" aria-label='+_("exit webradioFS")+' style=\"width:313px; height:54;font-size:1.4em;background-image: url(/webradiofs/skin/images/button_red.png)\" value=\"%s\" onclick=\"this.form.submit(); \">\n' % _("exit webradioFS")
                    html += '</form>\n'   
                    html += '</div>\n'
	# unter daneben volume     
                    html += '<div style=\"height:55px;padding-top:0px;padding-right:30px;text-align:right;\">\n'
                    html += '<div style=\"height:46px;padding-top:5px;\">'
                    html += '<form method=\"post\">'
		    html += '<input name=\"vol0\" aria-label='+_("Mute")+' type=\"image\" src=\"/webradiofs/skin/images/mute.png\"  >&nbsp;&nbsp;' 
                    html += '<input name=\"volm\" aria-label='+_("Volume Down")+' type=\"image\" src=\"/webradiofs/skin/images/Leise.png\"  >&nbsp;&nbsp;'
		    html += '<input name=\"volp\" aria-label='+_("Volume Up")+' type=\"image\" src=\"/webradiofs/skin/images/Laut.png\" >' 
		    html += '</form>'
                     
              # im volume      
                    html += '<div class="fsb">'
                    html += '<div class="fortschritt"></div>'
                    html += '</div>'
                    html += '</div>'                    
              ########
              # close volume      
                    html += '</div>'
              # links float aufheben      
                    html += '<div style=\"clear:left;\"></div>'
                    html += '<div class="line"></div>'

        #volume ende
                    html += '</div>'
                    if Webradiofs_l4l and self.l4l_info.get("Fav",""):
 
                        self.sel_fav=self.l4l_info.get("Fav","")
                    if Webradiofs_l4l and stream and running:
                      html += '<div style=\"background-repeat:repeat-y;width:600; background-image: url(/webradiofs/skin/images/webif_bgr.png)\">\n'
                      if self.l4l_info.get("Genres","") != _("wbrfsfiles"):
                          html += '<div style=\"text-align: left;padding-top:3px;padding-bottom:3px;padding-left:10px;width:340px;float:left;\"><nobr>'
                          html += 'Stream: '+ self.l4l_info.get("Station","")+'<br>'
                          html += self.l4l_info.get("art","")+' '+ self.l4l_info.get("Fav","")+'<br>'#%(_("Group:"))
                          html += 'Bitrate: '+ self.l4l_info.get("Bitrate","")+'<br>'
                          html += 'Genre(s): '+ self.l4l_info.get("Genres","")+'</nobr>'
                          if self.l4l_info.get("liste") and self.l4l_info.get("liste") != "": # and self.l4l_info.get("liste")==self.l4l_info.get("Fav","")
                                self.sel_fav=self.l4l_info.get("liste")

                      else:
                          if self.l4l_info.get("liste") and self.l4l_info.get("liste") != "": # and self.l4l_info.get("liste")==self.l4l_info.get("Fav","")
                                self.sel_fav=self.l4l_info.get("liste")
                          elif self.l4l_info.get("Fav","").startswith(_("Playing from folder")):
                                self.sel_fav=_("Playing from folder")
                                self.fav=_("Playing from folder")                             
                          elif self.l4l_info.get("Fav","")=="Playlist 8" or self.l4l_info.get("Fav","").endswith(".m3u"):
                                self.fav=_("Playing from *.m3u")
                          else:
                                if self.fav:
                                    if liste1[0][7]=='radio':
                                       self.sel_fav=self.fav_list[0] 
                                    else:
                                       self.sel_fav=_("My files")
                          html += '<div style=\"text-align: left;padding-top:3px;padding-bottom:3px;padding-left:10px;width:340px;float:left;\"><nobr>'
                          if self.fav == _("Playing from *.m3u"): 
                               html += '<b>'+_("m3u:")+ "</b> "+self.l4l_info.get("Fav","").replace(_("Files from"),"")+'<br>' 
                               self.stream=self.l4l_info.get("akt_txt","")

                          elif self.fav and not self.fav.startswith(_("Playing")):
                              html += '<b>'+_("Group:")+ "</b> "+self.l4l_info.get("Fav","")+'<br>'
                              self.sel_fav=self.l4l_info.get("Fav","")
                              
                          d1=self.l4l_info.get("Station","")
                          dir2=os.path.dirname(d1).split('/')
                          if len(dir2)>2:
                              dir2="... /"+dir2[-2]+"/"+dir2[-1]
                          else:
                              dir2=d1
                          html += '<b>'+'Dir:</b> '+ dir2 +'<br>'  
                          html += '<b>'+'Typ:</b> '+ self.l4l_info.get("art","")
                          t_len=self.l4l_info.get("Len","")
                          if t_len:
                             html += '<br><b>'+'Len:</b> '+ str(t_len)
                      html += '</div>' 
                      html += '<div align="right" style=\"float:left;text-align:right;\">'
                      html += '<img border=\"0\" src=\"'

                      if logo:
                              html += '/webradiofs/data/logo.png' 

                      else:
                              html += '/webradiofs/skin/images/webif_logo.png'
                      html += '\" >\n'

                      html += '</div>' 
                      html += '<div style=\"clear: left;\"></div>'
                      if self.l4l_info and len(self.l4l_info.get("akt_txt","")):
                           html += '<div align="center" style=\"background-repeat:repeat-y;width:600; background-image: url(/webradiofs/skin/images/webif_bgr.png)\">\n' 
                           if self.l4l_info.get("art","") != "dir":
                               html += '<span align="center"  style="color:#E0FFFF;font-size:1.2em">'+self.l4l_info.get("akt_txt","")+'</span>'
                           else:
                               html += '<span align="center"  style="color:#E0FFFF;font-size:1.2em">'+ text+'</span>'
                           html += '</div>'
                      html += '<div class="line"></div>\n'

                    no_found=False
                    if len(self.fav_list) and running and (not self.l4l_info or self.l4l_info.get("rec","") != 1):
                        no_found=True
                        #if self.playlist and int(self.playlist)>6 :
                        #
                        #      if not _("Playing from *.m3u") in self.fav_list: self.fav_list.append(_("Playing from *.m3u"))
                        #      if not _("Playing from folder") in self.fav_list: self.fav_list.append(_("Playing from folder"))
                        if self.fav: 
                                self.sel_fav=self.fav
                        if self.sel_fav != _("No group selected"):
                            no_found=False
                        html += '<div style=\"font-size:1.4em;text-align: left;height:50px;padding-left:10px;padding-top:10px;width:100%;background-repeat:repeat-y; background-image: url(/webradiofs/skin/images/webif_bgr.png)\">\n'
                        html += '<form name="group" autocomplete=\"off\" method=\"GET\" >\n'    
                        html += _("Group:")+' <select name=\"fav\" onchange=\"this.form.submit(); \" style=\"background-color:#99CCFF;font-size:1em;\">\n'
                        html +='<option selected=\"selected\">'+self.sel_fav+'</option>\n'
                        tf_list=[]
                        for x in self.fav_list:
                            if x not in tf_list and x != self.sel_fav and x != _("No group selected") and x !=_("Genres"):
                              html +='<option>%s</option>\n'  % str(x)
                              tf_list.append(str(x))
                        html +='</select>\n';
                        tf_list=None
                        html += "</form>\n"

                        html += '</div>\n'
                        html += '<div class="line"></div>\n'

                    if len(self.liste1) and running and not no_found: 
 
                        html += '<div style=\"width:600;background-repeat:repeat-y; background-image: url(/webradiofs/skin/images/webif_bgr.png)">'
                        html += "<table style=\"width:100%;background-image: url(/webradiofs/skin/images/webif_bgr.png)\">\n"

                        if audiofiles and self.sel_fav==_("My files"): 
                            try:
                              st_path=os.path.dirname(self.liste1[0][1])
                              html += '<tr><td width="30"></td><td width="35">&nbsp;<a href="?add=all" style="color:yellow;text-decoration: none;font-size:1.2em">add</a>'
                              html += '</td><td> '+_("all visible files (not folder)")+'</td><tr>'
                            except:
                               pass
                        for x in self.liste1:
                         rec_html='</td><td width="35">&nbsp;&nbsp;'
                         if not x[0].startswith("@") and x[0] != "..autofs":  
                            if x[7] =="Dir":
                                  html += '<tr><td width="30"><a href="?playdir=%s" style="color:#ffffff;text-decoration: none;font-size:1.2em"><img border=\"0\" src=\"/webradiofs/skin/images/dir.png\">'  % (urllib.quote(x[1]))
                                  html += '</a>' 

                            else:
                              html += '<tr><td width="30"><img border=\"0\" src=\"/webradiofs/skin/images/'
                              if x[0]==stream or (int(x[4])>29 and self.l4l_info.get("Station","")==x[1]) :  #( x[0]==stream or (int(x[4])>29 and x[0]==self.stream)) or  
                                  html += 'pic_play.png" >'
                                  rec_html='</td><td width="35"><a href="?list_play=rec"><img src="/webradiofs/skin/images/webifrec.png"  width="28" height="28" border="0" alt="Stop"></a>'
                              elif x[7]=="Dir1":
                                  self.searchdir=x[2]
                                  html += 'up.png" >'
                              elif int(x[4]) >29 and x[7] !="Dir":
                                  
                                  if  self.l4l_info.get("Fav","")=="Playlist 8" and x[0]==self.stream : 
                                       html += 'pic_play.png" >'
                                       
                                  else:
                                      html += 'audiofile.png" >'
                              elif int(x[3]) >0 and x[7] != "Dir":
                                  html += 'pic_err.png" >'
                              else:
                                  html += 'pic_ok.png" >'
                            if len(x)>7 and(x[7]== "Dir" or x[7]== "Files"):
                                 stra=urllib.quote(x[0]+";.;"+x[1]+";.;"+x[7])
                                 if  x[1].endswith(".m3u") or str(self.playlist)=="7": 
                                     if self.l4l_info.get("art","") == _("file") and x[0]==os.path.basename(self.playlistfile):
                                         html += '</td><td width="35"><img border=\"0\" src=\"/webradiofs/skin/images/pic_play.png" >'
                                     else:
                                         html += '</td><td width="35">&nbsp;' 
                                 else:    
                                     if not  self.sel_fav.startswith(_("Playlist")):
                                         html += '</td><td width="35">&nbsp;<a href="?add=%s" style="color:yellow;text-decoration: none;font-size:1.2em">add</a>' % urllib.quote(stra)
                                     else:
                                         html += '</td><td width="35">&nbsp;<a href="?entf=%s" style="color:yellow;text-decoration: none;font-size:1.2em">del</a>' % x[6]
                            else:
                                 html += rec_html
                            if not self.l4l_info or(self.l4l_info and self.l4l_info.get("rec","")!=1):
                                 if x[0].endswith(".m3u"):
                                     html += '</td><td><a href="?stream=%s" style="color:#ffffff;text-decoration: none;font-size:1.2em"> %s </a>' % (urllib.quote(x[1]),x[0])
                                 elif x[7] =="Dir":                                 
                                         html += '</td><td><a href="?stream=%s" style="color:#ffffff;text-decoration: none;font-size:1.2em"> %s </a>' % (urllib.quote(x[1]),x[0])
                                         
                                 else:
                                     html += '</td><td><a href="?stream=%s" style="color:#ffffff;text-decoration: none;font-size:1.2em"> %s </a>' % (urllib.quote(x[0]),x[0])

                            else:
                               html += '</td><td style="color:#ffffff;text-decoration: none;font-size:1.2em"> %s' % (x[0])

                            if x[0]==stream and self.l4l_info and self.l4l_info.get("rec","")==1:
                                 html += ' <img border=\"0\" src=\"/webradiofs/skin/images/rec1.png">'
                            elif x[0]==stream and self.l4l_info and self.l4l_info.get("rec","")==2:
                                 html += ' <img border=\"0\" src=\"/webradiofs/skin/images/rc1.png">'

                        html += "</td></tr></table>\n"
                        html += '<div class="line"></div>\n'
                #############################################
                        
                        if audiofiles: 
                            html += '<div style=\"width:600;background-repeat:repeat-y; background-image: url(/webradiofs/skin/images/webif_bgr.png)">'
                            if self.l4l_info.get("liste") and self.searchdir and self.l4l_info.get("liste")== _("My files"):  #and self.search_on 
                                html += '<div style="font-size:1.4em;text-align: center; background-image: url(/webradiofs/skin/images/webif_bgr.png)"><a style="font-size:1.2em;color:#6495ED"  href="?search_on=1">search</a>' #+self.searchdir
                            
                                html += '<form method=\"GET\">'
                                
                                html += '<input type="hidden" name="sdir" value='+urllib.quote(self.searchdir) +'>'     #sdir
                                html += '<table style=\"width:100%;\"><tr>'
                                html += '<td colspan="3" align="left">in: '+ self.searchdir +'</td></tr><tr><td> </td></td><td>\n'
                                for x in (("Files","fi"),("Folder","fo"),("Files+Folder","fifo")):
                                    if x[1] == self.search_art:
                                        html += '<input type="radio" name="art" value="'+x[1]+'" checked="checked"> '+x[0]
                                    else:
                                        html += '<input type="radio" name="art" value="'+x[1]+'"> '+x[0]
                                html += '</td><td align="right"><input type="submit" name="clear" value="clear list"></td></tr><tr>\n'
		                html += '<td style="font-size:1.2em;">Search term: </td><td><input style=\"font-size:1.4em;background-color:#99CCFF;\" name=\"searchtxt\" type=\"text\" size=\"26\" maxlength=\"50\"</td>\n'
		                html += '<td align="right"><input type="submit" name="search" value="Start">&nbsp;&nbsp;&nbsp;&nbsp;'
                                html += '</td></tr></table>\n'
		                html += '</form>\n' 
                               
			        t=0
                                if len(self.findliste):
                                    html += '<div class="line"></div>\n'
                                    html += '<div style="font-size:1em;text-align: left;color:#E0FFFF;background-repeat:repeat-y; background-image: url(/webradiofs/skin/images/webif_bgr.png)">\n'
                                    html += "<table style=\"width:100%;background-image: url(/webradiofs/skin/images/webif_bgr.png)\">\n"
                                    html += '<tr><td width="30"></td><td width="35">&nbsp;<a href="?add=all2" style="color:yellow;text-decoration: none;font-size:1.2em">add</a>'
                                    html += '</td><td> '+_("all visible files and all files in folder")+'</td><tr>'
                                    for x in self.findliste:
                                        
                                        if len(x)>7 and (x[7]== "Dir" or x[7]== "Files"):
                                            
                                            html += '<tr><td width="30"><img border=\"0\" src=\"/webradiofs/skin/images/'
                                            if x[7] =="Dir":
                                                    html += 'dir.png" >'
                                            elif int(x[4]) >29 and x[7] !="Dir":
                                                    html += 'audiofile.png" >'
                                            stra=urllib.quote(x[0]+";.;"+x[1]+";.;"+x[7])
                                            html += '<td width="35">&nbsp;<a href="?add=%s" style="color:yellow;text-decoration: none;font-size:1.2em">add</a>\n' % (stra)
                                            stra=urllib.quote(x[0]+";.;"+x[1]+";.;"+x[7])
                                            html += '</td><td><a href="?einzelstream=%s" style="color:#ffffff;text-decoration: none;font-size:1.2em"> %s </a>' % (stra,x[0])
                                            html += '</td><tr>\n'
                                            if t==0 and len(x): t=1
                                    html += '</tr></table>\n'
                                html += '</div>\n'
                                html += '<div class="line"></div>\n'
                            html += '</div>\n'
                            
#######################################################################                            
                            
                            html += '<div style=\"font-size:1.2em;text-align: center;color:#E0FFFF;background-repeat:repeat-y; background-image: url(/webradiofs/skin/images/webif_bgr.png)\">Play-List: '
                            akt_list="-1"
                            i=0
                            for i in range(6): 
                                u1=""
                                u2=""
                                farbe="#ffffff"
                                if str(i)==self.playlist:
                                    farbe="yellow"
                                    akt_list=self.playlist
                                    u1="<u>"
                                    u2="</u>"
                                else:                                    
                                    if i==0:
                                      file="/tmp/wbrfs_playlist"
                                    else:
                                      file="/etc/ConfFS/playlist"+str(i)+".m3u" 
                                    ylist=playlist_read(file)
                                    if len(ylist):
                                       farbe="green"
                                    else:
                                       farbe="#ffffff"
                                if i==0:
                                    html += '&nbsp;&nbsp;&nbsp;&nbsp;<a href="?list_num=0" style="color:'+farbe+';text-decoration: none;font-size:1.4em">'+u1+' temp '+u2+'</a>'
                                else:
                                    html += '&nbsp;&nbsp;&nbsp;&nbsp;<a href="?list_num='+str(i)+'" style="color:'+farbe+';text-decoration: none;font-size:1.4em">'+u1+str(i)+u2+'</a>'

                            html += '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="?list_play='+str(int(self.playlist)+1)+'"><img src="/webradiofs/skin/images/lPlay.png"  width="28" height="28" border="0" alt="Play"></a>'
                            html += '&nbsp;&nbsp;&nbsp;&nbsp;<a href="?list_play=stop"><img src="/webradiofs/skin/images/lStop.png"  width="28" height="28" border="0" alt="Stop"></a>'
                            html += '</div>\n'
                            html += '<div class="line"></div>\n'                            
                                           

                            if self.fav == _("Playing from *.m3u") or(os.path.isfile(self.playlistfile) and _("Playlist")+" "+akt_list != self.sel_fav):
                               playlist=playlist_read(self.playlistfile)
                               if str(self.playlist)!="7" :
                                 if len(playlist):
                                   html += "<table style=\"width:100%;background-image: url(/webradiofs/skin/images/webif_bgr.png)\">\n" 
                                   if int(self.playlist)<7:
                                       html += '<tr><td width="25" align="left"><a href="?entf=1" style="color:yellow;text-decoration: none;font-size:1.2em">del</a>' 
                                       html += '</td><td></td><td align="left" style="text-decoration: none;font-size:1.2em">%s</td></tr> ' % _("all (del all entries)")
                                   for x in playlist:
                                       stra=urllib.quote(x[1]+";.;"+x[2]+";.;"+"Files"+";.;"+self.playlistfile+";.;"+str(int(self.playlist)+1 ))
                                       html += '<tr><td width="25" align="left"><a href="?entf=%s" style="color:yellow;text-decoration: none;font-size:1.2em">' % (x)
                                       if int(self.playlist)<7:
                                           html += 'del</a>' 
                                       html += '</td><td>'
                                       if self.l4l_info.get("Station","")==x[2]: #.decode("iso-8859-1").encode("utf-8"):
                                          html += '<img border=\"0\" src=\"/webradiofs/skin/images/pic_play.png"></td>'
                                          txt=x[1].decode("iso-8859-1").encode("utf-8")
                                       else:
                                           html += '&nbsp;</td>'
                                           txt= x[1].decode("iso-8859-1").encode("utf-8")
                                       #f=open("/tmp/weblist","a")
                                       #f.write(str(x)+"\n")
                                       #f.close()
                                       if x[1].endswith(".m3u"):
                                           html += '</td><td><a href="?stream=%s" style="color:#ffffff;text-decoration: none;font-size:1.2em"> %s </a>' % (urllib.quote(x[2]),x[1])
                                       else:
                                          html += '<td><a href="?einzelstream=%s" style="color:#ffffff;text-decoration: none;font-size:1.2em">&nbsp;&nbsp;%s </a></td></tr>' % (stra,txt)
    
                                   #f.close()
                                   html += "</table>\n"
                                 else:
                                   html += '<div style=\"font-size:1.4em;text-align: center;height:50px;width:600;">'
                                   pl_nam=str(self.playlist)
                                   if self.playlist=="0":pl_nam="temp"
                                   html += _("Playlist")+" "+pl_nam+" "+_("contains no audio files\nor is incorrectly formatted").replace("\n","<br>")                                  
                               html += '<div class="line"></div>\n'
                    elif self.sel_fav == _("No group selected") and running:
                       html += '<div style=\"font-size:1.4em;text-align: center;height:50px;width:600;">'
                       html += _("save in favorites for all functions")+"..."
                       html += "</div>"

                html += "</div>"
                html += "</div>"
		return html








