#!/usr/bin/python
# Script to display Now playing info on a 16x2 LCD via lcdproc
#Copyright (C) 2016  Pradeep Murthy

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

# to do as of 20160326 
# make it flexible to accommodate 20x4 LCDs
# get player string instead of hardcoding

import lcdproc.server
import subprocess
import urllib
import re
import threading
from time import sleep
import sys
import syslog

def time_update(myartist,mytitle):
    global songchangeflag
    global pauseflag
    global mode
    curartist=get_metadata("artist")
    curtitle=get_metadata("title")
    if pauseflag == 1 :
        mytimeremaining = 0
    else :
        mydur = float(get_metadata("duration"))
        mytime = float(get_metadata("time"))
        mytimeremaining = int(mydur - mytime)
    while mytimeremaining != 0 :
        if pauseflag == 1 :
            return
        if (myartist == curartist and mytitle == curtitle):
            trmin=mytimeremaining/60
            trsec=mytimeremaining - trmin*60
            if trmin < 10 :
                trmin=" "+str(trmin)
            else:
                trmin=str(trmin)
            if trsec < 10 :
                trsec=":0"+str(trsec)
            else:
                trsec=":"+str(trsec)
            timeremaining_widget.set_text(trmin+trsec)
            sleep(1)
            mytimeremaining = mytimeremaining - 1
            if (songchangeflag == 1) :
                curartist = get_metadata("artist")
                curtitle = get_metadata("title")
                songchangeflag = 0
        else:
            return
    return

def get_metadata(metadata):
    # metadata: one of artist, title, mode, duration, time. always returns string, even for numbers
    p1 = subprocess.Popen('telnet 127.0.0.1 9090', stdin = subprocess.PIPE, stdout=subprocess.PIPE, stderr = None, shell=True)
    cmd = "80:1f:02:6f:c5:2f "+metadata+" ?\n"
    p1.stdin.write(cmd)
    myline=''
    while True:
        out = p1.stdout.read(1)
        if myline.endswith(metadata) and p1.poll != None:
            break
        else :
            myline=myline+out
    myline=''
    while True:
        out = p1.stdout.read(1)
        if out == '\n' and p1.poll != None:
            break
        else :
            myline=myline+out
    p1.stdin.write("exit\n")
    p1.kill()
    return(urllib.unquote(myline))

def update_display():
    global artist
    global title
    
    # get data
    artist = get_metadata("artist")
    title = get_metadata("title")

    # set data on LCD
    artist_widget.set_text(artist)
    title_widget.set_text(title)

    # Call time update
    t1 = threading.Thread(target=time_update, args=(artist,title,))
    t1.daemon = True
    t1.start()

    # switch on backlight
    scr1.set_backlight("on")

    return

# Set up the lcd screen
lcd = lcdproc.server.Server(debug=False)
lcd.start_session()
scr1 = lcd.add_screen("Squeezeboxtest")
scr1.set_heartbeat("off")
artist_widget = scr1.add_scroller_widget("Artist", left=1, top=1, right=10, bottom=1, direction="h", speed=4, text="")
timeremaining_widget = scr1.add_string_widget("timeremaining",  text="", x=12, y=1)
title_widget = scr1.add_scroller_widget("Title", left=1, top=2, right=16, bottom=2, direction="h", speed=4, text="")
scr1.set_backlight("off")


# Initialize variables
songchangeflag = 0
pauseflag = 0

# find out if the player is playing or stopped
mode=get_metadata("mode")

if mode == "play" :
    pauseflag = 0
    songchangeflag = 0
    update_display()
else :
    pauseflag = 1
    
# Now start main telnet session and listen
p = subprocess.Popen('telnet 127.0.0.1 9090', stdin = subprocess.PIPE, stdout=subprocess.PIPE, stderr = None, shell=True)
p.stdin.write("listen 1\n")

for line in iter(p.stdout.readline, b''):
#   Some update on the telnet socket. need to find out what happened. So get updated metadata
    line = line.rstrip()
    if not (re.search('Trying', line) or re.search('Connected', line) or re.search('Escape', line) ) :
        newmode=get_metadata('mode')
        if newmode == "play" :
            newartist = get_metadata("artist")
            newtitle = get_metadata("title")
            if mode == "play" : # old and new modes are both play. So maybe new song
                if ( artist != newartist or title != newtitle) : # defly new song
                    songchangeflag = 1
                    update_display()
            else : # mode was not play. So we got unpaused
                pauseflag = 0
                mode = newmode
                update_display()
        else : # new mode is not play. so we got paused
            pauseflag = 1
            scr1.set_backlight("off")
            mode = newmode

# clean up on exit
p.kill()
lcd.screen_del(scr1.ref)
