"""This module provides functionality to read binary GSHHS datasets."""

import urllib.request
import shutil
import zipfile
import os

import numpy as np

# Version, filename, and URL info for the file containing GSHHS data.
_GSHHS_VERSION = "2.3.7"
_GSHHS_ZIPFILE = "gshhg-bin-{}.zip".format(_GSHHS_VERSION)
_GSHHS_URL = "https://www.ngdc.noaa.gov/mgg/shorelines/data/gshhg/latest/{}".format(_GSHHS_ZIPFILE)

# GSHHS dataset polygon header.
gshhs_poly_header = np.dtype([
        ('id'       , '>i4'),
        ('n'        , '>i4'),
        ('flag'     , '>i4'),
        ('west'     , '>i4'),
        ('east'     , '>i4'),
        ('south'    , '>i4'),
        ('north'    , '>i4'),
        ('area'     , '>i4'),
        ('area_full', '>i4'),
        ('container', '>i4'),
        ('ancestor' , '>i4')
    ])

# GSHHS dataset point, in micro-degrees.
gshhs_point = np.dtype([
        ('longitude', '>i4'),
        ('latitude' , '>i4')
    ])


class GSHHS_Polygon:
    """Represents a single GSHHS polygon."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, poly_header, poly_points):
        if poly_header["n"] != len(poly_points):
            raise RuntimeError("value n is unexpected")
        self.id_ = int(poly_header["id"])
        self.flag = int(poly_header["flag"])
        self.west = int(poly_header["west"])
        self.east = int(poly_header["east"])
        self.south = int(poly_header["south"])
        self.north = int(poly_header["north"])
        self.area = int(poly_header["area"])
        self.area_full = int(poly_header["area_full"])
        self.container = int(poly_header["container"])
        self.ancestor = int(poly_header["ancestor"])
        self.points = poly_points

    @property
    def level(self):
        """Return 'level' field of flags."""
        return self.flag & 255

    @property
    def version(self):
        """Return 'version' field of flags."""
        return (self.flag >> 8) & 255

    @property
    def greenwich(self):
        """Return 'greenwich crossing' field of flags."""
        return (self.flag >> 16) & 1

    @property
    def source(self):
        """Return 'source' field of flags."""
        return (self.flag >> 24) & 1

    @property
    def river(self):
        """Return 'river' field of flags."""
        return (self.flag >> 25) & 1


def read_gshhs_polygons(gshhs_filename, polygon_filter_func=None):
    """Read binary GSHHS data directly from the GSHHS zip file."""

    polygons = []
    with zipfile.ZipFile(_GSHHS_ZIPFILE, 'r') as gshhs_zip, gshhs_zip.open(gshhs_filename, 'r') as fi:
        gshhs_binary_polygon_data = fi.read()

    offset = 0
    while offset != len(gshhs_binary_polygon_data):

        poly_header = np.frombuffer(gshhs_binary_polygon_data, dtype=gshhs_poly_header, count=1, offset=offset)
        offset += gshhs_poly_header.itemsize

        poly_header = poly_header[0]

        num_points = poly_header["n"]

        poly_points = np.frombuffer(gshhs_binary_polygon_data, dtype=gshhs_point, count=num_points, offset=offset)
        offset += num_points * gshhs_point.itemsize

        polygon = GSHHS_Polygon(poly_header, poly_points)

        if polygon_filter_func is None or polygon_filter_func(polygon):
            polygons.append(polygon)

    return polygons


def ensure_gshhs_zipfile_is_available():
    """Ensure the GSHHS zipfile is locally available.

    This function downloads the zip-file if necessary (after getting the user's permission).

    Raises:
        RuntimeError: the file is not available, and we didn't get permission to download it; or
           downloading the file failed.
    """

    if not os.path.exists(_GSHHS_ZIPFILE):

        print("To run this program, we must download a large (118 MB) file:")
        print()
        print("    {!r}".format(_GSHHS_URL))
        print()
        print("This file contains the GSHHS dataset, a vector-based representation of")
        print("  Earth's coastlines, rivers, and borders, in 5 resolution levels.")
        print()
        response = input("Okay to proceed with download (Y/N)? ")
        print()
        if response.lower() not in ("y", "yes"):
            raise RuntimeError("Download of {!r} not allowed by user.".format(_GSHHS_URL))

        print("Downloading {!r} (this may take a few minutes) ...".format(_GSHHS_ZIPFILE))
        with urllib.request.urlopen(_GSHHS_URL) as response, open(_GSHHS_ZIPFILE, 'wb') as fo:
            shutil.copyfileobj(response, fo)
