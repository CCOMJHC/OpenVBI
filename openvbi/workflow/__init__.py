##\file __init__.py
#
# Provide interface for a workflow management module.
#
# This provides a description of the requirements for a workflow management script: a
# set of instructions calling into OpenVBI that defines what "processed" means for a
# given application.  Having a common interface allows standard tools to call a
# workflow, no matter how it's implemented.
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

from typing import Protocol, Tuple, List, Dict
from pathlib import Path

class Workflow(Protocol):
    def insuffix(self) -> str:
        pass
    def outsuffix(self) -> str:
        pass
    def process_file(self, infile: str | Path, outfile: str | Path) -> Tuple[bool,Dict]:
        pass

def apply_workflow(inputdir: str | Path, outputdir: str | Path, workflow: Workflow) -> Tuple[bool,List[Path],List[Dict]]:
    errors = []
    processed = []
    rc = True
    indir: Path = Path(inputdir)
    outdir: Path = Path(outputdir)
    files: list[Path] = indir.glob(f'*{workflow.insuffix()}')
    for file in files:
        if file.is_file() and file.suffix == workflow.insuffix():
            outfile = outdir / file.with_suffix(workflow.outsuffix()).name
            result, err = workflow.process_file(file, outfile)
            if result:
                processed.append(str(file))
            else:
                rc = False
                errors.append(err)
    return rc, processed, errors
