import sys
from pathlib import Path

import click

from openvbi.adaptors import factory, Loader

@click.version_option()
@click.group()
def cli():
    pass


@click.command()
@click.argument('input_file', type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path))
@click.argument('output', type=click.File('w'))
def dump(input_file: Path, output):
    """
    Dump logger data file to ASCII format for debugging.

    \b
    INPUT_FILE represents the path of the logger data file to read from.
    OUTPUT represents the path of the file to write ASCII values to. Use '-' for standard output.

    """
    try:
        loader: Loader = factory.get_loader(input_file)
        data = loader.load(input_file)
        for i, p in enumerate(data.packets):
            output.write(f"Packet {i}: name: {p.Name()}\n")
            if hasattr(p, '_data'):
                output.write(f"\t_data: {p._data}\n")
    except Exception as e:
        sys.exit(str(e))

cli.add_command(dump)
