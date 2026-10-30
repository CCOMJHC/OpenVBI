"""Offline tests for DCDB/Crowbar upload request preparation and CLI handling."""

import json
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner
import pytest
import requests

from openvbi.command import cli
from openvbi.submission.dcdb import (
    BASE_URL, DCDBClient, DCDBSubmissionError, DCDBValidationError,
    prepare_submission,
)


UNIQUE_ID = 'EXAMPLE-f8c469f8-df38-11e5-b86d-9a79f06e9478'


def geojson_file(tmp_path: Path, *, unique_id: str = UNIQUE_ID) -> Path:
    path = tmp_path / 'track.geojson'
    path.write_text(json.dumps({
        'type': 'FeatureCollection',
        'properties': {'platform': {'uniqueID': unique_id}},
        'features': [{
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-123.0, 47.0]},
            'properties': {'depth': 23.0, 'time': '2026-10-01T09:00:00Z'},
        }],
    }), encoding='utf-8')
    return path


def xyz_file(tmp_path: Path, extension: str = '.csv') -> Path:
    path = tmp_path / f'track{extension}'
    path.write_text(
        'LON,LAT,DEPTH,TIME\n-123.5,47.5,25.0,2026-10-01T09:00:00Z\n',
        encoding='utf-8',
    )
    return path


def xyz_metadata(tmp_path: Path) -> Path:
    path = tmp_path / 'track.json'
    path.write_text(json.dumps({
        'trustedNode': {'convention': 'XYZ GeoJSON CSB 3.1'},
        'platform': {'uniqueID': UNIQUE_ID},
    }), encoding='utf-8')
    return path


def test_geojson_payload_and_test_url(tmp_path):
    plan = prepare_submission(geojson_file(tmp_path))
    assert plan.url == f'{BASE_URL}/test/geojson'
    assert plan.metadata_input == {'uniqueID': UNIQUE_ID}
    assert plan.unique_id == UNIQUE_ID
    assert plan.file_format == 'geojson'


def test_geojson_json_extension_is_supported(tmp_path):
    path = geojson_file(tmp_path).rename(tmp_path / 'track.json')
    assert prepare_submission(path).url.endswith('/test/geojson')


def test_geojson_external_metadata_must_agree(tmp_path):
    data_file = geojson_file(tmp_path)
    metadata_file = tmp_path / 'metadata.json'
    metadata_file.write_text(json.dumps({'uniqueID': UNIQUE_ID}), encoding='utf-8')
    assert prepare_submission(data_file, metadata_file).unique_id == UNIQUE_ID
    metadata_file.write_text(json.dumps({'uniqueID': 'OTHER-id'}), encoding='utf-8')
    with pytest.raises(DCDBValidationError, match='does not match'):
        prepare_submission(data_file, metadata_file)


def test_geojson_rejects_non_collection_and_empty_features(tmp_path):
    path = geojson_file(tmp_path)
    path.write_text('{"type":"Feature"}', encoding='utf-8')
    with pytest.raises(DCDBValidationError, match='FeatureCollection'):
        prepare_submission(path)
    path.write_text(json.dumps({
        'type': 'FeatureCollection', 'features': [],
        'properties': {'platform': {'uniqueID': UNIQUE_ID}},
    }), encoding='utf-8')
    with pytest.raises(DCDBValidationError, match='at least one'):
        prepare_submission(path)


def test_missing_and_invalid_json(tmp_path):
    with pytest.raises(DCDBValidationError, match='does not exist'):
        prepare_submission(tmp_path / 'absent.geojson')
    path = geojson_file(tmp_path)
    path.write_text('{', encoding='utf-8')
    with pytest.raises(DCDBValidationError, match='invalid UTF-8 JSON'):
        prepare_submission(path)


def test_geojson_rejects_unset_unique_id(tmp_path):
    with pytest.raises(DCDBValidationError, match='missing platform.uniqueID'):
        prepare_submission(geojson_file(tmp_path, unique_id='NOTSET'))


