from . import _

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Components.ServicePosition import ServicePositionGauge
from Components.Sources.List import List

from enigma import getDesktop
from enigma import ePicLoad

from Tools.LoadPixmap import LoadPixmap
from sqlite3 import dbapi2 as sqlite

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard

#from skin import parseColor

from .wbrfs_funct import webradioFSdisplay13,read_einzeln
#skin_ignore=read_einzeln().reading((("grund","skin_ignore"),))[0]

try:
    from Plugins.Extensions.LCD4linux.module import L4Lelement
    MyElements = L4Lelement()

except:
    l4l=None
 
plugin_path = "/usr/lib/enigma2/python/Plugins/Extensions/webradioFS"
picpath=plugin_path +"/skin/images/"
pngok = LoadPixmap(picpath+"pic_ok.png")
   

        
class menu_13(Screen):
    def __init__(self, session,sendlist=[],titel=_("webradioFS-Menu"),back=None,display=None,l4ls=None):
        from .webradioFS import fontlist
        tmpskin = open(fontlist[5]+"webradioFS.xml")
        self.sendlist=sendlist
        self.skin = tmpskin.read()
        tmpskin.close()
        Screen.__init__(self, session)
        if fontlist[9]:
                     self.skinName = "WebradioFSScreen_e"
        else:
                     self.skin=self.skin.replace('backgroundColor="#000000"','')
                     self.skin=self.skin.replace('foregroundColor="#ffffff"','')
        self.skinName = "WebradioFSScreen_16"
        self.back=back
        self.display=display
        self.l4ls=None
        try:
                   if l4ls[0]=="True":
                      self.l4ls=l4ls
        except:
                    pass

        self["streamlist"] = List([])
        self["dummy"] = Pixmap()
        self["playtext"] = StaticText("") #Label("")
        #self["rec_txt"] = Label()
        #self["rec_txt2"] = Label()
        self["rec_text_new"]=List([(titel,"")])
        self["rec_text_new"].style = "titel"
        #self["rec_text_new"].disable_callbacks = False

        self["green_pic"] = Pixmap()
        self["rec_pic"] = Pixmap() 
        self["buttons_abdeck"] = Label("")
        self["key_red2"] = Label("") 
        self["key_green2"] = Label("")
        self["key_red"] = Label("") 
        self["key_green"] = Label("") 
        self["key_yellow"] = Label("") 
        self["key_blue"] = Label("") 
        self["help"] = ScrollLabel("")

        hide_list=(self["key_red2"],self["key_green2"],self["rec_pic"],self["help"])
        for x in hide_list:
            x.hide()
        self["uactions"] = ActionMap(["DirectionActions"],
            {
                    "up" : self.upPressed,
                    "down" : self.downPressed,
            })
        self["actions"] = ActionMap(["wbrfsKeyActions"],
        {
        "ok": self.run,
        "back": self.exit,
        "menu": self.exit2,
        "cancel": self.exit,
        })
        self["GlobalwbrfsKeyActions"] = ActionMap(["GlobalwbrfsKeyActions"],
        {
                    "up" : self.upPressed,
                    "down" : self.downPressed,
        })
        self.onChangedEntry = []
        self["streamlist"].onSelectionChanged.append(self.selectionChanged)
        self.onLayoutFinish.append(self.updateList)
        self.setTitle(titel)

    def downPressed(self):
        self["streamlist"].selectNext()

    def upPressed(self):
        self["streamlist"].selectPrevious()


    def updateList(self):
        res=[]
        for eintrag in self.sendlist:
            res.append((eintrag,str(eintrag[0])))
        
        self["streamlist"].style = "menus"
        self["streamlist"].setList(res)
        #self["streamlist"].disable_callbacks = True
        self["streamlist"].setIndex(0)
    def run(self):
          auswahl = self["streamlist"].getCurrent()[0]
          if len(auswahl)>4 and auswahl[4] != None and auswahl[1] == None:
             from wbrfs_funct import filemenu
             filemenu(self.session).start(auswahl[4])
          else:
              self.close(auswahl,self.back)
    def exit(self):
          self.close(None,self.back)
    def exit2(self):
          self.close(None,None)

    def createSummary(self):
        if self.display:
            return webradioFSdisplay13

    def selectionChanged(self):
        try:
            sel = self["streamlist"].getCurrent()[0][0] 
            text1=_("webradioFS-Menu")
            text2= sel 
            self["playtext"].setText(str(self["streamlist"].getCurrent()[0][2]))
            if self.l4ls and len(self.sendlist):
            #try:
                       txt=""
                       menuliste=[]
                       for x in self.sendlist:
                            if self["streamlist"].getCurrent() and x[0]==self["streamlist"].getCurrent()[0][0]:
                               menuliste.append(">> "+x[0])#[0:20]
                            else:
                              menuliste.append(" "*5+x[0])
                       txt = '\n'.join(x for x in menuliste)
                       MyElements.add( "wbrFS.07.box7",{"Typ":"box","PosX":0,"PosY":0,"Width":5000, "Height":600,"Color":"black" , "Screen":str(self.l4ls[3]),"Lcd":self.l4ls[1],"Mode":"OnMedia"} )
                       MyElements.add( "wbrFS.08.txt8",{"Typ":"txt","Align":"0","Width":500,"Pos":0,"Text":txt,"Size":str(self.l4ls[27]),"Color":str(self.l4ls[29]),"Screen":str(self.l4ls[3]),"Lines":20,"Lcd":self.l4ls[1],"Mode":"OnMedia"} )
                       MyElements.setScreen(self.l4ls[3],self.l4ls[1],True)

        #f.close()
            if self.display:
                for cb in self.onChangedEntry:
                    cb(text1,text2)
        except:
                 pass
                 
