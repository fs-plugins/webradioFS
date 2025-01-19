from . import _
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from enigma import getDesktop
from enigma import eWindowStyleManager,eDVBVolumecontrol
from Components.ConfigList import ConfigListScreen

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.config import getConfigListEntry, ConfigInteger, ConfigYesNo, ConfigClock, ConfigSelection, ConfigNumber, ConfigSequence, config, NoSave

from time import localtime, mktime
from datetime import datetime, timedelta


class wbrfs_set_we(ConfigListScreen,Screen):
    def __init__(self, session):
        from webradioFS import fontlist
        self.fontlist=fontlist
        tmpskin = open(fontlist[5]+"wbrfs_set_we.xml")
        self.skin = tmpskin.read()
        tmpskin.close()
        self.now =datetime.now() + timedelta(minutes=3)
        self.alarm_time=NoSave(ConfigClock(default =mktime(self.now.timetuple())))
        self.chill_volume = NoSave(ConfigInteger(default=10, limits=(5, 100)))
        self.akt_volume=int(eDVBVolumecontrol.getInstance().getVolume())
        self.alarm_volume = NoSave(ConfigInteger(default=self.akt_volume, limits=(5, 100)))
        self.sound_on=False
        self.list1 = []
        self.list1.extend((
              getConfigListEntry(_("alert time"), self.alarm_time),
              getConfigListEntry(_("chill volume"), self.chill_volume),
              ))
        if self.akt_volume<100:
              self.list1.extend((
              getConfigListEntry(_("max volume"), self.alarm_volume),
              ))
        Screen.__init__(self, session)
        if self.fontlist[9]:
              self.skinName = "wbrfs_set_we_e"
        else:
              self.skin=self.skin.replace('backgroundColor="#000000"','')
              self.skin=self.skin.replace('foregroundColor="#ffffff"','')
              self.skinName = "wbrfs_set_we"
        self.setTitle(_("chill-timer")+"   - webradioFS ")
        ConfigListScreen.__init__(self, self.list1)
        self["key_green"] = Label(_("Start"))
        self["key_red"] = Label(_("Cancel"))
        txt= _("Set Time to wake up and volume for chilling")
        if self.akt_volume<100:
            txt="\n\n"+_("Warning: This function can changes the volume")
        self["warn"] = Label(txt)

        self["actions"] = ActionMap(["wbrfsKeyActions"],  #,"DirectionActions","MenuActions","InfobarChannelSelection"
            {
             "ok": self.ok,
             "green": self.ok,
             "red": self.exit,
             "cancel": self.exit,
             }, -2)
        self["config"].setList(self.list1)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self.onLayoutFinish.remove(self.layoutFinished)
        from webradioFS import fontlist
        if fontlist[8] or fontlist[9]:
          try:
            if not fontlist[4]: # and not my_settings['big_setup']:
                self['config'].instance.setFont(fontlist[3])
                self['config'].instance.setItemHeight(fontlist[2]) #(int((font+10)*font_scale))
            else:
                    from skin import parseFont
                    stylemgr = eWindowStyleManager.getInstance()
                    skinned = eWindowStyleSkinned()
                    eListboxPythonConfigContent.setDescriptionFont(parseFont(self.fontlist[3], ((1,1),(1,1))))
                    eListboxPythonConfigContent.setValueFont(parseFont(self.fontlist[3], ((1,1),(1,1))))
                    eListboxPythonConfigContent.setItemHeight(self.fontlist[2])
                    stylemgr.setStyle(0, styleskinned)
          except:
             pass


    def ok(self):
        lt = localtime()
        jetzt=(3600*lt[3])+(60*lt[4])+lt[5]
        meldezeit=3600*self.alarm_time.value[0]+60*self.alarm_time.value[1]
        if meldezeit <= jetzt:
            minuszeit=jetzt-meldezeit
            zeitdiff= 86400-minuszeit
        else:
            zeitdiff= meldezeit-jetzt
            if zeitdiff<120:
                self.session.open(MessageBox,_("Period must be greater than 2 minutes"),MessageBox.TYPE_INFO)
            else:
                self.close(zeitdiff,self.chill_volume.value,self.alarm_volume.value)

    def exit(self):
                self.close(0,None,None)