def test_csv_uses_sidecar_as_metadata_input(tmp_path):
    path = xyz_file(tmp_path)
    metadata = xyz_metadata(tmp_path)
    plan = prepare_submission(path)
    assert plan.url == f'{BASE_URL}/test/xyz'
    assert plan.unique_id == UNIQUE_ID
    assert plan.metadata_input == json.loads(metadata.read_text())


def test_xyz_supports_wrapped_metadata(tmp_path):
    path = xyz_file(tmp_path, '.xyz')
    metadata = tmp_path / 'external.json'
    props = {'platform': {'uniqueID': UNIQUE_ID}, 'convention': 'XYZ CSB 3.1'}
    metadata.write_text(json.dumps({'properties': props}), encoding='utf-8')
    plan = prepare_submission(path, metadata, 'prod')
    assert plan.url == f'{BASE_URL}/xyz'
    assert plan.metadata_input == props


def test_xyz_missing_metadata(tmp_path):
    with pytest.raises(DCDBValidationError, match='Missing XYZ metadata'):
        prepare_submission(xyz_file(tmp_path))


@pytest.mark.parametrize('csv_text,error', [
    ('LON,LAT,DEPTH\n1,2,3\n', 'header'),
    ('LON,LAT,DEPTH,TIME\n', 'four-column'),
    ('LON,LAT,DEPTH,TIME\nx,47,10,2026-10-01T10:00:00Z\n', 'coordinates/depth'),
    ('LON,LAT,DEPTH,TIME\n-200,47,10,2026-10-01T10:00:00Z\n', 'longitude/latitude'),
    ('LON,LAT,DEPTH,TIME\n-123,47,10,\n', 'no timestamp'),
    ('LON,LAT,DEPTH,TIME\n-123,47,10,2026-10-01T09:00:00+00:00Z\n', 'ISO 8601'),
    ('LON,LAT,DEPTH,TIME\n-123,47,10,2026-10-01T09:00:00\n', 'UTC timezone'),
    ('LON,LAT,DEPTH,TIME\n-123,47,nan,2026-10-01T09:00:00Z\n', 'non-finite'),
])
def test_xyz_preflight_rejects_bad_first_record(tmp_path, csv_text, error):
    path = xyz_file(tmp_path)
    xyz_metadata(tmp_path)
    path.write_text(csv_text, encoding='utf-8')
    with pytest.raises(DCDBValidationError, match=error):
        prepare_submission(path)


def test_unrecognized_type_and_environment(tmp_path):
    path = geojson_file(tmp_path)
    with pytest.raises(DCDBValidationError, match='Environment'):
        prepare_submission(path, environment='unknown')
    with pytest.raises(DCDBValidationError, match='Supported data formats'):
        prepare_submission(path.rename(tmp_path / 'track.txt'))


def test_http_upload_uses_crowbar_contract(tmp_path, monkeypatch):
    plan = prepare_submission(geojson_file(tmp_path))
    calls = []

    def fake_post(url, *, headers, files, data, timeout, allow_redirects):
        assert allow_redirects is False
        calls.append((url, headers, files['file'][0],
                      files['file'][1].read(), data, timeout))
        return SimpleNamespace(
            status_code=201,
            json=lambda: {'message': 'Submission successful.',
                          'submissionIds': ['123'], 'success': True},
        )

    monkeypatch.setattr(requests, 'post', fake_post)
    result = DCDBClient('my-secret-token', timeout=33).submit(plan)
    assert result['submissionIds'] == ['123']
    assert calls[0][0] == f'{BASE_URL}/test/geojson'
    assert calls[0][1]['x-auth-token'] == 'my-secret-token'
    assert calls[0][2] == 'track.geojson'
    assert json.loads(calls[0][3])['type'] == 'FeatureCollection'
    assert json.loads(calls[0][4]['metadataInput']) == {'uniqueID': UNIQUE_ID}
    assert calls[0][5] == 33


