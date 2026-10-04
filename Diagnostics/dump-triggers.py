import sys, re
path = sys.argv[1]
inst = {}
cur = None
for line in open(path, encoding='utf-8', errors='replace'):
    line = line.rstrip('\n')
    m = re.match(r'^  (\d+)=(\d+)\s*$', line)
    if m:
        cur = {'id': int(m.group(1)), 'asset': int(m.group(2)), 'props': {}}
        inst[cur['id']] = cur
        continue
    m = re.match(r'^    \.(\w+)=(.*)$', line)
    if m and cur is not None:
        cur['props'][m.group(1)] = m.group(2)

for i in inst.values():
    p = i['props']
    tct = p.get('TriggerClassType', '')
    if tct or p.get('Tag', '') not in ('', 'false'):
        print('id=%d asset=%d' % (i['id'], i['asset']))
        for k in sorted(p):
            print('    .%s=%s' % (k, p[k]))
        print()
