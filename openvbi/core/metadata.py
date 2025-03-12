## \file metadata.py
# \brief Core metadata structures and functionality for IHO CSBWG B.12-compatible metadata
#
# A key component of VBI output is (or should be) metadata to describe what you're providing.
# The International Hydrographic Organisation's Crowdsourced Bathmetry Working Group (CSBWG)
# guidance document (B.12, currently version 3.0.0, at
# https://iho.int/uploads/user/pubs/bathy/B_12_CSB-Guidance_Document-Edition_3.0.0_Final.pdf)
# specifies two types of metadata: mandatory, and recommended.  The "mandatory" metadata is
# very basic information required for the data to be minimally useful; the "recommended"
# metadata is significantly richer and includes things like sensor offsets, lineage of data,
# and processing information.  The objects here allow for this data to be harvested from the
# source files (if possible), or to be set as it is provided by the user.  The rendering is
# always in B.12 format.
#
# Copyright 2024 OpenVBI Project.  All Rights Reserved.
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

from typing import Dict, Any, Tuple, Union, List
from pathlib import Path
from enum import StrEnum
import datetime as dt
import tempfile
import os
import json
from csbschema.validators import validate_b12_3_1_0_2023_08

mandatoryMetadata = {
    'type': 'FeatureCollection',
    'crs': {
        'type': 'name',
        'properties': {
            'name': 'EPSG:4326'
        }
    },
    'properties': {
        'trustedNode': {
            'providerOrganizationName': 'NOTSET',
            'providerEmail': 'NOTSET',
            'uniqueVesselID': 'NOTSET',
            'convention': 'GeoJSON CSB 3.1',
            'dataLicense': 'CC0 1.0',
            'providerLogger': 'NOTSET',
            'providerLoggerVersion': 'NOTSET',
            'navigationCRS': 'EPSG:4326',
            'verticalReferenceOfDepth': 'NOTSET',
            'vesselPositionReferencePoint': 'NOTSET'
        },
        'platform': {
            'uniqueID': 'NOTSET'
        }
    }
}

class VerticalReference(StrEnum):
    TRANSDUCER = 'Transducer'
    UNKNOWN = 'Unknown'

class VerticalReferencePosition(StrEnum):
    GNSS = 'GNSS'
    TRANSDUCER = 'Transducer'
    REFERENCEPLATE = 'ReferencePlate'

class VesselIdentifier(StrEnum):
    MMSI = 'MMSI'
    IMO = 'IMO'

class SensorType(StrEnum):
    SOUNDER = 'Sounder'
    IMU = 'IMU'
    GNSS = 'GNSS'

class ProcessingType(StrEnum):
    TIMESTAMP = 'TimeStampInterpolation'
    COORDCHANGE = 'CRSChange'
    VERTREDUCTION = 'VerticalReduction'
    GNSSPROC = 'GNSS'
    SOUNDSPEED = 'SoundSpeed'
    UNCERTAINTY = 'Uncertainty'
    ALGORITHM = 'Algorithm'

