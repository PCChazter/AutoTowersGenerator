import os
import math

# Import the correct version of PyQt
try:
    from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, pyqtProperty
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, pyqtProperty

from cura.CuraApplication import CuraApplication

from UM.Application import Application
from UM.Logger import Logger

from .ControllerBase import ControllerBase

# Import the script that does the actual post-processing
from ..Postprocessing import TempTower_PostProcessing



class TempTowerController(ControllerBase):
    _openScadFilename = 'temptower.scad'
    _qmlFilename = 'TempTowerDialog.qml'

    _presetsTable = {
        'ABA': {
            'filename': 'temptower aba.stl',
            'start value': 260,
            'change value': -5,
        },

        'ABS': {
            'filename': 'temptower abs.stl',
            'start value': 250,
            'change value': -5,
        },

        'Nylon': {
            'filename': 'temptower nylon.stl',
            'start value': 260,
            'change value': -5,
        },

        'PC': {
            'filename': 'temptower pc.stl',
            'start value': 310,
            'change value': -5,
        },

        'PETG': {
            'filename': 'temptower petg.stl',
            'start value': 250,
            'change value': -5,
        },

        'PLA': {
            'filename': 'temptower pla.stl',
            'start value': 230,
            'change value': -5,
        },

        'PLA+': {
            'filename': 'temptower pla+.stl',
            'start value': 230,
            'change value': -5,
        },

        'TPU': {
            'filename': 'temptower tpu.stl',
            'start value': 230,
            'change value': -5,
        },
    }

    _criticalPropertiesTable = {
        'adaptive_layer_height_enabled': ('global', False),
        'layer_height': ('global', None),
        'meshfix_union_all_remove_holes': ('extruder', False),
        'support_enable': ('global', False),
    }

    _nominalBaseHeight = 0.8
    _nominalSectionHeight = 8.0



    def __init__(self, guiPath, stlPath, loadStlCallback, generateAndLoadStlCallback):
        super().__init__("Temp Tower", guiPath, stlPath, loadStlCallback, generateAndLoadStlCallback, self._openScadFilename, self._qmlFilename, self._presetsTable, self._criticalPropertiesTable)



    # The starting temperature value for the tower
    _startTemperatureStr = '220'

    startTemperatureStrChanged = pyqtSignal()
    
    def setStartTemperatureStr(self, value)->None:
        self._startTemperatureStr = value
        self.startTemperatureStrChanged.emit()

    @pyqtProperty(str, notify=startTemperatureStrChanged, fset=setStartTemperatureStr)
    def startTemperatureStr(self)->str:
        return self._startTemperatureStr



    # The ending temperature value for the tower
    _endTemperatureStr = '180'

    endTemperatureStrChanged = pyqtSignal()
    
    def setEndTemperatureStr(self, value)->None:
        self._endTemperatureStr = value
        self.endTemperatureStrChanged.emit()

    @pyqtProperty(str, notify=endTemperatureStrChanged, fset=setEndTemperatureStr)
    def endTemperatureStr(self)->str:
        return self._endTemperatureStr



    # The amount to change the temperature between tower sections
    _temperatureChangeStr = '-5'

    temperatureChangeStrChanged = pyqtSignal()
    
    def setTemperatureChangeStr(self, value)->None:
        self._temperatureChangeStr = value
        self.temperatureChangeStrChanged.emit()

    @pyqtProperty(str, notify=temperatureChangeStrChanged, fset=setTemperatureChangeStr)
    def temperatureChangeStr(self)->str:
        return self._temperatureChangeStr



    # The material label to add to the tower
    _towerLabelStr = ''

    towerLabelStrChanged = pyqtSignal()
    
    def setMaterialLabelStr(self, value)->None:
        self._towerLabelStr = value
        self.towerLabelStrChanged.emit()

    @pyqtProperty(str, notify=towerLabelStrChanged, fset=setMaterialLabelStr)
    def towerLabelStr(self)->str:
        return self._towerLabelStr



    # The description to carve up the side of the tower
    _towerDescriptionStr = 'TEMPERATURE'

    towerDescriptionStrChanged = pyqtSignal()
    
    def setTowerDescriptionStr(self, value)->None:
        self._towerDescriptionStr = value
        self.towerDescriptionStrChanged.emit()

    @pyqtProperty(str, notify=towerDescriptionStrChanged, fset=setTowerDescriptionStr)
    def towerDescriptionStr(self)->str:
        return self._towerDescriptionStr



    def _loadPreset(self, presetName)->None:
        ''' Load a preset tower '''
        # Load the preset table
        try:
            presetTable = self._presetsTable[presetName]
        except KeyError:
            Logger.log('e', f'A TempTower preset named "{presetName}" was requested, but has not been defined')
            return

        # Load the preset's file name
        try:
            stlFileName = presetTable['filename']
        except KeyError:
            Logger.log('e', f'The "filename" entry for TempTower preset table "{presetName}" has not been defined')
            return

        # Load the preset's starting temperature
        try:
            self._startTemperature = presetTable['start value']
        except KeyError:
            Logger.log('e', f'The "start value" for TempTower preset table "{presetName}" has not been defined')
            return

        # Load the preset's temperature change value
        try:
            self._temperatureChange = presetTable['change value']
        except KeyError:
            Logger.log('e', f'The "change value" for TempTower preset table "{presetName}" has not been defined')
            return

        # Query the current layer height
        layerHeight = Application.getInstance().getGlobalContainerStack().getProperty("layer_height", "value")

        # Calculate the number of layers in the base and each section of the tower
        self._baseLayers = math.ceil(self._nominalBaseHeight / layerHeight) # Round up
        self._sectionLayers = math.ceil(self._nominalSectionHeight / layerHeight) # Round up

        # Determine the file path of the preset
        stlFilePath = os.path.join(self._stlPath, stlFileName)

        # Determine the tower name
        towerName = f'Preset Temperature Tower {presetName}'

        # Use the callback to load the preset STL file
        self._loadStlCallback(towerName, stlFilePath, self.postProcess)



    @pyqtSlot()
    def dialogAccepted(self)->None:
        ''' This method is called by the dialog when the "Generate" button is clicked '''
        # Read the parameters directly from the dialog
        startTemperature = float(self.startTemperatureStr)
        endTemperature = float(self.endTemperatureStr)
        temperatureChange = float(self.temperatureChangeStr)
        towerLabel = self.towerLabelStr
        towerDescription = self.towerDescriptionStr

        # Query the current layer height
        layerHeight = Application.getInstance().getGlobalContainerStack().getProperty("layer_height", "value")

        # Correct the base height to ensure an integer number of layers in the base
        self._baseLayers = math.ceil(self._nominalBaseHeight / layerHeight) # Round up
        baseHeight = self._baseLayers * layerHeight

        # Correct the section height to ensure an integer number of layers per section
        self._sectionLayers = math.ceil(self._nominalSectionHeight / layerHeight) # Round up
        sectionHeight = self._sectionLayers * layerHeight

        # Ensure the change amount has the correct sign
        if endTemperature >= startTemperature:
            temperatureChange = abs(temperatureChange)
        else:
            temperatureChange = -abs(temperatureChange)

        # Record the tower settings that will be needed for post-processing
        self._startTemperature = startTemperature
        self._temperatureChange = temperatureChange

        # Compile the parameters to send to OpenSCAD
        openScadParameters = {}
        openScadParameters ['Starting_Value'] = startTemperature
        openScadParameters ['Ending_Value'] = endTemperature
        openScadParameters ['Value_Change'] = temperatureChange
        openScadParameters ['Base_Height'] = baseHeight
        openScadParameters ['Section_Height'] = sectionHeight
        openScadParameters ['Column_Label'] = towerLabel
        openScadParameters ['Tower_Label'] = towerDescription

        # Determine the tower name
        towerName = f'Auto-Generated Temperature Tower {startTemperature}-{endTemperature}x{temperatureChange}'

        # Send the filename and parameters to the model callback
        self._generateAndLoadStlCallback(towerName, self._openScadFilename, openScadParameters, self.postProcess)



    # This function is called by the main script when it's time to post-process the tower model
    def postProcess(self, gcode, displayOnLcd=False)->list:
        ''' This method is called to post-process the gcode before it is sent to the printer or disk '''

        # Call the post-processing script
        gcode = TempTower_PostProcessing.execute(gcode, self._startTemperature, self._temperatureChange, self._sectionLayers, self._baseLayers, displayOnLcd)

        return gcode
