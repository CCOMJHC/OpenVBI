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
from openvbi.filters import Filter

class deduplicate(Filter):
    def __init__(self, verbose: bool) -> None:
        self._verbose = verbose

    def Execute(self, dataset: geopandas.GeoDataFrame) -> geopandas.GeoDataFrame:
        current_depth: float = 0
        out_index = []
        n_in: int = len(dataset)
        for n in range(n_in):
            if dataset['z'][n] != current_depth:
                out_index.append(n)
                current_depth = dataset['z'][n]
        if self._verbose:
            print(f'After deduplication, total {len(out_index)} points selected from {n_in}.')
        return dataset.iloc[out_index]
