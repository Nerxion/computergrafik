"""
/*******************************************************************************
 *
 *            #, #,         CCCCCC  VV    VV MM      MM RRRRRRR
 *           %  %(  #%%#   CC    CC VV    VV MMM    MMM RR    RR
 *           %    %## #    CC        V    V  MM M  M MM RR    RR
 *            ,%      %    CC        VV  VV  MM  MM  MM RRRRRR
 *            (%      %,   CC    CC   VVVV   MM      MM RR   RR
 *              #%    %*    CCCCCC     VV    MM      MM RR    RR
 *             .%    %/
 *                (%.      Computer Vision & Mixed Reality Group
 *
 ******************************************************************************/
/**          @copyright:   Hochschule RheinMain,
 *                         University of Applied Sciences
 *              @author:   Prof. Dr. Ulrich Schwanecke
 *             @version:   0.91
 *                @date:   12.05.2022
 ******************************************************************************/
/**         raytracerTemplate.py
 *
 *          Simple Python OpenGL program that uses PyOpenGL + GLFW to get an
 *          OpenGL 3.2 context and display an image as a 2D texture.
 ******************************************************************************/
/**         edited by: Mike Daudrich
 *          credit to: James Bowman (git raytracer)
 *              @date: 16.05.2022
 ******************************************************************************/
"""

from functools import reduce
import numbers
import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np


# -----------------------------------------------------------------------------------------------------------------------

def extract(cond, x):
    if isinstance(x, numbers.Number):
        return x
    else:
        return np.extract(cond, x)

class vec3():
    def __init__(self, x, y, z):
        (self.x, self.y, self.z) = (x, y, z)
    def __mul__(self, other):
        return vec3(self.x * other, self.y * other, self.z * other)
    def __add__(self, other):
        return vec3(self.x + other.x, self.y + other.y, self.z + other.z)
    def __sub__(self, other):
        return vec3(self.x - other.x, self.y - other.y, self.z - other.z)
    def dot(self, other):
        return (self.x * other.x) + (self.y * other.y) + (self.z * other.z)
    def __abs__(self):
        return self.dot(self)
    def norm(self):
        mag = np.sqrt(abs(self))
        return self * (1.0 / np.where(mag == 0, 1, mag))
    #cross added:
    def cross(self,other):
        a = ((self.y * other.z) - (self.z * other.y))
        b = ((self.z * other.x) - (self.x * other.z))
        c = ((self.x * other.y) - (self.y * other.x))
        #return vec3(np.cross(self,other)) # was genau macht np.cross?
        return vec3(a, b, c)
    def components(self):
        return (self.x, self.y, self.z)
    def extract(self, cond):
        return vec3(extract(cond, self.x),
                    extract(cond, self.y),
                    extract(cond, self.z))
    def place(self, cond):
        r = vec3(np.zeros(cond.shape), np.zeros(cond.shape), np.zeros(cond.shape))
        np.place(r.x, cond, self.x)
        np.place(r.y, cond, self.y)
        np.place(r.z, cond, self.z)
        return r
rgb = vec3

L = vec3(5, 5, -10)        # Point light position   
E = vec3(0, 0.35, -1)       # Eye position
FARAWAY = 1.0e39           # an implausibly huge distance

def raytrace(O, D, scene, bounce = 0):
    # O is the ray origin, D is the normalized ray direction
    # scene is a list of Sphere objects (see below)
    # bounce is the number of the bounce, starting at zero for camera rays

    distances = [s.intersect(O, D) for s in scene] # Listen für die einzelnen Objekte
    nearest = reduce(np.minimum, distances) # schaut bei den 4 Werten (weil 4 Objekte)(also Listen durch), welcher der kleinste ist - man will nur den nächsten Punkt an der Kamera
    color = rgb(0, 0, 0)
    for (s, d) in zip(scene, distances): # zip verknüpft Objekte mit ihren Distanz-Listen
        hit = (nearest != FARAWAY) & (d == nearest)
        if np.any(hit):
            dc = extract(hit, d)
            Oc = O.extract(hit)
            Dc = D.extract(hit)
            cc = s.light(Oc, Dc, dc, scene, bounce)
            color += cc.place(hit)
    return color


