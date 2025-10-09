#\file schema_widget.py
#
# A simple Tkinter GUI widget that runs as a top-level window to allow for generation
# of JSON-format metadata for B.12 data files.  The code here reads the schema file and
# auto-generates the GUI, ensuring that it's always up to date with respect to the schema.
# The tool also allows for validation of the inputs, ensuring that the metadata is always
# going to be valid for data being submitted to the DCDB archive.
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
from pathlib import Path
import re
import json

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

from openvbi.core.schema import SchemaObject, SchemaRef, \
    SchemaLeafString, SchemaLeafInteger, SchemaArray

class SchemaNodeWidgetsRenderer(ABC):
    def validate(self) -> bool:
        ...

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
