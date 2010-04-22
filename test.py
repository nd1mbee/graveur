#!/usr/bin/python
# -*- coding: utf-8 -*-
import pygtk
pygtk.require("2.0")
import time
import gtk
import gtk.glade
import os
import thread
import threading
from subprocess import *
from config import *


gtk.gdk.threads_init() 
#----------------------------------------------------------------------
class LB:
	_isoList = []  # la liste des images trouvées
	selectedDist = ''  # variable contenant l'index de l'image selectionnée dans la liste 
	
	def __init__(self):
		"""Charge le fichier glade qui contient la 'maquette', associe les signaux définis dans la maquette aux méthodes de la classe"""
		self.Fenetre = gtk.glade.XML(GLADE_FILE, "lb")
		#self.Fenetre.set_default_size()
		self.distInfo = self.Fenetre.get_widget("distInfo")
		self.isoList = self.Fenetre.get_widget("isoList")
		self.button_graver = self.Fenetre.get_widget("graver")
		self.progression = self.Fenetre.get_widget("progression")
		self.entete = self.Fenetre.get_widget("entete")
		dic={"on_lb_destroy":self.fermer,"on_annuler_clicked":self.ouvrirCdrom,"on_isoList_unselect_row":self.desactiverButton,"on_isoList_select_row":self.getDistInfo,"on_graver_clicked":self.graver}
		self.Fenetre.signal_autoconnect(dic)
		welcomeText = open(WELCOME_TEXT_FILE,"r")
		self.entete.set_label(welcomeText.read())
		self.getDistrosList()
		
		gtk.main()
		
		
	def ouvrirCdrom(self):
		"""methode d'ouverture/fermeture du CDRom"""
		p = Popen("eject "+CDRW_DEVICE,shell=True,stdout=None)
		
	def desactiverButton(self,gtkCList,index,col,gdkEvent):
		"""désactive le button """
		self.button_graver.set_sensitive(False)
	
	def getFileTitle(self,fichierDesc):
		"""verifie s'il existe un fichier de description pour l'image donnée, si oui, renvoie la premiere ligne en tant que "titre" de l'image
		sinon, renvoie de le nom de l'image"""
		try:
			fichier=open(fichierDesc+INFO_FILE_EXT)
		except IOError:
			return os.path.basename(fichierDesc)
		else:
			return "%s"%fichier.readline()[:-1]
	
	def getDistrosList(self) :
		"""parcours le répértoire des images .iso et les ajoute dans la liste graphique"""
		os.chdir(ISO_DIR)
		for root, dirs, files in os.walk(os.getcwd()):
			for file in sorted(files):
				if file.endswith('.iso'):
					file = os.path.join(root,file)
					self._isoList.append(file)
					filesize = os.path.getsize(file)/(1024*1024)
					isoImage = self.getFileTitle(file)
					self.isoList.append(["%s" % isoImage + " (%s" %filesize + " Mo)"])						
	
	
	def getDistInfo(self,gtkCList,index,col,gdkEvent):
		""" affiche les informations détaillés sur la distribution
		     ouvre le fichier contenant la description de la distribution et l'affiche dans la zone d'information(le label à droite)"""
		self.selectedDist = index
		try:
			infoFile = open(self._isoList[index] + INFO_FILE_EXT,"r")
			self.distInfo.set_label("<b>"+infoFile.readline()+"</b>"+infoFile.read())
		except: 
			self.distInfo.set_label("<b>Pas de description disponible!</b>")
		self.button_graver.set_sensitive(True)

	def graver(self,donnees):
		if self.button_graver.get_label() == "Ouvrir CD-Rom" :
			self.ouvrirCdrom()
			self.button_graver.set_label("Graver")
		else:
			"""démarre la gravure dans un thread"""
			thread.start_new_thread(self.graverDist,()) 


	def graverDist(self):
		distTitle = self.getFileTitle(self._isoList[self.selectedDist])
		self.button_graver.set_sensitive(False)
		progressMessage = "Gravure de "+ distTitle +" en cours"
		self.progression.set_text(progressMessage+"...")
		self.button_graver.hide()
		burn_process  = Popen(["wodim dev="+CDRW_DEVICE+" -eject speed=%s -s -tao -vv  %s"%(WRITE_SPEED,self._isoList[self.selectedDist])],stdout=None,stderr=PIPE,stdin=None,shell=True)
		# process = Popen(["tail -f -n 1 --pid=%s"%subprocess.pid], stdin=subprocess.stdout, stdout=PIPE, shell=True)
		time.sleep(TIMEOUT)	
		#for i in range(1,200):
		while True:
			self.progression.set_pulse_step(0.1)
			self.progression.pulse()
			time.sleep(0.13)
			if burn_process.poll()==0 or burn_process.poll() == 255:
				break
		self.progression.set_fraction(1.0)
		#self.progression.set_text(WODIM_MESSAGES[burn_process.stderr.readlines()[-1][:-1]])
		self.progression.set_text(burn_process.stderr.readlines()[-1][:-1])
		self.reinit()
		
	def reinit(self):
		""" reinitialise l'application(ferme cdrom, désactive le bouton, déselectionne un item sélectioné précedemment dans la liste) """
		time.sleep(TIMEOUT)
		self.selectedDist =''
		p = Popen("eject -t "+CDRW_DEVICE,shell=True,stdout=None)
		self.isoList.unselect_all()
		self.progression.set_text("Veuillez sélectionner une image à graver")
		self.progression.set_fraction(0)
		self.button_graver.set_sensitive(False)
		self.button_graver.set_label("Ouvrir CD-Rom")
		self.button_graver.show()
		
	def fermer(self,widget,donnees=None):
		gtk.main_quit()
#----------------------------------------------------------------------
if __name__=='__main__':
    app=LB()
