##\file basic_workflow.py
#
# Provide a simple CSB workflow example.
#
# This provides a simple CSB workflow that converts from the source file type,
# generates depths using the default time source, adds static metadata set at
# construction time (presumably from the common observer), and then writes the
# output in the file format specified on construction.
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

from typing import Tuple
import copy
from pathlib import Path
from openvbi.adaptors import Loader, Writer
from openvbi.core.observations import Dataset
from openvbi.workflow import Workflow
from openvbi.core.metadata import Metadata

class BasicWorkflow(Workflow):
    def __init__(self, loader: Loader, depth_source: str, writer: Writer, metadata: Metadata) -> None:
        self.loader = loader
        self.writer = writer
        self.depth_source = depth_source
        self.metadata = copy.deepcopy(metadata.metadata())
    
    def insuffix(self):
        return self.loader.suffix()
    
    def outsuffix(self):
        return self.writer.suffix()

    def process_file(self, infile: str | Path, outfile: str | Path) -> Tuple[bool,dict]:
        errors = {"filename": infile, "stage": ""}
        try:
            errors["stage"] = "loader"
            data: Dataset = self.loader.load(infile)
            errors["stage"] = "observation generation"
            data.generate_observations(self.depth_source)
            errors["stage"] = "metadata update"
            data.meta.update(self.metadata)
            errors["stage"] = "output writing"
            self.writer.write(data, outfile)
        except:
            return False, errors
        return True, {}
