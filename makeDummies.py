import os
import sys
import numpy as np
from collections import OrderedDict

def groupSinglets(comp_name):
    d = { "sm": "SM",
          "lin": "L ",
          "quad": "Q ",
          "lin_mixed": "M ",
          "sm_lin_quad": "SM+L+Q ",
          "quad_mixed": "Q+Q+M ",
          "sm_lin_quad_mixed": "SM+L+L+Q+Q+M ",
          "DATA": "DATA"
        }

    type_ = comp_name.split("_c")[0]
    newName = d[type_]

    if type_ != "sm" and type_!= "DATA": #need to account for operators here
        ops = comp_name.split(type_ + "_")[1]
        if len(ops.split("_")) == 2: 
            ops = ops.split("_")
            newName += ops[0] + " " + ops[1]
        else:
            newName += ops

    return newName


def isBSM(sample):
    if any(i in sample for i in ["sm_", "quad_", "lin_"]):
        return True
    else:
        return False

def makeStructure(h_dict, model, outdir):

    for sample in h_dict:
        first_var = h_dict[sample].keys()[0]
        structure = h_dict[sample][first_var].keys()

        file_name = outdir + "/structure_" + sample + "_" + model + ".py"
        f = open(file_name, 'w')

        f.write("#-----------------------------------\n")
        f.write("#     Automatically generated       # \n")
        f.write("#        by mkDCInputs.py           # \n")
        f.write("#-----------------------------------\n")
        f.write("\n\n\n")

        for key in structure:

            isData = 0
            if key == "DATA": isData = 1

            f.write('structure["{}"]  = {} \n'.format(key, "{"))
            f.write("        'isSignal' : 0, \n")
            f.write("        'isData' : {}, \n".format(isData))
            f.write("{}\n".format("}"))
            f.write("\n\n")

        f.close()

