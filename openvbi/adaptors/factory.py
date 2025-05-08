##\file loader.py
# This file provides a factory method for instantiating loaders logger file loadeds, currently
# those defined in teamsurv.py, wibl.py, and ydvr.py. The extension of the input filename provided
# is used to select the underlying loader to return. If the file uses an incorrect file extension,
# the wrong loader will be returned.
#
# Copyright 2025 Center for Coastal and Ocean Mapping & NOAA-UNH Joint
# Hydrographic Center, University of New Hampshire.
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

from typing import Type
from pathlib import Path


from openvbi.adaptors import Loader, teamsurv, wibl, ydvr

def get_loader(input_file: str | Path) -> Loader:
    """

    :rtype: Loader
    """
    match input_file:
        case str():
            infile: Path = Path(input_file)
        case Path():
            infile: Path = input_file
        case _:
            raise ValueError(f"Expected input_file to be of type str or Path, but it was of type {type(input_file)}")

    suffixes = infile.suffixes
    if len(suffixes) == 0:
        raise ValueError(f"Unable to infer loader type for input file {str(input_file)}, which has no filename suffix.")

    first_suff = suffixes[0].lower()
    if first_suff == teamsurv.LOADER_SUFFIX.lower():
            return teamsurv.TeamSurvLoader()
    elif first_suff == wibl.LOADER_SUFFIX.lower():
            return wibl.WIBLLoader()
    elif first_suff == ydvr.LOADER_SUFFIX.lower():
            return ydvr.YDVRLoader()
    else:
        raise ValueError("Unable to infer loader type for input file {str(input_file}: unknown filename suffix.")
