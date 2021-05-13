#!/usr/bin/env python
import os
import argparse
import sys
from glob import glob
import numpy as np
import ROOT 
from copy import deepcopy
from makeDummies import *
from configparser import ConfigParser

def fillDict(dict_, base_folder, prefix, models):
    for folder in glob(base_folder + "/*/"):
        op = folder.split(base_folder + "/" + prefix + "_")[-1].strip("/")
        if "_" in op:
            # Dosomething when 2D
            pass 

        dict_[op] = {} 

        for model in  models:
            if os.path.isfile(folder + model+ "/rootFile/histos.root"):
                dict_[op][model] = folder + model+ "/rootFile/histos.root"
            else:
                sys.exit("Missing histograms for {}".format(folder  + model+ "/rootFile/histos.root"))

    return

def mkdir(p):
   try:
      os.mkdir(p)
   except:
      return 

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Command line parser for ewk QCD combination of profiling. STRICTLY WORKS ONLY FOR EFTNeg ALGEBRA\n \
                                                    Usage: provide the ewk  and qcd folders generated with a cfg that specifies all the  ops ( [op1:op2:op3:...]). \n \
                                                    There should be only one subfolder for ewk  and qcd with structure: prefix_process_op1_op2_op3_...')
    parser.add_argument('--ewk',     dest='ewk',     help='Base folder for ewk BEFORE mkDatacards. Only one subfolder with all the ops', required = True)
    parser.add_argument('--qcd',     dest='qcd',     help='Base folder for QCD BEFORE mkDatacards. Only one subfolder with all the ops', required = True)
    parser.add_argument('--outprocess',     dest='outprocess',     help='Name of the final process', required = True)
    parser.add_argument('--cfg',     dest='cfg',     help='Give one config for parents processes in order to generate dummy Latinos files, or create a new one with only "d_" fields', required = True)
    parser.add_argument('--prefix_ewk',     dest='prefix_ewk',     help='Prefix of EWK folder including channel name separated by _ eg to_Latinos_SSWW', required = False, default="to_Latinos")
    parser.add_argument('--prefix_qcd',     dest='prefix_qcd',     help='Prefix of QCD folder including channel name separated by _ eg to_Latinos_OSWWQCD', required = False, default="to_Latinos")
    parser.add_argument('--outfolder',     dest='outfolder',     help='outfolder name', required = False, default="Combined_EWK_QCD")
    parser.add_argument('--qcdAsbkg',     dest='qcdAsbkg',     help='Always add the SM QCD shape as an additional bkg. No QCD dependence on EFT. Default False', default=False, action="store_true")

    args = parser.parse_args()

    ROOT.gROOT.SetBatch(1)

    #read dummy config, used only for dummy files
    config = ConfigParser(converters={'list': lambda x: [str(i.strip()) for i in x.split(',')]})
    config.read(args.cfg)

    # Defining useful variables

    ewk_channel = args.prefix_ewk.split("_")[-1]
    qcd_channel = args.prefix_qcd.split("_")[-1]

    ewkDict =  { }
    qcdDict =  { }

    fillDict(ewkDict, args.ewk, args.prefix_ewk, ["EFTNeg"]) #hardcoded EFTNeg. Can only treat bkg with this algebra
    fillDict(qcdDict, args.qcd, args.prefix_qcd, ["EFTNeg"])


    # Folder with most of the operators. For missing ones, the QCD will be appended as a background (separately)
    majorDict, majorProc = (ewkDict, ewk_channel) if len(ewkDict.keys()[0].split("_")) > len(qcdDict.keys()[0].split("_")) else (qcdDict, qcd_channel)
    minorDict, minorProc = (ewkDict, ewk_channel) if len(ewkDict.keys()[0].split("_")) <= len(qcdDict.keys()[0].split("_")) else (qcdDict, qcd_channel)

    # as SM is equal for all the op we just retrieve the first for  each variable
    # from the minority dict. we store it for each

    #if args.profiled: args.qcdAsbkg = True

    fallBack = {}
    fallBack["EFTNeg"] = {}
    op = minorDict.keys()[0]
    f = ROOT.TFile(minorDict[minorDict.keys()[0]]["EFTNeg"])
    tb = minorProc + "_" + [i.GetName() for i in f.GetListOfKeys()][0].split(minorProc + "_")[1]
    d = f.Get(tb) # this is related to the file structure after mkDCInput.py
    variables = [i.GetName() for i in d.GetListOfKeys()]
    for var in variables:
        fallBack["EFTNeg"][var] = deepcopy( f.Get(tb + "/" + var + "/histo_sm") )

    f.Close()

    # Beginning the combination

    mkdir(args.outfolder)

    # Logging results for checks
    added = []
    sole = []

    opmaj = majorDict.keys()[0].split("_")
    opmin = minorDict.keys()[0].split("_")

    #creating dirs
    mkdir(args.outfolder + "/to_Latinos_" + args.outprocess + "_" + majorDict.keys()[0] )
    outPath = args.outfolder + "/to_Latinos_" + args.outprocess + "_" + majorDict.keys()[0] + "/EFTNeg"
    mkdir( outPath)
    mkdir(outPath + "/rootFile" )

    fOut = ROOT.TFile(outPath + "/rootFile/histos.root", "RECREATE")
    fOut.mkdir(args.outprocess + "_" + majorDict.keys()[0] + "/")

    fMaj = ROOT.TFile(majorDict["_".join([op for op in opmaj])]["EFTNeg"])

    majGet = majorProc + "_" + "_".join([op for op in opmaj])

    dMaj = fMaj.Get(majGet)
    varMaj = [i.GetName() for i in dMaj.GetListOfKeys()]

    fMin = ROOT.TFile(minorDict["_".join([op for op in opmin])]["EFTNeg"])
    minGet = minorProc + "_" + "_".join([op for op in opmin])
    
    dMin = fMin.Get(minGet)
    varMin = [i.GetName() for i in dMin.GetListOfKeys()]

    if not all(i in varMaj for i in varMin):
        sys.exit("[ERROR] Found different variables check you inputs ... ")


    finalVars = list(varMaj)

    commonComponents = []
    NotcommonComponents = []
    # At this point vars are  equal so wecycle on either one
    for var in varMaj:

        fOut.mkdir(args.outprocess + "_" + majorDict.keys()[0]  + "/" + var + "/")
        fOut.cd(args.outprocess + "_" + majorDict.keys()[0]  + "/" + var + "/")

        dCMaj = fMaj.Get(majGet + "/" + var)
        dCMin = fMin.Get(minGet + "/" + var )

        compMaj = [i.GetName() for i in dCMaj.GetListOfKeys()]
        compMin = [i.GetName() for i in dCMin.GetListOfKeys()]

        finalComponent = [i.split("histo_")[1] for i in compMaj]
        
        #Theoretically always present? mkDatacards breaks otherwise i think
        hMaj = deepcopy( fMaj.Get(majGet + "/" + var + "/histo_DATA") )
        hMaj.Write("histo_DATA")

        if not args.qcdAsbkg:

            #grab sm and add them 

            hMaj = deepcopy( fMaj.Get(majGet + "/" + var + "/histo_sm") )
            hMin = deepcopy( fMin.Get(minGet + "/" + var + "/histo_sm") )

            #print("First Integral: {} Second Integral: {}".format(hMaj.Integral(), hMin.Integral()))
            hMaj.Add(hMin)
            #print("Summed Integral: {}".format(hMaj.Integral()))

            hMaj.Write("histo_sm")

            if "histo_sm" not in  commonComponents: commonComponents.append("histo_sm")

            # Major part: 
            # Componeent are divided in:
            # sm -> No EFT dependence, always sum pairwise with qcd shape (already did)
            # quad -> No SM dependence,  add pairwise with qcd if match found or write as it is (EWK) if no match
            # sm_lin_quad -> Sm dependence, Add pairwise with qcd if correspondence found (operator shared between EWK and QCD), else just add QCD SM
            # sm_lin_quad_mixed ->Sm dependence and 2 operators. Same as sm_lin_quad -> Also we must take care of op1_op2, op2-op1 commutations which may happen

            for component in compMaj:

                #case quad
                if "histo_quad" in component:
                    #if the component is also in the qcd (minor) dict then we sum pairwise QU = QU(EWK) + QU(QCD)
                    if component in compMin:
                        if component not in  commonComponents: commonComponents.append(component)
                        hMaj = deepcopy( fMaj.Get(majGet + "/" + var + "/" + component) )
                        hMin = deepcopy( fMin.Get(minGet + "/" + var + "/" + component) )
                        hMaj.Add(hMin)
                        hMaj.Write(component)
                    #else we only write ewk  QU=QU(EWK)
                    else:
                        if component not in  NotcommonComponents: NotcommonComponents.append(component)
                        hMaj = deepcopy( fMaj.Get(majGet + "/" + var + "/" + component) )
                        hMaj.Write(component)


                #case sm_lin_quad
                if "histo_sm_lin_quad" in component and "mixed" not in component:
                    #if the component is also in the qcd (minor) dict then we sum pairwise sm_li_qu = sm_li_qu(EWK) + sm_li_qu(QCD)
                    if component in compMin:
                        if component not in  commonComponents: commonComponents.append(component)
                        hMaj = deepcopy( fMaj.Get(majGet + "/" + var + "/" + component) )
                        hMin = deepcopy( fMin.Get(minGet + "/" + var + "/" + component) )
                        hMaj.Add(hMin)
                        hMaj.Write(component)
                    #else we only write ewk  QU=QU(EWK)
                    else:
                        if component not in  NotcommonComponents: NotcommonComponents.append(component)
                        hMaj = deepcopy( fMaj.Get(majGet + "/" + var + "/" + component) )
                        #here we retrieve the minor shape -> QCD SM shape
                        hMin = fallBack["EFTNeg"][var]
                        hMaj.Add(hMin)
                        hMaj.Write(component)

                #case sm_lin_quad
                if "histo_sm_lin_quad_mixed" in component:
                    ops  = component.split("histo_sm_lin_quad_mixed_")[1]
                    if component in compMin:
                        if component not in  commonComponents: commonComponents.append(component)
                        hMaj = deepcopy( fMaj.Get(majGet + "/" + var + "/" + component) )
                        hMin = deepcopy( fMin.Get(minGet + "/" + var + "/" + component) )
                        hMaj.Add(hMin)
                        hMaj.Write(component)
                    #takes care of op1_op2 or op2_op1 differences
                    elif "histo_sm_lin_quad_mixed_" + "_".join(ops[::-1]) in compMin:
                        if component not in  commonComponents: commonComponents.append(component)
                        hMaj = deepcopy( fMaj.Get(majGet + "/" + var + "/" + component) )
                        hMin = deepcopy( fMin.Get(minGet + "/" + var + "/" + "histo_sm_lin_quad_mixed_" + "_".join(ops[::-1])) )
                        hMaj.Add(hMin)
                        hMaj.Write(component)

                    #else we only write ewk  sm_li_qu_mix = sm(ewk) + sm(qcd) + lin1(ewk) + lin2(ewk) + quad1(ewk) + quad2(ewk) + mix12(ewk)
                    else:
                        if component not in  NotcommonComponents: NotcommonComponents.append(component)
                        hMaj = deepcopy( fMaj.Get(majGet + "/" + var + "/" + component) )
                        #here we retrieve the minor shape -> QCD SM shape
                        hMin = fallBack["EFTNeg"][var]
                        hMaj.Add(hMin)
                        hMaj.Write(component)

        else:

            finalComponent.append("QCD_" + minorProc)

            #Just copy the major  dict component
            for comp in compMaj:
                if component not in  NotcommonComponents: NotcommonComponents.append(comp)
                hMaj = deepcopy( fMaj.Get(majGet + "/" + var + "/" + comp) )
                hMaj.Write(comp)
            
            # And append the SM component with a name != from combine model names
            hSM_bkg = fallBack["EFTNeg"][var]
            #god knows why Write does not overwrite object name...
            hSM_bkg.SetName("histo_QCD_" + minorProc)
            hSM_bkg.Write("histo_QCD_" + minorProc)

    fOut.Write()
    fOut.Close()

    # Generate Dummies
    sample = args.outprocess + "_" + majorDict.keys()[0] #just to make a dict name compatible with dummy maker
    print("[INFO] Generating dummies ...")
    if config.get("d_structure", "makeDummy") == "True"        : makeStructure({sample: finalComponent}, "EFTNeg", outPath, isMkDC = False)
    if config.get("d_plot", "makeDummy") == "True"             : makePlot({sample: finalComponent}, "EFTNeg", config, outPath, isMkDC = False)
    if config.get("d_samples", "makeDummy") == "True"          : makeSamples({sample: finalComponent}, "EFTNeg", config, outPath, isMkDC = False)
    if config.get("d_configuration", "makeDummy") == "True"    : makeConfiguration({sample: finalComponent}, "EFTNeg", config, outPath)
    if config.get("d_alias", "makeDummy") == "True"            : makeAliases({sample: finalComponent}, "EFTNeg", outPath)
    if config.get("d_cuts", "makeDummy") == "True"             : makeCuts({sample: finalComponent}, "EFTNeg", outPath)
    if config.get("d_variables", "makeDummy") == "True"        : makeVariables({sample: dict.fromkeys(finalVars)}, "EFTNeg", config, outPath)
    if config.get("d_nuisances", "makeDummy") == "True"        : makeNuisances({sample: finalComponent}, "EFTNeg", config, outPath, isMkDC = False)
        
    

    print("[INFO] Conclusions ...")
    qu = []
    slq = []
    slqm = []
    for i in commonComponents:
        if "histo_quad"  in i: qu.append(i)
        if "histo_sm_lin_quad"  in i and "mixed" not in i: slq.append(i)
        if "histo_sm_lin_quad_mixed"  in i: slqm.append(i)
    print("[INFO] The following components are shared and contributions summed {}".format(len(commonComponents)))
    print("------------- QUAD -----------")
    print(len(qu), qu)
    print("------------- SM+LIN+QUAD -----------")
    print(len(slq), slq)
    print("------------- SM+LIN+QUAD+MIXED -----------")
    print(len(slqm), slqm)
    print("-----------------------")
    print("-----------------------")
    print("-----------------------")
    qu = []
    slq = []
    slqm = []
    for i in NotcommonComponents:
        if "histo_quad"  in i: qu.append(i)
        if "histo_sm_lin_quad"  in i  and "mixed" not in i: slq.append(i)
        if "histo_sm_lin_quad_mixed"  in i: slqm.append(i)
    print("The following components are not shared. Contributions only from SM summed or ass bkg if specified {}".format(len(NotcommonComponents)))
    print("------------- QUAD -----------")
    print(len(qu), qu)
    print("------------- SM+LIN+QUAD -----------")
    print(len(slq), slq)
    print("------------- SM+LIN+QUAD+MIXED -----------")
    print(len(slqm), slqm)
    print("-----------------------")
    print("-----------------------")
    print("-----------------------")