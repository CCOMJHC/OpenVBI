##\file __init__.py
#
# Waterlevel corrections for depth using a variety of different sources
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
import openvbi.core.metadata as md

class Waterlevel(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def preload(self, dataset: Dataset) -> None:
        pass

    def correct(self, dataset: Dataset) -> Dataset:
        dataset.depths = self._execute(dataset.depths)
        self._metadata(dataset.meta)
        return dataset

    @abstractmethod
    def _execute(self, observations: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
        pass

    @abstractmethod
    def _metadata(self, meta: md.Metadata) -> None:
        pass
