##\file deduplicate.py
#
# Routine to deduplicate depths in the dataset
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

class deduplicate(Filter):
    def __init__(self, verbose: bool) -> None:
        self._verbose = verbose
        super().__init__()

    def _execute(self, dataset: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
        current_depth: float = 0
        out_index = []
        n_in: int = len(dataset)
        for n in range(n_in):
            if dataset['z'][n] != current_depth:
                out_index.append(n)
                current_depth = dataset['z'][n]
        self.n_inputs = n_in
        self.n_outputs = len(out_index)
        return dataset.iloc[out_index]

    def _metadata(self, meta: md.Metadata) -> None:
        meta.addProcessingAction(md.ProcessingType.ALGORITHM, None,
            name='Deduplicate',
            source='OpenVBI',
            version=version(),
            comment=f'After deduplication, total {self.n_outputs} points selected from {self.n_inputs}.')
