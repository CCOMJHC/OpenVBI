#\file workflow/__main__.py
#
# OpenVBI Workflow GUI Tool
#
# This file provides the main interface (primary window) implementing the workflow tool,
# which allows the BasicWorkflow class to be applied to all of the files in a given input
# directory, and an auxiliary tool to generate and validate GeoJSON metadata files that
# can be added to data that doesn't have this embedded in the files.  The metadata tool
# also allows for validation of existing metadata files.
# 
# Copyright 2025 OpenVBI Project.  All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

from typing import cast, Dict
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
import json
import threading

from openvbi.core.schema import open_schema, parse_schema, SchemaNode, SchemaObject
from openvbi.adaptors.factory import LoaderLibrary, LoaderFactory, WriterLibrary, WriterFactory, DepthMsgLibrary, DepthMsgTag
from openvbi.workflow.basic_workflow import BasicWorkflow
from openvbi.workflow import apply_workflow, WorkflowEvent
from openvbi.core.metadata import Metadata

from schema_widget import MetadataMainWindow

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

    root = tk.Tk()
    root.title("OpenVBI Workflow Tool")
    main_window = MainWindow(root, schema_obj)
    root.mainloop()

    sys.exit(0)

if __name__ == '__main__':
    main()
