#!/usr/bin/python
from __future__ import absolute_import, division, print_function, unicode_literals

from ft5406 import Touchscreen, Touch
from part_three_reader import Part3Reader
from interface_state import InterfaceState
from options import OptionsDialogue,OptionsEvent
from globes import Globes

from math import sin,cos,log
import pi3d, pickle, sensor_monitor, numpy as np
from scipy.spatial.transform import Rotation
from motion_delegate import UserGestures
from wifi_process_manager import WirelessToolkit
#from wifi_thread_manager import WirelessToolkit
from zoom_interp import ZoomInterpolator

#constants
back_wall=-15.0     #camera's max z coordinate
initial_cam_z=-12.0         #camera's initial z coordinate
partition=120       #sphere geometry complexity
touchscreen_id='generic ft5x06 (00)'
poetryxml='/var/www/html/xml/poems.xml'
fontpath='/var/www/html/css/fonts/Karma/Karma-Bold.ttf'
root_dir='/home/pi/globe/'

#camera state
cam_z=initial_cam_z
autoplay=list()

######################################
#       3d Infrastructure Setup
######################################

# Setup display and initialise pi3d
display = pi3d.Display.create(x=0, y=0, frames_per_second=30, display_config=pi3d.DISPLAY_CONFIG_HIDE_CURSOR | pi3d.DISPLAY_CONFIG_MAXIMIZED)
#display = pi3d.Display.create(x=0, y=0, frames_per_second=30, display_config=pi3d.DISPLAY_CONFIG_MAXIMIZED)
display.set_background(0,0,0,255)    # RGBA
flatsh = pi3d.Shader("uv_flat")

light = pi3d.Light(lightpos=(0.0, 0.0, back_wall))
#these two shaders implement a 2-pass Gaussian blur filter
hblur=pi3d.Shader(root_dir+"shaders/filter_hblur")
vblur=pi3d.Shader(root_dir+"shaders/filter_vblur")
hshader = pi3d.PostProcess(shader=hblur)
vshader = pi3d.PostProcess(shader=vblur)

#main camera
cam = pi3d.Camera(eye=(0,0,cam_z))
#torus camera
cam2 = pi3d.Camera(eye=(0,0,cam_z))
#2d camera for the menu
cam_flat=pi3d.Camera(is_3d=False)

#this object tracks the interface state: fade between torus/globes
ui_state:InterfaceState=InterfaceState()


######################################
#       Globe Setup
######################################
globes:Globes=Globes(cam,flatsh,display)

######################################
#       User IF Setup
######################################

# Fetch key presses
keys = pi3d.Keyboard()
mouse=pi3d.Mouse(use_x=True)

# Event manager for handling touchscreen events
gesture_mgr=UserGestures()
def ifnauto(action,a,b):
    if len(autoplay)==0:
        action(a,b)
def makeTS():
    try:
        tscr=Touchscreen(touchscreen_id)   
        for touchHandle in tscr.touches:
            touchHandle.on_press = lambda a,b: gesture_mgr.down(a,b)
            touchHandle.on_release = lambda a,b: gesture_mgr.up(a,b)
            touchHandle.on_move = lambda a,b: ifnauto(gesture_mgr.push,a,b)
        tscr.run()
        return tscr
    except Exception as ex:
        print(ex)
ts = makeTS()

######################################
#       Globe Rotation/&c
######################################

def init_zoom():
    if len(autoplay)==0:
        targetZ=globes.findNextFocalLength(cam_z)
        #at 30fps, 45 frames is a second and a half
        autoplay.extend(ZoomInterpolator(45).get_frames(cam_z,targetZ))

######################################
#       Alternate Interface (Options & Torus; Wireless)
######################################
def ambience_changed(alpha):
    global ui_state
    if alpha==0:
        ui_state.show_normal()
    else:
        ui_state.show_closed()
sensor_monitor=sensor_monitor.make_monitor(ambience_changed)
sensor_monitor.start()
torus=pi3d.Torus(radius=4,thickness=2,camera=cam2,name='torus',ringrots=int(partition/2),sides=partition)
textReader=Part3Reader(poetryxml,fontpath,torus,flatsh)
wireless:WirelessToolkit=None
def toggle_evil(stuff:OptionsEvent):
    wireless.cycle_ap(stuff.value)
