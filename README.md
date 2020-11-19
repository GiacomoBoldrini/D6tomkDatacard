# D6tomkDatacard

Framework to convert the output of MG5 generation with EFT components in readable histos for mkDatacards.py in the Latino framework.
This framework allows to create histograms allowing the exploitation of different combine physics model under the AnalyticAnomalousCoupling repo.

Useful links:
* Latinos: https://github.com/latinos/LatinoAnalysis 

* mkDatacard.py: https://github.com/latinos/LatinoAnalysis/blob/master/ShapeAnalysis/scripts/mkDatacards.py 

* example folder: https://github.com/amassiro/PlotsConfigurationsCMSDAS2020CERN/tree/master/ControlRegions/DY 

* D6EFT study for generation: https://github.com/UniMiBAnalyses/D6EFTStudies

* Latino tutorial CmsDas h->ww : https://twiki.cern.ch/twiki/bin/view/CMS/SWGuideCMSDataAnalysisSchoolCERN2020LongHWW

* AnalyticAnomalousCoupling combine model : https://github.com/GiacomoBoldrini/AnalyticAnomalousCoupling

---

# Setup

```
cmsrel CMSSW_10_6_4
cd CMSSW_10_6_4/src/
cmsenv
```

If you want to generate samples clone the D6EFT repo and follow the instruction provided in the link above.

```
git clone git@github.com:UniMiBAnalyses/D6EFTStudies.git
```

Setup the latino framework (remember to clone/source with the ssh key connected to git)
```
git clone --branch 13TeV git@github.com:latinos/setup.git LatinosSetup
source LatinosSetup/SetupShapeOnly.sh
scramv1 b -j 20

cd LatinoAnalysis/Tools/python
cp userConfig_TEMPLATE.py userConfig.py
# edit the userConfig.py so the paths correspond to a directory where you have write access (this will be used to write log files)
cd ../../../
scram b
```

Finally clone this repo. The implementation of this framework is independent both from the generation step and from the latinos framework so you can place it wherever you want.

```
git clone git@github.com:GiacomoBoldrini/D6tomkDatacard.git
```

---

# Configuration

This framework works if you can provide it with samples. So you need to generate them first. There are a bunch of them 1M event under `/afs/cern.ch/user/g/govoni/myeos/samples/2019_EFT`(restricted access)

The routine is specified in a `.cfg` under the cfg folder. It has many sections.
The `general`section specifies standard naming conventions for the process under study and the output folder/file names in which to store results.
The `ntuples` section specifies the folder with the ntuples. It can be a list of folders, files will be picked smartly using the `glob` module.
In the `eft` section one can specify the operators of interest. If they are more than one the full interference pattern will be saved (planning in the future to save different scenarios for example the single-operator/s one).
For example if two operators are specified you will get a two operator datacard. The section `model` is crucial as it defines how histos will be combined. It follows the nomenclature of AnalyticAnomalousCoupling. 
The model can be chosen from the following `EFT,EFTNeg,EFTNeg-alt`. It can be a list and all the output shapes will be saved in their own folders.
Section `cuts,supercuts` are work in progress and do nothing. The `variables` section specifies the tree names of the variables you want to create shapes for. You are suppposed to give a list of bins (one for each variable) and a list of lists ([xmin:xmax],[],..) with the x-axis ranges in order to build histos.
Sections starting with `d_` creates some dummy files needed for `mkDatacards.py`. You can switch on and off their creation by changin the boolean field `makeDummy` under each section.
They work but they are not fully reliable due to the enormous flexibility of the Latinos framework. Check and modify them if you have to add backgrounds or different stuffs.

---

# makeDummies.py

This is a collection of functions that creates dummy configuration files for mkDatacards.py. Not reliable but a good starting point for more complex use-cases.

---

# makeDCinputs.py

This is the main script. It reads the ntuples, make histograms according to the specified model and save them in a way mkDatacards.py can read them.
It only expects a config file input.



---

# Example

```
cd D6tomkDatacard
python mkDCInputs.py --cfg cfg/SSWW_to_mkDat.cfg 
cp -r SSWW_to_Latinos/ where_mkDatacard_can_see_it/
cd where_mkDatacard_can_see_it/SSWW_to_Latinos/EFTNeg
mkDatacards.py --pycfg=configuration_SSWW_EFTNeg.py --inputFile=rootFile/cW_cHWB.root 
```

Inspect the `datacard` folder. It has a subfolder with you process name and many subfolders with the variables you specified from the ntuples.
Each subfolder has a datacard with the EFT components according to the model you chose and to the AnalyticAnomalousCoupling nomenclature (e.g. lin_, quad_ sm_lin_quad_ etc...).
You will find the shapes in the `shape` folder.



# The End







 
