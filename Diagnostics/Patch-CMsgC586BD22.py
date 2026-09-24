r'''
Force re-send of the full in-world init + the two enter-world signals on every
CMsgC586BD22 when SWTOR_RE_SEND_INIT=1 (env var read at send time; restart
the server to pick up a change).

Also re-send the two enter-world signals (RendezvousPoint + ChangeState) via
AreaEnterSignals.Fire(client, "attach") under the same env gate, so a clean
run gets them on first attach (ActiveCharacter==null path) AND a re-attach run
gets them re-emitted when SWTOR_RE_SEND_INIT=1.
'''
import re, sys

PATH = r'D:\SWTORClassic\swtoremu\SharpServer\NET\Packets\Client\CMsgC586BD22.cs'

s = open(PATH, 'r', encoding='utf-8').read()

old = (
    '            else { Log.Write(LogLevel.Client, "CMsgC586BD22: area-entry re-attach char={0} (AreaServiceID={1}); placement already done, init skipped.", charID, client.AreaServiceID); }\n'
    '            // Echo the attach request back so the client can complete its handshake.\n'
)
new = (
    '            else\n'
    '            {\n'
    '                Log.Write(LogLevel.Client, "CMsgC586BD22: area-entry re-attach char={0} (AreaServiceID={1}); placement already done.", charID, client.AreaServiceID);\n'
    '                if (Environment.GetEnvironmentVariable("SWTOR_RE_SEND_INIT") == "1")\n'
    '                {\n'
    '                    Log.Write(LogLevel.Client, "CMsgC586BD22: SWTOR_RE_SEND_INIT=1; re-sending in-world init + attach signals on re-attach.");\n'
    '                    SendInWorldInit(client);\n'
    '                    AreaEnterSignals.Fire(client, "attach");\n'
    '                }\n'
    '            }\n'
    '            // Echo the attach request back so the client can complete its handshake.\n'
)

if old not in s:
    print('ERROR: expected old text not found in %s' % PATH)
    print('--- begin dump of target region ---')
    i = s.find('ulong charID')
    print(s[i:i+700])
    print('--- end dump ---')
    sys.exit(1)

s2 = s.replace(old, new, 1)
open(PATH, 'w', encoding='utf-8').write(s2)
print('patched %s (%d bytes -> %d bytes)' % (PATH, len(s), len(s2)))
