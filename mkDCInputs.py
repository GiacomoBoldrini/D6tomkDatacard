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


def makeExecRunt(model, process, config, outdir):
    #creates an executable to create binary workspaces after running mkDatacards.py

    modeltot2w = {
        "EFT": "EFT",
        "EFTNeg": "EFTNegative",
        "EFTNeg-alt": "EFTNegative"
    }

    variables = config.getlist("variables", "treenames")
    ops = process.split("_")[1:]

    mod = modeltot2w[model]

    file_name = outdir + "/t2w.sh"
    f = open(file_name, 'w')

    f.write("#-----------------------------------\n")
    f.write("#     Automatically generated       # \n")
    f.write("#        by mkDCInputs.py           # \n")
    f.write("#-----------------------------------\n")
    f.write("\n\n\n")

    for var in variables:
        f.write("#-----------------------------------\n")
        f.write("cd datacards/{}/{}\n".format(process, var))
        to_w = "text2workspace.py  datacard.txt  -P HiggsAnalysis.AnalyticAnomalousCoupling.AnomalousCoupling{}:analiticAnomalousCoupling{}  -o   model.root \
        --X-allow-no-signal --PO eftOperators={}".format(mod, mod, ",".join(op for op in ops))        
        if "alt" in model: to_w += " --PO  eftAlternative"
        
        to_w += "\n"
        f.write(to_w)
        f.write("cd ../../..\n\n\n")

    f.close()
    #convert to executable
    st = os.stat(file_name)
    os.chmod(file_name, st.st_mode | stat.S_IEXEC)

def createOpRange(config):

    if not config.has_option("eft", "fitranges"): 
        all_ops = np.unique([item for subs in redemensionOpinput(config) for item in subs])
        return dict((i, [-10,10]) for i in all_ops)
    
    else:
        or_ = config.getlist("eft", "fitranges")
        return dict( (i.split(":")[0], [ float(i.split(":")[1]) , float(i.split(":")[2]) ] ) for i in or_ )


def makeExecRunc(process, config, outdir, opr):
    #creates an executable to fit binary workspaces after running mkDatacards.py

    variables = config.getlist("variables", "treenames")
    ops = process.split("_")[1:]

    ranges = ":".join("k_"+op+"={},{}".format(opr[op][0],opr[op][1]) for op in ops)


    file_name = outdir + "/fit.sh"
    f = open(file_name, 'w')

    f.write("#-----------------------------------\n")
    f.write("#     Automatically generated       # \n")
    f.write("#        by mkDCInputs.py           # \n")
    f.write("#-----------------------------------\n")
    f.write("\n\n\n")

    for var in variables:
        f.write("#-----------------------------------\n")
        f.write("cd datacards/{}/{}\n".format(process, var))
        to_w = "combine -M MultiDimFit model.root  --algo=grid --points 30000  -m 125   -t -1   --robustFit=1 --X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NEVER_GIVE_UP --X-rtd FITTER_BOUND --redefineSignalPOIs {}     --freezeParameters r      --setParameters r=1    --setParameterRanges {}  --verbose -1".format(",".join("k_"+op for op in ops), ranges)
        to_w += "\n"
        f.write(to_w)
        f.write("cd ../../..\n\n\n")

    f.close()
    #convert to executable
    st = os.stat(file_name)
    os.chmod(file_name, st.st_mode | stat.S_IEXEC)


