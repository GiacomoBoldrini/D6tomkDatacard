#!/usr/bin/env python
import os
import argparse
import sys
from glob import glob
import numpy as np
import ROOT 

def mkdir(path):
    try:
        os.system("mkdir {}".format(path))
    except:
        pass

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Command line parser for comparing shapes between two mkDCInput shape folders')
    parser.add_argument('-f', '--folders',    dest='folder',     help='folders to compare shapes', required = True, nargs="+")
    parser.add_argument('-o', '--ops',        dest='ops',     help='compare only these operators', required = False, nargs="+", default=[])
    parser.add_argument('-l', '--leg',        dest='legend',     help='legend label pairwise with folders', required = False, nargs="+", default=[])
    parser.add_argument('-io', '--ignore-op',        dest='ignoreop',     help='Ignore operators', required = False, nargs="+", default=[])
    parser.add_argument('-v', '--vars',       dest='vars',     help='compare only these variables (TBranches)', required = False, nargs="+", default=[])
    parser.add_argument('-ou', '--output',       dest='output',     help='Output folder', required = False, default="plots")

    args = parser.parse_args()

    ROOT.gROOT.SetBatch(1)
    ROOT.gStyle.SetPalette(ROOT.kRainBow)
    ROOT.gStyle.SetOptStat(0)

    model = "EFT"

    files = [glob(i + "/to_Latinos*/EFT/rootFile/histos.root") for i in args.folder]
    ops = []

    for i in files:
        ops_ = []
        for p in i:
            op = p.split("to_Latinos_")[1].split("/")[0].split("_")[1]
            if op not in args.ignoreop: 
                if len(args.ops) == 0 or op in args.ops: ops_.append(op)
                else: pass
                

        ops.append(ops_)
    print(ops)
    if not all(set(ops[0]) == set(i) for i in ops[1:]): sys.exit("ahia")
    
    ops_dict = {}
    for op in ops[0]:
        ops_dict[op] = []
        for file_l in files:
            for file in file_l:
                op_ = file.split("to_Latinos_")[1].split("/")[0].split("_")[1]
                if op == op_: ops_dict[op].append(file)

    mkdir(args.output)

    #retrieve components and vars
    orig_file = ops_dict[ops_dict.keys()[0]][0]
    f = ROOT.TFile(orig_file)
    d = f.Get([i.GetName() for i in f.GetListOfKeys()][0])
    variables = [i.GetName() for i in d.GetListOfKeys()]
    #c = d.Get(variables[0])
    #components = [i.GetName() for i in c.GetListOfKeys()]
    f.Close()

    for op in ops_dict.keys():
        files = [ROOT.TFile(i) for i in ops_dict[op]]
        dir_ = [[i.GetName() for i in r.GetListOfKeys()][0] for r in files]
    
        for var in variables:
            comps = [f.Get(d + "/" + var) for f,d in zip(files, dir_)]
            components = [[i.GetName() for i in r.GetListOfKeys()] for r in comps]
            if not all(set(components[0]) == set(i) for i in components[1:]): sys.exit("ahia")
            components = components[0]

            for comp in components:
                name = op + "_" + var + "_" + comp 

                hs = [f.Get(j + "/" + var + "/" + comp) for f,j in zip(files, dir_)]
                
                c = ROOT.TCanvas("c", "c", 1000, 1000)
                
                hs[0].SetLineWidth(2)
                hs[0].Draw("hist PLC E")
                for i in hs[1:]:
                    i.SetLineWidth(2)
                    i.Draw("hist PLC E same")

                if len(args.legend):
                    leg = ROOT.TLegend(0.89, 0.89, 0.7, 0.7)
                    leg.SetBorderSize(0)
                    for i,j in zip(hs, args.legend):
                        leg.AddEntry(i, j, "F")

                    leg.Draw()

                c.Draw()
                c.Print(args.output + "/" + name + ".png")
                c.Print(args.output + "/" + name + ".pdf")


    os.system("cp /afs/cern.ch/user/g/gboldrin/public/index.php " + args.output)
    
