pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid

Item {
    id: root

    required property string titleText
    required property string statusText
    required property string bar1Label
    required property int bar1Percent
    required property string bar2Label
    required property int bar2Percent
    required property string colorScheme
    required property int pixelScale

    property real bar1Exact: bar1Percent
    property real bar2Exact: bar2Percent
    property string bar1Reset: ""
    property string bar2Reset: ""
    property string themeName: "retro_pixel"

    implicitWidth: 220
    implicitHeight: 215
    Layout.minimumWidth: 160
    Layout.minimumHeight: 160

    PixelWindow {
        id: windowFrame
        anchors.fill: parent
        anchors.margins: 1
        titleText: root.titleText
        statusText: root.statusText
        bar1Label: root.bar1Label
        bar1Percent: root.bar1Percent
        bar1Exact: root.bar1Exact
        bar1Reset: root.bar1Reset
        bar2Label: root.bar2Label
        bar2Percent: root.bar2Percent
        bar2Exact: root.bar2Exact
        bar2Reset: root.bar2Reset
        colorScheme: root.colorScheme
        themeName: root.themeName
        pixelScale: root.pixelScale
    }
}
