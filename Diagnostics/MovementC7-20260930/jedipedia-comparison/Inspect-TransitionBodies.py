"""Validate reader transition bodies against the local decrypted April script."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
payload = (out / 'sysBaseClient.payload.bin').read_bytes()
names = json.loads((out / 'sysBaseClient.name-hashes.json').read_text())['names']
expected = {172: 0x7f34cd54, 173: 0x43a3b07f, 174: 0xbf20a815}
for index, value in expected.items():
    assert int(names[index], 16) == value

# The longer nontrivial body establishes the section origin independently of RET.
body = bytes.fromhex('83 EC 04 C7 04 24 54 03 00 00 E8 FC FF FF FF 8B 44 24 20 89 04 24 E8 FC FF FF FF 85 C0 0F 94 C0 0F B6 C0 85 D2 0F 98 C1 0F B6 C9 66 0F 44 C8 84 C9 83 C4 04 C3')
positions = [i for i in range(len(payload)) if payload.startswith(body, i)]
assert len(positions) == 1, positions
base = positions[0] - 0x7ac0
assert payload[base + 0x7a40] == 0xc3
assert payload[base + 0x7a90] == 0xc3
report = {
    'section_base_in_payload': base,
    'dictionary_hashes': {str(k): hex(v) for k, v in expected.items()},
    'bodies': {
        '_NotifyPlayerCanTravel': {'offset': '0x7a40', 'bytes': 'C3', 'instruction': 'RET'},
        '_NotifyChangeAreaRequest': {'offset': '0x7a90', 'bytes': 'C3', 'instruction': 'RET'},
        '_Room_Transition': {'offset': '0x7ac0', 'bytes': body.hex(), 'calls': ['!HM.TrackLine', '!HM.GetStringLength']},
    },
    'scope': 'Compiled script bodies only; native callbacks and other scripts may have additional behavior.'
}
(out / 'transition-bodies.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
