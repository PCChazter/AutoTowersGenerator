import QtQuick 2.11
import QtQuick.Controls 2.11
import QtQuick.Layouts 1.11

import UM 1.2 as UM

UM.Dialog
{
    id: dialog
    title: "Flow Tower"

    minimumWidth: screenScaleFactor * 445
    minimumHeight: (screenScaleFactor * contents.childrenRect.height) + (2 * UM.Theme.getSize("default_margin").height) + UM.Theme.getSize("button").height
    maximumHeight: minimumHeight
    width: minimumWidth
    height: minimumHeight

    // Define the width of the number input text boxes
    property int numberInputWidth: UM.Theme.getSize("button").width

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
                source: Qt.resolvedUrl("../../Images/flowtower_icon.png")
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

            Label 
            { 
                text: "Starting Flow Rate %" 
            }
            TextField
            {
                Layout.preferredWidth: numberInputWidth
                validator: RegExpValidator { regExp: /[0-9]*(\.[0-9]+)?/ }
                text: manager.startValueStr
                onTextChanged: if (manager.startValueStr != text) manager.startValueStr = text
            }

            Label 
            { 
                text: "Ending Flow Rate %" 
            }
            TextField
            {
                Layout.preferredWidth: numberInputWidth
                validator: RegExpValidator { regExp: /[0-9]*(\.[0-9]+)?/ }
                text: manager.endValueStr
                onTextChanged: if (manager.endValueStr != text) manager.endValueStr = text
            }

            Label 
            { 
                text: "Flow Rate % Change" 
            }
            TextField
            {
                Layout.preferredWidth: numberInputWidth
                validator: RegExpValidator { regExp: /[+-]?[0-9]*(\.[0-9]+)?/ }
                text: manager.valueChangeStr
                onTextChanged: if (manager.valueChangeStr != text) manager.valueChangeStr = text
            }

            UM.Label 
            { 
                text: "Section Size" 
            }
            Cura.TextField
            {
                Layout.preferredWidth: numberInputWidth
                validator: RegExpValidator { regExp: /[+-]?[0-9]*(\.[0-9]+)?/ }
                text: manager.sectionSizeStr
                onTextChanged: if (manager.sectionSizeStr != text) manager.sectionSizeStr = text
            }

            UM.Label 
            { 
                text: "Section Hole Diameter" 
            }
            Cura.TextField
            {
                Layout.preferredWidth: numberInputWidth
                validator: RegExpValidator { regExp: /[+-]?[0-9]*(\.[0-9]+)?/ }
                text: manager.sectionHoleDiameterStr
                onTextChanged: if (manager.sectionHoleDiameterStr != text) manager.sectionHoleDiameterStr = text
            }
    
            Label 
            { 
                text: "Tower Label" 
            }
            TextField
            {
                Layout.fillWidth: true
                text: manager.towerLabelStr
                onTextChanged: if (manager.towerLabelStr != text) manager.towerLabelStr = text
            }
    
            Label 
            { 
                text: "Side Label" 
            }
            TextField
            {
                Layout.fillWidth: true
                text: manager.temperatureLabelStr
                onTextChanged: if (manager.temperatureLabelStr != text) manager.temperatureLabelStr = text
            }
        }
    }

    rightButtons: Button
    {
        text: "OK"
        onClicked: dialog.accept()
    }

    leftButtons: Button
    {
        text: "Cancel"
        onClicked: dialog.reject()
    }

    onAccepted:
    {
        manager.dialogAccepted()
    }
}
