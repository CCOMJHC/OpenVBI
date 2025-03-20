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
