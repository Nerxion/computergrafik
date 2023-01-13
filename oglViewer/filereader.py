import numpy as np

# teilt erstmal alle Zeilen in ein Array
def getLinesSplitted(path):
    f = open(path, "r")
    alleLines = f.readlines()
    alleLinesSplitted = []
    for line in alleLines:
        alleLinesSplitted.append(line.split(' '))
    f.close()
    for line in alleLinesSplitted:
        line[:] = [s.rstrip("\n") for s in line]
    return alleLinesSplitted

# gibt ein Array vom jeweiligen Buchstaben zurück
def gesArrayZuEinzArray(gesamtArray, lineStart):
    einzelnesArray = []
    for line in gesamtArray:
        if (line[0] == lineStart):
            einzelnesArray.append(line)
    return einzelnesArray

# gibt alle v Werte in einem Array zurück
def readInV(gesamtArray):
    einzelnesArray = gesArrayZuEinzArray(gesamtArray, "v")
    endArray = []
    for line in einzelnesArray:
        for ele in line:
            if (ele != "v"):
                if (ele != ""):
                    endArray.append(float(ele))
    return endArray

# gibt alle vn Werte aus den f in einem Array zurück
def readInVN(gesamtArray):
    einzelnesArray = gesArrayZuEinzArray(gesamtArray, "f")
    vnArray = []
    for line in einzelnesArray:
        for ele in line:
            if (ele != "f"):
                if (ele != ""):
                    eleSplitted = ele.split("//")
                    vnArray.append(int(eleSplitted[1])-1)
    return vnArray

# gibt alle Punkte aus f zurück, aka ohne vn falls gegeben (quasi nur die Punkt-Indize)
def readInF(gesamtArray, vn):
    einzelnesArray = gesArrayZuEinzArray(gesamtArray, "f")
    endArray = []
    for line in einzelnesArray:
        for ele in line:
            if (ele != "f"):
                if (ele != ""):
                    if (vn):
                        eleSplitted = ele.split("//")
                        endArray.append(int(eleSplitted[0])-1)
                    else: 
                        endArray.append((int(ele))-1)
    return endArray

# gibt true oder falls zurück, je nachdem, ob vn schon gegeben sind oder nicht
def hasNormalsGiven(gesamtArray):
    einzelnesArray = gesArrayZuEinzArray(gesamtArray, "f")
    hasNormals = False
    for line in einzelnesArray:
        for ele in line:
            if ("//" in ele):
                hasNormals = True
    return hasNormals

# Normalenberechnung (von vorheriger Aufgabe), nutzt v und f in originalem Status mit den einzelnen Zeilen
def normalenBerechnung(gesamtArray):
    varray = gesArrayZuEinzArray(gesamtArray, "v")
    farray = gesArrayZuEinzArray(gesamtArray, "f")
    vnarray = []
    newfarray = []
    for line in farray:
        p1 = varray[int(line[1])-1]
        p2 = varray[int(line[2])-1]
        p3 = varray[int(line[3])-1]
        p1 = [float(p1[1]),float(p1[2]),float(p1[3])]
        p2 = [float(p2[1]),float(p2[2]),float(p2[3])]
        p3 = [float(p3[1]),float(p3[2]),float(p3[3])]
        p1v = np.array(p1)
        p2v = np.array(p2)
        p3v = np.array(p3)
        v1 = np.array(p2v - p1v)
        v2 = np.array(p3v - p1v)
        normale = np.cross(v1,v2)
        vnarray.append(normale.tolist())
        stelle1 = line[1] + "//" + str(len(vnarray)-1)
        stelle2 = line[2] + "//" + str(len(vnarray)-1)
        stelle3 = line[3] + "//" + str(len(vnarray)-1)
        newfarray.append([line[0], stelle1, stelle2, stelle3])
    return newfarray
