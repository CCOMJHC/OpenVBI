"""
TODO:
    - Add validation for patterns
    - Add support for non-string fields (integer, enum, array)
    - Add * to label for required fields
    - Right justify labels
    - Use localization to provide friendly names for fields
    - Add tooltips with descriptions for fields
    - For fields that are controlled vocabularies, provide drop-downs instead of free text
    - Display version of schema used (when this tool is launched eventually by workflow tool, allow schema version
      to be chosen from drop-down
    - ...

"""

from abc import ABC
from typing import cast, Dict
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
from pathlib import Path
import json
import threading
import re

from openvbi.core.schema import open_schema, parse_schema, SchemaNode, SchemaObject, SchemaRef, \
    SchemaLeafString, SchemaLeafInteger, SchemaArray
from openvbi.adaptors.factory import LoaderLibrary, LoaderFactory, WriterLibrary, WriterFactory, DepthMsgLibrary, DepthMsgTag
from openvbi.workflow.basic_workflow import BasicWorkflow
from openvbi.workflow import apply_workflow, WorkflowEvent
from openvbi.core.metadata import Metadata

class SchemaNodeWidgetsRenderer(ABC):
    def validate(self) -> bool:
        pass

class SchemaLeafStringRenderer(SchemaNodeWidgetsRenderer):
    def __init__(self, parent_frame, name: str, leaf: SchemaLeafString, state: dict, row: int, column: int,
                 *,
                 pad_x: int = 10,
                 pad_y: int = 5):
        self.name = name
        self.required = leaf.is_required
        if leaf.pattern is not None:
            self.pattern = re.compile(leaf.pattern)
        else:
            self.pattern = None
        self.stringVar = tk.StringVar()
        state[name] = self.stringVar
        self.entry = tk.Entry(parent_frame, highlightthickness=1, textvariable=state[name])
        self.entry.grid(column=column, row=row)
        self.set_invalid(False)

    def set_invalid(self, is_invalid: bool):
        if is_invalid:
            self.entry.configure(highlightbackground="red", highlightcolor="red", highlightthickness=1)
            self.is_invalid = True
        else:
            self.entry.configure(highlightbackground='grey', highlightcolor='grey', highlightthickness=1)
            self.is_invalid = False

    def validate(self) -> bool:
        print("SchemaLeafStringRenderer.validate() called...")
        if self.required and self.stringVar.get() == '':
            print(f"SchemaLeafString:{self.name} is not valid because it is a required but no value was provided")
            self.set_invalid(True)
            return False

        if self.pattern is not None:
            if self.pattern.fullmatch(self.stringVar.get()) is None:
                self.set_invalid(True)
                return False

        self.set_invalid(False)
        return True

class SchemaLeafStringEnumRenderer(SchemaNodeWidgetsRenderer):
    def __init__(self, parent_frame, name: str, leaf: SchemaLeafString, state: dict, row: int, column: int,
                 *,
                 pad_x: int = 10,
                 pad_y: int = 5):
        if leaf.enum_values is None:
            raise ValueError("Expected enum values in SchemaLeafString, but there were none.")

        self.name = name
        self.required = leaf.is_required
        self.stringVar = tk.StringVar()
        state[name] = self.stringVar
        self.entry = ttk.Combobox(parent_frame, textvariable=state[name])
        values = list(leaf.enum_values)
        self.entry['values'] = list(leaf.enum_values)
        self.stringVar.set(values[0])
        self.entry.grid(column=column, row=row)
        self.set_invalid(False)

    def set_invalid(self, is_invalid: bool):
        if is_invalid:
            # TODO: Add red frame styling to indicate invalid
            # self.entry.configure(bordercolor='red')
            self.is_invalid = True
        else:
            # TODO: Remove red frame styling to indicate valid
            # self.entry.configure(bordercolor='grey')
            self.is_invalid = False

    def validate(self) -> bool:
        print("SchemaLeafStringRenderer.validate() called...")
        if self.required and self.stringVar.get() == '':
            print(f"SchemaLeafString:{self.name} is not valid because it is a required but no value was provided")
            self.set_invalid(True)
            return False

        self.set_invalid(False)
        return True

