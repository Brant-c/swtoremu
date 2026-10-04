import sys

path = sys.argv[1]
center = int(sys.argv[2])
before = int(sys.argv[3]) if len(sys.argv) > 3 else 60
after = int(sys.argv[4]) if len(sys.argv) > 4 else 90

with open(path, 'r', errors='replace') as f:
    lines = f.readlines()

start = max(0, center - before - 1)
end = min(len(lines), center + after)
for n in range(start, end):
    print('%d: %s' % (n + 1, lines[n].rstrip()))
