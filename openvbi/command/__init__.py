import sys
from pathlib import Path
import traceback

import click

from openvbi.adaptors import factory, Loader
import openvbi.workflow_gui.gui as workflow_gui

@click.version_option()
@click.group()
def cli():
    pass


@click.command()
@click.argument('input_file', type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path))
@click.argument('output', type=click.File(mode='w', encoding='ascii'))
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
            else:
                output.write(f"\tNo _data in packet.\n")
    except Exception as e:
        sys.exit(traceback.format_exc())
    
@click.command()
@click.option('--schema', type=str, default='', help='Set the CSB Schema JSON file to use for validating metadata.')
def workflow(schema: str) -> None:
    '''
    Start the workflow GUI tool.

    This command starts the GUI tool to apply a workflow to a directory of files.  The workflow can
    have any series of steps supported by the library, and might start with raw files for processing,
    or pre-processed (e.g., DCDB GeoJSON or GeoPackage) data for post-processing, depending on the
    workflow.
    '''
    workflow_gui.main(schema)

cli.add_command(dump)
cli.add_command(workflow)