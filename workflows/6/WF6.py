#!/bin/env python
"""script to do X"""
from DIRAC.Core.Base.Script import parseCommandLine
parseCommandLine()

from ILCDIRAC.Interfaces.API.NewInterface.Applications import DelphesApp, Babayaga
from ILCDIRAC.Interfaces.API.NewInterface.UserJob import UserJob
from ILCDIRAC.Interfaces.API.DiracILC import DiracILC


def run():
  """Run The Job."""
  energy = 91.2
  job = UserJob()
  job.setConfigPackage("fccConfig", 'key4hep-devel')

  babayaga = Babayaga()
  babayaga.setVersion('key4hep-latest')
  babayaga.setNumberOfEvents(1000)
  babayaga.setEnergy(energy)
  babayaga.setRandomSeed(-1)
  babayaga.setOutputFile('events.lhe')
  job.append(babayaga)
  
  delphes = DelphesApp()
  delphes.setVersion('key4hep-latest')
  delphes.setExecutableName("DelphesPythia8_EDM4HEP")
  delphes.setDetectorCard('card_IDEA.tcl')
  delphes.setOutputCard('edm4hep_IDEA.tcl')
  delphes.setPythia8Card('Pythia_LHEinput.cmd')
  delphes.setEnergy(91.2)
  delphes.setOutputFile('output.root')
  job.append(delphes)

  job.submit(DiracILC(), mode='local')
  

if __name__ =="__main__":
  run()