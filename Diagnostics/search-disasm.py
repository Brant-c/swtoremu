import sys, re

path = sys.argv[1]
needle = sys.argv[2]  # e.g. 1153A94
print('searching %s for %s' % (path, needle))
count = 0
with open(path, 'r', errors='replace') as f:
    for n, line in enumerate(f, 1):
        if needle.lower() in line.lower():
            print('LINE %d: %s' % (n, line.rstrip()))
            count += 1
            if count >= 40:
                print('(stopped after %d matches)' % count)
                break
print('total matches shown: %d' % count)
