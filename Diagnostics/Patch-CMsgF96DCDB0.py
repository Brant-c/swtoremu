r'''
Answer the client's CMsgF96DCDB0 RPC request with SMSG_RESULTS (0xD5280283)
instead of an echo/ack/swallow. Env-controlled via RpcReply:
  SWTOR_RPC_REPLY_MODE = results (default) | echo | swallow | ack
  SWTOR_RPC_RESULT_A / SWTOR_RPC_RESULT_B = the two result strings.
'''
import re, sys

PATH = r'D:\SWTORClassic\swtoremu\SharpServer\NET\Packets\Client\CMsgF96DCDB0.cs'
s = open(PATH, 'r', encoding='utf-8-sig').read()

# Match from the mode lookup through the end of the if/else chain.
pat = re.compile(
    r'var mode = AreaPollExperiment\.GetMode\("CMsgF96DCDB0"\);.*?\n(\s*)\}\n(\s*)\}\n',
    re.S)

new = (
    'var mode = RpcReply.GetMode();\r\n'
    '            if (mode == RpcReply.Mode.Results)\r\n'
    '            {\r\n'
    '                RpcReply.SendResults(client, 0x65B3, client.AreaServiceID, "CMsgF96DCDB0");\r\n'
    '                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "sms-results-sent");\r\n'
    '            }\r\n'
    '            else if (mode == RpcReply.Mode.Echo)\r\n'
    '            {\r\n'
    '                client.SendPacket(new AreaRPCPollAck(client.AreaServiceID, _body));\r\n'
    '                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "echo-reply-sent");\r\n'
    '            }\r\n'
    '            else if (mode == RpcReply.Mode.Ack)\r\n'
    '            {\r\n'
    '                client.SendPacket(new AreaRPCPollAck(client.AreaServiceID, new byte[0]));\r\n'
    '                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "empty-ack-sent");\r\n'
    '            }\r\n'
    '            else\r\n'
    '            {\r\n'
    '                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "swallowed");\r\n'
    '            }\r\n'
    '        }\r\n'
)

m = pat.search(s)
if not m:
    print('ERROR: pattern not found')
    i = s.find('var mode')
    print(repr(s[i:i+900]))
    sys.exit(1)

s2 = s[:m.start()] + new + s[m.end():]
open(PATH, 'w', encoding='utf-8-sig').write(s2)
print('patched CMsgF96DCDB0.cs (%d -> %d bytes)' % (len(s), len(s2)))
