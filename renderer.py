# Imports ¯\_( ͡° ͜ʖ ͡°)_/¯
from math import cos, sin, sqrt, pi, nan, isnan, log, e, tan
import sys
import random
 
import pygame
from pygame.locals import *

import numpy as np

import _thread

import os

from stl import mesh

import subprocess

import keyboard

shape = []


def xyToCameraPlane(camPos, worldPos):
    a, b, c = camPos[0], camPos[1], camPos[2]
    x0, y0, z0 = worldPos[0], worldPos[1], worldPos[2]
    x = x0-a*(a*x0+b*y0)/(a**2+b**2+c**2)
    y= y0-b*(a*x0+b*y0)/(a**2+b**2+c**2)
    z = -c*(a*x0+b*y0)/(a**2+b**2+c**2)
    return [x,y,z]

def open_file_dialog():
    ps = r'''
    Add-Type -AssemblyName System.Windows.Forms | Out-Null
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Filter = "STL Files (*.stl)|*.stl|All Files (*.*)|*.*"
    $dialog.InitialDirectory = [Environment]::GetFolderPath("Desktop")
    $dialog.ShowDialog() | Out-Null
    $dialog.FileName
    '''
    return subprocess.check_output(["powershell", "-NoProfile", "-Command", ps], text=True).strip()

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

def project_point(p, fov = 5):
    try:
        factor = fov / (p[2])
    except ZeroDivisionError:
        factor = 1
    x_proj = p[0] * factor
    y_proj = p[1] * factor
    if type(x_proj) == np.float32:
        return (float(x_proj), float(y_proj))
    else:
        return (x_proj, y_proj)


def normalize(v):
    v = np.array(v)
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

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

cameraPos = [0,0,0]

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
    global tool
    global toolDist
    global pointFieldMode
    global func
    global n
    while True:
        try:
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
                    shape.extend(move((float(command[2]),float(command[3]),float(command[4])),shapes[int(command[1])]))
                else:
                    print("Not a valid shape")
            elif(command[0] == "spin"):
                spinning = not spinning
            elif(command[0] == "color"):
                bgColor = [int(i) for i in command[1:4]]
                fgColor = [int(i) for i in command[4:7]]
            elif(command[0] == "save"):
                with open(command[1] + ".shps", "w") as f:
                    f.write(str(shape))
            elif(command[0] == "load"):
                with open(command[1] + ".shps", "r") as f:
                    exec("shape = " + f.read(), {"np": np}, globals())
            elif(command[0] == "pointfield"):
                pointFieldMode = not pointFieldMode
                if(pointFieldMode):
                    func = command[1]
                    n = int(command[2])
            elif(command[0] == "help"):
                if(len(command) == 1):
                    print("Right click to rotate the camera, press backspace to delete a face, left click on a face to attached another shape to it, use WASD to move, hit shift to go fast")
                    print("Commands:")
                    print("set - sets a parameter")
                    print("shape - creates a shape at given coordinates")
                    print("color - sets background and foreground colors")
                    print("save - saves shapes as .shps file")
                    print("load - load .shps file")
                    print("spin - s p i n")
                    print("help - helps with a command or prints help menu (e.g. help <command> or help)")
                    print("pointfield - creates a point field with an equation")
                    print("stl - loads an stl file")
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
                    print("Save and load files (obviously) (e.g. save <filename> or load <filename> filename should be without suffix)")
                    print("Available files:")
                    for file in os.listdir("./"):
                        if file.endswith(".shps"):
                            print(file)
                elif(command[1] == "stl"):
                    print("Load stl files (e.g. stl <x> <y> <z>)")
                else:
                    print("Help not availible for specified command.")
            elif(command[0] == "stl"):
                path = open_file_dialog()
                shapeTemp = mesh.Mesh.from_file(path).vectors
                shapeTemp /= 10
                if("xyz" not in path):
                    shapeTemp = shapeTemp[:, :, [0, 2, 1]]
                else:
                    shapeTemp = shapeTemp[:, :, [1,0,2]]
                shapeTemp[:, :, 1] -= 1
                shapeTemp[:, :, 1] = -shapeTemp[:, :, 1]
                shapeTemp = shapeTemp.tolist()

                shapeTemp = move((float(command[1]), float(command[2]), float(command[3])), shapeTemp)

                shape.extend(shapeTemp)
            else:
                print(f"Unknown commmand \"{command[0]}\"")
        except IndexError:
            print("Bad amount of parameters")

