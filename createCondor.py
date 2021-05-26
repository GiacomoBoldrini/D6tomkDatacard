#!/usr/bin/env python
import os
import sys
from glob import glob
#from configparser import ConfigParser
import numpy as np
import stat
import argparse

"""
opr = {
    'cW': [-1,1],
    'cHWB': [-20,20],
    'cHl3' : [-2,2],
    'cHq1':[-4,4],
    'cHq3': [-4,4],
    'cll1': [-2,2],
    'cHbox': [-20,20],
    'cHDD' : [-20,20], 
    'cHl1' : [-20,20], 
    'cHW': [-8,8]  ,    
    'cqq11': [-2,2]  ,     
    'cqq1' : [-2,2] ,  
    'cqq31':  [-2,2] ,   
    'cqq3':  [-3,3] ,   
    'cll':   [-5,5]   
}
"""
opr = {
    'cW': [-1,1],
    'cHWB': [-2,2],
    'cHl3' : [-1,1],
    'cHq1':[-3,3],
    'cHq3': [-1,1],
    'cll1': [-1,1],
    'cHbox': [-10,10],
    'cHDD' : [-10,10], 
    'cHl1' : [-1,1], 
    'cHW': [-8,8]  ,    
    'cqq11': [-1,1]  ,     
    'cqq1' : [-1,1] ,  
    'cqq31':  [-1,1] ,   
    'cqq3':  [-1,1] ,   
    'cll':   [-5,5]   
}

def redemensionOpinput(config):
    sample = config.getlist("general", "sample")
    ops = config.getlist("eft", "operators")

    ops = [i[1:-1].split(":") for i in ops]
    ops = [list(map(str, sublist)) for sublist in ops]

    if len(sample) > len(ops) and len(ops) == 1:
        return ops*len(samples)

    elif len(sample) > len(ops) and len(ops) == 1:
        sys.exit("[ERROR] Ambiguity in the definition of samples and op per sample")
    
    else:
        return ops

def createOpRange(config):

    if not config.has_option("eft", "fitranges"): 
        all_ops = np.unique([item for subs in redemensionOpinput(config) for item in subs])
        return dict((i, [-10,10]) for i in all_ops)
    
    else:
        or_ = config.getlist("eft", "fitranges")
        return dict( (i.split(":")[0], [ float(i.split(":")[1]) , float(i.split(":")[2]) ] ) for i in or_ )

def makeT2WFitCondor(path, model, ops, opr, npoints, floatOtherPOI, pois):
    path = os.path.abspath(path)

    modeltot2w = {
        "EFT": "EFT",
        "EFTNeg": "EFTNegative",
        "EFTNeg-alt": "EFTNegative",
        "EFTNeg-overall": "EFTNegative",
        "EFTNeg-alt-overall": "EFTNegative"
    }

    mod = modeltot2w[model]

    if pois == None:
       ranges = ":".join("k_"+op+"={},{}".format(opr[op][0],opr[op][1]) for op in ops)
    else:
       ranges = ":".join("k_"+op+"={},{}".format(-5,5) for op in pois if op not in ops)
       ranges += ":" + ":".join("k_"+op+"={},{}".format(opr[op][0],opr[op][1]) for op in ops)

    f = open(path + "/submit.sh", 'w')
    f.write("#!/bin/sh\n")
    f.write("#-----------------------------------\n")
    f.write("#     Automatically generated       # \n")
    f.write("#        by mkDCInputs.py           # \n")
    f.write("#-----------------------------------\n")
    f.write("\n\n\n")

    f.write("source /cvmfs/cms.cern.ch/cmsset_default.sh\n")
    f.write("cd {}\n".format(path))
    f.write("eval `scram run -sh`\ncd -\n")
    f.write("cp -r {} ./\n".format(path))

    if pois == None:
        to_w = "text2workspace.py  {}/datacard.txt  -P HiggsAnalysis.AnalyticAnomalousCoupling.AnomalousCoupling{}:analiticAnomalousCoupling{}  -o   model.root \
        --X-allow-no-signal --PO eftOperators={}".format(path, mod, mod, ",".join(op for op in ops))        
        if "alt" in model: to_w += " --PO  eftAlternative"
    else:
        to_w = "text2workspace.py  {}/datacard.txt  -P HiggsAnalysis.AnalyticAnomalousCoupling.AnomalousCoupling{}:analiticAnomalousCoupling{}  -o   model.root \
        --X-allow-no-signal --PO eftOperators={}".format(path, mod, mod, ",".join(op for op in pois))        
        if "alt" in model: to_w += " --PO  eftAlternative"

    
    to_w += "\n"
    f.write(to_w)

    f.write("#-----------------------------------\n")
    if pois == None:
        to_w = "combine -M MultiDimFit model.root  --algo=grid --points {}  -m 125   -t -1   --robustFit=1 --X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NEVER_GIVE_UP --X-rtd FITTER_BOUND --redefineSignalPOIs {}     --freezeParameters r      --setParameters r=1    --setParameterRanges {}  --verbose -1".format(npoints, ",".join("k_"+op for op in ops), ranges)
    else:
        to_w = "combine -M MultiDimFit model.root  --algo=grid --points {}  -m 125   -t -1   --robustFit=1 --X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NEVER_GIVE_UP --X-rtd FITTER_BOUND --redefineSignalPOIs {}     --freezeParameters r      --setParameters r=1    --setParameterRanges {}  --floatOtherPOI={} --saveSpecifiedFunc={}  --maxFailedSteps 100 --verbose 3".format(npoints, ",".join("k_"+op for op in ops), ranges, floatOtherPOI, ",".join("k_"+op for op in pois))
    to_w += "\n"
    f.write(to_w)
    f.write("cp model.root {}\n".format(path))
    f.write("cp higgsCombineTest.MultiDimFit.mH125.root {}\n".format(path))
    
    f.close()

    st = os.stat(path + "/submit.sh")
    os.chmod(path + "/submit.sh", st.st_mode | stat.S_IEXEC)

