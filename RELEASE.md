# PyPi release instructions

## Install dist dependencies in venv:
```shell
python3 -m venv venv-pypi
source venv-pypi/bin/activate
python -m pip install --upgrade build twine
```

## PyPi API token
Get a PyPi/Test PyPi API token(s) and save to $HOME/.pypirc

## Manual checks
Do the following before releasing:
  - Make sure pyproject.toml is up-to-date
  - Make sure README.md is up-to-date
  - Create new release on GitHub

## Build for upload to PyPi

Use `build` to build:
```shell
rm -rf dist && python -m build
```

## Upload to PyPi
Upload to Test PyPi:
```shell
python -m twine upload --repository testpypi dist/*
```

Upload to PyPi:
```shell
python -m twine upload dist/*
```