def makePlot(h_dict, model, config, outdir):

    colors = config.getlist("d_plot", "colors")
    c_types = [i.split(":")[0] for i in colors]
    c_vals = [[int(j) for j in i.split(":")[1:]] for i in colors]

    user_colors = {}
    for i,j in zip(c_types, c_vals):
        user_colors[i] = j

    group = []
    g_colors = []

    if config.has_option("d_plot", "isSignal"): 
        isSignal = config.getlist("d_plot", "isSignal")
        comp = [i.split(":")[0] for i in isSignal]
        val = [i.split(":")[1] for i in isSignal]
        isSignal = dict((c,v) for c,v in zip(comp, val))

    else:
        isSignal = {}

    if config.has_option("d_plot", "group"): group = config.getlist("d_plot", "group")
    if config.has_option("d_plot", "g_colors"): g_colors = [int(col) for col in config.getlist("d_plot", "g_colors")]

    for sample in h_dict:
        first_var = h_dict[sample].keys()[0]
        structure = h_dict[sample][first_var].keys()
        ops = sample.split("_")[1:]
        
        cd = {}

        for key in user_colors.keys():
            if key != "sm" and key not in config.getlist("variables", "makeDummy"):
                if len(user_colors[key]) == len(ops):
                    for j,op in enumerate(ops):
                        cd[key + "_" + op] = user_colors[key][j]

                if len(user_colors[key]) < len(ops):
                    if key + "_" + "_".join(op for op in ops) in structure:
                        cd[key + "_" + "_".join(op for op in ops)] = user_colors[key][0]
                    else:
                        cd[key + "_" + "_".join(op for op in ops[::-1])] = user_colors[key][0]

                if len(user_colors[key]) > len(ops):
                    for j,op in enumerate(ops):
                        cd[key + "_" + op] = user_colors[key][j]
            else:
                cd[key] = user_colors[key][0]

        for key in config.getlist("variables", "makeDummy"):
            if key not in user_colors.keys():
                cd[key] = 1

        file_name = outdir + "/plot_" + sample + "_" + model + ".py"
        f = open(file_name, 'w')

        f.write("#-----------------------------------\n")
        f.write("#     Automatically generated       # \n")
        f.write("#        by mkDCInputs.py           # \n")
        f.write("#-----------------------------------\n")
        f.write("\n\n\n")

        for idx,g_ in enumerate(group):

            group_these = {}

            if  g_.split(":")[1] == "BSM":

                g_name = g_.split(":")[0]
                if g_name == "model": g_name = model

                group_these[g_name] = {}

                if g_name in isSignal.keys(): sig_val = isSignal[g_name]
                else: sig_val = 2

                group_these[g_name]['nameHR'] = "'{}'".format(g_name)
                group_these[g_name]['isSignal'] = sig_val
                group_these[g_name]['color'] = g_colors[idx]
                group_these[g_name]['samples'] = []
                components = h_dict[sample][h_dict[sample].keys()[0]].keys() #they are equal forall variables

                for comp in components:
                    if isBSM(comp): group_these[g_name]['samples'].append(comp)

            elif g_.split(":")[1] == "all":
                for i,key in enumerate(structure):
                    if key != "DATA":
                        leg_name = groupSinglets(key)
                        group_these[key] = {}

                        if key in isSignal.keys(): sig_val = isSignal[key]
                        else: sig_val = 2

                        group_these[key]['nameHR'] = "'{}'".format(leg_name)
                        group_these[key]['isSignal'] = sig_val
                        group_these[key]['color'] = cd[key]
                        group_these[key]['samples'] = [key]


            else:
                g_name = g_.split(":")[0]
                g_list = [str(i) for i in (g_.split(":")[1])[1:-1].split(" ")]

                group_these[g_name] = {}

                if g_name in isSignal.keys(): sig_val = isSignal[g_name]
                else: sig_val = 2

                group_these[g_name]['nameHR'] = "'{}'".format(g_.split(":")[0])
                group_these[g_name]['isSignal'] = sig_val
                group_these[g_name]['color'] = g_colors[idx]
                group_these[g_name]['samples'] = []

                components = h_dict[sample][h_dict[sample].keys()[0]].keys() #they are equal forall variables

                for comp in g_list:
                    if comp not in components:
                        sys.exit("[ERROR] The sample {} specified for grouping into {} does not exists ...".format(comp, g_name))

                    group_these[g_name]['samples'].append(comp)


            if len(group_these.keys()) != 0:

                #sort the dict to allow right plotting
                group_these = OrderedDict(sorted(group_these.items(), key=lambda t: t[1]["isSignal"], reverse=True))

                for key in group_these.keys():
                    f.write('groupPlot["{}"]  = {} \n'.format(key, "{"))
                    for subkey in group_these[key]:
                        if subkey != 'samples':
                            f.write("        '{}' : {}, \n".format(subkey, group_these[key][subkey]))
                        else:
                            write_list = "["
                            for s in group_these[key][subkey]:
                                write_list += "'{}'".format(s) + ","

                            write_list = write_list[:-1] + "]"
                            f.write("        '{}' : {}, \n".format(subkey, write_list))

                    f.write("{}\n".format("}"))
                    f.write("\n\n")


        for i,key in enumerate(structure):

            if key in isSignal.keys(): sig_val = isSignal[key]
            else: sig_val = 2
            
            isData = 0
            if key == "DATA": 
                isData = 1

            color = 1
            if key in cd:
                color = cd[key]

            if i > len(cd.keys()): sys.exit("[ERROR]: Colors not sufficient, add more...")

            f.write('plot["{}"]  = {} \n'.format(key, "{"))
            f.write("        'color' : {}, \n".format(cd[key]))
            f.write("        'isSignal' : {}, \n".format(sig_val))
            f.write("        'isData' : {}, \n".format(isData))
            f.write("        'scale' : 1, \n")

            if key == "DATA":
                f.write("        'isBlind' : 1, \n") #default blinding on data

            f.write("{}\n".format("}"))
            f.write("\n\n")

        f.close()

