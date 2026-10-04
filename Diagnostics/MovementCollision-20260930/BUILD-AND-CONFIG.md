# Experiment15 preparation
Release Win32 build succeeded with MSBuild18.10.1. Passive hooks only; no server packet change.
DLL SHA256: 1D9E7A3AFCA3BF8CCF8C270852AE91A2C1F577A4E2C3EDDE2C81FB19E5C12FB7
Launch.ps1 -VerifyOnly passed: movement diagnostic=1, phase clear=1, phase update=1, CRT3=0, log-only=1, retry disabled. No processes launched.
Old selected-phase manifest compared before repinning: only authorized ToR.cpp and DLL differ. New identity.csv pins all baseline inputs plus diagnostic sources and launcher. Prior manifest preserved.
The diagnostic logs at most48 movement attempts,48 support checks,4 contacts per attempt, sampled every250ms. Standing still does not consume samples. Supporting-floor checks require the same active character and a movement sample in the preceding500ms.
Sweep output is the native query output, not proof of final character position or successful passage. Collision true is a hit outcome. Support outputValid=0 leaves output values uninterpreted.
Runtime installation, normal walking coverage and contact identity remain pending. Unsupported native prefixes disable this diagnostic. No collision flags or object state are changed.
Manual launcher: D:/SWTORClassic/swtoremu/Run-SWTORClassic-MovementCollision.cmd
Load Tython; approach door; walk against barrier for3 seconds; step back; close client. Review logs after run. Missing prepared/coverage markers means inconclusive, not evidence of no collision.