class groups_13(Screen):
    def __init__(self, session,fav,titel=_("Group-Menu")):
                from webradioFS import fontlist
                tmpskin = open(fontlist[5]+"webradioFS.xml")
                self.skin = tmpskin.read()
                tmpskin.close()                
                self.fav=fav
                self.g_list=[]
                Screen.__init__(self, session)
                if fontlist[9]:
                    self.skinName = "WebradioFSScreen_e"
                else:
                     self.skin=self.skin.replace('backgroundColor="#000000"','')
                     self.skin=self.skin.replace('foregroundColor="#ffffff"','')
                     self.skinName = "WebradioFSScreen_16"
                self["streamlist"] = List([])
                self["dummy"] = Pixmap()
                self["playtext"] = StaticText("")
                self["rec_text_new"]=List([(_("Group-Menu"),"")])
                self["rec_text_new"].style = "titel"
                self["green_pic"] = Pixmap()
                self["rec_pic"] = Pixmap() 
                self["buttons_abdeck"] = Label("")
                self["key_red2"] = Label("") 
                self["key_green2"] = Label("")
                self["playline2"] = ServicePositionGauge(self.session.nav)

                self["key_red"] = Label(_("Delete")) 
                self["key_green"] = Label(_("New")) 
                self["key_yellow"] = Label(_("Rename")) 
                self["key_blue"] = Label("") 
                self["help"] = ScrollLabel("")
                self.connection = sqlite.connect(self.fav)
                self.connection.text_factory = str
                self.cursor = self.connection.cursor()
                hide_list=(self["key_red2"],self["key_green2"],self["rec_pic"],self["help"],self["playline2"],self["buttons_abdeck"])
                for x in hide_list:
                    x.hide()

                self["actions"] = ActionMap(["wbrfsKeyActions", "ColorActions"],
                    {
                        "ok": self.run,
                        "cancel": self.exit,
                        "red": self.gdel,
                        "green": self.add,
                        "yellow": self.rename,
                    })
                #self["streamlist"].onSelectionChanged.append(self.selectionChanged)
                self.onLayoutFinish.append(self.updateList)
                self.setTitle(titel)


    def updateList(self):
                self.g_list=[]
                #self.g_list2=[]
                self.cursor.execute("select * from groups;")
                for row in self.cursor:
                    l= (row[0],row[1])      
                    if l not in self.g_list:      
                            self.g_list.append((row[0],row[1]))
                            #self.g_list2.append(row[0])
                #self.group_len=len(self.g_list2)
                self.cursor.execute("SELECT COUNT (*) from streams where group1 NOT IN ( select group_id from groups );")
                data=self.cursor.fetchone()
                if data[0]>0:
                    self.g_list.append((6000,_("not assigned")))
                self.group_len=len(self.g_list)
                self["streamlist"].style = "menus"
                self["streamlist"].setList(self.g_list)
                self["streamlist"].disable_callbacks = True

    def rename(self):
          self.group = self["streamlist"].getCurrent()
          self.session.openWithCallback(self.rename2,VirtualKeyBoard, title=_("Rename group"), text=self.group[1]) #, maxSize=max_laenge, type=typ1)
    def rename2(self,newnam):
          if newnam and newnam != self.group[1]:            
              grp_num=int(self.group[0])
              self.cursor.execute('UPDATE groups SET group1 = "%s" where group_id = %d' % (newnam,grp_num))
              self.connection.commit()
              self.updateList()
    def run(self):
          auswahl = self["streamlist"].getCurrent()[1]#[0]
          groups=[]
          for row in self.g_list:
               l= (row[0],row[1])
               if l not in groups:
                   groups.append(l)
          self.cursor.close()
          self.connection.close()

          self.close(auswahl,groups)
    def exit(self):
          groups=[]
          for row in self.g_list:
               l= (row[0],row[1])
               if l not in groups:
                   groups.append(l)
               #groups.append((row[0],row[1]))
          self.cursor.close()
          self.connection.close()
          self.close(None,groups)
    def add(self):
          self.session.openWithCallback(self.add_g2,VirtualKeyBoard, title=_("Enter Name for new group"), text="") #, maxSize=max_laenge, type=typ1)

    def add_g2(self,g=None):
         if g:  
           self.cursor.execute('INSERT INTO groups (group1) VALUES("%s");'  %g)
           self.connection.commit()
           self.updateList()
    def gdel(self):
        if self.group_len>1 or self["streamlist"].getCurrent()[1] == _("not assigned"):
            self.group = self["streamlist"].getCurrent()
            #if self.group[0]==_("not assigned"): self.group=""
            self.session.openWithCallback(self.del_2, MessageBox, _("Delete all the streams of this group?") +"\n\n%s" % self.group[1] ,type = MessageBox.TYPE_YESNO)
        else:
            self.session.open(MessageBox, _("at least one group must be present!") ,type = MessageBox.TYPE_ERROR)
    def del_2(self,answer):
         if answer==True and self.group:   
            if self.group_len>1 or self["streamlist"].getCurrent()[1] == _("not assigned"):
               #if self.group[1] != "5000" and self.group[1] != "6000":
               #self.cursor.execute("delete from groups where group_id = %d" % (self.group[1]))
               self.connection.commit()
               if self.group[0] == 6000:
                   bef="delete from streams where group1 NOT IN ( select group_id from groups )"
                   self.cursor.execute(bef)
                   self.connection.commit()
               else:
                   try:
                      grp_num=int(self.group[0])
                      self.cursor.execute("delete from streams where group1 = %d" % (grp_num))
                      self.cursor.execute("delete from groups where group_id = %d" % (grp_num))
                      self.connection.commit()
                   except:
                      self.session.open(MessageBox, _("Group can not be deleted") ,type = MessageBox.TYPE_ERROR)            
               self.updateList()

                        