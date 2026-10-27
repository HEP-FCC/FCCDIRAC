# LFV sample checks

This note records the September 30 Grid batch and the merging and publication
completed on October 1, 2026.

## Samples

| Sample | DIRAC job IDs | Events after merging | Known invalid clusters |
| --- | --- | ---: | ---: |
| Tau-minus LFV | 66942308-66942317 | 10,000 | 8 |
| Tau-plus LFV | 66942318-66942327 | 10,000 | 17 |

Each sample contains ten jobs of 1000 events, run at `LCG.CERN.ch`. The opposite
tau decays inclusively. PHOTOS and beam-energy spread are disabled.

The files for each charge were merged separately with
`podio-merge-files --metadata all`. The preliminary validator then checked
10,000 events in each merged file. The original job files were kept.

## Software used

- Generation: `kkmc.key4hep_260408`, KKMCee `5.01.rc`, from the fixed Key4hep
  2026-04-08 release on AlmaLinux 9 with GCC 14.2.0.
- Simulation: `gaudiapp.key4hep_nightly`, using
  `/cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh`. In the recorded runs this
  selected `devkey-head/Wed/x86_64-el9-gcc16-opt`.
- Delphes: `3.5.2pre02`. k4SimDelphes and k4FWCore were labelled `HEAD` in the
  installed nightly; these labels do not identify fixed commits.
- Merging: podio from `devkey-head/Thu/x86_64-el9-gcc16-opt` on October 1.

The five configuration files were delivered using:

```text
/fcc/prod/software/fccconfig/fccconfigkey4hep-lfv-sandbox-test-1.tgz
```

This test tarball has the files at its top level. The Grid jobs ran KKMC and
Gaudi directly and used job-derived random seeds. They did not run through
central production transformations.

## Results and known issues

The preliminary checks passed for event counts, charge-specific LFV truth,
spatial vertex smearing and photon fields, with the covariance exception below.
The saved inputs and KKMC runtime messages also confirmed `KeyBES=0` in all
20 jobs. The Gaussian BES issue reported in
[KKMCee #5](https://github.com/KrakowHEPSoft/KKMCee/pull/5) was not exercised.
This check does not validate generation with BES enabled.

There were 8 known invalid clusters in the tau-minus sample and 17 in the
tau-plus sample. These are cluster counts, not necessarily distinct events.
The preliminary validator accepts only this specific case: positive energy
below 10 MeV, positive finite energy error, zero position, zero pointing angles
and direction covariance, and all six position-covariance entries NaN. Other
non-finite values still fail the checks.

These clusters are listed in the validation reports and excluded from the
diagnostic summaries. They remain in the ROOT files, and no events were removed.
The underlying defect and its effect on an analysis still need to be reviewed.

Photon associations are geometric, and the diagnostic distributions are
unweighted. Photon response and sample normalisation need physics review.
The stored signal MC times were zero, so only spatial vertex smearing has been
validated. The final production also needs validation with a stable simulation
release. Inclusive Standard Model tau-pair backgrounds are separate work.

## Files on EOS

Storage element: `CERN-DST-EOS`. Uploads and replica queries completed successfully.

DIRAC LFN directory:

```text
/fcc/prod/lfv/preliminary/20260930_10k_v1/merged/
```

Physical EOS directory returned by DIRAC:

```text
/eos/experiment/fcc/prod/fcc/prod/lfv/preliminary/20260930_10k_v1/merged/
```

The two sample files are:

```text
lfv_tauminus_10000evt_preliminary.edm4hep.root
lfv_tauplus_10000evt_preliminary.edm4hep.root
```

The same directory contains `input_records.json`, `merge_summary.json`, and
the per-charge `_validation.json` and `_validation.log` files.

The configuration and software discussion is in
[ILCDIRAC-1068](https://its.cern.ch/jira/browse/ILCDIRAC-1068).