def handle_click(_event,double_click:bool):
    if double_click:
        init_zoom()
    else:
        option_screen.test_ui_event(_event,double_click)
option_screen=OptionsDialogue(fontpath,toggle_evil,(display.width,display.height),cam_flat,flatsh)
gesture_mgr.add_click_handler(handle_click)
wireless=WirelessToolkit()
wireless.add_status_handler(option_screen.status_message)
wireless.start()

######################################
#       Keys and Mouse
######################################
def appx(x):
    global gesture_mgr
    gesture_mgr.x=x
def appy(x):
    global gesture_mgr
    gesture_mgr.y=x
def appz(x):
    global gesture_mgr
    gesture_mgr.z=x
#a=97;z=122;q=113;arrows u,d,l,r=134,135,136,137
keyActions={97:lambda:appz(-10),122:lambda:appz(10),134:lambda:appy(10),135:lambda:appy(-10),136:lambda:appx(10),137:lambda:appx(-10)}
def doKeys(k):
    global sensor_monitor
    if (k<=0):
        sensor_monitor.setKeyValue(0)
        return
    action=keyActions.get(k)
    if action is not None:
        action()
    if chr(k)=='q':
        sensor_monitor.setKeyValue(1)
    else:
        sensor_monitor.setKeyValue(0)

#TS does mouse emulation. Switch off mouse handling if ts present,
#otherwise events are duplicated.
if ts is None:
    mouse.start()
mouse_state=False
def do_mouse():
    if ts is None:
        global mouse_state
        mdown=mouse.button_status()==9
        mpos=mouse.position()
        touch_evt=Touch(0,mpos[0],display.height-mpos[1])
        if mouse_state and mdown:
            gesture_mgr.push(None,touch_evt)
        elif mouse_state:
            gesture_mgr.up(None,touch_evt)
        elif mdown:
            gesture_mgr.down(None,touch_evt)
        mouse_state=mdown
    
######################################
#       Frame Loop
######################################
while display.loop_running():
    key = keys.read()
    do_mouse()
    masterAlpha=ui_state.calc_frame_alpha()
    if not globes.initialised:
        masterAlpha=0
    gesture_mgr.updateFrame()

    doKeys(key)
    frame_rot,tx_z=gesture_mgr.getFrameMovements()
    d2l=globes.distanceToNextLayer(cam_z)
    weight=1.3 if d2l is None else d2l[1]
    #scale factor for movement.
    #Movement should become more sluggish as the reader approaches a layer's focal point.
    sf:float=-log(weight/1.2)/30
    if len(autoplay)>0:
        #autoplay contains absolute camera positions. Ignore rotation,
        #and negate the scaling factor
        frame_rot=[0,0,0]
        tx_z=autoplay.pop(0)-cam_z
        sf=5 
    
    #x-axis movement on screen means rotation about Y axis, & vice-versa. Invert the context here: 
    globes.doRotation([frame_rot[1]*sf,frame_rot[0]*sf,frame_rot[2]/4],gesture_mgr.getTwistCentroid(),cam_z)
    
    max_z=-globes.min_radius
    cam_tz=tx_z * sf/5
    if (cam_z+cam_tz)<back_wall:
        cam_tz=back_wall-cam_z
    elif (cam_z+cam_tz)>max_z:
        cam_tz=max_z-cam_z
    cam_z+=cam_tz
    cam.offset((0,0,cam_tz))

    globes.doLayersAlpha(masterAlpha,cam_z)
    option_screen.set_alpha(1.0-masterAlpha)
    textReader.set_alpha(1.0-masterAlpha)

    hshader.start_capture()
    textReader.frame()
    globes.draw()
    hshader.end_capture()
    vshader.start_capture()
    hshader.draw({42:0.3,43:0.4,44:1.00,48:0.00})
    vshader.end_capture()
    vshader.draw({42:0.3,43:0.4,44:1.0,48:0.00})
    
    option_screen.show()

    #Escape to quit
    if key==27:
        sensor_monitor.runState=False
        try:
            wireless.shutdown()
        except:
            pass
        mouse.stop()
        keys.close()
        if ts is not None:
            ts.stop()
        sensor_monitor.join()
        display.stop()
        display.destroy()
