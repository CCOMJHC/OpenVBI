"""Submission of OpenVBI outputs to the IHO DCDB/Crowbar CSB API.

The Crowbar API accepts two forms of multipart POST:

* GeoJSON: file with embedded CSB metadata and metadataInput={"uniqueID": ...}
* XYZ/CSV: file with a separate metadataInput JSON form field.

The token is supplied in the x-auth-token header, not as a bearer token.
NOAA reference: https://www.reginfo.gov/public/do/DownloadDocument?objectID=134088401
"""

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any

import requests


BASE_URL = 'https://www.ngdc.noaa.gov/ingest-external/upload/csb'
FILE_FORMATS = {'.geojson': 'geojson', '.json': 'geojson', '.csv': 'xyz', '.xyz': 'xyz'}


class DCDBValidationError(ValueError):
    """a data file or metadata file is not ready for submission."""


class DCDBSubmissionError(RuntimeError):
    """an HTTP submission failed or returned an unexpected response."""


@dataclass(frozen=True)
class SubmissionPlan:
    """a validated, ready-to-send Crowbar submission request."""

    file: Path
    environment: str
    file_format: str
    url: str
    unique_id: str
    metadata_input: dict[str, Any]


def _read_object(path: Path) -> dict[str, Any]:
    try:
        with path.open('r', encoding='utf-8-sig') as stream:
            value = json.load(stream)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise DCDBValidationError(f'{path}: invalid UTF-8 JSON: {exc}') from exc
    except OSError as exc:
        raise DCDBValidationError(f'Cannot read {path}: {exc}') from exc
    if not isinstance(value, dict):
        raise DCDBValidationError(f'{path}: JSON root must be an object')
    return value


def _unique_id(metadata: dict[str, Any], source: Path) -> str:
    """Extract uniqueID from OpenVBI metadata or a GeoJSON FeatureCollection."""
    props = metadata.get('properties', metadata)
    platform = props.get('platform') if isinstance(props, dict) else None
    value = platform.get('uniqueID') if isinstance(platform, dict) else None
    if value is None:
        value = props.get('uniqueID') if isinstance(props, dict) else None
    if not isinstance(value, str) or not value.strip() or value.strip() == 'NOTSET':
        raise DCDBValidationError(
            f'{source}: missing platform.uniqueID (a DCDB-issued vessel identifier is required)'
        )
    return value.strip()


def _check_coordinates(lon: float, lat: float, depth: float, source: Path) -> None:
    if not all(math.isfinite(value) for value in (lon, lat, depth)):
        raise DCDBValidationError(f'{source}: first sounding has non-finite coordinates/depth')
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        raise DCDBValidationError(f'{source}: first sounding has invalid longitude/latitude')


def _check_utc_timestamp(value: str, source: Path) -> None:
    if not value.strip():
        raise DCDBValidationError(f'{source}: first sounding has no timestamp')
    try:
        parsed_time = datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
    except ValueError as exc:
        raise DCDBValidationError(f'{source}: first sounding has invalid ISO 8601 time') from exc
    if parsed_time.tzinfo is None or parsed_time.utcoffset() != timezone.utc.utcoffset(None):
        raise DCDBValidationError(f'{source}: first sounding time must include UTC timezone')


def _check_first_feature(features: list, path: Path) -> None:
    feature = features[0]
    if not isinstance(feature, dict) or feature.get('type') != 'Feature':
        raise DCDBValidationError(f'{path}: first item must be a GeoJSON Feature')
    geometry = feature.get('geometry')
    if not isinstance(geometry, dict) or geometry.get('type') != 'Point':
        raise DCDBValidationError(f'{path}: first feature must contain Point geometry')
    coords = geometry.get('coordinates')
    if not isinstance(coords, list) or len(coords) < 2:
        raise DCDBValidationError(f'{path}: first feature must contain longitude/latitude')
    properties = feature.get('properties')
    if not isinstance(properties, dict):
        raise DCDBValidationError(f'{path}: first feature must contain properties')
    try:
        lon = float(coords[0])
        lat = float(coords[1])
        depth = float(properties['depth'])
    except (ValueError, TypeError, KeyError) as exc:
        raise DCDBValidationError(f'{path}: first feature has invalid coordinates/depth') from exc
    _check_coordinates(lon, lat, depth, path)
    if not isinstance(properties.get('time'), str):
        raise DCDBValidationError(f'{path}: first feature requires an ISO 8601 time')
    _check_utc_timestamp(properties['time'], path)


def _check_xyz(path: Path) -> None:
    """Perform inexpensive preflight checks without loading large sounding files."""
    try:
        with path.open('r', encoding='utf-8-sig', newline='') as stream:
            reader = csv.reader(stream)
            header = next(reader, [])
            if [field.strip().upper() for field in header] != ['LON', 'LAT', 'DEPTH', 'TIME']:
                raise DCDBValidationError(
                    f'{path}: expected CSV/XYZ header LON,LAT,DEPTH,TIME'
                )
            row = next(reader, [])
            if len(row) != 4:
                raise DCDBValidationError(f'{path}: expected at least one four-column sounding row')
            try:
                longitude, latitude, depth = (float(value.strip()) for value in row[:3])
            except ValueError as exc:
                raise DCDBValidationError(f'{path}: first sounding has invalid coordinates/depth') from exc
            _check_coordinates(longitude, latitude, depth, path)
            _check_utc_timestamp(row[3], path)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise DCDBValidationError(f'Cannot read XYZ file {path}: {exc}') from exc