class Sphere:
    def __init__(self, center, r, diffuse, mirror = 0.5):
        self.c = center
        self.r = r
        self.diffuse = diffuse
        self.mirror = mirror

    def intersect(self, O, D):
        b = 2 * D.dot(O - self.c)
        c = abs(self.c) + abs(O) - 2 * self.c.dot(O) - (self.r * self.r) # Folie 28, entspricht dem unten rechts nach dem "-" in der Wurzel (Skalarprodukt o-c und -r²)
        disc = (b ** 2) - (4 * c)
        sq = np.sqrt(np.maximum(0, disc))
        h0 = (-b - sq) / 2
        h1 = (-b + sq) / 2
        h = np.where((h0 > 0) & (h0 < h1), h0, h1) # boolean array(?), wenn true, dann h0, wenn false, dann h1
        pred = (disc > 0) & (h > 0) # nimmt nur Werte > 0 auf
        return np.where(pred, h, FARAWAY) # setzt Faraway Wert, wenn kein Schnittpunkt

    def diffusecolor(self, M):
        return self.diffuse

    def light(self, O, D, d, scene, bounce):
        M = (O + D * d)                         # intersection point        # Usprung + Distanz * Strahl
        N = (M - self.c) * (1. / self.r)        # normal
        toL = (L - M).norm()                    # direction to light        # Richtung zum Licht
        toO = (E - M).norm()                    # direction to ray origin   # Richtung zum Ursprung
        nudged = M + N * .0001                  # M nudged to avoid itself  # damit er sich nicht selbst reflektiert, also sich nicht selbst nochmal schneidet (Strahl reflektiert an Objekt)

        # Shadow: find if the point is shadowed or not.
        # This amounts to finding out if M can see the light
        light_distances = [s.intersect(nudged, toL) for s in scene]
        light_nearest = reduce(np.minimum, light_distances)
        seelight = light_distances[scene.index(self)] == light_nearest # self = Objekt (z.B. Kugel), vergleicht, ob eigene Distanzen die nähsten sind??

        # Ambient
        color = rgb(0.05, 0.05, 0.05)

        # Lambert shading (diffuse)
        lv = np.maximum(N.dot(toL), 0)
        color += self.diffusecolor(M) * lv * seelight

        # Reflection
        if bounce < 2: # nur 1x reflektieren
            rayD = (D - N * 2 * D.dot(N)).norm()
            color += raytrace(nudged, rayD, scene, bounce + 1) * self.mirror # mirror = wie stark reflektiert es; dann addiert auf Farbe (aka dann neue Farbe)

        # Blinn-Phong shading (specular) # Spekularlicht wie in der Vorlesung
        phong = N.dot((toL + toO).norm())
        color += rgb(1, 1, 1) * np.power(np.clip(phong, 0, 1), 50) * seelight
        return color

    # Methode zum Drehen der Sphere
    def rotate(self, winkel):
        drehmatrix = np.array([[np.cos(winkel), 0, -np.sin(winkel)], [0, 1, 0], [np.sin(winkel), 0, np.cos(winkel)]]) # Drehung um y-Achse
        punktAlsArray = np.array([self.c.x, self.c.y, self.c.z]).T # Mittelpunkt der Sphere als np Array umwandeln
        gedrehterPunkt = drehmatrix.dot(punktAlsArray) # Drehmatrix auf den Punkt anwenden
        gedrehterPunktAlsVec = vec3(gedrehterPunkt[0], gedrehterPunkt[1], gedrehterPunkt[2]) # Punkt wieder zum vec wandeln
        self.c = gedrehterPunktAlsVec # Mittelpunkt der Sphere neu setzen


