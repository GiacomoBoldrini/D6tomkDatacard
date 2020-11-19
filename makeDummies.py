import os
import sys

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

            f.write('structure["{}"]  = {} \n'.format(key, "{"))
            f.write("        'isSignal' : 0, \n")
            f.write("        'isData' : 0, \n")
            f.write("{}\n".format("}"))
            f.write("\n\n")

        f.close()

def makePlot(h_dict, model, colors, outdir):

    for sample in h_dict:
        first_var = h_dict[sample].keys()[0]
        structure = h_dict[sample][first_var].keys()

        file_name = outdir + "/plot_" + sample + "_" + model + ".py"
        f = open(file_name, 'w')

        f.write("#-----------------------------------\n")
        f.write("#     Automatically generated       # \n")
        f.write("#        by mkDCInputs.py           # \n")
        f.write("#-----------------------------------\n")
        f.write("\n\n\n")

        for i,key in enumerate(structure):

            if i > len(colors): sys.exit("[ERROR]: Colors not sufficient, add more...")

            f.write('plot["{}"]  = {} \n'.format(key, "{"))
            f.write("        'color' : {}, \n".format(colors[i]))
            f.write("        'isSignal' : 0, \n")
            f.write("        'isData' : 0, \n")
            f.write("        'scale' : 1, \n")
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

            if xaxis_[0] == "auto": xaxis_ = vars_
            else: xaxis_ = xaxis_*len(vars_)
            if name_[0] == "auto": name_ = vars_ 
            else: name_ = name_*len(vars_)
            if fold_ == "auto": fold_ = [0]*len(vars_)
            else: fold_ = fold_*len(vars_)

            if range_[0] == "auto":
                bins = [int(i) for i in config.getlist("variables", "bins")]
                ranges = [i[1:-1].split(":") for i in config.getlist("variables", "xrange")]
                ranges = [list(map(float, sublist)) for sublist in ranges]
                range_ = []
                for b,r in zip(bins, ranges):
                    range_.append( [b, r[0], r[1]] )
            else: range_ = range_*len(vars_)


        file_name = outdir + "/variables_" + sample + "_" + model + ".py"
        f = open(file_name, 'w')

        f.write("#-----------------------------------\n")
        f.write("#     Automatically generated       # \n")
        f.write("#        by mkDCInputs.py           # \n")
        f.write("#-----------------------------------\n")
        f.write("\n\n\n")

        for var, xa, name, ra, fold in zip(vars_, xaxis_, name_, range_, fold_):

            f.write('variables["{}"]  = {} \n'.format(var, "{"))
            f.write("        'name' : '{}', \n".format(name))
            f.write("        'range' : ({},{},{}), \n".format(ra[0], ra[1], ra[2]))
            f.write("        'xaxis' : {}, \n".format(xa))
            f.write("        'fold' : {}, \n".format(fold))
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


def switchNuis(comp_1, nuis_comp_1, comp_2):
    #this stands also if the component is not sm
    return (nuis_comp_1 - 1) * float(comp_1)/comp_2 + 1

def propagateNuis(h_dict, nuis_dict):

    #only lnN nuisances can be propagated
    #checks are made


    for nuis_name in nuis_dict.keys():
        if nuis_dict[nuis_name]['type'] == "lnN":
            if len(nuis_dict[nuis_name]['samples'].keys()) > 1:
                sys.exit("[ERROR] Cannot propagate more than one nuisance, there is \
                ambiguity... Please insert only one component for each nuisance and it will be propagated")

            for sample in nuis_dict[nuis_name]['samples'].keys():
            
                #cerco questo oggetto nella dict degli histo
                comp_yield = 0
                comp_nuis = nuis_dict[nuis_name]['samples'][sample]
                for var in h_dict.keys():
                    compnames = h_dict[var].keys()
                    for j in compnames:
                        if j == sample:
                            comp_yield = h_dict[var][j].Integral()
                    # propagate to other components having
                    # the nuis name in their name

                    for cn in compnames:
                        if (sample in cn) and sample != cn:
                            comp2_yield = h_dict[var][cn].Integral()
                            comp2_nuis = switchNuis(comp_yield, comp_nuis, comp2_yield)

                            nuis_dict[nuis_name]['samples'][cn] = comp2_nuis

    return nuis_dict


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


def makeNuisDict(d_name_, name_, type_, samples_):

    n_d = {}

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
    #DID NOT CHECK FOR OTHER SCENARIO

    defname = config.getlist("d_nuisances", "defname") #the name in dict key
    name = config.getlist("d_nuisances", "name") # the 'name' field
    samples = [i[1:-1].split("|") for i in config.getlist("d_nuisances", "samples")]
    samples = [list(map(str, sublist)) for sublist in samples]
    types = config.getlist("d_nuisances", "types") 
    
    nd = makeNuisDict(defname, name, types, samples)

    if not check_Nuisances(nd, h_dict):
        sys.exit("[ERROR] Nuisances specified in cfg file are not present in components dict ... Check inputs")
        

    for sample in h_dict:

        if bool(config.get("d_nuisances", "propagate")):
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
                f.write("            '{}' : {}, \n".format(sample, nd[key]['samples'][sample]))
            f.write("        {} \n".format("}"))

            f.write("{}\n".format("}"))
            f.write("\n\n")

        f.close()







        
        