def makeActivations(outdir, config):

    models = config.getlist("eft", "models")
    prefix = config.get("general", "folder_prefix")
    
    #Activation of t2w:
    file_name = outdir + "/runt.py"
    f = open(file_name, 'w')

    f.write("#!/usr/bin/env python\n\n")
    f.write("#-----------------------------------\n")
    f.write("#     Automatically generated       # \n")
    f.write("#        by mkDCInputs.py           # \n")
    f.write("#-----------------------------------\n")
    f.write("\n\n\n")

    f.write('from glob import glob\n')
    f.write('import os\n')

    f.write('if __name__ == "__main__":\n')
    f.write('   base_dir = os.getcwd()\n')
    f.write('   for dir in glob(base_dir + "/*/"):\n')
    f.write('      process = dir.split("/")[-2]\n')
    f.write('      process = process.split("{}")[1]\n'.format(prefix))
    f.write('      op = process.split("_")[1]\n')
    f.write('      for model in [{}]:\n'.format(",".join("\"{}\"".format(i) for i in models)))
    f.write('         print("[INFO] Running for op: {}, model: {}".format(op, model))\n')
    f.write('         os.chdir(dir + "/" + model)\n')
    f.write('         os.system("bash t2w.sh")\n')

    f.close()
    #convert to executable
    st = os.stat(file_name)
    os.chmod(file_name, st.st_mode | stat.S_IEXEC)

    #Activation of fit.sh:
    file_name = outdir + "/runc.py"
    f = open(file_name, 'w')

    f.write("#!/usr/bin/env python\n\n")
    f.write("#-----------------------------------\n")
    f.write("#     Automatically generated       # \n")
    f.write("#        by mkDCInputs.py           # \n")
    f.write("#-----------------------------------\n")
    f.write("\n\n\n")

    f.write('from glob import glob\n')
    f.write('import os\n')

    f.write('if __name__ == "__main__":\n')
    f.write('   base_dir = os.getcwd()\n')
    f.write('   for dir in glob(base_dir + "/*/"):\n')
    f.write('      process = dir.split("/")[-2]\n')
    f.write('      process = process.split("{}")[1]\n'.format(prefix))
    f.write('      op = process.split("_")[1]\n')
    f.write('      for model in [{}]:\n'.format(",".join("\"{}\"".format(i) for i in models)))
    f.write('         print("[INFO] Running for op: {}, model: {}".format(op, model))\n')
    f.write('         os.chdir(dir + "/" + model)\n')
    f.write('         os.system("bash fit.sh")\n')

    f.close()
    #convert to executable
    st = os.stat(file_name)
    os.chmod(file_name, st.st_mode | stat.S_IEXEC)


def convertCfgLists(list_):
    list_ = [i[1:-1].split(":") for i in list_]
    return [list(map(float, sublist)) for sublist in list_]
    

def get_model_syntax(comp_name):

    d = { "SM": "sm",
          "LI": "lin_",
          "QU": "quad_",
          "IN": "lin_mixed_",
          "SM_LI_QU": "sm_lin_quad_",
          "QU_INT": "quad_mixed_",
          "SM_LI_QU_INT": "sm_lin_quad_mixed_",
          "DATA" : "DATA",
        }

    type_ = comp_name.split("_c")[0]
    newName = d[type_]

    if type_ != "SM" and type_ != "DATA": #need to account for operators here
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
        return cleanNames(deepcopy(histo_dict))

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
                data = [i for i in components if "DATA" in i]

                #Checks that everything is right
                if len(linear) != 1:
                    if len(mixed) != mt.factorial(len(linear)) / (mt.factorial(2) * mt.factorial(len(linear)-2)) or len(sm) != 1: 
                        sys.exit("[ERROR] errors in the combinatorial, Probably you are missing some interference samples for the op you specified ...")

                eft_neg_dict[sample][var][sm[0]] = histo_dict[sample][var][sm[0]]
                if len(data) != 0:
                    eft_neg_dict[sample][var][data[0]] = histo_dict[sample][var][data[0]]

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
        
        return cleanNames(deepcopy(eft_neg_dict))


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
                data = [i for i in components if "DATA" in i]

                #Checks that everything is right
                if len(linear) != 1:
                    if len(mixed) != mt.factorial(len(linear)) / (mt.factorial(2) * mt.factorial(len(linear)-2)) or len(sm) != 1: 
                        sys.exit("[ERROR] errors in the combinatorial, Probably you are missing some interference samples for the op you specified ...")

                eft_negalt_dict[sample][var][sm[0]] = histo_dict[sample][var][sm[0]]

                if len(data) != 0:
                    eft_negalt_dict[sample][var][data[0]] = histo_dict[sample][var][data[0]]

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
                    new_sm.Reset("ICESM") #resetting histo, now blank
                    new_sm.SetDirectory(0)
                    new_sm.Add(histo_dict[sample][var]["QU_{}".format(o_c[0])])
                    new_sm.Add(histo_dict[sample][var]["QU_{}".format(o_c[1])])
                    new_sm.Add(histo_dict[sample][var]["IN_{}_{}".format(o_c[0], o_c[1])])
                    eft_negalt_dict[sample][var]["QU_INT_{}_{}".format(o_c[0], o_c[1])] = new_sm

        return cleanNames(deepcopy(eft_negalt_dict))


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


