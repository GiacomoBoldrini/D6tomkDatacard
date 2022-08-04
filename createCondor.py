#!/usr/bin/env python
import os
import sys
from glob import glob
#from configparser import ConfigParser
import numpy as np
import stat
from copy import deepcopy
import json

opr = {
    'cW': [-7,7],
    'cHWB': [-40,40],
    'cHl3' : [-20,20],
    'cHq1':[-10,10],
    'cHq3': [-10,10],
    'cll1': [-1,1],
    'cHbox': [-40,30],
    'cHDD' : [-5,5], 
    'cHl1' : [-3,3], 
    'cHW': [-20,20]  ,    
    'cqq11': [-4,4]  ,     
    'cqq1' : [-4,4] ,  
    'cqq31':  [-4,4] ,   
    'cqq3':  [-4,4] ,   
    'cll':   [-200,200]   
}

poir = deepcopy(opr) 

def read_results(rf):
    
    res = {}
    f = open(rf, "r")
    content = f.readlines()[2:-2]
    c = [i.split("\t") for i in content] #0: op #1: var #2: 1sigma #3: 2 sigma
    for i in c:
        op = i[0].strip(" ")
        
        #1s
        os = json.loads(i[2])
        #2s
        ts = json.loads(i[3])
        res[op] = {}
        res[op]["1s"] = os
        res[op]["2s"] = ts
        
    return res

def reaOPranges(txt):
    res  = read_results(txt)
    for op in  res.keys():
       poir[op] = res[op]['2s']
    return

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
    if len(pois) == 0:
       pois = []
       ranges = ":".join("k_"+op+"={},{}".format(opr[op][0],opr[op][1]) for op in ops)
    else:
       ranges = ":".join("k_"+op+"={},{}".format(poir[op][0], poir[op][1]) for op in pois if op not in ops)
       ranges += ":" + ":".join("k_"+op+"={},{}".format(opr[op][0],opr[op][1]) for op in ops)
       ranges += ":r=1,1"
    
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

    if len(pois) == 0:
        to_w = "text2workspace.py  {}/datacard.txt  -P HiggsAnalysis.AnalyticAnomalousCoupling.AnomalousCoupling{}:analiticAnomalousCoupling{}  -o   model.root \
        --X-allow-no-signal --PO eftOperators={}".format(path, mod, mod, ",".join(op for op in ops))        
        if "alt" in model: to_w += " --PO  eftAlternative"
        ssf = ""
    else:
        the_ops = np.unique(ops + pois)
        to_w = "text2workspace.py  {}/datacard.txt  -P HiggsAnalysis.AnalyticAnomalousCoupling.AnomalousCoupling{}:analiticAnomalousCoupling{}  -o   model.root \
        --X-allow-no-signal --PO eftOperators={}".format(path, mod, mod, ",".join(op for op in the_ops))        
        if "alt" in model: to_w += " --PO  eftAlternative"
        ssf = "--saveSpecifiedFunc={}".format(",".join("k_"+op for op in pois))
    
    
    
    to_w += "\n"
    f.write(to_w)

    f.write("#-----------------------------------\n")
    to_w = "combine -M MultiDimFit model.root  --algo=grid --points {}  -m 125   -t -1 --robustFit=1 --setRobustFitTolerance=0.3 --cminDefaultMinimizerStrategy=0 --X-rtd=MINIMIZER_analytic --X-rtd MINIMIZER_MaxCalls=9999999 --cminFallbackAlgo Minuit2,Migrad,0:0.3 --stepSize=0.001 --setRobustFitStrategy=1 --robustHesse=1  --maxFailedSteps 100 --X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NEVER_GIVE_UP --X-rtd FITTER_BOUND --redefineSignalPOIs {}     --freezeParameters r      --setParameters r=1    --setParameterRanges {}  --floatOtherPOIs={} {} --verbose 3".format(npoints, ",".join("k_"+op for op in ops), ranges, floatOtherPOI,ssf)
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

    if len(sys.argv) < 4: sys.exit("[ERROR] Provide folder path, prefix, process name, [npoints = 20000], [models = EFTNeg], [flavour = microcentury], [floatOtherPOI = 0], [ pois = Default ] [poisRanges =  results.txt] after running mkDatacards.py ...")

    subf = glob(sys.argv[1] + "/*/")
    prefix = sys.argv[2]
    process = sys.argv[3]
    npoints = 20000
    models = ["EFTNeg"]
    flavour = "microcentury"
    floatOtherPOI = 0
    pois = None
    if len(sys.argv) > 4:
        npoints = sys.argv[4]
    if len(sys.argv) > 5:
        models = sys.argv[5].split(",")
    if len(sys.argv) > 6:
        flavour = sys.argv[6]
    if len(sys.argv) > 7:
        floatOtherPOI = sys.argv[7]
    if len(sys.argv) > 8:
        pois = sys.argv[8].split(",")
    if len(sys.argv) > 9:
        res = sys.argv[9]
        reaOPranges(res)

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
                makeT2WFitCondor(v, model, ops, opr, npoints, floatOtherPOI, pois)
                makeBatchSub(v, flavour)

                all_sub_paths.append(os.path.abspath(v))

    makeSub(sys.argv[1], all_sub_paths)

    print(". . . @ @ @ Done @ @ @ . . .")





