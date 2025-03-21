from typing import cast
import sys
import tkinter as tk

from openvbi.core.schema import open_schema, parse_schema, SchemaNode, SchemaObject

class MainWindow:
    hor_pad = 10
    ver_pad = 5

    def __init__(self, root: tk.Tk, schema: SchemaObject) -> None:
        self.sections: dict[str, tk.LabelFrame] = {}

        self.root = root

        self.main_frame = tk.Frame(root, padx=self.hor_pad, pady=self.ver_pad)
        self.main_frame.pack(fill='both')

        for k, v in schema.properties.items():
            frame = tk.LabelFrame(self.main_frame, text=k, padx=self.hor_pad, pady=self.ver_pad)
            if hasattr(v, 'referent'):
                r = v.referent
                if isinstance(r, SchemaObject):
                    row = 0
                    for prop, value in r.properties.items():
                        tk.Label(frame, text=prop).grid(column=0, row=row)
                        row += 1
            frame.pack(fill='x')
            self.sections[v] = frame

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
    print(f"Parsed schema AFTER resolving refs was:\n{schema_obj.to_string()}")

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
    root.mainloop()

    root.mainloop()
    sys.exit(0)

if __name__ == '__main__':
    main()
