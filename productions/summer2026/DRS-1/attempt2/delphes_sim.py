from Gaudi.Configuration import *

from Configurables import EventDataSvc
from k4FWCore import ApplicationMgr, IOSvc
app = ApplicationMgr()
app.EvtMax = 100
app.EvtSel = "NONE"
app.ExtSvc += [EventDataSvc("EventDataSvc")]

iosvc = IOSvc()
iosvc.Input = ["events_gen.edm4hep.root"]
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
