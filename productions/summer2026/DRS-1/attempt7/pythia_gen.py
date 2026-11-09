# SANDBOX-DELIVERED (attempt7): loaded from the job InputSandbox, not the fccConfig tarball
from Gaudi.Configuration import *

from Configurables import EventDataSvc
from k4FWCore import ApplicationMgr
app = ApplicationMgr()
app.EvtMax = 100
app.EvtSel = "NONE"
app.ExtSvc += [EventDataSvc("EventDataSvc")]

from Configurables import PythiaInterface
pythia8gentool = PythiaInterface()
pythia8gentool.pythiacard = "pythia8card.cmd"
pythia8gentool.doEvtGenDecays = False
pythia8gentool.printPythiaStatistics = True

from Configurables import GenAlg
gun = GenAlg()
gun.SignalProvider = pythia8gentool
gun.hepmc.Path = "hepmc"
ApplicationMgr().TopAlg += [gun]

# Vertex smearing happens in the Sim stage instead (GenAlg + HepMCFileReader +
# GaussSmearVertex in delphes_sim.py), so this stage writes an unsmeared HepMC3
# file for the Sim stage to read back.
from Configurables import HepMCFileWriter
hepmc_writer = HepMCFileWriter()
hepmc_writer.hepmc.Path = "hepmc"
hepmc_writer.Filename = "events_gen.hepmc"
ApplicationMgr().TopAlg += [hepmc_writer]
