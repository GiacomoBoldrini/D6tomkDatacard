from configparser import ConfigParser
from worker import Worker
import time
import sys
from multiprocessing import Manager

class WorkerLeader():

    def __init__(self, file_dict, nWorkers=1, dum=[]):

        self.file_dict = file_dict
        self.nWorkers = nWorkers
        self.dum = dum
        self.histos = []

    def setVars(self, vars):
        self.vars = vars 

    def setCppVars(self, vars):
        self.cppvars = vars 
    
    def setBins(self, bins):
        self.bins = bins

    def setBinSize(self, binsize):
        self.binsize = binsize 

    def setRanges(self, ranges):
        self.ranges = ranges 

    def setHistoNames(self, histo_name):
        self.histo_name = histo_name

    def setLumi(self, lumi):
        self.lumi = lumi

    def setFillMissing(self, fillMissing):
        self.fillMissing_ = fillMissing

    def setCut(self, cut):
        self.cut = cut 

    def setBaseDict(self, baseDictKeys ):
        self.baseDictKeys = baseDictKeys
        self.baseDict = {}
        for s in baseDictKeys:
            self.baseDict[s] = {}


    def initializeWorkers(self):
        
        k = self.file_dict.keys() #{'inWW_cHl3': {'LI_cHl3': ['path'] }, 'QU_cHl3': ['path'], 'SM': ['path']}, 'inWW_cHl1': ...}

        self.flattened = []
        id_ = 0
        for key in self.file_dict.keys(): #[inWW_cHl3, inWW_cHl1, ...]
            for comp in self.file_dict[key].keys(): # ['LI_cHl3', 'QU_cHl3', 'SM']
                for path in self.file_dict[key][comp]:
                    self.flattened.append({'idx': id_, 's': key, 'comp': comp, 'path': path})
                    id_ += 1

                #dummy!
                if len(self.file_dict[key][comp]) == 0:
                    self.flattened.append({'idx': id_, 's': key, 'comp': comp, 'path': ''})
                    id_ += 1


        step = len(self.flattened) / self.nWorkers

        if step * self.nWorkers < len(self.flattened): step+=1 

        self.k_split = [self.flattened[i:i+step] for i in range(0, len(self.flattened), step)] # nWorker lists with file components
        
        self.histoSetDict = {
            'vars': self.vars,
            'cppvars': self.cppvars,
            'bins': self.bins,
            'binsize': self.binsize,
            'ranges': self.ranges,
            'hn': self.histo_name,
            'lumi': self.lumi,
            'fillMissing': self.fillMissing_,
            'cut': self.cut,
            'dummies': self.dum,
        }

        self.Worker = Worker(self.flattened, self.histoSetDict, nThreads=self.nWorkers)

    def startWorkers(self):

        start = time.time()

        self.baseDict = self.Worker.run()

        stop = time.time()
        
        print("---> INFO: FINISHED FILLING")

        print("Took {:0.4f} seconds".format(stop-start))

        return self.baseDict
