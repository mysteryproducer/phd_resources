import math, numpy as np, time
from ft5406 import Touch
from threading import Lock

#time (in seconds) between clicks to count as double
dbl_click_timeout=0.3
#number of pixels the pointer can move (in both x,y directions) and still count as a click.
click_allowance=3.0

def car2pol(x,y) -> float:
    hyp=np.sqrt(x**2+y**2)
    theta=np.arctan2(y,x)
    return hyp, theta

def diff_scrub_flip(theta,last_theta) -> float:
    res=theta-last_theta
    if abs(res)>np.pi:
#    if np.sign(theta)+np.sign(last_theta)==0 and res>np.pi:
        if theta<0: theta+=2*np.pi
        if last_theta<0: last_theta+=2*np.pi
        res=theta-last_theta
    return res

class UserGestures:
    
    def __init__(self):
        self._events:list=[None,None,None,None,None,None,None,None,None,None]
        self._active_slots:list=list()
        self._velocity:list=[0,0,0,0]
        self._last:list=[0,0,0,0]
        self.x:float=0
        self.y:float=0
        self.z:float=0
        self._twist:float=0
        self._lock:Lock=Lock()
        self._twistCentroid:tuple=(0,0)
        self._clickstate:tuple=(0,0,0)
        self._t_last_click:float=0
        self._click_handler=list()

    def getCentroid(self) -> tuple:
        x=0.0
        y=0.0
        count=0.0
        for i in self._active_slots:
            x+=self._events[i].x
            y+=self._events[i].y
            count+=1
        return None if count==0 else x/count,y/count

    #Click handler should take 2 args: an event descriptor with .x and .y; and a bool, true for for double click
    def add_click_handler(self,callback):
        self._click_handler.append(callback)
    def click_match(self,tsEvent:Touch) -> bool:
        if self._clickstate[0]==tsEvent.slot:
            #allow some wiggle room in the click detection
            close_to=lambda a,b: abs(a-b)<click_allowance
            return close_to(self._clickstate[1],tsEvent.x) and close_to(self._clickstate[2],tsEvent.y)
        return False
    
    def down(self,event,tsEvent:Touch) -> None:
        self._lock.acquire()
        try:
            self._active_slots.append(tsEvent.slot)
            self._events[tsEvent.slot]=tsEvent
            if len(self._active_slots)==1:
                self._clickstate=(tsEvent.slot,tsEvent.x,tsEvent.y)
                self._last[0]=tsEvent.x
                self._last[1]=tsEvent.y
            else:
                self._clickstate=(-1,0,0)
                self._twistCentroid=self.getCentroid()
                self._last[0],self._last[1]=self._twistCentroid
                self._last[2],self._last[3]=self.toPolar(self._events[self._active_slots[0]],tsEvent)
        finally:
            self._lock.release()
    
    def up(self,event,tsEvent:Touch) -> None:
        self._lock.acquire()
        try:
            self._active_slots.remove(tsEvent.slot)
            self._events[tsEvent.slot]=None
            if len(self._active_slots)==1:
                self._last[0]=self._events[self._active_slots[0]].x
                self._last[1]=self._events[self._active_slots[0]].y
                self._twistCentroid=None
            elif len(self._active_slots)>1:
                #rejig state so that remaining index becomes primary 
                self._twistCentroid=self.getCentroid()
                self._last[0],self._last[1]=self._twistCentroid
            elif self.click_match(tsEvent):
                self._twistCentroid=None
                for f in self._click_handler:
                    this_click=time.monotonic()
                    dblclick=(this_click-self._t_last_click)<dbl_click_timeout
                    f(tsEvent,dblclick)
                    self._t_last_click=this_click
        finally:
            self._lock.release()
        
    def push(self,event,tsEvent:Touch) -> None:
        self._lock.acquire()
        try:
            if not self.click_match(tsEvent):
                self._clickstate=(-1,0,0)
            self._events[tsEvent.slot]=tsEvent
        finally:
            self._lock.release()
        
    def getFrameMovements(self) -> tuple:
        return [self.x, self.y, self._twist], self.z
        
    def getX(self) -> float:
        return self.x
    
    def getY(self) -> float:
        return self.y
    
    def getZ(self) -> float:
        return self.z
    
    def getTheta(self) -> float:
        return self._twist
    
    def getTwistCentroid(self) -> tuple:
        return self._twistCentroid
    
    def updateFrame(self) -> None:
        self._lock.acquire()
        try:
            if len(self._active_slots)==0:
                self.x=self.smooth(0,None)
                self.y=self.smooth(1,None)
                self.z=self.delta_smooth(2,None)
                self._twist=self.delta_smooth(3,None)
                return
            if len(self._active_slots)>1:
                self._twistCentroid=self.getCentroid()
                distance,angle=self.get_multitouch()
                diff:float=self._last[2]-distance
                diff_theta:float=diff_scrub_flip(angle,self._last[3])
                self._last[2]=distance
                self._last[3]=angle
                self._twist=math.degrees(self.delta_smooth(3,diff_theta))
                if abs(diff_theta)>math.pi/180.0:
                    self.x=self.smooth(0,None)
                    self.y=self.smooth(1,None)
                    self.z=self.delta_smooth(2,None)
                    return
                self.z=self.delta_smooth(2,diff)
            else: 
                self.z=self.delta_smooth(2,0)
                self._twist=self.delta_smooth(3,0)
            scrpt=self.getCentroid()
            self.x=self.smooth(0,scrpt[0])
            self.y=self.smooth(1,scrpt[1])
        finally:
            self._lock.release()

    def delta_smooth(self,i:int,value:float) -> float:
        if value is None:
            self._velocity[i]*=.95
        else:
            self._velocity[i]=self._velocity[i]*0.6 + value * 0.4
        return self._velocity[i]

    def smooth(self,i:int,value:float) -> float:
        if value is None:
            self._velocity[i]*=.95
        else:
            self._velocity[i]=self._velocity[i]*0.6 + (self._last[i]-value) * 0.4
            self._last[i]=value
        if abs(self._velocity[i])<0.01:
            self._velocity[i]=0.0
        return self._velocity[i]

    def toPolar(self,a,b) -> float:
        return car2pol(a.x-b.x,a.y-b.y)
    
    def get_multitouch(self) -> float:
        result=None
        for i in range(0,len(self._active_slots)):
            for j in range(i+1,len(self._active_slots)):
                d,t=self.toPolar(self._events[self._active_slots[i]],self._events[self._active_slots[j]])
                if (result is None or d>result[0]):
                    result=d,t
        return result
