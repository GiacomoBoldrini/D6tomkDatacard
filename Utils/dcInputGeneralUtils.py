import sys
import os 
import stat
from itertools import combinations


def mkdir(path):
    try:
        os.mkdir(path)
    except:
        sys.exit("[ERROR] Dirs are already present ... Delete them or change name in order to avoid overriding")
    return 


def makeCut(config):
    n_cut = config.getlist("cuts", "normalcuts")
    return " && ".join(cut for cut in n_cut)

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
        to_w = "combine -M MultiDimFit model.root  --algo=grid --points 10000  -m 125   -t -1   --robustFit=1 --X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NEVER_GIVE_UP --X-rtd FITTER_BOUND --redefineSignalPOIs {}     --freezeParameters r      --setParameters r=1    --setParameterRanges {}  --verbose -1".format(",".join("k_"+op for op in ops), ranges)
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
        if set(vars_[i]) != set(vars_[i+1]): check = False

    if check: return vars_[0]
    else: sys.exit("[ERROR] Vars do not coincide between the various samples. Check .cfg ...")


def cleanNames(model_dict):
    
    for sample in model_dict.keys():
        for var in model_dict[sample].keys():
            tb_clear = model_dict[sample][var].keys()
            for c in model_dict[sample][var].keys():
                if c in tb_clear: #after popping we will modify the keys 
                    name = get_model_syntax(c)
                    model_dict[sample][var][name] = model_dict[sample][var].pop(c)
                else:
                    continue

    #sanity check
    #retireve ops
    ops = [] # single operators
    blocks = [] # which will go in the datacard
    for sample in model_dict.keys():
        for var in model_dict[sample].keys():
            for c in model_dict[sample][var].keys():
                if c not in blocks: blocks.append(c)
                if "quad" in c: #quad is the only component common to every model and should be present for each op
                    op = c.split("_")[-1] #last is the op (don't worry about two ops)
                    if op not in ops: ops.append(op)

    op_pairs = list(combinations(ops, 2)) #for interferences

    #checks for components after cleaning names:
    if len([j for j in blocks if "quad" in j and "mixed" not in j and "sm" not in j]) != len(ops): sys.exit("[ERROR] Missing pure quadratic components...")
    if len([j for j in blocks if "lin" in j and "mixed" not in j]) != len(ops): print("[WARNING] Missing linear components, this can be ignored when building models other than EFT...")
    if "sm" not in blocks: sys.exit("[ERROR] no SM sample...")
    if len([j for j in blocks if "mixed" in j]) != len(op_pairs): print("[WARNING] Missing interference samples for some operators. This may be ignored if you are sure they do not exist")

    return model_dict


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