class Triangle:
    def __init__(self, posA, posB, posC, diffuse, mirror = 0.5):
        self.posA = posA
        self.posB = posB
        self.posC = posC
        self.diffuse = diffuse
        self.mirror = mirror

    def intersect(self, O, D):
        # Berechnung 1 zu 1 aus Folien übernommen (Folie 30 - Ray-Triangle Intersection)
        u = self.posB - self.posA
        v = self.posC - self.posA
        w = O - self.posA

        t = 1 / (D.cross(v).dot(u)) * (w.cross(u).dot(v))
        r = 1 / (D.cross(v).dot(u)) * (D.cross(v).dot(w))
        s = 1 / (D.cross(v).dot(u)) * (w.cross(u).dot(D))

        pred = (r >= 0) & (r <= 1) & (s >= 0) & (s <= 1) & (r + s <= 1) # nimmt nur Werte auf, an denen r,s zwischen 0,1 sind und r+s kleiner gleich 1
        return np.where(pred, t, FARAWAY) # setzt Faraway Wert, wenn kein Schnittpunkt

    def diffusecolor(self, M):
        return self.diffuse

    def light(self, O, D, d, scene, bounce):
        M = (O + D * d)                         # intersection point        # Usprung + Distanz * Strahl
        N = self.posA.cross(self.posB)          # normal
        toL = (L - M).norm()                    # direction to light        # Richtung zum Licht
        toO = (E - M).norm()                    # direction to ray origin   # Richtung zum Ursprung
        nudged = M + N * .0001                  # M nudged to avoid itself  # damit er sich nicht selbst reflektiert, also sich nicht selbst nochmal schneidet (Strahl reflektiert an Objekt)

        # Shadow: find if the point is shadowed or not.
        # This amounts to finding out if M can see the light
        light_distances = [s.intersect(nudged, toL) for s in scene]
        light_nearest = reduce(np.minimum, light_distances)
        seelight = light_distances[scene.index(self)] == light_nearest # self = Objekt (z.B. Kugel), vergleicht, ob eigene Distanzen die nähsten sind??

        # Ambient
        color = rgb(0.05, 0.05, 0.05)

        # Lambert shading (diffuse)
        lv = np.maximum(N.dot(toL), 0)
        color += self.diffusecolor(M) * lv * seelight

        # Reflection
        if bounce < 2: # nur 1x reflektieren
            rayD = (D - N * 2 * D.dot(N)).norm()
            color += raytrace(nudged, rayD, scene, bounce + 1) * self.mirror # mirror = wie stark reflektiert es; dann addiert auf Farbe (aka dann neue Farbe)

        # Blinn-Phong shading (specular) # Spekularlicht wie in der Vorlesung
        phong = N.dot((toL + toO).norm())
        color += rgb(1, 1, 1) * np.power(np.clip(phong, 0, 1), 50) * seelight
        return color

    # Methode zum Drehen des Dreiecks (rotate von Sphere, aber auf jeden Punkt anwenden (also 3x))
    def rotate(self, winkel):
        # Punkt A:
        drehmatrix = np.array([[np.cos(winkel), 0, -np.sin(winkel)], [0, 1, 0], [np.sin(winkel), 0, np.cos(winkel)]]) # Drehung um y-Achse
        punktAlsArray = np.array([self.posA.x, self.posA.y, self.posA.z]).T # Punkt A als np Array umwandeln
        gedrehterPunkt = drehmatrix @ punktAlsArray # Drehmatrix auf den Punkt anwenden
        gedrehterPunktAlsVec = vec3(gedrehterPunkt[0], gedrehterPunkt[1], gedrehterPunkt[2]) # Punkt wieder zum vec wandeln
        self.posA = gedrehterPunktAlsVec # Punkt A neu setzen
        # Punkt B:
        drehmatrix = np.array([[np.cos(winkel), 0, -np.sin(winkel)], [0, 1, 0], [np.sin(winkel), 0, np.cos(winkel)]]) # Drehung um y-Achse
        punktAlsArray = np.array([self.posB.x, self.posB.y, self.posB.z]).T # Punkt B als np Array umwandeln
        gedrehterPunkt = drehmatrix.dot(punktAlsArray) # Drehmatrix auf den Punkt anwenden
        gedrehterPunktAlsVec = vec3(gedrehterPunkt[0], gedrehterPunkt[1], gedrehterPunkt[2]) # Punkt wieder zum vec wandeln
        self.posB = gedrehterPunktAlsVec # Punkt B neu setzen
        # Punkt C:
        drehmatrix = np.array([[np.cos(winkel), 0, -np.sin(winkel)], [0, 1, 0], [np.sin(winkel), 0, np.cos(winkel)]]) # Drehung um y-Achse
        punktAlsArray = np.array([self.posC.x, self.posC.y, self.posC.z]).T # Punkt C als np Array umwandeln
        gedrehterPunkt = drehmatrix.dot(punktAlsArray) # Drehmatrix auf den Punkt anwenden
        gedrehterPunktAlsVec = vec3(gedrehterPunkt[0], gedrehterPunkt[1], gedrehterPunkt[2]) # Punkt wieder zum vec wandeln
        self.posC = gedrehterPunktAlsVec # Punkt C neu setzen