def test_xyz_post_includes_metadata(tmp_path, monkeypatch):
    xyz_metadata(tmp_path)
    plan = prepare_submission(xyz_file(tmp_path))

    def fake_post(url, *, headers, files, data, timeout, allow_redirects):
        assert url.endswith('/test/xyz')
        assert json.loads(data['metadataInput']) == plan.metadata_input
        assert files['file'][1].read().startswith(b'LON,LAT,DEPTH,TIME')
        return SimpleNamespace(status_code=201, json=lambda: {'success': True})

    monkeypatch.setattr(requests, 'post', fake_post)
    assert DCDBClient('token').submit(plan)['success']


def test_http_rejection_shows_status(tmp_path, monkeypatch):
    plan = prepare_submission(geojson_file(tmp_path))
    monkeypatch.setattr(requests, 'post', lambda *a, **k: SimpleNamespace(
        status_code=401, text='Invalid token'))
    with pytest.raises(DCDBSubmissionError, match='HTTP 401'):
        DCDBClient('secret').submit(plan)


def test_http_body_rejection(tmp_path, monkeypatch):
    plan = prepare_submission(geojson_file(tmp_path))
    monkeypatch.setattr(requests, 'post', lambda *a, **k: SimpleNamespace(
        status_code=200, json=lambda: {'success': False, 'message': 'Invalid metadata'}))
    with pytest.raises(DCDBSubmissionError, match='Invalid metadata'):
        DCDBClient('secret').submit(plan)


def test_network_error_requires_check_before_retry(tmp_path, monkeypatch):
    plan = prepare_submission(geojson_file(tmp_path))

    def fake_post(*args, **kwargs):
        raise requests.Timeout('request timed out')

    monkeypatch.setattr(requests, 'post', fake_post)
    with pytest.raises(DCDBSubmissionError, match='before retrying'):
        DCDBClient('secret').submit(plan)


def test_non_json_success_unknown_state(tmp_path, monkeypatch):
    plan = prepare_submission(geojson_file(tmp_path))

    def invalid_json():
        raise ValueError('non-JSON')

    monkeypatch.setattr(requests, 'post', lambda *a, **k: SimpleNamespace(
        status_code=201, json=invalid_json))
    with pytest.raises(DCDBSubmissionError, match='before retrying'):
        DCDBClient('secret').submit(plan)


def test_cli_dry_run_needs_no_token_and_posts_nothing(tmp_path, monkeypatch):
    path = geojson_file(tmp_path)

    def forbidden_post(*args, **kwargs):
        raise AssertionError('dry-run must never issue an HTTP request')

    monkeypatch.setattr(requests, 'post', forbidden_post)
    output = CliRunner().invoke(cli, ['submit', '--file', str(path), '--dry-run'],
                                env={'CROWBAR_API_TOKEN': ''})
    assert output.exit_code == 0, output.output
    payload = json.loads(output.output)
    assert payload['dryRun'] is True
    assert payload['endpoint'].endswith('/test/geojson')
    assert payload['uniqueID'] == UNIQUE_ID
    assert 'token' not in output.output.lower()


def test_cli_prod_requires_confirmation(tmp_path, monkeypatch):
    path = geojson_file(tmp_path)

    def forbidden_post(*args, **kwargs):
        raise AssertionError('unconfirmed PROD must not issue an HTTP request')

    monkeypatch.setattr(requests, 'post', forbidden_post)
    output = CliRunner().invoke(cli, ['submit', '--file', str(path), '--environment', 'prod'],
                                env={'CROWBAR_API_TOKEN': 'secret'})
    assert output.exit_code != 0
    assert 'requires --confirm-prod' in output.output


