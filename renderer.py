# Imports ¯\_( ͡° ͜ʖ ͡°)_/¯
from math import cos, sin, sqrt, pi, nan, isnan, log, e, tan  # Import math functions used for geometry + camera transforms
import sys  # Used for sys.exit()
import random  # Randomization (unused in current code but imported)
 
import pygame  # Main rendering & input handling library
from pygame.locals import *  # Import Pygame constants (QUIT, MOUSEBUTTONDOWN, etc.)

import numpy as np  # Numerical operations, vectors, matrix transformations

import _thread  # Used to run console() as background thread

import os  # For directory scanning and file I/O

from stl import mesh  # Library for loading STL mesh files

import subprocess  # Used to execute PowerShell dialog
import keyboard  # For direct keyboard polling (WASD movement)

shape = []  # Stores list of triangle faces (each face = 3 XYZ points)
shapenp = np.array([])  # NumPy version of shape for fast math operations

def open_file_dialog():
    # Opens Windows file dialog via PowerShell and returns selected file path
    ps = r'''
    Add-Type -AssemblyName System.Windows.Forms | Out-Null
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Filter = "STL Files (*.stl)|*.stl|All Files (*.*)|*.*"
    $dialog.InitialDirectory = [Environment]::GetFolderPath("Desktop")
    $dialog.ShowDialog() | Out-Null
    $dialog.FileName
    '''
    # Execute PowerShell script and return result as string
    return subprocess.check_output(["powershell", "-NoProfile", "-Command", ps], text=True).strip()

pygame.mixer.init()  # Initialize audio system for click sounds

def play_sound_async(filename):
    # Loads audio file and plays it asynchronously (non-blocking)
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

def point_in_polygon(point, polygon):
    # Ray casting algorithm — checks if (x,y) lies inside projected polygon
    x, y = point
    inside = False

    for i in range(len(polygon)):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % len(polygon)]
        
        # Check if the scanline intersects polygon edge
        if ((y1 > y) != (y2 > y)) and \
           (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1):
            inside = not inside  # Toggle state when crossing an edge

    return inside

vd = 4  # View distance modifier used for zooming
fov = 5  # Projection scaling factor (not true FOV but scalar)

def normalize(v):
    # Normalize vector to unit length, avoid divide-by-zero
    v = np.array(v)
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

shapes = []  # Preloaded template shapes from .sstl files

for file in os.listdir("./"):
    if file.endswith(".sstl"):
        with open(file) as f:
            # Each .sstl file contains literal Python defining a shape list
            exec("shapes.append("+f.read()+")")

pygame.init()  # Start pygame environment
 
fps = 60  # Frame rate target
fpsClock = pygame.time.Clock()

iconImage = pygame.image.load('icon.png')  # Set window icon
pygame.display.set_icon(iconImage)
pygame.display.set_caption("3D Renderer")

width, height = 640, 480  # Default window size
screen = pygame.display.set_mode((width, height), RESIZABLE)

phi = 0  # Horizontal camera rotation angle
psi = pi  # Vertical camera rotation angle

fill = False  # Toggle filled polygon rendering
randomFill = True  # If True, fill color based on face normal magnitude

scale = 100  # Projection scaling factor for 2D conversion
modelScale = 1  # Scaling applied to imported models

showPoints = True  # Draw vertex points

spinning = False  # Auto-rotate scene

bgColor = (0,0,0)  # Background color (RGB)
fgColor = (255,255,255)  # Wireframe / point color (RGB)

tool = 0  # Which shape index is used when clicking to attach shapes
toolDist = 1  # Offset distance along face normal

pointFieldMode = False  # Mode: generate procedural point fields
func = ""  # Holds string expression used for point field

n = 20  # Resolution / number of samples for point field

cameraPos = [0,0,0]  # 3D world camera position (XYZ)

def move(vector, s):
    # Applies translation to shape 's' by vector (x,y,z)
    newShape = np.array(s)+np.array(vector)
    return newShape

precomputedNormals = []  # Stores normals for each face for fast access