class Plane:
    def __init__(self, center, normal, diffuse, mirror=0.05):
        self.c = center
        self.n = normal
        self.diffuse = diffuse
        self.mirror = mirror

    def intersect(self, O, D):
        co = O - self.c
        t = -self.n.dot(co) / self.n.dot(D)
        return np.where((t > 0), t, FARAWAY)

    def diffusecolor(self, M):
        checker = ((M.x * 2).astype(int) % 2) == ((M.z * 2).astype(int) % 2)
        return self.diffuse * checker

    def light(self, O, D, d, scene, bounce):
        M = (O + D * d)                         # intersection point        # Usprung + Distanz * Strahl
        N = self.n                              # normal
        toL = (L - M).norm()                    # direction to light        # Richtung zum Licht
        toO = (E - M).norm()                    # direction to ray origin   # Richtung zum Ursprung
        nudged = M + N * .0001                  # M nudged to avoid itself  # damit er sich nicht selbst reflektiert, also sich nicht selbst nochmal schneidet (Strahl reflektiert an Objekt)

        # Shadow: find if the point is shadowed or not.
        # This amounts to finding out if M can see the light
        light_distances = [s.intersect(nudged, toL) for s in scene]
        light_nearest = reduce(np.minimum, light_distances)
        seelight = light_distances[scene.index(self)] == light_nearest # self = Objekt (z.B. Kugel), vergleicht, ob eigene Distanzen die nähsten sind??

        # Ambient
        color = rgb(0.05, 0.05, 0.05)

        # Lambert shading (diffuse)
        lv = np.maximum(N.dot(toL), 0)
        color += self.diffusecolor(M) * lv * seelight

        # Reflection
        if bounce < 2: # nur 1x reflektieren
            rayD = (D - N * 2 * D.dot(N)).norm()
            color += raytrace(nudged, rayD, scene, bounce + 1) * self.mirror # mirror = wie stark reflektiert es; dann addiert auf Farbe (aka dann neue Farbe)

        # Blinn-Phong shading (specular) # Spekularlicht wie in der Vorlesung
        phong = N.dot((toL + toO).norm())
        color += rgb(1, 1, 1) * np.power(np.clip(phong, 0, 1), 50) * seelight
        return color

    # Methode zum Drehen der Plane (rotate von Sphere basically)
    def rotate(self, winkel):
        drehmatrix = np.array([[np.cos(winkel), 0, -np.sin(winkel)], [0, 1, 0], [np.sin(winkel), 0, np.cos(winkel)]]) # Drehung um y-Achse
        punktAlsArray = np.array([self.c.x, self.c.y, self.c.z]).T # Mittelpunkt der Plane als np Array umwandeln
        gedrehterPunkt = drehmatrix.dot(punktAlsArray) # Drehmatrix auf den Punkt anwenden
        gedrehterPunktAlsVec = vec3(gedrehterPunkt[0], gedrehterPunkt[1], gedrehterPunkt[2]) # Punkt wieder zum vec wandeln
        self.c = gedrehterPunktAlsVec # Mittelpunkt der Plane neu setzen