class SchemaLeafIntegerRenderer(SchemaNodeWidgetsRenderer):
    def __init__(self, parent_frame, name: str, leaf: SchemaLeafInteger, state: dict, row: int, column: int,
                 *,
                 pad_x: int = 10,
                 pad_y: int = 5):
        self.name = name
        self.required = leaf.is_required
        self.minimum = leaf.minimum
        self.maximum = leaf.maximum
        self.stringVar = tk.StringVar()
        state[name] = self.stringVar
        self.entry = tk.Entry(parent_frame, highlightthickness=1, textvariable=state[name])
        self.entry.grid(column=column, row=row)
        self.set_invalid(False)

    def set_invalid(self, is_invalid: bool):
        if is_invalid:
            self.entry.configure(highlightbackground="red", highlightcolor="red", highlightthickness=1)
            self.is_invalid = True
        else:
            self.entry.configure(highlightbackground='grey', highlightcolor='grey', highlightthickness=1)
            self.is_invalid = False

    def validate(self) -> bool:
        print("SchemaLeafIntegerRenderer.validate() called...")
        if self.required and self.stringVar.get() == '':
            print(f"SchemaLeafString:{self.name} is not valid because it is a required but no value was provided")
            self.set_invalid(True)
            return False

        try:
            int_val: int = int(self.stringVar.get())
        except ValueError:
            self.set_invalid(True)
            return False

        if self.minimum:
            if int_val < self.minimum:
                self.set_invalid(True)
                return False

        if self.maximum:
            if int_val > self.maximum:
                self.set_invalid(True)
                return False

        self.set_invalid(False)
        return True


class SchemaObjectWidgetsRenderer(SchemaNodeWidgetsRenderer):
    def __init__(self, parent_frame, name: str, obj: SchemaObject, state: dict,
                 *,
                 pad_x: int = 10,
                 pad_y: int = 5):
        self.state = {}
        state[name] = self.state
        self.properties: dict[str, SchemaNodeWidgetsRenderer] = {}

        row = 0
        for prop, value in obj.properties.items():
            if value is None:
                # TODO: Remove after we have implemented all node types, after which no nodes will be None
                continue
            if value.is_required:
                label: str = f"{prop}*"
            else:
                label: str = prop
            tk.Label(parent_frame, text=label, anchor='e', justify='right').grid(sticky=tk.E, column=0, row=row)
            if isinstance(value, SchemaLeafString):
                if value.enum_values is None:
                    self.properties[prop] = SchemaLeafStringRenderer(parent_frame, prop, value, self.state, column=1, row=row)
                else:
                    self.properties[prop] = SchemaLeafStringEnumRenderer(parent_frame, prop, value, self.state, column=1, row=row)
            if isinstance(value, SchemaLeafInteger):
                self.properties[prop] = SchemaLeafIntegerRenderer(parent_frame, prop, value, self.state, column=1, row=row)
            if isinstance(value, SchemaArray):
                array_frame = tk.Frame(parent_frame)
                self.properties[prop] = SchemaArrayWidgetsRenderer(array_frame, prop, value, self.state)
                array_frame.grid(column=1, row=row)
            row += 1

    def validate(self) -> bool:
        print("SchemaObjectWidgetsRenderer.validate() called...")
        valid: bool = True
        for p in self.properties.values():
            if not p.validate():
                valid = False
        return valid


