#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Script qui mosaïque les orthos de l'IGN (ECW) en France métropolitaine
# ---------------------------------------------------------------------------
# 
# Auteur    : LAVENTURE Sylvio
# Nom       : MosaiqueIRC.py
# Date      : 2 Avril 2015
# Projet    : CarHab IRSTEA (UMR TETIS)
# Version 3.0 (Sélection des images en utilisant les 4 segments d'un carré - Tuile BD Ortho)
# ---------------------------------------------------------------------------
# 
# IMPORT DES MODULES
# ---------------------------------------------------------------------------
import os, glob, shutil, sys
import subprocess, time
from osgeo import ogr


if __name__=='__main__':
    
    usage='usage: python MosaiqueIRC.py <ECW_Folder> <Area_in_shp>'
    
    if len(sys.argv) == 3:

        ##########################################
        ## Données en entrée
        ##########################################
         
        # Départ t=0
        startTime = time.time()
         
        # Dossier en entrée contenant les Orthos
        #FolderIn = r'/media/DATA/_CarHab15/HautesPyrennees_65/65-2010-irc-5x5-la93-c07-ecw'
        #FolderIn = r'/media/DATA/_CarHab15/Cher18/IRC/18-2010-irc-5x5-la93-c07-ecw'
        # FolderIn = r'/media/laventure/DATA/_CarHab16/33/33-2012-irc-5x5-la93-c07-ecw'
        FolderIn = sys.argv[1]
        if FolderIn[len(FolderIn)-1] == '/':
            FolderIn = FolderIn[:len(FolderIn)-1]
        # Listing des orthos généralement en ECW
        OrthoIRC = glob.glob(FolderIn + '/*.ecw')
         
        # Chemin du transect
        #Zone = r'/media/DATA/_CarHab15/HautesPyrennees_65/Zone_test_65_2015/zone_test_finale_2015.shp'
        Zone = sys.argv[2]
        ## Dossier en sortie
        FolderOut = os.path.split(FolderIn)[0] + '/Mosaique_OrthoIRC'
         
        # Supprime le dossier si il existe
        if os.path.exists(FolderOut):
            try: # Si rempli
                shutil.rmtree(FolderOut)
            except OSError: # Si il est vide
                try :
                    os.rmdir(FolderOut)
                except OSError:
                    pass
         
        # Creer le dossier
        if not os.path.exists(FolderOut):
            os.mkdir(FolderOut)
         
        ##########################################
        ## Sélection des images à mosaïquer
        ##########################################
        Select_OrthoIRC = [] # Variable de sélection des IRC qui intersect la zone
        # Ouverture du shapefile
        # Avec import ogr
        driver = ogr.GetDriverByName('ESRI Shapefile')
        dataSource = driver.Open(Zone, 0)
         
        if dataSource is None:
            print 'Could not open file'
            sys.exit(1)
         
        shp_ogr = dataSource.GetLayer()
         
        # Nom du fichier d'entrée
        print '\nShapefile en entrée:',shp_ogr.GetName()
         
        ## Liste le nom des champs
        Def_shp_ogr = shp_ogr.GetLayerDefn()
        field_names = [Def_shp_ogr.GetFieldDefn(l).GetName() for l in range(Def_shp_ogr.GetFieldCount())]
        print '\nNom des champs:', field_names
        print '\nNbre de champs:',len(field_names)
         
        # Nombres de polygones avec ogr
        nb_poly = shp_ogr.GetFeatureCount()
        print '\nNombre de polygones:', nb_poly
         
        # Boucle sur les éléments en entrée
        inFeature = shp_ogr.GetNextFeature()
         
        # Comptage
        cnt = 1
        cnt_1 = 50000
        # Initialisation de la condition pour extraire les point voulus
        cnt5 = 0
         
        # Remplissage du shp
        while inFeature:
         
            # Extrait la géométrie en entrée
            geom = inFeature.GetGeometryRef()
             
            # Vérifie que le point est dans le polygone
            for IRC in OrthoIRC:
                 
                # Récupère les coordonnées des 4 coins des images dans le nom de chaque ortho
                # Upper Left
                ULx = int(os.path.split(IRC)[1][8:12] + '000')
                ULy = int(os.path.split(IRC)[1][13:17] + '000')
                 
                # Upper Right
                URx = ULx + 5000
                URy = ULy
                 
                # Down Right
                DRx = ULx + 5000
                DRy = ULy - 5000
                 
                # Down Left
                DLx = ULx
                DLy = ULy - 5000
                 
                # Initialisation des variables de type LineString
                # Left
                lineLt = ogr.Geometry(ogr.wkbLineString)
                lineLt.AddPoint(ULx, ULy)
                lineLt.AddPoint(DLx, DLy)
                # Right
                lineRt = ogr.Geometry(ogr.wkbLineString)
                lineRt.AddPoint(URx, URy)
                lineRt.AddPoint(DRx, DRy)
                # Upper
                lineUp = ogr.Geometry(ogr.wkbLineString)
                lineLt.AddPoint(ULx, ULy)
                lineUp.AddPoint(URx, URy)
                # Bottom
                lineBm = ogr.Geometry(ogr.wkbLineString)
                lineBm.AddPoint(DLx, DLy)
                lineRt.AddPoint(DRx, DRy)
                 
                # SI le segment intersect le polygone
                if geom.Intersect(lineLt) or geom.Intersect(lineRt) or geom.Intersect(lineUp) or geom.Intersect(lineBm) :
                    Select_OrthoIRC.append(IRC)
             
            # Détruit les polygones
            inFeature.Destroy()
             
            # incremente inFeature pour parcourir le shp
            inFeature = shp_ogr.GetNextFeature()
         
            # Comptage de l'affichage (Affichage toutes les 10 000 itérations)
            cnt_terminal_if = cnt - 50000
            if cnt_terminal_if == 0:
                print cnt_1
                cnt_1 = 50000 + cnt_1
                cnt = 0
            cnt = cnt + 1
         
        ## Ferme les données sources
        dataSource.Destroy()
         
        ##########################################
        ## Méthode de Mosaique d'images
        ##########################################
         
        #Construction du fichier VRT qui dispose de toutes les données img necessaire
        ProcessToCall = []
         
        # Nom du fichier de sortie
        VrtIRC = FolderOut + '/' + os.path.split(Zone)[1][:-4] + '_IRCOrtho.VRT'
         
        print 'Construction du VRT pour la mosaique'
        if os.path.exists(VrtIRC):
            os.remove(VrtIRC)
        ProcessToCall = ['gdalbuildvrt', '-srcnodata', '-10000', VrtIRC]
         
        a = 1   
        # Copie des rasters
        for CpImage in Select_OrthoIRC:
            print 'Conversion des IRC :'
            print '----> ' + str(a) + ' / ' + str(len(Select_OrthoIRC))
            # Convertir les images ECW en TIF
            Tif_Intem = CpImage[:-3]+'VRT'
            if os.path.exists(Tif_Intem):
                os.remove(Tif_Intem)
            subprocess.call(['gdal_translate', '-of', 'VRT', '-co', 'TILED=YES', CpImage, Tif_Intem ])
            # Reprojet l'image en RGF93
            Tif_IRC = Tif_Intem[:-4]+'_.VRT'
            if os.path.exists(Tif_IRC):
                os.remove(Tif_IRC)
            subprocess.call(['gdalwarp', '-t_srs', 'EPSG:2154', '-of', 'VRT', Tif_Intem, Tif_IRC])
            # Supprime les images intermédiaires Tif_Interm
        #    os.remove(Tif_Intem)
             
            ProcessToCall.append(Tif_IRC)
            a = a +1
             
        # Lancement du processus gdalbuildvrt
        subprocess.call(ProcessToCall)
         
        # A partir du VRT, on crée la nouvelle image
        ProcessToCall = []
         
         # Nom de l'image mosaïquée de sortie
        MosIRC = VrtIRC[:-4] + '_2m.VRT'
         
        print 'Création de la mosaïque !!!'
        # Lancement de la mosaïque
        ProcessToCall = ['gdal_translate', '-of', 'VRT', '-a_nodata', '-10000', VrtIRC, MosIRC]
        subprocess.call(ProcessToCall)
         
        # Lancement du réechantillonnage de l'image (dégradation à 2m)
        ImgOut = MosIRC[:-3] + 'TIF'
        PxlOut = 2 # Taille du pxl en sortie en metre
         
        print 'Dégradation du raster en sortie à '+ str(PxlOut) +'m !!!'
        ProcessToCall = ['gdalwarp', '-of', 'GTiff', '-tr',str(PxlOut) , str(PxlOut), '-rc', VrtIRC, ImgOut]
        subprocess.call(ProcessToCall)
         
        endTime = time.time() # Tps : Terminé
        print '...........' + ' Outputted to File in ' + str(endTime - startTime) + ' secondes'
        print "Soit, ",time.strftime('%H:%M:%S', time.gmtime(endTime - startTime))

    else:
        print usage
        sys.exit(1)
