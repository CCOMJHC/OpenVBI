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
import tempfile

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as msgbox
from tkinter import filedialog

from csbschema import validate_data

from openvbi.core.schema import SchemaObject, SchemaRef, \
    SchemaString, SchemaInteger, SchemaNumber, SchemaBoolean, SchemaArray

class SchemaNodeRenderer(ABC):
    def validate(self) -> tuple[bool,str]:
        ...

class SchemaStringRenderer(SchemaNodeRenderer):
    def __init__(self, parent_frame, name: str, leaf: SchemaString, state: dict, row: int, column: int,
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

    def validate(self) -> tuple[bool, str]:
        if self.required and self.stringVar.get() == '':
            self.set_invalid(True)
            return False, f"{self.name}: required, but no value set"

        if self.pattern is not None:
            if self.pattern.fullmatch(self.stringVar.get()) is None:
                self.set_invalid(True)
                return False, f"{self.name}: value does not match the pattern given"

        self.set_invalid(False)
        return True, ""

class SchemaStringEnumRenderer(SchemaNodeRenderer):
    def __init__(self, parent_frame, name: str, leaf: SchemaString, state: dict, row: int, column: int,
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

    def validate(self) -> tuple[bool, str]:
        if self.required and self.stringVar.get() == '':
            self.set_invalid(True)
            return False, f"{self.name}: required, but no value set"

        self.set_invalid(False)
        return True, ""

class SchemaIntegerRenderer(SchemaNodeRenderer):
    def __init__(self, parent_frame, name: str, leaf: SchemaInteger, state: dict, row: int, column: int,
                 *,
                 pad_x: int = 10,
                 pad_y: int = 5):
        self.name = name
        self.required = leaf.is_required
        self.minimum = leaf.minimum
        self.maximum = leaf.maximum
        # TODO: Consider making this an IntVar() instead, which would simplify validation
        self.intVar = tk.IntVar()
        state[name] = self.intVar
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

    def validate(self) -> tuple[bool, str]:
        if self.required and self.intVar.get() == None:
            self.set_invalid(True)
            return False, f"{self.name}: required, but no value set"

        try:
            int_val: int = self.intVar.get()
        except ValueError:
            self.set_invalid(True)
            return False, f"{self.name}: value is not a valid integer"

        if self.minimum:
            if int_val < self.minimum:
                self.set_invalid(True)
                return False, f"{self.name}: value is less than {self.minimum} limit"

        if self.maximum:
            if int_val > self.maximum:
                self.set_invalid(True)
                return False, f"{self.name}: value is more than {self.maximum} limit"

        self.set_invalid(False)
        return True, ""
    
class SchemaNumberRenderer(SchemaNodeRenderer):
    def __init__(self, parent_frame, name: str, leaf: SchemaNumber, state: dict, row: int, column: int,
                 *,
                 pad_x: int = 10,
                 pad_y: int = 5):
        self.name = name
        self.required = leaf.is_required
        self.minimum = leaf.minimum
        self.maximum = leaf.maximum
        self.numberVar = tk.DoubleVar()
        state[name] = self.numberVar
        self.entry = tk.Entry(parent_frame, highlightthickness=1, textvariable=state[name])
        self.entry.grid(row=row, column=column)
        self.set_invalid(False)
    
    def set_invalid(self, is_invalid: bool):
        if is_invalid:
            self.entry.configure(highlightbackground='red', highlightcolor='red', highlightthickness=1)
            self.is_invalid = True
        else:
            self.entry.configure(highlightbackground='grey', highlightcolor='grey', highlightthickness=1)
            self.is_invalid = False

    def validate(self) -> tuple[bool, str]:
        try:
            num_val: float = self.numberVar.get()
        except ValueError:
            self.set_invalid(True)
            return False, f"{self.name}: value is not a valid float"

        if self.minimum:
            if num_val < self.minimum:
                self.set_invalid(True)
                return False, f"{self.name}: value is less than {self.minimum} limit"

        if self.maximum:
            if num_val > self.maximum:
                self.set_invalid(True)
                return False, f"{self.name}: value is more than {self.maximum} limit"

        self.set_invalid(False)
        return True, ""
    
class SchemaBooleanRenderer(SchemaNodeRenderer):
    def __init__(self, parent_frame, name: str, leaf: SchemaBoolean, state: dict, row: int, column: int,
                 *,
                 pad_x: int = 10,
                 pad_y: int = 5):
        self.name = name
        self.required = leaf.is_required
        self.checkVar = tk.BooleanVar()
        state[name] = self.checkVar
        self.checkButton = tk.Checkbutton(parent_frame, variable=state[name], onvalue=True, offvalue=False)
        self.checkButton.grid(column=column, row=row, sticky='w')
        self.set_invalid(False)
    
    def set_invalid(self, is_invalid: bool):
        if is_invalid:
            self.checkButton.configure(highlightcolor='red', highlightthickness=1)
            self.is_valid = False
        else:
            self.checkButton.configure(highlightcolor='grey', highlightthickness=1)
            self.is_valid = True

    def validate(self) -> tuple[bool, str]:
        # For a boolean, even if it's marked "required", there's always a state to use,
        # and therefore nothing to validate --- it's always valid.
        self.set_invalid(False)
        return True, ""

class SchemaObjectRenderer(SchemaNodeRenderer):
    def __init__(self, parent_frame, name: str, obj: SchemaObject, state: dict,
                 *,
                 pad_x: int = 10,
                 pad_y: int = 5):
        self.state = {}
        state[name] = self.state
        self.properties: dict[str, SchemaNodeRenderer] = {}

        row = 0
        for prop, value in obj.properties.items():
            if value is None:
                # TODO: Remove after we have implemented all node types, after which no nodes will be None
                continue
            if value.is_required:
                label: str = f"{prop} *"
            else:
                label: str = prop
            if isinstance(value, SchemaRef):
                value = value.referent
                if value is None:
                    print(f'error: reference {prop} has no referent.')
                    continue
            if isinstance(value, SchemaObject):
                object_frame = tk.LabelFrame(parent_frame, text=prop, padx=pad_x, pady=pad_y)
                self.properties[prop] = SchemaObjectRenderer(object_frame, prop, value, self.state)
                object_frame.grid(column=0, row=row, columnspan=2, sticky='ew')
                row += 1
                continue
            if isinstance(value, SchemaArray):
                array_frame = tk.LabelFrame(parent_frame, text=prop, padx=pad_x, pady=pad_y)
                self.properties[prop] = SchemaArrayRenderer(array_frame, prop, value, self.state)
                array_frame.grid(column=0, row=row, columnspan=2, sticky='ew')
                row += 1
                continue
            tk.Label(parent_frame, text=label, anchor='e', justify='right').grid(sticky=tk.E, column=0, row=row)
            processed: bool = False
            if isinstance(value, SchemaString):
                if value.enum_values is None:
                    self.properties[prop] = SchemaStringRenderer(parent_frame, prop, value, self.state, column=1, row=row)
                else:
                    self.properties[prop] = SchemaStringEnumRenderer(parent_frame, prop, value, self.state, column=1, row=row)
                processed = True
            if isinstance(value, SchemaInteger):
                self.properties[prop] = SchemaIntegerRenderer(parent_frame, prop, value, self.state, column=1, row=row)
                processed = True
            if isinstance(value, SchemaNumber):
                self.properties[prop] = SchemaNumberRenderer(parent_frame, prop, value, self.state, column=1,
                                                                 row=row)
                processed = True
            if isinstance(value, SchemaBoolean):
                self.properties[prop] = SchemaBooleanRenderer(parent_frame, prop, value, self.state, row=row, column=1)
                processed = True

            if not processed:
                print(f"error: have not yet implemented rendering of node type {type(value)} | {name} | {prop}")
            row += 1

    def validate(self) -> tuple[bool, str]:
        valid: bool = True
        messages: list[str] = []
        for p in self.properties.values():
            rc, msg = p.validate()
            if not rc:
                valid = False
                messages.append(msg)
        return valid, "\n\n".join(messages)

class SchemaArrayRenderer(SchemaNodeRenderer):
    hor_pad = 10
    ver_pad = 5

    def __init__(self, parent: tk.LabelFrame, name: str, arr: SchemaArray, state: dict,
                 *,
                 pad_x: int = 10,
                 pad_y: int = 5) -> None:
        self.state = []
        state[name] = self.state
        self.parent = parent
        self.arr = arr
        self.is_open = False

        self.preview = tk.Label(parent, text="$PREVIEW", anchor='e', padx=pad_x, pady=pad_y)
        self.preview.grid(column=0, row=0)
        self.open_button = tk.Button(parent, text="Edit...", command=self.open)
        self.open_button.grid(column=1, row=0)

    def validate(self) -> tuple[bool, str]:
        return True, ""

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


class SchemaRefRenderer(SchemaNodeRenderer):
    def __init__(self, parent_frame, ref: SchemaRef, state: dict,
                 row: int, column: int,
                 *,
                 pad_x: int = 10,
                 pad_y: int = 5):
        self.referents: dict[str, SchemaNodeRenderer] = {}

        self.frame = tk.LabelFrame(parent_frame, text=ref.name,
                              padx=pad_x, pady=pad_y)
        if ref.referent:
            r = ref.referent
            if isinstance(r, SchemaObject):
                self.referents[r.name] = SchemaObjectRenderer(self.frame, ref.name, r, state)

        self.frame.grid(row=row, column=0, columnspan=2, sticky='ew')

    def validate(self) -> tuple[bool, str]:
        valid: bool = True
        messages: list[str] = []
        for r in self.referents.values():
            rc, msg = r.validate()
            if not rc:
                valid = False
                messages.append(msg)
        return valid, '\n\n'.join(messages)

def generate_output(d: dict) -> dict:
    ser = {}
    for k, v in d.items():
        if isinstance(v, dict):
            ser[k] = generate_output(v)
        elif isinstance(v, list):
            if len(v) > 0:
                ser[k] = []
                for item in v:
                    if isinstance(item, dict):
                        ser[k].append(generate_output(item))
                    else:
                        ser[k].append(item.get())
        else:
            # This is a leaf item which is a tk variable, so the interface is
            # the same for any item.
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

    def validate_entries(self) -> tuple[bool, list[str]]:
        valid: bool = True
        messages: list[str] = []
        # First validate properties against schema
        for p in self.properties.values():
            rc, msg = p.validate()
            if not rc:
                valid = False
                messages.append(msg)
        # Now make sure meta properties (like output filename) are valid
        if self.export_filename.get() == '':
            self.set_export_filename_invalid(True)
            valid = False
            messages.append("Output filename not set")
        else:
            self.set_export_filename_invalid(False)
        return valid, messages
    
    def on_preflight(self):
        is_valid, messages = self.validate_entries()
        self.report.delete('1.0', tk.END)
        if is_valid:
            self.report.insert(tk.END, "Preflight Checks: Metadata appears to be valid.\n")
        else:
            self.report.insert(tk.END, "Preflight Checks: Metadata validation failed:\n\n" + "\n\n".join(messages))

    def on_extern_validate(self):
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as tmpf:
            data = generate_output(self.state)
            data['features'] = [] # Need this to validate as a FeatureCollection
            json.dump(data, tmpf)
            tmpf.flush()
            valid, result = validate_data(tmpf.name, version='3.1.0-2024-04')
            self.report.delete('1.0', tk.END)
            if valid:
                self.report.insert(tk.END, "Metadata passes validation!\n")
            else:
                errors: list[str] = []
                for e in result['errors']:
                    errors.append(f'Path: {e["path"]}\nError: {e["message"]}')
                self.report.insert(tk.END, "Metadata validation failed:\n\n" + "\n\n".join(errors))

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
            data =  generate_output(self.state)
            # We ignore the "features" array, since we're just trying to generate the
            # core metadata to include in files that don't contain their own.  However,
            # this needs to exist for the metadata to validate (since it's a FeatureCollection)
            # so we add an empty array here.
            data['features'] = []
            json.dump(data, f)
        return True

    def do_export(self):
        is_valid, messages = self.validate_entries()
        self.report.delete('1.0', tk.END)
        if not is_valid:
            msg = "\n\n".join(messages)
            self.report.insert(tk.END, f"WARNING: validation failed:\n\n{msg}\n\n")
        # Export
        if self.serialize(Path(self.export_filename.get())):
            self.report.insert(tk.END, f"INFO: metadata export to {self.export_filename.get()} complete.\n")
        else:
            self.report.insert(tk.END, f"ERROR: metadata export to {self.export_filename.get()} failed.\n")

    def __init__(self, root: tk.Tk, schema: SchemaObject) -> None:
        self.properties: dict[str, SchemaNodeRenderer] = {}
        # Dict to hold state variables that will be used to generate a JSON document based on the schema
        self.state = {}

        self.root = tk.Toplevel(root)

        self.main_frame = tk.Frame(self.root, padx=self.hor_pad, pady=self.ver_pad)
        self.main_frame.grid(row=0, column=0, sticky='nsew')

        row: int = 0
        for v in schema.properties.values():
            if isinstance(v, SchemaRef):
                self.properties[v.name] = SchemaRefRenderer(self.main_frame, v, self.state, row, column=0)
            elif isinstance(v, SchemaObject):
                self.properties[v.name] = SchemaObjectRenderer(self.main_frame, v.name, v, self.state)
            elif isinstance(v, SchemaArray):
                self.properties[v.name] = SchemaArrayRenderer(self.main_frame, v.name, v, self.state)
            else:
                if v.is_required:
                    label: str = f"{v.name} *"
                else:
                    label: str = v.name
                name = tk.Label(self.main_frame, text=label, anchor='e', justify='right')
                name.grid(row=row, column=0, sticky=tk.E)
                if isinstance(v, SchemaString):
                    if len(v.enum_values):
                        self.properties[v.name] = SchemaStringEnumRenderer(self.main_frame, v.name, v, self.state, row, column=1)
                    else:
                        self.properties[v.name] = SchemaStringRenderer(self.main_frame, v.name, v, self.state, row, column=1)
                elif isinstance(v, SchemaInteger):
                    self.properties[v.name] = SchemaIntegerRenderer(self.main_frame, v.name, v, self.state, row, column=1)
                elif isinstance(v, SchemaNumber):
                    self.properties[v.name] = SchemaNumberRenderer(self.main_frame, v.name, v, self.state, row, column=1)
                elif isinstance(v, SchemaBoolean):
                    self.properties[v.name] = SchemaBooleanRenderer(self.main_frame, v.name, v, self.state, row, column=1)
            row += 1
            

        self.export_frame = tk.LabelFrame(self.main_frame, text='Export', padx=self.hor_pad, pady=self.ver_pad)
        self.filename_label = tk.Label(self.export_frame, text='Filename', anchor='e')
        self.filename_label.grid(column=0, row=0)
        self.export_filename = tk.StringVar()
        self.filename_entry = tk.Entry(self.export_frame, highlightthickness=1, textvariable=self.export_filename)
        self.filename_entry.grid(column=1, row=0)
        self.filename_button = tk.Button(self.export_frame, text='Choose...', command=self.set_export_filename)
        self.filename_button.grid(column=3, row=0)
        self.set_export_filename_invalid(False)
        self.export_frame.grid(row=row, column=0, columnspan=2, sticky='ew')
        row += 1

        # Set up buttons for direct actions
        self.button_frame = tk.LabelFrame(self.main_frame, text='Actions', padx=self.hor_pad, pady=self.ver_pad)

        self.preflight_button = tk.Button(self.button_frame, text="Preflight Check", command=self.on_preflight)
        self.preflight_button.grid(row=0, column=0)

        self.validate_button = tk.Button(self.button_frame, text='Validate', command=self.on_extern_validate)
        self.validate_button.grid(row=0, column=1)

        self.export_button = tk.Button(self.button_frame, text="Export", command=self.do_export)
        self.export_button.grid(row=0, column=2)

        self.exit_button = tk.Button(self.button_frame, text="Quit", command=self.root.destroy)
        self.exit_button.grid(row=0, column=3)

        self.button_frame.grid(row=row, column=0, columnspan=2, sticky='ew')
        row += 1

        # Set up output region for reports from validation, etc.
        self.report_frame = tk.LabelFrame(self.main_frame, text='Validation Output', padx=self.hor_pad, pady=self.ver_pad)
        self.report = tk.Text(self.report_frame, width=100, height=50, padx=self.hor_pad, pady=self.ver_pad)
        self.report.grid(row=0, column=0, sticky='nsew')
        self.report_frame.grid(row=0, column=3, rowspan=row, sticky='nsew', padx=self.hor_pad, pady=self.ver_pad)
