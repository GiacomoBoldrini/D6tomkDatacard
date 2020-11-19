import os
import sys
from configparser import ConfigParser
import argparse
from glob import glob
import ROOT
from copy import deepcopy
from itertools import combinations
import math as mt
from makeDummies import *
import warnings

def convertCfgLists(list_):
    list_ = [i[1:-1].split(":") for i in list_]
    return [list(map(float, sublist)) for sublist in list_]
    

def get_model_syntax(comp_name):

    d = { "SM": "sm",
          "LI": "lin_",
          "QU": "quad_",
          "INT": "lin_mixed_",
          "SM_LI_QU": "sm_lin_quad_",
          "QU_INT": "quad_mixed_",
          "SM_LI_QU_INT": "sm_lin_quad_mixed_",
        }

    type_ = comp_name.split("_c")[0]
    newName = d[type_]

    if type_ != "SM": #need to account for operators here
        ops = comp_name.split(type_ + "_")[1]
        if len(ops.split("_")) == 2: 
            ops = ops.split("_")
            newName += ops[0] + "_" + ops[1]
        else:
            newName += ops

    return newName

def get_var_list(h_dict):
    vars_ = []
    for s in h_dict.keys():
        for comp in h_dict[s].keys():
            vars_.append(h_dict[s][comp].keys())
    
    check = True
    for i in range(len(vars_[:-1])):
        if vars_[i] != vars_[i+1]: check = False

    if check: return vars_[0]
    else: sys.exit("[ERROR] Vars do not coincide between the various samples. Check .cfg ...")


def cleanNames(model_dict):
    
    for sample in model_dict.keys():
        for var in model_dict[sample].keys():
            tb_clear = model_dict[sample][var].keys()
            for c in model_dict[sample][var]:
                if c in tb_clear: #after popping we will modify the keys 
                    name = get_model_syntax(c)
                    model_dict[sample][var][name] = model_dict[sample][var].pop(c)
                else:
                    continue

    return model_dict
                

def histosToModel(histo_dict, model_type = "EFT"):
    if model_type == "EFT":
        print("[INFO]: Converting base model to EFT...")
        return histo_dict #identity

    if model_type == "EFTNeg":

        print("[INFO]: Converting base model to EFTNeg ...")
        
        eft_neg_dict = {}

        for sample in histo_dict.keys():
            eft_neg_dict[sample] = {}
            for var in histo_dict[sample].keys():
                eft_neg_dict[sample][var] = {}

                components = histo_dict[sample][var].keys()
                linear = [i for i in components if "LI" in i]
                quadratic = [i for i in components if "QU" in i]
                mixed = [i for i in components if "IN" in i]
                sm = [i for i in components if "SM" in i]

                if len(mixed) != mt.factorial(len(linear)) / (mt.factorial(2) * mt.factorial(len(linear)-2)) or len(sm) != 1: 
                    sys.exit("[ERROR] errors in the combinatorial, check inputs ...")

                eft_neg_dict[sample][var][sm[0]] = histo_dict[sample][var][sm[0]]

                #store linear and quadratic fine
                for q in quadratic:
                    eft_neg_dict[sample][var][q] = histo_dict[sample][var][q]


                ops = [i.split("LI_")[1] for i in linear]
                for op in ops:
                    new_sm = histo_dict[sample][var][sm[0]].Clone(var + "_" + "SM_LI_QU_{}".format(op))
                    new_sm.SetDirectory(0)
                    new_sm.Add(histo_dict[sample][var]["LI_{}".format(op)])
                    new_sm.Add(histo_dict[sample][var]["QU_{}".format(op)])
                    eft_neg_dict[sample][var]["SM_LI_QU_{}".format(op)] = new_sm

                op_comb = [(i.split("IN_")[1]).split("_") for i in components if "IN" in i]
                for o_c in op_comb:
                    new_sm = histo_dict[sample][var][sm[0]].Clone(var + "_" + "SM_LI_QU_INT_{}_{}".format(o_c[0], o_c[1]))
                    new_sm.SetDirectory(0)
                    new_sm.Add(histo_dict[sample][var]["LI_{}".format(o_c[0])])
                    new_sm.Add(histo_dict[sample][var]["QU_{}".format(o_c[0])])
                    new_sm.Add(histo_dict[sample][var]["LI_{}".format(o_c[1])])
                    new_sm.Add(histo_dict[sample][var]["QU_{}".format(o_c[1])])
                    new_sm.Add(histo_dict[sample][var]["IN_{}_{}".format(o_c[0], o_c[1])])
                    eft_neg_dict[sample][var]["SM_LI_QU_INT_{}_{}".format(o_c[0], o_c[1])] = new_sm
        
        return cleanNames(eft_neg_dict)


    if model_type == "EFTNeg-alt":

        print("[INFO]: Converting base model to EFTNeg-alt ...")

        eft_negalt_dict = {}

        for sample in histo_dict.keys():

            eft_negalt_dict[sample] = {}
            for var in histo_dict[sample].keys():

                eft_negalt_dict[sample][var] = {}

                components = histo_dict[sample][var]
                linear = [i for i in components if "LI" in i]
                quadratic = [i for i in components if "QU" in i]
                mixed = [i for i in components if "IN" in i]
                sm = [i for i in components if "SM" in i]
                if len(mixed) != mt.factorial(len(linear)) / (mt.factorial(2) * mt.factorial(len(linear)-2)) or len(sm) != 1: 
                    sys.exit("[ERROR] errors in the combinatorial, check inputs ...")

                eft_negalt_dict[sample][var][sm[0]] = histo_dict[sample][var][sm[0]]

                #store linear and quadratic fine
                for q in quadratic:
                    eft_negalt_dict[sample][var][q] = histo_dict[sample][var][q]
        
                ops = [i.split("LI_")[1] for i in linear]
                for op in ops:
                    new_sm = histo_dict[sample][var][sm[0]].Clone(var + "_" + "SM_LI_QU_{}".format(op))
                    new_sm.SetDirectory(0)
                    new_sm.Add(histo_dict[sample][var]["LI_{}".format(op)])
                    new_sm.Add(histo_dict[sample][var]["QU_{}".format(op)])
                    eft_negalt_dict[sample][var]["SM_LI_QU_{}".format(op)] = new_sm

                op_comb = [(i.split("IN_")[1]).split("_") for i in components if "IN" in i]
                for o_c in op_comb:
                    new_sm = histo_dict[sample][var][sm[0]].Clone(var + "_" + "QU_INT_{}_{}".format(o_c[0], o_c[1]))
                    new_sm.SetDirectory(0)
                    new_sm.Add(histo_dict[sample][var]["QU_{}".format(o_c[0])])
                    new_sm.Add(histo_dict[sample][var]["QU_{}".format(o_c[1])])
                    new_sm.Add(histo_dict[sample][var]["IN_{}_{}".format(o_c[0], o_c[1])])
                    eft_negalt_dict[sample][var]["QU_INT_{}_{}".format(o_c[0], o_c[1])] = new_sm

        return cleanNames(eft_negalt_dict)


