# Imports ¯\_( ͡° ͜ʖ ͡°)_/¯
from math import cos, sin, sqrt, pi, nan, isnan, log, e, tan
import sys
import random
 
import pygame
from pygame.locals import *

import numpy as np

import _thread

import os

pygame.mixer.init()

def play_sound_async(filename):
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

def point_in_polygon(point, polygon):
    x, y = point
    inside = False

    for i in range(len(polygon)):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % len(polygon)]
        
        if ((y1 > y) != (y2 > y)) and \
           (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1):
            inside = not inside

    return inside

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

shapeUntranslated = []

shapes = []

for file in os.listdir("./"):
    if file.endswith(".sstl"):
        with open(file) as f:
            exec("shapes.append("+f.read()+")")

pygame.init()
 
fps = 60
fpsClock = pygame.time.Clock()

icon_image = pygame.image.load('icon.png')
pygame.display.set_icon(icon_image)
pygame.display.set_caption("3D Renderer")

width, height = 640, 480
screen = pygame.display.set_mode((width, height), RESIZABLE)

phi = 0
psi = pi

fill = False
randomFill = True

scale = 100

showPoints = True

orthographic = False

spinning = False

bgColor = (0,0,0)

fgColor = (255,255,255)

tool = 0

toolDist = 1

pointFieldMode = False

func = ""

n = 20

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
    global shapeUntranslated
    global scale
    global orthographic
    global showPoints
    global spinning
    global bgColor
    global fgColor
    global tool
    global toolDist
    global pointFieldMode
    global func
    global n
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
            elif(command[1] == "points"):
                showPoints = not showPoints
            elif(command[1] == "s"):
                scale = int(command[2])
            elif(command[1] == "o"):
                orthographic = True
            elif(command[1] == "p"):
                orthographic = False
            elif(command[1] == "tool"):
                tool = int(command[2])
                toolDist = float(command[3])
            else:
                print(f"Unkown parameter \"{command[1]}\"")
        elif(command[0] == "shape"):
            if(int(command[1]) < len(shapes)):
                shapeUntranslated.extend(move((float(command[2]),float(command[3]),float(command[4])),shapes[int(command[1])]))
            else:
                print("Not a valid shape")
        elif(command[0] == "spin"):
            spinning = not spinning
        elif(command[0] == "color"):
            bgColor = [int(i) for i in command[1:4]]
            fgColor = [int(i) for i in command[4:7]]
        elif(command[0] == "save"):
            with open(command[1] + ".shps", "w") as f:
                f.write(str(shapeUntranslated))
        elif(command[0] == "load"):
            with open(command[1] + ".shps", "r") as f:
                exec("shapeUntranslated = " + f.read(), {"np": np}, globals())
        elif(command[0] == "pointfield"):
            pointFieldMode = not pointFieldMode
            if(pointFieldMode):
                func = command[1]
                n = int(command[2])
        elif(command[0] == "help"):
            if(len(command) == 1):
                print("Commands:")
                print("set - sets a parameter")
                print("shape - creates a shape at given coordinates")
                print("color - sets background and foreground colors")
                print("save - saves shapes as .shps file")
                print("load - load .shps file")
                print("spin - s p i n")
                print("help - helps with a command or prints help menu (e.g. help <command> or help)")
            elif(command[1] == "set"):
                print("Sets parameter")
                print("Parameters:")
                print("f - fills the shape with foreground color")
                print("rf - fills each face with normal color")
                print("nf - disables fill")
                print("points - toggles points")
                print("s - changes scale (deprecated)")
                print("o - makes everything orthographic")
                print("p - makes everything have perspective (default)")
                print("tool - changes what shape places when clicking on a face, (e.g. set tool <shape> <normal-offset>)")
            elif(command[1] == "shape"):
                print("Creates a shape at coordinates (e.g. shape <shape-index> <x> <y> <z>)")
                print("Shape indexes:")
                i = 0
                for file in os.listdir("./"):
                    if file.endswith(".sstl"):
                        print(str(i) + " - " + file)
                        i += 1
            elif(command[1] == "color"):
                print("Sets foreground and background color (e.g. color <bgr> <bgg> <bgb> <fgr> <fgg> <fgb>)")
            elif(command[1] in ["save","load"]):
                print("Save and load save and load files (obviously) (e.g. save <filename> or load <filename> filename should be without suffix)")
                print("Available files:")
                for file in os.listdir("./"):
                    if file.endswith(".shps"):
                        print(file)
            elif(command[1] == "pointfield"):
                print("Create a point field with the given equation and number of points (e.g. pointfield <equation> <number of points in side>)")
            else:
                print("Help not availible for specified command.")
        else:
            print(f"Unknown commmand \"{command[0]}\"")

