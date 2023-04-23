#!/bin/env python
"""script to do X"""
from DIRAC.Core.Base.Script import parseCommandLine
parseCommandLine()

from ILCDIRAC.Interfaces.API.NewInterface.Applications import GaudiApp
from ILCDIRAC.Interfaces.API.NewInterface.UserJob import UserJob
from ILCDIRAC.Interfaces.API.DiracILC import DiracILC

def run():
  """Run The Job."""
  job = UserJob()
  job.setConfigPackage("fccConfig", 'key4hep-devel-2')

  ga = GaudiApp()
  ga.setVersion('key4hep-latest')
  ga.setExecutable("k4run")
  ga.setSteeringFile('geant_fullsim_fccee_lar_pgun.py')
  ga.setRandomSeedFlag('--SimG4Svc.seedValue')
  ga.setRandomSeed(100)
  ga.setEnergy(10)
  ga.setNumberOfEvents(25)
  ga.setOutputFile('output.root')
  
  job.append(ga)
  job.submit(DiracILC(), mode='local')


if __name__ =="__main__":
  run()
