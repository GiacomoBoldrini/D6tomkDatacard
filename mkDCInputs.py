import os
import sys
import stat
from array import array
from configparser import ConfigParser
import argparse
from glob import glob
import ROOT
from copy import deepcopy
from itertools import combinations
import math as mt
from makeDummies import *
import numpy as np
import Utils # This is needed to load EFT shape makers
from Utils.dcInputGeneralUtils import * # This is needed to load general utilities functions
from Utils.dcInputHistoUtils import * # This is needed to load general histogram functions
from src.workerLeader import WorkerLeader

def prettyPrintConfig(config, file_dict):

    print(" ---------- @ @ @ @ @ @ @ ----------")
    print(" -------- Generating histos --------")
    print("")

    fmt = '{0:>22}: {1:>1}'
    print(fmt.format("Processes", "{}".format(",".join(k for k in config.getlist("general", "sample")))))
    print(fmt.format("Main output folder", "{}".format(config.get("general", "outfolder"))))
    print(fmt.format("Output sub-folder/s", "{}".format(",".join(config.get("general", "folder_prefix")+k for k in config.getlist("general", "sample")))))
    print(fmt.format("Operator/s", "{}".format(",".join(k for k in config.getlist("eft", "operators")))))
    print(fmt.format("Luminosity", "{}".format(config.get("general", "lumi"))))
    print(fmt.format("Combine Model/s","{}".format(",".join(k for k in config.getlist("eft", "models")))))
    print(fmt.format("Variables/s","{}".format(",".join(k for k in config.getlist("variables", "treenames")))))
    print(fmt.format("Bins for variable/s","{}".format(",".join(k for k in config.getlist("variables", "bins")))))
    print(fmt.format("Binsize for variable/s","{}".format(",".join(k for k in config.getlist("variables", "binsize")))))
    print(fmt.format("Ranges for variable/s", "{}".format(",".join(k for k in config.getlist("variables", "xrange")))))
    print("")
    if len(config.getlist("general", "sample")) < len(config.getlist("eft", "operators")):
        print("WARNING: \t Ignoring operator/s: {}".format(config.getlist("eft", "operators")[len(config.getlist("general", "sample")):]))

    print("---------- Retrieved files ---------")
    print("")

    for process in file_dict:
        print("Process: {}".format(process))
        print("")
        for component in file_dict[process]:
            print("\t component: {}, file: {}".format(component, file_dict[process][component]))
        print("")

    return


def makeHistos(config, file_dict, nThreads):

    vars_ = config.getlist("variables", "treenames")
    bins = [int(i) for i in config.getlist("variables", "bins")]
    binsize = config.getlist("variables", "binsize")
    ranges = convertCfgLists(config.getlist("variables", "xrange"))
    histo_name = config.getlist("variables", "histonames")
    lumi = float(config.get("general", "lumi"))

    fillMissing_ = 0
    if config.has_option("eft", "fillMissing"): fillMissing_ = config.get("eft", "fillMissing")

    dummies = []
    if config.has_option("variables", "makeDummy"): dummies = config.getlist("variables", "makeDummy")
    
    # expand file list to include the dummies
    for component in file_dict.keys():
        for d in dummies:
            file_dict[component][d] = []

    

    if vars_[0] != "*" and len(vars_) != len(bins) or len(vars_) != len(ranges) or len(vars_) != len(binsize):
        sys.exit("[ERROR] var names ({}) and bins({})/binsize({})/xranges({}) do not match. Ignore or take action ...".format(len(vars_),len(bins), len(binsize),len(ranges)))

    cut = "1==1"
    if config.has_option("cuts", "normalcuts"): cut = makeCut(config)    


    WL = WorkerLeader(file_dict, nWorkers=nThreads, dum = dummies)
    WL.setVars(vars_)
    WL.setBins(bins)
    WL.setBinSize(binsize)
    WL.setRanges(ranges)
    WL.setHistoNames(histo_name)
    WL.setLumi(lumi)
    WL.setFillMissing(fillMissing_)
    WL.setCut(cut)
    WL.setBaseDict(file_dict.keys())

    WL.initializeWorkers()

    WL.startWorkers()

    base_histos = WL.joinWorkerDicts()
    
    base_histos = invertHistoDict(base_histos)
    
    return base_histos


