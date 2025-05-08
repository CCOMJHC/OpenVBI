##\file __init__.py
#
# General types and routines for filtering depth data
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

from abc import ABC, abstractmethod

import geopandas

from openvbi.core.observations import Dataset
from openvbi.core.metadata import Metadata

class Filter(ABC):
    def __init__(self):
        pass

    def Execute(self, dataset: Dataset) -> Dataset:
        dataset.data = self._execute(dataset.data)
        self._metadata(dataset.meta)
        return dataset

    @abstractmethod
    def _execute(self, dataset: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
        pass

    @abstractmethod
    def _metadata(self, meta: Metadata) -> None:
        pass