def list_duplicates_of(seq,item):
    start_at = -1
    locs = []
    while True:
        try:
            loc = seq.index(item,start_at+1)
        except ValueError:
            break
        else:
            locs.append(loc)
            start_at = loc
    return locs


def cleanDuplicates(paths):
    p  = [i.split("/")[-1] for i in paths]
    cleaned_paths = paths
    for item in p:
        #appending only the first of the duplicates
        dup = list_duplicates_of(p, item)
        if dup > 0:
            for d in dup[1:]:
                cleaned_paths.pop(d)
                p.pop(d)

    return cleaned_paths


def retireve_samples(config):

    print("[INFO] Retrieving samples ...")
    section = "ntuples"
    sample = config.getlist("general", "sample")
    folders = config.getlist(section, "folder")
    #ops = config.getlist("eft", "operators")
    ops_ = redemensionOpinput(config)
    sample_headers = [i + "_" + "_".join(op for op in k) for i,k in zip(sample,ops_)]

    file_dict = dict.fromkeys(sample_headers)

    for sh, s,ops in zip(sample_headers, sample, ops_):
        file_dict[sh] = {}

        int_ = len(ops) > 1

        comb = list(combinations(ops, 2))
        comb2 = [(i[1],i[0]) for i in comb] #reverse in case of wrong ordering

        #scan simple ops
        for op in ops:
            file_dict[sh]
            file_dict[sh]["QU_{}".format(op)] = []
            file_dict[sh]["LI_{}".format(op)] = []


            for folder in folders:
                files = glob(folder + "/*_" + s + "_" + op + "_*.root")
                for file_ in files:
                    if "QU" in file_: file_dict[sh]["QU_{}".format(op)].append(file_)
                    if "LI" in file_: file_dict[sh]["LI_{}".format(op)].append(file_)

            file_dict[sh]["QU_{}".format(op)] = cleanDuplicates(file_dict[sh]["QU_{}".format(op)])
            file_dict[sh]["LI_{}".format(op)] = cleanDuplicates(file_dict[sh]["LI_{}".format(op)])
            

                        
        #scan interference if present
        if int_:
            for c1, c2 in zip(comb, comb2):
                file_dict[sh]["IN_{}_{}".format(c1[0], c1[1])] = []
                file_dict[sh]["IN_{}_{}".format(c2[0], c2[1])] = []

                files1 = []
                files2 = []

                for folder in folders:
                    #either cG_cGtil or cGtil_cG, not both (repetition should be avoided)
                    files1 += glob(folder + "/*_" + s + "_{}_{}_".format(c1[0], c1[1]) + "*.root")
                    files2 += glob(folder + "/*_" + s + "_{}_{}_".format(c2[0], c2[1]) + "*.root")

                if len(files1) != 0 and len(files2) == 0: 
                    files = files1
                    c = c1
                    del file_dict[sh]["IN_{}_{}".format(c2[0], c2[1])]
                elif len(files1) == 0 and len(files2) != 0: 
                    files = files2
                    c = c2
                    del file_dict[sh]["IN_{}_{}".format(c1[0], c1[1])]
                else:
                    continue

                for file_ in files:
                    if "IN" in file_: file_dict[sh]["IN_{}_{}".format(c[0], c[1])].append(file_)

                if "IN_{}_{}".format(c1[0], c1[1]) in file_dict[sh]:
                    if len(file_dict[sh]["IN_{}_{}".format(c1[0], c1[1])]) == 0:
                        sys.exit("[ERROR] Missing Interference sample for op pair {} {}".format(c1[0], c1[1]))

                if "IN_{}_{}".format(c2[0], c2[1]) in file_dict[sh]:
                    if len(file_dict[sh]["IN_{}_{}".format(c2[0], c2[1])]) == 0:
                        sys.exit("[ERROR] Missing Interference sample for op pair {} {}".format(c2[0], c2[1]))

                file_dict[sh]["IN_{}_{}".format(c[0], c[1])] = cleanDuplicates(file_dict[sh]["IN_{}_{}".format(c[0], c[1])])
                    

        sm_fl = []
        for folder in folders:
            sm_fl += glob(folder + "/*" + s + "*SM.root")

        sm_fl = cleanDuplicates(sm_fl)

        file_dict[sh]["SM"] = sm_fl

    return file_dict


