"""Regression: locate phase callback from pinned April GUI anchor, including rel32 relocation."""
import importlib.util, struct
from pathlib import Path
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('refs',root/'Diagnostics/Inspect-V5ScriptGomRefs.py')
refs=importlib.util.module_from_spec(spec);spec.loader.exec_module(refs)
payload=refs.script_payload(root/'Diagnostics/GomCompatibility/ResourceCacheApril2012/scripts/C10C1F8290BE3551.scpt')
gui=0x32E3
oracle=0x25C3
assert gui-oracle==0xD20
expected=payload[oracle:oracle+58]
assert payload[gui-0x720:gui-0x720+58]!=expected, 'Old incorrect displacement must reject'
# Exercise relocated external calls at two different load bases. Keep body
# comparison exact except the loader-owned rel32 operands.
def matches(actual,pattern):
 i=0
 while i<len(pattern):
  if actual[i]!=pattern[i]: return False
  if pattern[i:i+5]==bytes.fromhex('E8 FC FF FF FF'): i+=5
  else: i+=1
 return True
for imagebase,scriptbase in [(0x230000,0xEC710000),(0x400000,0xF0000000)]:
 loaded=bytearray(payload)
 helper=imagebase+0x1D20A0
 for base,operand,end in [(gui,15,19),(oracle,0x12,0x16)]:
  struct.pack_into('<I',loaded,base+operand,(helper-(scriptbase+base+end))&0xffffffff)
 candidate=gui-0xD20
 assert matches(loaded[candidate:candidate+58],expected)
 for base,operand,end in [(gui,15,19),(candidate,0x12,0x16)]:
  assert (scriptbase+base+end+struct.unpack_from('<I',loaded,base+operand)[0])&0xffffffff==helper
 assert loaded[candidate+0xCA7:candidate+0xCB2]==bytes.fromhex('81 C4 BC 00 00 00 5E 5F 5B 5D C3')
 loaded[candidate+5]^=1
 assert not matches(loaded[candidate:candidate+58],expected), 'Corrupt non-relocated bytes must reject'
header=(root/'Client/Hook/Src/PhaseUpdatePrefixes.h').read_text()
assert 'phaseOracleGuiDelta = 0x00000D20' in header
trace=(root/'Client/Hook/Src/PhaseUpdateTrace.h').read_text()
assert 'guiAnchor - phaseOracleGuiDelta' in trace
print('PASS callback address: old delta rejected; correct method, epilogue and both relocated TrackLine calls verified at two load bases; corrupt prefix rejected.')
