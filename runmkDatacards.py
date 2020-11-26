#!/usr/bin/env python
import os
import sys
from glob import glob
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Activate mkDatacards automatically')
    parser.add_argument('--f',     dest='folder',     help='passing this to glob so all directories starting with this will be activated', 
                       required = True)

    parser.add_argument('--m',     dest='mod',     help='models subfolders you want to activate', default = "EFT,EFTNeg,EFTNeg-alt", required = False)

    args = parser.parse_args()

    dl = glob(args.folder + "*")
    models = args.mod.split(",")

    print(". . . @ @ @ Activating @ @ @ . . .")

    base_folder = os.getcwd()

    for f in dl:
        for mod in models:
            activate_path = base_folder + "/" + f + "/" + mod 
            cfg = glob(activate_path + "/configuration*")
            if len(cfg) != 1: sys.exit("[ERROR] No config file in dir {}".format(activate_path))
            os.chdir(activate_path)

            #check on shapes
            shapes = glob(activate_path + "/*/*.root")
            if len(shapes) != 1: sys.exit("[ERROR] Too many shapes detected in fir {}".format(activate_path))

            #everything fine, we launch mkDatacards.py

            os.system("mkDatacards.py --pycfg={} --inputFile={}".format(cfg[0], shapes[0]))
            os.chdir(base_folder)

    print(". . . @ @ @ Done @ @ @ . . .")
    
            

