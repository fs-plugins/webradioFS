from . import _

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen
from skin import parseColor
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.ActionMap import HelpableActionMap,ActionMap
from Components.Pixmap import Pixmap
from Components.ConfigList import ConfigListScreen, ConfigList
from Components.config import getConfigListEntry, ConfigText, NoSave
from GlobalActions import globalActionMap
from Tools.LoadPixmap import LoadPixmap
from enigma import getDesktop
from time import *
import time
import datetime
import os

plugin_path = "/usr/lib/enigma2/python/Plugins/Extensions/webradioFS"

class wbrfs_col_13(Screen, HelpableScreen):
    def __init__(self, session, text_col,back_col,r_inf):
                from .webradioFS import fontlist
                tmpskin = open(fontlist[5]+"wbrFS_screensaver.xml")
                self.skin = tmpskin.read()
                tmpskin.close() 
                self.r_inf=r_inf
                self.list=[]
                self.color_list=["00008B","D2691E","006400","696969","FFD700","000000","B22222","8B8878","CD0000","00868B","FFFFF0",
                "F0F8FF","8A2BE2","5F9EA0","98F5FF","8EE5EE","7AC5CD","53868B","6495ED","00008B","008B8B","483D8B","00CED1","00BFFF",
                "00BFFF","00B2EE","009ACD","00688B","1E90FF","1E90FF","C86EE","1874CD","104E8B","ADD8E6","BFEFFF","B2DFEE","9AC0CD",
                "68838B","E0FFFF","E0FFFF","D1EEEE","B4CDCD","7A8B8B","87CEFA","B0E2FF","A4D3EE","8DB6CD","607B8B","8470FF","B0C4DE",
                "CAE1FF","BCD2EE","A2B5CD","6E7B8B","66CDAA","0000CD","7B68EE","48D1CC","191970","000080","AFEEEE","BBFFFF","AEEEEE",
                "96CDCD","668B8B","B0E0E6","4169E1","4876FF","436EEE","3A5FCD","27408B","87CEEB","87CEFF","7EC0EE","6CA6CD","4A708B",
                "6A5ACD","836FFF","7A67EE","6959CD","473C8B","4682B4","63B8FF","5CACEE","4F94CD","36648B","7FFFD4","7FFFD4","76EEC6",
                "66CDAA","458B74","F0FFFF","F0FFFF","E0EEEE","C1CDCD","838B8B","0000FF","0000FF","0000EE","0000CD","00008B","00FFFF",
                "00FFFF","00EEEE","00CDCD","008B8B","000080","40E0D0","00F5FF","00E5EE","00C5CD","00868B","BC8F8F","FFC1C1","EEB4B4",
                "CD9B9B","8B6969","8B4513","F4A460","F5F5DC","A52A2A","FF4040","EE3B3B","CD3333","8B2323","DEB887","FFD39B","EEC591",
                "CDAA7D","8B7355","D2691E","FF7F24","EE7621","CD661D","8B4513","CD853F","D2B48C","FFA54F","EE9A49","CD853F","8B5A2B",
                "006400","BDB76B","556B2F","CAFF70","BCEE68","A2CD5A","6E8B3D","8FBC8F","C1FFC1","B4EEB4","9BCD9B","698B69","228B22",
                "ADFF2F","7CFC00","90EE90","20B2AA","32CD32","3CB371","00FA9A","F5FFFA","6B8E23","C0FF3E","B3EE3A","9ACD32","698B22",
                "98FB98","9AFF9A","90EE90","7CCD7C","548B54","2E8B57","54FF9F","4EEE94","43CD80","2E8B57","00FF7F","00FF7F","00EE76",
                "00CD66","008B45","9ACD32","7FFF00","7FFF00","76EE00","66CD00","458B00","00FF00","00FF00","00EE00","00CD00","008B00",
                "F0E68C","FFF68F","EEE685","CDC673","8B864E","FF8C00","FF7F00","EE7600","CD6600","8B4500","E9967A","F08080","FFA07A",
                "FFA07A","EE9572","CD8162","8B5742","FFDAB9","FFDAB9","EECBAD","CDAF95","8B7765","FFE4C4","FFE4C4","EED5B7","CDB79E",
                "8B7D6B","FF7F50","FF7256","EE6A50","CD5B45","8B3E2F","F0FFF0","F0FFF0","E0EEE0","C1CDC1","838B83","FFA500","FFA500",
                "EE9A00","CD8500","8B5A00","FA8072","FF8C69","EE8262","CD7054","8B4C39","A0522D","FF8247","EE7942","CD6839","8B4726",
                "8B0000","FF1493","FF1493","EE1289","CD1076","8B0A50","FF69B4","FF6EB4","EE6AA7","CD6090","8B3A62","CD5C5C","FF6A6A",
                "EE6363","CD5555","8B3A3A","FFB6C1","FFAEB9","EEA2AD","CD8C95","8B5F65","C71585","FFE4E1","FFE4E1","EED5D2","CDB7B5",
                "8B7D7B","FF4500","FF4500","EE4000","CD3700","8B2500","DB7093","FF82AB","EE799F","CD6889","8B475D","D02090","FF3E96",
                "EE3A8C","CD3278","8B2252","B22222","FF3030","EE2C2C","CD2626","8B1A1A","FFC0CB","FFB5C5","EEA9B8","CD919E","8B636C",
                "FF0000","FF0000","EE0000","CD0000","8B0000","FF6347","FF6347","EE5C42","CD4F39","8B3626","8B008B","9932CC","BF3EFF",
                "B23AEE","9A32CD","68228B","9400D3","FFF0F5","FFF0F5","EEE0E5","CDC1C5","8B8386","BA55D3","E066FF","D15FEE","B452CD",
                "7A378B","9370DB","AB82FF","9F79EE","8968CD","5D478B","E6E6FA","FF00FF","FF00FF","EE00EE","CD00CD","8B008B","B03060",
                "FF34B3","EE30A7","CD2990","8B1C62","DA70D6","FF83FA","EE7AE9","CD69C9","8B4789","DDA0DD","FFBBFF","EEAEEE","CD96CD",
                "8B668B","A020F0","9B30FF","912CEE","7D26CD","551A8B","D8BFD8","FFE1FF","EED2EE","CDB5CD","8B7B8B","EE82EE"
                ]
                self.text_color_index=0
                self.back_color_index=0
                if back_col not in  self.color_list:  
                      self.color_list.append(back_col)
                if text_col not in  self.color_list:  
                      self.color_list.append(text_col)
                self.back_color_index=self.color_list.index(back_col)
                self.text_color_index=self.color_list.index(text_col)
                Screen.__init__(self, session)
                self.skinName = "wbrScreenSaver_13"
                tage = [_('Monday'),_('Tuesday'),_('Wednesday'),_('Thursday'),_('Friday'),_('Saturday'),_('Sunday')]
                diezeit = time.localtime(time.time())
                self.TagesZahl = tage[diezeit[6]]
                uhrzeit = strftime("%H:%M",localtime())
                timewidget = "\n"+self.TagesZahl +", " + strftime("%d.%m.%Y",localtime()) + "   " + uhrzeit
                text01="webradioFS "+timewidget
                self["display_station"] = Label(_("Show live what you set"))
                self["display_nplaying"] = Label(_("Change color with: left,right, up,down")+",Help")

                self["display_time"] = Label(text01)
                self["background1"] = Label("")
                self["cover"] = Pixmap()
                self.dummyTxt=""
                self["cover2"] = Pixmap()
                #self["cover"].hide()
                self["cover2"].hide()
                #self["key_green"] = Label(_("Save"))
                #self["key_red"] = Label(_("Cancel"))
                HelpableScreen.__init__(self)
                self["actions"] = HelpableActionMap(self, "wbrfsKeyActions",
                        {
                        "green": (self.save,_("Save")),
                        "red": (self.exit,_("Cancel")),
                        "cancel": (self.exit,_("Cancel")),
                        "ok": (self.save, _("Save")),
                        "down": (self.text_color_down,_("preview text color")),
                        "up": (self.text_color_up,_("next text color")),
                        "right": (self.b_color_right,_("next back color")),
                        "left": (self.b_color_left,_("preview back color")),
                        }, -2)
                self.onLayoutFinish.append(self.start)

    def start(self):
                self.onLayoutFinish.remove(self.start)
                cover=LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/webradioFS/skin/images/wbrfsdef.png")
                self["cover"].instance.setPixmap(cover)
                self["display_nplaying"].instance.setTransparent(0)
                self["display_station"].instance.setTransparent(0)
                self["display_time"].instance.setTransparent(0)
                self.change_textfarbe()

    def col_set_back(self,bg,txt):
            if bg and txt:    
                self.color_list.append(bg)
                self.color_list.append(txt)
                self.text_color_index = len(self.color_list)-1
                self.back_color_index = len(self.color_list)-2
                self.change_textfarbe()

    def b_color_right(self):
         if self.back_color_index < len(self.color_list)-1:
           self.back_color_index +=1
         else:  
           self.back_color_index= 0
         self.change_textfarbe()

    def b_color_left(self):
         if self.back_color_index > 0:
           self.back_color_index -=1
         else:  
           self.back_color_index= len(self.color_list)-1
         self.change_textfarbe()

    def text_color_up(self):
         if self.text_color_index < (len(self.color_list)-1):
           self.text_color_index += 1
         else:  
           self.text_color_index= 0
         self.change_textfarbe()  

    def text_color_down(self):
         if self.text_color_index > 0:
           self.text_color_index-=1
         else:  
           self.text_color_index= len(self.color_list)-1
         self.change_textfarbe()

    def change_textfarbe(self):
            if self.dummyTxt==" ":
               self.dummyTxt=""
            else:
               self.dummyTxt=" "
            bg_farbe="#"+self.color_list[self.back_color_index]
            tx_farbe="#"+self.color_list[self.text_color_index]
            try:
                self["background1"].instance.setBackgroundColor(parseColor(bg_farbe))
                self["background1"].instance.setForegroundColor(parseColor(bg_farbe))
                self["display_nplaying"].instance.setBackgroundColor(parseColor(bg_farbe))
                self["display_station"].instance.setBackgroundColor(parseColor(bg_farbe))
                self["display_time"].instance.setBackgroundColor(parseColor(bg_farbe))
                self["display_nplaying"].instance.setForegroundColor(parseColor(tx_farbe))
                self["display_station"].instance.setForegroundColor(parseColor(tx_farbe))
                self["display_time"].instance.setForegroundColor(parseColor(tx_farbe))
                self.setTime()
            except:
                self.session.open(MessageBox, _("failed, not a regular color-string"), type = MessageBox.TYPE_INFO)

    def setTime(self):
                uhrzeit = strftime("%H:%M",localtime())
                timewidget = "\n"+self.TagesZahl +", " + strftime("%d.%m.%Y",localtime()) + "   " + uhrzeit
                self["display_time"].setText("webradioFS "+timewidget+self.dummyTxt)
                self["display_station"].setText(_("Show live what you set")+self.dummyTxt)
                self["display_nplaying"].setText(_("Change color with: left,right, up,down")+",Help"+self.dummyTxt)

    def save(self):
        col1=self.color_list[self.text_color_index]#.replace("#","")
        col2=self.color_list[self.back_color_index]#.replace("#","")
        self.close(col1,col2)

    def exit(self):
            self.close(None)
            
    def cancel(self):
        self.close(None)

