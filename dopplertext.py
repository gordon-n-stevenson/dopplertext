# -*- coding: utf-8 -*-
"""
dopplertext is a program to convert Doppler parameters stored on DCM images of PW Doppler into a readable, useable format.

Copyright (c) 2018 Gordon Stevenson.

This file is part of dopplertext.

dopplertext is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

dopplertext is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with dopplertext.  If not, see <http://www.gnu.org/licenses/>.

dopplertext Created on Thu July 12 14:41:18 2018

@author: gordon

"""


import skimage.io
import skimage.color
import skimage.util
from skimage.feature import match_template

import pandas as pd
import imghdr

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import pydicom as dicom
except:
    import dicom

import numpy as np

import os, glob, sys

from gooey import Gooey, GooeyParser

@Gooey(default_size=(800,600))
def main():
    parser = GooeyParser(description="GE DICOM Text Parser")
    parser.add_argument('outputfile', help='Select Output Spreadsheet Filename',widget="FileChooser")

    area_threshold_group = parser.add_mutually_exclusive_group(required=True)
    area_threshold_group.add_argument('--inputfile',
                                      help='Input DCM File', widget='FileChooser')
    area_threshold_group.add_argument('--inputdir',
                                      help='Input DCM Directory', widget='DirChooser')

    args = parser.parse_args()
    runFile(args)

def loadImgDict():
    if not os.path.isfile('image_dictionary.pickle'):
        raise NotImplementedError

    with open('image_dictionary.pickle', 'rb') as handle:
        image_dictionary = pickle.load(handle,)
    return image_dictionary

def runFile(args):
    #run depending on if inputfile or inputdir
    inputfile = args.inputfile
    inputdir = args.inputdir

    image_dictionary = loadImgDict()
    output_df = []
    final_df = pd.DataFrame()

    if inputfile is not None:
        print('Analysing Single File....')
        inputfile = inputfile.replace('\\', '/')

        output_df, y_order = getTextFromDCMFile(inputfile, image_dictionary)
        output_df = pd.DataFrame(output_df)
        output_df['FileName'] = [inputfile[inputfile.rfind('/') + 1:] for i in range(len(output_df))]
        output_df = output_df.iloc[np.argsort(y_order)].reset_index(drop=True)

        write_df = pd.DataFrame(output_df)
        print('done!')

    if inputdir is not None:
        file_list = glob.glob(args.inputdir + '/*')
        print('Analysing Each DCM File....')
        final_df = pd.DataFrame([])
        for i,f in enumerate(file_list):
            f= f.replace('\\', '/')
            if isDICOM(f):
                print('Processing....{} of {}'.format(i+1, len(file_list)))
                output_df, y_order = getTextFromDCMFile(f, image_dictionary)

                output_df = pd.DataFrame(output_df)
                output_df['FileName'] = [f[f.rfind('/') + 1:] for i in range(len(output_df))]
                output_df = output_df.iloc[np.argsort(y_order)].reset_index(drop=True)

                final_df = final_df.append(output_df)
        print('...done!')
        final_df = final_df.reindex()
        write_df = final_df

    save_df(write_df, args.outputfile)

def save_df(write_df, outputfile):
    """
    save out a dataframe write_df to a file with path outputfile depending on if excel or csv based on suffix
    """
    print('Saving File....')
    if outputfile.split('.')[1] == 'csv':
        write_df.to_csv(outputfile)

    if outputfile.split('.')[1] == 'xls' or outputfile.split('.')[1] == 'xlsx':
        writer = pd.ExcelWriter(outputfile)
        write_df.to_excel(writer,'Result')
        writer.save()

    write_df.to_clipboard()
    print('...done!')


def isDICOM(file_name):
    #return a bool depending on if this is a DICOM file
    with open(file_name, 'rb') as f:
        hdr = f.read()[128:132]
        return (hdr == b'DICM')

def isJPEG(file_name):
    #return a bool depending on if this is a jpeg file
    if imghdr.what(file_name) == 'jpeg' or imghdr.what(file_name) == 'jpg':
        return True
    return False


def getTextFromDCMFile(file_name, image_dictionary):
    """
    returns a List for Dataframe and the ordering in row order of which statistics are
    provided
    """

    file_name = file_name.replace('\\', '/')
    output_df = []
    if isDICOM(file_name):
        ds = dicom.read_file(file_name)
        image = skimage.color.rgb2gray(ds.pixel_array)
    else:
        raise NotImplementedError

    image = image[50:300, 700:]
    positions = {}
    image = skimage.util.pad(image, [3, 3], 'constant', constant_values=[0])

    for i, d in image_dictionary.items():
        result = match_template(image, d)
        ij = np.unravel_index(np.argmax(result), result.shape)
        x, y = ij[::-1]
        positions[i] = np.argwhere(result > 0.95)

        for p in positions[i]:
            p[0], p[1] = p[0] - 3, p[1] - 3

    y_pos = set()
    for i, d in positions.items():
        for ele in d:
            y_pos.add(ele[0])

    output_df = []
    y_list = list(y_pos)
    for y in y_pos:
        txt = list()
        x_pos = list()

        for i, d in positions.items():
            for ele in d:
                if ele[0] == y:
                    txt.append(i)
                    x_pos.append(ele[1])

        for i, d in positions.items():
            for ele in d:
                if ele[0] == y:
                    if isNumber(i):
                        if distanceFromNum(i, txt, x_pos):
                            txt.remove(i)
                            x_pos.remove(ele[1])

        out_txt = np.array(txt)[np.argsort(x_pos)]
        output_df.append(getText(out_txt).split(' '))

    return output_df, y_list


def getText(out_txt):
    """
    given a list of strings found in a doppler image line, return a complete string with spacing
    formed correctly for gaps between numbers, words, hyphens and periods.
    """
    final_o = ''
    for o in out_txt:
        if o.isdigit():
            final_o += o
        elif o == '.':
            final_o += o
        elif len(o) > 0 and len(final_o) > 1:
            if final_o[-1][0].isdigit():
                final_o += ' ' + o
            else:
                final_o += o + ' '
        else:
            final_o = final_o + o + ' '
    return final_o

def isNumber(i):
    if i in [str(n) for n in np.arange(0,10)]:
        return True
    else:
        return False

def distanceFromNum(i,txt,x_pos):
    if not isNumber(i):
        return False

    num_pos = x_pos[txt.index(i)]
    dist = 100
    for x in x_pos:
        if x != num_pos:
                dist = (np.min([dist,np.abs(num_pos-x)]))
    if dist > 12:
        return True

    return False

if __name__ == '__main__':

    nonbuffered_stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    sys.stdout = nonbuffered_stdout
    main()

    """class argsobj(object):
        def __init__(self):
            self.inputfile = None
            #self.inputfile = "C:\\Users\\gordo\\Google Drive\\GitHub\\DopplerText\\data\\IMG_20180516_1_3.dcm"
            #self.inputdir = None
            self.inputdir = "C:\\Users\\gordo\\Google Drive\\GitHub\\DopplerText\\data"
            self.outputfile = "test1.csv"

    args = argsobj()
    runFile(args)"""