_thread.start_new_thread(console, ())

dragging = False

mouseX, mouseY = 0, 0

dragStart = (0,0)
psiStart = 0
phiStart = 0

moving = False
moveStart = (0,0)
xStart, yStart, zStart = 0, 0, 0

worldPos = [0, 0, 0]

while True:
    shape = move(worldPos,shapeUntranslated)
    mouseDown = False
    screen.fill(bgColor)
    if(spinning):
        phi += 0.02
        psi += 0.02

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == MOUSEBUTTONDOWN:
            if(event.button == 3):
                dragging = True
                dragStart = event.pos
                phiStart = phi
                psiStart = psi
            if(event.button == 1):
                mouseDown = True
            if(event.button == 2):
                moving = True
                moveStart = event.pos
                xStart = worldPos[0]
                yStart = worldPos[1]
        if event.type == MOUSEBUTTONUP:
            if(event.button == 3):
                dragging = False
            if(event.button == 2):
                moving = False

        if event.type == MOUSEWHEEL:
            if(pointFieldMode):
                vd += event.y/10
            else:
                vd += event.y
        if event.type == MOUSEMOTION:
            mouseX = event.pos[0]
            mouseY = event.pos[1]
            if(dragging):
                vector = np.subtract(dragStart,event.pos)
                phi = phiStart - vector[0]/100
                psi = psiStart - vector[1]/100
            if(moving):
                vector = np.subtract(moveStart,event.pos)
                worldPos[0] = xStart - vector[0]/100
                worldPos[1] = yStart - vector[1]/100
        elif event.type == pygame.VIDEORESIZE:
                width, height = event.size
                screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    if(not pointFieldMode):
        rotpoints = []
        for face in shape:
            rotface = []
            for point in face:
                rotface.append(rot_point_origin(rot_point_origin(point, phi, "y"), psi, "x"))
            rotpoints.append(rotface)

        cameraPos = (0,0,-vd)

        rotpoints2d = []
        for face in rotpoints:
            face2d = []
            for point in face:
                if(not orthographic):
                    projected = project_point(point)
                else:
                    projected = point
                face2d.append((projected[0]*scale+width/2, projected[1]*scale+height/2))
            rotpoints2d.append(face2d)
        
        indexesByCloseness = {}
        for i, face in enumerate(rotpoints):
            npFace = np.array(face)
            faceCenter = npFace.mean(axis=0)
            dist = np.linalg.norm(np.subtract(cameraPos,faceCenter))
            indexesByCloseness[str(i)] = dist

        sortedItems = sorted(indexesByCloseness.items(), key=lambda item: item[1], reverse=True)
        indexesByCloseness = dict(sortedItems)

        selected = False
        added = False

        for index in indexesByCloseness.keys():
            i = int(index)
            face = rotpoints2d[i]
            face3d = shape[i]
            if (fill):
                if(not randomFill):
                    pygame.draw.polygon(screen,fgColor,face)
                else:
                    normal = normalize(np.cross(np.subtract(face3d[1],face3d[0]),np.subtract(face3d[2],face3d[0])))
                    pygame.draw.polygon(screen,(abs(normal[0]*255),abs(normal[1]*255),abs(normal[2]*255)),face)

        for index in reversed(indexesByCloseness.keys()):
            i = int(index)
            face = rotpoints2d[i]
            if ((point_in_polygon((mouseX,mouseY),face)) and (not selected)):
                pygame.draw.polygon(screen, (127,127,255), face)
            if(point_in_polygon((mouseX,mouseY),face) and (not added) and mouseDown):
                face3d = np.array(shapeUntranslated[i])
                normal = normalize(np.cross(np.subtract(face3d[1],face3d[0]),np.subtract(face3d[2],face3d[0])))
                faceCenter = face3d.mean(axis=0)
                newPos = normal*toolDist + faceCenter
                shapeUntranslated.extend(move((newPos[0],newPos[1],newPos[2]),shapes[tool]))
                added = True
                play_sound_async("click.mp3")
            if(point_in_polygon((mouseX,mouseY),face)):
                selected = True

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
                    if(not fill):
                        pygame.draw.line(screen,fgColor, (pp1[0]*scale+width/2,pp1[1]*scale+height/2), (pp2[0]*scale+width/2,pp2[1]*scale+height/2))
    else:
        pointField = []
        for x in range(n):
            for z in range(n):
                newX = x/n-0.5
                newZ = z/n-0.5
                newFunc = func
                newFunc = newFunc.replace("y","(sqrt(x**2+z**2))")
                newFunc = newFunc.replace("x","("+str(newX)+")")
                newFunc = newFunc.replace("z","("+str(newZ)+")")
                try:
                    val = eval(newFunc)
                except Exception as exc:
                    val = nan
                pointField.append((newX,val,newZ))
        rotpoints = []
        pointFaces = []
        for i in range(len(pointField)):
            rotface = []
            try:
                if (i+1) % n != 0:
                    rotface.append(rot_point_origin(rot_point_origin(pointField[i], phi, "y"), psi, "x"))
                    rotface.append(rot_point_origin(rot_point_origin(pointField[i+n], phi, "y"), psi, "x"))
                    rotface.append(rot_point_origin(rot_point_origin(pointField[i+n+1], phi, "y"), psi, "x"))
                    rotface.append(rot_point_origin(rot_point_origin(pointField[i+1], phi, "y"), psi, "x"))
                    pointFaces.append([pointField[i],pointField[i+n],pointField[i+n+1],pointField[i+1]])
                    rotpoints.append(rotface)
            except IndexError:
                pass

        if(not orthographic):
            projectedRotpoints = []
            for face in rotpoints:
                projectedFace = []
                for point in face:
                    projected = project_point(point)
                    projectedFace.append((projected[0]*scale+width/2, projected[1]*scale+height/2))
                projectedRotpoints.append(projectedFace)
            rotpoints2d = projectedRotpoints
        else:
            rotpoints2d = []
            for face in rotpoints:
                face2d = []
                for point in face:
                    face2d.append((point[0]*scale+width/2,point[1]*scale+height/2))
                rotpoints2d.append(face2d)

        cameraPos = (0,0,-vd)

        indexesByCloseness = {}
        for i, face in enumerate(rotpoints):
            npFace = np.array(face)
            faceCenter = npFace.mean(axis=0)
            dist = np.linalg.norm(np.subtract(cameraPos,faceCenter))
            indexesByCloseness[str(i)] = dist

        sortedItems = sorted(indexesByCloseness.items(), key=lambda item: item[1], reverse=True)
        indexesByCloseness = dict(sortedItems)

        for index in indexesByCloseness.keys():
            i = int(index)
            face = rotpoints2d[i]
            face3d = rotpoints[i]
            shapeFace = pointFaces[i]
            cont = False
            for point in face3d:
                for value in point:
                    if isnan(value):
                        cont = True
            if cont: continue
            normal = normalize(np.cross(np.subtract(shapeFace[1],shapeFace[0]),np.subtract(shapeFace[2],shapeFace[0])))

            pygame.draw.polygon(screen,(abs(normal[0]*255),abs(normal[1]*255),abs(normal[2]*255)), face)


    pygame.display.flip()
    fpsClock.tick(fps)