from configparser import ConfigParser
from worker import Worker
import time
import sys
from multiprocessing import Manager

class WorkerLeader():

    def __init__(self, file_dict, nWorkers=1):

        self.file_dict = file_dict
        self.nWorkers = nWorkers
        self.histos = []

    def setVars(self, vars):
        self.vars = vars 
    
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
            print(s)
            self.baseDict[s] = {}


    def initializeWorkers(self):
        
        print("---> nWorkers: {}".format(self.nWorkers))
        k = self.file_dict.keys() #{'inWW_cHl3': {'LI_cHl3': ['path'] }, 'QU_cHl3': ['path'], 'SM': ['path']}, 'inWW_cHl1': ...}

        self.flattened = []
        id_ = 0
        for key in self.file_dict.keys(): #[inWW_cHl3, inWW_cHl1, ...]
            for comp in self.file_dict[key].keys(): # ['LI_cHl3', 'QU_cHl3', 'SM']
                for path in self.file_dict[key][comp]:
                    self.flattened.append({'idx': id_, 's': key, 'comp': comp, 'path': path})
                    id_ += 1


        step = len(self.flattened) / self.nWorkers

        if step * self.nWorkers < len(self.flattened): step+=1 

        self.k_split = [self.flattened[i:i+step] for i in range(0, len(self.flattened), step)] # nWorker lists with file components
        
        self.histoSetDict = {
            'vars': self.vars,
            'bins': self.bins,
            'binsize': self.binsize,
            'ranges': self.ranges,
            'hn': self.histo_name,
            'lumi': self.lumi,
            'fillMissing': self.fillMissing_,
            'cut': self.cut,
        }

        self.workers = []

        for fl in self.k_split:
            self.workers.append(Worker(fl, self.histoSetDict))

        print("----> INFO: Workers Ready")

    def startWorkers(self):

        start = time.time()

        
        for w in self.workers:
            #w.runWorker()
            p = w.start()

        for w in self.workers:
            w.join()

        stop = time.time()
        
        print("---> INFO: FINISHED FILLING")

        print("Took {:0.4f} seconds".format(stop-start))

    def joinWorkerDicts(self):
        d = {}
        for worker in self.workers:
            fl = worker.histos
            for key in fl.keys():
                if key not in d.keys(): d[key] = {}

                for component in fl[key].keys():
                    if component not in d[key].keys(): d[key][component] = fl[key][component]

        return d

