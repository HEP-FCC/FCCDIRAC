#!/bin/env python

'''
Generates Delphes+Pythia8 ee->ggqq @ 91.188 GeV sample.
'''
import os
import shutil

from DIRAC import gLogger, S_OK
from DIRAC.Core.Base.Script import Script

from ILCDIRAC.Interfaces.API.NewInterface.Applications import DelphesApp
from ILCDIRAC.Interfaces.API.NewInterface.UserJob import UserJob
from ILCDIRAC.Interfaces.API.DiracILC import DiracILC

# Class to hold the script parameters
class Params:
    def __init__(self):
        self.where = 'local'

    def run_on_wms(self, _):
        self.where = 'wms'
        return S_OK()

    def run_locally(self, _):
        self.where = 'local'
        return S_OK()


def submit(cli_params):
    '''
    The definition of the DIRAC job itself.
    '''

    p8_card = 'p8_ee_ggqq_ecm91.cmd'
    shutil.copy2(f'../{p8_card}', os.getcwd())
    output_data_file = 'output.root'

    job = UserJob()
    job.setConfigPackage('fccConfig', 'key4hep-devel-6')
    job.setOutputData(output_data_file, '', 'CNAF-DISK')

    delphes = DelphesApp()
    delphes.setVersion('key4hep-latest')
    delphes.setExecutableName('DelphesPythia8_EDM4HEP')
    delphes.setDetectorCard('card_IDEA.tcl')
    delphes.setOutputCard('edm4hep_IDEA.tcl')
    delphes.setPythia8Card(p8_card)
    delphes.setRandomSeed(36)
    delphes.setEnergy(91.188)
    delphes.setNumberOfEvents(100)
    delphes.setOutputFile(output_data_file)

    job.append(delphes)
    job.submit(DiracILC(), mode=cli_params.where)


if __name__ == "__main__":
    # Setup argument parsing
    cli_params = Params()

    Script.registerSwitch('w', 'wms', 'Run on DIRAC WMS',
                          cli_params.run_on_wms)
    Script.registerSwitch('l', 'local', 'Run locally',
                          cli_params.run_locally)

    Script.parseCommandLine()

    gLogger.notice('Submitting Workflow 3')
    gLogger.notice(' - execution location: ', cli_params.where)

    submit(cli_params)