def test_cli_reads_token_from_environment(tmp_path, monkeypatch):
    path = geojson_file(tmp_path)

    def fake_post(url, *, headers, files, data, timeout, allow_redirects):
        assert headers['x-auth-token'] == 'from-env'
        return SimpleNamespace(status_code=201, json=lambda: {
            'success': True, 'submissionIds': ['456'],
        })

    monkeypatch.setattr(requests, 'post', fake_post)
    output = CliRunner().invoke(cli, ['submit', '--file', str(path)],
                                env={'CROWBAR_API_TOKEN': 'from-env'})
    assert output.exit_code == 0, output.output
    assert json.loads(output.output)['submissionIds'] == ['456']
    assert 'from-env' not in output.output


def test_cli_missing_token_fails(tmp_path):
    output = CliRunner().invoke(cli, ['submit', '--file', str(geojson_file(tmp_path))],
                                env={'CROWBAR_API_TOKEN': ''})
    assert output.exit_code != 0
    assert 'authentication token is required' in output.output


def test_cli_help_exposes_submit():
    output = CliRunner().invoke(cli, ['--help'])
    assert output.exit_code == 0
    assert 'submit' in output.output


def test_cli_confirmed_prod_upload(tmp_path, monkeypatch):
    path = geojson_file(tmp_path)

    def fake_post(url, *, headers, files, data, timeout, allow_redirects):
        assert url == f'{BASE_URL}/geojson'
        assert not allow_redirects
        return SimpleNamespace(status_code=201, json=lambda: {
            'success': True, 'submissionIds': ['789'],
        })

    monkeypatch.setattr(requests, 'post', fake_post)
    output = CliRunner().invoke(
        cli, ['submit', '--file', str(path), '--environment', 'prod', '--confirm-prod'],
        env={'CROWBAR_API_TOKEN': 'secret'},
    )
    assert output.exit_code == 0, output.output
    assert json.loads(output.output)['submissionIds'] == ['789']


def test_redirect_does_not_forward_token(tmp_path, monkeypatch):
    plan = prepare_submission(geojson_file(tmp_path))

    def redirected(url, *, headers, files, data, timeout, allow_redirects):
        assert allow_redirects is False
        return SimpleNamespace(status_code=302, text='redirect blocked')

    monkeypatch.setattr(requests, 'post', redirected)
    with pytest.raises(DCDBSubmissionError, match='HTTP 302'):
        DCDBClient('secret').submit(plan)


def test_csv_writer_uses_valid_utc_timestamps(tmp_path):
    pytest.importorskip('csbschema')
    pytest.importorskip('marulc')
    pytest.importorskip('deepmerge')
    import pandas as pd
    from openvbi.adaptors.dcdb import CSVWriter

    data = SimpleNamespace(
        data=pd.DataFrame({'lon': [-123.0], 'lat': [47.0], 'z': [12.5], 't': [0.0]}),
        meta=SimpleNamespace(metadata=lambda: {'properties': {
            'trustedNode': {}, 'platform': {'uniqueID': UNIQUE_ID},
        }}),
    )
    CSVWriter().write(data, tmp_path / 'processed-data.csv')
    contents = (tmp_path / 'processed-data.csv').read_text()
    assert '1970-01-01T00:00:00.000Z' in contents
    assert '+00:00Z' not in contents
    assert prepare_submission(tmp_path / 'processed-data.csv').file_format == 'xyz'


def test_geojson_preflight_rejects_invalid_first_sounding(tmp_path):
    path = geojson_file(tmp_path)
    data = json.loads(path.read_text())
    data['features'][0]['properties']['time'] = 'invalid-time'
    path.write_text(json.dumps(data))
    with pytest.raises(DCDBValidationError, match='ISO 8601'):
        prepare_submission(path)
    data['features'][0]['properties']['time'] = '2026-10-01T09:00:00Z'
    data['features'][0]['geometry']['type'] = 'LineString'
    path.write_text(json.dumps(data))
    with pytest.raises(DCDBValidationError, match='Point geometry'):
        prepare_submission(path)