class SchemaArrayWidgetsRenderer(SchemaNodeWidgetsRenderer):
    hor_pad = 10
    ver_pad = 5

    def __init__(self, parent: tk.Frame, name: str, arr: SchemaArray, state: dict,
                 *,
                 pad_x: int = 10,
                 pad_y: int = 5) -> None:
        self.state = {}
        state[name] = self.state
        self.parent = parent
        self.arr = arr
        self.is_open = False

        self.preview = tk.Label(parent, text="$PREVIEW", anchor='e')
        self.preview.grid(column=0, row=0)
        self.open_button = tk.Button(parent, text="Edit...", command=self.open)
        self.open_button.grid(column=1, row=0)

    def open(self):
        if not self.is_open:
            self.root = tk.Toplevel(self.parent)
            self.main_frame = tk.Frame(self.root, padx=self.hor_pad, pady=self.ver_pad)
            self.main_frame.pack(fill='both')

            # Set up buttons for direct actions
            self.button_frame = tk.LabelFrame(self.main_frame, text='Actions', padx=self.hor_pad, pady=self.ver_pad)
            self.save_button = tk.Button(self.button_frame, text="Save", command=self.save)
            self.save_button.grid(row=0, column=0)
            self.button_frame.pack(fill='x')
            self.is_open = True

    def save(self):
        if self.is_open:
            print('TODO save...')
            self.root.grab_release()
            self.root.destroy()
            self.is_open = False


class SchemaRefWidgetsRenderer(SchemaNodeWidgetsRenderer):
    def __init__(self, parent_frame, ref: SchemaRef, state: dict,
                 *,
                 pad_x: int = 10,
                 pad_y: int = 5):
        self.referents: dict[str, SchemaNodeWidgetsRenderer] = {}

        self.frame = tk.LabelFrame(parent_frame, text=ref.name,
                              padx=pad_x, pady=pad_y)
        if ref.referent:
            r = ref.referent
            if isinstance(r, SchemaObject):
                self.referents[r.name] = SchemaObjectWidgetsRenderer(self.frame, ref.name, r, state)

        self.frame.pack(fill='x')

    def validate(self) -> bool:
        print("SchemaRefWidgetsRenderer.validate() called...")
        valid: bool = True
        for r in self.referents.values():
            if not r.validate():
                valid = False
        return valid


def generate_output(d: dict) -> dict:
    ser = {}
    for k, v in d.items():
        if isinstance(v, dict):
            ser[k] = generate_output(v)
        elif isinstance(v, tk.StringVar):
            ser[k] = v.get()
    return ser


