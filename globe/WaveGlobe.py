import pi3d, numpy, math
from scipy.interpolate import interp1d

class WaveGlobe(pi3d.Sphere):
    def __init__(self, camera=None, light=None,radius=1, slices=12, sides=12, hemi=0.0, name="",
               x=0.0, y=0.0, z=0.0, rx=0.0, ry=0.0, rz=0.0, sx=1.0, sy=1.0, sz=1.0, cx=0.0, cy=0.0, cz=0.0, invert=False):
        self.counter:int=0
        self.positions=[(0,0),(0,0.1),(0.1,0.1),(0.1,0)]
        super().__init__(camera=camera,light=light,radius=radius,slices=slices,sides=sides,hemi=hemi,name=name,invert=invert,
               x=x, y=y, z=z, rx=rx, ry=ry, rz=rz, sx=sx, sy=sy, sz=sz, cx=cx, cy=cy, cz=cz)
    def set_draw_details(self, shader, textures, ntiles = 0.0, shiny = 0.0,umult=1.0, vmult=1.0, bump_factor=1.0):
        super().set_draw_details(shader=shader,textures=textures,ntiles=ntiles,shiny=shiny,umult=umult,vmult=vmult,bump_factor=bump_factor)
    def draw(self, shader=None, txtrs=None, ntl=None, shny=None, camera=None, next_m=None, light_camera=None):
        self.counter+=1
        si=math.sin(self.counter*0.01)*0.008
        self.set_offset((si,si))
        super().draw(shader=shader,txtrs=txtrs,ntl=ntl,shny=shny,camera=camera,next_m=next_m,light_camera=light_camera)
