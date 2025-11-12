from math import pi, sin, cos
s = int(input("Sides: "))
name = input("Name of shape: ")
shape = []
for i in range(s):
    theta = 2*pi/s*i
    shape.append((cos(theta)*100,sin(theta)*100,-100))
for i in range(s):
    theta = 2*pi/s*i
    shape.append((cos(theta)*100,sin(theta)*100,100))
with open(name+".shp","w") as f:
    f.write(str(shape))