class MetadataMainWindow:
    hor_pad = 10
    ver_pad = 5

    def set_export_filename_invalid(self, is_invalid: bool):
        if is_invalid:
            self.filename_entry.configure(highlightbackground="red", highlightcolor="red", highlightthickness=1)
            self.is_invalid = True
        else:
            self.filename_entry.configure(highlightbackground='grey', highlightcolor='grey', highlightthickness=1)
            self.is_invalid = False

    def validate(self) -> bool:
        print("MainWindow.validate() called...")
        valid: bool = True
        # First validate properties against schema
        for p in self.properties.values():
            if not p.validate():
                valid = False
        # Now make sure meta properties (like output filename) are valid
        if self.export_filename.get() == '':
            self.set_export_filename_invalid(True)
        else:
            self.set_export_filename_invalid(False)
        return valid

    def set_export_filename(self):
        export_filename = filedialog.asksaveasfilename(title="Select metadata output",
                                                       filetypes=(('JSON','*.json'),))
        self.export_filename.set(export_filename)
        self.filename_entry.xview_moveto(1.0)
        if self.export_filename.get() == '':
            self.set_export_filename_invalid(True)
        else:
            self.set_export_filename_invalid(False)

    def serialize(self, out_file: Path) -> bool:
        with open(out_file, mode='w') as f:
            json.dump(generate_output(self.state), f)
        return True

    def do_export(self):
        is_valid: bool = self.validate()
        if not is_valid:
            print("Normally we'd stop exporting because validation failed...")
        # Export
        self.serialize(Path(self.export_filename.get()))



    def __init__(self, root: tk.Tk, schema: SchemaObject) -> None:
        self.properties: dict[str, SchemaNodeWidgetsRenderer] = {}
        # Dict to hold state variables that will be used to generate a JSON document based on the schema
        self.state = {}

        self.root = tk.Toplevel(root)

        self.main_frame = tk.Frame(self.root, padx=self.hor_pad, pady=self.ver_pad)
        self.main_frame.pack(fill='both')

        for v in schema.properties.values():
            if isinstance(v, SchemaRef):
                self.properties[v.name] = SchemaRefWidgetsRenderer(self.main_frame, v, self.state)

        self.export_frame = tk.LabelFrame(self.main_frame, text='Export', padx=self.hor_pad, pady=self.ver_pad)
        self.filename_label = tk.Label(self.export_frame, text='Filename', anchor='e')
        self.filename_label.grid(column=0, row=0)
        self.export_filename = tk.StringVar()
        self.filename_entry = tk.Entry(self.export_frame, highlightthickness=1, textvariable=self.export_filename)
        self.filename_entry.grid(column=1, row=0)
        self.filename_button = tk.Button(self.export_frame, text='Choose...', command=self.set_export_filename)
        self.filename_button.grid(column=3, row=0)
        self.set_export_filename_invalid(False)
        self.export_frame.pack(fill='x')

        # Set up buttons for direct actions
        self.button_frame = tk.LabelFrame(self.main_frame, text='Actions', padx=self.hor_pad, pady=self.ver_pad)

        self.validate_button = tk.Button(self.button_frame, text="Validate", command=self.validate)
        self.validate_button.grid(row=0, column=0)

        self.export_button = tk.Button(self.button_frame, text="Export", command=self.do_export)
        self.export_button.grid(row=0, column=1)

        self.exit_button = tk.Button(self.button_frame, text="Quit", command=self.root.destroy)
        self.exit_button.grid(row=0, column=2)

        self.button_frame.pack(fill='x')


        # self.setup_button = tk.Button(self.button_frame, text='Setup', command=self.on_setup)
        # self.status_button = tk.Button(self.button_frame, text='Status', command=self.on_status)
        # self.metadata_button = tk.Button(self.button_frame, text='Metadata', command=self.on_metadata)
        # self.auth_button = tk.Button(self.button_frame, text='Authorisation', command=self.on_auth)
        # self.algorithm_button = tk.Button(self.button_frame, text='Algorithms', command=self.on_algorithms)
        # self.nmea0183_button = tk.Button(self.button_frame, text='NMEA0183 Filter', command=self.on_filter)
        # self.transfer_button = tk.Button(self.button_frame, text='Transfer Data', command=self.on_transfer)
        # self.restart_button = tk.Button(self.button_frame, text='Restart', command=self.on_restart)

        # self.setup_button.grid(row=0, column=0)
        # self.status_button.grid(row=0, column=1)
        # self.metadata_button.grid(row=0, column=2)
        # self.auth_button.grid(row=0, column=3)
        # self.algorithm_button.grid(row=0, column=4)
        # self.nmea0183_button.grid(row=0, column=5)
        # self.transfer_button.grid(row=0, column=6)
        # self.restart_button.grid(row=0, column=7)