def console():
    # Console input thread for real-time commands (runs parallel to renderer)
    # Allows typing commands like "set f", "shape 2 0 0 0", etc.
    global fill
    global randomFill
    global shape
    global scale
    global showPoints
    global spinning
    global bgColor
    global fgColor
    global tool
    global toolDist
    global pointFieldMode
    global func
    global n
    global modelScale
    global precomputedNormals
    global shapenp
    while True:
        try:
            command = input("> ").split()  # Read space-separated command tokens
            if(command[0] == "set"):
                # Handle settings toggles + config
                if(command[1] == "f"):
                    fill = True
                    randomFill = False  # Enable solid fill
                elif(command[1] == "rf"):
                    fill = True
                    randomFill = True  # Normal-based coloring
                elif(command[1] == "nf"):
                    fill = False  # Disable fill entirely (wireframe)
                elif(command[1] == "points"):
                    showPoints = not showPoints  # Toggle vertex rendering
                elif(command[1] == "s"):
                    scale = int(command[2])  # Projection scale
                elif(command[1] == "ms"):
                    modelScale = float(command[2])  # Multiplier when spawning shapes
                elif(command[1] == "tool"):
                    # Set which shape attaches to clicked face + distance offset
                    tool = int(command[2])
                    toolDist = float(command[3])
                else:
                    print(f"Unkown parameter \"{command[1]}\"")
            
            elif(command[0] == "shape"):
                # Spawn a stored shape at given XYZ offset
                if(int(command[1]) < len(shapes)):
                    shape.extend(move((float(command[2]),float(command[3]),float(command[4])),shapes[int(command[1])]))
                else:
                    print("Not a valid shape")

            elif(command[0] == "spin"):
                spinning = not spinning  # Toggle automatic rotation

            elif(command[0] == "color"):
                # Background then foreground RGB
                bgColor = [int(i) for i in command[1:4]]
                fgColor = [int(i) for i in command[4:7]]

            elif(command[0] == "save"):
                # Save shape list to custom .shps file
                with open(command[1] + ".shps", "w") as f:
                    f.write(str(shape))

            elif(command[0] == "load"):
                # Load stored shape array from .shps file
                with open(command[1] + ".shps", "r") as f:
                    exec("shape = " + f.read(), {"np": np}, globals())

            elif(command[0] == "pointfield"):
                # Enable procedural point field generator
                pointFieldMode = not pointFieldMode
                if(pointFieldMode):
                    func = command[1]  # Expression to evaluate field
                    n = int(command[2])  # Density of sampling

            elif(command[0] == "help"):
                # Print usage help for console commands
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
                path = open_file_dialog()  # User selects STL file
                shapeTemp = mesh.Mesh.from_file(path).vectors  # Load triangles
                shapeTemp /= 10  # Scale down mesh units

                # Reorder axes depending on coordinate convention of model
                if("xyz" not in path):
                    shapeTemp = shapeTemp[:, :, [0, 2, 1]]
                else:
                    shapeTemp = shapeTemp[:, :, [1,0,2]]

                # Flip Y axis to match renderer orientation
                shapeTemp[:, :, 1] -= 1
                shapeTemp[:, :, 1] = -shapeTemp[:, :, 1]
                shapeTemp = shapeTemp.tolist()

                # Offset mesh to spawn location
                shapeTemp = move((float(command[1]), float(command[2]), float(command[3])), shapeTemp)

                shape.extend(shapeTemp)  # Add triangles to scene
            else:
                print(f"Unknown commmand \"{command[0]}\"")
        except IndexError:
            print("Bad amount of parameters")

        shapenp = np.array(shape, dtype=np.float32)  # Convert to NumPy for math
        if(shapenp.size > 0):
            # Compute normals using cross product of edges (v1 × v2)
            v1 = shapenp[:,1] - shapenp[:,0]
            v2 = shapenp[:,2] - shapenp[:,0]
            precomputedNormals = np.array(np.cross(v1, v2), dtype=np.float32)

            # Normalize each normal vector
            precomputedNormals /= np.linalg.norm(precomputedNormals, axis=1, keepdims=True)
        else:
            precomputedNormals = []

