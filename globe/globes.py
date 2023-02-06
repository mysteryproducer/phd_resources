import pi3d, pickle, numpy as np, threading, os.path
from scipy.spatial.transform import Rotation
from math import sin,cos
from WaveGlobe import WaveGlobe

partition=120       #sphere geometry complexity
max_radius=4.5      #radius of largest sphere
water_radius=2.5    #radius of water sphere
layer_gap=0.35      #distance between spheres
sphere_count=5
min_radius=max_radius-sphere_count*layer_gap
root_dir='/home/pi/globe/'
initial_rotation=Rotation.from_quat([0,0,0,1])

class Globes():
    def __init__(self,camera:pi3d.Camera,shader:pi3d.Shader,display:pi3d.Display):
        self.camera=camera
        self.globe1=None
        self.allTextures:list=list()
        self.allLayers:list=list()
        self.globe1 = None
        self.rotation=initial_rotation
        self._no_z_rot=self._makeQuat([0,0,1],0)
        self.globe5=None
        self._display=display
        self.waterworld=None
        self.burbworld=None
        self.initialised=False
        
        bump_shader=pi3d.Shader("uv_bump")
        threading.Thread(target=lambda:self.initialise(camera,shader,bump_shader)).start()
        
    def initialise(self,camera:pi3d.Camera,shader:pi3d.Shader,bump_shader:pi3d.Shader):
        if not os.path.isfile(root_dir+'textures.pkl'):
            for i in range(0,sphere_count):
                tex=pi3d.Texture(root_dir+'layer '+str(i)+'.png',blend=True,free_after_load=True)
                self.allTextures.append(tex)
                print('loaded ' +str(i))
            self.allTextures.append(pi3d.Texture(root_dir+'layer 5.land.png',blend=True,free_after_load=True,automatic_resize=False))
    #        print('loaded land')
            self.allTextures.append(pi3d.Texture(root_dir+'layer 5.water.png',blend=True,free_after_load=True,automatic_resize=False))
    #        print('loaded water')
            with open('textures.pkl', 'wb') as f:
                pickle.dump(self.allTextures, f)
            print ('dumped to file')
        with open(root_dir+'textures.pkl', 'rb') as f:
            self.allTextures = pickle.load(f)

        temp_layers=list()
        for i in range(0,sphere_count):
            lyr_rad=max_radius-i*layer_gap
            lyr=pi3d.Sphere(camera=camera,radius=lyr_rad, slices=partition, sides=partition, name="layer "+str(i))
            temp_layers.append(lyr)
            lyr.set_draw_details(shader,[self.allTextures[i]])
            if i==0:
                self.globe1 = lyr
            else:
                self.globe1.add_child(lyr)
            #lyr.draw()
        self.allLayers=temp_layers
        self.globe5=self.allLayers[-1]
        
        #This sphere is managed separately. This means it doesn't factor into the double-click gestures
        self.waterworld=WaveGlobe(camera=camera,radius=water_radius, slices=partition, sides=partition, name="swan")
        self.waterworld.set_draw_details(bump_shader,[self.allTextures[-1]])
        #self.waterworld.set_fog((0.196,0.788,0.87,0.5),3)
        self.globe1.add_child(self.waterworld)
        self.burbworld=pi3d.Sphere(camera=camera,radius=water_radius, slices=partition, sides=partition, name="burbs")
        self.burbworld.set_draw_details(shader,[self.allTextures[-2]])
        self.globe1.add_child(self.burbworld)

        self.initialised=True
        
    @property
    def min_radius(self):
        return max_radius
    @property
    def max_radius(self):
        return max_radius - sphere_count * layer_gap

    def _makeQuat(self,unitVector,theta) -> Rotation:
        theta=theta*0.5
        c,s=cos(theta),sin(theta)
        return Rotation.from_quat(np.array([s*unitVector[0],s*unitVector[1],s*unitVector[2],c]))

    #rotation as 3-tuple, around (x,y,z) axes
    #z-centroid is (x,y)
    def doRotation(self,rot:tuple,z_centroid:tuple,cam_z:float) -> None:
        if not self.initialised:
             return
        rot=np.radians(rot)
        rx=self._makeQuat([1.0,0.0,0.0],rot[0])
        ry=self._makeQuat([0.0,1.0,0.0],rot[1])
        rz=self._no_z_rot
        if rot[2]!=0 and z_centroid is not None:
            #z-axis rotation should be at multitouch centroid. How the screen position
            #in pixels maps to coordinate space is guesswork:
            #(x,y)=twist distance from screen centre * cam distance from (0,0,0) * scale factor
            sfx=0.4
            sfy=0.2
            qzx=(z_centroid[0]-self._display.width/2) * (-cam_z/max_radius) / self._display.width*sfx
            qzy=(self._display.height/2-z_centroid[1]) * (-cam_z/max_radius) / self._display.height*sfy
            #scipy will normalise this vector
            zaxis=[qzx,qzy,1]
            rz=self._makeQuat(zaxis,rot[2]*2)
        #rotate about axes from the global perspective; in quaternions
        #this is old rotation first (switch terms for object-local)
        self.rotation=self.rotation*rz*rx*ry

    def distanceToNextLayer(self,cam_z:float) -> tuple:
        for lyr in self.allLayers:
            d2l=self.distanceToLayer(lyr,cam_z)
            if d2l>1.5:
                return (lyr,d2l)
        return None

    def distanceToLayer(self,layer:pi3d.Sphere,cam_z:float) -> float:
        return layer.z()-cam_z-layer.radius

    def doLayersAlpha(self,master_alpha:float,cam_z:float) -> None:
        if self.initialised:
            for layer in self.allLayers:
                self.doLayerAlpha(layer,master_alpha,cam_z)
            self.waterworld.set_alpha(master_alpha)
            self.doLayerAlpha(self.burbworld,master_alpha,cam_z)
        
    def doLayerAlpha(self,layer:pi3d.Sphere,master_alpha:float,cam_z:float) -> None:
        distance:float=self.distanceToLayer(layer,cam_z)-1.5
        la:float=1.0-(distance*5)**2
        la=max(la,0.2 if distance>0.0 else 0)
        layer.set_alpha(la*master_alpha)

    def findNextFocalLength(self,cam_z:float) -> float:
        if len(self.allLayers)==0:
            return cam_z
        d2l=self.distanceToNextLayer(cam_z)
        if (d2l is None):
            return -self.globe1.radius-1.5
        else:
            targetZ=-d2l[0].radius-1.5
            #correct for rounding error:
            if (targetZ-cam_z)<0.1:
                ix=self.allLayers.index(d2l[0])+1
                ix=0 if ix>=len(self.allLayers) else ix
                targetZ=-self.allLayers[ix].radius-1.5
            return targetZ
        
    def draw(self):
        if not self.initialised:
            return
        mat=self.rotation.as_matrix()
        sphere_matrix=[[mat[0][0],mat[0][1],mat[0][2],0.0],
             [mat[1][0],mat[1][1],mat[1][2],0.0],
             [mat[2][0],mat[2][1],mat[2][2],0.0],
             [0.0,0.0,0.0,1.0]]
        for layer in self.allLayers[1:]:
            if (layer.alpha()>0.1):
                layer.draw()
        self.globe1.draw(next_m=sphere_matrix)
        self.waterworld.draw()
        self.burbworld.draw()