def retrieveDummy(name, var, bins, ranges):

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
        print("[INFO] @ Filling {} histo dummy ...".format(v))
        h = ROOT.TH1D(name + "_" + v, name, b, r[0], r[1])
        for i in range(1, b):
            h.SetBinContent(i,0)

        th_dict[v] = deepcopy(h)

    return th_dict

def makeCut(config):
    n_cut = config.getlist("cuts", "normalcuts")
    return " && ".join(cut for cut in n_cut)


def isCut(cutdf, cuts):

    isCut = False 
    for var, op, value in zip(cuts["cut"]["var"], cuts["cut"]["op"], cuts["cut"]["value"]):
        if not eval("cutdf['{}'][0] {} {}".format(var, op, value)):
            return True

def mkLogHisto(v, b, low, up):

    #low = 0 is not admiitted
    if low == 0: low = sys.float_info.min
    if low < 0:
        sys.exit("[ERROR] Log scale in a negative range. Check .cfg ...")
    edges = np.logspace(mt.log(low,10), mt.log(up,10), b+1)
    htemp = ROOT.TH1D(v + "_temp", v + "_temp", b, edges)
    return htemp


def retrieveHisto(paths, tree, var, bins, binsize, ranges, luminosity, cuts):
    
    chain = ROOT.TChain(tree)
    for path in paths:
        chain.AddFile(path)

    if var == "*":
        var = [i.GetName() for i in chain.GetListOfBranches()]
        bins = bins*len(var)
        binsize = binsize*len(var)
        ranges = ranges*len(var)

    if type(var) != list: 
        var = [var]
        bins = [bins]
        binsize = [binsize]
        ranges = [ranges]

    th_dict = dict.fromkeys(var)
    for v, b, bs, r in zip(var, bins, binsize, ranges):

        if bs == "fix":
            h = ROOT.TH1D(v, v, b, r[0], r[1])

        if bs == "log":
            h = mkLogHisto(v, b, r[0], r[1])

        elif bs != "fix" and bs !=  "log":
            sys.exit("[ERROR] Choose binsize between log and fix ... ")

        print("[INFO] @ Filling {} histo, bins: {}, binsize: {}, range: {} ...".format(v, b, bs, r))

        for path in paths:
            f = ROOT.TFile(path)
            t = f.Get(tree)

            if bs == "fix":
                htemp = ROOT.TH1D(v + "_temp", v + "_temp", b, r[0], r[1])

            elif bs == "log":
                htemp = mkLogHisto(v, b, r[0], r[1])

            #reading some important infos
            global_numbers             = f.Get ( tree + "_nums")
            cross_section              = global_numbers.GetBinContent (1) 
            sum_weights_total          = global_numbers.GetBinContent (2) 
            #sum_weights_selected       = global_numbers.GetBinContent (3) 

            #NB luminosity in fb, cross-section expected in pb in the config files
            normalization = cross_section * 1000. * luminosity / (sum_weights_total)
            t.Draw("{} >> {}".format(v, v + "_temp"), "w*({})".format(cuts), "")

            #Normalize the histo
            htemp.Scale(normalization)
            #overflow bin count -> last bin count
            htemp.SetBinContent(htemp.GetNbinsX(), htemp.GetBinContent(h.GetNbinsX()) + htemp.GetBinContent(h.GetNbinsX() + 1))
            htemp.SetBinContent(htemp.GetNbinsX() + 1, 0.)

            h.Add(htemp)

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
    binsize = config.getlist("variables", "binsize")
    ranges = convertCfgLists(config.getlist("variables", "xrange"))
    histo_name = config.getlist("variables", "histonames")
    lumi = float(config.get("general", "lumi"))

    dummies = []
    if config.has_option("variables", "makeDummy"): dummies = config.getlist("variables", "makeDummy")

    if vars_[0] != "*" and len(vars_) != len(bins) or len(vars_) != len(ranges) or len(vars_) != len(binsize):
        sys.exit("[ERROR] var names and bins/binsize/xranges do not match. Ignore or take action ...")

    cut = "1==1"
    if config.has_option("cuts", "normalcuts"): cut = makeCut(config)    

    base_histos = dict.fromkeys(file_dict.keys()) 

    for s in file_dict.keys():
        base_histos[s] = {}
        for component in file_dict[s]:
            if len(file_dict[s][component]) != 0:
                base_histos[s][component] = {}
                print("[INFO] @ ---- Starting filling histos for sample {}, component: {} ---- \
                \n ---------- @ @ @ @ @ @ @ ---------- ".format(s, component))
                for var, bins_, binsize_, ranges_ in zip(vars_, bins, binsize, ranges) :
                    nt = (file_dict[s][component][0].split("ntuple_")[1]).split(".root")[0]
                    base_histos[s][component].update(retrieveHisto(file_dict[s][component], nt, var, bins_, binsize_, ranges_, lumi, cut))
                
        for dummy in dummies:
            print("[INFO] @ ---- Filling dummy histos for sample {}, component: {} ---- \
                \n ---------- @ @ @ @ @ @ @ ---------- ".format(s, dummy))
            vars_copy = base_histos[s][file_dict[s].keys()[0]].keys() #because here we retrieved from the .root, can be "*"
            base_histos[s][dummy] = {}
            for var, bins_, ranges_ in zip(vars_, bins, ranges) :
                base_histos[s][dummy].update(retrieveDummy( dummy, var, bins_, ranges_))
                    
    base_histos = invertHistoDict(base_histos)
    
    return base_histos


