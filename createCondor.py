#!/usr/bin/env python
import os
import sys
from glob import glob
#from configparser import ConfigParser
import numpy as np
import stat

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

def makeT2WFitCondor(path, model, ops, opr, npoints):
    path = os.path.abspath(path)

    modeltot2w = {
        "EFT": "EFT",
        "EFTNeg": "EFTNegative",
        "EFTNeg-alt": "EFTNegative"
    }

    mod = modeltot2w[model]
    ranges = ":".join("k_"+op+"={},{}".format(opr[op][0],opr[op][1]) for op in ops)

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

    to_w = "text2workspace.py  {}/datacard.txt  -P HiggsAnalysis.AnalyticAnomalousCoupling.AnomalousCoupling{}:analiticAnomalousCoupling{}  -o   model.root \
    --X-allow-no-signal --PO eftOperators={}".format(path, mod, mod, ",".join(op for op in ops))        
    if "alt" in model: to_w += " --PO  eftAlternative"
    
    to_w += "\n"
    f.write(to_w)

    f.write("#-----------------------------------\n")
    to_w = "combine -M MultiDimFit model.root  --algo=grid --points {}  -m 125   -t -1   --robustFit=1 --X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NEVER_GIVE_UP --X-rtd FITTER_BOUND --redefineSignalPOIs {}     --freezeParameters r      --setParameters r=1    --setParameterRanges {}  --verbose -1".format(npoints, ",".join("k_"+op for op in ops), ranges)
    to_w += "\n"
    f.write(to_w)
    f.write("cp model.root {}\n".format(path))
    f.write("cp higgsCombineTest.MultiDimFit.mH125.root {}\n".format(path))
    
    f.close()

    st = os.stat(path + "/submit.sh")
    os.chmod(path + "/submit.sh", st.st_mode | stat.S_IEXEC)

def makeBatchSub(path):
    path = os.path.abspath(path)
    f = open(path + "/submit.sub", 'w')
    f.write("executable = {}/submit.sh\n".format(path))
    f.write("output     = {}/submit.out\n".format(path))
    f.write("error      = {}/submit.err\n".format(path))
    f.write("log        = {}/submit.log\n".format(path))
    f.write("queue 1\n")
    f.write("+JobFlavour = 'microcentury'\n")
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

    """
    if len(sys.argv) < 5: sys.exit("[ERROR] Provide folder path, prefix, process name, config file, after running mkDatacards.py ...")

    subf = glob(sys.argv[1] + "/*/")
    prefix = sys.argv[2]
    process = sys.argv[3]
    cfg = sys.argv[4]
    npoints = 20000
    if len(sys.argv) > 5:
        npoints = sys.argv[5]

    config = ConfigParser(converters={'list': lambda x: [str(i.strip()) for i in x.split(',')]})
    config.read(cfg)
    """

    if len(sys.argv) < 4: sys.exit("[ERROR] Provide folder path, prefix, process name, [npoints = 20000] after running mkDatacards.py ...")

    subf = glob(sys.argv[1] + "/*/")
    prefix = sys.argv[2]
    process = sys.argv[3]
    npoints = 20000
    models = ["EFTNeg"]
    if len(sys.argv) > 4:
        npoints = sys.argv[4]
    if len(sys.argv) > 5:
        models = sys.argv[5].split(",")
    all_sub_paths = []

    print(". . . @ @ @ Retrieving folders @ @ @ . . .")
    
    for s in subf:
        subfolder = s.split("/")[-2]
        prc = subfolder.split(prefix+"_")[-1]
        ops = prc.split(process + "_")[-1]
        ops = ops.split("_")
               
        for model in models:
            vars_ = glob(s + "/" + model + "/datacards/" + prc + "/*/")
            print("[INFO] Running: {}, model: {}, tot fits: {}".format(s, model, len(vars_)))
            for v in vars_:
                makeT2WFitCondor(v, model, ops, opr, npoints)
                makeBatchSub(v)

                all_sub_paths.append(os.path.abspath(v))

    makeSub(sys.argv[1], all_sub_paths)

    print(". . . @ @ @ Done @ @ @ . . .")





