# -*- coding: utf-8 -*-
"""
/***************************************************************************
 icgcPSI
                                 A QGIS plugin
 Plugin para el ICGC
                              -------------------
        begin                : 2017-12-12
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Sergio Illera
        email                : sergiollera22@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication,QDate, Qt, QUrl
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QMessageBox
from PyQt4.QtSql import *
from qgis.core import *
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from icgcPSI_dialog import icgcPSIDialog
import os
import csv
from psi_config import params, filezone
import time

class icgcPSI:
    """QGIS Plugin Implementation."""

    """ GLOBAL VARIABLES INSIDE THE CLASS"""
    Flagprocessat=False
    Flagcampaing=True
    conectardb={}

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'icgcPSI_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&icgcPSI')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'icgcPSI')
        self.toolbar.setObjectName(u'icgcPSI')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('icgcPSI', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.fv

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = icgcPSIDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/icgcPSI/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'icgc PSI plugin'),
            callback=self.run,
            parent=self.iface.mainWindow())
       
        #tab 1 buttons-----------------------------------------------------------
        self.dlg.pBloaddoc.clicked.connect(self.write_to_documentcitation)
        self.dlg.pBloadgeocol.clicked.connect(self.write_to_geocol)
        self.dlg.pBloadcamp.clicked.connect(self.write_to_campaing) #new campaign
        
        self.dlg.campedit.clicked.connect(self.show_campdata) #campaing edit button
        self.dlg.docedit.clicked.connect(self.show_docdata) #doc edit button
        self.dlg.geocoledit.clicked.connect(self.show_geocoldata)
        
            #tab1 checkbuttons
        self.dlg.cBcampanya.stateChanged.connect(self.show_campbutton) #funcion asociada al checkbox campaigns             
        self.dlg.cBdocumentacio.stateChanged.connect(self.show_docbutton) #funcion asociada al checkbox documentacio
        self.dlg.cBgeocol.stateChanged.connect(self.show_geocolbutton) #funcion asociada al checkbox de projecte
        #--------------------------------------------------------------------------        
        
        #tab2 buttons----------------------------------------------------------------------
        self.dlg.pBloadcsvprocessat.clicked.connect(self.load_csvprocessat) #buscar archivo procesat
        self.dlg.pBloadcsv.clicked.connect(self.cargar_foldercsvdades) #buscar la carpeta de archivos csv
        self.dlg.pBloadprocessat.clicked.connect(self.write_to_processat) #escribir en la tabla processat
        self.dlg.pBcarregardades.clicked.connect(self.carregar_dades) #iniciar carga de datos 
        self.dlg.editgeoset.clicked.connect(self.show_geoset_data)
        self.dlg.modgeoset.clicked.connect(self.mod_geoset)
            #tab2 checkbuttons hide the edit-modify button
        self.dlg.cBdades.stateChanged.connect(self.hide_geosetedit)
        self.dlg.cBdadespart.stateChanged.connect(self.hide_geosetedit)
        self.dlg.cBdadespart.stateChanged.connect(self.show_processbut)
            #tab2 dades campaing combobox
        self.dlg.CBdadescamp.currentIndexChanged.connect(self.show_geoset)
        
        #----------------------------------------------------------------------------------
        
        #tab3 buttons-----------------------------------------------------------------------
        self.dlg.QPBcampinfo.clicked.connect(self.show_campaign_info)
        self.dlg.pBdeleteobs.clicked.connect(self.delete_observationname)
        #self.dlg.QPBobsinfo.clicked.connect(self.show_obsinfo)
        self.dlg.QPBcampdelete.clicked.connect(self.delete_campaign)
            #tab3 campaign combobox
        self.dlg.campainglist.currentIndexChanged.connect(self.show_geoset_tabIII)
        #-----------------------------------------------------------------------------------
        
        #tab4 buttons------------------------------------------------------------------------
        self.dlg.pBloadshp.clicked.connect(self.cargar_csv)
        self.dlg.pBcarregar.clicked.connect(self.carregarpunts)
        #------------------------------------------------------------------------------------
        
    
    
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&icgcPSI'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        
        ###SET VISIBLE OR NOT SOME LABELS INITIALLY++++++++++++++++++++++++++++++++++++++
        #tab1------------------------------------------------------------
        self.dlg.dateEdit.setDate(QDate.currentDate()) #current date in doc calendar
        self.dlg.datepojectinit.setDate(QDate.currentDate()) #current date in inici project
        self.dlg.datepojectfin.setDate(QDate.currentDate()) #current date in end project
        self.dlg.pBloaddoc.setText('Modificar') #doccitation button
        self.dlg.pBloadgeocol.setText('Modificar') #projecte (geocol) button
        self.dlg.pBloadcamp.setText('Modificar') #campaign button
        #----------------------------------------------------------------
        
        #tab2------------------------------------------------------------
        self.dlg.pathcsvprocessat.clear()
        self.dlg.lEloadpath.clear() #clear the label text box (load shp path)
        self.dlg.modgeoset.setVisible(False)
        self.dlg.modgeoset.setEnabled(False)
        self.dlg.pBloadprocessat.setVisible(False)
        self.dlg.pBloadprocessat.setEnabled(False)
        #----------------------------------------------------------------
        
        #tab3------------------------------------------------------------
        self.dlg.campainglist.clear() #clear campaing combobox 
        self.dlg.CBdadescamp.clear()
        #----------------------------------------------------------------
        
        #tab4------------------------------------------------------------
        #----------------------------------------------------------------
        
        #conexion to DB  (only once when the GUI is created)
        self.conectardb = self.connecttobd() 
        
        #POPULATE INITIALLY THE COMBOBOXS
        #tab1------------------------------------------------------------
        self.show_bd_doccitation() #show table I documentation combobox
        self.show_bd_geocol() #show table I prOyecte combobox (geocolection)
        self.show_bd_campaigns() #show campaigns name combobox (in all tables)
        self.show_void() #show table I projecte void
        #----------------------------------------------------------------

        #tab2------------------------------------------------------------
        self.show_all_geoset() #show list of geosets of all campaings
        #----------------------------------------------------------------
        
        #tab3------------------------------------------------------------
        #self.show_bd_campaigns() #called in tab I
        #----------------------------------------------------------------
        
        #tab4------------------------------------------------------------
        #----------------------------------------------------------------
        
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass


#####ERROR MISSAGE FUNCTION++++++++++++++++++++++++++++++++++++++++++++++++++++
    def Missatge(self,t,title="Error"): #error missatge function
            m = QMessageBox()
            if title!='Error':
                m.setIcon(QMessageBox.Information)
            else:
                m.setIcon(QMessageBox.Warning)
            m.setWindowTitle(title)
            m.setText(t)
            m.setStandardButtons(QMessageBox.Ok);
            m.setButtonText(QMessageBox.Ok,"Segueix")
            m.exec_() 
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


###################  READING FUNCTIONS ##############################        
    def cargar_foldercsvdades(self):
        #choose directory path
        self.dlg.lEloadpath.clear()
        path_dir=QFileDialog().getExistingDirectory(
            self.dlg,
            'Open folder',
            'C:\Users')
        self.dlg.lEloadpath.setText(path_dir)
        
    
    def load_csvprocessat(self): #get path processat folder 
        self.dlg.pathcsvprocessat.clear()
        path_dir=QFileDialog().getExistingDirectory(
            self.dlg,
            'Open folder',
            'C:\Users')
        self.dlg.pathcsvprocessat.setText(path_dir)
            
    
#------------------------------------------------------------------------------

#########FUNCTIONS DATA BASE INTERFACE+++++++++++++++++++++++++++++++++++++++++

    def connecttobd(self):#connect to the bd
        db = QSqlDatabase.addDatabase(params[0]) 
        db.setHostName(params[1]) 
        db.setDatabaseName(params[2])
        db.setPort(params[3]) 
        db.setUserName(params[4]) 
        db.setPassword(params[5]) 
        db.open()
        if db.isOpen(): 
            #print 'Abieto sql'
            self.Missatge(self.tr(u'Conectat a la base de dades\nBase de dades: {} '.format(params[2])),'Informacio')
        else:
            #print 'Error al abrir sql'
            db.close()
            self.Missatge(self.tr(u"Error al conectar a la base de dades!\n")+db.lastError().text())
        return db
        

    def obtain_max_id(self,query,tabla,nombreid):
        lastid=0
        if query.exec_('SELECT {0} FROM {1} ORDER BY {0} DESC limit 1'.format(nombreid,tabla))==0:
            self.Missatge(self.tr(u"Error al consultar\n")+query.lastError().text())
            return
        else:
            while query.next():
                lastid = query.value(0)
        return lastid 
        
    
    def isinbd(self,query,tabla,campo,valor,campoid):
        exist=False #flag if exist
        ide=0
        if query.exec_('SELECT {0} FROM {1} WHERE {2}=\'{3}\';'.format(campoid,tabla,campo,valor))==0:
            self.Missatge(self.tr(u"Error al consultar\n")+query.lastError().text())
        else:
            exist=False
            while query.next():
                exist=True
                ide= query.value(0)
            return exist,ide
            
    def fromidtovoid(self,query,ide):
        if query.exec_('SELECT voidtypevalue FROM cl_voidtypevalue WHERE voidtypevalueid={};'.format(ide))==0:
            self.Missatge(self.tr(u"Error al consultar voidtypevalue des de id\n")+query.lastError().text())
            error=True
            return error,[]
        else:
            while query.next():
                void= query.value(0)
            error=False
            return error,void
            
    def fromidtodocument(self,query,ide):
        if query.exec_('SELECT name FROM documentcitation WHERE documentcitationid={};'.format(ide))==0:
            self.Missatge(self.tr(u"Error al consultar documentcitation des de id\n")+query.lastError().text())
            error=True
            return error,[]
        else:
            while query.next():
                void= query.value(0)
            error=False
            return error,void
        
      
#---------------------------------------------------------------------------------------
        
# POPULATE COMBOBOX FUNCTIONS+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def show_bd_doccitation(self):
        '''
        Docstring: mostremos en la comboBox de la tabla I el campo short name de todos los registros
        de la tabla document citation
        '''
        #show all doccitation in the combobox
        
        db = self.conectardb 
        query = QSqlQuery(db)
        if query.exec_('SELECT DISTINCT ON (name) name FROM documentcitation;')==0:
            self.Missatge(self.tr(u"Error:{}\n".format(query.lastError().text())))
        docs=[]
        docs.append('')
        while query.next():
            docs.append(query.value(0).encode('utf-8','ignore'))
        self.dlg.CBshortnamedoccit.clear()   
        self.dlg.CBshortnamedoccit.addItems(docs)
        self.dlg.CBsprojdoccit.clear()
        self.dlg.CBsprojdoccit.addItems(docs)
        self.dlg.CBdoccitdades.clear()
        self.dlg.CBdoccitdades.addItems(docs)
        self.dlg.CBdistnfo.clear()
        self.dlg.CBdistnfo.addItems(docs)
        
        
    def show_bd_geocol(self):
        '''
        Docstring: mostremos en el combobox de la tabla I en la zona de poyectos la lista de proyectos
        ya existentes en la tabla geocolection
        '''
        db = self.conectardb 
        query = QSqlQuery(db)
        if query.exec_('SELECT DISTINCT ON (name) name FROM geologiccollection;')==0:
            self.Missatge(self.tr(u"Error:{}\n".format(query.lastError().text())))
        geocol=[]
        geocol.append('')
        while query.next():
            geocol.append(str(query.value(0)).encode('utf-8','ignore'))
        self.dlg.CBgeocol.clear()
        self.dlg.CBgeocol.addItems(geocol)
        self.dlg.CBgeocoldades.clear()
        self.dlg.CBgeocoldades.addItems(geocol)
        
        
    def show_bd_campaigns(self):
        '''
        Docstring:  mostremos en el combobox de la tabla I en la zona de campañas la lista de campañas
        ya existentes en la tabla campaign
        '''
        db = self.conectardb 
        query = QSqlQuery(db)
        if query.exec_('SELECT name FROM campaign;')==0:
           self.Missatge(self.tr(u"Error:{}\n".format(query.lastError().text())))
        campaings=[]
        campaings.append('')
        while query.next():
            campaings.append(str(query.value(0)).encode('utf-8','ignore'))
        self.dlg.CBcamp.clear()
        self.dlg.CBcamp.addItems(campaings)
        self.dlg.CBcampdades.clear()
        self.dlg.CBcampdades.addItems(campaings)
        self.dlg.campainglist.clear()
        self.dlg.campainglist.addItems(campaings)
        self.dlg.CBdadescamp.clear()
        self.dlg.CBdadescamp.addItems(campaings)
        
        
    def show_void(self):
        '''
        Docstring: mostremos los voids en los comboboxs
        '''
        db = self.conectardb 
        query = QSqlQuery(db)
        if query.exec_('SELECT DISTINCT ON (voidtypevalue) voidtypevalue FROM cl_voidtypevalue;')==0:
            self.Missatge(self.tr(u"Error:{}\n".format(query.lastError().text())))
        voids=[]
        voids.append('')
        while query.next():
            voids.append(str(query.value(0)))
        self.dlg.CBprojecvoid.clear()
        self.dlg.CBprojecvoid.addItems(voids) #table I,projecte void
        self.dlg.CBprojecvoid2.clear()
        self.dlg.CBprojecvoid2.addItems(voids) #table I,projecte void
        self.dlg.CBclient_void.clear()
        self.dlg.CBclient_void.addItems(voids) #table I, campign client void
        self.dlg.CBcontractor_void.clear()
        self.dlg.CBcontractor_void.addItems(voids) #table I, contractor client void
        self.dlg.CBinformevoid.clear()
        self.dlg.CBinformevoid.addItems(voids)
        self.dlg.CBlargework_void.clear()
        self.dlg.CBlargework_void.addItems(voids) #tble II largework_void (codi projecte)
        self.dlg.CBdistnfo_void.clear()
        self.dlg.CBdistnfo_void.addItems(voids) #tble II metadates_void 
        
    
    def show_geoset(self):
        if self.dlg.CBdadescamp.currentText()==None or self.dlg.CBdadescamp.currentText()=='':  
            self.dlg.CBdadesgeoset.clear()
            pass
        else:
            #si la campaña existe, buscar los geosets asociados a ella
            db = self.conectardb 
            query = QSqlQuery(db)
            
            #buscar la campaña id
            error,idcamp=self.isinbd(query,'campaign','name',self.dlg.CBdadescamp.currentText(),'campaignid') 
            if error==0:
                self.Missatge(self.tr(u"Error buscant la ID de la campanya: {}".format(self.dlg.CBdadescamp.currentText())))
                return
            
            if query.exec_('SELECT DISTINCT ON (InspireId) InspireId FROM geophobjectset WHERE geophobjectset.campaign={};'.format(idcamp))==0:
                self.Missatge(self.tr(u"Error:{}\n".format(query.lastError().text())))
            geosets=[]
            while query.next():
                geosets.append(str(query.value(0)).encode('utf-8','ignore'))
            self.dlg.CBdadesgeoset.clear()
            self.dlg.CBdadesgeoset.addItems(geosets) #table II, list of processats
            
    def show_geoset_tabIII(self):
        if self.dlg.campainglist.currentText()==None or self.dlg.campainglist.currentText()=='':  
            self.dlg.dadeslist.clear()
            pass
        else:
            #si la campaña existe, buscar los geosets asociados a ella
            db = self.conectardb 
            query = QSqlQuery(db)
            
            #buscar la campaña id
            error,idcamp=self.isinbd(query,'campaign','name',self.dlg.campainglist.currentText(),'campaignid') 
            if error==0:
                self.Missatge(self.tr(u"Error buscant la ID de la campanya: {}".format(self.dlg.CBdadescamp.currentText())))
                return
            
            if query.exec_('SELECT DISTINCT ON (InspireId) InspireId FROM geophobjectset WHERE geophobjectset.campaign={};'.format(idcamp))==0:
                self.Missatge(self.tr(u"Error:{}\n".format(query.lastError().text())))
            geosets=[]
            while query.next():
                geosets.append(str(query.value(0)).encode('utf-8','ignore'))
            self.dlg.dadeslist.clear()
            self.dlg.dadeslist.addItems(geosets) #table II, list of processats    
    
            
    def show_all_geoset(self):
        self.dlg.CBgeosetshow.clear()
        db = self.conectardb 
        query = QSqlQuery(db)
        if query.exec_('SELECT inspireid FROM geophobjectset;')==0:
            self.Missatge(self.tr(u"Error:{}\n".format(query.lastError().text())))
        geosets=[]
        geosets.append('')
        while query.next():
            geosets.append(str(query.value(0)).encode('utf-8','ignore'))
        self.dlg.CBgeosetshow.addItems(geosets)
#-----------------------------------------------------------------------------------    

# ++++++++++++++++++++++++++ SHOW HIDDEN BUTTONS +++++++++++++++++++++++++++++++++++

    def show_geocolbutton(self):
        if self.dlg.cBgeocol.isChecked():
            self.dlg.pBloadgeocol.setText('Carregar')
            self.dlg.geocoledit.setVisible(False)
            self.dlg.geocoledit.setEnabled(False) 
        else:
            self.dlg.pBloadgeocol.setText('Modificar')
            self.dlg.geocoledit.setVisible(True) 
            self.dlg.geocoledit.setEnabled(True) 

    def show_docbutton(self):
        if self.dlg.cBdocumentacio.isChecked():
            self.dlg.pBloaddoc.setText('Carregar')
            self.dlg.docedit.setVisible(False) 
            self.dlg.docedit.setEnabled(False) 
        else:
            self.dlg.pBloaddoc.setText('Modificar')
            self.dlg.docedit.setVisible(True) 
            self.dlg.docedit.setEnabled(True) 
            
    def show_campbutton(self):
        if self.dlg.cBcampanya.isChecked():
            self.dlg.pBloadcamp.setText('Carregar') 
            self.dlg.campedit.setVisible(False)
            self.dlg.campedit.setEnabled(False)
        else:
            self.dlg.pBloadcamp.setText('Modificar')
            self.dlg.campedit.setVisible(True)
            self.dlg.campedit.setEnabled(True)
            
    def hide_geosetedit(self):
        if self.dlg.cBdades.isChecked() or self.dlg.cBdadespart.isChecked():
            self.dlg.editgeoset.setVisible(False)
            self.dlg.modgeoset.setVisible(False)
            self.dlg.editgeoset.setEnabled(False)
            self.dlg.modgeoset.setEnabled(False)
        else:
            self.dlg.editgeoset.setVisible(True)
            self.dlg.editgeoset.setEnabled(True)
    
    def show_processbut(self):
        if self.dlg.cBdadespart.isChecked():
            self.dlg.pBloadprocessat.setVisible(True)
            self.dlg.pBloadprocessat.setEnabled(True)
        else:
            self.dlg.pBloadprocessat.setVisible(False)
            self.dlg.pBloadprocessat.setEnabled(False)

#----------------------------------------------------------------------------------
        
# ++++++++++++++++++++++++++  TABLE I FUNCTIONS +++++++++++++++++++++++++++++++++++

    def show_geocoldata(self):
        '''
        Docstring: mostrar en los labels correspondientes de la primera pestaña los datos asociados
        a la tabla geologiccollection para poderla modificar
        '''
        db = self.conectardb 
        query = QSqlQuery(db)        
        
        #set to 0 some combobox
        self.dlg.CBsprojdoccit.setCurrentIndex(0)
        self.dlg.CBinformevoid.setCurrentIndex(0) 
        self.dlg.CBprojecvoid.setCurrentIndex(0) 
        
        name=self.dlg.CBgeocol.currentText()
        datos={}
        campos='inspireid,reference,reference_void,beginlifespanversion,beginlifespanversion_void,endlifespanversion,endlifespanversion_void'
        if query.exec_('SELECT ({}) FROM geologiccollection WHERE geologiccollection.name=\'{}\';'.format(campos,name))==0:
            self.Missatge(self.tr(u"Error al buscar informacio de la geologiccollection\n")+query.lastError().text())
            return
        while query.next():
            datos=query.value(0)
        if datos=={}:
            return
        datos=datos.replace('(','')
        datos=datos.replace(')','')
        datos=datos.split(',')
        
        #populate the labels
        self.dlg.QLEprojectcodi.clear()
        self.dlg.QLEprojectcodi.setText(datos[0]) #inspire id (codi projecte)
        self.dlg.QLEprojectname.clear()
        self.dlg.QLEprojectname.setText(name) #name (nombre projecte)
        
        #documentacion        
        if datos[1]=='': #no documentacion asociada
            self.dlg.CBsprojdoccit.setCurrentIndex(0) #la documentacion a 0
            error,void_doc=self.fromidtovoid(query,datos[2]) #nodumentation void
            if error:
                self.Missatge(self.tr(u"Error a la id nodocument geocollection\n"))
                return
            self.dlg.CBinformevoid.setCurrentIndex(self.dlg.CBinformevoid.findText(void_doc))
            
        else: #existe documentacion asociada
            self.dlg.CBsprojdoccit.setCurrentIndex(0) #el void a 0
            error,docu=self.fromidtodocument(query,datos[1])
            if error:
                self.Missatge(self.tr(u"Error a la id documentacio geocollection\n"))
                return
            self.dlg.CBsprojdoccit.setCurrentIndex(self.dlg.CBsprojdoccit.findText(docu))   
        
        #begin life date
        if datos[3]=='': #no init date
            self.dlg.datepojectinit.setDate(QDate.currentDate())
            error,void_initdate=self.fromidtovoid(query,datos[4]) #initdate_void
            if error:
                self.Missatge(self.tr(u"Error a la id initdate geocollection\n"))
                return
            self.dlg.CBprojecvoid2.setCurrentIndex(self.dlg.CBprojecvoid2.findText(void_initdate))
        else: #existe init date
            year=int(datos[3].split('-') [0])
            month=int(datos[3].split('-') [1])
            day=int(datos[3].split('-') [2])
            self.dlg.datepojectinit.setDate(QDate(year,month,day)) #DD
            self.dlg.CBprojecvoid2.setCurrentIndex(0)
        
        #end life date
        if datos[5]=='': #no end date
            self.dlg.datepojectfin.setDate(QDate.currentDate())
            error,void_enddate=self.fromidtovoid(query,datos[6]) #enddate_void
            if error:
                self.Missatge(self.tr(u"Error a la id enddate geocollection\n"))
                return
            self.dlg.CBprojecvoid.setCurrentIndex(self.dlg.CBprojecvoid.findText(void_enddate))
        else: #existe end date
            year=int(datos[5].split('-') [0])
            month=int(datos[5].split('-') [1])
            day=int(datos[5].split('-') [2])
            self.dlg.datepojectfin.setDate(QDate(year,month,day))
            self.dlg.CBprojecvoid.setCurrentIndex(0)
             

    def show_docdata(self):
        '''
        Docstring: mostrar en los labels correspondientes de la primera pestaña los datos asociados 
        a la documentacion seleccionada para poderla modificar
        '''
        db = self.conectardb 
        query = QSqlQuery(db)
        
        name=self.dlg.CBshortnamedoccit.currentText().encode('utf-8','ignore')
        
        datos={}
        campos='name,shortname,date,link'
        if query.exec_('SELECT ({}) FROM documentcitation WHERE documentcitation.name=\'{}\';'.format(campos,name))==0:
            self.Missatge(self.tr(u"Error al buscar informacio de la campanya\n")+query.lastError().text())
            return
        while query.next():
            datos=query.value(0)
        if datos=={}:
            return
        datos=datos.replace('(','')
        datos=datos.replace(')','')
        datos=datos.split(',')
        print datos
        #populate the labels
        self.dlg.QLEname.clear() #name
        self.dlg.QLEname.setText(str(datos[0].replace('"','')))
        self.dlg.QLEshortname.clear() #shortname
        self.dlg.QLEshortname.setText(str(datos[1].replace('"','')))
        self.dlg.QLElink.clear() #link
        self.dlg.QLElink.setText(str(datos[3].replace('"','')))
        #date label
        year=int(datos[2].split('-') [0])
        month=int(datos[2].split('-') [1])
        day=int(datos[2].split('-') [2])
        self.dlg.dateEdit.setDate(QDate(year,month,day))
        

    def show_campdata(self):
        '''
        Docstring: mostrar en los labels correspondientes de la primera pestaña los datos asociados
        a la campaña seleccionada para poderlos modificar
        '''
        db = self.conectardb 
        query = QSqlQuery(db)

        name=self.dlg.CBcamp.currentText().encode('utf-8','ignore')
        if name=='':
            self.Missatge(self.tr(u"Selecciona una campanya"))
            return            
            
        datos={}
        campos='name,client,client_void,contractor,contractor_void'           
        if query.exec_('SELECT ({}) FROM campaign WHERE campaign.name=\'{}\';'.format(campos,name))==0:
            self.Missatge(self.tr(u"Error al buscar informacio de la campanya\n")+query.lastError().text())
            return
        while query.next():
            datos=query.value(0)
        if datos=={}:
            return
        datos=datos.replace('(','')
        datos=datos.replace(')','')
        datos=datos.split(',')
        
        #populate the labels
        self.dlg.QLEcampname.clear() #name
        self.dlg.QLEcampname.setText(datos[0].replace('"',''))
        self.dlg.QLEclient.clear() #client
        self.dlg.QLEclient.setText(datos[1].replace('"',''))
        self.dlg.QLEcontractor.clear() #contractor
        self.dlg.QLEcontractor.setText(datos[3].replace('"',''))
        #los voids
        if datos[2]!='':
            error,void_client=self.fromidtovoid(query,datos[2]) #client_void
            if error:
                self.Missatge(self.tr(u"Error a la id client\n"))
                return
            self.dlg.CBclient_void.setCurrentIndex(self.dlg.CBclient_void.findText(void_client))
        else:
            self.dlg.CBclient_void.setCurrentIndex(0)
        if datos[4]!='':
            error,void_contractor=self.fromidtovoid(query,datos[4]) #contractor_void
            if error:
                self.Missatge(self.tr(u"Error a la id contractant\n"))
                return
            self.dlg.CBcontractor_void.setCurrentIndex(self.dlg.CBcontractor_void.findText(void_contractor))
        else:
            self.dlg.CBcontractor_void.setCurrentIndex(0)
        
        
    def write_to_campaing(self):
        '''
        Docstring: escribir en la tabla campaign los datos de la gui
        Alterna la funcionalidad con modifcar una campaña ya existente en la base de datos dependiendo
        de si el combo box esta activo o no
        '''
        db = self.conectardb 
        query = QSqlQuery(db)
        
        tabla='campaign' 
        
        if self.dlg.cBcampanya.isChecked()==False: #edit camp
            exist,campaingid=self.isinbd(query,tabla,'name',self.dlg.CBcamp.currentText(),'campaignid')
            if exist==False:
                self.Missatge(self.tr(u"El nom de la acampanya no \nexisteix a la base de dades"))
                return 
                
        else: #new camp
            campaingid=self.obtain_max_id(query,tabla,'campaignid')+1 #id campaign                
            #check si el nombre esta repetido        
            name=self.dlg.QLEcampname.text() 
            for i in range(1,self.dlg.CBcamp.count()):
                if name == str(self.dlg.CBcamp.itemText(i)): #nombre repetido
                    self.Missatge(self.tr(u"El nom de la campanya ja existeix"))
                    return
                
        id_survey=18
        id_camptype=3
        
        client=self.dlg.QLEclient.text()
        if client=='':
            client=None
            void=self.dlg.CBclient_void.currentText() #get from the  campaign client combobox void text
            if void=='':
                self.Missatge(self.tr(u"El camp client esta buit. Indica el perque"))
                return
            exist,client_void = self.isinbd(query,'cl_voidtypevalue','voidtypevalue',void,'voidtypevalueid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el void ide"))
                return 
        else:
            client_void=None
        
        contractor=self.dlg.QLEcontractor.text()
        if contractor=='':
            contractor=None
            void=self.dlg.CBcontractor_void.currentText() #get from the  campaign contractor combobox void text
            if void=='':
                self.Missatge(self.tr(u"El camp contractant esta buit. Indica el perque"))
                return
            exist,contractor_void = self.isinbd(query,'cl_voidtypevalue','voidtypevalue',void,'voidtypevalueid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el void ide"))
                return 
        else:
            contractor_void=None
        
        campos='campaignid,surveytype,campaigntype,client,client_void,contractor,contractor_void,name'

        if self.dlg.cBcampanya.isChecked()==False: #edit camp
            name=self.dlg.QLEcampname.text()
            query.prepare('UPDATE {} SET client=:3,client_void=:4,contractor=:5,contractor_void=:6,name=:7 WHERE campaignid={};'.format(tabla,campaingid))
            query.bindValue(':3',client)
            query.bindValue(':4',client_void)
            query.bindValue(':5',contractor)
            query.bindValue(':6',contractor_void)
            query.bindValue(':7',name)
            
        else: #new camp
            query.prepare('INSERT INTO {} ({}) VALUES (:0,:1,:2,:3,:4,:5,:6,:7);'.format(tabla,campos)) 
            query.bindValue(':0',campaingid)
            query.bindValue(':1',id_survey)
            query.bindValue(':2',id_camptype)
            query.bindValue(':3',client)
            query.bindValue(':4',client_void)
            query.bindValue(':5',contractor)
            query.bindValue(':6',contractor_void)
            query.bindValue(':7',name)

        if query.exec_()==0:
            self.Missatge(self.tr(u"Error al actualitzar la taula {}\n".format(tabla))+query.lastError().text())
            return 
        else:
            if self.dlg.cBcampanya.isChecked()==False:
                self.Missatge(self.tr(u"Campanya editada\n"),'Informacio')
                self.dlg.CBcampdades.removeItem(self.dlg.CBcamp.findText(self.dlg.CBcamp.currentText()))
                self.dlg.campainglist.removeItem(self.dlg.CBcamp.findText(self.dlg.CBcamp.currentText()))
                self.dlg.CBdadescamp.removeItem(self.dlg.CBcamp.findText(self.dlg.CBcamp.currentText()))
                self.dlg.CBcamp.removeItem(self.dlg.CBcamp.findText(self.dlg.CBcamp.currentText()))
            else:
                self.Missatge(self.tr(u"Campanya carregada\n"),'Informacio') 
                
            self.dlg.CBcamp.addItems([name])
            self.dlg.CBcampdades.addItems([name])
            self.dlg.campainglist.addItems([name])
            self.dlg.CBdadescamp.addItems([name])
            self.dlg.QLEcampname.clear()
            self.dlg.QLEcontractor.clear()
            self.dlg.QLEclient.clear()


    def write_to_geocol(self):
        '''
        Docstring: escribir en la tabla geologiccolection los datos de la gui
        '''
        tabla='geologiccollection'
        db=self.conectardb     #create the connection and the Query        
        query = QSqlQuery(db)
        
        inspireid=self.dlg.QLEprojectcodi.text().encode('utf-8','ignore')
        name=self.dlg.QLEprojectname.text().encode('utf-8','ignore')       
        
        if self.dlg.cBgeocol.isChecked()==False: #edit geocol
            exist,geocolid=self.isinbd(query,tabla,'name',self.dlg.CBgeocol.currentText(),'geologiccollectionid')
            if exist==False:
                self.Missatge(self.tr(u"El nom de la geocollection no \nexisteix a la base de dades"))
                return 
        else:  #new geocol 
            #check si el nombre esta repetido         
            for i in range(1,self.dlg.CBgeocol.count()):
                if name == str(self.dlg.CBgeocol.itemText(i)): #nombre repetido
                    self.Missatge(self.tr(u"El nom del projecte ja existeix"))
                    return
            geocolid=self.obtain_max_id(query,tabla,'geologiccollectionid')+1
        
        
        #referencia (to doccitation)
        reference=self.dlg.CBsprojdoccit.currentText().encode('utf-8','ignore')
        if reference=='':
            if self.dlg.CBinformevoid.currentText()=='':
               self.Missatge(self.tr(u"El camp informe esta buit. Indica un motiu"))
               return
            else:
               reference=None
               exist,void_ide = self.isinbd(query,'cl_voidtypevalue','voidtypevalue',self.dlg.CBinformevoid.currentText(),'voidtypevalueid')
               if exist==0:
                   self.Missatge(self.tr(u"Error al buscar el void ide"))
                   return
        else:
            exist,ide=self.isinbd(query,'documentcitation','name',reference,'documentcitationid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar la documentcitation ide"))
                return
            reference=ide
            void_ide=None
        
        #fecha inicio
        if self.dlg.checkBoxprojectedate2.isChecked():
            fechainit=None
            void=self.dlg.CBprojecvoid2.currentText() #get from the  project combobox void text
            if void=='':
                self.Missatge(self.tr(u"Indica perque la data inicial esta buida"))
                return
            exist,ide = self.isinbd(query,'cl_voidtypevalue','voidtypevalue',void,'voidtypevalueid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el void ide"))
                return
            fechainit_void=ide
        else:
            fechainit=str(self.dlg.datepojectinit.date().year())+'-'       
            fechainit=fechainit+str(self.dlg.datepojectinit.date().month())+'-' 
            fechainit=fechainit+str(self.dlg.datepojectinit.date().day())
            fechainit_void=None
        
        #fecha fin
        if self.dlg.checkBoxprojectedate.isChecked():
            fechafin=None
            void=self.dlg.CBprojecvoid.currentText() #get from the  project combobox void text
            if void=='':
                self.Missatge(self.tr(u"Indica perque la data final esta buida"))
                return
            exist,ide = self.isinbd(query,'cl_voidtypevalue','voidtypevalue',void,'voidtypevalueid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el void ide"))
                return
            endlife_void=ide
        else:
            fechafin=str(self.dlg.datepojectfin.date().year())+'-'       
            fechafin=fechafin+str(self.dlg.datepojectfin.date().month())+'-' 
            fechafin=fechafin+str(self.dlg.datepojectfin.date().day())  
            endlife_void=None
        
        if name=='':
            self.Missatge(self.tr(u"El camp Nom del projecte no pot estar buit"))
            return
        
        
        campos='geologiccollectionid,inspireid,name,collectiontype,reference,reference_void,beginlifespanversion,beginlifespanversion_void,'
        campos+='endlifespanversion,endlifespanversion_void'
        
        if self.dlg.cBgeocol.isChecked()==False: #edit
            query.prepare('UPDATE {} SET inspireid=:1,name=:2,reference=:4,reference_void=:5,beginlifespanversion=:6,beginlifespanversion_void=:7,endlifespanversion=:8,endlifespanversion_void=:9 WHERE geologiccollectionid={};'.format(tabla,geocolid))
        else:        #new
            query.prepare('INSERT INTO {} ({}) VALUES (:0,:1,:2,:3,:4,:5,:6,:7,:8,:9);'.format(tabla,campos))
            
        query.bindValue(':0',geocolid)
        query.bindValue(':1',inspireid) #inspireid
        query.bindValue(':2',name) #name
        query.bindValue(':3',4) #collectiontype
        query.bindValue(':4',reference) #reference--> documentcitation id
        query.bindValue(':5',void_ide) #reference void
        query.bindValue(':6',fechainit) #beginlife
        query.bindValue(':7',fechainit_void) #beginlife_void
        query.bindValue(':8',fechafin) #endlife
        query.bindValue(':9',endlife_void) #endlife_void
        
        if query.exec_()==0:
            self.Missatge(self.tr(u"Error al actualitzar la taula {}\n".format(tabla))+query.lastError().text())
            return
        else:
            if self.dlg.cBgeocol.isChecked()==False: #edit
                self.Missatge(self.tr(u"Taula Geologiccolection modificada\n"),'Informacio') 
                self.dlg.CBgeocoldades.removeItem(self.dlg.CBgeocoldades.findText(self.dlg.CBgeocol.currentText())) #remove el combobox de projectes (tab II)
                self.dlg.CBgeocol.removeItem(self.dlg.CBgeocol.findText(self.dlg.CBgeocol.currentText())) #remove combobox geocol  
            else: #new
                self.Missatge(self.tr(u"Afegit registre a la taula Geologiccolection\n"),'Informacio')
                
            self.dlg.CBgeocol.addItems([name]) #actualizar el combobox de projectes
            self.dlg.CBgeocoldades.addItems([name]) #actualizar el combobox de projectes (tab II)
            self.dlg.QLEprojectcodi.clear() #limpiar
            self.dlg.QLEprojectname.clear()
        

    def write_to_documentcitation(self):
        '''
        Docstring: funcion que lee los campos de la GUI de la documentacion y
        lo guarda en la tabla documentcitation
        '''
        # 5 campos a escribir (4 por GUI + ID)      
        tabla='documentcitation'
        db=self.conectardb     #create the connection and the Query        
        query = QSqlQuery(db)
        
        if self.dlg.cBdocumentacio.isChecked()==False: #edit doccitation
            exist,ide=self.isinbd(query,tabla,'name',self.dlg.CBshortnamedoccit.currentText(),'documentcitationid')
            if exist==False:
                self.Missatge(self.tr(u"El nom de la documentacio no \nexisteix a la base de dades"))
                return 
            
        else: #new doccitation
            #check si el nombre ya existe
            name=self.dlg.QLEname.text()
            for i in range(1,self.dlg.CBshortnamedoccit.count()):
                if name == str(self.dlg.CBshortnamedoccit.itemText(i)): #nombre repetido
                    self.Missatge(self.tr(u"Documentacio amb aquest nom ja existeix"))
                    return
            ide = self.obtain_max_id(query,tabla,'documentcitationid') + 1 

        
        fecha=str(self.dlg.dateEdit.date().year())+'-'       
        fecha=fecha+str(self.dlg.dateEdit.date().month())+'-' 
        fecha=fecha+str(self.dlg.dateEdit.date().day())
        
        if (self.dlg.QLEname.text() or self.dlg.QLEshortname.text()) =='': 
            self.Missatge(self.tr(u"Els camps informe del projecte o codi estan buits"))
            return
        
        if self.dlg.cBdocumentacio.isChecked()==False: #edit doccitation
            name=self.dlg.QLEname.text()
            query.prepare('UPDATE {} SET name=:2,shortname=:3,date=:4,link=:5 WHERE documentcitationid={};'.format(tabla,ide))
            query.bindValue(':2',name) #name
            query.bindValue(':3',self.dlg.QLEshortname.text()) #shortname
            query.bindValue(':4',fecha) #date
            query.bindValue(':5',self.dlg.QLElink.text()) #link

        else: #new doccitation
            campos='documentcitationid,name,shortname,date,link'
            query.prepare('INSERT INTO {} ({}) VALUES (:0,:1,:2,:3,:4);'.format(tabla,campos)) 
            query.bindValue(':0',ide)
            query.bindValue(':1',name) #doc name
            query.bindValue(':2',self.dlg.QLEshortname.text()) #doc short name
            query.bindValue(':3',fecha) # doc date
            query.bindValue(':4',str(self.dlg.QLElink.text())) # doc link
            
        if query.exec_()==0:
            self.Missatge(self.tr(u"Error al actualitzar la taula {}\n".format(tabla))+query.lastError().text())
            return
        else:
            if self.dlg.cBdocumentacio.isChecked()==False: #edit case
                self.Missatge(self.tr(u"Documentacio modificada!\n"),'Informacio')
                self.dlg.CBsprojdoccit.removeItem(self.dlg.CBsprojdoccit.findText(self.dlg.CBshortnamedoccit.currentText())) #update combobox proyecte
                self.dlg.CBdoccitdades.removeItem(self.dlg.CBdoccitdades.findText(self.dlg.CBshortnamedoccit.currentText())) #update comobox doccittion tab II
                self.dlg.CBshortnamedoccit.removeItem(self.dlg.CBshortnamedoccit.findText(self.dlg.CBshortnamedoccit.currentText())) #update combobox documentacio
                self.dlg.CBdistnfo.removeItem(self.dlg.CBshortnamedoccit.findText(self.dlg.CBshortnamedoccit.currentText())) #update codi informe metaddates
            else:
                self.Missatge(self.tr(u"Documentacio carregada!\n"),'Informacio')  
            self.dlg.CBshortnamedoccit.addItems([name]) #update combobox documentacio
            self.dlg.CBsprojdoccit.addItems([name]) #update combobox proyecte
            self.dlg.CBdoccitdades.addItems([name]) #update comobox doccittion tab II
            self.dlg.CBdistnfo.addItems([name]) #update codi informe metaddates
            self.dlg.QLEname.clear()
            self.dlg.QLEshortname.clear()
            self.dlg.QLElink.clear()
            

# +++++++++++++++++++++++++++  TABLE II FUNCTIONS +++++++++++++++++++++++++++++++++
    def write_to_processat(self):
        '''
        Docstring: funcion que escribe a la tabla processes los datos almacenados en 
        la variable self.processat. Esta variable ha sido leida del archivo csv antes.
        No se mira que los datos sean correctos ni que esten o no repetidos
        Se escribe en la fila con la siguiente id (current id + 1)
        '''        
        #18 campos para escribir en la tabla processat
        # los datos del csv leido estan en la variable self.proocessat
        db = self.conectardb 
        query = QSqlQuery(db)
        
        start_time=time.time()
        
        #get folder path        
        path_dir = self.dlg.pathcsvprocessat.text() # folder path
        if path_dir=='':
            self.Missatge(self.tr(u'Error. Tria una carpeta de dades!!')) 
            return
            
        files=os.listdir(str(path_dir))
        list_files=[] #list all the csv files
        for name in files:
            try:
                num=name.find('METADADES.csv')
                if num>=0:
                  list_files.append(name)  
            except ValueError: 
                pass
                
        if list_files==[]:
            self.Missatge(self.tr(u'Error. No hi ha arxius de METADADES per carregar a aqueta carpeta:\n{} !!'.format(path_dir)))
            return

        #buscar la geoset id que necesitamos
        if self.dlg.CBdadesgeoset.currentText()=='' or self.dlg.CBdadesgeoset.currentText()==None:
            self.Missatge(self.tr(u"Selecciona un conjunt de dades.\n"))
            return 
                
        orden='SELECT geophobjectsetid FROM geophobjectset WHERE inspireid=\'{}\';'.format(self.dlg.CBdadesgeoset.currentText())  
        if query.exec_(orden)==0: 
            self.Missatge(self.tr(u"Error al consultar la tabla geoset per els processats.\n")+query.lastError().text())
            return True 
        while query.next():
            idgeoset=query.value(0)        
        
        for name in list_files: #corremos todos los archivos
            archivo=open(path_dir+'\\'+name,'r')
            reader=csv.reader(archivo)
            processat=[]
            for row in reader:
                row=row[0].split(';')
                processat.append(row)
            archivo.close()
            
            if processat==[]:
                self.Missatge(self.tr(u"No hi ha dades de processat a carregar"))
                return
        
            #change '' for None's
            for i in range(len(processat)):
                if processat[i][1]=='':
                    processat[i][1]=None
                    
            campos='inspireid,name,type,documentcitation,documentation_void,processparameter_name,processparameter_name_void'
            campos+=',processparameter_description,processparameter_description_void,responsibleparty,responsibleparty_void'
            campos+=',pixelarea,satellite,orbit,imagenum,firstimage,lastimage,date,incidenceangle,geophobjectset'
        
            query.prepare('INSERT INTO {} ({}) VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14,:15,:16,:17,:18,:19,:20);'.format('processes',campos)) #no check nada
            query.bindValue(':1','es.icgc.ge.psi_'+processat[0][1]) #inspire id
            query.bindValue(':2',processat[0][1]) #name
            query.bindValue(':3',processat[1][1]) #type 
            query.bindValue(':4',processat[2][1]) #dataprocessat[2][1]) #doccitation
            query.bindValue(':5',processat[3][1])   
            query.bindValue(':6',processat[4][1]) #processparam_name        
            query.bindValue(':7',processat[5][1])  
            query.bindValue(':8',processat[6][1]) #processparam_deescription
            query.bindValue(':9',processat[7][1])
            query.bindValue(':10',processat[8][1]) #responsible
            query.bindValue(':11',processat[9][1]) 
            query.bindValue(':12',processat[10][1]) #pixelarea
            query.bindValue(':13',processat[11][1]) #satellite   
            query.bindValue(':14',processat[12][1]) #orbit
            query.bindValue(':15',int(processat[13][1])) #imagenum
        
            date=processat[14][1].split('/')
            fecha=date[2]+'-'+date[1]+'-'+date[0]
            query.bindValue(':16',fecha) #firstimage
        
            date=processat[15][1].split('/')
            fecha=date[2]+'-'+date[1]+'-'+date[0]
            query.bindValue(':17',fecha) #lastimage
        
            date=processat[16][1].split('/')
            fecha=date[2]+'-'+date[1]+'-'+date[0]
            query.bindValue(':18',fecha) #date
        
            query.bindValue(':19',processat[17][1]) #incident angle
            query.bindValue(':20',idgeoset) #geosetid

            if query.exec_()==0:
                self.Missatge(self.tr(u"Error al escriure a la taula processes\n")+query.lastError().text())
                return
            else:
                if os.isatty(1):
                    print 'Cargado procesado: {}'.format(name) 


        if os.isatty(1):
            print 'Finalizada carga de procesados'
            print '--- {} seconds ---'.format(time.time() - start_time)  
        
        self.dlg.pathcsvprocessat.clear()
        return #acaba


    def carregar_dades(self):
        '''
        Docstring: funcion carga y escribe todos los datos en la base de datos. Rellena las tablas:
            geophobjectset, geophobject, spatialsamplingfeature, samplingfeature, samplingresult,
            observation y observation result.
            Loop sobre archivos en la carpeta y loop sobre filas en cada archivo
        ''' 
        if self.dlg.cBdades.isChecked() and self.dlg.cBdadespart.isChecked():
            self.Missatge(self.tr(u"Error. Les dues opcions estan seleccionades\n"))
            return
        elif self.dlg.cBdades.isChecked():
            self.Missatge(self.tr(u"Començant la carrega de dades\n"),'Informacio') 
            
            if self.dlg.lEgeosetinspireid.text()=='':
                self.Missatge(self.tr(u"Error. Identificador del conjunt en blanc.\n"))
                return
                
        elif self.dlg.cBdadespart.isChecked():
            self.Missatge(self.tr(u"Començant la carrega de dades.\nAfegint dades a un conjunt existent"),'Informacio')
        else:
            self.Missatge(self.tr(u"Error. Selecciona una opcio.\n"))
            return    
        
        db=self.conectardb     #create the connection and the Query        
        query = QSqlQuery(db)
        
        #obtain campaign id
        if self.dlg.cBdades.isChecked(): #carga total
            campname=self.dlg.CBcampdades.currentText()
            exist,idcampaign = self.isinbd(query,'campaign','name',campname,'campaignid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el campaign ide"))
                return
                
        else:                           #carga parcial
            campname=self.dlg.CBdadescamp.currentText()
            

        if self.dlg.cBdades.isChecked(): #CARGA TOTAL GEOSET + DATOS
            if self.dlg.CBdoccitdades.currentText()=='':
                idcitation=None #citation geoset None
            else:
                exist,idcitation = self.isinbd(query,'documentcitation','name', #obtain citation id
                                       self.dlg.CBdoccitdades.currentText(),'documentcitationid')
                if exist==0:
                    self.Missatge(self.tr(u"Error al buscar el documentcitation ide"))
                    return

            exist,idgeocol = self.isinbd(query,'geologiccollection','name',#obtain geocol id
                                       self.dlg.CBgeocoldades.currentText(),'geologiccollectionid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el geologiccollection ide"))
                return
                
            #como la carga es total, usaremos el max(idgeoset)+1 , que ya lo crearemos despues
            orden='SELECT max(geophobjectsetid) FROM geophobjectset WHERE campaign={}'.format(idcampaign)
            if query.exec_(orden)==0:
                self.Missatge(self.tr(u"Error a la consulta max geophobjectset en carrega total.\n")+query.lastError().text())
                return True
            while query.next():
                num=query.value(0)
                if num==None or num=='':
                    num=0
                idgeopset=num+1 #añadimos el siguiente en la lista            
            
        else: #carga parcial: obtener de la geoset las id's anteriores SOLO DATOS
            campos='geophobjectsetid,campaign,citation,geologiccollection'
            if query.exec_('SELECT ({0}) FROM {1} WHERE {2}=\'{3}\';'.format(campos,'geophobjectset','Inspireid',self.dlg.CBdadesgeoset.currentText()))==0:
                self.Missatge(self.tr(u"Error al consultar geoset.\n")+query.lastError().text())
                return
            else:
                ide=[]
                while query.next():
                    ide=query.value(0)
            ide=ide.replace('(','')
            ide=ide.replace(')','')
            ide=ide.split(',')

            idgeopset=ide[0]
            idcampaign=ide[1]
            idcitation=ide[2]
            idgeocol=ide[3]
            
        #aqui estan todas las id's definidas para los DOS casos
        #print 'todas las ids geoset,camp,cit,process,geocol',idgeopset,idcampaign,idcitation,idprocess,idgeocol
            
        path_dir = self.dlg.lEloadpath.text() # folder path
        if path_dir=='':
            self.Missatge(self.tr(u'Error. Tria una carpeta de dades!!')) 
            return
            
        files=os.listdir(str(path_dir))
        list_files=[] #list all the csv files
        for name in files:
            if name[-4:]=='.csv':
                list_files.append(name)
        if list_files==[]:
            self.Missatge(self.tr(u'Error. No hi han arxius csv per carregar a aqueta carpeta:\n{} !!'.format(path_dir)))
            return 
        
        list_files_mod = self.rename_listfiles(path_dir,list_files) #rename las fechas de los nombres de los  archivos a 
        #la 1 y ultima columna de datos
        #list_files=nombres de los archivos en la carpeta
        #list_files_mod = nombres de los archivos con las fechas cambiadas
        
        error=self.check_dependencias(query,list_files_mod,idcampaign,idgeopset) #check file dependencies
        
        if error:
            self.dlg.progressBar.reset()
            return
        
        for num,files in enumerate(list_files): #read each csv file
            header=[]  #una lista      
            header,geometrygeoset,maxrows=self.prelectura(path_dir+'\\'+files,header)

            #write to geophobjectset 
            if (num ==0) and self.dlg.cBdades.isChecked(): #carga total 1a vez
                error,idgeoset = self.write_to_geophobjectset(query,idcampaign,idcitation,
                                                           idgeocol,geometrygeoset)
                if error:
                    self.Missatge(self.tr(u"Error al escriure a la taula geocollectionset"))
                    return 
            elif (num==0) and self.dlg.cBdadespart.isChecked(): #carga parcial, buscar el idgeoset selecionado
                error,idgeoset = self.isinbd(query,'geophobjectset','InspireId',#obtain geoset id
                                       self.dlg.CBdadesgeoset.currentText(),'geophobjectsetid')
                if error==0:
                    self.Missatge(self.tr(u"Error. La geophobjectset seleccionada no existeix"))
                    return
            else:
                pass
            
            #extraer la informacion necesaria del header del archivo csv            
            name=files.split('_')[2]+'_'+files.split('_')[3] #name for table
            init_dades=header.index('EFF_AREA')+1 #indice de la primera fecha en el header
            dates=[];maxdates=[]
            dates.extend(header[init_dades:]) #todas las fechas
            for i,fecha in enumerate(dates):
                dates[i]=fecha.replace('D','')
        
            maxdates.append(dates[0]);maxdates.append(dates[-1])
            numdates=len(dates) #numero de fechas que hay
            
            #progress bar and missages
            self.dlg.progressBar.reset()
            self.dlg.progressBar.setMinimum(0)
            self.dlg.progressBar.setMaximum(11+numdates)
            self.dlg.lEstatexport.clear()
            self.dlg.lEstatexport.setText('LLegint arxiu {}/{} : {}'.format(num+1,len(list_files),files))
            
            #cargamos datos en tabla temporal
            if self.importcsvtodb(query,path_dir+'\\'+files,numdates) ==1: #si devuelve error, adios
                return
            self.dlg.progressBar.setValue(1)
            
            #rellenamos tabla geophobject
            if self.writetogeophobject(query,idgeocol)==1: #si devuelve error, adios
                return
            self.dlg.progressBar.setValue(2) 
            
            #rellenamos tabla spatialsampling
            if self.writespatialsampling(query,idgeoset)==1: #si devuelve error, adios
                return
            self.dlg.progressBar.setValue(3)    
            
            #rellenamos tabla samplingfeature
            if self.writesamplingfeature(query,maxdates)==1: #si devuelve error, adios
                return
            self.dlg.progressBar.setValue(4) 
            

            #rellenar la tabla samplingresult: todo lo que necesitamos ya existe en la tabla temporal (las ids y los valores)
            #-------------------------------------------------------------------------------
            tipo=['_VEL','_V_STDEV','_COH']
            #-----------------------velocidades
            if os.isatty(1):
                print 'Cargando datos de velocidad...' 
            start_time = time.time() #tiempo
            orden='INSERT INTO samplingresult(samplingfeature,value,name) '
            orden+='SELECT idsampfeat, vel, \'{}\' FROM temporal;'.format(name+tipo[0])
            if query.exec_(orden)==0:
                self.Missatge(self.tr(u"Error a la taula samplingresult (velocitats).\n")+query.lastError().text())
                return
            self.dlg.progressBar.setValue(6)
            if os.isatty(1):
                print 'Cargados datos de velocidad'       
                print '--- {} seconds ---'.format(time.time() - start_time)            
            
            #-----------------------v_std 
            if os.isatty(1):
                print 'Cargando datos de v_std...' 
            start_time = time.time() #tiempo
            orden='INSERT INTO samplingresult(samplingfeature,value,name) '
            orden+='SELECT idsampfeat, vel_std, \'{}\' FROM temporal;'.format(name+tipo[1])
            if query.exec_(orden)==0:
                self.Missatge(self.tr(u"Error a la taula samplingresult (v_std).\n")+query.lastError().text())
                return
            self.dlg.progressBar.setValue(7)
            if os.isatty(1):
                print 'Cargados datos de v_std'       
                print '--- {} seconds ---'.format(time.time() - start_time)
            
            #-----------------------coherencia
            if os.isatty(1):
                print 'Cargando datos de coherencia...' 
            start_time = time.time() #tiempo
            orden='INSERT INTO samplingresult(samplingfeature,value,name) '
            orden+='SELECT idsampfeat, COHERENCE, \'{}\' FROM temporal;'.format(name+tipo[2])
            if query.exec_(orden)==0:
                self.Missatge(self.tr(u"Error a la taula samplingresult (coherencia).\n")+query.lastError().text())
                return
            self.dlg.progressBar.setValue(8)
            if os.isatty(1):
                print 'Cargados datos de coherencia'       
                print '--- {} seconds ---'.format(time.time() - start_time)
            
            #abrimos loop sobre fechas (columnas de datos con fecha)            
            for i,fecha in enumerate(dates):
                start_time = time.time() #tiempo

                maxidobser=self.obtain_max_id(query,'observation','observationid')
                
                # rellenar la tabla observation: se ponen en serie, sin mirar duplicados ni nada mas....             
                orden='INSERT INTO observation(phenomenontime,samplingfeature) '
                orden+='SELECT to_date(\'{}\',\'YYYYMMDD\'), idsampfeat FROM temporal;'.format(fecha)
                if query.exec_(orden)==0:
                    self.Missatge(self.tr(u"Error al escriure a la taula observation.\n")+query.lastError().text())
                    return
                if os.isatty(1):
                    print 'Cargados datos en la tabla observation para la columna i={}'.format(i)      
                    print '--- {} seconds ---'.format( time.time() - start_time)
    
                ####rellenar la tabla observationresult
                #creo una tabla auxiliar con todas las id's de observation (numero de puntos)
                start_time = time.time() #tiempo
                #----------------------idobstemporal----------------------
                orden='DROP TABLE IF EXISTS idobstemporal;'
                if query.exec_(orden)==0:
                    self.Missatge(self.tr(u"Error taula idobstemporal (drop).\n")+query.lastError().text())
                    return
    
                orden='CREATE TABLE idobstemporal (id SERIAL PRIMARY KEY,id_obs int);'
                if query.exec_(orden)==0:
                    self.Missatge(self.tr(u"Error taula idobstemporal (create).\n")+query.lastError().text())
                    return

                orden='TRUNCATE idobstemporal RESTART IDENTITY;'
                if query.exec_(orden)==0:
                    self.Missatge(self.tr(u"Error taula idobstemporal (truncate).\n")+query.lastError().text())
                    return

                orden='INSERT INTO idobstemporal(id_obs) SELECT observationid FROM observation '
                orden+=' WHERE observationid>{};'.format(maxidobser)
                if query.exec_(orden)==0:
                    self.Missatge(self.tr(u"Error taula idobstemporal (insert).\n")+query.lastError().text())
                    return
                if os.isatty(1):
                    print 'Creada tabla idobstemporal para la columna i={}'.format(i)       
                    print '--- {} seconds ---'.format(time.time() - start_time)
                
                #-------------------------------------------------------------------------------
                #escribir en observationresult
                start_time = time.time() #tiempo
                orden='INSERT INTO observationresult(name,value,observation) '
                orden+='SELECT \'{}\', {}, id_obs FROM temporal, idobstemporal WHERE temporal.ids=idobstemporal.id;'.format(name,'dato'+str(i))
                if query.exec_(orden)==0:
                    self.Missatge(self.tr(u"Error al escriure a la taula observationresult.\n")+query.lastError().text())
                    return
                if os.isatty(1):
                    print 'Cargados datos en la tabla observationresult para la columna i={}'.format(i)       
                    print '--- {} seconds ---'.format(time.time() - start_time)  
                    
                #borramos la tabla temporal idobstemporal
                start_time = time.time() #tiempo
                orden='DROP TABLE IF EXISTS idobstemporal;'
                if query.exec_(orden)==0:
                    self.Missatge(self.tr(u"Error taula idobstemporal (end drop).\n")+query.lastError().text())
                    return
                self.dlg.progressBar.setValue(9+i)
                
                if os.isatty(1):
                    print 'Borrada tabla idobstemporal para la columna i={}'.format(i)       
                    print '--- {} seconds ---'.format(time.time() - start_time)

            #end fecha loop--------
            
            #borramos la tabla temporal donde estan los datos importados del csv
            orden='DROP TABLE IF EXISTS temporal;'
            if query.exec_(orden)==0:
                self.Missatge(self.tr(u"Error taula temporal (end drop).\n")+query.lastError().text())
                return 
            self.dlg.progressBar.setValue(11+numdates)
            
            #añadimos registro en la tabla log_obs
            orden='INSERT INTO log_obs(name, campaignid, geosetid, date_init, date_end) VALUES '
            orden+='(\'{}\',{},{},'.format(name,idcampaign,idgeopset)
            orden+='to_date(\'{}\',\'YYYYMMDD\'),to_date(\'{}\',\'YYYYMMDD\'));'.format(maxdates[0],maxdates[1])
            if query.exec_(orden)==0:
                self.Missatge(self.tr(u"Error al actualizar tabla log_obs.\n")+query.lastError().text())
                return
            
        #end files loop---------------------------------
        self.Missatge(self.tr(u'Carrega de dades finalitzada'),'Informacio')
        
        
    def writesamplingfeature(self,query,maxdates):
        '''
        Docstring: Funcion que escribe en la tabla samplingfeature
        1 - Buscas los puntos que has de añadir (que no existes en samplingfeature),guardas su temporal.id
        2 - Añades estos puntos a la tabla samplingfeature
        3 - Buscas el samplingfeatureid de los puntos de la tabla temporal        
        '''
        if os.isatty(1):
            print 'Escribiendo en tabla samplingfeature...' 
            
        start_time = time.time() #tiempo
        #añadimos nueva columna a la tabla de datos temporal, esta columna almacenara los idsamplingfeature
        orden='ALTER TABLE temporal ADD COLUMN idsampfeat int;' #añadimos id a la tabla de datos
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula temporal (alter idsampfeat).\n")+query.lastError().text())
            return True               

        if os.isatty(1):
            print 'Buscando registros repetidos en samplingfeature y actualizando...' 
            
        orden='INSERT INTO samplingfeature (spatialsamplingfeature,validtime_begin,validtime_end) ' 
        orden+='SELECT idsspatialsamp,to_date(\'{}\',\'YYYYMMDD\'),to_date(\'{}\',\'YYYYMMDD\') '.format(maxdates[0],maxdates[1])
        orden+='FROM temporal WHERE idsspatialsamp IN ' 
        orden+='(SELECT foo.ids FROM '
        orden+='(SELECT idsspatialsamp AS ids FROM temporal '
        orden+='EXCEPT '
        orden+='SELECT spatialsamplingfeature FROM samplingfeature '
        orden+='WHERE validtime_begin=to_date(\'{}\',\'YYYYMMDD\') '.format(maxdates[0])
        orden+='AND validtime_end=to_date(\'{}\',\'YYYYMMDD\')) as foo)   '.format(maxdates[1])
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error al escriure a la taula samplingfeature els nous punts.\n")+query.lastError().text())
            return True 

        #3 buscamos la samplingfeatureid de los puntos de la tabla temporal y lo insertamos en la columna temporal.idsampfeat
        #----------------------idssamptemporal----------------------
        orden='DROP TABLE IF EXISTS idssamptemporal;'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula idssamptemporal (drop).\n")+query.lastError().text())
            return True
    
        orden='CREATE TABLE idssamptemporal (id SERIAL PRIMARY KEY,id_sptfeat int);'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula idssamptemporal (create).\n")+query.lastError().text())
            return True

        orden='TRUNCATE idssamptemporal RESTART IDENTITY;'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula idssamptemporal (truncate).\n")+query.lastError().text())
            return True

        if os.isatty(1):
            print 'Escribiendo en tabla idssamptemporal...' 
            
        orden='INSERT INTO idssamptemporal(id_sptfeat) '
        orden+='(SELECT foo.ids FROM  '
        orden+='(SELECT samplingfeatureid as ids,spatialsamplingfeature as spatials FROM samplingfeature '
        orden+='WHERE validtime_begin=to_date(\'{}\',\'YYYYMMDD\') '.format(maxdates[0])
        orden+='AND validtime_end=to_date(\'{}\',\'YYYYMMDD\')) as foo, temporal '.format(maxdates[1])
        orden+='WHERE foo.spatials = temporal.idsspatialsamp);'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error al escriure a la taula idspatialsamptemporal el spatialsamplingid.\n")+query.lastError().text())
            return True

        if os.isatty(1):
            print 'Escribiendo ids en tabla temporal...'    
            
        #ya tenemos la tabla idssamptemporal llena, ahora pasamos los datos a la tabla temporal igualando las primary keys 
        orden='UPDATE temporal SET idsampfeat=id_sptfeat FROM idssamptemporal WHERE temporal.ids=idssamptemporal.id;'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error al escriure a la taula temporal el samplingfeatureid.\n")+query.lastError().text())
            return True

        #borramos la tabla idssamptemporal
        orden='DROP TABLE IF EXISTS idssamptemporal;'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula idssamptemporal (end drop).\n")+query.lastError().text())
            return True 

        if os.isatty(1):
            print 'Obtenidos samplingfeatureid de los puntos'       
            print '--- {} seconds ---'.format(time.time() - start_time)        
        
        self.dlg.progressBar.reset()
        return False #el error final


    def writespatialsampling(self,query,idgeoset):
        '''
        Docstring: Funcion que escribe en la tabla spatialsamplingfeature.
        1 - Buscas los puntos que has de añadir (que no existes en spatialsamplingfeature),guardas su temporal.id
        2 - Añades estos puntos a la tabla spatialsamplingfeature
        3 - Buscas el spatialsamplingid de los puntos de la tabla temporal
        '''
        if os.isatty(1):
            print 'Escribiendo en tabla spatialsampling...'         
        
        start_time = time.time() #tiempo
        #añadimos nueva columna a la tabla de datos temporal, esta columna almacenara los idspatialsampling
        orden='ALTER TABLE temporal ADD column idsspatialsamp int;' #añadimos id a la tabla de datos
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula temporal (alter idsspatialsamp).\n")+query.lastError().text())
            return True 

        if os.isatty(1):
            print 'Buscando registros repetidos en spatialsampling y actualizando...'
            
        orden='INSERT INTO spatialsamplingfeature (geophobject,geophobjectset) '
        orden+='SELECT idsgeophobject,{} FROM temporal WHERE idsgeophobject in '.format(idgeoset)
        orden+='(SELECT foo.ids FROM ' 
        orden+='(SELECT idsgeophobject as ids FROM temporal '  
        orden+=' EXCEPT '
        orden+='SELECT geophobject FROM spatialsamplingfeature WHERE geophobjectset={}) as foo);'.format(idgeoset)

        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error al escriure a la taula spatialsamplingfeature els nous punts.\n")+query.lastError().text())
            error=True
            return error

        #3 buscamos la spatialsamplingid de los puntos de la tabla temporal y lo insertamos en la columna temporal.idsspatialsamp
        #----------------------idspatialsamptemporal----------------------
        orden='DROP TABLE IF EXISTS idspatialsamptemporal;'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula idspatialsamptemporal (drop).\n")+query.lastError().text())
            return True
    
        orden='CREATE TABLE idspatialsamptemporal (id SERIAL PRIMARY KEY,id_sptfeat int);'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula idspatialsamptemporal (create).\n")+query.lastError().text())
            return True

        orden='TRUNCATE idspatialsamptemporal RESTART IDENTITY;'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula idspatialsamptemporal (truncate).\n")+query.lastError().text())
            return True

        if os.isatty(1):
            print 'Escribiendo en tabla idspatialsamptemporal...' 
            
        orden='INSERT INTO idspatialsamptemporal (id_sptfeat) '
        orden+='(SELECT spatialsamplingid FROM spatialsamplingfeature '
        orden+='INNER JOIN temporal ON '
        orden+='geophobject = idsgeophobject WHERE geophobjectset={});'.format(idgeoset)
#        orden+='(SELECT spatialsamplingid FROM spatialsamplingfeature WHERE geophobjectset={} '.format(idgeoset)
#        orden+='AND geophobject IN ' 
#        orden+='(SELECT idsgeophobject FROM temporal));'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error al escriure a la taula idspatialsamptemporal el spatialsamplingid.\n")+query.lastError().text())
            error=True
            return error

        if os.isatty(1):
            print 'Escribiendo ids en tabla temporal...'  
        #ya tenemos la tabla idspatialsamptemporal llena, ahora pasamos los datos a la tabla temporal igualando las primary keys 
        orden='UPDATE temporal SET idsspatialsamp=id_sptfeat FROM idspatialsamptemporal WHERE temporal.ids=idspatialsamptemporal.id;'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error al escriure a la taula temporal el geophobjectid.\n")+query.lastError().text())
            return True

        #borramos la tabla idspatialsamptemporal
        orden='DROP TABLE IF EXISTS idspatialsamptemporal;'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula idspatialsamptemporal (end drop).\n")+query.lastError().text())
            return True 

        if os.isatty(1):
            print 'Obtenidos spatialsamplingfeatureid de los puntos'       
            print '--- {} seconds ---'.format(time.time() - start_time)        

        return False #el error final
    

    def writetogeophobject(self,query,idgeocol):
        '''
        Doctsring: Funcion que escribe en la tabla geophobject.
        1- Buscas los nuevos puntos que has de añadir (que no existen en geophobject), guardas su temporal.id
        2- Añades estos puntos a la tabla geophobject
        3- Buscas el geophobject.id de los puntos que tienes en la tabla temporal
        '''
        if os.isatty(1):
            print 'Escribiendo en tabla geophobject...' 
            
        error=False
        start_time = time.time() #tiempo
        #añadimos nueva columna a la tabla de datos temporal, esta columna almacenara los idgeophobject
        orden='ALTER TABLE temporal ADD column idsgeophobject int;' #añadimos id a la tabla de datos
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula temporal (alter geophobjectid).\n")+query.lastError().text())
            error=True
            return error

        if os.isatty(1):
            print 'Buscando registros repetidos en geophobject y actualizando...'
            
        orden='INSERT INTO geophobject (inspireid, geologiccollection, projectedgeometry,height) ' 
        orden+='SELECT \'es.icgc.ge.psi_\' || utmx || \'_\' || utmy, {},ST_SetSRID(ST_MakePoint(utmx, utmy), 25831),'.format(idgeocol)
        orden+='height FROM temporal WHERE \'es.icgc.ge.psi_\' || utmx || \'_\' || utmy in  ('
        orden+='select foo.coord from ' 
        orden+='(SELECT \'es.icgc.ge.psi_\' || utmx || \'_\' || utmy as coord from temporal except '
        orden+='SELECT inspireid from geophobject) as foo);'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error al escriure a la taula geophobject els nous punts.\n")+query.lastError().text())
            error=True
            return error    
    
        
        #3 buscamos la geophobjectid de los puntos de la tabla temporal y lo insertamos en la columna temporal.idsgeophobject
        #necesitamos una tabla temporal para poder hacer esto
        #----------------------idgeotemporal----------------------
        orden='DROP TABLE IF EXISTS idgeotemporal;'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula idgeotemporal (drop).\n")+query.lastError().text())
            error=True
            return error
    
        orden='CREATE TABLE idgeotemporal (id SERIAL PRIMARY KEY,id_geo int);'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula idgeotemporal (create).\n")+query.lastError().text())
            error=True
            return error

        orden='TRUNCATE idgeotemporal RESTART IDENTITY;'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula idgeotemporal (truncate).\n")+query.lastError().text())
            error=True
            return error

        if os.isatty(1):
            print 'Escribiendo en tabla idgeotemporal...'
            
        orden='INSERT INTO idgeotemporal (id_geo) '
        orden+='(SELECT geophobjectid FROM geophobject INNER JOIN temporal ON '
        orden+='inspireid=\'es.icgc.ge.psi_\' || utmx || \'_\' || utmy);'
#        orden+='(SELECT geophobjectid FROM geophobject WHERE inspireid IN '
#        orden+='(SELECT \'es.icgc.ge.psi_\' || utmx || \'_\' || utmy FROM temporal));'

        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error al escriure a la taula idgeotemporal el geophobjectid.\n")+query.lastError().text())
            error=True
            return error

        if os.isatty(1):
            print 'Escribiendo ids en tabla temporal...' 
            
        #ya tenemos la tabla idgeotemporal llena, ahora pasamos los datos a la tabla temporal igualando las primary keys 
        orden='UPDATE temporal SET idsgeophobject=id_geo FROM idgeotemporal WHERE temporal.ids=idgeotemporal.id;'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error al escriure a la taula temporal el geophobjectid.\n")+query.lastError().text())
            error=True
            return error

        #borramos la tabla idgeotemporal
        orden='DROP TABLE IF EXISTS idgeotemporal;'
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula idgeotemporal (end drop).\n")+query.lastError().text())
            error=True
            return error 

        if os.isatty(1):
            print 'Obtenidos geophobjectid de los puntos'       
            print '--- {} seconds ---'.format(time.time() - start_time)        
        return error

        

    def importcsvtodb(self,query,archivo,numdates):
        orden='DROP TABLE IF EXISTS temporal;' #borramos la tabla si existe
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula temporal (drop).\n")+query.lastError().text())
            return True #devuelve error
            
        datos=''
        for i in range(numdates):
            datos=datos+',dato{} double precision'.format(i)
    
        orden='CREATE TABLE temporal (code char(20), UTMX int, UTMY int, height double precision, '
        orden+='h_stv double precision,vel double precision,vel_std double precision'
        orden+=',COHERENCE double precision,EFF_AREA double precision' + datos+');'        
        if query.exec_(orden)==0:  #creamos la tabla
            self.Missatge(self.tr(u"Error taula temporal (create).\n")+query.lastError().text())
            return True #devuelve error            

        
        orden='TRUNCATE temporal RESTART IDENTITY;' #reiniciamos para que las ids sean correctas
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula temporal (truncate).\n")+query.lastError().text())
            return True #devuelve error            

        if os.isatty(1):
            print 'Importando datos del csv a la tabla temporal...'   
            
        start_time = time.time() #tiempo
        arch=open(archivo,'r')
        reader=csv.reader(arch,delimiter=';')
        next(reader) #saltamos el header del file
        i=0;valor=''
        for row in reader:
            i+=1
            data=row
            data[1]=int(float(data[1]))
            data[2]=int(float(data[2]))
            for j in range(3,len(data)):
                data[j]=float(data[j])    
            valor=valor+str(tuple(data))+','
            if i>900: #queries de 900 filas
                valor=valor[:-1]
                orden='INSERT INTO temporal VALUES {};'.format(valor)
                if query.exec_(orden)==0:
                    self.Missatge(self.tr(u"Error taula temporal (insert values).\n")+query.lastError().text())
                    return True #devuelve error                    
                    break
                i=0
                valor=''
        
        if valor!='': #las filas que no son multiplos de 900 (las que falta)
            valor=valor[:-1]
            orden='INSERT INTO temporal VALUES {};'.format(valor)
            if query.exec_(orden)==0:
                self.Missatge(self.tr(u"Error taula temporal (insert values).\n")+query.lastError().text())
                return True #devuelve error                
            
        if os.isatty(1):
            print 'Created temporal table in the database'       
            print '--- {} seconds ---'.format(time.time() - start_time)        
        arch.close()
        
        orden='ALTER TABLE temporal ADD column ids SERIAL PRIMARY KEY;' #añadimos id a la tabla de datos
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error taula temporal (alter).\n")+query.lastError().text())
            return True #devuelve error 
            
        return False #el error final
        

    def rename_listfiles(self,path_dir,list_files):
        #renombramos las fechas de los archivos (las que aparecen en su nombre) con las fechas de la primera y
        #ultima columna de datos.
        if os.isatty(1):
            print 'renombrando archivos...'         
        
        lista_archivos=[]
        for name in list_files:
            archivo=open(path_dir+'\\'+name,'r')
            reader=csv.reader(archivo,delimiter=';') 
            for row in reader:
                header=row
                break
            archivo.close()
            init_dades=header.index('EFF_AREA')+1 
            init_dates=header[init_dades].replace('D','')
            fin_dates=header[-1].replace('D','')
            name=name.split('_')[0]+'_'+name.split('_')[1] +'_'+name.split('_')[2] +'_'+name.split('_')[3]
            lista_archivos.append(name+'_'+init_dates+'_'+fin_dates)
        return lista_archivos

    def prelectura(self,archivo,header):
        
        if os.isatty(1):
            print 'Prelectura del archivo...' 
            
        archivo=open(archivo,'r')
        reader=csv.reader(archivo,delimiter=';')
        i=0 #first row
        UTMX=[];UTMY=[]
        for row in reader:
            if i==0:
                header=row
            else:
                UTMX.append(int(float(row[1])))
                UTMY.append(int(float(row[2])))
            i=i+1

        max_xind=UTMX.index(max(UTMX))
        max_yind=UTMY.index(max(UTMY))
        min_xind=UTMX.index(min(UTMX))
        min_yind=UTMY.index(min(UTMY))
        maxrow=i-1 #quitamos la columna del header
        #U4---U3
        #U1---U2
        
        U1=[UTMX[min_xind],UTMY[min_yind]] #los puntos de la geometria
        U2=[UTMX[max_xind],UTMY[min_yind]]
        U3=[UTMX[max_xind],UTMY[max_yind]]
        U4=[UTMX[min_xind],UTMY[max_yind]]
        del UTMY,UTMX
        archivo.close()
        geometry=[U1,U2,U3,U4] 
    
        if os.isatty(1):
            print 'Prelectura finalizada' 
        
        return header,geometry,maxrow


    def write_to_geophobjectset(self,query,idcampaign,idcitation,
                                                           idgeocol,geometrygeoset):
        '''
        Docstring: funcion que escribe en la tabla geophobjectset
        input: ides[idcampaign,idgeocollection,idcitation,idprocesses]
                geometria del poligono que envuelve los puntos (un cuadrado)
        '''
        tabla='geophobjectset'
        ide=self.obtain_max_id(query,tabla,'geophobjectsetid')+1
        
        #distribution void solo si no existe distribution (metadatos)
        if self.dlg.CBdistnfo.currentText()=='': 
            distribuinfo=None
            void=self.dlg.CBdistnfo_void.currentText() #get from the  distribution combobox void text
            if void=='':
                self.Missatge(self.tr(u"El camp informe metadades esta buit. Indica el perque"))
                return True
            exist,distribuinfo_void = self.isinbd(query,'cl_voidtypevalue','voidtypevalue',void,'voidtypevalueid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el void ide"))
                return True
        else:
            exist,distribuinfo = self.isinbd(query,'documentcitation','name', #obtain citation id de metadates
                                       self.dlg.CBdistnfo.currentText(),'documentcitationid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar la id de les metedades (documentcitation)"))
                return True 
            distribuinfo_void=None
            
        #largework void solo si no existe largework (codigo ICGC)
        if self.dlg.lEgeosetlargework.text() =='': 
            largework=None
            void=self.dlg.CBlargework_void.currentText()
            if void=='':
                self.Missatge(self.tr(u"El camp codi projecte esta buit. Indica el perque"))
                return True
            exist,largework_void = self.isinbd(query,'cl_voidtypevalue','voidtypevalue',void,'voidtypevalueid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el void ide"))
                return True

        else:
            largework= self.dlg.lEgeosetlargework.text()
            largework_void=None
        
        U1=geometrygeoset[0][:];U2=geometrygeoset[1][:];U3=geometrygeoset[2][:]
        U4=geometrygeoset[3][:];U5=geometrygeoset[0][:]
        geometry='SRID=25831;POLYGON(({} {},{} {},{} {},{} {},{} {}))'.format(U1[0],U1[1],
                                                            U2[0],U2[1],U3[0],U3[1],U4[0],U4[1],U5[0],U5[1])
        
        campos='geophobjectsetid,inspireid,distributioninfo,distributioninfo_void,largerwork,largerwork_void,projectedgeometry'
        campos+=',geologiccollection,campaign,citation'
        
        query.prepare('INSERT INTO {} ({}) VALUES (:0,:1,:2,:3,:4,:5,ST_GeomFromEWKT(:6),:7,:8,:9);'.format(tabla,campos))
        query.bindValue(':0',ide)
        query.bindValue(':1',self.dlg.lEgeosetinspireid.text()) #inspireid
        query.bindValue(':2',distribuinfo) #distribuinfo
        query.bindValue(':3',distribuinfo_void) #distribuinfo_void
        query.bindValue(':4',largework) #largework
        query.bindValue(':5',largework_void) #largework void
        query.bindValue(':6',geometry) #geometry
        query.bindValue(':7',idgeocol) #geocollection id
        query.bindValue(':8',idcampaign) #campaign id
        query.bindValue(':9',idcitation) #citation id
        if query.exec_()==0:
            self.Missatge(self.tr(u"Error al actualitzar la taula {}.\n".format(tabla))+query.lastError().text())
            error=True
        else:
            #self.Missatge(self.tr(u"Taula {} actualitzada\n".format(tabla)))
            self.dlg.CBgeosetshow.addItems([self.dlg.lEgeosetinspireid.text()]) #añadir al cbox de geosets existentes
            error=False
        return error,ide

 
    def check_dependencias(self,query,list_files,idcampaign,idgeopset):
        '''
        Docstring: funcion que mira las dependencias al cargar los archivos de la carpeta
                    Mirar dependencias implica que si cargas un tipo LOS, todos los que se derivan de esta medida
                    se han de borrar. Si la observacion ya esta, se borrara y se sustituye por la nueva del archivo.
            input-list_files: lista de archivos.csv que va ha cargar
        '''
        #filezone contiene todos los archivos correctos posibles para leer (definido en psi_zone.txt)
        #Antes de nada, vamos a ver si la lista de archivos se puede cargar o no
        for archivo in list_files:
            partes=archivo.split('_')
            medida=partes[0]+'_'+partes[1]+'_'+partes[2]+'_'+partes[3]
            try:
                filezone.index(medida)
            except ValueError: #no existe
                msgerror='L\'arxiu que intentes carregar {} no es una zona/mesura valida.\n'.format(archivo)
                msgerror+='Comprova les zones/mesures valides a l\'arxiu spi_zone.txt'
                self.Missatge(self.tr(msgerror))
                return True
                   
        #obtenemos las medidas que ya hemos introducido desde la tabla log_obs
            #creamos la tabla si no existe
        orden='SELECT COUNT (name) FROM log_obs'
        if query.exec_(orden)==0:
            Istabla=False
        else:
            Istabla=True
            
        if Istabla==False:   
            orden='CREATE TABLE log_obs (id SERIAL PRIMARY KEY, name varchar(30), '
            orden+='campaignid int, geosetid int, date_init date, date_end date);'
            if query.exec_(orden)==0:
                self.Missatge(self.tr(u"Error al crear la tabla log_obs.\n")+query.lastError().text())
                return True
            
        #obtenemos los tipos de medidas ya existentes en la tabla en formato MEDIDA_ZONA_FECHAINIT_FECHAFIN
            #mismo formato que los nombres de los archivo
        orden='SELECT name,date_init,date_end FROM log_obs '
        orden+='WHERE campaignid={} AND geosetid={}'.format(idcampaign,idgeopset)
        observacion=[]; fecha_in=[]; fecha_end=[]  
        if query.exec_(orden)==0: 
            self.Missatge(self.tr(u"Error al consultar la tabla log_obs.\n")+query.lastError().text())
            return True 
        while query.next():
            observacion.append(query.value(0))
            fecha=query.value(1)
            fecha_in.append(fecha.toString('yyyyMMdd'))
            fecha=query.value(2)
            fecha_end.append(fecha.toString('yyyyMMdd'))   
            
        #construir el formato adecuado
        observaciones=[]
        if observacion!=[]: #existen observaciones   
            for ind,obs in enumerate(observacion):
                observaciones.append(obs+'_'+fecha_in[ind]+'_'+fecha_end[ind])
                      
        #filtrar todos  los LOS existentes en la bdd
        zonaLOS=[]
        for obs in observaciones:
            if obs.find('LOS')>=0:
                zonaLOS.append(obs) #contiene [LOS_ZONA_FECHA] de la bdd

        todeleteobs=[]
        archivosLOS=[] #archivos LOS que vas a cargar LOS_ZONA
        #ordenar la lista de archivos: primero los LOS..., crea lista de todos los archivos LOS que va a cargar
        for i,archivo in enumerate(list_files):
            if archivo.find('LOS')>=0:
                list_files.remove(list_files[i])
                list_files.insert(0,archivo)  
                archivosLOS.append(archivo.split('_')[2]+'_'+archivo.split('_')[3]+'_'+archivo.split('_')[4]+'_'+archivo[:-4].split('_')[5]) #añadidas las fechas
        
        for archivo in list_files:
            if archivo.find('LOS')>=0:
                #es tipo LOS: LOS_+zona+FECHA
                mapcoord='LOS_'+archivo.split('_')[3]+'_' #mapa de la observacion
                mapcoord+=archivo.split('_')[4]+'_'+archivo[:-4].split('_')[5] #añadida la fecha init_fin
                #borrar todos las observaciones con estas cordenadas y fechas
                for obs in observaciones:
                    if (obs.find(mapcoord)==0) and (obs not in todeleteobs):
                        todeleteobs.append(str(obs))
            else:
                #no es tipo LOS: MEDIDA_ZONA_fecha
                medida=archivo.split('_')[2]+'_'+archivo.split('_')[3]+'_'
                medida+=archivo.split('_')[4]+'_'+archivo[:-4].split('_')[5] #añadida la fecha init_fin
                
                #comparar lo que cargas con la bdd y los LOS a cargar
                existeLOS=False 
                zonamedida=archivo.split('_')[3]
                fechamedida='_'+archivo.split('_')[4]+'_'+archivo[:-4].split('_')[5] #añadimos la fecha

                #miramos en los archivos a cargar
                for x in range(0,len(zonamedida),4):
                
                #miramos en los archivos que cargamos     
                    try:
                        existeLOS1=bool((archivosLOS.index('LOS_'+zonamedida[x:x+4]+fechamedida)>=0)) 
                    except ValueError:
                        existeLOS1=False 
                    
                #miramos en las zonas cargadas en la bd      
                    try:
                        existeLOS2=bool(zonaLOS.index('LOS_'+zonamedida[x:x+4]+fechamedida)>=0) 
                    except ValueError:
                        existeLOS2=False
                        
                    existeLOS= existeLOS1 or existeLOS2
                
                    if existeLOS==0: #si una zona ya no existe, fuera
                        error=True
                        self.Missatge(self.tr(u'Cancelada la carrega de dades,\nno existeix un LOS a la base de dades,\n'
                        'ni es carrega un arxiu LOS associat a aquesta zona \n'
                        'amb aquestes rang de dates.\nZona : {}'.format(zonamedida+fechamedida)))
                        return error                
                
                #borrar la observacion si ya existe en la campaña
                for obs in observaciones:
                    if (obs.find(medida)>=0) and (obs not in todeleteobs):
                        todeleteobs.append(obs)           
        
        error=False        
        if todeleteobs!=[]: #existen cosas a borrar
            m = QMessageBox()
            m.setIcon(QMessageBox.Warning)
            m.setWindowTitle('Confirmar')
            m.setText('Alguns arxius a carregar ja estan en la base de dades. \n'
            +'Abans de carregar s\'esborraran aquestes entrades a la base de dades.\n'
            +'{}\n'.format(todeleteobs)
            +'Estas segur?')
            m.setStandardButtons(QMessageBox.Ok);
            m.addButton(QMessageBox.Cancel);
            m.setButtonText(QMessageBox.Ok,"Aceptar")
            m.setButtonText(QMessageBox.Cancel,"Cancelar")
            
            if m.exec_()==  QMessageBox.Ok:
                for nombre in todeleteobs:
                    self.delete_observation(query,nombre,idgeopset)
                self.Missatge(self.tr(u'Entrades existents en la base de dades borrades'),'Informacio')
                error=False
            else:
                self.Missatge(self.tr(u'Cancelada la carrega de dades'),'Informacio')
                error=True
        return error

    def show_geoset_data(self):
        '''
        Docstring: funcion que activa el boton modificar para los conjuntos de datos (tabla geoset) y muestra en el
        formulario todos los datos asociados al geoset seleccionado en el combobox que esta a su izquierda
        '''
        if self.dlg.CBgeosetshow.currentText()=='': #no se ha seleccionado un geoset de la lista
            return 
        else:
            self.dlg.modgeoset.setEnabled(True) #activas el boton modificar y lo haces visible
            self.dlg.modgeoset.setVisible(True)
            
            #crear la query y consultar a la tabla geoset
            db=self.conectardb
            query = QSqlQuery(db)
              
            datos={}
            name=self.dlg.CBgeosetshow.currentText()
            campos='inspireid,distributioninfo,distributioninfo_void,largerwork,largerwork_void,geologiccollection'
            campos=campos+',campaign,citation'
            if query.exec_('SELECT ({}) FROM geophobjectset WHERE geophobjectset.inspireid=\'{}\';'.format(campos,name))==0:
                self.Missatge(self.tr(u"Error al buscar informacio del geoset.\n")+query.lastError().text())
                return
            while query.next():
                datos=query.value(0)
            if datos=={}:
                return
            datos=datos.replace('(','')
            datos=datos.replace(')','')
            datos=datos.split(',')
        
            #rellenar los campos de la ui
            self.dlg.lEgeosetinspireid.clear()
            self.dlg.lEgeosetinspireid.setText(datos[0]) #identificador conjunt
            
            #distribution + distribution void   
            if datos[1]=='': #consultar el distribution void
                self.dlg.CBdistnfo.setCurrentIndex(0) #lista a 0
                error,void=self.fromidtovoid(query,datos[2]) #distribution_void
                if error:
                    self.Missatge(self.tr(u"Error a la id distribution_void.\n"))
                    return
                self.dlg.CBdistnfo_void.setCurrentIndex(self.dlg.CBdistnfo_void.findText(void))
                
            else:            
                self.dlg.CBdistnfo_void.setCurrentIndex(0) #lista a 0
                error,nom=self.isinbd(query,'documentcitation','documentcitationid',datos[1],'name') #distribution id->name           
                if error <1:
                    self.Missatge(self.tr(u"Error al buscar citation from id.\n")+query.lastError().text())
                    return
                self.dlg.CBdistnfo.setCurrentIndex(self.dlg.CBdistnfo.findText(nom))

            
            #largework + largework void   
            self.dlg.lEgeosetlargework.clear()
            if datos[3]=='': #consultar el largework void
                self.dlg.lEgeosetlargework.setText('') 
                error,void=self.fromidtovoid(query,datos[4]) #distribution_void
                if error:
                    self.Missatge(self.tr(u"Error a la id distribution_void.\n"))
                    return
                self.dlg.CBlargework_void.setCurrentIndex(self.dlg.CBlargework_void.findText(void))
                
            else:            
                self.dlg.CBdistnfo_void.setCurrentIndex(0) #lista a 0
                self.dlg.lEgeosetlargework.setText(datos[3])             
           
            error,nom=self.isinbd(query,'geologiccollection','geologiccollectionid',datos[5],'name') #geocol id->name
            if error <1:
                self.Missatge(self.tr(u"Error al buscar geocol from id.\n")+query.lastError().text())
                return
            self.dlg.CBgeocoldades.setCurrentIndex(self.dlg.CBgeocoldades.findText(nom))
            
            error,nom=self.isinbd(query,'campaign','campaignid',datos[6],'name') #campaña id->name
            if error <1:
                self.Missatge(self.tr(u"Error al buscar campanya from id.\n")+query.lastError().text())
                return
            self.dlg.CBcampdades.setCurrentIndex(self.dlg.CBcampdades.findText(nom))
            
            if datos[7]!='':
                error,nom=self.isinbd(query,'documentcitation','documentcitationid',datos[7],'name') #citation id->name           
                if error <1:
                    self.Missatge(self.tr(u"Error al buscar citation from id.\n")+query.lastError().text())
                    return
                self.dlg.CBdoccitdades.setCurrentIndex(self.dlg.CBdoccitdades.findText(nom)) 
            else:
                self.dlg.CBdoccitdades.setCurrentIndex(0)
 
       
        
    def mod_geoset(self):
        '''
        Docstring: funcion que altera el registro en la tabla geoset con los nuevos datos del formulario
        '''
        #crear la query 
        db=self.conectardb
        query = QSqlQuery(db)
        
        #registro a modificar id geoset
        error,idegeoset=self.isinbd(query,'geophobjectset','inspireid',self.dlg.CBgeosetshow.currentText(),'geophobjectsetid')
        if error<1:
            self.Missatge(self.tr(u"Error al buscar geosetid from inspireid(list).\n")+query.lastError().text())
            return
        
        #distribution void solo si no existe distribution (metadatos)
        if self.dlg.CBdistnfo.currentText()=='': 
            distribuinfo=None
            void=self.dlg.CBdistnfo_void.currentText() #get from the  distribution combobox void text
            if void=='':
                self.Missatge(self.tr(u"El camp informe metadades esta buit. Indica el perque"))
                return True
            exist,distribuinfo_void = self.isinbd(query,'cl_voidtypevalue','voidtypevalue',void,'voidtypevalueid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el void ide"))
                return True
        else:
            exist,distribuinfo = self.isinbd(query,'documentcitation','name', #obtain citation id de metadates
                                       self.dlg.CBdistnfo.currentText(),'documentcitationid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar la id de les metedades (documentcitation)"))
                return True 
            distribuinfo_void=None
            
        #largework void solo si no existe largework (codigo ICGC)
        if self.dlg.lEgeosetlargework.text() =='': 
            largework=None
            void=self.dlg.CBlargework_void.currentText()
            if void=='':
                self.Missatge(self.tr(u"El camp codi projecte esta buit. Indica el perque"))
                return True
            exist,largework_void = self.isinbd(query,'cl_voidtypevalue','voidtypevalue',void,'voidtypevalueid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el void ide"))
                return True

        else:
            largework= self.dlg.lEgeosetlargework.text()
            largework_void=None
        
        
        #id geocol (projecte)
        if self.dlg.CBgeocoldades.currentText()=='':
            self.Missatge(self.tr(u"Error. Selecciona un projecte."))
            return
        else:
            exist,idgeocol = self.isinbd(query,'geologiccollection','name',
                                       self.dlg.CBgeocoldades.currentText(),'geologiccollectionid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el geologiccollection ide"))
                return
        
        #id campaign 
        if self.dlg.CBcampdades.currentText()=='':
            self.Missatge(self.tr(u"Error. Selecciona una campanya."))
            return
        else:
            exist,idcampaign = self.isinbd(query,'campaign','name',self.dlg.CBcampdades.currentText(),'campaignid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el campaign ide"))
                return
        
        #id citation
        if self.dlg.CBdoccitdades.currentText()=='':
            idcitation = None
        else:
            exist,idcitation = self.isinbd(query,'documentcitation','name', #obtain citation id
                                       self.dlg.CBdoccitdades.currentText(),'documentcitationid')
            if exist==0:
                self.Missatge(self.tr(u"Error al buscar el documentcitation ide"))
                return
       
        querytext='UPDATE {} SET inspireid=:1,distributioninfo=:2,distributioninfo_void=:3,largework=:4,'.format('geophobjectset')
        querytext=querytext+'largework_void=:5,geologiccollection=:6,campaign=:7,citation=:8 WHERE geophobjectsetid={};'.format(idegeoset)
        
        query.prepare('UPDATE {} SET inspireid=:1,distributioninfo=:2,distributioninfo_void=:3,largerwork=:4,largerwork_void=:5,geologiccollection=:6,campaign=:7,citation=:8 WHERE geophobjectset.geophobjectsetid={};'.format('geophobjectset',idegeoset))
        inspireid=self.dlg.lEgeosetinspireid.text()
        query.bindValue(':1',inspireid) #inspireid
        query.bindValue(':2',distribuinfo) #distribution info
        query.bindValue(':3',distribuinfo_void) #distributioninfo_void
        query.bindValue(':4',largework) #largework
        query.bindValue(':5',largework_void) #largework_void
        query.bindValue(':6',idgeocol) #geocol id (projecte)
        query.bindValue(':7',idcampaign) #campaign id
        query.bindValue(':8',idcitation)
        
        if query.exec_()==0:
            self.Missatge(self.tr(u"Error al modificar el registre de la geoset.\n")+query.lastError().text())
            return
        else: #si ha funcionado
        
            self.Missatge(self.tr(u"Taula geoset modifcada\n"),'Informacio')
            self.dlg.modgeoset.setEnabled(False) #ocultar otra vez el boton modificar
            self.dlg.modgeoset.setVisible(False)
            #borrar la entrada en la CBgeosetshow
            self.dlg.CBgeosetshow.removeItem(self.dlg.CBgeosetshow.findText(self.dlg.CBgeosetshow.currentText()))
            self.dlg.CBgeosetshow.addItems([self.dlg.lEgeosetinspireid.text()])
            return
        

# ----------------------------------------------------------------------------------

#++++++++++++++++++++ TABLE III FUNCTIONS +++++++++++++++++++++++++++++++++++++

    def show_campaign_info(self):
        '''
        Docstring: funcion que crea un mensaje donde muestra toda la info de la
        campaña seleccionada en el combobox
        '''
        
        start_time=time.time()
        
        db=self.conectardb
        query = QSqlQuery(db)
        registro=self.dlg.campainglist.currentText()
        geoset=self.dlg.dadeslist.currentText()
        if registro=='' or registro==None: #campaña vacia
            return
        if geoset=='' or geoset==None: #geoset vacia
            return
        
        campos='client,contractor'
        datos={}
        if query.exec_('SELECT ({0}) FROM campaign WHERE campaign.name=\'{1}\';'.format(campos,registro))==0:
            self.Missatge(self.tr(u"Error al buscar informacio de la campanya.\n")+query.lastError().text())
            return
        while query.next():
            datos=query.value(0)
        if datos=={}:
            return
        datos=datos.replace('(','')
        datos=datos.replace(')','')
        datos=datos.split(',')
        
        campos=campos.split(',')
        mensaje=''
        for i in range(len(campos)):
            mensaje=mensaje + str(campos[i])+': ' + str(datos[i]) + ' \n'
        
        mensaje='Nom de la campanya: ' + self.dlg.campainglist.currentText() +'\n'+mensaje
        mensaje='Dades de la campanya \n' + mensaje
        self.Missatge(self.tr(mensaje),'Informacio')
        
        #populate the list widget
        #obtain campaign id
        
        exist,idcampaign = self.isinbd(query,'campaign','name',self.dlg.campainglist.currentText(),
                                       'campaignid')
        if exist==0:
            self.Missatge(self.tr(u"Error al buscar el campaign ide"))
            return
        
        #obtain the geosetid
        orden='SELECT geophobjectsetid FROM geophobjectset WHERE campaign={} '.format(idcampaign)
        orden+='AND inspireid=\'{}\';'.format(geoset)
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error al consultar geoset de la campanya.\n")+query.lastError().text())
            return 
        idgeoset=[]
        while query.next():
            idgeoset.append(query.value(0))
            
        self.dlg.listWidget.clear()
        self.show_observationname(query,idcampaign,idgeoset)
        
        if os.isatty(1):
            print 'Informacion de la campaña seleccionada'    
            print '--- {} seconds ---'.format(time.time() - start_time)


    def show_observationname(self,query,idecamp,idgeoset):
        '''
        Docstring: llena el list widget con los diferentes tipos de observacion que hay en la tabla observationresult
        '''
        start_time=time.time()
        if query.exec_('SELECT name,date_init,date_end FROM log_obs WHERE '
            +'campaignid={} AND geosetid={}'.format(idecamp,idgeoset[0]))==0:  
            self.Missatge(self.tr(u"Error al consultar dades a log_obs.\n")+query.lastError().text())
            return
            
        observacion=[]; fecha_in=[]; fecha_end=[]     
        while query.next():
            observacion.append(query.value(0))
            fecha=query.value(1)
            fecha_in.append(fecha.toString('yyyyMM'))
            fecha=query.value(2)
            fecha_end.append(fecha.toString('yyyyMM'))
            
        for ind,obs in enumerate(observacion):
            self.dlg.listWidget.addItems([obs+'_'+fecha_in[ind]+'_'+fecha_end[ind]])            
     
        if os.isatty(1):
            print 'Mostrar los tipos de observaciones existentes'    
            print '--- {} seconds ---'.format(time.time() - start_time)
  
    def delete_observationname(self):
        '''
        Docstring: funcion que borra las entradas en la tabla que hacen referencia a un tipo de observacion
        Borraremos en cascada desde spatialsamplingfeature. Llamado solo desde la TAB III
        '''
        db=self.conectardb
        query = QSqlQuery(db)
        #obtener idcampaign y idgeoset
        campana=self.dlg.campainglist.currentText()
        geoset=self.dlg.dadeslist.currentText()
        
        idcamp=[] #id de la campaña
        orden='SELECT campaignid FROM campaign WHERE name=\'{}\';'.format(campana)
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error al buscar id de la campanya.\n")+query.lastError().text())
            return
        while query.next():
            idcamp.append(query.value(0))
        
        idgeoset=[] #id geoset seleccionado y asociado a la campaña
        orden='SELECT geophobjectsetid FROM geophobjectset WHERE campaign={} AND inspireid=\'{}\';'.format(idcamp[0],geoset)
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error al buscar id del geoset.\n")+query.lastError().text())
            return
        while query.next():
            idgeoset.append(query.value(0))        
        #******************************************
        
        if 'LOS' in self.dlg.listWidget.currentItem().text():
            #buscar las medidas relacionadas a este LOS
            nombre=self.dlg.listWidget.currentItem().text().split('_')
            coordenada=nombre[1]
            fechas=nombre[2]+'_'+nombre[3] #coordenada+fechainicio+fechafin
            datosaborrar=[]
            for i in range(self.dlg.listWidget.count()):
                textitem=self.dlg.listWidget.item(i).text()
                if (coordenada in textitem) and (fechas in textitem):
                    datosaborrar.append(textitem) #todas las medidas derivadas del LOS con las coordenadas y fechas adecuadas
            m = QMessageBox()
            m.setIcon(QMessageBox.Warning)
            m.setWindowTitle('Confirmar')
            m.setText('Confirmacio per esborrar l\'observacio: {}. Es una observacio tipus LOS.\n'.format(self.dlg.listWidget.currentItem().text())
            +'S\'esborraran totes les observacions derivades d\'aquest LOS. En total: {}.\n'.format(len(datosaborrar))
            +'Estas segur?')
            m.setStandardButtons(QMessageBox.Ok);
            m.addButton(QMessageBox.Cancel);
            m.setButtonText(QMessageBox.Ok,"Aceptar")
            m.setButtonText(QMessageBox.Cancel,"Cancelar")
            
            if m.exec_()==  QMessageBox.Ok:
                for nombre in datosaborrar:
                    #borrar en la base de datos
                    if self.delete_observation(query,nombre,idgeoset)==1:
                        return
                    #borrar el listwidget
                    item=self.dlg.listWidget.findItems(nombre,Qt.MatchRegExp)
                    self.dlg.listWidget.takeItem(self.dlg.listWidget.row(item[0]))

                self.Missatge(self.tr(u"Entrada esborrada\n"),'Informacio')
            return 
                
        else:
            
            m = QMessageBox()
            m.setIcon(QMessageBox.Warning)
            m.setWindowTitle('Confirmar')
            m.setText('Confirmacio per esborrar l\'observacio: {}. Estas segur?'.format(self.dlg.listWidget.currentItem().text()))
            m.setStandardButtons(QMessageBox.Ok);
            m.addButton(QMessageBox.Cancel);
            m.setButtonText(QMessageBox.Ok,"Aceptar")
            m.setButtonText(QMessageBox.Cancel,"Cancelar")
            if m.exec_()==  QMessageBox.Ok:
                if self.delete_observation(query,self.dlg.listWidget.currentItem().text(),idgeoset)==1:
                    return
                self.Missatge(self.tr(u"Entrada esborrada\n"),'Informacio')
                self.dlg.listWidget.takeItem(self.dlg.listWidget.currentRow())
            return
        

    def delete_observation(self,query,observacion,idgeoset): #idgeoset (el de la campaña no es necesario)
        '''
        Docstring: devuelve el rango de ides asocociados a la observacion que queremos borrar 
        de la tabla spatialsamplingfeature
        para 1 registro= las ides de spatialsampling=geophonject=samplingfeature
        Hemos de encontrar el numero de registros (las ides) para un tipo de medida en observation result
        input: MEDIDA_ZONA_fechain_fechaend
        ''' 
        start_time=time.time()
        sampfeat_inidate=observacion.split('_')[2]
        sampfeat_enddate=observacion.split('_')[3]
        medida_zona=observacion.split('_')[0]+'_'+observacion.split('_')[1]
        
        if os.isatty(1):
            print 'Borrando la observacion {} ...'.format(observacion) 
            
        orden='DELETE FROM spatialsamplingfeature where spatialsamplingid IN ( '
        orden+='(SELECT spatialsamplingid FROM spatialsamplingfeature WHERE geophobjectset={}) '.format(idgeoset[0])
        orden+='INTERSECT '
        orden+='(select spatialsamplingfeature from samplingfeature where samplingfeatureid IN '
        orden+='(select foo.idssamp from '
        orden+='(SELECT samplingfeatureid as idssamp FROM samplingfeature WHERE ' 
        orden+='validtime_begin=to_date(\'{}\',\'YYYYMMDD\') AND validtime_end=to_date(\'{}\',\'YYYYMMDD\') '.format(sampfeat_inidate,sampfeat_enddate)
        orden+='intersect '
        orden+='select samplingfeature from samplingresult where samplingresult.name LIKE \'{}%\') as foo)));'.format(medida_zona)
        
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error a l'esborrar l' observacio. \n")+query.lastError().text())
            return True 
   
        #borramos la observacion de la tabla log_obs
        orden='DELETE FROM log_obs WHERE name=\'{}\' AND '.format(medida_zona)
        orden+='geosetid={} AND '.format(idgeoset[0])
        orden+='date_init=to_date(\'{}\',\'YYYYMMDD\') AND '.format(sampfeat_inidate)
        orden+='date_end=to_date(\'{}\',\'YYYYMMDD\');'.format(sampfeat_enddate)
        if query.exec_(orden)==0:
            self.Missatge(self.tr(u"Error l'esborrar la taula log_obs \n")+query.lastError().text())
            return True   
        
        if os.isatty(1):
            print 'Borrado todo para la observacion {}'.format(observacion)    
            print '--- {} seconds ---'.format(time.time() - start_time)        
        
        return False


    def show_obsinfo(self):
        '''
        Docstring: funcion asociada al boton de info de la observacion, devuelve mensaje con algunos campos interesantes
        '''
        if self.dlg.listWidget.currentItem()==None:
             self.Missatge(self.tr(u"No hi ha cap observacio seleccionada"),'Informacio')
             return
        else:
            db=self.conectardb
            query = QSqlQuery(db)
            idgeoset=self.obtain_geosetid(query,self.dlg.listWidget.currentItem().text())
            campos=['inspireid','largerwork','geologiccollection','citation','process']
            datos=[]
            for consulta in campos:
                if query.exec_('SELECT public.geophobjectset.{} FROM public.geophobjectset WHERE public.geophobjectset.geophobjectsetid={};'.format(consulta,idgeoset))==0:
                    self.Missatge(self.tr(u"Error al buscar informacio de l\'observacion\n")+query.lastError().text())
                    return 
                while query.next():
                    datos.append(query.value(0))
            mensaje='Identificador: '+str(datos[0])+'\n'
            mensaje=mensaje + 'Codi projecte ICGC: ' + str(datos[1])+'\n'
            
            if query.exec_('SELECT public.geologiccollection.inspireid FROM public.geologiccollection WHERE public.geologiccollection.geologiccollectionid={};'.format(datos[2]))==0:
                self.Missatge(self.tr(u"Error al buscar informacio de l\'observacion\n")+query.lastError().text())
                return 
            while query.next():
                mensaje=mensaje + 'Codi projecte: ' + str(query.value(0)) + '\n'
                    
            if query.exec_('SELECT public.documentcitation.name FROM public.documentcitation WHERE public.documentcitation.documentcitationid={};'.format(datos[3]))==0:
                    self.Missatge(self.tr(u"Error al buscar informacio de l\'observacion\n")+query.lastError().text())
                    return 
            while query.next():
                mensaje=mensaje + 'Informe del projecte:  ' + str(query.value(0)) + '\n'
            
            if query.exec_('SELECT public.processes.name FROM public.processes WHERE public.processes.processesid={};'.format(datos[4]))==0:
                self.Missatge(self.tr(u"Error al buscar informacio de l\'observacion\n")+query.lastError().text())
                return 
            while query.next():
                mensaje=mensaje + 'Nom del processat:  ' + str(query.value(0)) + '\n'
            
            mensaje='Informacio sobre l\'observacio: {}\n'.format(self.dlg.listWidget.currentItem().text())+mensaje
            self.Missatge(self.tr(mensaje),'Informacio')
            
            
    def delete_campaign(self):
        db=self.conectardb
        query = QSqlQuery(db)
        registro=self.dlg.campainglist.currentText()
        m = QMessageBox()
        m.setIcon(QMessageBox.Warning)
        m.setWindowTitle('Confirmar')
        m.setText('Confirmacio per esborrar la campanya: {}. Estas segur?'.format(registro))
        m.setStandardButtons(QMessageBox.Ok);
        m.addButton(QMessageBox.Cancel);
        m.setButtonText(QMessageBox.Ok,"Aceptar")
        m.setButtonText(QMessageBox.Cancel,"Cancelar")
        if m.exec_()==  QMessageBox.Ok:
            start_time=time.time()
            
            if query.exec_('SELECT campaignid FROM public.campaign WHERE public.campaign.name=\'{}\';'.format(registro))==0:
                self.Missatge(self.tr(u"Error al buscar el nom de la campanya per esborrarlan.\n")+query.lastError().text())
                return
            while query.next():
                idcamp=query.value(0)
            
            #borramos los procesados que tiene dependencia del geoset
            if os.isatty(1):
                print 'Borrando procesados asociados...'  
            orden='DELETE FROM processes WHERE geophobjectset IN '
            orden='(SELECT geophobjectsetid FROM geophobjectset WHERE campaign={})'.format(idcamp)            
            if query.exec_(orden)==0:
                self.Missatge(self.tr(u"Error al esborrar els processats.\n")+query.lastError().text())
                return
            if os.isatty(1):
                print 'Procesados borrados.' 
                
            #borramos la tabla log_obs
            if os.isatty(1):
                print 'Borrando campaña de la tabla log_obs...'
            orden='DELETE FROM log_obs WHERE campaignid={};'.format(idcamp) 
            if query.exec_(orden)==0:
               self.Missatge(self.tr(u"Error al esborrar la campanya de la taula log_obs.\n")+query.lastError().text())
               return 
            if os.isatty(1):
                print 'Campaña en la tabla log_obs borrada.'
                
            #borramos geophobjectset (y borra todo lo que tiene por debajo)
            if os.isatty(1):
                print 'Borrando geosets de la campaña en la tabla geoset...'
            orden='DELETE FROM geophobjectset WHERE campaign={};'.format(idcamp)
            if query.exec_(orden)==0:
                self.Missatge(self.tr(u"Error al borrar la taula geophobjset.\n")+query.lastError().text())
                return
            if os.isatty(1):
                print 'Geosets de la campaña borrados.'
            self.dlg.CBdadesgeoset.clear()
            
            #limpiar la tabla campaña
            if os.isatty(1):
                print 'Borrando campaña de la tabla campaign...'
            orden='DELETE FROM campaign WHERE campaignid={};'.format(idcamp)
            if query.exec_(orden) ==0:
                self.Missatge(self.tr(u"Error al borrar la taula campanya.\n")+query.lastError().text())
            else:
                self.Missatge(self.tr('Campanya: {} borrada'.format(registro)),'Informacio')
                self.dlg.campainglist.removeItem(self.dlg.campainglist.findText(registro))
                self.dlg.CBdadescamp.removeItem(self.dlg.CBdadescamp.findText(registro))
                self.dlg.CBcamp.removeItem(self.dlg.CBcamp.findText(registro))
                self.dlg.CBcampdades.removeItem(self.dlg.CBcampdades.findText(registro))
                self.dlg.listWidget.clear()
               
            if os.isatty(1):
                print 'Campaña borrada {}'.format(registro)    
                print '--- {} seconds ---'.format(time.time() - start_time)   
            
        else:
            pass #cancel option, do nothing
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


#++++++++++++++++++++++++++++++++++ TABLE IV FUNCTIONS ++++++++++++++++++++++++
 
    def cargar_csv(self):
        #choose directory path
        self.dlg.lEshppath.setText('')
        name=QFileDialog().getOpenFileName(
            self.dlg, self.tr(u'Selecció arxiu .csv'),'C:\Users')
        if name[-4:]!='.csv':
            self.Missatge(self.tr(u"Arxiu no es .csv!\n"))
            return
        else:
            self.dlg.lEshppath.setText(name)
            uri='file:///'+name+'?type=csv&delimiter=,%5Ct;&xField=UTM_X&yField=UTM_Y&spatialIndex=no&subsetIndex=no&watchFile=no'
            lyr = QgsVectorLayer(uri,name.split('/')[-1],'delimitedtext')
            if not lyr:
                self.Missatge(self.tr(u"Error al carregar les dades\n"))
                return
            print lyr.isValid()

            QgsMapLayerRegistry.instance().addMapLayer(lyr)
            
                
    def carregarpunts(self):
        self.dlg.lEnselected.clear()
        layer=self.iface.activeLayer()
        if layer ==None: #no capa activa
             self.Missatge(self.tr('No hi ha una capa activa!'))
             return
        self.dlg.lEnselected.setText(str(layer.selectedFeatureCount()))
        if layer.selectedFeatureCount()==0 or layer.selectedFeatureCount()>4:
            self.Missatge(self.tr('Massa punts seleccionats!'))
            return 
            
        points=layer.selectedFeatures()
        #date keys
        keys=[]
        for field in layer.pendingFields():
            keys.append(field.name())
        
        indexdata=keys.index('EFF_AREA')+1
        dates=keys[indexdata:]
        x = [dt.datetime.strptime(d.replace('D',''),'%Y%m%d').date() for d in dates]
        
        #obtain data
        datos=[]
        nombre=[]
        vx=[];vcoehr=[];
        for feat in points:
            elemento=[]
            nombre.append(feat[0])
            vx.append(feat[5])
            vcoehr.append(feat[6])
            for fecha in dates:
                elemento.append(feat[fecha])
            datos.append(elemento)
        
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator())
        plt.hold(True)
        
        col=['coral','blue','red','green']        
        
        for i in range(len(datos)):
            plt.scatter(x,datos[i],marker='s',color=col[i],label=nombre[i]+' vel:%.4f vel_stdv:%.4f' %(vx[i],vcoehr[i]) )
            if self.dlg.cbline.isChecked():
                z=np.polyfit(mdates.date2num(x),datos[i],1)
                line=np.poly1d(z)
                xx=np.linspace(mdates.date2num(x).min(),mdates.date2num(x).max(),100)
                dd=mdates.num2date(xx)
                plt.plot(dd,line(xx),color=col[i])
            if self.dlg.cbpol.isChecked():   
                z=np.polyfit(mdates.date2num(x),datos[i],6)
                spline=np.poly1d(z)
                xx=np.linspace(mdates.date2num(x).min(),mdates.date2num(x).max(),100)
                dd=mdates.num2date(xx)
                plt.plot(dd,spline(xx),color=col[i])
            
            
            
        dates=['201601','201602','201604','201606','201608','201610','201612','201701']
        xlab = [dt.datetime.strptime(d,'%Y%m').date() for d in dates]
        
        xlim=[dt.datetime.strptime('201512'+'01','%Y%m%d').date(),dt.datetime.strptime('201701'+'31','%Y%m%d').date()]

        plt.gcf().autofmt_xdate()
        plt.xticks(xlab,rotation=45)
        plt.xlabel('Date',FontSize=16)
        plt.ylabel('mm', Fontsize=16)
        plt.xlim(xlim)
        chartbox=plt.gca().get_position()
        plt.ylim([plt.gca().get_ylim()[0]-2,plt.gca().get_ylim()[1]+2])

        coef=1.-0.05*layer.selectedFeatureCount()
        altura=1.4+0.1*(layer.selectedFeatureCount()-4)
        plt.gca().set_position([chartbox.x0, chartbox.y0, chartbox.width, chartbox.height*coef])
        plt.legend(loc='upper right',bbox_to_anchor=(0.9,altura),prop={'size': 10})
        plt.grid()
        plt.show()
        
