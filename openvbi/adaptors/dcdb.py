##\file dcdb.py
#
# Read files of DCDB data
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

from typing import Dict,Tuple,Any
import geopandas
import pandas
import numpy as np

def load_csv_data(filename: str) -> Tuple[geopandas.GeoDataFrame, Dict[str,Any]]:
    data = geopandas.read_file(filename)
    data = data.rename(columns={'DEPTH': 'z', 'LON': 'lon', 'LAT': 'lat'})
    data['t'] = np.fromiter((t.timestamp() for t in pandas.to_datetime(data['TIME'])), dtype='float')
    
    logger_uuid = data['UNIQUE_ID'].unique()[0]
    file_uuid = data['FILE_UUID'].unique()[0]
    ship_name = data['PLATFORM_NAME'].unique()[0]
    
    data = data.drop(columns=['TIME', 'UNIQUE_ID','FILE_UUID', 'PROVIDER', 'PLATFORM_NAME'])
    data = data.astype({'z':'float'})
    data = data.dropna(subset=['t'])

    meta = {'LoggerUUID': logger_uuid, 'FileUUID': file_uuid, 'ShipName': ship_name}
    return geopandas.GeoDataFrame(data, geometry=geopandas.points_from_xy(data.lon, data.lat), crs='EPSG:4326'), meta
