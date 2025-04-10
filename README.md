# OpenVBI
Reference Algorithms for Volunteer Bathymetric Information processing.

## Installation
### Local installation

```pip install .```

### Running in a VS Code dev container
You will need docker installed to use the dev container. There is more info
on the specific prerequisites [here](https://code.visualstudio.com/docs/devcontainers/containers).
Once you have docker installed, open the project in `vscode` and select "Dev
Container: Reopen in Container" from the command palette. Once the container is
built and running, you can open a terminal with access to it in `vscode` and
your environment will be set up.

## Usage

At present, most functionality is accessed via the OpenVBI Python API, examples of 
which can be found in the [examples](openvbi/examples) folder.

There is a simple command line tool called `vbi`:
```shell
vbi --help
Usage: vbi [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  dump  Dump logger data file to ASCII format for debugging.
```

The `dump` command allows logger data files to be written as ASCII to the screen or to a file. To dump
a file to the screen, run:
```shell
vbi dump tests/data/00000029.TSV.lzma -
Packet 0: name: RMC
	_data: {'Fields': {'timestamp': 123458, 'status': 'A', 'lat': 5048.614, 'lat_dir': 'N', 'lon': 108.632, 'lon_dir': 'W', 'spd_over_grnd': 0, 'true_course': 119.9, 'datestamp': 260822, 'mag_variation': 3.4, 'mag_var_dir': 'W'}, 'Talker': 'GP', 'Formatter': 'RMC'}
Packet 1: name: RMB
	_data: {'Fields': {'status': 'A', 'cross_track_error': '', 'cte_correction_dir': '', 'origin_waypoint_id': '', 'dest_waypoint_id': '', 'dest_lat': '', 'dest_lat_dir': '', 'dest_lon': '', 'dest_lon_dir': '', 'dest_range': '', 'dest_true_bearing': '', 'dest_velocity': '', 'arrival_alarm': 'V'}, 'Talker': 'GP', 'Formatter': 'RMB'}
Packet 2: name: GLL
	_data: {'Fields': {'lat': 5048.614, 'lat_dir': 'N', 'lon': 108.632, 'lon_dir': 'W', 'timestamp': 123458, 'status': 'A'}, 'Talker': 'GP', 'Formatter': 'GLL'}
...
...
...
```

To output to a file, specify the output file name instead of '-' as the last argument:
```shell
vbi dump tests/data/00000029.TSV.lzma 00000029.txt
```

## Testing
Create a virtual environment with test dependencies:
```shell
python3 -m venv venv
source venv/bin/activate
pip -r requirements-test.txt
```

Run tests:
```shell
pytest tests/unit/test_*.py
================================================================================================================================================ test session starts ================================================================================================================================================
platform darwin -- Python 3.13.2, pytest-8.3.5, pluggy-1.5.0
rootdir: /Users/$USER/repos/OpenVBI
configfile: pyproject.toml
plugins: cov-6.0.0, xdist-3.6.1
collected 2 items                                                                                                                                                                                                                                                                                                   

tests/unit/test_metadata.py ..                                                                                                                                                                                                                                                                                [100%]

================================================================================================================================================= warnings summary ==================================================================================================================================================
tests/unit/test_metadata.py::test_optional_metadata
tests/unit/test_metadata.py::test_optional_metadata
  /Users/$USER/repos/OpenVBI/openvbi/core/metadata.py:180: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    timestamp = dt.datetime.utcnow()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================================================================================================================================== 2 passed, 2 warnings in 0.06s ===========================================================================================================================================
```

## Library Components
