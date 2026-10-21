! 1) Random number generator and number of events
Random:setSeed = on
Main:numberOfEvents = 20000        ! number of events to generate
Main:timesAllowErrors = 5          ! how many aborts before run stops


! 2) Settings related to output in init(), next() and stat().
Init:showChangedSettings = on      ! list changed settings
Init:showChangedParticleData = off ! list changed particle data
Next:numberCount = 100             ! print message every n events
Next:numberShowInfo = 1            ! print event information n times
Next:numberShowProcess = 1         ! print process record n times
Next:numberShowEvent = 0           ! print event record n times

Beams:idA = 11                     ! first beam, e+ = 11
Beams:idB = -11                    ! second beam, e- = -11

Beams:allowMomentumSpread = off

! Vertex smearing (FSR 2025 parameters, arXiv:2505.00274 Table 2):
Beams:allowVertexSpread = on
Beams:sigmaVertexX = 26.17e-3
Beams:sigmaVertexY = 31.1E-6
Beams:sigmaVertexZ = 1.198
Beams:sigmaTime = 1.65             !  5.50 ps


! 3) Hard process : tt at 365 GeV
Beams:eCM = 365                    ! CM energy of collision
Top:ffbar2ttbar(s:gmZ) = on

! 4) Settings for the event generation process in the Pythia8 library.
PartonLevel:ISR = on               ! no initial-state radiation
PartonLevel:FSR = on               ! no final-state radiation
