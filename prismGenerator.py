from math import pi, sin, cos
s = int(input("Sides: "))
name = input("Name of shape: ")
shape = []

curFace = []
for i in range(s):
    theta = 2*pi/s*i
    curFace.append((cos(theta),sin(theta),1))
shape.append(curFace)

curFace = []
for i in range(s):
    theta = 2*pi/s*i
    curFace.append((cos(theta),-sin(theta),-1))
shape.append(curFace)

for i in range(s):
    curFace = []
    theta = 2*pi/s*i
    theta2 = 2*pi/s*(i+1)
    curFace.append((cos(theta),sin(theta),1))
    curFace.append((cos(theta),sin(theta),-1))
    curFace.append((cos(theta2),sin(theta2),-1))
    curFace.append((cos(theta2),sin(theta2),1))
    shape.append(curFace)
    
with open(name+".sstl","w") as f:
    f.write(str(shape))