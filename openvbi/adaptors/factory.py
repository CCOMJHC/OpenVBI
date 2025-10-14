##\file factory.py
#
# A simple factory method (and supporting code) for loaders, writers, and depth messages
#
# Copyright 2025 OpenVBI Project.  All Rights Reserved.
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

from typing import Dict, List
from openvbi.adaptors import Loader, Writer
from openvbi.adaptors.ydvr import YDVRLoader
from openvbi.adaptors.wibl import WIBLLoader
from openvbi.adaptors.teamsurv import TeamSurvLoader
from openvbi.adaptors.generic_ascii import GenericASCIILoader
from openvbi.adaptors.dcdb import GeoJSONWriter, CSVWriter

LOADER_DICT: Dict[str, Loader] = {'YDVR': YDVRLoader, 'WIBL': WIBLLoader, 'TeamSurv': TeamSurvLoader, 'Generic ASCII': GenericASCIILoader}
WRITER_DICT: Dict[str, Writer] = {'DCDB GeoJSON': GeoJSONWriter, 'DCDB CSV': CSVWriter}
DEPTH_MESSAGES: Dict[str, str] = {'Depth (NMEA2000)': 'Depth', 'DBT (NMEA0183)': 'DBT', 'DPT (NMEA0183)': 'DPT'}

def LoaderLibrary() -> List[str]:
    return list(LOADER_DICT.keys())

def LoaderFactory(loader_name: str) -> Loader:
    try:
        loader = LOADER_DICT[loader_name]()
    except KeyError:
        raise ValueError()
    return loader
    
def WriterLibrary() -> List[str]:
    return list(WRITER_DICT.keys())

def WriterFactory(writer_name: str) -> Writer:
    try:
        writer = WRITER_DICT[writer_name]()
    except KeyError:
        raise ValueError()
    return writer

def DepthMsgLibrary() -> List[str]:
    return list(DEPTH_MESSAGES.keys())

def DepthMsgTag(depth_message: str) -> str:
    try:
        depth_tag = DEPTH_MESSAGES[depth_message]
    except KeyError:
        raise ValueError()
    return depth_tag
