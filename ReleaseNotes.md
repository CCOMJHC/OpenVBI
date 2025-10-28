# Release 1.0.1

This release includes the GUI tool for running workflows and creating metadata JSON files for adding to files that don't already have them, in addition to a number of other improvements are updates:

1. WIBL files can now be loaded into OpenVBI for processing.
2. Significant improvements in packaging, installation, and test fixture support.
3. Workflow objects that allow packaging of a series of processing steps for a single file.
4. GUI to apply a workflow object to all files in a directory, with visual feedback on progress.
5. GUI to read a JSON schema document and automatically generate the GUI to specify the metadata for a file, and validate it.
6. Support for output of auxiliary variables that might be captured as timestamped data (e.g., surface temperature, speed over ground, wind speed and direction, etc.)
7. Command line utility prototype to give some packaged tools (e.g., dump data to ASCII).
8. Functionality for loading compressed data files directly.
