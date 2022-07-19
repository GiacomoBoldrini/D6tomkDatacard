import numpy as np
import math as mt
import ROOT
import sys 
from copy import deepcopy
import os


class Worker():

    def __init__(self, fileList, histoSetDict, nThreads=1):

        #super(Worker, self).__init__()

        self.baseDict = {}
        self.fileList = fileList
        self.histoSetDict = histoSetDict
        self.histos = {}
        self.dataframes = []

        ROOT.EnableImplicitMT(nThreads)


    def mkLogHisto(self, name, b, low, up):

        #low = 0 is not admiitted
        if low == 0: low = sys.float_info.min
        if low < 0:
            sys.exit("[ERROR] Log scale in a negative range. Check .cfg ...")
        edges = np.logspace(mt.log(low,10), mt.log(up,10), b+1)
        return (name, name, b, edges)

    def mkFixHisto(self, name, b, low, up):
        return (name, name, b, low, up)


    def retrieveDummy(self, name, var, bins, binsize, ranges):

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
                template = self.mkFixHisto(name, b, r[0], r[1])
                h = ROOT.TH1D(*template)

            if bs == "log":
                template = self.mkLogHisto(name, b, r[0], r[1])
                h = ROOT.TH1D(*template)

            elif bs != "fix" and bs !=  "log":
                sys.exit("[ERROR] Choose binsize between log and fix ... ")
            #h = ROOT.TH1D(name + "_" + v, name, b, r[0], r[1])
            for i in range(1, b):
                h.SetBinContent(i,0)

            th_dict[v] = deepcopy(h)

        return th_dict

    def run(self):

        print("Starting ...")

        hists = []
        
        for idx, f in enumerate(self.fileList):
            s = self.fileList[idx]["s"]
            paths = self.fileList[idx]["path"]
            component = self.fileList[idx]["comp"]
            
            if s not in self.histos.keys():
                self.histos[s] = {}

            curr_hist = self.histos[s]

            curr_hist[component] = {}

            if len(paths) != 0:

                print("[INFO] @ ---- Starting filling histos for component: {} ---- \
                \n ---------- @ @ @ @ @ @ @ ---------- ".format(component))

                nt = (paths.split("/ntuple_")[1]).split(".root")[0]

                self.dataframes.append(ROOT.RDataFrame(nt, paths))

                for external_var in self.histoSetDict["cppvars"]:
                    self.dataframes[-1] = self.dataframes[-1].Define(external_var[0], external_var[1])

                # hists = []
                # for var, bins_, binsize_, ranges_ in zip(self.histoSetDict["vars"], self.histoSetDict["bins"], self.histoSetDict["binsize"], self.histoSetDict["ranges"]) :
                #     print("[INFO] @ Filling  {} histo, bins: {}, binsize: {}, range: {} ...".format(var, bins_, binsize_, ranges_))
                #     if binsize_ == "fix":
                #         template = self.mkFixHisto(s + "_"+component + "_" + var, bins_, ranges_[0], ranges_[1])
                #     if binsize_ == "log":
                #         template = self.mkLogHisto(s + "_"+component + "_" + var, bins_, ranges_[0], ranges_[1])

                #     hists.append(self.dataframes[-1].Filter(self.histoSetDict["cut"]).Histo1D(template, var, "w"))


                # #trigger filling
                # h = [i.GetValue() for i in hists]
                # for v_, h_ in zip(self.histoSetDict["vars"], h): curr_hist[component][v_] = h_ 

                for var, bins_, binsize_, ranges_ in zip(self.histoSetDict["vars"], self.histoSetDict["bins"], self.histoSetDict["binsize"], self.histoSetDict["ranges"]) :
                    print("[INFO] @ Filling  {} histo, bins: {}, binsize: {}, range: {} ...".format(var, bins_, binsize_, ranges_))
                    if binsize_ == "fix":
                        template = self.mkFixHisto(s + "_"+component + "_" + var, bins_, ranges_[0], ranges_[1])
                    if binsize_ == "log":
                        template = self.mkLogHisto(s + "_"+component + "_" + var, bins_, ranges_[0], ranges_[1])

                    #hists.append(self.dataframes[-1].Filter(self.histoSetDict["cut"]).Histo1D(template, var, "w"))
                    curr_hist[component][var] = self.dataframes[-1].Filter(self.histoSetDict["cut"]).Histo1D(template, var, "w")
                    hists.append(curr_hist[component][var])

                # trigger filling
                # h = [i.GetValue() for i in hists]
                # for v_, h_ in zip(self.histoSetDict["vars"], h): curr_hist[component][v_] = h_ 


            elif self.histoSetDict["fillMissing"]:
                print("[WARNING] Missing component for component {} but fillMissing = 1 so filling it with a 0 content histo ...".format(component))
                print("[INFO] @ ---- Starting filling histos for component: {} ---- \
                \n ---------- @ @ @ @ @ @ @ ---------- ".format(component))

                for var, bins_, binsize_, ranges_ in zip(self.histoSetDict["vars"], self.histoSetDict["bins"], self.histoSetDict["binsize"], self.histoSetDict["ranges"]) :
                    print("[INFO] @ Filling  {} histo, bins: {}, binsize: {}, range: {} ...".format(var, bins_, binsize_, ranges_))
                    curr_hist[component][var] = self.retrieveDummy( s+"_"+component, var, bins_, binsize_, ranges_).items()[0][1]

            self.histos[s] = curr_hist

        #triggering histo filling

        for k in self.histos.keys():
            for comp in self.histos[k].keys():
                if comp in self.histoSetDict["dummies"]: continue
                for var in self.histos[k][comp].keys():
                    print("Triggering Sample {}, variable {}".format(comp, var))
                    self.histos[k][comp][var] = self.histos[k][comp][var].GetValue()

        return self.histos
        