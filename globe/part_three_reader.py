import xml.etree.ElementTree as ET
import pi3d, random
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from scipy.spatial.transform import Rotation
from math import cos, sin

nt={'zero':'http://arts.uwa.edu.au/els/zeroday'}
ROT_FRAME_COUNT=100

class Part3Reader:
    def __init__(self,filename:str,fontfile:str,shape:pi3d.Shape,shader:pi3d.Shader,bgcolour=0,fgcolour='#FFFFFFFF'):
        self._fgcolour=fgcolour
        self._bgcolour=bgcolour
        self._shape=shape
        self._shader=shader
        self._rotation=Rotation.from_quat([0,0,0,1])
        self._momentum=[0.0,0.0,0.0]
        self._frame_counter=0
        
        self._index:float=-0.5
        self._increment:float=0.005
        self._alpha:float=0

        self._font=ImageFont.truetype(fontfile,size=32)
        self._lines:list=self.readLines(filename)
        self._lineIndex:int=0
        self._buffer:np.ndarray=self.drawLine(self._lines[self._lineIndex])
        self._texture:pi3d.Texture=pi3d.Texture(self._buffer)

    @property
    def texture(self):
        return self._texture
    @property
    def offset(self):
        return self._index
    @property
    def shape(self) -> pi3d.Shape:
        return self._shape
    @property
    def shader(self) -> pi3d.Shader:
        return self._shader
    def set_alpha(self,value:float) -> None:
        self._alpha=value
        self._shape.set_alpha(value)

    def drawLine(self,line:str) -> np.ndarray:
        width,height=self._font.getsize(line)
        canvas:Image=Image.new('RGBA',[width+400,100],self._bgcolour)
        draw=ImageDraw.Draw(canvas)
        offset=(200,(100-height)/2)
        draw.text(offset,line,font=self._font,fill=self._fgcolour)
        return np.array(canvas)

    def makeQuat(self,unitVector,theta):
        c,s=cos(theta*0.5),sin(theta*0.5)
        return Rotation.from_quat(np.array([s*unitVector[0],s*unitVector[1],s*unitVector[2],c]))

    def rotate_shape(self):
        rot=self._momentum
        rx=self.makeQuat([1.0,0.0,0.0],rot[0])
        ry=self.makeQuat([0.0,1.0,0.0],rot[1])
        rz=self.makeQuat([0.0,0.0,1.0],rot[2])
        self._rotation=self._rotation*rz*rx*ry

    def frame(self) -> None:
        self._frame_counter+=1
        if (self._frame_counter % ROT_FRAME_COUNT)==0:
            index=int((self._frame_counter/ROT_FRAME_COUNT)%3)
            self._momentum[index]=(random.random()-0.5)/10
        self.rotate_shape()
        mt=self._rotation.as_matrix()
        matrix=[[mt[0][0],mt[0][1],mt[0][2],0],[mt[1][0],mt[1][1],mt[1][2],0],[mt[2][0],mt[2][1],mt[2][2],0],[0,0,0,1]]
        if self._alpha<0.01:
            return
        if self._index>=0.5:
            self._lineIndex=(self._lineIndex+1)%len(self._lines)
            self._buffer:np.ndarray=self.drawLine(self._lines[self._lineIndex])
            self._texture:pi3d.Texture=pi3d.Texture(self._buffer)
            self._index=-0.5#self._increment
        self._index+=self._increment
        self.shape.set_offset((self._index,0.0))
        self.shape.draw(self.shader,[self.texture],next_m=matrix)

    def readLines(self,filename:str) -> list:
        xmldoc:ET.ElementTree=ET.parse(filename)
        poems=xmldoc.getroot().findall('.//zero:poem',nt)
        result:list=list()
        for poem in poems:
            result.append(poem.attrib['title'])
            lines=poem.findall('.//zero:line',nt)
            for line in lines:
                result.append(line.text)
        return result

    def make_quat(self,unitVector,theta:float):
        theta=theta/2
        s=sin(theta)
        return Rotation.from_quat(np.array([s*unitVector[0],s*unitVector[1],s*unitVector[2],cos(theta)]))

    def increment_rotation(self,rot):
        np.radians(rot)
        rx=self.make_quat([1.0,0.0,0.0],rot[0])
        ry=self.make_quat([0.0,1.0,0.0],rot[1])
        rz=self.make_quat([0.0,0.0,1.0],rot[2])
        self._rotation=self._rotation*rz*rx*ry
