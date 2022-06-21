fdone = open('done.log', 'r')
fall = open('config.txt', 'r')
for line in fall:
  if '[packages]' in line:
    break
sdone = set()
sall = set()
for line in fdone.readlines():
  sdone.add(line.strip())
for line in fall.readlines():
  sall.add(line.strip())

print(sall.difference(sdone))
