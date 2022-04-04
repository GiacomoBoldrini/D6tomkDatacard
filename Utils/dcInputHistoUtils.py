import numpy as np
import ROOT
from copy import deepcopy

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


def retrieveDummy(name, var, bins, binsize, ranges):

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
        print("[INFO] @ Filling {} histo dummy ...".format(v))
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