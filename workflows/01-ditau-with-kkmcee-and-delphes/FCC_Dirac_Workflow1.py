'''
Example workflow 1 from the FCC Tutorial:
https://hep-fcc.github.io/fcc-tutorials/main/distributed-computing/workflows/01/DiTauKKMCeeDelphesStandAlone.html
'''

# standard library imports
import os
from shutil import copy2
# DIRAC imports
from DIRAC import gLogger, S_OK
from DIRAC.Core.Base import Script
# iLCDirac imports
from ILCDIRAC.Interfaces.API.DiracILC import DiracILC
from ILCDIRAC.Interfaces.API.NewInterface.UserJob import UserJob
from ILCDIRAC.Interfaces.API.NewInterface import Applications


def copywithreplace(filein: str, fileout: str,
                    repls: list[tuple[str, str]] = []):
    '''
    Copy the contents of the file with possible string replacements.
    '''
    # If no replacements, just copy the file
    if repls is None:
        copy2(filein, fileout)
        return

    # Load the contents of the input file
    with open(filein, 'rt', encoding='utf-8') as infile:
        # open the output file to write the result to
        lines = infile.readlines()
    with open(fileout, 'wt', encoding='utf-8') as outfile:
        # for each line in the input file
        for line in lines:
            # Apply each requested replacement
            lout = line
            for rpl in repls:
                lout = lout.replace(str(rpl[0]), str(rpl[1]))
            outfile.write(lout)


# Define a simple class to hold the script parameters
class Params:
    def __init__(self):
        self.where = 'local'
    def run_on_wms(self, _):
        self.where = 'wms'
        return S_OK()
    def run_locally(self, _):
        self.where = 'local'
        return S_OK()


def main():
    # Setup argument parsing
    cli_params = Params()

    Script.registerSwitch('w', 'wms', 'Run on DIRAC WMS',
                          cli_params.run_on_wms)
    Script.registerSwitch('l', 'local', 'Run locally',
                          cli_params.run_locally)

    Script.parseCommandLine()

    gLogger.notice('Submitting Example Workflow 1')
    gLogger.notice(' - execution location: ', cli_params.where)

    # Creating an instance of an user job

    job = UserJob()

    job.setOutputSandbox(['*.log', '*.sh', '*.py', '*.xml'])
    outputdatafile = 'kktautau_delphes_edm4hep_output.root'
    job.setOutputData(outputdatafile, '', 'CERN-DST-EOS')

    job.setJobGroup('KKMC_EDM4HEP_Run')
    job.setName('KKMC_EDM4HEP')
    job.setLogLevel('DEBUG')

    # KKMCee generation

    kkmc_app = Applications.KKMC()
    kkmc_app.setVersion('key4hep_250128')
    kkmc_app.setEvtType('Tau')
    kkmc_app.setEnergy(91.2)
    nevts = 10000
    outputfile = f'kktautau_delphes_{nevts}.lhe'
    kkmc_app.setNumberOfEvents(nevts)
    kkmc_app.setOutputFile(outputfile)

    # Register KKMC application to the Job instance
    job.append(kkmc_app)

    # Delphes simulation

    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Delphes IDEA card
    # copy of $DELPHES/cards/delphes_card_IDEA.tcl
    idea_card = 'delphes_card_IDEA.tcl'
    copy2(os.path.join(script_dir, idea_card), idea_card)
    # Delphes EDM4hep output card
    # copy of $K4SIMDELPHES/edm4hep_output_config.tcl
    edm4hep_output_def = 'edm4hep_output_config.tcl'
    copy2(os.path.join(script_dir, edm4hep_output_def), edm4hep_output_def)
    # Pythia card
    # copy of $K4GEN/Pythia_LHEinput.cmd
    pythia_card = 'Pythia_LHEinput.cmd'
    replacements = [
        ('Main:numberOfEvents = 100',
         f'Main:numberOfEvents = {nevts}'),
        ('Beams:LHEF = Generation/data/events.lhe',
         f'Beams:LHEF = {outputfile}')
    ]
    copywithreplace(os.path.join(script_dir, pythia_card), pythia_card,
                    replacements)

    # Set the sandbox content
    job.setInputSandbox(
        ['./' + idea_card, './' + edm4hep_output_def, './' + pythia_card]
    )

    ga = Applications.GenericApplication()
    ga.setSetupScript(
        '/cvmfs/sw.hsf.org/key4hep/releases/2025-01-28/'
        'x86_64-almalinux9-gcc14.2.0-opt/key4hep-stack/'
        '2025-01-28-q6hyek/setup.sh'
    )
    ga.setScript(
        '/cvmfs/sw.hsf.org/key4hep/releases/2025-01-28/'
        'x86_64-almalinux9-gcc14.2.0-opt/k4simdelphes/00-07-04-naw5vm/'
        'bin/DelphesPythia8_EDM4HEP'
    )
    ga.setArguments(
        f'{idea_card} {edm4hep_output_def} {pythia_card} {outputdatafile}'
    )

    job.append(ga)

    dilc = DiracILC()
    print(job.submit(dilc, mode=cli_params.where))


if __name__ == '__main__':
    main()
