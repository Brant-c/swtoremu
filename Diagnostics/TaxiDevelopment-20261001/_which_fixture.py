"""Confirm which fixture build the current run actually sent.

TythonTaxi logs "fixture hash logged by AreaTaxiAwareness", so the payload
identity is in the live log. Without this check a negative result could just be
the stale fixture still being shipped.
"""
import datetime
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
log = ROOT / 'SharpServer/bin/Debug/NexusToR.log'
NEW = '7F98AA2F0CD596D26AC2FC0D45E088D54B57783D62E1F12BD870B9C621405F39'
OLD = '78CE8D7A66552C5631DE89489CC753CB2DDF3060F8C4572A8F28BF72DC95023D'

text = log.read_text(encoding='utf-8', errors='ignore')
lines = text.splitlines()
print('log mtime : %s' % datetime.datetime.fromtimestamp(
    log.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'))
print('log lines : %d' % len(lines))
print()

# Every line mentioning the taxi, plus any line carrying a payload hash.
for ln in lines:
    low = ln.lower()
    if ('tythontaxi' in low or 'areataxiawareness' in low
            or 'taxi npc' in low or NEW[:12].lower() in low
            or OLD[:12].lower() in low):
        print(ln.strip()[:230])

print()
print('NEW fixture hash present in this log: %s' % (NEW in text))
print('OLD fixture hash present in this log: %s' % (OLD in text))

print()
print('--- last 25 lines of the log ---')
for ln in lines[-25:]:
    print(ln.strip()[:200])