def makeVariables(h_dict, model, config, outdir):

    xaxis_ = config.getlist("d_variables", "xaxis")
    name_ = config.getlist("d_variables", "name")
    range_ = config.getlist("d_variables", "range")
    fold_ = config.getlist("d_variables", "fold")

    for sample in h_dict:
        vars_ = h_dict[sample].keys()

        bl = len(vars_)
        if not all(len(lst) == bl for lst in [xaxis_, name_, range_, fold_]):

            if xaxis_[0] == "auto": xaxis_ = dict((i,j) for i,j in zip(vars_, vars_))
            elif len(xaxis_) == len(vars_): 
                tn = config.getlist("variables", "treenames")
                xaxis_ = dict((i,j) for i,j in zip(tn, xaxis_))
            else:
                sys.exit("[ERROR] xaxis name do not match variables, check inputs in cfg ...")


            if name_[0] == "auto": name_ = dict((i,j) for i,j in zip(vars_, vars_)) 
            elif len(name_) == len(vars_): 
                tn = config.getlist("variables", "treenames")
                name_ = dict((i,j) for i,j in zip(tn, name_))
            else:
                sys.exit("[ERROR] names do not match variables, check inputs in cfg ...")
            

            if fold_[0] == "auto": fold_ = dict((i,0) for i in vars_)
            elif len(fold_) == len(vars_): 
                tn = config.getlist("variables", "treenames")
                fold_ = dict((i,j) for i,j in zip(tn, fold_))
            else:
                sys.exit("[ERROR] folds do not match variables, check inputs in cfg ...")

            if range_[0] == "auto":
                tn = config.getlist("variables", "treenames")
                range_ = dict.fromkeys(tn)
                bins = [int(i) for i in config.getlist("variables", "bins")]
                ranges = [i[1:-1].split(":") for i in config.getlist("variables", "xrange")]
                ranges = [list(map(float, sublist)) for sublist in ranges]

                for k,b,r in zip(range_.keys(), bins, ranges):
                    range_[k] = {'bins': b, 'range': [r[0], r[1]]}

            elif len(range_) == len(vars_): 
                tn = config.getlist("variables", "treenames")
                range_ = dict((i,j) for i,j in zip(tn, range_))  
            else: 
                sys.exit("[ERROR] ranges do not match variables, check inputs in cfg ...")


        file_name = outdir + "/variables_" + sample + "_" + model + ".py"
        f = open(file_name, 'w')

        f.write("#-----------------------------------\n")
        f.write("#     Automatically generated       # \n")
        f.write("#        by mkDCInputs.py           # \n")
        f.write("#-----------------------------------\n")
        f.write("\n\n\n")

        for var, xa, name, ra, fold in zip(vars_, xaxis_, name_, range_, fold_):

            f.write('variables["{}"]  = {} \n'.format(var, "{"))
            f.write("        'name' : '{}', \n".format(name_[var]))
            f.write("        'range' : ({},{},{}), \n".format(range_[var]['bins'], range_[var]['range'][0], range_[var]['range'][1]))
            f.write("        'xaxis' : {}, \n".format(xaxis_[var]))
            f.write("        'fold' : {}, \n".format(fold_[var]))
            f.write("{}\n".format("}"))
            f.write("\n\n")

        f.close()