_thread.start_new_thread(console, ())

dragging = False

mouseX, mouseY = 0, 0

dragStart = (0,0)
psiStart = 0
phiStart = 0

worldPos = [0, 0, 0]

while True:
    forward = np.array([
        -np.cos(psi) * np.sin(phi),
        np.sin(psi),
        -np.cos(psi) * np.cos(phi)
    ])

    right = np.array([
        np.sin(phi - np.pi/2),
        0,
        np.cos(phi - np.pi/2),
    ])

    if(keyboard.is_pressed("shift")):
        move_speed = 0.5
    else:
        move_speed = 0.2

    if keyboard.is_pressed("w"):
        cameraPos += forward * move_speed
    if keyboard.is_pressed("s"):
        cameraPos -= forward * move_speed
    if keyboard.is_pressed("a"):
        cameraPos -= right * move_speed
    if keyboard.is_pressed("d"):
        cameraPos += right * move_speed

    backspace = False
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
        if event.type == MOUSEBUTTONUP:
            if(event.button == 3):
                dragging = False

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
                phi = phiStart + vector[0]/100
                psi = psiStart + vector[1]/100
        elif event.type == pygame.VIDEORESIZE:
                width, height = event.size
                screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        if(event.type == KEYDOWN):
            if(event.key == K_BACKSPACE):
                backspace = True
    rotpoints = []
    visibleFaces = []
    for face in shape:
        rotface = []
        behind = True
        for point in face:
            camRelative = np.subtract(point, cameraPos)
            rotX = rot_point_origin(camRelative, -phi, "y")
            rotY = rot_point_origin(rotX, -psi, "x")
            rotface.append(rotY)
            if rotY[2] > 0:
                behind = False  # At least one point is in front
        if behind:
            visibleFaces.append(rotface)
        rotpoints.append(rotface)

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
    for i, face in enumerate(shape):
        if(i < len(rotpoints)):
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

        normal = normalize(np.cross(np.subtract(face3d[1], face3d[0]), np.subtract(face3d[2], face3d[0])))

        if (fill and rotpoints[i] in visibleFaces):
            if(not randomFill):
                pygame.draw.polygon(screen,fgColor,face)
            else:
                pygame.draw.polygon(screen,(abs(normal[0]*255),abs(normal[1]*255),abs(normal[2]*255)),face)

    for index in reversed(indexesByCloseness.keys()):
        i = int(index)
        face = rotpoints2d[i]
        if(rotpoints[i] in visibleFaces):
            if ((point_in_polygon((mouseX,mouseY),face)) and (not selected)):
                if(backspace):
                    del shape[i]
                try:
                    pygame.draw.polygon(screen, (127,127,255), face.tolist())
                except AttributeError:
                    pygame.draw.polygon(screen, (127,127,255), face)
            if(point_in_polygon((mouseX,mouseY),face) and (not added) and mouseDown):
                face3d = np.array(shape[i])
                normal = normalize(np.cross(np.subtract(face3d[1],face3d[0]),np.subtract(face3d[2],face3d[0])))
                faceCenter = face3d.mean(axis=0)
                newPos = normal*toolDist + faceCenter
                shape.extend(move((newPos[0],newPos[1],newPos[2]),shapes[tool]))
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
                pygame.draw.circle(screen, fgColor, (projected[0]*scale+width/2,projected[1]*scale+height/2), 3)

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

    pygame.display.flip()
    fpsClock.tick(fps)