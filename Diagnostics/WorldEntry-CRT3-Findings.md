# 2026-09-17 18:11 run — CRT3 disabled + trace instrumentation: NO CRASH, client now waits on unanswered client requests

Configuration: CRT3 renamed `.disabled`, `SWTOR_CRT_MISSING_MODE=skip`, `SWTOR_TRACE_AREA_PAYLOADS=1`,
instrumented server (17:51) + instrumented launcher with AV capture (17:59), fresh server start 18:11.

Result: **the `SerializationException` and both access violations are gone.** No dump written.
Client progressed far past every previous crash point (character-spec specs bmn/bms/astromech all resolved).

Transcript ends in a repeating idle loop: `Resource worker RVA=00745CF0 thread=... state=5 queued=0`.
Not a deadlock — the client process stays alive at high CPU.

## Definitive answer on the 4 previously-unknown opcodes

The new handler decodes prove they are **client→server requests, not noise**:

| Opcode | Body (after 8-byte transport hdr) | Behavior this run |
|---|---|---|
| `C586BD22` | `01 00 00 00` | once, at area attach |
| `F96DCDB0` | `09 00 00 00 C7 71 C3 79 12 2C EF 39 EF` (id=9) and `0B 00 00 00 CF 14 63 F5 32 F5 5F 35 EB 02 64` (id=11) | **every 30 s, forever, unanswered** |
| `4A765897` | `09 00 00 00 CF 6F 6F 2E 93 B7 43 63 6C` | once |

`F96DCDB0` is a periodic keepalive/RPC poll. The `C7 …`/`CF …` payloads inside it match the
RPC-packet shape the server itself sends (`AreaRequestRPC` bodies start with the same prefixes).
The server currently logs the decode and does not respond; the client keeps polling and never advances.

## Conclusion

1. CRT3's truncated payload caused the original `SerializationException` (confirmed twice).
2. With CRT3 skipped, the client gets much further but stalls waiting for replies to
   `F96DCDB0` (and one-shot `C586BD22` / `4A765897`) requests.
3. Next step: implement server responses for these three opcodes (echo/ack or the RPC
   payload each carries) and re-test. The 30 s cadence of `F96DCDB0` makes it the first target.

# World-entry CRT3 investigation — 2026-09-17

## Status

World entry remains broken. No fixture correction was established.
The trailing-byte removal experiment failed and CRT3 was restored
byte-for-byte from its backup.

## Confirmed evidence

The original capture pairs are:

- `world-entry-20260917-132537-33464-first.dmp`
- `world-entry-20260917-132538-33464-unhandled.dmp`
- `world-entry-20260917-133948-24676-first.dmp`
- `world-entry-20260917-133949-24676-unhandled.dmp`

Both pairs contain `G::SerializationException` objects referencing:

- First chance: `Incorrect token found in input stream`
- Unhandled: `Unable to skip missing fields when stream has no type information`

`Analyze-WorldEntryDump.py` reads these buffers without executing client code.
High x86 memory addresses are sign-extended in these dumps; the analyzer
normalizes that representation for 32-bit memory lookups. Its printed stack
scan is a list of address candidates, not a fully unwound stack.

A separate read-only frame-pointer inspection of the 13:39 first-chance
dump located the serialization reader at `0x0FD0EF38`. Its buffer pointer
was `0xED114C60`; its cursor and length were both 25. The buffer was:

```text
01 16 01 01 01 cf ff 5f 18 4a aa 9e ce 77 00 cf 40 00 01 0e 21 8a 83 9c c0
```

All 25 bytes match offset 30 of:

```text
SharpServer/bin/Debug/AreaServer/CRT/tython_blockout-4611686019869492753-1.3.acrt
```

This was the sole exact match among the 28 area fixture files checked.
The original fixture is 55 bytes; its header at offset 27 is `05 07 19`.
The complete declared 25-byte blob was present in client memory.

The original throw path includes RVA `0xDC16F`, following a failed
four-byte component read in a three-component value reader. Exhaustion
establishes a mismatch between the available input and the reader's
expectations. It does not by itself establish physical truncation of the
source capture, the identity of the incompatible field, or a bad final token.

## Failed experiment and restoration

The experiment removed the final `c0` byte and changed the declared blob
length from `0x19` to `0x18`. The controlled run still crashed:

- `world-entry-20260917-150522-15316-first.dmp`
- `world-entry-20260917-150523-15316-unhandled.dmp`
- Message in both: `Past the end of the stream`
- Stack includes RVAs `0x1B0F77`, `0x1AC3DC`, `0xF4746`, `0x4D5097`

A changed throw site is not proof of progress. The integer-only token walk
used to justify removing `c0` was invalid for this mixed-type, style-7
payload. Raw float bytes and compact field-state encoding cannot be
validated as a sequence of packed integers. Earlier comparisons also
included incorrectly aligned slices of some other fixtures; they must not
be used as schema evidence.

CRT3 was restored and verified against the full original byte sequence.
Its SHA256 is:

```text
3e79b4c94fadfad09db854b2979027bb2187d230cc2cb37493dd140d86c3cfba
```

Backup:

```text
Diagnostics/CrtTokenFixBackup-20260917/tython_blockout-4611686019869492753-1.3.acrt
```

CRT4 and awareness fixtures were not modified by this experiment.

## Schema investigation

CRT3 references class `0x40000012338B5ACB`. It exists in the April core GOM:

```text
Diagnostics/GomCompatibility/ResourceCacheApril2012/systemgenerated/client.gom
```

The core file contains 7,738 records. This class has five direct fields
(names are empty in the inspected records):

