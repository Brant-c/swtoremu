# Schema-matched phase CRT diagnostic candidate

These files are offline candidates, not production fixtures and not captured
packets. `SharpServer/bin/Debug/AreaServer/CRT` was not modified.

- CRT1 appends dependency-first compact structures 105
  (`phsActivePhaseInfo`), 106 (`phsUniqueActivePhaseInfo`), and 107
  (`phsPlayerPhaseData`). Its pre-existing 104 structures and complete trailing
  transaction are preserved byte-for-byte.
- CRT1's little-endian schema bound at offsets `0x04..0x07` is updated from
  44,001 to 44,207 bytes so the native sub-reader includes the appended
  structures. The rejected 19:55 version omitted this framing update and was
  therefore truncated at the original schema boundary.
- CRT3 preserves its header, object, 22 value bytes, and `00` state byte. Its
  sole change is offset `0x1E`: compact structure `1` becomes `107` (`0x6B`).
- No phase value or field-state byte was invented.

SHA-256:

- CRT1: `A75C5DE9C0E32DC3C6602607FC79B216D687BE538601D3A5F9D581BF99E08229`
- CRT3: `EFE780D0AD25CB7BB14C110B60589A0B76E4EC86C474E910AFEDBC0C45F8CA7D`

Regenerate with:

```powershell
python Diagnostics/Generate-MatchedPhaseCrtCandidate.py `
  --output-dir Diagnostics/GeneratedPhaseCandidate
```

The next acceptance gate is a narrowly controlled client parse of this
correctly bounded isolated pair. Success would establish schema acceptance;
it would not by itself prove that every decoded phase value is semantically
correct.
