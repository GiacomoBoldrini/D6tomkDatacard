from itertools import combinations
from dcInputGeneralUtils import cleanDuplicates, redemensionOpinput
from glob import glob

def retireve_samples(config):

    print("[INFO] Retrieving samples ...")
    section = "ntuples"
    sample = config.getlist("general", "sample")
    folders = config.getlist(section, "folder")
    #ops = config.getlist("eft", "operators")
    ops_ = redemensionOpinput(config)
    sample_headers = [i + "_" + "_".join(op for op in k) for i,k in zip(sample,ops_)]

    file_dict = dict.fromkeys(sample_headers)

    for sh, s,ops in zip(sample_headers, sample, ops_):
        file_dict[sh] = {}

        int_ = len(ops) > 1

        comb = list(combinations(ops, 2))
        comb2 = [(i[1],i[0]) for i in comb] #reverse in case of wrong ordering

        #scan simple ops
        for op in ops:
            file_dict[sh]
            file_dict[sh]["QU_{}".format(op)] = []
            file_dict[sh]["LI_{}".format(op)] = []


            for folder in folders:
                files = glob(folder + "/*_" + s + "_" + op + "_*.root")
                for file_ in files:
                    if "QU" in file_: file_dict[sh]["QU_{}".format(op)].append(file_)
                    if "LI" in file_: file_dict[sh]["LI_{}".format(op)].append(file_)

            file_dict[sh]["QU_{}".format(op)] = cleanDuplicates(file_dict[sh]["QU_{}".format(op)])
            file_dict[sh]["LI_{}".format(op)] = cleanDuplicates(file_dict[sh]["LI_{}".format(op)])

            if len(file_dict[sh]["QU_{}".format(op)]) == 0:
                print("[WARNING] Missing interference sample for op {}".format(op))
            if len(file_dict[sh]["LI_{}".format(op)]) == 0:
                print("[WARNING] Missing interference sample for op {}".format(op))
                              
        #scan interference if present
        if int_:
            for c1, c2 in zip(comb, comb2):
                file_dict[sh]["IN_{}_{}".format(c1[0], c1[1])] = []
                file_dict[sh]["IN_{}_{}".format(c2[0], c2[1])] = []

                files1 = []
                files2 = []

                for folder in folders:
                    #either cG_cGtil or cGtil_cG, not both (repetition should be avoided)
                    files1 += glob(folder + "/*_" + s + "_{}_{}_".format(c1[0], c1[1]) + "*.root")
                    files2 += glob(folder + "/*_" + s + "_{}_{}_".format(c2[0], c2[1]) + "*.root")

                if len(files1) != 0 and len(files2) == 0: 
                    files = files1
                    c = c1
                    del file_dict[sh]["IN_{}_{}".format(c2[0], c2[1])]
                elif len(files1) == 0 and len(files2) != 0: 
                    files = files2
                    c = c2
                    del file_dict[sh]["IN_{}_{}".format(c1[0], c1[1])]
                else: #interference does not exist (can happen!) delete the fields so makeHistos do not see this
                    print("[WARNING] Missing interference sample for pair {},{}".format(c1[0], c1[1]))
                    del file_dict[sh]["IN_{}_{}".format(c1[0], c1[1])]
                    #del file_dict[sh]["IN_{}_{}".format(c2[0], c2[1])]
                    continue
                
                #don't remember what this check is for...
                for file_ in files:
                    if "IN" in file_: file_dict[sh]["IN_{}_{}".format(c[0], c[1])].append(file_)

                if "IN_{}_{}".format(c1[0], c1[1]) in file_dict[sh]:
                    if len(file_dict[sh]["IN_{}_{}".format(c1[0], c1[1])]) == 0:
                        sys.exit("[ERROR] Missing Interference sample for op pair {} {}".format(c1[0], c1[1]))

                if "IN_{}_{}".format(c2[0], c2[1]) in file_dict[sh]:
                    if len(file_dict[sh]["IN_{}_{}".format(c2[0], c2[1])]) == 0:
                        sys.exit("[ERROR] Missing Interference sample for op pair {} {}".format(c2[0], c2[1]))

                file_dict[sh]["IN_{}_{}".format(c[0], c[1])] = cleanDuplicates(file_dict[sh]["IN_{}_{}".format(c[0], c[1])])
                    

        sm_fl = []
        for folder in folders:
            sm_fl += glob(folder + "/*" + s + "*SM.root")

        sm_fl = cleanDuplicates(sm_fl)

        file_dict[sh]["SM"] = sm_fl

    return file_dict