class MainWindow():
    hor_pad = 10
    ver_pad = 5

    def __init__(self, root: tk.Tk, schema_object: SchemaObject) -> None:
        self.schema_object = schema_object

        # Text variables for the various input entry widgets
        self.input_directory = tk.StringVar()
        self.output_directory = tk.StringVar()
        self.loader = tk.StringVar()
        self.writer = tk.StringVar()
        self.depth_message = tk.StringVar()
        self.metadata_file = tk.StringVar()

        self.root = root
        self.main_frame = tk.Frame(root, padx=self.hor_pad, pady=self.ver_pad)
        self.main_frame.pack(fill='both')

        # Set up input side (left) with the various input components
        self.input_frame = tk.LabelFrame(self.main_frame, text='Inputs', padx=self.hor_pad, pady=self.ver_pad)
        self.input_frame.grid(row=0, column=0, sticky='nw')

        self.input_directory_label = tk.Label(self.input_frame, text='Input Directory', anchor='e')
        self.input_directory_entry = tk.Entry(self.input_frame, textvariable=self.input_directory)
        self.input_directory_button = tk.Button(self.input_frame, text='...', command=self.on_set_indir)
        self.input_directory_label.grid(row=0, column=0, sticky='e')
        self.input_directory_entry.grid(row=0, column=1, sticky='w')
        self.input_directory_button.grid(row=0, column=2, sticky='w')

        self.output_directory_label = tk.Label(self.input_frame, text='Output Directory', anchor='e')
        self.output_directory_entry = tk.Entry(self.input_frame, textvariable=self.output_directory)
        self.output_directory_button = tk.Button(self.input_frame, text='...', command=self.on_set_outdir)
        self.output_directory_label.grid(row=1, column=0, sticky='e')
        self.output_directory_entry.grid(row=1, column=1, sticky='w')
        self.output_directory_button.grid(row=1, column=2, sticky='w')

        self.workflow_frame = tk.LabelFrame(self.input_frame, text='Workflow', padx=self.hor_pad, pady=self.ver_pad)
        self.workflow_frame.grid(row=2, columnspan=3)

        self.workflow_loader_label = tk.Label(self.workflow_frame, text='Loader', anchor='e')
        self.workflow_loader_combo = ttk.Combobox(self.workflow_frame, textvariable=self.loader,
                                                  values=LoaderLibrary())
        self.workflow_loader_combo.current(0)
        self.workflow_loader_label.grid(row=0, column=0, sticky='e')
        self.workflow_loader_combo.grid(row=0, column=1, sticky='w')

        self.workflow_writer_label = tk.Label(self.workflow_frame, text='Writer', anchor='e')
        self.workflow_writer_combo = ttk.Combobox(self.workflow_frame, textvariable=self.writer,
                                                  values=WriterLibrary())
        self.workflow_writer_combo.current(0)
        self.workflow_writer_label.grid(row=1, column=0, sticky='e')
        self.workflow_writer_combo.grid(row=1, column=1, sticky='w')

        self.workflow_depth_label = tk.Label(self.workflow_frame, text='Depth Mesage', anchor='e')
        self.workflow_depth_combo = ttk.Combobox(self.workflow_frame, textvariable=self.depth_message,
                                                 values=DepthMsgLibrary())
        self.workflow_depth_combo.current(0)
        self.workflow_depth_label.grid(row=2, column=0, sticky='e')
        self.workflow_depth_combo.grid(row=2, column=1, sticky='w')

        self.workflow_metadata_label = tk.Label(self.workflow_frame, text='Metadata File', anchor='e')
        self.workflow_metadata_entry = tk.Entry(self.workflow_frame, textvariable=self.metadata_file)
        self.workflow_metadata_load_button = tk.Button(self.workflow_frame, text='...', command=self.on_load_metadata)
        self.workflow_metadata_create_button = tk.Button(self.workflow_frame, text='Create', command=self.on_create_metadata)
        self.workflow_metadata_label.grid(row=3, column=0, sticky='e')
        self.workflow_metadata_entry.grid(row=3, column=1, sticky='w')
        self.workflow_metadata_load_button.grid(row=3, column=2)
        self.workflow_metadata_create_button.grid(row=3, column=3)

        self.workflow_run_button = tk.Button(self.input_frame, text='Run Workflow', command=self.on_run_workflow)
        self.workflow_run_button.grid(row=3, columnspan=3)

        # Log output sequence
        self.log_frame = tk.LabelFrame(self.main_frame, text='Log Output', padx=self.hor_pad, pady=self.ver_pad)
        self.log_frame.grid(row=1, column=0, sticky='nw')
        self.log_scrollbar = tk.Scrollbar(self.log_frame, orient='vertical')
        self.log_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.log_output = tk.Text(self.log_frame, yscrollcommand=self.log_scrollbar.set)
        self.log_scrollbar.config(command=self.log_output.yview)
        self.log_output.pack(fill='both')

        # Run statistics
        self.stats_frame = tk.LabelFrame(self.main_frame, text='Run Statistics', padx=self.hor_pad, pady=self.ver_pad)
        self.stats_frame.grid(row=2, column=0, sticky='nw')
        self.stats_progress_label = tk.Label(self.stats_frame, text='Progress')
        self.stats_progressbar = ttk.Progressbar(self.stats_frame, orient='horizontal', maximum=100, value=0, length=500, mode='determinate')
        self.stats_progress_label.grid(row=0, column=0, sticky='e')
        self.stats_progressbar.grid(row=0, column=1)
        self.stats_success_count_label = tk.Label(self.stats_frame, text='Succeeded:', anchor='e')
        self.stats_success_count_value = tk.Label(self.stats_frame, text='0', anchor='w')
        self.stats_success_count_label.grid(row=1, column=0, sticky='e')
        self.stats_success_count_value.grid(row=1, column=1, sticky='w')
        self.stats_failed_count_label = tk.Label(self.stats_frame, text='Failed:', anchor='e')
        self.stats_failed_count_value = tk.Label(self.stats_frame, text='0', anchor='w')
        self.stats_failed_count_label.grid(row=2, column=0, sticky='e')
        self.stats_failed_count_value.grid(row=2, column=1, sticky='w')
        self.stats_total_count_label = tk.Label(self.stats_frame, text='Total:', anchor='e')
        self.stats_total_count_value = tk.Label(self.stats_frame, text='0', anchor='w')
        self.stats_total_count_label.grid(row=3, column=0, sticky='e')
        self.stats_total_count_value.grid(row=3, column=1, sticky='w')

        # Set up the output side (right) with a window for successful files, and one for problems
        self.output_frame = tk.LabelFrame(self.main_frame, text='Results', padx=self.hor_pad, pady=self.ver_pad)
        self.output_frame.grid(row=0, rowspan=3, column=1)

        self.success_frame = tk.LabelFrame(self.output_frame, text='Successful Files', padx=self.hor_pad, pady=self.ver_pad)
        self.success_frame.grid(row=0, column=0)

        self.success_scrollbar = tk.Scrollbar(self.success_frame, orient='vertical')
        self.success_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.success_files = tk.Text(self.success_frame, yscrollcommand=self.success_scrollbar.set)
        self.success_scrollbar.config(command=self.success_files.yview)
        self.success_files.pack(fill='both')

        self.failed_frame = tk.LabelFrame(self.output_frame, text='Failed Files', padx=self.hor_pad, pady=self.ver_pad)
        self.failed_frame.grid(row=1, column=0)

        self.failed_scrollbar = tk.Scrollbar(self.failed_frame, orient='vertical')
        self.failed_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.failed_files = tk.Text(self.failed_frame, yscrollcommand=self.failed_scrollbar.set)
        self.failed_scrollbar.config(command=self.failed_files.yview)
        self.failed_files.pack(fill='both')

    def on_set_indir(self) -> None:
        input_directory = filedialog.askdirectory(title='Select Input Directory')
        if input_directory:
            self.input_directory.set(input_directory)
            self.input_directory_entry.xview_moveto(1.0)

    def on_set_outdir(self) -> None:
        output_directory = filedialog.askdirectory(title='Select Output Directory')
        if output_directory:
            self.output_directory.set(output_directory)
            self.output_directory_entry.xview_moveto(1.0)

    def on_load_metadata(self) -> None:
        json_filename = filedialog.askopenfilename(title='Select JSON Metadata File ...', filetypes=[('JSON Files', '*.json')])
        if json_filename:
            self.metadata_file.set(json_filename)
            self.workflow_metadata_entry.xview_moveto(1.0)

    def on_create_metadata(self) -> None:
        metadata_widget: MetadataMainWindow = MetadataMainWindow(self.root, self.schema_object)
        self.root.wait_window(metadata_widget.root)

    def update_stats_display(self) -> None:
        if self.target_filecount == 0:
            self.stats_progressbar.config(value=0)
            self.stats_success_count_value.config(text='0')
            self.stats_failed_count_value.config(text='0')
            self.stats_total_count_value.config(text='0')
        else:
            self.stats_progressbar.config(value=int(100*self.total_count/self.target_filecount))
            percentage = 100.0*self.success_count/self.target_filecount
            self.stats_success_count_value.config(text=f'{self.success_count}/{self.target_filecount} ({percentage} %)')
            percentage = 100.0*self.failed_count/self.target_filecount
            self.stats_failed_count_value.config(text=f'{self.failed_count}/{self.target_filecount} ({percentage} %)')
            percentage = 100.0*self.total_count/self.target_filecount
            self.stats_total_count_value.config(text=f'{self.total_count}/{self.target_filecount} ({percentage} %)')

    def reset_stats(self) -> None:
        self.success_count = 0
        self.failed_count = 0
        self.total_count = 0
        self.target_filecount = 0
        self.update_stats_display()

    def increment_success_count(self) -> None:
        self.success_count += 1
        self.total_count += 1
        self.update_stats_display()

    def increment_failed_count(self) -> None:
        self.failed_count += 1
        self.total_count += 1
        self.update_stats_display()

    def workflow_callback(self, event: WorkflowEvent, info: Dict) -> None:
        match event:
            case WorkflowEvent.StartingWorkflow:
                self.log_output.insert(tk.END, f'Starting workflow for {info["count"]} files in |{info["inputdir"]}|\n')
                self.workflow_run_button.config(state='disabled')
                self.target_filecount = info['count']
            case WorkflowEvent.StartingFile:
                self.log_output.insert(tk.END, f'Starting processing for file |{info["name"]}|\n')
            case WorkflowEvent.StartingStage:
                self.log_output.insert(tk.END, f'  .... {info["stage"]}\n')
            case WorkflowEvent.FinishingFile:
                self.log_output.insert(tk.END, f'Finishing processing for file |{info["name"]}|\n')
                if info['success']:
                    self.success_files.insert(tk.END, f'{info["name"]}\n')
                    self.success_files.yview_moveto(1.0)
                    self.increment_success_count()
                else:
                    self.failed_files.insert(tk.END, f'{info["name"]} failed at stage {info["errors"]["stage"]}\n')
                    self.failed_files.yview_moveto(1.0)
                    self.increment_failed_count()
            case WorkflowEvent.FinishingWorkflow:
                self.log_output.insert(tk.END, f'Finishing workflow.')
                self.workflow_run_button.config(state='normal')
        self.log_output.yview_moveto(1.0)

    def on_run_workflow(self) -> None:
        # Remove the results of any previous run before starting!
        self.success_files.delete(1.0, tk.END)
        self.failed_files.delete(1.0, tk.END)
        self.log_output.delete(1.0, tk.END)
        self.reset_stats()

        loader = LoaderFactory(self.loader.get())
        writer = WriterFactory(self.writer.get())
        depth_message = DepthMsgTag(self.depth_message.get())
        metadata: Metadata = Metadata()
        if self.metadata_file.get():
            with open(self.metadata_file.get(), 'r') as f:
                meta_raw = json.load(f)
            try:
                metadata.adopt(meta_raw)
            except ValueError:
                print(f'error: failed to process metadata file.')
                messagebox.showerror(title='Metadata Validation Failure', message=f'Failed to validate metadata from {self.metadata_file.get()}')
                return

        input_dir: str = self.input_directory.get()
        output_dir: str = self.output_directory.get()
        if input_dir == '' or output_dir == '':
            messagebox.showerror(title='Input Validation', message='You must specify an input and output directory')
            return

        workflow: BasicWorkflow = BasicWorkflow(loader, depth_message, writer, metadata)
        self.workflow_thread = threading.Thread(target=apply_workflow, args=[input_dir, output_dir, workflow, self.workflow_callback])
        self.workflow_thread.start()

def main():
    schema: dict = open_schema()
    schema_node: SchemaNode = parse_schema(schema, None, None, None)
    schema_obj: SchemaObject = cast(SchemaObject, schema_node)
    schema_obj.resolve_refs()
    #print(f"DEBUG: Parsed schema AFTER resolving refs was:\n{schema_obj.to_string()}")

    # root = Tk()
    # frm = ttk.Frame(root, padding=10)
    # frm.grid()
    #
    # row: int = 0
    # for k, v in schema_obj.properties.items():
    #     ttk.Label(frm, text=v.name).grid(column=0, row=row)
    #     row += 1
    #
    # ttk.Button(frm, text="Quit", command=root.destroy).grid(column=0, row=row)

    root = tk.Tk()
    root.title("OpenVBI Workflow Tool")
    main_window = MainWindow(root, schema_obj)
    #print(f"DEBUG: state: {main_window.state}")
    root.mainloop()

    sys.exit(0)

if __name__ == '__main__':
    main()
