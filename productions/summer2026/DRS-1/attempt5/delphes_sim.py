from Gaudi.Configuration import *
from GaudiKernel import SystemOfUnits as units

from Configurables import EventDataSvc
from k4FWCore import ApplicationMgr, IOSvc
app = ApplicationMgr()
app.EvtMax = 100
app.EvtSel = "NONE"
app.ExtSvc += ["RndmGenSvc", EventDataSvc("EventDataSvc")]

from Configurables import HepMCFileReader
hepmc_reader = HepMCFileReader()
hepmc_reader.Filename = "events_gen.hepmc"

# FCC-ee IDEA beamspot smearing, applied here rather than in the Gen stage,
# via the Gaudi VertexSmearingTool.
from Configurables import GaussSmearVertex
smeartool = GaussSmearVertex()
smeartool.xVertexSigma = 5.96e-3 * units.mm
smeartool.yVertexSigma = 23.8e-6 * units.mm
smeartool.zVertexSigma = 0.397 * units.mm
smeartool.tVertexSigma = 10.89 * units.mm

from Configurables import GenAlg
gun = GenAlg()
gun.SignalProvider = hepmc_reader
gun.VertexSmearingTool = smeartool
gun.hepmc.Path = "hepmc"
ApplicationMgr().TopAlg += [gun]

from Configurables import HepMCToEDMConverter
hepmc_converter = HepMCToEDMConverter()
hepmc_converter.hepmc.Path = "hepmc"
hepmc_converter.GenParticles.Path = "GenParticles"
ApplicationMgr().TopAlg += [hepmc_converter]

iosvc = IOSvc()
iosvc.Output = "output.root"
iosvc.outputCommands = ["keep *"]
iosvc.OutputType = "rntuple"

from Configurables import k4SimDelphesAlg
delphesalg = k4SimDelphesAlg()
delphesalg.DelphesCard = "card_IDEA.tcl"
delphesalg.DelphesOutputSettings = "edm4hep_IDEA.tcl"
delphesalg.GenParticles.Path = "GenParticles"
delphesalg.OutputLevel = VERBOSE
ApplicationMgr().TopAlg += [delphesalg]
