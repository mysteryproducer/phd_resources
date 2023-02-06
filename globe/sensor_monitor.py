from PiicoDev_VEML6030 import PiicoDev_VEML6030
from PiicoDev_VL53L1X import PiicoDev_VL53L1X
import threading
from time import sleep

#Abstract class for monitoring sensors. Runs as a thread.
#Takes an event handler (alpha_delegate in ctor) to notify on change
class SensorMonitor(threading.Thread):
    def __init__(self,thread_name,alpha_delegate):
        super().__init__(name=thread_name)
        self._set_alpha=alpha_delegate
        self.runState=True
        self._sleep_t=0.2
        self._state=0.0
    def run(self):
        while self.runState:
            try:
                sleep(self._sleep_t)
                newState=self._get_target()
                if newState!=self._state:
                    self._set_alpha(newState)
                    self._state=newState
            except Exception as e:
                #pass
                print(e)
    #Override in implementation. Gets the sensor value.
    def _get_target(self) -> float:
        return 0.0
    #This allows keyboard input as a separate mechanism. Off by default
    def setKeyValue(self,v) -> None:
        pass

def make_monitor(alpha_delegate) -> SensorMonitor:
    try:
        return MFLidarMonitor(alpha_delegate)
    except Exception as e:
        print(e)
    try:
        return LightMonitor(alpha_delegate)
    except Exception as e:
        print(e)
    return KeyboardSensorMonitor(alpha_delegate)

#For running in VM:
class KeyboardSensorMonitor(SensorMonitor):
    def __init__(self,alpha_delegate):
        super().__init__("Fake Sensor Monitor",alpha_delegate)
        self._temp=0.0
        
    def setKeyValue(self,v):
        self._temp=1.0 if v>0 else 0.0

    def _get_target(self):
        return self._temp

#The distance sensor is easy to implement:
class MFLidarMonitor(SensorMonitor):
    def __init__(self,alpha_delegate):
        super().__init__("LIDAR Monitor",alpha_delegate)
        self._sensor=PiicoDev_VL53L1X()
    def _get_target(self):
        distance=self._sensor.read()
        return 1.0 if distance<30 else 0.0

#The ambient light monitor's performance is very variable depending on indoor/outdoor use.
#Some of the commented code below was working towards a self-adpative routine.
#Ultimately, a good solution would require quite a bit of stastical analysis.
class LightMonitor(SensorMonitor):
    def __init__(self,alpha_delegate):
        super().__init__("Ambient Light Monitor",alpha_delegate)
        self._sensor=PiicoDev_VEML6030()
        self._uthresh=50.0
        self._lthresh=10.0
        self._minmax=[1000.0,0.0]
        self._rthresh=self._uthresh-self._lthresh
    
    def updateSensBand(self,lvl:float):
        pass
#        self._minmax[0]=min(self._minmax[0],lvl)
#        self._minmax[1]=max(self._minmax[1],lvl)
#        diff=self._minmax[1]-self._minmax[0]
#        if diff>0:
#            self._uthresh=min(50,self._minmax[1]-diff*0.3)
#            self._lthresh=max(10,self._minmax[0]+diff*0.3)
#            self._rthresh=self._uthresh-self._lthresh
    
    def getTargetState(self,level):
        distFromLowerBound=max(level-self._lthresh,0)
        partRange=max(0,min(self._rthresh,self._rthresh-distFromLowerBound))
        return partRange/self._rthresh
    
    def _get_target(self):
        level=self._sensor.read()
        self.updateSensBand(level)
        return self.getTargetState(level)
        
