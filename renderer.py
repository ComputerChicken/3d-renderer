from math import cos, sin
import sys
import random
 
import pygame
from pygame.locals import *

import _thread

import os

def rotpointorigin(p, theta, axis):
    if axis == "x":
        return (p[0],p[1]*cos(theta)-p[2]*sin(theta),p[1]*sin(theta)+p[2]*cos(theta))
    if axis == "y":
       return (p[0]*cos(theta)+p[2]*sin(theta),p[1],-p[0]*sin(theta)+p[2]*cos(theta))
    if axis == "z":
        return (p[0]*cos(theta)-p[1]*sin(theta),p[0]*sin(theta)+p[1]*cos(theta),p[2])

# points = [(300,0,0),(0,100,100),(0,-100,100),(0,100,-100),(0,-100,-100)]
points = []

for x in range(2):
   for y in range(2):
        for z in range(2):
           points.append((200*x-100,200*y-100,200*z-100))

shapes = [
    [
        (0,0,100),
        (100,100,-100),
        (-100,100,-100),
        (100,-100,-100),
        (-100,-100,-100),
    ],
]

for file in os.listdir("./"):
    if file.endswith(".shp"):
        with open(file) as f:
            exec("shapes.append("+f.read()+")")

pygame.init()
 
fps = 60
fpsClock = pygame.time.Clock()
 
width, height = 640, 480
screen = pygame.display.set_mode((width, height))

phi = 0
psi = 0

fill = False
randomFill = True

def console():
    global fill
    global randomFill
    global points
    while True:
        command = input("> ").split()
        if(command[0] == "set"):
            if(command[1] == "f"):
                fill = True
                randomFill = False
            elif(command[1] == "rf"):
                fill = True
                randomFill = True
            elif(command[1] == "nf"):
                fill = False
            else:
                print(f"Unkown parameter \"{command[1]}\"")
        elif(command[0] == "shape"):
            points = shapes[int(command[1])]
        else:
            print(f"Unknown commmand \"{command[0]}\"")

_thread.start_new_thread(console)

rands = [random.randint(0,255) for i in range(100)]

# Game loop.
while True:
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == MOUSEMOTION:
            phi = event.pos[0]/100
            psi = event.pos[1]/100

    # Update.
    rotpoints = []
    for point in points:
        rotpoints.append(rotpointorigin(rotpointorigin(point, phi, "y"), psi, "x"))

    # Draw.
    for point in rotpoints:
        pygame.draw.circle(screen, (255,255,255), (point[0]+width/2,point[1]+height/2), 5)
    
    for i1, p1 in enumerate(rotpoints):
        for i2, p2 in enumerate(rotpoints):
            if(not fill):
                pygame.draw.line(screen,(255,255,255), (p1[0]+width/2,p1[1]+height/2), (p2[0]+width/2,p2[1]+height/2))
            else:
                color = rands[i1+i2]
                pygame.draw.polygon(screen,(color,color,color), [(width/2,height/2),(p1[0]+width/2,p1[1]+height/2), (p2[0]+width/2,p2[1]+height/2)])
    pygame.display.flip()
    fpsClock.tick(fps)