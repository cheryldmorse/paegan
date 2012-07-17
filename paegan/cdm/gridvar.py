import numpy as np
import netCDF4
from paegan.utils.asagreatcircle import AsaGreatCircle
from paegan.transport.location4d import Location4D

class Gridobj:
    def __init__(self, nc, xname=None, yname=None,
        xunits=None, yunits=None, projected=False, **kwargs):
        self._projected = projected
        if type(nc) is str:
            nc = netCDF4.Dataset(nc)
        
        self._nc = nc
        self._xname = xname
        self._yname = yname
        self._ndim = self._nc.variables[self._xname].ndim
        
        if self._xname != None:
            self._x_nc = self._nc.variables[self._xname]
            self._xarray = np.asarray(self._x_nc[:])
            if self.xmax <= 360 and self.xmin >= 0:
                self._xarray[np.where(self._xarray > 180)] = \
                    self._xarray[np.where(self._xarray > 180)] - 360
            
        else:
            self._xarray = np.asarray((),)
        if self._yname !=None:
            self._y_nc = self._nc.variables[self._yname]
            self._yarray = np.asarray(self._y_nc[:])
        else:
            self._yarray = np.asarray((),)

    
    def get_xbool_from_bbox(self, bbox):
        return np.logical_and(self._xarray<=bbox[2],                
                              self._xarray>=bbox[0])
        
    def get_ybool_from_bbox(self, bbox):
        return np.logical_and(self._yarray<=bbox[3],                
                              self._yarray>=bbox[1])
        
    def getydata(self):
        pass
        
    def getxdata(self):
        pass
        
    def findx(self):
        pass
        
    def findy(self):
        pass
    
    def get_xmax(self):
        return np.max(np.max(self._xarray))
        
    def get_ymax(self):
        return np.max(np.max(self._yarray))
        
    def get_xmin(self):
        return np.min(np.min(self._xarray))
        
    def get_ymin(self):
        return np.min(np.min(self._yarray))
    
    def get_bbox(self):
        self.bbox = self.xmin, self.ymin, self.xmax, self.ymax
        return self.xmin, self.ymin, self.xmax, self.ymax
            
    def get_projectedbool(self):
        return self._projected
    
    def get_xunits(self):
        try:
            units = self._nc.variables[self._xname].units
        except:
            units = None
        return units
        
    def get_yunits(self):
        try:
            units = self._nc.variables[self._yname].units
        except:
            units = None
        return units
        
    def bbox_to_wkt(self):
        pass
    
    def near_xy(self, **kwargs):
        point = kwargs.get("point", None)
        if point == None:
            lat = kwargs.get("lat", None)
            lon = kwargs.get("lon", None)
            point = Location4D(latitude=lat, longitude=lon, depth=0, time=0)
        if self._ndim == 2:
            point1 = np.asarray([point for i in range(self._xarray.flat)])
            point1.shape = self._xarray.shape
            point2 = np.asarray(map(Location4D, latitude=self._yarray,
                         longitude=self._xarray, depth=np.ones_like(self._xarray),
                         time=np.ones_like(self._xarray))) 
        else:
            point1 = np.asarray([point for i in range(self._xarray.size * self._yarray.size)])
            point2 = []
            for x in self._xarray:
                for y in self._yarray:
                    point2.append(Location4D(latitude=x, longitude=y, depth=0, time=0))
            point2 = np.asarray(point2)
            point1.shape, point2.shape = (self._xarray.size,self._yarray.size,),(self._xarray.size,self._yarray.size)
        gc = AsaGreatCircle()
        vec_dist = np.vectorize(gc.great_distance)
        distance = vec_dist( point1, point2 )
        return np.where(distance == np.min(distance))
        
    is_projected = property(get_projectedbool, None)
    xmax = property(get_xmax, None)
    ymax = property(get_ymax, None)
    xmin = property(get_xmin, None)
    ymin = property(get_ymin, None)
    bbox = property(get_bbox, None)
    xunits = property(get_xunits, None)
    yunits = property(get_yunits, None)
    _findy = findy
    _findx = findx
    _getxdata = getxdata
    _getydata = getydata
    
    