| Field ID | Type descriptor bytes |
| --- | --- |
| `0x4000000F409F59D8` | `08 05 d9 70 14 a4 0b 00 00 40 08 02 09 d7 59 9f 40 0f 00 00 40` |
| `0x40000018B68A60B2` | `03` |
| `0x40000034F215C400` | `01` |
| `0x40000011FD570309` | `09 08 03 57 fd 11 00 00 40` |
| `0x4000000F4630859F` | `01` |

These direct field descriptors do not establish the complete inherited,
nested, ordered replication schema or the compact field-state encoding.

All three inspected class decoders leave style-7 class decoding
unimplemented:

- `Parser/SWTORParser/Hero/DeserializeClass.cs`
- `Tools/tor_tools/Hero/Hero/DeserializeClass.cs`
- `Tools/Hero/Hero/DeserializeClass.cs`

A known-good world-entry capture/reference server was not established.
A bounded repository binary-pattern search found no additional copy in
the files searched; excluded archives, dump files, and large files were
not exhaustively searched.

## Changes and validation scope

- Added the read-only dump analyzer.
- Added opt-in `SWTOR_TRACE_AREA_PAYLOADS=1` logging in
  `SharpServer/NET/TORGameServerPacket.cs`. It reports only area packet
  types, lengths, and at most 256 plaintext prefix bytes.
- Built that source into `Diagnostics/AreaPayloadBuild`.
- The existing area-framing test passed 38 packet-body cases against the
  isolated build before the fixture experiment.
- The controlled client launch used the installed server executable,
  not the isolated diagnostic build.
- No successful world-entry result has been observed.
- The framing test verifies routing and fixture preservation, not
  compatibility of the embedded schema with the client.
- The controlled launch started server processes reported as
  `NexusToRServer` PID 5424 and `ShardListServer` PID 30560. Their current
  status must be checked before any subsequent restart.

## Next required evidence

Establish style-7 field-state decoding and resolve the relevant inherited
and nested class definitions, then map the captured cursor to the exact
expected field. Alternatively, obtain a compatible reference payload
with known provenance and schema. Only then propose a replacement
fixture, validate it with a schema-aware decoder, and test world entry.

Do not strip `c0`, append guessed float values, suppress the exception,
or label a passing outer-framing test as a gameplay fix.


## Follow-up: latest captures and wire validation

Added two diagnostics:

- `D:\SWTORClassic\swtoremu\Diagnostics\Inspect-WorldEntryReader.py`
- `D:\SWTORClassic\swtoremu\Diagnostics\Test-AreaWireRoundTrip.ps1`

The build-specific reader inspection uses the saved x86 frame-pointer chain,
return RVA `0x1AE35A`, repeated reader arguments, and the observed style-7
reader layout. It is not a general native unwinder or field decoder.

Both first-chance dumps at 15:44:10 and 16:16:41 contain the complete original
25-byte CRT3 buffer at fixture offset 30, with cursor 25 and length 25.
The reader/buffer addresses are respectively `0B73F238`/`ED1F5160` and
`0FBDF038`/`ED864C60`.

The existing C# source built successfully with warnings to the isolated folder
`D:\SWTORClassic\swtoremu\Diagnostics\AreaWireBuild`. The installed executable
was not replaced. A newly emitted 63-byte plaintext CRT3 packet matches the
55-byte fixture exactly after its 8-byte opcode/routing header. `fc /b` reported
no differences; both bodies have the original SHA256 recorded above. The
emitted inner buffer also matches all 25 bytes in both captured readers.

Validation:

- 54 cases passed fixture preservation, routing, effect length prefixes,
  transport header/checksum, and raw-deflate round trips (17 CRT, 2 awareness,
  8 effect fixtures at two destination handles).
- The existing outer-framing test passed 38 cases against the isolated build.
- Compression history is retained across the test sequence, but that sequence
  is not the complete live startup sequence. Encryption and native field
  decoding are outside the round-trip test's scope.
- Tests require 32-bit PowerShell to load the x86 assembly.

Reproduce:

```powershell
& 'C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe' -NoProfile -NonInteractive -ExecutionPolicy Bypass -File 'D:\SWTORClassic\swtoremu\Diagnostics\Test-AreaWireRoundTrip.ps1' -Crt3OutputPath 'D:\SWTORClassic\swtoremu\Diagnostics\AreaWireBuild\crt3-plaintext.bin'
python -B 'D:\SWTORClassic\swtoremu\Diagnostics\Inspect-WorldEntryReader.py' --emitted-packet 'D:\SWTORClassic\swtoremu\Diagnostics\AreaWireBuild\crt3-plaintext.bin' 'D:\SWTORClassic\swtoremu\Diagnostics\world-entry-20260917-154410-35280-first.dmp'
```

### Narrower native failure evidence

Read-only inspection of the disassembly and 15:44 dump shows the failing call
is the third four-byte component read. The reader word at +0x28 is 5, selecting
the raw-read branch in RVA `0xC96F0`, not the branch requiring float token 0x82.
The vector reader receives value state 1. Its caller initializes three float
slots to zero before the call. At the exception those slots contain:

```text
cf 40 00 01 | 0e 21 8a 83 | 9c c0 00 00
```

These correspond to the final ten payload bytes beginning at inner offset 15:
two complete raw components and a partial third. The generic token error is
therefore not evidence that a token byte itself needs removing. The mapping
from this nested value to an actual field/contract remains unresolved.

No production source or fixture was changed. No new live run was performed,
and no existing server process was restarted. At the last process check there
was no live client to attach to; no cdb/windbg was found on PATH or in the
checked Windows Kits debugger directory. World entry is still unresolved.
