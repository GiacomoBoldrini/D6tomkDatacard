#!/usr/bin/env python
from glob import glob
import os
import argparse
from itertools import combinations

def mkdir(p):
   try:
      os.mkdir(p)
   except:
      return 

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Command line parser for model testing')
    parser.add_argument('--baseFolder',     dest='baseFolder',     help='Base folder containing all the shapes and op e.g. OSWW_1op', required = True)
    parser.add_argument('--prefix',     dest='prefix',     help='base folder prefix name', required = False, default = "to_Latinos")
    parser.add_argument('--models',     dest='models',     help='models to be extracted', required = False, default = "EFTNeg")
    parser.add_argument('--process',     dest='process',     help='base folder process name', required = True)
    parser.add_argument('--nPois',     dest='nPois',     help='Number of oprators for the fit default is 1', required = False, default="1")
    parser.add_argument('--outfolder',     dest='outfolder',     help='outfolder name', required = True)

    args = parser.parse_args()

    baseFolder = args.baseFolder
    prefix = args.prefix
    process = args.process
    out = args.outfolder
    models = args.models.split(",")

    nPois = int(args.nPois)

    subf = glob(baseFolder + "/" + prefix + "_" + process + "*")
    if len(subf) != 1: 
        print("[ERROR] target folder contains multiple subdirectories, this script only works with an overall folder containing all ops and all the shapes to be profiled")
        sys.exit(0)

    ops = subf[0].split("/")[-1].split(prefix + "_" + process + "_")[-1].split("_")

    mkdir(out)

    ops_combo = list(combinations(ops, nPois))

    for op in ops_combo:
        
        op_ = "_".join(i for i in op)
        mkdir(out + "/" + prefix + "_" + process + "_" + op_)

        for model in models:
            os.system("cp -r " + subf[0] + "/{} ".format(model) +  out + "/" + prefix + "_" + process + "_" + op_)

        