def setNamesToKeys(h_dict):
    for sample in h_dict.keys():
        for var in h_dict[sample].keys():
            for c in h_dict[sample][var]:
                h_dict[sample][var][c].SetName("histo_" + c)
    return h_dict


def write(h_dict, outname = "out.root"):

    #Naming convention
    h_dict = setNamesToKeys(h_dict)

    for sample in h_dict.keys():
        print("[INFO] Writing histos to {} ...".format(sample + "_" + outname))
        f_out = ROOT.TFile(outname, "RECREATE")
        f_out.mkdir(sample + "/")
        
        for var in h_dict[sample].keys():
            f_out.mkdir(sample + "/" + var + "/")
            f_out.cd(sample + "/" + var + "/")

            for c in h_dict[sample][var]:
                histo_name = "histo_{}".format(c)
                h_dict[sample][var][c].Write(histo_name)

    f_out.Write()
    f_out.Close()


def retireve_samples(config):

    print("[INFO] Retrieving samples ...")
    section = "ntuples"
    sample = config.getlist("general", "sample")
    folders = config.getlist(section, "folder")
    ops = config.getlist("eft", "operators")
    int_ = len(ops) > 1

    comb = list(combinations(ops, 2))
    comb2 = [(i[1],i[0]) for i in comb] #reverse in case of wrong ordering

    file_dict = dict.fromkeys(sample)

    for s in sample:
        file_dict[s] = {}

        #scan simple ops
        for op in ops:
            file_dict[s]
            file_dict[s]["QU_{}".format(op)] = []
            file_dict[s]["LI_{}".format(op)] = []


            for folder in folders:
                files = glob(folder + "/*_" + s + "_" + op + "*.root")
                for file_ in files:
                    if "QU" in file_: file_dict[s]["QU_{}".format(op)].append(file_)
                    if "LI" in file_: file_dict[s]["LI_{}".format(op)].append(file_)

                        
        #scan interference if present
        if int_:
            for c1, c2 in zip(comb, comb2):
                file_dict[s]["IN_{}_{}".format(c1[0], c1[1])] = []
                file_dict[s]["IN_{}_{}".format(c2[0], c2[1])] = []

                for folder in folders:
                    #either cG_cGtil or cGtil_cG, not both (repetition should be avoided)
                    files1 = glob(folder + "/*_" + s + "_{}_{}_".format(c1[0], c1[1]) + "*.root")
                    files2 = glob(folder + "/*_" + s + "_{}_{}_".format(c2[0], c2[1]) + "*.root")


                    if len(files1) != 0 and len(files2) == 0: 
                        files = files1
                        c = c1
                        del file_dict[s]["IN_{}_{}".format(c2[0], c2[1])]
                    else: 
                        files = files2
                        c = c2
                        del file_dict[s]["IN_{}_{}".format(c1[0], c1[1])]

                    for file_ in files:

                        if "IN" in file_: file_dict[s]["IN_{}_{}".format(c[0], c[1])].append(file_)


        sm_fl = []
        for folder in folders:
            sm_fl += glob(folder + "/*" + s + "*SM*.root")

        file_dict[s]["SM"] = sm_fl

    return file_dict


