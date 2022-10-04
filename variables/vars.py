ROOT.gInterpreter.Declare('''
std::vector<ROOT::Math::PxPyPzEVector> jets(double pxj1, double pxj2, double pxj3, double pxj4, double pyj1, double pyj2, double pyj3, double pyj4, double pzj1, double pzj2, double pzj3, double pzj4, double Ej1, double Ej2, double Ej3, double Ej4) {
    ROOT::Math::PxPyPzEVector p1(pxj1, pyj1, pzj1, Ej1);
    ROOT::Math::PxPyPzEVector p2(pxj2, pyj2, pzj2, Ej2);
    ROOT::Math::PxPyPzEVector p3(pxj3, pyj3, pzj3, Ej3);
    ROOT::Math::PxPyPzEVector p4(pxj4, pyj4, pzj4, Ej4);
    
    std::vector<ROOT::Math::PxPyPzEVector> pjs = {p1, p2, p3, p4};

    return pjs;
}
''')

ROOT.gInterpreter.Declare('''
std::pair<int,int> mjj_index(std::vector<ROOT::Math::PxPyPzEVector> pjs) {

    std::pair<int, int> max_mjj{0,1};

    double max = 0;

    for (int j=1; j < pjs.size(); ++j){
        for (int i=0; i < j; ++i){
            double tmp_max = (pjs[j] + pjs[i]).M();
            if (tmp_max  > max){
                max = tmp_max;
                max_mjj.first = j;
                max_mjj.second = i;
            }      
        }
    }

    
    return max_mjj;
}
''')

# ROOT.gInterpreter.Declare('''
# double mjj(std::vector<ROOT::Math::PxPyPzEVector> pjs, std::pair<int, int> mjj_idx) {

#     return (pjs.at(mjj_idx.first) + pjs.at(mjj_idx.second)).M();
# }
# ''')

ROOT.gInterpreter.Declare('''
double mV(std::vector<ROOT::Math::PxPyPzEVector> pjs, std::pair<int, int> mjj_idx) {

    ROOT::Math::PxPyPzEVector pV(0, 0, 0, 0);
    for (int i =0; i < pjs.size(); ++i){
        if (i != mjj_idx.first && i != mjj_idx.second){
            pV += pjs.at(i);
        }
    }
    return pV.M();
}
''')

ROOT.gInterpreter.Declare('''
double detajj(std::vector<ROOT::Math::PxPyPzEVector> pjs, std::pair<int, int> mjj_idx) {

    return std::abs(pjs.at(mjj_idx.first).Eta() - pjs.at(mjj_idx.second).Eta());
}
''')

ROOT.gInterpreter.Declare('''
double dphijj(std::vector<ROOT::Math::PxPyPzEVector> pjs, std::pair<int, int> mjj_idx) {

    return std::abs(pjs.at(mjj_idx.first).Phi() - pjs.at(mjj_idx.second).Phi());
}
''')

ROOT.gInterpreter.Declare('''
bool isThereATop(std::vector<ROOT::Math::PxPyPzEVector> pjs, std::pair<int, int> mjj_idx) {

    ROOT::Math::PxPyPzEVector pV(0, 0, 0, 0);
    for (int i =0; i < pjs.size(); ++i){
        if (i != mjj_idx.first && i != mjj_idx.second){
            pV += pjs.at(i);
        }
    }
    

    if ( std::abs( (pV + pjs.at(mjj_idx.first)).M() - 172. ) < 15 || std::abs( (pV + pjs.at(mjj_idx.second)).M() - 172. ) < 15 ) {
        return 1;
    }
    else {
        return 0;
    }
    
}
''')


ROOT.gInterpreter.Declare('''
double mtop(std::vector<ROOT::Math::PxPyPzEVector> pjs, std::pair<int, int> mjj_idx) {

    ROOT::Math::PxPyPzEVector pV(0, 0, 0, 0);
    for (int i =0; i < pjs.size(); ++i){
        if (i != mjj_idx.first && i != mjj_idx.second){
            pV += pjs.at(i);
        }
    }
    

    if ( std::abs( (pV + pjs.at(mjj_idx.first)).M() - 172. ) < std::abs( (pV + pjs.at(mjj_idx.second)).M() - 172. )  ) {
        return (pV + pjs.at(mjj_idx.first)).M();
        std::cout << (pV + pjs.at(mjj_idx.first)).M() << std::endl;
    }
    else {
        return (pV + pjs.at(mjj_idx.second)).M();
    }
}
''')



cppvars.append(["pjs", "jets(pxj1, pxj2, pxj3, pxj4, pyj1, pyj2, pyj3, pyj4, pzj1, pzj2, pzj3, pzj4, Ej1, Ej2, Ej3, Ej4)"])
cppvars.append(["mjj_index", "mjj_index(pjs)"])
#cppvars.append(["mjj", "mjj(pjs, mjj_index)"])
cppvars.append(["detajj", "detajj(pjs, mjj_index)"])
cppvars.append(["dphijj", "dphijj(pjs, mjj_index)"])
cppvars.append(["mV", "mV(pjs, mjj_index)"])
cppvars.append(["mtop", "mtop(pjs, mjj_index)"])
cppvars.append(["isThereATop", "isThereATop(pjs, mjj_index)"])
