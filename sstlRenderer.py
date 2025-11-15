# Imports ¯\_( ͡° ͜ʖ ͡°)_/¯
from math import cos, sin, sqrt
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

vd = 4

def project_point(p, fov = 3):
    try:
        factor = fov / (vd + p[2])
    except ZeroDivisionError:
        factor = 1
    x_proj = p[0] * factor
    y_proj = p[1] * factor
    return (x_proj, y_proj)

def normalize(v):
    v = np.array(v)
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

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
screen = pygame.display.set_mode((width, height), RESIZABLE)

phi = 0
psi = 0

fill = False
randomFill = True

scale = 100

showPoints = True

orthographic = False

spinning = False

bgColor = (0,0,0)

fgColor = (255,255,255)

def move(vector, s):
    newShape = []
    for face in s:
        newFace = []
        for point in face:
            newFace.append((point[0]+vector[0],point[1]+vector[1],point[2]+vector[2]))
        newShape.append(newFace)
    return newShape

def console():
    global fill
    global randomFill
    global shape
    global scale
    global orthographic
    global showPoints
    global spinning
    global bgColor
    global fgColor
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
            elif(command[1] == "pon"):
                showPoints = True
            elif(command[1] == "poff"):
                showPoints = False
            elif(command[1] == "s"):
                scale = int(command[2])
            elif(command[1] == "o"):
                orthographic = True
            elif(command[1] == "p"):
                orthographic = False
            else:
                print(f"Unkown parameter \"{command[1]}\"")
        elif(command[0] == "shape"):
            if(int(command[1]) < len(shapes)):
                shape = shapes[int(command[1])]
            else:
                print("Not a valid shape")
        elif(command[0] == "shape2"):
            shape.extend(move((float(command[2]),float(command[3]),float(command[4])),shapes[int(command[1])]))
        elif(command[0] == "spin"):
            spinning = True
        elif(command[0] == "nospin"):
            spinning = False
        elif(command[0] == "color"):
            bgColor = [int(i) for i in command[1:4]]
            fgColor = [int(i) for i in command[4:7]]
        else:
            print(f"Unknown commmand \"{command[0]}\"")

_thread.start_new_thread(console)

rands = [random.randint(0,255) for i in range(101)]

dragging = False

# Game loop.
while True:
    screen.fill(bgColor)
    if(spinning):
        phi += 0.02
        psi += 0.02

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == MOUSEBUTTONDOWN:
            dragging = True
        if event.type == MOUSEBUTTONUP:
            dragging = False
        if event.type == MOUSEWHEEL:
            vd += event.y
        if event.type == MOUSEMOTION:
            if(dragging):
                phi = event.pos[0]/101
                psi = event.pos[1]/101
        elif event.type == pygame.VIDEORESIZE:
                width, height = event.size
                screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)

    # Update.
    rotpoints = []
    for face in shape:
        rotface = []
        for point in face:
            rotface.append(rot_point_origin(rot_point_origin(point, phi, "y"), psi, "x"))
        rotpoints.append(rotface)

    # Draw.
    if fill:
        rotpoints2d = []
        for face in rotpoints:
            face2d = []
            for point in face:
                projected = project_point(point)
                face2d.append((projected[0]*scale+width/2, projected[1]*scale+height/2))
            rotpoints2d.append(face2d)
        for i, face in enumerate(rotpoints2d):
            if(not randomFill):
                pygame.draw.polygon(screen,fgColor,face)
            else:
                pygame.draw.polygon(screen,(rands[i],rands[i],rands[i]),face)

    if(showPoints):
        for face in rotpoints:
            for point in face:
                if(not orthographic):
                    projected = project_point(point)
                else:
                    projected = point
                pygame.draw.circle(screen, fgColor, (projected[0]*scale+width/2,projected[1]*scale+height/2), 5)

    for face in rotpoints:
        for p1 in face:
            for p2 in face:
                if(not orthographic):
                    pp1 = project_point(p1)
                    pp2 = project_point(p2)
                else:
                    pp1 = p1
                    pp2 = p2
                pygame.draw.line(screen,fgColor, (pp1[0]*scale+width/2,pp1[1]*scale+height/2), (pp2[0]*scale+width/2,pp2[1]*scale+height/2))

    pygame.display.flip()
    fpsClock.tick(fps)