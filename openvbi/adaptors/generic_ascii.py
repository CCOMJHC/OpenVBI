##\file generic_ascii.py
#
# Read files of generic ASCII NMEA0183 data into internal format for processing
#
# Copyright 2023 OpenVBI Project.  All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

import pandas
import geopandas
from openvbi.core.observations import RawN0183Obs, Dataset
from openvbi.core.timebase import determine_time_source, generate_timebase
from openvbi.adaptors import Loader

class GenericASCIILoader(Loader):
    def __init__(self, maxelapsed: int, suffix: str) -> None:
        self.maxelapsed = maxelapsed
        self.suffix = suffix

    def suffix(self) -> str:
        return self.suffix
    
    def load(self, filename: str) -> Dataset:
        rtn: Dataset = Dataset()

        # The elapsed time is milliseconds since the start of logging, and can wrap round
        # depending on the length of the counter (on some systems it's 16 bit) and the runtime
        # of the logger.  We look for this by checking whether the next packet has a timestamp
        # that appears to go backwards, and add in another offset of the maxelapsed time.
        elapsed_offset: int = 0
        last_elapsed_mark: int = 0

        with open(filename) as f:
            for line in f:
                elapsed, message = line.split(' ')
                elapsed = int(elapsed)
                if elapsed < last_elapsed_mark:
                    elapsed_offset = elapsed_offset + self.maxelapsed
                last_elapsed_mark = elapsed
                obs = RawN0183Obs(elapsed + elapsed_offset, message)
                rtn.packets.append(obs)
                rtn.stats.Observed(obs.Name())
        rtn.timesrc = determine_time_source(rtn.stats)
        rtn.timebase = generate_timebase(rtn.packets, rtn.timesrc)
        rtn.meta.setIdentifiers('NOTSET', 'Generic ASCII Inputs', '1.0')
        return rtn

class PreparsedASCIILoader(Loader):
    def suffix(self) -> str:
        return '.csv'
    
    def load(self, filename: str) -> Dataset:
        data = Dataset()
        depths = pandas.read_csv(filename)
        # Translate from "Epoch,Longitude,Latitude,Depth" as input columns, to the standard set
        depths = depths.rename(columns={'Epoch': 't', 'Longitude': 'lon', 'Latitude': 'lat', 'Depth': 'z'})
        data.depths = geopandas.GeoDataFrame(depths, geometry=geopandas.points_from_xy(depths['lon'], depths['lat']), crs='EPSG:4326')
        return data
