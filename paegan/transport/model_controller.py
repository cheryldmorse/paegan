import unittest
import time
import matplotlib
import matplotlib.pyplot
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import netCDF4
from datetime import datetime, timedelta
from paegan.transport.models.transport import Transport
from paegan.transport.particles.particle import Particle
from paegan.transport.location4d import Location4D
from paegan.utils.asarandom import AsaRandom
from paegan.transport.shoreline import Shoreline
from paegan.transport.bathymetry import Bathymetry
from shapely.geometry import Point
from shapely.geometry import MultiLineString

class ModelController(object):
    """
        Controls the models
    """
    def __init__(self, **kwargs):

        """ 
            Mandatory named arguments:
            * point (Shapely Point Object) no default
            * depth (meters) default 0
            * start (DateTime Object) none
            * step (seconds) default 3600
            * npart (number of particles) default 1
            * nstep (number of steps) no default
            * models (list object) no default, so far there is a transport model and a behavior model
            point is interchangeable with:
            * latitude (DD) no default
            * longitude (DD) no default
            * depth (meters) default 0
        """

        # Dataset
        self._dataset = None

        # Defaults
        self._use_shoreline = kwargs.pop('use_shoreline', True)
        self._use_bathymetry = kwargs.pop('use_bathymetry', True)
        self._use_seasurface = kwargs.pop('use_seasurface', True)
        self.depth = kwargs.pop('depth', 0)
        self.npart = kwargs.pop('npart', 1)
        self.start = kwargs.pop('start', None)
        self.step = kwargs.pop('step', 3600)
        self.models = kwargs.pop('models', None)
        self._dirty = True
        self._particles = []

        # Inerchangeables
        if "point" in kwargs:
            self.point = kwargs.pop('point')
        elif "latitude" and "longitude" in kwargs:
            self.latitude = kwargs.pop('latitude')
            self.longitude = kwargs.pop('longitude') 
        else:
            raise TypeError("must provide a point geometry object or latitude and longitude")

        # Create shoreline
        if self._use_shoreline == True:
            self._shoreline = Shoreline(point=self.point)

        # Create Bathymetry
        if self.use_bathymetry == True:
            self._bathymetry = Bathymetry(point=self.point)

        # Errors
        if "nstep" in kwargs:
            self._nstep = kwargs.pop('nstep')
        else:
            raise TypeError("must provide the number of timesteps")

    def set_point(self, point):
        self._point = point
        self._dirty = False
    def get_point(self):
        if self._dirty:
            self.point = Point(self._longitude, self._latitude, self._depth)
        return self._point
    point = property(get_point, set_point)

    def set_latitude(self, lat):
        self._latitude = lat
        self._dirty = True
    def get_latitude(self):
        return self._latitude
    latitude = property(get_latitude, set_latitude)

    def set_longitude(self, lon):
        self._longitude = lon
        self._dirty = True
    def get_longitude(self):
        return self._longitude
    longitude = property(get_longitude, set_longitude)

    def set_depth(self, dep):
        self._depth = dep
        self._dirty = True
    def get_depth(self):
        return self._depth
    depth = property(get_depth, set_depth)

    def set_start(self, sta):
        self._start = sta
    def get_start(self):
        return self._start
    start = property(get_start, set_start)

    def set_step(self, ste):
        self._step = ste
    def get_step(self):
        return self._step
    step = property(get_step, set_step)

    def set_nstep(self, nst):
        self._nstep = nst
    def get_nstep(self):
        return self._nstep
    nstep = property(get_nstep, set_nstep)

    def set_use_shoreline(self, sho):
        self._use_shoreline = sho
    def get_use_shoreline(self):
        return self._use_shoreline
    use_shoreline = property(get_use_shoreline, set_use_shoreline)

    def set_use_bathymetry(self, bat):
        self._use_bathymetry = bat
    def get_use_bathymetry(self):
        return self._use_bathymetry
    use_bathymetry = property(get_use_bathymetry, set_use_bathymetry)

    def set_use_seasurface(self, sea):
        self._use_seasurface = sea
    def get_use_seasurface(self):
        return self._use_seasurface
    use_seasurface = property(get_use_seasurface, set_use_seasurface)

    def set_npart(self, npa):
        self._npart = npa
    def get_npart(self):
        return self._npart
    npart = property(get_npart, set_npart)

    def set_models(self, mod):
        self._models = mod
    def get_models(self):
        return self._models
    models = property(get_models, set_models)

    def set_particles(self, parts):
        self._particles = parts
    def get_particles(self):
        return self._particles
    particles = property(get_particles, set_particles)

    def __str__(self):
        return  " *** ModelController *** " + \
                "\nlatitude: " + str(self.latitude) + \
                "\nlongitude: " + str(self.longitude) + \
                "\ndepth: " + str(self.depth) + \
                "\nstart: " + str(self.start) +\
                "\nstep: " + str(self.step) +\
                "\nnstep: " + str(self.nstep) +\
                "\nnpart: " + str(self.npart) +\
                "\nmodels: " + str(self.models) +\
                "\nuse_bathymetry: " + str(self.use_bathymetry) +\
                "\nuse_shoreline: " + str(self.use_shoreline)

    def boundry_interaction(self, **kwargs):
        """
            Returns a list of Location4D objects
        """

        particle = kwargs.pop('particle')
        starting = kwargs.pop('starting')
        ending = kwargs.pop('ending')

        # bathymetry
        if self.use_bathymetry:
            pt = self._bathymetry.intersect(start_point=starting.point,
                                            end_point=ending.point,
                                            distance=kwargs.get('vertical_distance'),
                                            angle=kwargs.get('vertical_angle'))
            if pt:
                ending.latitude = pt.latitude
                ending.longitude = pt.longitude
                ending.depth = pt.depth

        # shoreline
        if self.use_shoreline:
            intersection_point = self._shoreline.intersect(start_point=starting.point, end_point=ending.point)
            if intersection_point:
                # Set the intersection point
                hitpoint = Location4D(point=intersection_point['point'])
                particle.location = hitpoint
                resulting_point = self._shoreline.react(start_point=starting,
                                                        end_point=ending,
                                                        hit_point=hitpoint,
                                                        feature=intersection_point['feature'],
                                                        distance=kwargs.get('distance'),
                                                        angle=kwargs.get('angle'),
                                                        azimuth=kwargs.get('azimuth'),
                                                        reverse_azimuth=kwargs.get('reverse_azimuth'))
                ending.latitude = resulting_point.latitude
                ending.longitude = resulting_point.longitude
                ending.depth = resulting_point.depth

        # sea-surface
        if self.use_seasurface:
            if ending.depth > 0:
                ending.depth = 0

        particle.location = ending

    def generate_map(self):
        fig = matplotlib.pyplot.figure() # call a blank figure
        ax = fig.gca(projection='3d') # line with points

        tracks = []

        #for x in range(len(arr)):
        for particle in self.particles:
            tracks.append(particle.linestring())
            p_proj_lats = map(lambda la: la.latitude, particle.locations)
            p_proj_lons = map(lambda lo: lo.longitude, particle.locations)
            p_proj_depths = map(lambda dp: dp.depth, particle.locations)

            ax.plot(p_proj_lons, p_proj_lats, p_proj_depths, marker='o', c='red') # particles

        #add shoreline
        tracks = MultiLineString(tracks)
        midpoint = tracks.centroid

        bbox = tracks.bounds
        visual_bbox = tracks.buffer(1).bounds

        max_distance = max(abs(bbox[0] - bbox[2]), abs(bbox[1] - bbox[3])) + 0.25

        coast_line = Shoreline(point=midpoint, spatialbuffer=max_distance).linestring

        c_lons, c_lats = coast_line.xy
        c_lons = np.array(c_lons)
        c_lats = np.array(c_lats)
        c_lons = np.where((c_lons >= visual_bbox[0]) & (c_lons <= visual_bbox[2]), c_lons, np.nan)
        c_lats = np.where((c_lats >= visual_bbox[1]) & (c_lats <= visual_bbox[3]), c_lats, np.nan)

        #add bathymetry
        nc1 = netCDF4.Dataset('/home/dev/Development/paegan/paegan/resources/bathymetry/ETOPO1_Bed_g_gmt4.grd')
        x = nc1.variables['x']
        y = nc1.variables['y']

        x_indexes = np.where((x[:] >= visual_bbox[0]) & (x[:] <= visual_bbox[2]))[0]
        y_indexes = np.where((y[:] >= visual_bbox[1]) & (y[:] <= visual_bbox[3]))[0]

        x_min = x_indexes[0] 
        x_max = x_indexes[-1]
        y_min = y_indexes[0]
        y_max = y_indexes[-1]

        lons = x[x_min:x_max]
        lats = y[y_min:y_max]
        bath = nc1.variables['z'][y_min:y_max,x_min:x_max]

        x_grid, y_grid = np.meshgrid(lons, lats)

        mpl_extent = matplotlib.transforms.Bbox.from_extents(visual_bbox[0],visual_bbox[1],visual_bbox[2],visual_bbox[3])
        
        ax.plot_surface(x_grid,y_grid,bath, rstride=5, cstride=5) # bathymetry
        ax.plot(c_lons, c_lats, clip_box=mpl_extent, clip_on=True) # shoreline
        ax.set_xlim3d(visual_bbox[0],visual_bbox[2])
        ax.set_ylim3d(visual_bbox[1],visual_bbox[3])
        ax.set_zmargin(0.1)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_zlabel('Depth (m)')
        matplotlib.pyplot.show()

    def run(self):
        ######################################################
        u=[] # random u,v,z generator
        v=[]
        z=[]
        for w in xrange(0,self._nstep):
            z.append(0)
            u.append(abs(AsaRandom.random()))
            v.append(abs(AsaRandom.random()))
        #######################################################
        times = range(0,(self._step*self._nstep)+1,self._step)
        start_lat = self._latitude
        start_lon = self._longitude
        start_depth = self._depth
        start_time = self._start

        if start_time == None:
            raise TypeError("must provide a start time to run the models")

        startloc = Location4D(latitude=start_lat, longitude=start_lon, depth=start_depth, time=start_time)

        # Initialize the particles
        for x in xrange(0, self._npart):
            p = Particle()
            p.location = startloc
            self.particles.append(p)

        # loop over timesteps
        for i in xrange(0, len(times)-1): 
            try:
                modelTimestep = times[i+1] - times[i]
                calculatedTime = times[i+1]
            except:
                modelTimestep = times[i] - times[i-1]
                calculatedTime = times[i] + modelTimestep
                
            newtime = start_time + timedelta(seconds=calculatedTime)
            newloc = None
            
            # loop over particles
            for part in self.particles:
                # loop over models - sort these in the order you want them to run
                for model in self._models:
                    movement = model.move(part.location, u[i], v[i], z[i], modelTimestep)
                    newloc = Location4D(latitude=movement['latitude'], longitude=movement['longitude'], depth=movement['depth'], time=newtime)
                    if newloc:
                        self.boundry_interaction(particle=part, starting=p.location, ending=newloc, distance=movement['distance'], angle=movement['angle'], azimuth=movement['azimuth'], reverse_azimuth=movement['reverse_azimuth'], vertical_distance=movement['vertical_distance'], vertical_angle=movement['vertical_angle'])