def prepare_submission(
    data_file: str | Path,
    metadata_file: str | Path | None = None,
    environment: str = 'test',
) -> SubmissionPlan:
    """Validate an OpenVBI output and construct the Crowbar multipart payload.

    For XYZ/CSV, OpenVBI's CSVWriter creates a same-named .json sidecar,
    which will be discovered automatically if --metadata is omitted.
    For GeoJSON, the uniqueID is taken from the embedded metadata. An optional
    metadata file is checked for agreement, but is not uploaded separately.

    This is a structural preflight, not full IHO B-12 schema validation.
    """
    path = Path(data_file)
    if not path.is_file():
        raise DCDBValidationError(f'Data file does not exist: {path}')
    if environment not in ('test', 'prod'):
        raise DCDBValidationError('Environment must be test or prod')

    file_format = FILE_FORMATS.get(path.suffix.lower())
    if file_format is None:
        raise DCDBValidationError('Supported data formats: .geojson, .json, .csv, .xyz')

    metadata_path = Path(metadata_file) if metadata_file is not None else None
    if file_format == 'geojson':
        data = _read_object(path)
        if data.get('type') != 'FeatureCollection':
            raise DCDBValidationError(f'{path}: expected a GeoJSON FeatureCollection')
        features = data.get('features')
        if not isinstance(features, list) or not features:
            raise DCDBValidationError(f'{path}: expected at least one GeoJSON feature')
        _check_first_feature(features, path)
        unique_id = _unique_id(data, path)
        if metadata_path is not None:
            metadata_id = _unique_id(_read_object(metadata_path), metadata_path)
            if metadata_id != unique_id:
                raise DCDBValidationError(
                    f'{metadata_path}: uniqueID does not match embedded GeoJSON metadata'
                )
        metadata_input = {'uniqueID': unique_id}
    else:
        _check_xyz(path)
        if metadata_path is None:
            metadata_path = path.with_suffix('.json')
        if not metadata_path.is_file():
            raise DCDBValidationError(
                f'Missing XYZ metadata file: {metadata_path} (pass --metadata)'
            )
        metadata = _read_object(metadata_path)
        props = metadata.get('properties', metadata)
        if not isinstance(props, dict):
            raise DCDBValidationError(f'{metadata_path}: metadata properties must be an object')
        unique_id = _unique_id(props, metadata_path)
        metadata_input = props

    route = f'test/{file_format}' if environment == 'test' else file_format
    return SubmissionPlan(
        file=path,
        environment=environment,
        file_format=file_format,
        url=f'{BASE_URL}/{route}',
        unique_id=unique_id,
        metadata_input=metadata_input,
    )


class DCDBClient:
    """Small reusable Crowbar upload client, with no automatic retries."""

    def __init__(self, token: str, *, timeout: int = 300):
        if not token or not token.strip():
            raise DCDBValidationError('A Crowbar authentication token is required')
        if timeout <= 0:
            raise DCDBValidationError('Timeout must be positive')
        self._token = token.strip()
        self._timeout = timeout

    def submit(self, plan: SubmissionPlan) -> dict[str, Any]:
        """POST a previously validated submission plan to Crowbar.

        The API may accept an upload even if its response is lost. Therefore
        connection failures are *not retried* automatically.
        """
        try:
            with plan.file.open('rb') as stream:
                response = requests.post(
                    plan.url,
                    headers={
                        'x-auth-token': self._token,
                        'Accept': 'application/json',
                    },
                    files={
                        'file': (plan.file.name, stream, 'application/octet-stream'),
                    },
                    data={'metadataInput': json.dumps(plan.metadata_input)},
                    timeout=self._timeout,
                    allow_redirects=False,  # never forward a trusted node token on redirects.
                )
        except requests.RequestException as exc:
            raise DCDBSubmissionError(
                f'Could not confirm submission ({type(exc).__name__}). '
                'Check Crowbar before retrying to avoid duplicate submissions.'
            ) from exc
        except OSError as exc:
            raise DCDBSubmissionError(f'Cannot open data file: {exc}') from exc

        if not 200 <= response.status_code < 300:
            # never include auth headers or an unbounded server response.
            message = response.text.strip()[:500]
            raise DCDBSubmissionError(
                f'Crowbar returned HTTP {response.status_code}: {message}'
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise DCDBSubmissionError(
                'Crowbar returned HTTP success without JSON; confirm the submission '
                'in Crowbar before retrying.'
            ) from exc

        if not isinstance(payload, dict):
            raise DCDBSubmissionError(
                'Crowbar returned an unexpected success response; verify before retrying.'
            )
        if payload.get('success') is False:
            raise DCDBSubmissionError(
                f"Crowbar rejected the upload: {str(payload.get('message', 'Unknown error'))[:500]}"
            )
        return payload
