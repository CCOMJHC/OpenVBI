import json
import sys
from pathlib import Path
import traceback

import click

from openvbi.submission.dcdb import (
    DCDBClient, DCDBSubmissionError, DCDBValidationError, prepare_submission,
)


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
    from openvbi.adaptors.factory import LoaderFactoryByFilename, Loader

    try:
        loader: Loader = LoaderFactoryByFilename(input_file)
        data = loader.load(input_file)
        for i, p in enumerate(data.packets):
            output.write(f"Packet {i}: name: {p.Name()}\n")
            if hasattr(p, '_data'):
                output.write(f"\t_data: {p.RawPacketRep()}\n")
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
    import openvbi.workflow_gui.gui as workflow_gui

    workflow_gui.main(schema)


@click.command()
@click.option('--file', 'data_file', required=True,
              type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
              help='DCDB GeoJSON (.geojson/.json) or XYZ/CSV (.xyz/.csv) output file.')
@click.option('--metadata', 'metadata_file',
              type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
              help='External metadata JSON. Optional for GeoJSON; defaults to CSV sidecar .json for XYZ.')
@click.option('--environment', type=click.Choice(['test', 'prod']),
              default='test', show_default=True, help='Crowbar destination environment.')
@click.option('--token', envvar='CROWBAR_API_TOKEN',
              help='Trusted Node token (prefer CROWBAR_API_TOKEN to avoid shell history exposure).')
@click.option('--confirm-prod', is_flag=True,
              help='Required to upload to PROD; TEST is the default.')
@click.option('--dry-run', is_flag=True,
              help='Validate and show the planned request without contacting Crowbar.')
@click.option('--timeout', type=click.IntRange(min=1), default=300, show_default=True,
              help='HTTP request timeout in seconds.')
def submit(data_file: Path, metadata_file: Path | None, environment: str,
           token: str | None, confirm_prod: bool, dry_run: bool, timeout: int) -> None:
    """Submit OpenVBI output to the DCDB/Crowbar CSB ingestion API.

    GeoJSON embeds its metadata; XYZ/CSV requires a metadata JSON sidecar.
    The token can be provided with the CROWBAR_API_TOKEN environment variable.
    """
    try:
        plan = prepare_submission(data_file, metadata_file, environment)
        if dry_run:
            click.echo(json.dumps({
                'dryRun': True,
                'file': str(plan.file),
                'environment': plan.environment,
                'endpoint': plan.url,
                'format': plan.file_format,
                'uniqueID': plan.unique_id,
            }, indent=2))
            return
        if environment == 'prod' and not confirm_prod:
            raise DCDBValidationError(
                'PROD submission requires --confirm-prod (test in TEST first)'
            )
        client = DCDBClient(token or '', timeout=timeout)
        click.echo(json.dumps(client.submit(plan), indent=2))
    except (DCDBValidationError, DCDBSubmissionError) as exc:
        raise click.ClickException(str(exc)) from exc


cli.add_command(dump)
cli.add_command(workflow)
cli.add_command(submit)
