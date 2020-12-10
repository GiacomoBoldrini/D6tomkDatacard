#!/usr/bin/env python
import ROOT
import os
from glob import glob
import sys
from configparser import ConfigParser
import argparse
import numpy as np
from copy import deepcopy

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Command line parser to remove quadratic component after mkDCInput, before mkDatacard')
    parser.add_argument('--cfg',     dest='cfg',     help='Config file with infos about samples/variables/...', 
                       required = True)
    parser.add_argument('--after_mkD',     dest='after_mkD',     help='if the folder was generated after mkDatacard', required = False, default = "False", action="store_true")

    args = parser.parse_args()
    
    #reading the configuration
    config = ConfigParser(converters={'list': lambda x: [str(i.strip()) for i in x.split(',')]})
    config.read(args.cfg)

    outdir = str(config.get("general", "outfolder"))
    outprefix = str(config.get("general", "folder_prefix"))
    outfile = str(config.get("general", "outfile"))
    models = config.getlist("eft", "models")
    h_folder = "/rootFile"
    vars_ = config.getlist("variables", "treenames")

    #retrieve every subfolder for each operator
    subf = glob(outdir + "/*/")

    #cycle on the subfolders    
    for s in subf:
        
        #retrieve process, ops from subfolder name
        fol_name = s.split("/")[-2]
        process = fol_name.split(outprefix)[1]
        process = process.strip(" ")

        ops = process.split("_")[1:]
        proc = process.split("_")[0]

        print(". . . @ @ @ Running in {} @ @ @ . . .".format(s))
        print("[INFO] Models: {}".format(" ".join(m for m in models)))
        print("[INFO] Variables: {}".format(" ".join(v for v in vars_)))

        #cycling on the models in the config file
        for model in models:

            file_n = s + "/" + model
            if args.after_mkD == "True": file_n += "/datacards"
            file_n += "/" + h_folder + "/" + outfile
            file_ = str(file_n)
            df = {}
            f = ROOT.TFile(file_n, "UPDATE")

            for var in vars_:

                df[var] = {}
                
                #retrieve TDirectory that stores the histo for a specific var
                d = f.Get(str(process + "/" + var))
                #get the histo names histo_ + proc + operatorss involved
                histos = [i.GetName() for i in d.GetListOfKeys()]

                #defining the components we want to put at zero
                q_ = "quad_"
                h_q = [i for i in histos if q_ in i]

                #base
                quad_names = ["histo_" + q_ + str(op) for op in ops]
                quad_histos = [[key, deepcopy(d.Get(key))] for key in quad_names]

                #touched
                derived_names = [str(key) for key in histos if key not in quad_names and q_ in key and any(i in key for i in ops)]
                derived_histos = [[key, deepcopy(d.Get(key))] for key in derived_names]

                #untouched
                others_name = [str(key) for key in histos if key not in quad_names and key not in derived_names]
                others_histos = [[key, deepcopy(d.Get(key))] for key in others_name]
                
                if len(derived_names) > 0:
                    for i in range(len(quad_histos)):
                        for j in range(len(derived_histos)):
                            if quad_histos[i][0].split("_")[2] in derived_histos[j][0]:
                                derived_histos[j][1].Add(quad_histos[i][1], -1)
                        quad_histos[i][1].Reset()

                else:
                    for i in range(len(quad_histos)):
                        quad_histos[i][1].Reset()

                #ugly ... But does the work
                for dh in derived_histos:
                    df[var][dh[0]] = dh[1]
                
                for dh in others_histos:
                    df[var][dh[0]] = dh[1] 
                
                for dh in quad_histos:
                    df[var][dh[0]] = dh[1]

            f.Close()
            #oper new temporary files to copy and paste new histos  
            fout = ROOT.TFile(file_n.replace(outfile, '') + "tmp.root", "RECREATE")
            fout.mkdir(str(process))

            for var in vars_:
                fout.mkdir(str(process + "/" + var))
                for key in df[var].keys():
                    fout.cd(str(process + "/" + var))
                    df[var][key].Write(key)

            fout.Write()
            fout.Close()

            #remove old file and replace it with the new one with previous name
            os.system("rm {}".format(file_n))
            os.system("mv {} {}".format(file_n.replace(outfile, '') + "tmp.root", file_n))

    print(". . . @ @ @ Done @ @ @ . . .")