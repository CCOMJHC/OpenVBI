##\file deduplicate.py
#
# Routine to remove data before/after a given time
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

import datetime as dt
import geopandas
from openvbi.filters import Filter

class before_time(Filter):
    def __init__(self, timepoint: float) -> None:
        self._threshold = timepoint
        super().__init__()

    def Execute(self, dataset: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
        return dataset[dataset['t'] < self._threshold]

class after_time(Filter):
    def __init__(self, timepoint: float) -> None:
        self._threshold = timepoint
        super().__init__()

    def Execute(self, dataset: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
        return dataset[dataset['t'] > self._threshold]
