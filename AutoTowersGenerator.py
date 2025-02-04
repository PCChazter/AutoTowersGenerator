import json
import os
import tempfile

# Import the correct version of PyQt
try:
    from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, pyqtProperty
    PYQT_VERSION = 6
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, pyqtProperty
    PYQT_VERSION = 5

from cura.CuraApplication import CuraApplication
from cura.Scene.CuraSceneNode import CuraSceneNode
from UM.Application import Application
from UM.Extension import Extension
from UM.Logger import Logger
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry
from UM.Scene.Camera import Camera

from . import MeshImporter
from .OpenScadInterface import OpenScadInterface
from .OpenScadJob import OpenScadJob

from .Controllers.BedLevelPatternContoller import BedLevelPatternController
from .Controllers.FanTowerController import FanTowerController
from .Controllers.FlowTowerController import FlowTowerController
from .Controllers.RetractTowerController import RetractTowerController
from .Controllers.SpeedTowerController import SpeedTowerController
from .Controllers.TempTowerController import TempTowerController



class AutoTowersGenerator(QObject, Extension):
    _pluginName = 'AutoTowersGenerator'

    _gcodeProcessedMarker = ';Post-processed by the AutoTowersGenerator plugin'

    # Add additional controller classes to this list
    _controllerClasses = [BedLevelPatternController, FanTowerController, FlowTowerController, RetractTowerController, SpeedTowerController, TempTowerController]



    def __init__(self):
        QObject.__init__(self)
        Extension.__init__(self)

        # Initialize the plugin settings
        self._pluginSettings = {}

        # Keep track of the post-processing callback and the node added by the OpenSCAD import
        self._towerControllerPostProcessingCallback = None
        self._importedNode = None

        # Keep track of whether a model has been generated and is in the scene
        self._autoTowerNode = None
        self._autoTowerOperation = None

        # Keep track of the currently active tower controller
        self._currentTowerController = None

        # Update the view when the main window is changed so the "remove" button is always visible when enabled
        CuraApplication.getInstance().mainWindowChanged.connect(self._displayRemoveAutoTowerButton)

        # Finish initializing the plugin after Cura is fully ready
        CuraApplication.getInstance().pluginsLoaded.connect(self._onPluginsLoadedCallback)



    @property
    def _pluginPath(self)->str:
        ''' Returns the path to the plugin directory '''

        return PluginRegistry.getInstance().getPluginPath(self.getPluginId())



    @property
    def _openScadSourcePath(self)->str:
        ''' Returns the path to the OpenSCAD source models'''

        return os.path.join(self._pluginPath, 'Resources', 'OpenScad')


    
    @property
    def _qmlPath(self)->str:
        ''' Returns the path to where the QML dialog files directory '''

        return os.path.join(self._pluginPath, 'Resources', 'QML', f'QT{PYQT_VERSION}')



    @property
    def _stlPath(self)->str:
        ''' Returns the path where STL files are stored '''

        return os.path.join(self._pluginPath, 'Resources', 'STL')



    @property
    def _pluginSettingsFilePath(self)->str:
        ''' Returns the path of the plugins settings file '''

        return os.path.join(self._pluginPath, 'Resources', 'settings.json')



    _cachedRemoveModelsButton = None

    @property
    def _removeAutoTowerButton(self)->QObject:
        ''' Returns the button used to remove the Auto Tower from the scene '''

        if self._cachedRemoveModelsButton is None:
            self._cachedRemoveModelsButton = self._createDialog('RemoveModelsButton.qml')
        return self._cachedRemoveModelsButton



    _cachedPluginSettingsDialog = None

    @property
    def _pluginSettingsDialog(self)->QObject:
        ''' Returns the settings dialog '''

        if self._cachedPluginSettingsDialog is None:
            self._cachedPluginSettingsDialog = self._createDialog('PluginSettingsDialog.qml')
        return self._cachedPluginSettingsDialog



    _cachedSettingsVerificationDialog = None

    @property
    def _settingsVerificationDialog(self)->QObject:
        ''' Returns a dialog asking the user whether they want to continue with incompatible settings '''

        if self._cachedSettingsVerificationDialog is None:
            self._cachedSettingsVerificationDialog = self._createDialog('SettingsVerificationDialog.qml')
        return self._cachedSettingsVerificationDialog




    _cachedWaitDialog = None

    @property
    def _waitDialog(self)->QObject:
        ''' Returns the dialog used to tell the user that generating a model may take a long time '''

        if self._cachedWaitDialog is None:
            self._cachedWaitDialog = self._createDialog('WaitDialog.qml')
        return self._cachedWaitDialog



    _cachedOpenScadInterface = None
    @property
    def _openScadInterface(self)->OpenScadInterface:
        ''' Provides lazy instantiation of the OpenScad interface '''

        if self._cachedOpenScadInterface is None:
            self._cachedOpenScadInterface = OpenScadInterface()

        return self._cachedOpenScadInterface



    autoTowerGeneratedChanged = pyqtSignal()
    @pyqtProperty(bool, notify=autoTowerGeneratedChanged)
    def autoTowerGenerated(self)->bool:
        ''' Used to show or hide the button for removing the generated Auto Tower '''

        return not self._autoTowerOperation is None



    @pyqtProperty(str)
    def pluginVersion(self)->str:
        ''' Returns the plugin's version number '''

        return self.getVersion()



    _openScadPathSetting = ''

    _openScadPathSettingChanged = pyqtSignal()
    
    def setOpenScadPathSetting(self, value)->None:
        self._openScadPathSetting = value
        self._openScadPathSettingChanged.emit()

    @pyqtProperty(str, notify=_openScadPathSettingChanged, fset=setOpenScadPathSetting)
    def openScadPathSetting(self)->str:
        return self._openScadPathSetting



    _displayOnLcdSetting = True

    _displayOnLcdSettingChanged = pyqtSignal()

    def setDisplayOnLcdSetting(self, value)->None:
        self._displayOnLcdSetting = value
        self._displayOnLcdSettingChanged.emit()

    @pyqtProperty(bool, notify=_displayOnLcdSettingChanged, fset=setDisplayOnLcdSetting)
    def displayOnLcdSetting(self)->bool:
        return self._displayOnLcdSetting



    @pyqtSlot()
    def removeButtonClicked(self)->None:
        ''' Called when the remove button is clicked to remove the generated Auto Tower from the scene'''

        # Remove the tower
        self._removeAutoTower('The Auto Tower model and its associated post-processing has been removed')



    @pyqtSlot()
    def pluginSettingsModified(self)->None:
        ''' Saves plugin settings to a json file so they persist between sessions '''

        # Send the new OpenScad path to the OpenScad Interface
        self._openScadInterface.SetOpenScadPath(self.openScadPathSetting)

        # Warn the user if the OpenScad path is not valid
        if not self._openScadInterface.OpenScadPathValid:
            message = f'The OpenScad path "{self._openScadInterface.OpenScadPath}" is not valid'
            Message(message, title=self._pluginName).show()

        # Create a settings dictionary to dump to the settings file
        pluginSettings = {
            'openscad path': self.openScadPathSetting,
            'display on lcd': self.displayOnLcdSetting,
        }

        # Save the settings to the settings file
        with open(self._pluginSettingsFilePath, 'w') as settingsFile:
            json.dump(pluginSettings, settingsFile)

        # Remove the tower to force it to be regenerated
        self._removeAutoTower('The AutoTower was removed because plugin settings were changed')



    def _loadPluginSettings(self)->None:
        ''' Load plugin settings from the settings.json file  '''

        try:
            # Load settings from the settings file, if it exists
            with open(self._pluginSettingsFilePath, 'r') as settingsFile:
                pluginSettings = json.load(settingsFile)

            # Forward the OpenScad path to the OpenScadInterface object
            self.setOpenScadPathSetting(pluginSettings['openscad path'])
            self._openScadInterface.SetOpenScadPath(self.openScadPathSetting)

            # Read in the 'display to LCD' setting
            self.setDisplayOnLcdSetting(pluginSettings['display on lcd'])

        except (FileNotFoundError, KeyError):
            pass



    _cachedControllerTable = {}
    def _retrieveTowerController(self, ControllerClass):
        ''' Provides lazy instantiation of the tower controllers '''
    
        if not ControllerClass in self._cachedControllerTable:
            self._cachedControllerTable[ControllerClass] = ControllerClass(self._qmlPath, self._stlPath, self._loadStlCallback, self._generateAndLoadStlCallback)
        return self._cachedControllerTable[ControllerClass]



    def _initializeMenu(self)->None:
        # Add a menu for this plugin
        self.setMenuName('Auto Towers')

        dividerCount = 0

        # Add menu entries for each tower controller
        for controllerClass in self._controllerClasses:
            controller = self._retrieveTowerController(controllerClass)

            # Add a divider
            if dividerCount >= 0:
                self.addMenuItem(' ' * dividerCount, lambda:None)
            dividerCount += 1

            # Iterate over each of the tower controller presets
            for presetName in controller.presetNames:
                self.addMenuItem(f'{controller.name} ({presetName})', lambda controllerClass=controllerClass, presetName=presetName: self._generateAutoTower(controllerClass, presetName))

            # Add a custom tower entry
            self.addMenuItem(f'{controller.name} (Custom)', lambda controllerClass=controllerClass: self._generateAutoTower(controllerClass))

        # Add a menu item for modifying plugin settings
        self.addMenuItem(' ' * dividerCount, lambda: None)
        dividerCount += 1
        self.addMenuItem('Settings', lambda: self._displayPluginSettingsDialog())



    def _generateAutoTower(self, controllerClass, presetName=''):
        ''' Verifies print settings and generates the requested auto tower '''

        self._currentTowerController = self._retrieveTowerController(controllerClass)

        # Allow the tower controller to update Cura's settings to ensure it can be generated correctly
        recommendedSettings = self._currentTowerController.checkPrintSettings()
        if len(recommendedSettings) > 0:
            message = '\n'.join([f'\tSet {entry[0]} to {entry[1]}' for entry in recommendedSettings])
            message = 'For best results, the following setting changes are recommended:' + message
            Message(message).show()

        # Custom auto towers cannot be generated unless OpenScad is correctly installed and configured
        openscad_path_is_valid = self._openScadInterface.OpenScadPathValid
        if presetName == '' and not openscad_path_is_valid:
            Logger.log('d', f'The openScad path "{self._openScadInterface.OpenScadPath}" is invalid')
            message = 'This functionality relies on OpenSCAD, which is not installed or configured correctly\n'
            message += 'Please ensure OpenSCAD is installed (openscad.org) and that its path has been set correctly in this plugin\'s settings\n'
            Message(message, title=self._pluginName).show()
            return

        self._currentTowerController.generate(presetName)



    def _removeAutoTower(self, message = None)->None:
        ''' Removes the generated Auto Tower and post-processing callbacks '''

        # Display the requested message
        if message != None:
            Message(message, title=self._pluginName).show()

        try:
            # Remove the Auto Tower itself
            if not self._autoTowerOperation is None:
                self._autoTowerOperation.undo()
        except Exception as e:
            message = f'Error: {e}'
            Message(message).show()
            Logger.log('e', message)

        try:
            # Remove the post-processing callback
            self._towerControllerPostProcessingCallback = None
            Application.getInstance().getOutputDeviceManager().writeStarted.disconnect(self._postProcessCallback)
        except Exception as e:
            #Logger.log('e', e)
            pass

        try:
            # Stop listening for machine changes
            CuraApplication.getInstance().getMachineManager().globalContainerChanged.disconnect(self._onMachineChanged)
        except Exception as e:
            #Logger.log('e', e)
            pass

        try:
            # Stop listening for settings changes
            CuraApplication.getInstance().getMachineManager().activeMachine.propertyChanged.disconnect(self._onPrintSettingChanged)
        except Exception as e:
            #Logger.log('e', e)
            pass

        try:
            # Stop listening for node changes
            CuraApplication.getInstance().getController().getScene().getRoot().childrenChanged.disconnect(self._onSceneChanged)
        except Exception as e:
            #Logger.log('e', e)
            pass

        # Clear the job name
        CuraApplication.getInstance().getPrintInformation().setJobName('')

        # Indicate that there is no longer an Auto Tower in the scene
        self._autoTowerOperation = None
        self.autoTowerGeneratedChanged.emit()



    def _createDialog(self, qml_filename)->QObject:
        ''' Creates a dialog object from a QML file name 
            The QML file is assumed to be in the GUI directory             
            Returns a dialog object, with this object assigned as the "manager" '''

        qml_file_path = os.path.join(self._qmlPath, qml_filename)
        dialog = Application.getInstance().createQmlComponent(qml_file_path, {'manager': self})
        return dialog



    def _displayRemoveAutoTowerButton(self)->None:
        ''' Adds a button to Cura's window to remove the Auto Tower '''

        CuraApplication.getInstance().addAdditionalComponent('saveButton', self._removeAutoTowerButton)



    def _displayPluginSettingsDialog(self)->None:
        ''' Prepares and displays the plugin settings dialog '''

        # Update the OpenScad path from the OpenScad interface
        self.setOpenScadPathSetting(self._openScadInterface.OpenScadPath)

        self._pluginSettingsDialog.show()



    def _generateAndLoadStlCallback(self, towerName, openScadFilename, openScadParameters, postProcessingCallback)->None:
        ''' This callback is called by the tower model controller after a tower has been configured to generate an STL model from an OpenSCAD file '''

        # This could take up to a couple of minutes...
        self._waitDialog.show()
        CuraApplication.getInstance().processEvents() # Allow Cura to update itself periodically through this method

        # Remove all models from the scene
        CuraApplication.getInstance().deleteAll()
        CuraApplication.getInstance().processEvents()
        
        # Compile the STL file name
        openScadFilePath = os.path.join(self._openScadSourcePath, openScadFilename)
        stlFilename = 'custom_autotower.stl'
        stlOutputDir = tempfile.TemporaryDirectory()
        stlFilePath = os.path.join(stlOutputDir.name, stlFilename)

        # Generate the STL file
        # Since it can take a while to generate the STL file, do it in a separate thread to allow the GUI to remain responsive
        job = OpenScadJob(self._openScadInterface, openScadFilePath, openScadParameters, stlFilePath)
        job.run()

        # Wait for OpenSCAD to finish
        # This should probably be done by having a function called when the job finishes...
        while (job.isRunning()):
            pass

        # Make sure the STL file was generated
        if os.path.isfile(stlFilePath) == False:
            errorMessage = f'Failed to generate "{stlFilePath}" from "{openScadFilename}":\n{self._openScadInterface.errorMessage}'
            Logger.log('e', errorMessage)
            Message(errorMessage, title=self._pluginName).show()
            self._waitDialog.hide()
            return

        # Import the STL file into the scene
        self._importStl(towerName, stlFilePath, postProcessingCallback)



    def _importStl(self, towerName, stlFilePath, postProcessingCallback)->None:
        ''' Imports an STL file into the scene '''

        # Remove all models from the scene
        self._removeAutoTower()
        CuraApplication.getInstance().deleteAll()
        CuraApplication.getInstance().processEvents()

        # Import the STL file into the scene
        self._autoTowerOperation = MeshImporter.ImportMesh(stlFilePath, name=self._pluginName)
        CuraApplication.getInstance().processEvents()

        # Register the post-processing callback for this particular tower
        Application.getInstance().getOutputDeviceManager().writeStarted.connect(self._postProcessCallback)
        self._towerControllerPostProcessingCallback = postProcessingCallback

        # The dialog is no longer needed
        self._waitDialog.hide()

        # Rename the print job
        CuraApplication.getInstance().getPrintInformation().setJobName(towerName)

        # Register that the Auto Tower has been generated
        self.autoTowerGeneratedChanged.emit()

        # Remove the model if the selected machine (printer) is changed
        CuraApplication.getInstance().getMachineManager().globalContainerChanged.connect(self._onMachineChanged)

        # Remove the model if critical print settings (settings that are important for the AutoTower) are changed
        CuraApplication.getInstance().getMachineManager().activeMachine.propertyChanged.connect(self._onPrintSettingChanged)

        # Remove the model if it is deleted or another model is added to the scene
        CuraApplication.getInstance().getController().getScene().getRoot().childrenChanged.connect(self._onSceneChanged)



    def _onMachineChanged(self)->None:
        ''' Listen for machine changes made after an Auto Tower is generated 
            In this case, the Auto Tower needs to be removed and regenerated '''

        self._removeAutoTower('The Auto Tower was removed because the active machine was changed')



    def _onPrintSettingChanged(self, settingKey, propertyName)->None:
        ''' Listen for setting changes made after an Auto Tower is generated '''

        # Remove the tower in response to changes to critical print settings
        if not self._currentTowerController is None:
            if settingKey in self._currentTowerController.criticalSettingsList:
                settingLabel = CuraApplication.getInstance().getMachineManager().activeMachine.getProperty(settingKey, 'label')
                self._removeAutoTower(f'The Auto Tower was removed because the Cura setting "{settingLabel}" has changed since the tower was generated')



    def _onPluginsLoadedCallback(self)->None:
        ''' Called after plugins have been loaded
            Iniializing here means that Cura is fully ready '''

        self._loadPluginSettings()
        self._initializeMenu()



    def _onSceneChanged(self, node)->None:
        # If the AutoTower node no longer exists, then clean up
        AutoTowerNodes = [child for child in node.getChildren() if child.getName() == self._pluginName]
        if len(AutoTowerNodes) <= 0:
            self._removeAutoTower()



    def _loadStlCallback(self, towerName, stlFilePath, postProcessingCallback)->None:
        ''' This callback is called by the tower model controller if a preset tower is requested '''

        # If the file does not exist, display an error message
        if os.path.isfile(stlFilePath) == False:
            errorMessage = f'The STL file "{stlFilePath}" does not exist'
            Logger.log('e', errorMessage)
            Message(errorMessage, title = self._pluginName).show()
            return

        # Import the STL file into the scene
        self._importStl(towerName, stlFilePath, postProcessingCallback)



    def _postProcessCallback(self, output_device)->None:
        ''' This callback is called just before gcode is generated for the model 
            (this happens when the sliced model is sent to the printer or a file '''
        
        # Retrieve the g-code
        scene = Application.getInstance().getController().getScene()

        try:
            # Proceed if the g-code is valid
            gcode_dict = getattr(scene, 'gcode_dict')
        except AttributeError:
            # If there is no g-code, there's nothing more to do
            return

        try:
            # Retrieve the g-code for the current build plate
            active_build_plate_id = CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate
            gcode = gcode_dict[active_build_plate_id]
        except (TypeError, KeyError):
            # If there is no g-code for the current build plate, there's nothing more to do
            return

        try:
            # Proceed if the g-code has not already been post-processed
            if self._gcodeProcessedMarker not in gcode[0]:

                # Mark the g-code as having been post-processed
                gcode[0] = gcode[0] + self._gcodeProcessedMarker + '\n'

                # Call the tower controller post-processing callback to modify the g-code
                gcode = self._towerControllerPostProcessingCallback(gcode, self.displayOnLcdSetting)

                Message('AutoTowersGenerator post-processing completed', title=self._pluginName).show()

        except IndexError:
            return
        