def makeBatchSub(path, flavour):
    path = os.path.abspath(path)
    f = open(path + "/submit.sub", 'w')
    f.write("executable = {}/submit.sh\n".format(path))
    f.write("output     = {}/submit.out\n".format(path))
    f.write("error      = {}/submit.err\n".format(path))
    f.write("log        = {}/submit.log\n".format(path))
    f.write("queue 1\n")
    f.write('+JobFlavour = "{}"\n'.format(flavour))
    f.close()

def makeSub(path_, all_paths):

    f = open(path_ + "/submit_all.sh", 'w')
    for path in all_paths:
        f.write("condor_submit {}/submit.sub\n".format(path))
        f.write("# ------------------------------------------------------ #\n")

    f.close()
    st = os.stat(path_ + "/submit_all.sh")
    os.chmod(path_ + "/submit_all.sh", st.st_mode | stat.S_IEXEC)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('-b',     dest='base',     help='Base folder path', required = True)
    parser.add_argument('--prefix',     dest='prefix',     help='Prefix', required = True)
    parser.add_argument('--proc',     dest='proc',     help='Process name', required = True)
    parser.add_argument('-N',     dest='points',     help='Number of points', required = False, default=20000, type=int)
    parser.add_argument('--models',     dest='models',     help='Comma separated list of models', required = False, default='EFTNeg')
    parser.add_argument('-Q',     dest='queue',     help='Queue flavour', required = False, default='microcentury')
    parser.add_argument('--floatOtherPOI',     dest='floatotherpoi',     help='floatOtherPOI', required = False, default=0)
    parser.add_argument('--pois',     dest='pois',     help='pois', required = False)
    parser.add_argument('--compute',     dest='compute',     help='Comma separated list of operators to be computed', required = False)
    args = parser.parse_args()

    subf = glob(args.base + "/*/")
    prefix = args.prefix
    process = args.proc
    npoints = args.points
    models = args.models.split(',')
    flavour = args.queue
    floatOtherPOI = args.floatotherpoi
    if args.pois is None:
        pois = None
    else:
        pois = args.pois.split(',')
    if args.compute is None:
        to_compute = None
    else:
        to_compute = args.compute.split(',')
    all_sub_paths = []

    print(". . . @ @ @ Retrieving folders @ @ @ . . .")
    
    for s in subf:
        subfolder = s.split("/")[-2]
        prc = subfolder.split(prefix+"_")[-1]
        ops = prc.split(process + "_")[-1]
        ops = ops.split("_")

        if to_compute is not None:
            if len(set(to_compute).intersection(set(ops))) == 0:
                print(">>> skipping operator {0}".format(ops))
                continue
               
        for model in models:
            vars_ = glob(s + "/" + model + "/datacards/" + prc + "/*/")
            print("[INFO] Running: {}, model: {}, tot fits: {}".format(s, model, len(vars_)))
            for v in vars_:
                makeT2WFitCondor(v, model, ops, opr, npoints, floatOtherPOI, pois)
                makeBatchSub(v, flavour)

                all_sub_paths.append(os.path.abspath(v))

    makeSub(args.base, all_sub_paths)

    print(". . . @ @ @ Done @ @ @ . . .")





