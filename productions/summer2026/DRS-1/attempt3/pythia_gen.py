from Gaudi.Configuration import *
from GaudiKernel import SystemOfUnits as units

from Configurables import EventDataSvc
from k4FWCore import ApplicationMgr, IOSvc
app = ApplicationMgr()
app.EvtMax = 100
app.EvtSel = "NONE"
app.ExtSvc += ["RndmGenSvc", EventDataSvc("EventDataSvc")]

from Configurables import PythiaInterface
pythia8gentool = PythiaInterface()
pythia8gentool.pythiacard = "pythia8card.cmd"
pythia8gentool.doEvtGenDecays = False
pythia8gentool.printPythiaStatistics = True

# FCC-ee IDEA beamspot smearing, applied via the Gaudi VertexSmearingTool
# rather than the pythia card's own Beams:allowVertexSpread.
from Configurables import GaussSmearVertex
smeartool = GaussSmearVertex()
smeartool.xVertexSigma = 5.96e-3 * units.mm
smeartool.yVertexSigma = 23.8e-6 * units.mm
smeartool.zVertexSigma = 0.397 * units.mm
smeartool.tVertexSigma = 10.89 * units.mm

from Configurables import GenAlg
gun = GenAlg()
gun.SignalProvider = pythia8gentool
gun.VertexSmearingTool = smeartool
gun.hepmc.Path = "hepmc"
ApplicationMgr().TopAlg += [gun]

from Configurables import HepMCToEDMConverter
hepmc_converter = HepMCToEDMConverter()
hepmc_converter.hepmc.Path = "hepmc"
hepmc_converter.GenParticles.Path = "GenParticles"
ApplicationMgr().TopAlg += [hepmc_converter]

iosvc = IOSvc()
iosvc.Output = "events_gen.edm4hep.root"
iosvc.outputCommands = ["keep *"]
iosvc.OutputType = "rntuple"