def makeSamples(h_dict, model, config, outdir):

    for sample in h_dict:
        first_var = h_dict[sample].keys()[0]
        structure = h_dict[sample][first_var].keys()

        file_name = outdir + "/samples_" + sample + "_" + model + ".py"
        f = open(file_name, 'w')

        f.write("#-----------------------------------\n")
        f.write("#     Automatically generated       # \n")
        f.write("#        by mkDCInputs.py           # \n")
        f.write("#-----------------------------------\n")
        f.write("\n\n\n")

        f.write("import os \n")
        f.write("import inspect \n")
        f.write("configurations = os.path.realpath(inspect.getfile(inspect.currentframe())) # this file \n")
        f.write("configurations = os.path.dirname(configurations) \n\n")
        f.write("from LatinoAnalysis.Tools.commonTools import getSampleFiles, getBaseW, addSampleWeight\n\n")

        #Samples declaration
        f.write("# samples\n\n")
        f.write("try:\n")
        f.write("   len(samples)\n")
        f.write("except NameError:\n")
        f.write("   import collections\n")
        f.write("   samples = collections.OrderedDict()")
        f.write("\n\n")

        names = config.getlist("d_samples", "name")
        w = config.getlist("d_samples", "weight")
        ws = config.getlist("d_samples", "weights")
        fxj = config.getlist("d_samples", "filesperjob")

        if len(names) == len(w) == len(ws) == len(fxj) == 1:
            names = names*len(structure)
            w = w*len(structure)
            ws = ws*len(structure)
            fxj = fxj*len(structure)

        elif len(names) == len(w) == len(ws) == len(fxj) != len(structure):
            sys.exit("[ERROR] While making sample, provide a list of parameters = to number of EFT component \
                        or only one value (repeated). Nothing inbetween ...")
        else:
            sys.exit("[ERROR] While making sample, provide a list of parameters = to number of EFT component \
                        or only one value (repeated). Nothing inbetween ...")


        for i,key in enumerate(structure):

            f.write('samples["{}"]  = {} \n'.format(key, "{"))
            f.write("        'name' : {}, \n".format(names[i]))
            f.write("        'weight' : {}, \n".format(w[i]))
            f.write("        'weights' : {}, \n".format(ws[i]))
            f.write("        'isData' : 0, \n")
            f.write("        'FilesPerJob' : {}, \n".format(fxj[i]))
            f.write("{}\n".format("}"))
            f.write("\n\n")

        f.close()


def makeConfiguration(h_dict, model, config, outdir):

    for sample in h_dict:

        file_name = outdir + "/configuration_" + sample + "_" + model + ".py"

        write_out = {}

        write_out["tag"] = config.get("d_configuration", "tag")

        aliasesFile = config.get("d_configuration", "aliasesFile")
        if aliasesFile == "auto":
            aliasesFile = "aliases_" + sample + "_" + model + ".py"
        write_out["aliasesFile"] = aliasesFile

        variablesFile = config.get("d_configuration", "variablesFile")
        if variablesFile == "auto":
            variablesFile = "variables_" + sample + "_" + model + ".py"
        write_out["variablesFile"] = variablesFile

        cutsFile = config.get("d_configuration", "cutsFile")
        if cutsFile == "auto":
            cutsFile = "cuts_" + sample + "_" + model + ".py"
        write_out["cutsFile"] = cutsFile

        samplesFile = config.get("d_configuration", "samplesFile")
        if samplesFile == "auto":
            samplesFile = "samples_" + sample + "_" + model + ".py"
        write_out["samplesFile"] = samplesFile

        plotFile = config.get("d_configuration", "plotFile")
        if plotFile == "auto":
            plotFile = "plot_" + sample + "_" + model + ".py"
        write_out["plotFile"] = plotFile

        structureFile = config.get("d_configuration", "structureFile")
        if structureFile == "auto":
            structureFile = "structure_" + sample + "_" + model + ".py"
        write_out["structureFile"] = structureFile

        nuisancesFile = config.get("d_configuration", "nuisancesFile")
        if nuisancesFile == "auto":
            nuisancesFile = "nuisances_" + sample + "_" + model + ".py"
        write_out["nuisancesFile"] = nuisancesFile


        write_out["lumi"] = config.get("d_configuration", "lumi")
        write_out["outputDirPlots"] = config.get("d_configuration", "outputDirPlots")
        write_out["outputDirDatacard"] = config.get("d_configuration", "outputDirDatacard")

        f = open(file_name, 'w')

        f.write("#-----------------------------------\n")
        f.write("#     Automatically generated       # \n")
        f.write("#        by mkDCInputs.py           # \n")
        f.write("#-----------------------------------\n")
        f.write("\n\n\n")

        for key, value in write_out.items():
            if type(value) == str:
                f.write("{} = '{}' \n\n".format(key, value))
            else:
                f.write("{} = {} \n\n".format(key, value))

        f.close()

