from math import cos, sin
import sys
import random
 
import pygame
from pygame.locals import *

import numpy as np

import _thread

import os

def rot_point_origin(p, theta, axis):
    if axis == "x":
        return (p[0],p[1]*cos(theta)-p[2]*sin(theta),p[1]*sin(theta)+p[2]*cos(theta))
    if axis == "y":
       return (p[0]*cos(theta)+p[2]*sin(theta),p[1],-p[0]*sin(theta)+p[2]*cos(theta))
    if axis == "z":
        return (p[0]*cos(theta)-p[1]*sin(theta),p[0]*sin(theta)+p[1]*cos(theta),p[2])

def project_point(p, fov = 3, viewer_distance = 4):
    factor = fov / (viewer_distance + p[2])
    x_proj = p[0] * factor
    y_proj = p[1] * factor
    return (x_proj, y_proj)

shape = []

shapes = []

for file in os.listdir("./"):
    if file.endswith(".sstl"):
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

scale = 100

orthographic = False

def console():
    global fill
    global randomFill
    global shape
    global scale
    global orthographic
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
            elif(command[1] == "s"):
                scale = int(command[2])
                print(scale)
            elif(command[1] == "o"):
                orthographic = True
            elif(command[1] == "p"):
                orthographic = False
            else:
                print(f"Unkown parameter \"{command[1]}\"")
        elif(command[0] == "shape"):
            shape = shapes[int(command[1])]
        else:
            print(f"Unknown commmand \"{command[0]}\"")

_thread.start_new_thread(console)

rands = [random.randint(0,255) for i in range(101)]

dragging = False

# Game loop.
while True:
    camera = (0,0,scale)
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == MOUSEBUTTONDOWN:
            dragging = True
        if event.type == MOUSEBUTTONUP:
            dragging = False
        if event.type == MOUSEMOTION:
            if(dragging):
                phi = event.pos[0]/101
                psi = event.pos[1]/101

    # Update.
    rotpoints = []
    for face in shape:
        rotface = []
        for point in face:
            rotface.append(rot_point_origin(rot_point_origin(point, phi, "y"), psi, "x"))
        rotpoints.append(rotface)

    # Draw.
    for face in rotpoints:
        for point in face:
            if(not orthographic):
                projected = project_point(point)
            else:
                projected = point
            pygame.draw.circle(screen, (255,255,255), (projected[0]*scale+width/2,projected[1]*scale+height/2), 5)

    for face in rotpoints:
        for p1 in face:
            for p2 in face:
                if(not orthographic):
                    pp1 = project_point(p1)
                    pp2 = project_point(p2)
                else:
                    pp1 = p1
                    pp2 = p2
                pygame.draw.line(screen,(255,255,255), (pp1[0]*scale+width/2,pp1[1]*scale+height/2), (pp2[0]*scale+width/2,pp2[1]*scale+height/2))

    pygame.display.flip()
    fpsClock.tick(fps)