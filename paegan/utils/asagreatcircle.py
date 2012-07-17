import math
from paegan.external.greatcircle import GreatCircle

class AsaGreatCircle(object):

    @classmethod
    def great_circle(self, **kwargs):
        """
            Named arguments:
            distance = distance to traveled
            azimuth = angle, in DECIMAL DEGREES of HEADING from NORTH
            start_point = Location4D object representing the starting point
            rmajor = radius of earth's major axis. default=6378137.0 (WGS84)
            rminor = radius of earth's minor axis. default=6356752.3142 (WGS84)

            Returns a dictionary with:
            'latitude' in decimal degrees
            'longitude' in decimal degrees
            'reverse_azimuth' in decimal degrees

        """

        distance = kwargs.pop('distance')
        azimuth = kwargs.pop('azimuth')
        starting = kwargs.pop('start_point')
        rmajor = kwargs.pop('rmajor', 6378137.0)
        rminor = kwargs.pop('rminor', 6356752.3142)
        f = (rmajor - rminor) / rmajor

        lat_result, lon_result, angle_result = GreatCircle.vinc_pt(f, rmajor, math.radians(starting.latitude), math.radians(starting.longitude), math.radians(azimuth), distance)

        return {'latitude': math.degrees(lat_result), 'longitude': math.degrees(lon_result), 'reverse_azimuth': math.degrees(angle_result)}

    @classmethod
    def great_distance(self, start_point, end_point, **kwargs):
        """
            Named arguments:
            start_point = Location4D obect representing start point
            end_point = Location4D obect representing end point
            rmajor = radius of earth's major axis. default=6378137.0 (WGS84)
            rminor = radius of earth's minor axis. default=6356752.3142 (WGS84)

            Returns a dictionaty with:
            'distance' in meters
            'azimuth' in decimal degrees
            'reverse_azimuth' in decimal degrees

        """

        #start_point = kwargs.pop('start_point')
        #end_point = kwargs.pop('end_point')
        rmajor = kwargs.pop('rmajor', 6378137.0)
        rminor = kwargs.pop('rminor', 6356752.3142)
        f = (rmajor - rminor) / rmajor

        distance, angle, reverse_angle = GreatCircle.vinc_dist(f, rmajor, math.radians(start_point.latitude), math.radians(start_point.longitude), math.radians(end_point.latitude), math.radians(end_point.longitude))

        return {'distance': distance, 'azimuth': math.degrees(angle), 'reverse_azimuth': math.degrees(reverse_angle)}