if __name__ == "__main__":

    print("""
 ______________________________ 
< From D6EFTStudies to Latinos >
 ------------------------------ 
   \\
    \\
        .--.
       |o_o |
       |:_/ |
      //   \ \\
     (|     | )
    /'\_   _/`\\
    \___)=(___/

    """)

    parser = argparse.ArgumentParser(description='Command line parser for smooth transition to mkDatacrads')
    parser.add_argument('--cfg',     dest='cfg',     help='Config file with infos about samples/variables/...', 
                       required = True)

    parser.add_argument('--v',     dest='verbose',     help='Optional prints with retrieved infos', default = True, action = 'store_false',
                       required = False)

    parser.add_argument('--nt',     dest='nThreads',     help='Number of threads to divide the histogram filling. Default is one', 
                       required = False, default = 1, type=int)

    args = parser.parse_args()

    ROOT.gROOT.SetBatch(1)

    config = ConfigParser(converters={'list': lambda x: [str(i.strip()) for i in x.split(',')]})
    config.read(args.cfg)

    outdir = config.get("general", "outfolder")
    outprefix = config.get("general", "folder_prefix")
    outfile = config.get("general", "outfile")
    models = config.getlist("eft", "models")
    fillMissing_ = 0
    if config.has_option("eft", "fillMissing"): fillMissing_ = config.get("eft", "fillMissing")

    opr = createOpRange(config)

    mkdir(outdir)
    makeActivations(outdir, config) #make scripts for automatic activation of text2workspace and combine

    if len(models) == 0: sys.exit("[ERROR] No model specified, exiting ...")
    
    if config.has_option("files", "module"): 
        exec("import Utils.{} as fileRetriever".format(config.get("files", "module")))
    else:
        import Utils.defaultFileRetrieve as fileRetriever

    fd = fileRetriever.retireve_samples(config)

    if args.verbose: prettyPrintConfig(config, fd)

    base_histo = makeHistos(config, fd, args.nThreads)

    for process in base_histo.keys():

        #Saving, discriminating processes
        outfile_path = outdir + "/" + outprefix + process
        mkdir(outfile_path)
        
        for mod in models:

            exec("import Utils.{}ShapeMaker as ModelShapeMaker".format(mod.replace("-", "")))
            mod_path = outfile_path + "/" + mod
            mkdir(mod_path)
            mkdir(mod_path + "/rootFile/")

            #model_dict = histosToModel(dict((proc,base_histo[proc]) for proc in base_histo.keys() if proc == process), model_type=mod, fillMissing = fillMissing_)
            model_dict = ModelShapeMaker.histosToModel(dict((proc,base_histo[proc]) for proc in base_histo.keys() if proc == process), fillMissing = fillMissing_)
            write(model_dict, outname = mod_path + "/rootFile/" + outfile)

            makeExecRunt(mod, process, config, mod_path)
            makeExecRunc(process, config, mod_path, opr)
            
            print("[INFO] Generating dummies ...")
            if config.get("d_structure", "makeDummy") == "True": makeStructure(model_dict, mod, mod_path)
            if config.get("d_plot", "makeDummy") == "True": makePlot(model_dict, mod, config, mod_path)
            if config.get("d_samples", "makeDummy") == "True": makeSamples(model_dict, mod, config, mod_path)
            if config.get("d_configuration", "makeDummy") == "True": makeConfiguration(model_dict, mod, config, mod_path)
            if config.get("d_alias", "makeDummy") == "True": makeAliases(model_dict, mod, mod_path)
            if config.get("d_cuts", "makeDummy") == "True": makeCuts(model_dict, mod, mod_path)
            if config.get("d_variables", "makeDummy") == "True": makeVariables(model_dict, mod, config, mod_path)
            if config.get("d_nuisances", "makeDummy") == "True": makeNuisances(model_dict, mod, config, mod_path)

    
    print("[INFO] @Done ...")