def makeAliases(h_dict, model, outdir):

    for sample in h_dict:

        file_name = outdir + "/aliases_" + sample + "_" + model + ".py"
        f = open(file_name, 'w')

        f.write("#-----------------------------------\n")
        f.write("#     Automatically generated       # \n")
        f.write("#        by mkDCInputs.py           # \n")
        f.write("#-----------------------------------\n")
        f.write("\n\n\n")
        
        f.write('aliases["inclusive"] = {} \n'.format("{"))
        f.write("      'expr': 0 == 0'\n".format("{"))
        f.write("{}\n".format("}"))
        f.write("\n\n")

        f.close()

def makeCuts(h_dict, model, outdir):

    for sample in h_dict:

        file_name = outdir + "/cuts_" + sample + "_" + model + ".py"
        f = open(file_name, 'w')

        f.write("#-----------------------------------\n")
        f.write("#     Automatically generated       # \n")
        f.write("#        by mkDCInputs.py           # \n")
        f.write("#-----------------------------------\n")
        f.write("\n\n\n")

        f.write("cuts['{}'] = {} \n".format(sample, "{"))
        f.write("  'expr': 'inclusive', \n")
        f.write("{}\n".format("}"))
        f.write("\n\n")

        f.close()


def whatNuis(comp):

    test = np.array(["sm", "lin", "quad", "mixed"])
    base = np.array(comp.split("_")) #sm #lin #quad #

    if base.size == 1: return base #only identical sm has 1 len

    mask = np.isin(base, test)
    c = base[mask]
    ops = np.setdiff1d(base, c)

    #so finally this component
    #receives nuis contributions from these

    final = [mod + "_" + op  for mod in c if mod != "sm" for op in ops]
    if "sm" in c:
        final.append("sm")

    return final 


def propagateNuis(h_dict, nuis_dict):

    var = h_dict.keys()[0]
    s_int = h_dict[var].keys()

    for key_name in nuis_dict.keys():
        samples_dict = nuis_dict[key_name]['samples']
        
        for sam in samples_dict.keys():
            sam_nuis_prop = 0
            c = whatNuis(sam)
            sample_nuis = samples_dict[sam] - 1


            #propagation
            if sam in s_int:
                #comp_yield = float('%.4f'%h_dict[var][sam].Integral())
                comp_yield = h_dict[var][sam].Integral()
            else: continue

            for basic_component in c:
                if basic_component in s_int and basic_component in samples_dict.keys():
                    #yield_ = float('%.4f'%h_dict[var][basic_component].Integral())
                    yield_ = h_dict[var][basic_component].Integral()

                    sam_nuis_prop += (yield_ * samples_dict[basic_component]) / comp_yield

            nuis_dict[key_name]['samples'][sam] = sam_nuis_prop

    return nuis_dict

            

# def switchNuis(comp_1, nuis_comp_1, comp_2):
#     #this stands also if the component is not sm
#     #print("sigma_{} = ({}-1) * {}/{} + 1 = {}".format("2", nuis_comp_1, comp_1, comp_2, (nuis_comp_1 - 1) * float(comp_1)/comp_2 + 1))
#     return (nuis_comp_1 - 1) * float(comp_1)/comp_2 + 1

# def propagateNuis(h_dict, nuis_dict):

#     #only lnN nuisances can be propagated
#     #checks are made


#     for nuis_name in nuis_dict.keys():
#         if nuis_dict[nuis_name]['type'] == "lnN":
#             if len(nuis_dict[nuis_name]['samples'].keys()) > 1:
#                 sys.exit("[ERROR] Cannot propagate more than one nuisance, there is \
#                 ambiguity... Please insert only one component for each nuisance and it will be propagated")

#             for sample in nuis_dict[nuis_name]['samples'].keys():
            
#                 #cerco questo oggetto nella dict degli histo
#                 comp_yield = 0
#                 comp_nuis = nuis_dict[nuis_name]['samples'][sample]
#                 for var in h_dict.keys():
#                     compnames = h_dict[var].keys()
#                     for j in compnames:
#                         if j == sample:
#                             #We do this because mkDatacards saves only the first 4 decimal places
#                             #in the rate. Without this the models are distorted... Not nice but still..
#                             #card.write(''.join(('%-.4f' % yieldsSig[name]) line 240
#                             comp_yield = float('%.4f'%h_dict[var][j].Integral())
#                     # propagate to other components having
#                     # the nuis name in their name

