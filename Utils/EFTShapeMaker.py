from dcInputGeneralUtils import cleanNames
from copy import deepcopy
from itertools import combinations
import ROOT

def histosToModel(histo_dict, fillMissing = True):
    print("[INFO]: Converting base model to EFT...")
    return  cleanNames(deepcopy(histo_dict))

def addSMHistogramAsDefault(model_dict):
    """
        It may happen that sometime an interferencee term does not exist for a process.
        But the combine model expects a bin. Workaround -> the  interference is 0 so if the model
        expects Sm + Li1 + Li2 + Qu1 + Qu2 + INT we give him SM + Li1 + Li2 + Qu1 + Qu2
    """

    #there is no way to assume k = 0 for the EFT, each component is independent of sm
    return model_dict