# -----------------------------------------------------------------------------------------------------------------------


class Scene:
    """
        OpenGL 2D scene class that render a textured quad.
        DO NOT CHANGE ANY OF THE GIVEN FUNCTIONS EXCEPT raytrace_image()
    """

    # initialization
    def __init__(self, width, height, scenetitle="2D Scene"):
        # time
        self.scenetitle = scenetitle
        self.width = width
        self.height = height
        self.texture_id = None
        self.anzahlPos = 0
        self.anzahlNeg = 0


    def set_size(self, width, height):
        self.width = width
        self.height = height
        self.initialize_image()


    def initialize_image(self):
        # initialize a texture object with empty (black) rgb image
        image_data = np.zeros((self.width, self.height, 3), dtype=np.uint8)
        w, h, d = image_data.shape
        image_data = image_data.reshape((w * h, d))
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        if not self.texture_id:
            self.texture_id = glGenTextures(1) 
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_BASE_LEVEL, 0)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, 0)
        # allocate texture for the first time
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, image_data)


    def update_img(self, image_data):
        # update texture by replace the image data of the texture object
        # using glTextSubImage2D(...) 
        w, h, d = image_data.shape
        image_data = image_data.reshape((w * h, d))

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE, image_data)
        # draw textured rectangle
        glBegin(GL_TRIANGLE_STRIP)
        for vt in np.array([(0, 0), (0, 1), (1, 0), (1, 1)]):
            glTexCoord2fv(vt)
            glVertex2fv(vt * np.array([self.width, self.height]))
        glEnd()
        glDisable(GL_TEXTURE_2D)


    def render(self):
        # if no texture_id is available (first call of render) initialize
        if not self.texture_id:
            self.initialize_image()
        else:
            image = self.raytrace_image()
            self.update_img(image)
        

    # musste in Ihrem Code rumpfuschen, wusste nicht wie ich das Rotieren sonst umsetzen soll ^^"
    def addAnzahlPos(self, anzahl):
        self.anzahlPos = self.anzahlPos + anzahl
    
    def addAnzahlNeg(self, anzahl):
        self.anzahlNeg = self.anzahlNeg + anzahl


    def raytrace_image(self, start=True):
        # generate a raytraced color image of size (self.width, self.height) .....
        from time import sleep
        sleep(.2)
        
        scene = [
            Plane(vec3(0, -1, 0), vec3(0, 1, 0), vec3(1, 1, 1)),
            Triangle(vec3(-0.5, .3, 1.2), vec3(0.5, .3, 1.2), vec3(0, 1.2, 1.2), vec3(1, 1, 0)),
            Sphere(vec3(-0.5, .3, 1.2), .4, vec3(0, 1, 0)), # links
            Sphere(vec3(0.5, .3, 1.2), .4, vec3(1, 0, 0)), # rechts
            Sphere(vec3(0, 1.2, 1.2), .4, vec3(0, 0, 1)) # oben
            ]
        
        # Rotierung:
        for i in range(self.anzahlPos): # durchläuft entsprechend der Pos-Drehungs-Anzahl
            winkel = np.pi / 10
            for obj in scene:
            #print(obj.c.x, obj.c.y, obj.c.z)
                obj.rotate(winkel)
        for i in range(self.anzahlNeg): # durchläuft entsprechend der Neg-Drehungs-Anzahl
            winkel = -(np.pi / 10)
            for obj in scene:
                obj.rotate(winkel)

        r = float(self.width) / self.height
        # Screen coordinates: x0, y0, x1, y1.
        S = (-1, 1 / r + .25, 1, -1 / r + .25)
        x = np.tile(np.linspace(S[0], S[2], self.width), self.height)
        y = np.repeat(np.linspace(S[1], S[3], self.height), self.width)

        Q = vec3(x, y, 0)
        color = raytrace(E, (Q - E).norm(), scene)

        #rgb = [Image.fromarray((255 * np.clip(c, 0, 1).reshape((self.height, self.width))).astype(np.uint8), "L") for c in color.components()] # von rt3.py
        rgb = [(255 * np.clip(c, 0, 1)) for c in color.components()]
        # image = np.random.randint(0, 255, (self.width, self.height, 3)) # von Schwani
        image = np.array(rgb).T.reshape(self.width, self.height, 3)

        return image
    


