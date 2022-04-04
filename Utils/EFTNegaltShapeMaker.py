from dcInputGeneralUtils import cleanNames
from copy import deepcopy
from itertools import combinations
import ROOT

def histosToModel(histo_dict, fillMissing = True):

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
            #if len(linear) != 1:
            #    if len(mixed) != mt.factorial(len(linear)) / (mt.factorial(2) * mt.factorial(len(linear)-2)) or len(sm) != 1: 
            #        sys.exit("[ERROR] errors in the combinatorial, Probably you are missing some interference samples for the op you specified ...")

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

    the_cleaned_dict = cleanNames(deepcopy(eft_negalt_dict))
    #if fillMissing: the_cleaned_dict = addSMHistogramAsDefault(deepcopy(the_cleaned_dict), model_type)
    return the_cleaned_dict
    #return cleanNames(deepcopy(eft_negalt_dict))

def addSMHistogramAsDefault(model_dict):
    """
        It may happen that sometime an interferencee term does not exist for a process.
        But the combine model expects a bin. Workaround -> the  interference is 0 so if the model
        expects Sm + Li1 + Li2 + Qu1 + Qu2 + INT we give him SM + Li1 + Li2 + Qu1 + Qu2
    """

    ops = [] # single operators
    for sample in model_dict.keys():
        for var in model_dict[sample].keys():
            for c in model_dict[sample][var].keys():
                if "quad" in c: #quad is the only component common to every model and should be present for each op
                    op = c.split("_")[-1] #last is the op (don't worry about two ops)
                    if op not in ops: ops.append(op)

    op_pairs = list(combinations(ops, 2)) #for interferences

    sm_lin_quad = ["sm_lin_quad_" + i for i in ops] #common to all models
    mixed_EFTNegalt = "quad_mixed_"

    for sample in model_dict.keys():
        for var in model_dict[sample].keys():
            components = model_dict[sample][var].keys()
            h_sm = deepcopy(model_dict[sample][var]["sm"])
            to_be_filled = list(set(sm_lin_quad).difference(components))
            for i in to_be_filled:
                print("[INFO] addSMHistogramAsDefault: var {} creating {}".format( var , i))
                model_dict[sample][var][i] = h_sm

            for op_p in op_pairs:
                if not mixed_EFTNegalt + op_p[0] + "_" + op_p[1] in components and not mixed_EFTNegalt + op_p[1] + "_" + op_p[0] in components:
                    print("[INFO] addSMHistogramAsDefault: var {} creating {} ".format( var, mixed_EFTNegalt + op_p[0] + "_" + op_p[1]))
                    h_int = deepcopy(model_dict[sample][var]["sm"])
                    h_int.Reset("ICESM") #Resetting hissto conteent errorss min max and stats and integral
                    #quad should exist for both operators
                    h_int.Add(model_dict[sample][var]["quad_" + op_p[0]])
                    h_int.Add(model_dict[sample][var]["quad_" + op_p[1]])

                    model_dict[sample][var]["quad_mixed_" + op_p[0] + "_" + op_p[1]] = h_int

    return model_dict