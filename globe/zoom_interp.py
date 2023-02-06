import numpy
from scipy.interpolate import interp1d

class LinearInterpolator:
    def __init__(self,frames):
        self._frames=frames
    def get_frames(self,start_coord,end_coord):
        increment:float=(end_coord-start_coord)/self._frames
        return numpy.arange(start_coord,end_coord,increment)
    
class ZoomInterpolator:
    def __init__(self,frames):
        self._iframes=1.0/frames
    def get_frames(self,i_val,e_val) -> list:
        x=[-0.01,0.0,0.26,0.75,1.0,1.01]
        diff=e_val-i_val
        y=[i_val,i_val,i_val+diff*0.1,e_val-diff*0.1,e_val,e_val]
        time=numpy.arange(0,1+self._iframes,self._iframes)
        interp=interp1d(x,y,kind='cubic')
        return interp(time)
