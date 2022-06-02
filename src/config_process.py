import sys

with open(sys.argv[1], 'r') as f:
  d = f.read()
  d = d.replace('-', '_')

with open(sys.argv[1]+'new', 'w') as f:
  f.write(d)
