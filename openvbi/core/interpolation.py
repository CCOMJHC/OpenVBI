## \file interpolation.py
# \brief Simple (linear) interpolation structure for arbitrary numbers of dependent variables
#
# Most sources have asynchronous data packets for depths, positions, and other variables, but we need
# to be able to match up positions and real-world times with the observations in order to make
# them into something useful.  Since each data packet also only has a timestamp for when it was
# received (according to the millisecond elapsed-time counter on the logger, or an equivalent),
# we need to be able to interpolate between elapsed times and real-world times available in
# certain packets.  This file provides a simple linear interpolation class that can be used to
# establish a relationship between a single independent variable, and one or more dependent
# variables, and then interpolate to points in a NumPy vector for the independent variable.
#
# Copyright 2023 OpenVBI Project.  All Rights Reserved.
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

from collections.abc import Collection
from typing import Any

import numpy as np

## Exception to indicate that the variable requested in the InterpTable does not exist
class NoSuchVariable(Exception):
    pass

## Exception to indicate that there are insufficient number of values in an add_points() call
class NotEnoughValues(Exception):
    pass

## Simple linear interpolation table for one or more dependent variables
#
# In order to establish real-world times for the packets, and their positions, we need to
# interpolate the asynchronous packets for this information against the elapsed times for
# the variables on interest.  This class provides facilities to register one or more named
# dependent variables (and automatically adds an independent variable), which can be added
# to as data becomes available.  Interpolation can then be done at given time points against
# one or more of the dependent variables, returned as a list of NumPy arrays.

class InterpTable:
    ## Constructor, specifying the names of the dependent variables to be interpolated
    #
    # This sets up for interpolation of an independent variable (added automatically) against
    # the named dependent variables.
    #
    # \param vars   (Collection[str]) list|tuple|etc. of the names of the dependent variables to manage
    def __init__(self, vars: Collection[str]) -> None:
        # Each dependent variable is stored as a dict mapping independent variable datum to dependent variable datum
        self.vars: dict[str, dict[int|float, Any]] = {}
        # Track all independent variables
        self.indep_var = []
        for v in vars:
            self.vars[v] = {}
    
    ## Add a data point to a single dependent variable
    #
    # Add a single data point to a single dependent variable.
    #
    # \param ind    Independent variable value to add to the array
    # \param var    Name of the dependent variable to update
    # \param value  Value to add to the dependent variable array
    def add_point(self, ind: float, var: str, value: float) -> None:
        if var not in self.vars:
            raise NoSuchVariable()
        self.indep_var.append(ind)
        self.vars[var][ind] = value
    
    ## Add a data point to multiple dependent variables simultaneously
    #
    # Add a data point for one or more dependent variables at a common independent variable
    # point.
    #
    # \param ind    Independent variable value to add to the array
    # \param vars   list|tuple of names of the dependent variables to update
    # \param values list|tuple of values to update for the named dependent variables, in the same order
    def add_points(self, ind: float, vars: list[str]|tuple[str], values: list[float]|tuple[str]) -> None:
        for var in vars:
            if var not in self.vars:
                raise NoSuchVariable()
        if len(vars) != len(values):
            raise NotEnoughValues()
        self.indep_var.append(ind)
        for n in range(len(vars)):
            self.vars[vars[n]][ind] = values[n]

    ## Interpolate one or more dependent variables at an array of independent variable values
    #
    # Construct a linear interpolation of the named dependent variables at the given array
    # of independent variable values.
    #
    # \param yvars  Collection list|tuple|etc. of names of the dependent variables to interpolate
    # \param x      NumPy array of the independent variable points at which to interpolate
    # \return List of NumPy arrays for the named dependent variables, in the same order
    def interpolate(self, yvars: Collection[str], x: np.ndarray) -> list[np.ndarray]:
        for yvar in yvars:
            if yvar not in self.vars:
                raise NoSuchVariable()
        rtn = []
        for yvar in yvars:
            rtn.append(np.interp(x, self.indep_var, self.var(yvar)))
        return rtn
    
    ## Determine the number of points in the independent variable array
    #
    # This provides the count of points that have been added to the table for interpolation.  Since
    # you have to add an independent variable point for each dependent variable point(s) added, this
    # should be the total number of points in the table.
    #
    # \return Number of points in the interpolation table
    def n_points(self) -> int:
        return len(self.indep_var)
    
    ## Accessor for the array of points for a named variable
    #
    # This provides checked access to one of the dependent variables stored in the array.  This method
    # generates an array of the same length as the independent variable, with values from var, where var
    # has valid data for that ind, or None. This way, all variables returned will be of the same length,
    # allowing interpolation and combination of multiple dependent variables into a single
    # ndarray/dataframe.
    #
    # \param name   Name of the dependent variable to extract
    # \return NumPy array for the dependent variable named
    def var(self, name: str) -> np.ndarray:
        if name not in self.vars:
            raise NoSuchVariable()
        dst_array = []
        var_data = self.vars[name]
        for ind in self.indep_var:
            dst_array.append(var_data.get(ind, None))

        return np.array(dst_array)
    
    ## Accessor for the array of points for the independent variable
    #
    # This provides access to the independent variable array, without exposing the specifics
    # of how this is stored.
    #
    # \return NumPy array for the independent variable
    def ind(self) -> np.ndarray:
        return np.array(self.indep_var)
