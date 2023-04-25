#!/bin/env python
"""script to do X"""
from DIRAC.Core.Base.Script import parseCommandLine
parseCommandLine()

from ILCDIRAC.Interfaces.API.NewInterface.Applications import DelphesApp
from ILCDIRAC.Interfaces.API.NewInterface.UserJob import UserJob
from ILCDIRAC.Interfaces.API.DiracILC import DiracILC


def run():
  """Run The Job."""
  job = UserJob()
  job.setConfigPackage("fccConfig", 'key4hep-devel-2')

  delphes = DelphesApp()
  delphes.setVersion('key4hep-latest')
  delphes.setExecutable("DelphesPythia8_EDM4HEP")
  delphes.setDetectorCard('delphes_card_IDEA.tcl')
  delphes.setOutputCard('edm4hep_output_config.tcl')
  delphes.setPythia8CardFile('p8_ee_ggqq_ecm91.cmd')
  delphes.setRandomSeed(12340)
  delphes.setEnergy(91.2)
  delphes.setNumberOfEvents(100)
  delphes.setOutputFile('output.root')

  job.append(delphes)
  job.submit(DiracILC(), mode='local')

  

if __name__ =="__main__":
  run()