class Metadata:
    def __init__(self) -> None:
        self.meta = mandatoryMetadata.copy()

    def setProviderID(self, providerName: str, providerEmail: str) -> None:
        self.meta['properties']['trustedNode']['providerOrganizationName'] = providerName
        self.meta['properties']['trustedNode']['providerEmail'] = providerEmail
    
    def setIdentifiers(self, uniqueID: str, logger: str, loggerVersion: str) -> None:
        self.meta['properties']['trustedNode']['uniqueVesselID'] = uniqueID
        self.meta['properties']['platform']['uniqueID'] = uniqueID
        self.meta['properties']['trustedNode']['providerLogger'] = logger
        self.meta['properties']['trustedNode']['providerLoggerVersion'] = loggerVersion
    
    def setReferencing(self, verticalRef: VerticalReference, verticalRefPosition: VerticalReferencePosition) -> None:
        self.meta['properties']['trustedNode']['verticalReferenceOfDepth'] = verticalRef
        self.meta['properties']['trustedNode']['vesselPositionReferencePoint'] = verticalRefPosition
    
    def setVessel(self, vesselType: str, vesselName: str, vesselLength: float) -> None:
        self.meta['properties']['platform']['type'] = vesselType
        self.meta['properties']['platform']['name'] = vesselName
        self.meta['properties']['platform']['length'] = vesselLength
    
    def setVesselID(self, idType: VesselIdentifier, idNumber: str) -> None:
        self.meta['properties']['platform']['IDType'] = idType
        self.meta['properties']['platform']['IDNumber'] = idNumber
    
    def addSensor(self, sensorType: SensorType, make: str, model: str, position: List[float], **kwargs) -> None:
        sensor = dict()
        if type is None:
            raise ValueError()
        sensor['type'] = sensorType
        if make is not None:
            sensor['make'] = make
        if model is not None:
            sensor['model'] = model
        if position is not None:
            if len(position) != 3:
                raise ValueError()
            sensor['position'] = position
        if sensorType == SensorType.SOUNDER:
            if 'draft' in kwargs:
                sensor['draft'] = kwargs['draft']
                if 'draftUncert' in kwargs:
                    sensor['draftUncert'] = kwargs['draftUncert']
            if 'frequency' in kwargs:
                sensor['frequency'] = kwargs['frequency']
            if 'pulseLength' in kwargs:
                sensor['pulseLength'] = kwargs['pulseLength']
        elif sensorType == SensorType.GNSS:
            if 'antennaModel' in kwargs:
                sensor['antennaModel'] = kwargs['antennaModel']
        if 'sensors' not in self.meta['properties']['platform']:
            self.meta['properties']['platform']['sensors'] = list()
        self.meta['properties']['platform']['sensors'].append(sensor)

    def setProcessingFlags(self, soundSpeed: bool, positionOffsets: bool, dataProcessed: bool) -> None:
        if soundSpeed is not None:
            self.meta['properties']['platform']['soundSpeedDocumented'] = soundSpeed
        if positionOffsets is not None:
            self.meta['properties']['platform']['positionOffsetsDocumented'] = positionOffsets
        if dataProcessed is not None:
            self.meta['properties']['platform']['dataProcessed'] = dataProcessed
    
    def getComment(self) -> str:
        value: str = None
        if 'contributorComments' in self.meta['properties']:
            value = self.meta['properties']['platform']['contributorComments']
        return value

    def setComment(self, comment: str) -> None:
        self.meta['properties']['platform']['contributorComments'] = comment
    
    def addProcessingAction(self, procType: ProcessingType, timestamp: dt.datetime, **kwargs) -> None:
        element = dict()
        element['type'] = procType
        if timestamp is None:
            timestamp = dt.datetime.utcnow()
        element['timestamp'] = timestamp.isoformat() + 'Z'
        if procType == ProcessingType.TIMESTAMP:
            if 'method' not in kwargs:
                raise ValueError()
            element['method'] = kwargs['method']
            if 'algorithm' in kwargs:
                element['algorithm'] = kwargs['algorithm']
            if 'version' in kwargs:
                element['version'] = kwargs['version']
        elif procType == ProcessingType.COORDCHANGE:
            if 'original' not in kwargs or 'destination' not in kwargs:
                raise ValueError()
            element['original'] = kwargs['original']
            element['destination'] = kwargs['destination']
            if 'method' in kwargs:
                element['method'] = kwargs['method']
        elif procType == ProcessingType.VERTREDUCTION:
            if 'reference' not in kwargs or 'datum' not in kwargs or 'method' not in kwargs:
                raise ValueError()
            element['reference'] = kwargs['reference']
            element['datum'] = kwargs['datum']
            if kwargs['method'] not in ['Ellipsoid Reduction', 'Observed Waterlevel', 'Predicted Waterlevel']:
                raise ValueError()
            element['method'] = kwargs['method']
            if 'algorithm' in kwargs:
                element['algorithm'] = kwargs['algorithm']
                if 'version' not in kwargs:
                    raise ValueError()
                element['version'] = kwargs['version']
            if 'model' in kwargs:
                element['model'] = kwargs['model']
        elif procType == ProcessingType.GNSSPROC:
            if 'algorithm' not in kwargs or kwargs['algorithm'] not in ['RTKLib', 'CSRS-PPP']:
                raise ValueError()
            element['algorithm'] = kwargs['algorithm']
            if 'version' in kwargs:
                element['version'] = kwargs['version']
        elif procType == ProcessingType.SOUNDSPEED:
            if 'source' not in kwargs or 'method' not in kwargs:
                raise ValueError()
            element['source'] = kwargs['source']
            element['method'] = kwargs['method']
            if 'version' in kwargs:
                element['version'] = kwargs['version']
        elif procType == ProcessingType.UNCERTAINTY:
            if 'name' not in kwargs or 'parameters' not in kwargs or 'version' not in kwargs or 'comment' not in kwargs or 'reference' not in kwargs:
                raise ValueError()
            element['name'] = kwargs['name']
            element['parameters'] = kwargs['parameters']
            element['version'] = kwargs['version']
            element['comment'] = kwargs['comment']
            element['reference'] = kwargs['reference']
        elif procType == ProcessingType.ALGORITHM:
            if 'name' not in kwargs:
                raise ValueError()
            element['name'] = kwargs['name']
            if 'source' in kwargs:
                element['source'] = kwargs['source']
            if 'parameters' in kwargs:
                if not isinstance(kwargs['parameters'], 'dict'):
                    raise ValueError()
                element['parameters'] = kwargs['parameters']
            if 'version' in kwargs:
                element['version'] = kwargs['version']
            if 'comment' in kwargs:
                element['comment'] = kwargs['comment']
        if 'processing' not in self.meta['properties']:
            self.meta['properties']['processing'] = list()
        self.meta['properties']['processing'].append(element)

    def render(self, filename: Union[Path,str]) -> None:
        metadata = self.meta
        metadata['features'] = []
        with open(filename, 'w') as f:
            json.dump(metadata, f)

    def metadata(self) -> Dict[str,Any]:
        return self.meta
    
    def validate(self) -> Tuple[bool,Dict[str,Any]]:
        # Since the validator doesn't accept in-memory dictionaries, we have to render the
        # internal structure to a file
        fd, filename = tempfile.mkstemp(suffix='json')
        os.close(fd)
        filepath = Path(filename)
        self.render(filepath)
        # (valid, result) = validate_b12_3_1_0_2024_04(filepath)
        (valid, result) = validate_b12_3_1_0_2023_08(filepath)
        filepath.unlink()
        if valid:
            return valid, None
        else:
            return valid, result['errors']

    def adopt(self, metadata: Dict[str,Any]) -> None:
        if 'type' not in metadata or 'crs' not in metadata or 'properties' not in metadata or 'platform' not in metadata:
            raise ValueError()
        self.meta = dict()
        self.meta['type'] = metadata['type']
        self.meta['crs'] = metadata['crs']
        self.meta['properties'] = metadata['properties']
        self.meta['platform'] = metadata['platform']
        if 'processing' in metadata:
            self.meta['processing'] = metadata['processing']
        result, errors = validate()
        if not result:
            raise ValueError()
