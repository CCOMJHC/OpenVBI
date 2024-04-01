##\file __init__.py
#
# Waterlevel corrections using NOAA methods and APIs
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

from abc import abstractmethod
import geopandas
import pandas
import numpy as np
import datetime as dt
import requests
from openvbi.corrections.waterlevel import Waterlevel
from openvbi.core.interpolation import InterpTable

def get_noaa_station(stationName: str, startTime: float, endTime: float) -> pandas.DataFrame:
    base_url = "https://tidesandcurrents.noaa.gov/api/datagetter"
    params = {
        "begin_date": dt.datetime.utcfromtimestamp(startTime).strftime('%Y%m%d %H:%M'),
        "end_date": dt.datetime.utcfromtimestamp(endTime).strftime('%Y%m%d %H:%M'),
        "station": stationName,
        "product": "predictions",
        "datum": "MLLW",
        "time_zone": "gmt",
        "units": "metric",
        "application": "OpenVBI",
        "format": "json"
    }

    request_url = requests.Request('GET', base_url, params=params).prepare().url
    response = requests.get(request_url)
    data = response.json()

    if 'predictions' in data:
        waterlevels = pandas.json_normalize(data['predictions'])
        if 't' in waterlevels and 'v' in waterlevels:
            waterlevels['v'] = waterlevels['v'].astype(float)
            waterlevels['t'] = pandas.to_datetime(waterlevels['t'])
    elif 'data' in data:
        waterlevels = pandas.json_normalize(data['data'])
        if 't' in waterlevels and 'v' in waterlevels:
            waterlevels['v'] = pandas.to_numeric(waterlevels['v'], errors='coerce')
            waterlevels['t'] = pandas.to_datetime(waterlevels['t'], errors='coerce')
        else:
            print(f"Warning: Missing 't' or 'v' column in response for station {stationName}.")
            waterlevels = None
    else:
        print(f"Warning: No 'predictions' in response for station {stationName}.")
        waterlevels = None
    return waterlevels

class SingleStation(Waterlevel):
    def __init__(self, stationName: str) -> None:
        self._stationID = stationName
        super().__init__()

    def preload(self, observations: geopandas.GeoDataFrame) -> None:
        startTime = observations['t'].min()
        endTime = observations['t'].max()
        raw_levels = get_noaa_station(self._stationID, startTime, endTime)
        if raw_levels is None:
            print(f'Error: station failed to resolve waterlevels for time range [{startTime.isoformat()}, {endTime.isoformat()}].')
            self._corrector = None
        else:
            self._corrector = InterpTable(['dz',])
            for n in range(len(raw_levels)):
                self._corrector.add_point(raw_levels['t'][n].timestamp(), 'dz', raw_levels['v'][n])

    def correct(self, observations: geopandas.GeoDataFrame) -> None:
        if self._corrector is None:
            print(f'Error: no station corrections are available.')
            return None
        corrections = self._corrector.interpolate(['dz',], observations['t'])[0]
        observations['z'] -= corrections

class ZoneTides(Waterlevel):
    def __init__(self, zone_shapefile: str) -> None:
        self._zones = geopandas.read_file(zone_shapefile)
        super().__init__()

    def preload(self, observations: geopandas.GeoDataFrame) -> None:
        # Spatial join to determine which polygon each observation is in (and hence which station controls)
        annotated_pts = geopandas.sjoin(observations, self._zones, how='inner', predicate='within')
        # List of all required stations
        self._stations = annotated_pts['ControlStn'].unique()
        self._tides = dict()
        # For each station, we need to determine the time bounds of the observations affected, then
        # call the CO-OPS API to get the waterlevel corrections; these are stored until it's time to
        # do the corrections for some/all of the observations
        for station in self._stations:
            station_times = annotated_pts[annotated_pts['ControlStn'] == station]['t']
            min_time = station_times.min() - 10*60
            max_time = station_times.max() + 10*60
            raw_levels = get_noaa_station(station, min_time, max_time)
            corrections = InterpTable(['dz',])
            for n in range(len(raw_levels)):
                corrections.add_point(raw_levels['t'][n].timestamp(), 'dz', raw_levels['v'][n])
            self._tides[station] = { 'min': min_time, 'max': max_time, 'raw': raw_levels, 'table': corrections }

    def correct(self, observations: geopandas.GeoDataFrame) -> None:
        # Spatial join to determine which polygon each observation is in (and hence which station controls)
        annotated_pts = geopandas.sjoin(observations, self._zones, how='inner', predicate='within')
        for station, data in self._tides.items():
            station_points = annotated_pts[annotated_pts['ControlStn'] == station]
            lut_times = station_points['t'] - station_points['ATCorr']*60
            wl_corr = data['table'].interpolate(['dz',], lut_times)[0]
            station_points['z'] -= station_points['RR']*wl_corr
            observations.loc[station_points.index, 'z'] = station_points['z']
