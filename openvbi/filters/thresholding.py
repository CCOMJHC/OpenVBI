##\file thresholding.py
#
# Routines for over/under thresholding of depth data
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

import geopandas
from openvbi.core.observations import Dataset
import openvbi.core.metadata as md
from openvbi.filters import Filter
from openvbi import version

# Remove any points that are shoaler than the threshold specified
class shoaler_than(Filter):
    def __init__(self, threshold: float) -> None:
        self._threshold = threshold
        super().__init__()
    
    def _execute(self, dataset: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
        self.n_inputs = len(dataset)
        dataset = dataset[dataset['z'] > self._threshold]
        self.n_outputs = len(dataset)
        return dataset

    def _metadata(self, meta: md.Metadata) -> None:
        meta.addProcessingAction(md.ProcessingType.ALGORITHM, None,
            name='ShoalDepth Filter',
            source='OpenVBI',
            version=version(),
            comment=f'After filtering, total {self.n_outputs} points selected from {self.n_inputs}.')

# Remove any points that are deeper than the threshold specified
class deeper_than(Filter):
    def __init__(self, threshold: float) -> None:
        self._threshold = threshold
        super().__init__()

    def _execute(self, dataset: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
        self.n_inputs = len(dataset)
        dataset = dataset[dataset['z'] < self._threshold]
        self.n_outputs = len(dataset)
        return dataset

    def _metadata(self, meta: md.Metadata) -> None:
        meta.addProcessingAction(md.ProcessingType.ALGORITHM, None,
            name='DeepDepth Filter',
            source='OpenVBI',
            version=version(),
            comment=f'After filtering, total {self.n_outputs} points selected from {self.n_inputs}.')