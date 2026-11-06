"""Read KKMC HepMC3, run IDEA Delphes, and write EDM4hep."""

import os
import re
from pathlib import Path

from Gaudi.Configuration import INFO
from GaudiKernel import SystemOfUnits as units

from Configurables import (
    GaussSmearVertex,
    HepRndm__Engine_CLHEP__RanluxEngine_ as RndmEngine,
    RndmGenSvc,
    EventDataSvc,
    GenAlg,
    HepMCFileReader,
    HepMCToEDMConverter,
    k4SimDelphesAlg,
)

from k4FWCore import ApplicationMgr, IOSvc

MAX_DELPHES_SEED = 2147483647
MAX_GAUDI_SEED = 2147483647
VERTEX_SEED_OFFSET = 1000003


def select_delphes_seed():
    """Return a reproducible detector simulation seed."""

    override = os.environ.get("DELPHES_RANDOM_SEED")

    if override is not None:
        try:
            seed = int(override)
        except ValueError as exc:
            raise RuntimeError(
                "DELPHES_RANDOM_SEED must be an integer"
            ) from exc

        if not 1 <= seed <= MAX_DELPHES_SEED:
            raise RuntimeError(
                "DELPHES_RANDOM_SEED must be between 1 and "
                f"{MAX_DELPHES_SEED}"
            )

        return seed, "DELPHES_RANDOM_SEED"

    job_id_text = os.environ.get("JOBID")

    if job_id_text:
        try:
            job_id = int(job_id_text)
        except ValueError as exc:
            raise RuntimeError(
                f"DIRAC JOBID is not an integer: {job_id_text}"
            ) from exc

        if job_id < 0:
            raise RuntimeError(
                f"DIRAC JOBID must not be negative: {job_id}"
            )

        if job_id > 0:
            seed = ((job_id - 1) % MAX_DELPHES_SEED) + 1
            return seed, "JOBID"

    #Local DIRAC execution normally has no real Grid JOBID.
    return 123, "local fallback"


def select_vertex_seed():
    """Return a reproducible, job-specific Gaudi vertex seed."""

    override = os.environ.get("VERTEX_RANDOM_SEED")

    if override is not None:
        try:
            seed = int(override)
        except ValueError as exc:
            raise RuntimeError(
                "VERTEX_RANDOM_SEED must be an integer"
            ) from exc

        if not 1 <= seed <= MAX_GAUDI_SEED:
            raise RuntimeError(
                "VERTEX_RANDOM_SEED must be between 1 and "
                f"{MAX_GAUDI_SEED}"
            )

        return seed, "VERTEX_RANDOM_SEED"

    job_id_text = os.environ.get("JOBID")

    if job_id_text:
        try:
            job_id = int(job_id_text)
        except ValueError as exc:
            raise RuntimeError(
                f"DIRAC JOBID is not an integer: {job_id_text}"
            ) from exc

        if job_id < 0:
            raise RuntimeError(
                f"DIRAC JOBID must not be negative: {job_id}"
            )

        if job_id > 0:
            seed = (
                (job_id + VERTEX_SEED_OFFSET - 1)
                % MAX_GAUDI_SEED
            ) + 1
            return seed, "JOBID-derived"

    return 456789, "local fallback"


def make_seeded_delphes_card():
    """Create a job local IDEA card containing the selected seed."""

    source_card = Path("card_IDEA.tcl")
    seeded_card = Path("card_IDEA_seeded.tcl")

    if not source_card.is_file():
        raise RuntimeError(
            f"Delphes detector card not found: {source_card}"
        )

    card_content = source_card.read_text(encoding="utf-8")

    seed_pattern = re.compile(
        r"^([ \t]*set[ \t]+RandomSeed[ \t]+)\S+(.*)$",
        re.MULTILINE,
    )

    matches = list(seed_pattern.finditer(card_content))

    if len(matches) != 1:
        raise RuntimeError(
            "Expected exactly one 'set RandomSeed' entry in "
            f"{source_card}, found {len(matches)}"
        )

    seed, seed_source = select_delphes_seed()

    seeded_content = seed_pattern.sub(
        lambda match: (
            match.group(1) + str(seed) + match.group(2)
        ),
        card_content,
        count=1,
    )

    seeded_card.write_text(seeded_content, encoding="utf-8")

    print(
        f"DELPHES_RANDOM_SEED={seed} "
        f"(source: {seed_source})",
        flush=True,
    )
    print(
        f"Delphes seeded card: {seeded_card}",
        flush=True,
    )

    return str(seeded_card)

# Event data service.
# Data service for the current Key4hep interface.
event_service = EventDataSvc("EventDataSvc")

# GaussSmearVertex draws from Gaudi's RndmGenSvc. Use a separate random stream from the Delphes card and vary it between Grid jobs.
vertex_seed, vertex_seed_source = select_vertex_seed()

random_engine = RndmEngine(
    "RndmGenSvc.Engine",
    SetSingleton=True,
    Seeds=[vertex_seed],
)
random_service = RndmGenSvc(
    "RndmGenSvc",
    Engine=random_engine.name(),
)

print(
    f"VERTEX_RANDOM_SEED={vertex_seed} "
    f"(source: {vertex_seed_source})",
    flush=True,
)


# Read the HepMC3 file produced by KKMCee.
# This filename can be overridden from the k4run command line (?)
hepmc_reader = HepMCFileReader(
    "HepMCFileReader",
    Filename="events.hepmc",
)

# FCC-ee Z-pole luminous-region widths. The HepMC time coordinate is ct, therefore 36.3 ps is represented as approximately 10.89 mm.
vertex_smearing = GaussSmearVertex("FCCeeZVertexSmearing")
vertex_smearing.xVertexSigma = 5.96e-3 * units.mm
vertex_smearing.yVertexSigma = 23.8e-6 * units.mm
vertex_smearing.zVertexSigma = 0.397 * units.mm
vertex_smearing.tVertexSigma = 10.89 * units.mm

generator = GenAlg(
    "GenAlg",
    SignalProvider=hepmc_reader,
)

generator.VertexSmearingTool = vertex_smearing
generator.hepmc.Path = "hepmc"


# Convert the in-memory HepMC3 event into EDM4hep MCParticles.
converter = HepMCToEDMConverter("HepMCToEDMConverter")

converter.hepmc.Path = "hepmc"
converter.GenParticles.Path = "GenParticles"


# Run Delphes using the EDM4hep generator-particle collection.
delphes = k4SimDelphesAlg("k4SimDelphesAlg")

delphes.DelphesCard = make_seeded_delphes_card()
delphes.DelphesOutputSettings = "edm4hep_IDEA.tcl"
delphes.GenParticles.Path = "GenParticles"


# Write the Delphes output collections directly to EDM4hep
output = IOSvc()

output.Output = "photon_upgrade.edm4hep.root"
output.outputCommands = ["keep *"]


ApplicationMgr(
    TopAlg=[
        generator,
        converter,
        delphes,
    ],
    EvtSel="NONE",
    EvtMax=-1,
    ExtSvc=[
        event_service,
        random_engine,
        random_service,
    ],
    OutputLevel=INFO,
)
