import sys

data = open('input.in')
open = data.readline().rstrip()
print(open)
root = data.readline().rstrip()
print(root)
for new in data:
    print(new.rstrip())
