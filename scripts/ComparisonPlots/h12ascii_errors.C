#include <iostream>
#include <fstream>
using namespace std;

void h12ascii_errors(TString filename, TString odir) {
    TObject *obj;
    TFile *f1 = new TFile(filename, "R");
    TIter it(f1->GetListOfKeys());
    //TH1F *h1;
    while (obj=it.Next()) {
    	TH1F *h1 = (TH1F*) obj->Clone();
    	//h1->Print("ALL");
		TString name = h1->GetName();
		TString fname = odir+"/"+name+".txt";

		TH1F *h = (TH1F*) f1->Get(name);

		ofstream outputfile;
		outputfile.open(fname);

		Int_t n = h->GetNbinsX();

<<<<<<< HEAD
		// starting at 2 as fist entry is sumation of all entries?
=======
>>>>>>> 507fdcf53c4464f4822d763ecffe7109305ed0d6
		for (Int_t i=1; i<=n; i++) {
			outputfile << h->GetBinLowEdge(i) << " " << h->GetBinContent(i) << " " << h->GetBinWidth(i) << " " << h->GetBinError(i) << "\n";
		}
		outputfile.close();
    } 
} 