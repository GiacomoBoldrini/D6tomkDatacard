import threading 
import numpy as np
import ROOT
import sys 
import math as mt
from copy import deepcopy
import multiprocessing
from multiprocessing import Manager

class Worker(multiprocessing.Process):

    def __init__(self, fileList, histoSetDict):

        super(Worker, self).__init__()

        self.baseDict = {}
        self.fileList = fileList
        self.histoSetDict = histoSetDict
        self.run_event = threading.Event()
        self.manager = Manager()
        self.histos = self.manager.dict()


    def mkLogHisto(self, v, b, low, up):

        #low = 0 is not admiitted
        if low == 0: low = sys.float_info.min
        if low < 0:
            sys.exit("[ERROR] Log scale in a negative range. Check .cfg ...")
        edges = np.logspace(mt.log(low,10), mt.log(up,10), b+1)
        htemp = ROOT.TH1D(v + "_temp", v + "_temp", b, edges)
        return htemp

    def retrieveHisto(self, name, paths, tree, var, bins, binsize, ranges, luminosity, cuts):
        
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
                h = ROOT.TH1D(name, v, b, r[0], r[1])

            if bs == "log":
                h = self.mkLogHisto(name, b, r[0], r[1])

            elif bs != "fix" and bs !=  "log":
                sys.exit("[ERROR] Choose binsize between log and fix ... ")

            print("[INFO] @ Filling  {} histo, bins: {}, binsize: {}, range: {} ...".format(v, b, bs, r))

            for path in paths:
                f = ROOT.TFile(path)
                t = f.Get(tree)

                if bs == "fix":
                    htemp = ROOT.TH1D(v + "_temp", v + "_temp", b, r[0], r[1])

                elif bs == "log":
                    htemp = self.mkLogHisto(v, b, r[0], r[1])

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
            print("[INFO] @ Filling {} {} histo dummy ...".format(name, v))
            if bs == "fix":
                h = ROOT.TH1D(name + "_" + v, name, b, r[0], r[1])

            if bs == "log":
                h = mkLogHisto(name + "_" + v, b, r[0], r[1])

            elif bs != "fix" and bs !=  "log":
                sys.exit("[ERROR] Choose binsize between log and fix ... ")
            #h = ROOT.TH1D(name + "_" + v, name, b, r[0], r[1])
            for i in range(1, b):
                h.SetBinContent(i,0)

            th_dict[v] = deepcopy(h)

        return th_dict

    def run(self):

        print("Starting ...")
        
        for idx, f in enumerate(self.fileList):
            s = self.fileList[idx]["s"]
            paths = self.fileList[idx]["path"]
            component = self.fileList[idx]["comp"]
            
            if s not in self.histos.keys():
                self.histos[s] = self.manager.dict()

            curr_hist = self.histos[s]

            curr_hist[component] = self.manager.dict()


            if len(paths) != 0:
                print("[INFO] @ ---- Starting filling histos for component: {} ---- \
                \n ---------- @ @ @ @ @ @ @ ---------- ".format(component))

                for var, bins_, binsize_, ranges_ in zip(self.histoSetDict["vars"], self.histoSetDict["bins"], self.histoSetDict["binsize"], self.histoSetDict["ranges"]) :
                    nt = (paths.split("/ntuple_")[1]).split(".root")[0]
                    curr_hist[component][var] = self.retrieveHisto( s+"_"+component, [paths], nt, var, bins_, binsize_, ranges_, self.histoSetDict["lumi"], self.histoSetDict["cut"]).items()[0][1]
                    
            elif self.histoSetDict["fillMissing"]:
                print("[WARNING] Missing component for component {} but fillMissing = 1 so filling it with a 0 content histo ...".format(component))
                print("[INFO] @ ---- Starting filling histos for component: {} ---- \
                \n ---------- @ @ @ @ @ @ @ ---------- ".format(component))

                for var, bins_, binsize_, ranges_ in zip(self.histoSetDict["vars"], self.histoSetDict["bins"], self.histoSetDict["binsize"], self.histoSetDict["ranges"]) :
                    curr_hist[component][var] = self.retrieveDummy( s+"_"+component, var, bins_, binsize_, ranges_).items()[0][1]

            self.histos[s] = curr_hist
        

    def isRunning(self):
        return self.run_event.is_set()