def mkdir(path):
    try:
        os.mkdir(path)
    except:
        sys.exit("[ERROR] Dirs are already present ... Delete them or change name in order to avoid overriding")
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

    parser.add_argument('--v',     dest='verbose',     help='Optional prints with retrieved infos', default = True, action = 'store_false',
                       required = False)

    args = parser.parse_args()

    config = ConfigParser(converters={'list': lambda x: [str(i.strip()) for i in x.split(',')]})
    config.read(args.cfg)

    outdir = config.get("general", "outfolder")
    outprefix = config.get("general", "folder_prefix")
    outfile = config.get("general", "outfile")
    models = config.getlist("eft", "models")

    opr = createOpRange(config)

    mkdir(outdir)
    makeActivations(outdir, config) #make scripts for automatic activation of text2workspace and combine

    if len(models) == 0: sys.exit("[ERROR] No model specified, exiting ...")

    fd = retireve_samples(config)

    if args.verbose: prettyPrintConfig(config, fd)

    base_histo = makeHistos(config, fd)

    for process in base_histo.keys():

        #Saving, discriminating processes
        outfile_path = outdir + "/" + outprefix + process
        mkdir(outfile_path)
        
        for mod in models:

            mod_path = outfile_path + "/" + mod
            mkdir(mod_path)
            mkdir(mod_path + "/rootFile/")

            model_dict = histosToModel(dict((proc,base_histo[proc]) for proc in base_histo.keys() if proc == process), model_type=mod)
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
