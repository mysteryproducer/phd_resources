import pi3d, wifi_process_manager as wifi
from pi3d.util.Font import Font
from pi3d.util.Gui import Gui, Radio, Button

root_dir='/home/pi/globe/'

class EnableButton(Button):
    def __init__(self,gui,imgs,x,y,callback=None,label=None,label_pos='left',shortcut=None,enabled=True):
        self._enabled=enabled
        if len(imgs)==3:
            imgs.append(imgs[2])
        #todo: a general solution should account for 1 or 2 images
        super(EnableButton,self).__init__(gui,imgs,x,y,callback=callback,label=label,label_pos=label_pos,shortcut=shortcut)
    def get_enabled(self):
        return self._enabled
    def set_enabled(self,value:bool):
        self._enabled=value
    def draw(self):
        #effectively: enabled << 1 & clicked
        index1=0 if self._enabled else 2
        index2=1 if self.clicked else 0
#        print(str(index1) + ", " + str(index2))
        self.shapes[index1+index2].draw()
        if self.labelobj:
            self.labelobj.draw()
    def _click(self, *args):
        if self._enabled:
            super()._click(args)


class OptionsDialogue:
    def __init__(self,font_file:str,evil_callback,screen_dim:tuple,cam:pi3d.Camera,shader:pi3d.Shader):
        self._font:Font=Font(font_file,font_size=36)
        #save some refs for displaying the status message
        self._fontpath=font_file
        self._cam=cam
        self._status_strings=dict()
        self._current_status=None 
        self._shader=shader

        #one gui instance has the checkbox
        self._gui:Gui=Gui(self._font,show_pointer=False)
#        self._btn:Radio=Radio(self._gui,200,100,label='evil mode',callback=evil_callback)
        btn_imgs=[root_dir+'img/cb_off_en.png',root_dir+'img/cb_on_en.png',root_dir+'img/cb_off_dis.png',root_dir+'img/cb_on_dis.png']
        self._btn:EnableButton=EnableButton(self._gui,btn_imgs,280,120,label='Evil Mode',callback=self._raise_evil)
        self._canvas:pi3d.ImageSprite=pi3d.ImageSprite(root_dir+'img/midgrey.png',shader,w=300,h=200,z=5.1,x=200,y=100,camera=cam)
#        self._canvases:dict={'':self._canvas}

        #the other instance has the button which toggles the 1st interface
        #did I mean enable_ui when I named this, or ennui?
        self._en_ui:Gui=Gui(self._font,show_pointer=False)
        self._en_btn:Button=Button(self._en_ui,[root_dir+'img/options.png',root_dir+'img/close.png'],300,200)
        #if alpha<1, don't display anything or respond to input
        self._alpha:float=0.0
        self._evil_cb=evil_callback
        self._screensize=screen_dim

        #init the status message stuff. This will assign into self._current_status, 
        #so it'll always be ready to .draw()
        self.status_message((wifi.STATUS_STARTING,wifi.status_txt[wifi.STATUS_STARTING]))

    def set_alpha(self,value:float) -> None:
        self._alpha=value
    def test_ui_event(self,event,dblclick:bool):
        if not dblclick:
            self.test_click(event.x-self._screensize[0]/2,self._screensize[1]/2-event.y)
            #self.test_click(event.x,self._screensize[1]-event.y)
    def test_click(self,x,y):
        if self._alpha>=0.99:
            self._btn.check(x,y)
            self._en_btn.check(x,y)
        
    def show(self):
        if self._alpha<0.99:
            return
        if self._en_btn.clicked:
            self._canvas.draw()
            self._gui.draw(0,0)
            self._current_status.sprite.draw(0,0)
        self._en_ui.draw(100,-100)
    
    def _raise_evil(self,event):
        if self._evil_cb is not None:
            self._evil_cb(OptionsEvent('evil',self._btn.clicked))
    
    def status_message(self,status:tuple):
        message=status[1]
        str_tex=self._status_strings.get(message)
        if str_tex is None:
            msg="Wireless Status: " + message
            str_tex=pi3d.FixedString(self._fontpath,msg,
                         color=(255,255,255,255),
                         camera=self._cam,font_size=18,
                         shader=self._shader)
            str_tex.sprite.position(200,38,0)
        self._current_status=str_tex
        self._btn.set_enabled((status[0]&1)!=1)

#This solution implemented when the one above didn't work. Seems a valid alternative.
    def drawStatus(self,message:str):
        background=self._canvases.get(message)
        if background is None:
            msg="Wireless Status: " + message
            canvas:Image=Image.new('RGBA',[300,200],'#7F7F7FFF')
            draw=ImageDraw.Draw(canvas)
            draw.text((10,180),msg,font=self._font,fill='#FFFFFFFF')
            background:pi3d.ImageSprite=pi3d.ImageSprite(canvas,shader,w=300,h=200,z=5.1,x=200,y=100,camera=cam)
            self._canvases[message]=background
        self._canvas=background
    
class OptionsEvent:
    def __init__(self,option:str,value):
        self.option:str=option
        self.value=value
        