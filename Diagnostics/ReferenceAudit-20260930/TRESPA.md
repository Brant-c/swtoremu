# trespa/SwTor-1.3 reference audit

Repository: https://github.com/trespa/SwTor-1.3
Reviewed master commit: 877fc9b268c30b575a85e1a68e62f54ebe331383
Commit date: 2012-09-10; message: added the server.
Separate reference checkout: D:/SWTORClassic/References/trespa-SwTor-1.3.
Read only; not built or executed.

## Result

All 86 tracked server files have identical SHA256 hashes to the corresponding
files in D:/SWTORClassic/swtoremu/Server. No additional implementation is present
in those files. Full per-file comparison: trespa-file-comparison.csv.

Reviewed Session::Setup registrations, character selection handlers/senders,
service request/acknowledgement, Game::World, and project dependencies. Searched
the entire server tree for phase, instance, room, collision, transfer, movement
opcode61116AD5, SendToArea, and area/player loading references.

SendCharacterRegionSpecs emits SMSG_SEND_TO_AREA with an AreaServer address
string, called by HandleCharacterSelect after selection/current-map/travel
status. It is an initial character-selection path, not an implementation of
same-area phase exit. Service requests similarly advertise an area service;
they do not implement doorway collision or phase lifecycle.

The published server tree contains ProxyServer, TimeServer, WorldServer,
Script, and PluginNet. It omits the Framework directory referenced by includes
and build files, and contains no separate AreaServer implementation. Bullet
dependencies/includes alone do not establish working character physics:
Game::World.cpp contains only an empty constructor. Numerous message handlers
remain unknown-named or logging stubs.

This repository does not supply a missing phase-exit solution for the current
problem. Its name does not establish compatibility with April1.2.0. No protocol
behavior was imported or promoted from this reference.