#                     for cn in compnames:
#                         if (sample in cn) and sample != cn:
#                             comp2_yield = float('%.4f'%h_dict[var][cn].Integral())
#                             #print(cn, comp2_yield)
#                             comp2_nuis = switchNuis(comp_yield, comp_nuis, comp2_yield)
#                             #print(comp2_nuis)

#                             nuis_dict[nuis_name]['samples'][cn] = comp2_nuis

#     #print(nuis_dict)
#     return nuis_dict


def check_Nuisances(nuis_dict, h_dict):
    
    for nuis_name in nuis_dict.keys():
        for sample in nuis_dict[nuis_name]['samples'].keys():

            for sam in h_dict.keys():
                for var in h_dict[sam].keys():
                    compnames = h_dict[sam][var].keys()
                    #check if the nuis same is present in at least one component
                    #for each variable
                    if not any([sample in i for i in compnames]):
                        return False
    return True


def makeNuisDict(config, d_name_, name_, type_, samples_, components):

    n_d = {}

    if len(samples_) == 1 and samples_[0][0].split(":")[0] == "all":
        val = float(samples_[0][0].split(":")[1])
        t = type_[0]
        dn = d_name_[0]
        n = name_[0]
        n_d[dn] = {}
        n_d[dn]['name'] = n
        n_d[dn]['type'] = t
        n_d[dn]['samples'] = {}
        for comp in components:
            if comp not in config.getlist("variables", "makeDummy"):
                n_d[dn]['samples'][comp] = val

        return n_d

    for dn, n, t, s in zip(d_name_, name_, type_, samples_):
        n_d[dn] = {}
        n_d[dn]['name'] = n
        n_d[dn]['type'] = t
        n_d[dn]['samples'] = {}
        
        for kv in s:
            comp = kv.split(":")[0]
            val = float(kv.split(":")[1])
            n_d[dn]['samples'][comp] = val

    return n_d


def makeNuisances(h_dict, model, config, outdir):

    #THIS PART IS NOT PERFECT
    #CAN WORK IF THE NUISANCE IS ONLY ON SM
    #DID NOT CHECK FOR OTHER SCENARIOS

    defname = config.getlist("d_nuisances", "defname") #the name in dict key
    name = config.getlist("d_nuisances", "name") # the 'name' field
    samples = [i[1:-1].split("|") for i in config.getlist("d_nuisances", "samples")]
    samples = [list(map(str, sublist)) for sublist in samples]
    types = config.getlist("d_nuisances", "types") 
        

    for sample in h_dict:

        components = h_dict[sample][h_dict[sample].keys()[0]].keys()

        nd = makeNuisDict(config, defname, name, types, samples, components)


        if not check_Nuisances(nd, h_dict):
            sys.exit("[ERROR] Nuisances specified in cfg file are not present in components dict ... Check inputs")

        if config.get("d_nuisances", "propagate") == "True":
            #
            # HORRIBLE FIX FOR 1D NUIS
            #

            nd = propagateNuis(h_dict[sample], nd)

        file_name = outdir + "/nuisances_" + sample + "_" + model + ".py"
        f = open(file_name, 'w')

        f.write("#-----------------------------------\n")
        f.write("#     Automatically generated       # \n")
        f.write("#        by mkDCInputs.py           # \n")
        f.write("#-----------------------------------\n")
        f.write("\n\n\n")
        
        for key in nd.keys():
            f.write("nuisances['{}'] = {} \n".format(key, "{"))
            f.write("        'name' : '{}', \n".format(nd[key]['name']))
            f.write("        'type' : '{}', \n".format(nd[key]['type']))
            f.write("        'samples': {} \n".format("{"))
            
            for sample in nd[key]['samples']:
                f.write("            '{}' : '{}', \n".format(sample, nd[key]['samples'][sample]))
            f.write("        {} \n".format("}"))

            f.write("{}\n".format("}"))
            f.write("\n\n")

        f.close()