def retrieveHisto(paths, tree, var, bins, ranges):
    
    chain = ROOT.TChain(tree)
    for path in paths:
        chain.AddFile(path)

    if var == "*":
        var = [i.GetName() for i in chain.GetListOfBranches()]
        bins = bins*len(var)
        ranges = ranges*len(var)

    if type(var) != list: 
        var = [var]
        bins = [bins]
        ranges = [ranges]

    th_dict = dict.fromkeys(var)
    for v, b, r in zip(var, bins, ranges):
        print("[INFO] @ Filling {} histo ...".format(v))
        h = ROOT.TH1F(v, v, b, r[0], r[1])
        h.SetDirectory(0)
        for event in chain:
            h.Fill(getattr(event, v), getattr(event, "w"))

        th_dict[v] = deepcopy(h)

    return th_dict

def invertHistoDict(h_dict):
    vars_ = get_var_list(h_dict)
    new_h_dict = dict.fromkeys(h_dict.keys())

    for sample in h_dict.keys():
        new_h_dict[sample] = dict.fromkeys(vars_)

        for var in new_h_dict[sample].keys():
            new_h_dict[sample][var] = {}

            for component in h_dict[sample]:
                new_h_dict[sample][var][component] = h_dict[sample][component][var]

    return new_h_dict

def makeHistos(config, file_dict):

    vars_ = config.getlist("variables", "treenames")
    bins = [int(i) for i in config.getlist("variables", "bins")]
    ranges = convertCfgLists(config.getlist("variables", "xrange"))
    histo_name = config.getlist("variables", "histonames")
    ops = config.getlist("eft", "operators")
    int_ = len(ops) > 1

    if vars_[0] != "*" and len(vars_) != len(bins) or len(vars_) != len(ranges):
        sys.exit("[ERROR] var names and bins/xranges do not match. Ignore or take action ...")
        

    base_histos = dict.fromkeys(file_dict.keys()) 

    for s in file_dict.keys():
        base_histos[s] = {}
        for component in file_dict[s]:
            if len(file_dict[s][component]) != 0:
                base_histos[s][component] = {}
                print("[INFO] @ ---- Starting filling histos for sample {}, component: {} ---- \
                \n ---------- @ @ @ @ @ @ @ ---------- ".format(s, component))
                for var, bins_, ranges_ in zip(vars_, bins, ranges) :
                    nt = (file_dict[s][component][0].split("ntuple_")[1]).split(".root")[0]
                    base_histos[s][component].update(retrieveHisto(file_dict[s][component], nt, var, bins_, ranges_))

    base_histos = invertHistoDict(base_histos)
    
    return base_histos


def mkdir(path):
    try:
        os.mkdir(path)
    except:
        print('[INFO] Folder {} already present, skipping ...'.format(path))
    
    return 


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

    args = parser.parse_args()

    config = ConfigParser(converters={'list': lambda x: [str(i.strip()) for i in x.split(',')]})
    config.read(args.cfg)

    outdir = config.get("general", "outfolder")
    outfile = config.get("general", "outfile")
    models = config.getlist("eft", "models")

    if len(models) == 0: sys.exit("[ERROR] No model specified, exiting ...")

    mkdir(outdir)

    fd = retireve_samples(config)
    base_histo = makeHistos(config, fd)

    for mod in models:

        mkdir(outdir+ "/" + mod)
        mkdir(outdir+ "/" + mod + "/rootFile")
        model_dict = histosToModel(base_histo, model_type=mod)
        write(model_dict, outname = outdir+ "/" + mod + "/rootFile/" + outfile)

        cfg_folder = outdir + "/" + mod 
        mkdir(cfg_folder)
        print("[INFO] Generating dummies ...")
        if bool(config.get("d_structure", "makeDummy")): makeStructure(model_dict, mod, cfg_folder)
        if bool(config.get("d_plot", "makeDummy")): 
            colors = config.getlist("d_plot", "colors")
            makePlot(model_dict, mod, colors, cfg_folder)
        if bool(config.get("d_samples", "makeDummy")): makeSamples(model_dict, mod, config, cfg_folder)
        if bool(config.get("d_configuration", "makeDummy")): makeConfiguration(model_dict, mod, config, cfg_folder)
        if bool(config.get("d_alias", "makeDummy")): makeAliases(model_dict, mod, cfg_folder)
        if bool(config.get("d_cuts", "makeDummy")): makeCuts(model_dict, mod, cfg_folder)
        if bool(config.get("d_variables", "makeDummy")): makeVariables(model_dict, mod, config, cfg_folder)
        if bool(config.get("d_nuisances", "makeDummy")): makeNuisances(model_dict, mod, config, cfg_folder)

    
    print("[INFO] @Done ...")
