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
 *                @date:   07.06.2022
 ******************************************************************************/
/**         oglViewer.py
 *
 *          Simple Python OpenGL program that uses PyOpenGL + GLFW to get an
 *          OpenGL 3.2 core profile context and animate an object.
 ******************************************************************************/
/**         edited by: Mike Daudrich
 *              @date: 20.06.2022
 ******************************************************************************/
"""

import math
import sys
import glfw
import numpy as np

from OpenGL.GL import *
from OpenGL.arrays.vbo import VBO
from OpenGL.GL.shaders import *

from mat4 import *
from filereader import *

EXIT_FAILURE = -1


class Scene:
    """
        OpenGL scene class that render a RGB colored tetrahedron.
    """

    def __init__(self, width, height, scenetitle="Hello OpenGL"):
        self.scenetitle         = scenetitle
        self.width              = width
        self.height             = height
        self.angle_increment    = 10
        self.rotateX            = 0
        self.rotateY            = 0
        self.rotateZ            = 0
        self.ortho              = False
        self.zentrierung        = np.array([0,0,0])
        self.maxlen             = 0
        self.anfangsDrehung     = np.array([0,0,0])
        self.aktuelleDrehung    = np.identity(4) 
        self.winkel             = 0
        self.achse              = np.array([0,0,0])
        self.size               = 1


    def init_GL(self):
        # setup buffer (vertices, colors, normals, ...)
        self.gen_buffers()

        # setup shader
        glBindVertexArray(self.vertex_array)
        vertex_shader       = open("shader.vert","r").read()
        fragment_shader     = open("shader.frag","r").read()
        vertex_prog         = compileShader(vertex_shader, GL_VERTEX_SHADER)
        frag_prog           = compileShader(fragment_shader, GL_FRAGMENT_SHADER)
        self.shader_program = compileProgram(vertex_prog, frag_prog)

        # unbind vertex array to bind it again in method draw
        glBindVertexArray(0)

 
    def gen_buffers(self):
        # TODO: 
        # 1. Load geometry from file and calc normals if not available
        # 2. Load geometry and normals in buffer objects
        if(len(sys.argv) != 2):
            print("Format: python3 oglViewer.py object.obj")
            sys.exit(1)
        path = "models/" + sys.argv[1] # nimmt Argument vom obj

        gesamtArray = getLinesSplitted(path)
        varray = readInV(gesamtArray)
        
        if (hasNormalsGiven(gesamtArray)):          # Normalen sind gegeben, müssen nur extrahiert werden
            farray = readInF(gesamtArray, True)
            vnarray = readInVN(gesamtArray)
        else:                                       # Normalen nicht gegeben, müssen berechnet werde
            farray = readInF(gesamtArray, False)
            objButOnlyF = normalenBerechnung(gesamtArray)
            vnarray = readInVN(objButOnlyF)
        
        # generate vertex array object (VAO)
        self.vertex_array = glGenVertexArrays(1)
        glBindVertexArray(self.vertex_array)

        # generate and fill buffer with vertex positions (attribute 0)
        self.positions = np.array(varray, dtype=np.float32)
        pos_buffer = glGenBuffers(1)        # pos_buffer = index of opengl buffer
        glBindBuffer(GL_ARRAY_BUFFER, pos_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.positions.nbytes, self.positions, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)


        # Zeug zum Berechnen der maximalen und minimalen Koordinaten je Achse
        xmax = xmin = varray[farray[0]]
        ymax = ymin = varray[farray[1]]
        zmax = zmin = varray[farray[2]]
        for i in range(len(varray)):
            if (i%3 == 0 and i < len(varray)-2):
                x = varray[farray[i]]
                y = varray[farray[i+1]]
                z = varray[farray[i+2]]
                if x > xmax: xmax = x
                elif x < xmin: xmin = x
                if y > ymax: ymax = y
                elif y < ymin: ymin = y
                if z > zmax: zmax = z
                elif z < zmin: zmin = z
        if(xmax-xmin > self.maxlen): self.maxlen = xmax-xmin 
        if(ymax-ymin > self.maxlen): self.maxlen = ymax-ymin
        if(zmax-zmin > self.maxlen): self.maxlen = zmax-zmin
        self.zentrierung = np.array([(xmax+xmin)/(xmax-xmin), (ymax+ymin)/(ymax-ymin), (zmax+zmin)/(zmax-zmin)])


        # Normalengenerieren plus Buffer füllen (Attribut: 1) - aus Foliensatz 7, Folie 27
        self.normals = np.array(vnarray, dtype=np.int32)
        normal_buffer = glGenBuffers(1)      # nbo = index of OpenGL buffer  
        glBindBuffer(GL_ARRAY_BUFFER, normal_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.normals.nbytes, self.normals, GL_STATIC_DRAW)
        #glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, 0)
        #glEnableVertexAttribArray(1)
 
        # generate and fill buffer with vertex colors (attribute 1)
        colarray = [1.0] * len(varray)
        colors = np.array(colarray, dtype=np.float32)
        col_buffer = glGenBuffers(1) # grad mal zu 2 geändert, statt 1
        glBindBuffer(GL_ARRAY_BUFFER, col_buffer)
        glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1) # grad mal zu 2 geändert, statt 1

        # generate index buffer (for triangle strip)  
        self.indices = np.array(farray, dtype=np.int32)
        ind_buffer_object = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ind_buffer_object)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        
        # unbind buffers to bind again in draw()
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        

    def set_size(self, width, height):
        self.width = width
        self.height = height


    def draw(self):
        # TODO:
        # 1. Render geometry 
        #    (a) just as a wireframe model and - check
        #    with 
        #    (b) a shader that realize Gouraud Shading - nope
        #    (c) a shader that realize Phong Shading - nope
        # 2. Rotate object around the x, y, z axis using the keys x, y, z - check
        # 3. Rotate object with the mouse by realizing the arcball metaphor as 
        #    well as scaling an translation - check
        # 4. Realize Shadow Mapping - nope
        # 
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


        # setup matrices
        if (self.ortho):
            projection = ortho((self.width / self.height) * -1, (self.width / self.height) * 1, -1, 1, 0, 10)
        else:
            projection = perspective(45.0, self.width/self.height, 1.0, 5.0) # regular perspective as given = frustum?
            
        view       = look_at(0,0,2, 0,0,0, 0,1,0)
 
        rotMatrixX = rotate(self.rotateX, [1,0,0]) # Rotationsmatrix um die x-Achse
        rotMatrixY = rotate(self.rotateY, [0,1,0]) # Rotationsmatrix um die y-Achse
        rotMatrixZ = rotate(self.rotateZ, [0,0,1]) # Rotationsmatrix um die z-Achse
        model = rotMatrixX @ rotMatrixY @ rotMatrixZ # alle zusammenfügen

        translatematrix = translate(-self.zentrierung[0], -self.zentrierung[1], -self.zentrierung[2]) # Zentrieren
        scalematrix = scale((1/self.maxlen)*(self.size), (1/self.maxlen)*(self.size), (1/self.maxlen)*(self.size)) # Zentrieren

        arcballrot = self.aktuelleDrehung @ self.rotatePlus(self.winkel,self.achse) # Drehung auf aktuelle Position anwenden

        mvp_matrix = projection @ view @ model @ translatematrix @ scalematrix @ arcballrot

        # enable shader & set uniforms
        glUseProgram(self.shader_program)
        
        # determine location of uniform variable varName
        varLocation = glGetUniformLocation(self.shader_program, 'modelview_projection_matrix')
        # pass value to shader
        glUniformMatrix4fv(varLocation, 1, GL_TRUE, mvp_matrix)


        # enable vertex array & draw triangle(s)
        glBindVertexArray(self.vertex_array)
        glDrawElements(GL_TRIANGLES, self.indices.nbytes//4, GL_UNSIGNED_INT, None) # GL_TRIANGLE_STRIP zu GL_TRIANGLES geändert - draw all the Triangles, nicht den einen Strip wie vom Code vorher gegeben
        
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE) # zeichnet nur die Linien aka Polygonnetz ("Wireframedarstellung")

        # unbind the shader and vertex array state
        glUseProgram(0)
        glBindVertexArray(0)
    

    # basically rotate ohne radians
    def rotatePlus(self, winkel, achse):
        drehCheck = math.sqrt(np.array(achse) @ np.array(achse))
        if drehCheck == 0:
            return np.identity(4)
        c, mc, s = np.cos(winkel), 1-np.cos(winkel), np.sin(winkel)
        x, y, z = list(np.array(achse) / np.linalg.norm(np.array(achse)))
        return  np.array([[x*x*mc + c    , x*y*mc - z*s , x*z*mc + y*s  , 0],
                        [x*y*mc + z*s  , y*y*mc + c   , y*z*mc - x*s  , 0], 
                        [x*z*mc - y*s  , y*z*mc + x*s , z*z*mc + c    , 0], 
                        [     0        ,      0       ,      0        , 1]]).transpose()



class RenderWindow:
    """
        GLFW Rendering window class
    """

    def __init__(self, scene):
        # initialize GLFW
        if not glfw.init():
            sys.exit(EXIT_FAILURE)

        # request window with old OpenGL 3.2
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)

        # make a window
        self.width, self.height = scene.width, scene.height
        self.aspect = self.width / self.height
        self.window = glfw.create_window(self.width, self.height, scene.scenetitle, None, None)
        if not self.window:
            glfw.terminate()
            sys.exit(EXIT_FAILURE)

        self.drehen = False
        self.startxpos = 0
        self.zoom = False

        # Make the window's context current
        glfw.make_context_current(self.window)

        # initialize GL
        self.init_GL()

        # set window callbacks
        glfw.set_mouse_button_callback(self.window, self.on_mouse_button)
        glfw.set_key_callback(self.window, self.on_keyboard)
        glfw.set_window_size_callback(self.window, self.on_size)

        glfw.set_cursor_pos_callback(self.window, self.bewegungskontr) # wie mouse_button_callback - trackt Cursor Bewegung

        # create scene
        self.scene = scene  
        if not self.scene:
            glfw.terminate()
            sys.exit(EXIT_FAILURE)

        self.scene.init_GL()

        # exit flag
        self.exitNow = False


    def init_GL(self):
        # debug: print GL and GLS version
        # print('Vendor       : %s' % glGetString(GL_VENDOR))
        # print('OpenGL Vers. : %s' % glGetString(GL_VERSION))
        # print('GLSL Vers.   : %s' % glGetString(GL_SHADING_LANGUAGE_VERSION))
        # print('Renderer     : %s' % glGetString(GL_RENDERER))

        # set background color to black
        glClearColor(0, 0, 0, 0)     

        # Enable depthtest
        glEnable(GL_DEPTH_TEST)


    def on_mouse_button(self, win, button, action, mods):
        print("mouse button: ", win, button, action, mods)
        # TODO: realize arcball metaphor for rotations as well as
        #       scaling and translation paralell to the image plane,
        #       with the mouse. 
        if button == glfw.MOUSE_BUTTON_LEFT: # checkt, ob linker Mausbutton
            x, y = glfw.get_cursor_pos(win)
            mitte = min(self.width, self.height) / 2
            if action == glfw.PRESS: # wenn gedrückt: Anfangswert abspeichern
                self.drehen = True
                self.scene.anfangsDrehung = self.projectOnSphere(x, y, mitte)
            if action == glfw.RELEASE: # wenn losgelassen: Endwert abspeichern
                self.drehen = False
                self.scene.aktuelleDrehung = self.scene.aktuelleDrehung @ self.scene.rotatePlus(self.scene.winkel, self.scene.achse)
                self.scene.winkel = 0
        if button == glfw.MOUSE_BUTTON_MIDDLE: # checkt, ob mittlerer Mausbutton
            self.startxpos, y = glfw.get_cursor_pos(win) # y nicht genutzt
            if action == glfw.PRESS:
                self.zoom = True
            if action == glfw.RELEASE:
                self.zoom = False


    def on_keyboard(self, win, key, scancode, action, mods):
        print("keyboard: ", win, key, scancode, action, mods)
        if action == glfw.PRESS:
            # ESC to quit
            if key == glfw.KEY_ESCAPE:
                self.exitNow = True
            if key == glfw.KEY_A:
                self.scene.animate = not self.scene.animate
            if key == glfw.KEY_P:
                # TODO:
                print("toggle projection: orthographic / perspective ")
                self.scene.ortho = not self.scene.ortho
            if key == glfw.KEY_S:
                # TODO:
                print("toggle shading: wireframe, grouraud, phong")
            if key == glfw.KEY_X:
                # TODO:
                print("rotate: around x-axis")
                self.scene.rotateX += self.scene.angle_increment
            if key == glfw.KEY_Y:
                # TODO:
                print("rotate: around y-axis")
                self.scene.rotateY += self.scene.angle_increment
            if key == glfw.KEY_Z:
                # TODO:
                print("rotate: around z-axis")
                self.scene.rotateZ += self.scene.angle_increment


    def on_size(self, win, width, height):
        self.scene.set_size(width, height)


    def projectOnSphere(self, x, y, r):
        x, y = x - self.width/2.0, self.height/2.0 - y
        a = min(r*r, x**2 + y**2)
        z = math.sqrt(r*r - a)
        l = math.sqrt(x**2 + y**2 + z**2)
        return x/l, y/l, z/l


    # checkt, ob drehen oder zoomen - das ist das, was aktiv während der Bewegung dreht/zoomt
    def bewegungskontr(self, window, x, y):
        if self.drehen:
            mitte = min(self.width, self.height) / 2
            zwischenvariable = self.projectOnSphere(x, y, mitte)
            self.scene.winkel = np.arccos(np.dot(self.scene.anfangsDrehung, zwischenvariable))
            self.scene.achse = np.cross(self.scene.anfangsDrehung, zwischenvariable) # np.cross = Kreuzprodukt
        if self.zoom:
            if self.startxpos > x:
                self.scene.size *= 0.99 # 1 = nichts passiert, je niedrieger der Wert desto schnellerer Zoom
            else:
                self.scene.size /= 0.99


    def run(self):
        while not glfw.window_should_close(self.window) and not self.exitNow:
            # poll for and process events
            glfw.poll_events()

            # setup viewport
            width, height = glfw.get_framebuffer_size(self.window)
            glViewport(0, 0, width, height)
            
            # call the rendering function
            self.scene.draw()
            
            # swap front and back buffer
            glfw.swap_buffers(self.window)

        # end
        glfw.terminate()




# main function
if __name__ == '__main__':

    print("presse 'a' to toggle animation...")

    # set size of render viewport
    width, height = 640, 480

    # instantiate a scene
    scene = Scene(width, height)

    # pass the scene to a render window ... 
    rw = RenderWindow(scene)

    # ... and start main loop
    rw.run()


