from abc import ABC
from typing import cast
import sys
import tkinter as tk

from openvbi.core.schema import open_schema, parse_schema, SchemaNode, SchemaObject, SchemaRef, \
    SchemaLeafString


class SchemaNodeWidgetsRenderer(ABC):
    pass

class SchemaLeafStringRenderer(SchemaNodeWidgetsRenderer):
    def __init__(self, parent_frame, name: str, leaf: SchemaLeafString, state: dict, row: int, column: int,
                 *,
                 pad_x: int = 10,
                 pad_y: int = 5):
        state[name] = tk.StringVar()
        tk.Entry(parent_frame, textvariable=state[name]).grid(column=column, row=row)


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
            tk.Label(parent_frame, text=prop).grid(column=0, row=row)
            if isinstance(value, SchemaLeafString):
                self.properties[prop] = SchemaLeafStringRenderer(parent_frame, prop, value, self.state, column=1, row=row)
            row += 1


class SchemaRefWidgetsRender(SchemaNodeWidgetsRenderer):
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


class MainWindow:
    hor_pad = 10
    ver_pad = 5

    def __init__(self, root: tk.Tk, schema: SchemaObject) -> None:
        self.properties: dict[str, SchemaNodeWidgetsRenderer] = {}
        # Dict to hold state variables that will be used to generate a JSON document based on the schema
        self.state = {}

        self.root = root

        self.main_frame = tk.Frame(root, padx=self.hor_pad, pady=self.ver_pad)
        self.main_frame.pack(fill='both')

        for v in schema.properties.values():
            if isinstance(v, SchemaRef):
                self.properties[v.name] = SchemaRefWidgetsRender(self.main_frame, v, self.state)

        # Set up buttons for direct actions
        self.button_frame = tk.LabelFrame(self.main_frame, text='Actions', padx=self.hor_pad, pady=self.ver_pad)
        self.exit_button = tk.Button(self.button_frame, text="Quit", command=root.destroy)
        self.exit_button.grid(row=0, column=0)
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


def main():
    schema: dict = open_schema()
    schema_node: SchemaNode = parse_schema(schema, None, None, None)
    schema_obj: SchemaObject = cast(SchemaObject, schema_node)
    schema_obj.resolve_refs()
    print(f"DEBUG: Parsed schema AFTER resolving refs was:\n{schema_obj.to_string()}")

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
    root.title("OpenVBI Metadata Generator")
    main_window = MainWindow(root, schema_obj)
    print(f"DEBUG: state: {main_window.state}")
    root.mainloop()

    sys.exit(0)

if __name__ == '__main__':
    main()
