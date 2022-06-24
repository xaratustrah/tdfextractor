#!/usr/bin/env python
'''
extracts data from TDF file structure
needs BDIO library

xaratustrah 2022

'''

import numpy as np
import os
import argparse
import types
import uproot3
import uproot3_methods.classes.TH1

from bdio.bdio import BDIOReader


# ------------ MAIN ----------------------------

def xytdf(filename):
    # Thanks to @DFreireF @ GitHUB

    # We have 1 line with all the data/ info, that's what is called "stream"
    stream = BDIOReader(filename)  # bdio.py
    # The stream is composed of blocks, with get-directory we get the basic INFO of the blocks
    # not the data, just the position, tag, size...
    blocks = stream.get_directory()  # bdio.py
    for block in blocks:
        # we look for the block that we want to get the data
        if block.is_xycurve_block():  # block.py
            # We move in our "line" (stream) to the position in which starts our block
            stream.seek(block.get_pos())
            # We create a Block object of the type xycurve_block
            nb = stream.next_block()  # bdio.py
            # Each type of block has it owns methods for getting the data
            x = nb.get_xvalues()  # xycurveblock.py
            y = nb.get_yvalues()  # xycurveblock.py
    return x, y


def write_to_root(x, y, filename, title=''):
    # x and y are lists
    class MyTH1(uproot3_methods.classes.TH1.Methods, list):
        def __init__(self, low, high, values, title=''):
            self._fXaxis = types.SimpleNamespace()
            self._fXaxis._fNbins = len(values)
            self._fXaxis._fXmin = low
            self._fXaxis._fXmax = high
            values.insert(0, 0)
            values.append(0)
            for x in values:
                self.append(float(x))
            self._fTitle = title
            self._classname = "TH1F"

    th1f = MyTH1(x[0], x[-1], y, title=title)
    file = uproot3.recreate(filename + '.root', compression=uproot3.ZLIB(4))
    file["th1f"] = th1f


def write_to_csv(x, y, filename, title=''):
    # x and y are lists
    x, y = np.array(x), np.array(y)
    a = np.concatenate((x, y))
    a = np.reshape(a, (2, -1)).T
    np.savetxt(filename + '.csv', a, delimiter='|')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='+', type=str,
                        help='Name of the input files.')
    parser.add_argument('-o', '--outdir', type=str, default='.',
                        help='Output directory.')
    parser.add_argument('-r', '--root', action='store_true',
                        help='Save as ROOT.')
    parser.add_argument('-c', '--csv', action='store_true',
                        help='Save as CSV.')

    args = parser.parse_args()

    # handle trailing slash properly
    outfilepath = os.path.join(args.outdir, '')

    for filename in args.filenames:
        if not os.path.isfile(filename):
            print('File not found: {}'.format(filename))
            exit()
        x, y = xytdf(filename)
        outfilename = outfilepath + os.path.basename(filename)

    if args.root:
        write_to_root(x, y, outfilename)

    if args.csv:
        write_to_csv(x, y, outfilename)

    if not args.root and not args.csv:
        print('Please specify output format.')
    # ----------------------------------------


if __name__ == '__main__':
    main()
