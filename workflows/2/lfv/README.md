# KKMC LFV tau-to-mu-gamma samples

This directory contains the KKMC inputs, IDEA cards and Gaudi steering used
for the preliminary FCC-ee LFV samples at 91.2 GeV. Generation is followed by
k4SimDelphes in Gaudi, as in workflow 2.

The Grid tests produced 10,000 events for each signal charge. The results,
software versions and EOS locations are listed in [VALIDATION.md](VALIDATION.md).
Simulation used a nightly build, so these samples are preliminary.

## Configuration

| Setting | Tau-minus sample | Tau-plus sample |
| --- | --- | --- |
| Signal decay | tau- -> mu- gamma | tau+ -> mu+ gamma |
| Signal tau PDG code | 15 | -15 |
| KKMC parameters 2001 / 2002 | 162 / 0 | 0 / 162 |
| Opposite tau decay | Inclusive | Inclusive |
| PHOTOS, parameter 35 | Off | Off |
| Beam-energy spread, parameter 25 | Off | Off |

The inclusive decay applies to the opposite tau in each signal event. An
inclusive Standard Model tau-pair background sample still needs to be produced
separately. Turning off PHOTOS does not turn off all production radiation.

The IDEA card comes from Delphes 3.5.2pre02. The simulation uses the photon
direction and pointing information added in
[k4SimDelphes #161](https://github.com/key4hep/k4SimDelphes/pull/161).
The steering uses `EventDataSvc` and `IOSvc` for EDM4hep output.

Gaudi smears the collision vertex before HepMC conversion and Delphes. The
spatial widths are 0.00596 mm in x, 0.0000238 mm in y and 0.397 mm in z.
These settings are for the Z pole. A time component is also configured, but
the stored signal MC times were zero; time propagation has not been validated.

## Running a local test

The example below generates 1000 tau-minus events. It requires CERN CVMFS.
Use a fresh terminal for generation and another for simulation, since they
use different software environments.

Starting from the FCCDIRAC checkout, copy the configuration to a run directory:

```bash
cd workflows/2/lfv
mkdir run_tauminus
cp config/* run_tauminus/
cd run_tauminus
```

Set up the generator release and run KKMC:

```bash
source /cvmfs/sw.hsf.org/key4hep/releases/2026-04-08/x86_64-almalinux9-gcc14.2.0-opt/key4hep-stack/2026-04-08-i6h4f2/setup.sh

KKMCee --config kkmc_tauminus_mugamma_taginclusive_nophotos.input \
  --nevts 1000 --outfile events.hepmc --initialseed 98765433
```

After generation completes successfully, open a fresh terminal and return to
the FCCDIRAC checkout. Then run the simulation:

```bash
cd workflows/2/lfv/run_tauminus
source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh

export VERTEX_RANDOM_SEED=1357911
export DELPHES_RANDOM_SEED=24681357

k4run hepmc3_delphes_IDEA.py \
  --GenAlg.HepMCFileReader.Filename events.hepmc \
  --IOSvc.Output sample.edm4hep.root -n 1000
```

The default nightly changes over time. Check the results again when using a
different build. A stable simulation release still needs to be selected and
tested for the final production.

For tau-plus, use the other `.input` file, a separate run directory and different
seeds. Set `--signal-tau-pdg -15` in the validation commands below. The fixed
seeds here are examples; the Grid jobs used their DIRAC job IDs to derive seeds.

## Checking the output

After a successful simulation, run the strict validator from the same directory
and in the same simulation environment:

```bash
python3 ../validation/validate_lfv_photon_upgrade.py sample.edm4hep.root \
  --signal-tau-pdg 15 --expected-events 1000
```

A few very low-energy clusters in the Grid samples had zero position and NaN
position covariance. The separate preliminary validator can record this known
case and exclude those clusters from its diagnostics:

```bash
python3 ../validation/validate_lfv_preliminary.py sample.edm4hep.root \
  --signal-tau-pdg 15 --expected-events 1000 \
  --allow-known-zero-position-covariance --json-report validation.json
```

This option applies only to the specific case described in
[VALIDATION.md](VALIDATION.md). It does not fix the clusters or change the ROOT
file. Other invalid values still fail validation.

The checks cover event counts, LFV truth, spatial vertex smearing and photon
fields. Photon diagnostics use a unique geometric match within 10 mrad, with
no energy selection. The distributions are unweighted and depend on that
selection; they still need physics review.

## Grid tests

The tests used direct KKMC and Gaudi execution in DIRAC jobs, with the five
configuration files delivered through an LFN configuration tarball. Central
production transformations have not been tested with this setup.

The configuration files and both validators are listed in `SHA256SUMS` and
match the versions used for the samples. The batch submission and publication
scripts are not included here.

Beam-energy spread was disabled in all 20 jobs, confirmed from both saved
inputs and KKMC runtime messages. The Gaussian BES issue in
[KKMCee #5](https://github.com/KrakowHEPSoft/KKMCee/pull/5) was therefore not
exercised by this batch. This is separate from collision-vertex smearing and
the cluster covariance issue. Enabling BES will require a corrected generator
build and a new validation.
