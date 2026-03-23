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

from datetime import datetime as dt, timezone
import geopandas
import openvbi.core.metadata as md
from openvbi.filters import Filter
from openvbi import version

class before_time(Filter):
    def __init__(self, timepoint: float) -> None:
        self._threshold = timepoint
        super().__init__()
            
    @property
    def params(self) -> dict:
        return {'threshold': self._threshold}

    def _execute(self, dataset: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
        self.n_inputs = len(dataset)
        dataset = dataset[dataset['t'] < self._threshold]
        self.n_outputs = len(dataset)
        return dataset
    
    def _metadata(self, meta: md.Metadata) -> None:
        meta.addProcessingAction(md.ProcessingType.ALGORITHM, dt.now(tz=timezone.utc),
            name='BeforeTime Filter',
            source='OpenVBI',
            version=version(),
            parameters=self.params,
            comment=f'After filtering, total {self.n_outputs} points selected from {self.n_inputs}.')

class after_time(Filter):
    def __init__(self, timepoint: float) -> None:
        self._threshold = timepoint
        super().__init__()
    
    @property
    def params(self) -> dict:
        return {'threshold': self._threshold}
    
    def _execute(self, dataset: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
        self.n_inputs = len(dataset)
        dataset = dataset[dataset['t'] > self._threshold]
        self.n_outputs = len(dataset)
        return dataset

    def _metadata(self, meta: md.Metadata) -> None:
        meta.addProcessingAction(md.ProcessingType.ALGORITHM, dt.now(tz=timezone.utc),
            name='AfterTime Filter',
            source='OpenVBI',
            version=version(),
            parameters=self.params,
            comment=f'After filtering, total {self.n_outputs} points selected from {self.n_inputs}.')