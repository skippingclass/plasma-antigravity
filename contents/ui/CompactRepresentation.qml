pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami

Item {
    id: root

    property string statusText: "отдыхает"
    property int bar1Val: 99
    property string colorScheme: "green"

    implicitWidth: Kirigami.Units.iconSizes.medium
    implicitHeight: Kirigami.Units.iconSizes.medium

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: Plasmoid.expanded = !Plasmoid.expanded
    }

    Item {
        anchors.centerIn: parent
        width: 24
        height: 20

        PixelAntigravityLogo {
            anchors.centerIn: parent
            status: root.statusText
            pixelScale: 2
        }

        // Mini status dot in the bottom right corner
        Rectangle {
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            width: 4
            height: 4
            color: root.statusText === "спит" ? "#666677" : PixelTheme.greenNeon
            border.color: "#111116"
            border.width: 1
        }
    }
}
