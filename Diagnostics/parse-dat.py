import sys, re

def parse_dat(path):
    inst = {}          # instanceID -> {asset, props}
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
    return inst

def show(inst):
    p = inst['props']
    return (f"id={inst['id']} asset={inst['asset']} "
            f"pos={p.get('Position','?')} rot={p.get('Rotation','?')} "
            f"scale={p.get('Scale','?')} portal={p.get('PortalTag','?')} "
            f"tag={p.get('Tag','')!r} movable={p.get('movable','?')} "
            f"parent={p.get('ParentInstance','?')}")

inst = parse_dat(sys.argv[1])
print(f'total instances: {len(inst)}')
print('--- portals (PortalTag=true) ---')
for i in inst.values():
    if i['props'].get('PortalTag') == 'true':
        print(' ', show(i))
print('--- tagged / non-default triggers ---')
for i in inst.values():
    t = i['props'].get('Tag', '')
    if t not in ('', 'false'):
        print(' ', show(i))
print('--- instances with parent != 0 (dynamic parents) ---')
n = 0
for i in inst.values():
    if i['props'].get('ParentInstance', '0') != '0':
        print(' ', show(i)); n += 1
        if n > 40: break
print(f'   (shown {n})')
