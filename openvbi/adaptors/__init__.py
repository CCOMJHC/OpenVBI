##\file __init__.py
#
# General types for file adaptors
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

from typing import Protocol, Callable, TypeVar
from pathlib import Path
import gzip
import bz2
import lzma

import geopandas

import openvbi.core.metadata as md
from openvbi.core.observations import Dataset


def get_fopen(filename: str | Path) -> Callable:
    if isinstance(filename, Path):
        fname: Path = filename
    elif isinstance(filename, str):
        fname: Path = Path(filename)
    else:
        raise ValueError(f"Expected filename to be of type str or Path but it was {type(filename)}.")

    match fname.suffix:
        case '.gz' | '.gzip':
            return gzip.open
        case '.bz2' | '.bzip2':
            return bz2.open
        case 'lz' | '.lzma':
            return lzma.open
        case _:
            return open

# Type aliases
GeoPandasDataset = tuple[geopandas.GeoDataFrame, md.Metadata]
OpenVBIDataset = TypeVar('OpenVBIDataset', bound=Dataset|GeoPandasDataset)

class Loader(Protocol):
    def suffix(self) -> str:
        pass

    def load(self, filename: str | Path, **kwargs) -> OpenVBIDataset:
        pass


class Writer(Protocol):
    def suffix(self) -> str:
        pass

    def write(self, data: Dataset, filename: str | Path, **kwargs) -> None:
        pass