_thread.start_new_thread(console, ())  # Run console() in background thread

dragging = False  # True while right mouse is held to rotate camera

mouseX, mouseY = 0, 0  # Mouse screen coordinates

dragStart = (0,0)  # Mouse position at start of drag
psiStart = 0  # Camera pitch stored at start of drag
phiStart = 0  # Camera yaw stored at start of drag

while True:
    # Compute camera direction vectors based on current angles phi, psi
    forward = np.array([
        -np.cos(psi) * np.sin(phi),  # X component of forward
        np.sin(psi),                 # Y component (vertical)
        -np.cos(psi) * np.cos(phi)   # Z component of forward
    ])

    right = np.array([
        np.sin(phi - np.pi/2),  # X component of right vector (perpendicular to forward)
        0,                       # Y component (flat)
        np.cos(phi - np.pi/2),   # Z component
    ])

    up = np.array([0,1,0])  # Global Y-up vector

    # Movement speed modifier for shift key (faster movement)
    if(keyboard.is_pressed("shift")):
        moveSpeed = 0.5
    else:
        moveSpeed = 0.2

    # WASD + vertical movement
    if keyboard.is_pressed("w"):
        cameraPos += forward * moveSpeed
    if keyboard.is_pressed("s"):
        cameraPos -= forward * moveSpeed
    if keyboard.is_pressed("a"):
        cameraPos -= right * moveSpeed
    if keyboard.is_pressed("d"):
        cameraPos += right * moveSpeed
    if keyboard.is_pressed("space"):
        cameraPos -= up * moveSpeed  # Move down
    if keyboard.is_pressed("ctrl"):
        cameraPos += up * moveSpeed  # Move up

    backspace = False  # Track if backspace is pressed for face deletion
    mouseDown = False  # Track if left mouse clicked
    screen.fill(bgColor)  # Clear screen with background color

    if(spinning):
        # Automatic scene rotation
        phi += 0.02
        psi += 0.02

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        if event.type == MOUSEBUTTONDOWN:
            if(event.button == 3):  # Right mouse
                dragging = True
                dragStart = event.pos
                phiStart = phi
                psiStart = psi
            if(event.button == 1):  # Left mouse
                mouseDown = True

        if event.type == MOUSEBUTTONUP:
            if(event.button == 3):  # Stop camera drag
                dragging = False

        if event.type == MOUSEWHEEL:
            # Zoom (vd) adjustment
            if(pointFieldMode):
                vd += event.y/10
            else:
                vd += event.y

        if event.type == MOUSEMOTION:
            mouseX = event.pos[0]
            mouseY = event.pos[1]
            if(dragging):
                # Update camera angles based on drag distance
                vector = np.subtract(dragStart,event.pos)
                phi = phiStart + vector[0]/100
                psi = psiStart + vector[1]/100

        elif event.type == pygame.VIDEORESIZE:
            # Update screen size when window is resized
            width, height = event.size
            screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)

        if(event.type == KEYDOWN):
            if(event.key == K_BACKSPACE):
                backspace = True

    faces = shapenp.reshape(-1, 3)  # Flatten faces to Nx3 vertices

    vectors = faces - cameraPos  # Translate faces relative to camera position

    # Precompute rotation matrix components
    cy, sy = np.cos(phi), np.sin(phi)
    cx, sx = np.cos(-psi), np.sin(-psi)

    Ry = np.array([
        [ cy, 0, -sy],  # Y-axis rotation
        [  0, 1,   0],
        [ sy, 0,  cy]
    ])

    Rx = np.array([
        [1, 0,  0],     # X-axis rotation
        [0, cx, -sx],
        [0, sx,  cx]
    ])

    R = Rx @ Ry  # Combined rotation matrix

    rotated = (R @ vectors.T).T  # Rotate all vertices

    rotpoints = rotated.reshape(shapenp.shape)  # Restore face grouping

    visibleFaces = []  # List of faces potentially visible (later used)
    visibilityMask = []  # Boolean mask of faces in front of camera
    for face in rotpoints:
        # True if all vertices are behind camera (z<=0), invert mask logic
        if np.invert((face[:, 2] > 0).any()):
            visibilityMask.append(True)
        else:
            visibilityMask.append(False)
  
    if(rotpoints.size > 0):
        zs = rotpoints[:,:,2]  # Z-depth for each vertex
        factors = fov / zs     # Perspective factor
        rotpoints2d = np.dstack([
            rotpoints[:,:,0] * factors * scale + width/2,   # X -> screen coordinates
            rotpoints[:,:,1] * factors * scale + height/2  # Y -> screen coordinates
        ])
    else:
        rotpoints2d = []
    
    indexesByCloseness = {}  # Dictionary mapping face index -> distance from camera
    for i, face in enumerate(shape):
        if(i < len(rotpoints)):
            npFace = np.array(face)
            faceCenter = npFace.mean(axis=0)  # Compute center point of face
            dist = np.linalg.norm(np.subtract(cameraPos,faceCenter))  # Euclidean distance
            indexesByCloseness[str(i)] = dist

    # Sort faces by distance, farthest first (painter's algorithm for proper overlap)
    sortedItems = sorted(indexesByCloseness.items(), key=lambda item: item[1], reverse=True)
    indexesByCloseness = dict(sortedItems)

    selected = False  # Track if mouse is over any polygon
    added = False     # Track if a new shape has been added this frame

    for index in indexesByCloseness.keys():
        i = int(index)
        face = rotpoints2d[i]  # Projected 2D vertices
        face3d = shape[i]       # Original 3D vertices

        try:
            normal = precomputedNormals[i]  # Get precomputed normal for lighting/color
        except IndexError:
            pass

        # Draw filled polygons if enabled and face is visible
        if (fill and visibilityMask[i]):
            if(not randomFill):
                pygame.draw.polygon(screen,fgColor,face)  # Solid color
            else:
                # Color based on normal vector components
                pygame.draw.polygon(screen,(abs(normal[0]*255),abs(normal[1]*255),abs(normal[2]*255)),face)

    # Iterate faces in reverse order (front-most first)
    for index in reversed(indexesByCloseness.keys()):
        i = int(index)
        face = rotpoints2d[i]
        if(visibilityMask[i]):
            if ((point_in_polygon((mouseX,mouseY),face)) and (not selected)):
                if(backspace):
                    del shape[i]  # Delete face under cursor if backspace pressed
                try:
                    pygame.draw.polygon(screen, (127,127,255), face.tolist())  # Highlight face
                except AttributeError:
                    pygame.draw.polygon(screen, (127,127,255), face)

            if(point_in_polygon((mouseX,mouseY),face) and (not added) and mouseDown):
                # Attach new shape to selected face
                face3d = np.array(shape[i])
                normal = precomputedNormals[i]
                faceCenter = face3d.mean(axis=0)
                newPos = normal*toolDist + faceCenter  # Offset along normal
                shape.extend(move((newPos[0],newPos[1],newPos[2]),shapes[tool]))  # Add shape
                added = True
                play_sound_async("click.mp3")  # Click feedback

                # Recompute normals after addition
                shapenp = np.array(shape, dtype=float)
                v1 = shapenp[:,1] - shapenp[:,0]
                v2 = shapenp[:,2] - shapenp[:,0]
                precomputedNormals = np.array(np.cross(v1, v2),dtype=np.float32)
                precomputedNormals /= np.linalg.norm(precomputedNormals, axis=1, keepdims=True)

            if(point_in_polygon((mouseX,mouseY),face)):
                selected = True  # Only first overlapping face is selected
    if(showPoints):
        # Draw each vertex as small circle
        for face in rotpoints2d:
            for point in face:
                pygame.draw.circle(screen, fgColor, (point[0],point[1]), 3)
                
    if(not fill):
        # Draw wireframe edges for each face
        for face in rotpoints2d:
            for p1 in face:
                for p2 in face:
                    pygame.draw.line(screen,fgColor, (p1[0],p1[1]), (p2[0],p2[1]))

    pygame.display.flip()  # Update the window with rendered frame
    fpsClock.tick(fps)     # Limit loop to target FPS