import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

import UM 1.6 as UM
import Cura 1.7 as Cura

UM.Dialog
{
    id: dialog
    title: "Temperature Tower"

    buttonSpacing: UM.Theme.getSize("default_margin").width
    minimumWidth: screenScaleFactor * 445
    minimumHeight: screenScaleFactor * (contents.childrenRect.height + 2 * UM.Theme.getSize("default_margin").height + UM.Theme.getSize("button").height)
    maximumHeight: minimumHeight
    width: minimumWidth
    height: minimumHeight

    // Define the width of the text input text boxes
    property int numberInputWidth: screenScaleFactor * UM.Theme.getSize("button").width

    RowLayout
    {
        id: contents
        width: dialog.width - 2 * UM.Theme.getSize("default_margin").width
        spacing: UM.Theme.getSize("default_margin").width

        Rectangle
        {
            Layout.preferredWidth: icon.width
            Layout.preferredHeight: icon.height
            Layout.fillHeight: true
            color: UM.Theme.getColor("primary_button")

            Image
            {
                id: icon
                source: Qt.resolvedUrl("../../Images/temptower_icon.png")
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }

        GridLayout
        {
            columns: 2
            rowSpacing: UM.Theme.getSize("default_lining").height
            columnSpacing: UM.Theme.getSize("default_margin").width
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignTop


            UM.Label 
            { 
                text: "Scale" 
            }
            Cura.TextField
            {
                Layout.preferredWidth: numberInputWidth
                validator: RegularExpressionValidator { regularExpression: /[0-9]*(\.[0-9]+)?/ }
                text: manager.scaleStr
                onTextChanged: if (manager.scaleStr != text) manager.scaleStr = text
            }


            UM.Label
            {
                text: "Starting Temperature"
            }
            Cura.TextField
            {
                Layout.preferredWidth: numberInputWidth
                validator: RegularExpressionValidator { regularExpression: /[0-9]*(\.[0-9]+)?/ }
                text: manager.startTemperatureStr
                onTextChanged: if (manager.startTemperatureStr != text) manager.startTemperatureStr = text
            }

            UM.Label
            {
                text: "Ending Temperature"
            }
            Cura.TextField
            {
                Layout.preferredWidth: numberInputWidth
                validator: RegularExpressionValidator { regularExpression: /[0-9]*(\.[0-9]+)?/ }
                text: manager.endTemperatureStr
                onTextChanged: if (manager.endTemperatureStr != text) manager.endTemperatureStr = text
            }

            UM.Label
            {
                text: "Temperature Change"
            }
            Cura.TextField
            {
                Layout.preferredWidth: numberInputWidth
                validator: RegularExpressionValidator { regularExpression: /[+-]?[0-9]*(\.[0-9]+)?/ }
                text: manager.temperatureChangeStr
                onTextChanged: if (manager.temperatureChangeStr != text) manager.temperatureChangeStr = text
            }

            UM.Label
            {
                text: "Tower Label"
            }
            Cura.TextField
            {
                Layout.preferredWidth: numberInputWidth
                validator: RegularExpressionValidator { regularExpression: /.{0,4}/ }
                text: manager.towerLabelStr
                onTextChanged: if (manager.towerLabelStr != text) manager.towerLabelStr = text
            }

            UM.Label
            {
                text: "Tower Description"
            }
            Cura.TextField
            {
                Layout.fillWidth: true
                text: manager.towerDescriptionStr
                onTextChanged: if (manager.towerDescriptionStr != text) manager.towerDescriptionStr = text
            }
       }
    }

    rightButtons: 
    [
        Cura.SecondaryButton
        {
            text: "Cancel"
            onClicked: dialog.reject()
        },
        Cura.PrimaryButton
        {
            text: "OK"
            onClicked: dialog.accept()
        }
    ]

    onAccepted:
    {
        manager.dialogAccepted()
    }
}
