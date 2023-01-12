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
 *             @version:   0.9
 *                @date:   23.05.2020
 ******************************************************************************/
/**         bezierTemplate.py
 *
 *          Simple Python OpenGL program that uses PyOpenGL + GLFW to get an
 *          OpenGL 3.2 context and display a Bezier curve.
 ******************************************************************************/
/**         edited by: Mike Daudrich
 *              @date: 03.07.2022
 ******************************************************************************/
"""

from re import A
import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np
import copy



class Scene:
    """ OpenGL 2D scene class """
    # initialization
    def __init__(self, width, height, 
                scenetitle="De Boor"):
        self.scenetitle = scenetitle
        self.pointsize = 7
        self.linewidth = 5
        self.width = width
        self.height = height
        self.points = []
        self.lines = []
        self.points_on_bezier_curve = []
        self.npPunkte = [] # Punkte als np Array
        self.knoten = [] # Knotenarray
        self.kurvenpunktanz = 0.3 # Wert zur Berechnung der Anzahl der Kurvenpunkte
        self.ordnung = 5 # Ordnung der Kurve
        self.grad = 4 # Grad der Kurve, equals ordnung-1


    # set scene dependent OpenGL states
    def setOpenGLStates(self):
        glPointSize(self.pointsize)
        glLineWidth(self.linewidth)
        glEnable(GL_POINT_SMOOTH)


    # render 
    def render(self):
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        # set foreground color to black
        glColor(0.0, 0.0, 0.0)

        # render all points
        glBegin(GL_POINTS)
        for p in self.points:
            glVertex2fv(p)
        glEnd()

        if len(self.points) >= 2: 
            # render polygon
            glLineWidth(self.linewidth)
            glBegin(GL_LINE_STRIP)
            for p in self.points:
                glVertex2fv(p)
            glEnd()

            # render bezier curve
            glColor(0.6, 0.0, 0.7) # lila Kurve hehe
            glBegin(GL_LINE_STRIP)
            for p in self.points_on_bezier_curve:
                glVertex2fv(p)
            glEnd() 

        # aus add_point hierher verschoben, damit die Ansicht nicht nur bei neuem Punkt geupdatet wird ^^
        if len(self.points) >= 2:
            self.determine_points_on_bezier_curve()           

                
    # set polygon
    def add_point(self, point):
        #self.points.append(point)
        #self.npPunkte.append(np.array([point[0], point[1]]))

        # ersten und letzten Punkt mehrmals in der Punktliste haben, damit Linie auch ordentlich durchgezogen wird
        if len(self.points) == 0:
            for i in range(5):
                self.points.append(point)
                self.npPunkte.append(np.array([point[0], point[1]]))
        else:
            for i in range(2):
                self.points.pop()
                self.npPunkte.pop()
            for i in range(3):
                self.points.append(point)
                self.npPunkte.append(np.array([point[0], point[1]]))


    # clear polygon
    def clear(self):
        self.points = []
        self.points_on_bezier_curve = []
        self.npPunkte = []
        self.knoten = []
        self.ordnung = 5
        self.grad = 4


    # determine line code
    def determine_points_on_bezier_curve(self):
        """ TODO:
            - Implement two different algorithms to determine points on a bezier curve
            1. Implementing de Casteljaus algorithm
            2. Implementing repeated subdivision 
        """
        self.points_on_bezier_curve = []

        self.knotenberechnung()

        t = 0
        while t < self.knoten[-1]:
            index = self.indexberechnung(t)
            if index is not None: # wirft sonst Error
                #point = self.deboorNonRec(self.grad, self.npPunkte, self.knoten, t, index) # nicht-rekursiver De Boor Code von Wiki
                point = self.deboor(self.grad, self.npPunkte, self.knoten, t, index) # Punkt rekursiv per De Boor berechnen
                self.points_on_bezier_curve.append(point) # und in die Kurve packen
            t += self.kurvenpunktanz # bestimmt wie "smooth" die Kurve nachher ist - je kleiner, desto smoother (0.1 = recht grob, 0.01 = sehr smooth)


    # vom Aufgabenblatt (K = {...})
    def knotenberechnung(self):
        self.knoten = [0] * self.ordnung # Ordnung-Mal die 0

        for i in range(1, len(self.points) - (self.ordnung - 1)): # von 1 bis n - (k - 1) Mal; n = Länge Punktarray, k = Ordnung
            self.knoten.append(i) # einfach die Zahlen durch

        for i in range(self.ordnung): # Ordnung-Mal...
            self.knoten.append(len(self.points) - (self.ordnung - 2)) # ... n - (k - 2); n = Länge Punktarray, k = Ordnung
    

    # durchläuft Knotenarray und gibt Index für letzten Knoten kleiner als t zurück
    def indexberechnung(self, t):
        for i in range(len(self.knoten) - 1):
            if self.knoten[i] > t:
                return i - 1

    
    def deboor(self, degree, controlpoints, knotvector, t, index):
        if degree == 0: # Abbruchbedingung, da degree immer um 1 kleiner wird
            return controlpoints[index]

        # Berechnung von Foliensatz 9, Folie 70 (de Boor Algorithm - Recursion)
        alpha = (t - knotvector[index]) / (knotvector[index + self.ordnung - degree] - knotvector[index])
        d = (1 - alpha) * self.deboor(degree-1, controlpoints, knotvector, t, index-1) + alpha * self.deboor(degree-1, controlpoints, knotvector, t, index)
        return d


    # nicht-rekursiver Code von Wiki (https://en.wikipedia.org/wiki/De_Boor%27s_algorithm)
    def deboorNonRec(self, degree, controlpoints, knotvector, t, index):
        # Wiki Code Zeug:
        # alpha = (x - t[j + k - p]) / (t[j + 1 + k - r] - t[j + k - p])
        # d[j] = (1.0 - alpha) * d[j - 1] + alpha * d[j]
        # p = degree, c = cpntrolpoints, t = knotvector, x = t
        
        # umgeformt mit den richtigen Parametern:
        d = [controlpoints[i + index - degree] for i in range(0, degree + 1)]

        for i in range(1, degree + 1):
            for j in range(degree, i-1, -1):
                alpha = (t - knotvector[j + index - degree]) / (knotvector[j + 1 + index - i] - knotvector[j + index - degree])
                d[j] = (1.0 - alpha) * d[j - 1] + alpha * d[j]
            
        return d[degree]
    
        
        


class RenderWindow:
    """GLFW Rendering window class"""
    def __init__(self, scene):
        
        # save current working directory
        cwd = os.getcwd()
        
        # Initialize the library
        if not glfw.init():
            return
        
        # restore cwd
        os.chdir(cwd)
        
        # version hints
        #glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        #glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        #glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
        #glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        
        # buffer hints
        glfw.window_hint(glfw.DEPTH_BITS, 32)

        # define desired frame rate
        self.frame_rate = 100

        # make a window
        self.width, self.height = scene.width, scene.height
        self.aspect = self.width/float(self.height)
        self.window = glfw.create_window(self.width, self.height, scene.scenetitle, None, None)
        if not self.window:
            glfw.terminate()
            return

        # Make the window's context current
        glfw.make_context_current(self.window)
    
        # initialize GL
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0,  -2, 2)
        glMatrixMode(GL_MODELVIEW)

        # set window callbacks
        glfw.set_mouse_button_callback(self.window, self.onMouseButton)
        glfw.set_key_callback(self.window, self.onKeyboard)
        glfw.set_window_size_callback(self.window, self.onSize)
        
        # create scene
        self.scene = scene #Scene(self.width, self.height)
        self.scene.setOpenGLStates()
        
        # exit flag
        self.exitNow = False


    def onMouseButton(self, win, button, action, mods):
        print("mouse button: ", win, button, action, mods)
        if action == glfw.PRESS:
            x, y = glfw.get_cursor_pos(win)
            p = [int(x), int(y)]
            scene.add_point(p)


    def onKeyboard(self, win, key, scancode, action, mods):
        print("keyboard: ", win, key, scancode, action, mods)
        if action == glfw.PRESS:
            # ESC to quit
            if key == glfw.KEY_ESCAPE:
                self.exitNow = True
            # clear everything
            if key == glfw.KEY_C:
                self.scene.clear()
            # Ordnung der Kurve verändern
            if key == glfw.KEY_K:
                if mods == glfw.MOD_SHIFT: # Kontrolle, ob Groß- oder Kleinbuchstabe
                    if self.scene.ordnung > 2: # geht sicher, dass die Ordnung nicht unter 2 fällt und somit der Grad nicht unter 1
                        self.scene.ordnung -= 1
                        self.scene.grad = self.scene.ordnung - 1
                    print("Kurvenordnung: ", self.scene.ordnung)
                else:
                    if self.scene.ordnung < (len(self.scene.points) - int((len(self.scene.points) / 3))): # geht sicher, dass die Ordnung nicht größer als die Anzahl an Punkten ist
                        self.scene.ordnung += 1
                        self.scene.grad = self.scene.ordnung - 1
                    print("Kurvenordnung: ", self.scene.ordnung)
            # Anzahl der Kurvenpunkte verändern
            if key == glfw.KEY_M:
                if mods == glfw.MOD_SHIFT: # Kontrolle, ob Groß- oder Kleinbuchstabe
                    if self.scene.kurvenpunktanz > 0.1: # soll nicht unter 0.05 fallen
                        self.scene.kurvenpunktanz -= 0.05
                    print("Kurvenpunktanzahl: ", self.scene.kurvenpunktanz)
                else:
                    if self.scene.kurvenpunktanz < 0.6: # soll nicht größer als 0.6 werden
                        self.scene.kurvenpunktanz += 0.05
                    print("Kurvenpunktanzahl: ", self.scene.kurvenpunktanz)



    def onSize(self, win, width, height):
        print("onsize: ", win, width, height)
        self.width = width
        self.height = height
        self.aspect = width/float(height)
        glViewport(0, 0, self.width, self.height)
    

    def run(self):
        # initializer timer
        glfw.set_time(0.0)
        t = 0.0
        while not glfw.window_should_close(self.window) and not self.exitNow:
            # update every x seconds
            currT = glfw.get_time()
            if currT - t > 1.0/self.frame_rate:
                # update time
                t = currT
                # clear viewport
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                # render scene
                self.scene.render()
                # swap front and back buffer
                glfw.swap_buffers(self.window)
                # Poll for and process events
                glfw.poll_events()
        # end
        glfw.terminate()




# call main
if __name__ == '__main__':
    print("daudrich_bezier.py")
    print("pressing 'C' should clear the everything")
    print("pressing 'grad' should decrease, 'K' should increase the Ordnung of the Kurve")
    print("pressing 'm' should decrease, 'M' should increase the Anzahl of Kurvenpunkte")

    # set size of render viewport
    width, height = 640, 480

    # instantiate a scene
    scene = Scene(width, height, "De Boor")

    rw = RenderWindow(scene)
    rw.run()
