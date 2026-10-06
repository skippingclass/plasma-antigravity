pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: root

    property string label: "5 часов"
    property int percent: 99
    property bool isSecondBar: false
    property int totalSegments: 22
    property string colorScheme: "green"
    property int fontSize: 11
    property int barHeight: 12

    spacing: Math.max(2, Math.round(root.fontSize * 0.25))

    readonly property color activeColor: PixelTheme.getBarColor(root.isSecondBar, root.percent)
    readonly property color dimColor: PixelTheme.getBarDimColor(root.isSecondBar, root.percent)

    // Number of active filled blocks
    readonly property int activeCount: Math.max(0, Math.min(root.totalSegments, Math.round((root.percent / 100.0) * root.totalSegments)))

    // Label Row: "5 часов" on left, "осталось XX%" on right
    RowLayout {
        Layout.fillWidth: true
        spacing: 0

        Text {
            text: root.label
            font.family: PixelTheme.pixelFontFamily
            font.pixelSize: root.fontSize
            font.bold: !PixelTheme.isPixelFont
            color: PixelTheme.textLabel
            renderType: Text.NativeRendering
            antialiasing: !PixelTheme.isPixelFont
        }

        Item {
            Layout.fillWidth: true
        }

        Text {
            text: "осталось " + root.percent + "%"
            font.family: PixelTheme.pixelFontFamily
            font.pixelSize: root.fontSize
            font.bold: !PixelTheme.isPixelFont
            color: root.activeColor
            renderType: Text.NativeRendering
            antialiasing: !PixelTheme.isPixelFont
        }
    }

    // Bar Container
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: root.barHeight
        color: PixelTheme.slotBg
        border.color: PixelTheme.slotBorder
        border.width: 1
        radius: PixelTheme.slotRadius

        // Material 3 Continuous Pill Mode vs Retro Segmented Mode
        Loader {
            anchors.fill: parent
            anchors.margins: PixelTheme.isRounded ? 2 : 1
            sourceComponent: PixelTheme.isRounded && !PixelTheme.isPixelFont ? continuousBarComp : segmentedBarComp
        }

        // 1. Continuous Pill Progress Bar (Material 3 Expressive, Catppuccin, Tokyo Night)
        Component {
            id: continuousBarComp

            Item {
                anchors.fill: parent

                Rectangle {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: Math.max(0, Math.min(parent.width, (root.percent / 100.0) * parent.width))
                    color: root.activeColor
                    radius: Math.max(2, PixelTheme.slotRadius - 1)

                    Behavior on width {
                        NumberAnimation { duration: 250; easing.type: Easing.OutCubic }
                    }
                }
            }
        }

        // 2. Retro Pixel Segmented Bar (Retro Pixel, Windows 95, Cyberpunk, Gruvbox)
        Component {
            id: segmentedBarComp

            RowLayout {
                anchors.fill: parent
                spacing: 1

                Repeater {
                    model: root.totalSegments

                    Rectangle {
                        required property int index
                        readonly property bool isActive: index < root.activeCount

                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: isActive ? root.activeColor : root.dimColor
                        radius: PixelTheme.slotRadius > 0 ? 1 : 0

                        // Pixel 3D top shine
                        Rectangle {
                            anchors.top: parent.top
                            anchors.left: parent.left
                            anchors.right: parent.right
                            height: Math.max(1, Math.round(root.barHeight * 0.15))
                            color: parent.isActive ? Qt.rgba(1, 1, 1, 0.4) : "transparent"
                        }
                    }
                }
            }
        }
    }
}