class RenderWindow:
    """
        GLFW Rendering window class
        YOU SHOULD NOT EDIT THIS CLASS!
    """

    def __init__(self, scene):

        # save current working directory
        cwd = os.getcwd()

        # Initialize the library
        if not glfw.init():
            return

        # restore cwd
        os.chdir(cwd)

        # version hints
        # glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        # glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        # glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
        # glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        #glfw.window_hint(glfw.COCOA_RETINA_FRAMEBUFFER, glfw.TRUE)
        # buffer hints
        glfw.window_hint(glfw.DEPTH_BITS, 32)

        # make a window
        self.width, self.height = scene.width, scene.height
        self.aspect = self.width / float(self.height)
        self.window = glfw.create_window(self.width, self.height, scene.scenetitle, None, None)
        if not self.window:
            glfw.terminate()
            return

        # Make the window's context current
        glfw.make_context_current(self.window)

        # initialize GL
        self.initGL()

        # set window callbacks
        glfw.set_mouse_button_callback(self.window, self.onMouseButton)
        glfw.set_key_callback(self.window, self.onKeyboard)
        glfw.set_window_size_callback(self.window, self.onSize)
        # hack to avoid framebuffer size error
        x, y = glfw.get_window_pos(self.window)
        glfw.set_window_pos(self.window, x+1, y+1)

        # create scene
        self.scene = scene  # Scene(self.width, self.height)

        # exit flag
        self.exitNow = False


    def initGL(self):
        # initialize OpenGL
        glEnable(GL_BLEND)
        glClear(GL_COLOR_BUFFER_BIT)
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, float(self.width), float(self.height), 0.0, 0.0, 1.0)


    def onMouseButton(self, win, button, action, mods):
        print("mouse button: ", win, button, action, mods)


    def onKeyboard(self, win, key, scancode, action, mods):
        print("keyboard: ", win, key, scancode, action, mods)
        if action == glfw.PRESS:
            # ESC to quit
            if key == glfw.KEY_ESCAPE:
                self.exitNow = True
            if key == glfw.KEY_N:
                print("key 'n' or 'N' pressed ...")
                self.scene.addAnzahlNeg(1) # in negativer Richtung rotieren 
            if key == glfw.KEY_P:
                print("key 'p' or 'P' pressed ...")
                self.scene.addAnzahlPos(1) # in positiver Richtung rotieren


    def onSize(self, win, width, height):
        self.width = width
        self.height = height
        self.aspect = width / float(height)
        self.scene.set_size(width, height)
        # update size of viewport ...
        glViewport(0, 0, self.width, self.height)
        # ... and projection matrix
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, float(self.width), float(self.height), 0.0, 0.0, 1.0)
        # hack to avoid framebuffer size error
        x, y = glfw.get_window_pos(self.window)
        glfw.set_window_pos(self.window, x+1, y+1)
        x, y = glfw.get_window_pos(self.window)        
        glfw.set_window_pos(self.window, x-1, y-1)
        

    def run(self):
        while not glfw.window_should_close(self.window) and not self.exitNow:
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT)
            self.scene.render()
            glfw.swap_buffers(self.window)
        # end
        glfw.terminate()



# main function
if __name__ == '__main__':

    # set size of render viewport
    width, height = 640, 480

    # instantiate a scene
    scene = Scene(width, height, "Raytracing Template")

    # pass the scene to a render window ... 
    rw = RenderWindow(scene)

    # ... and start main loop
    rw.run()