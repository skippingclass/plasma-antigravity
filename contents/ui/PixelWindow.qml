pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid

Rectangle {
    id: root

    property string titleText: "antigravity.exe"
    property string statusText: "отдыхает"
    property string bar1Label: "5 часов"
    property int bar1Percent: 72
    property string bar2Label: "неделя"
    property int bar2Percent: 95
    property string colorScheme: "green"
    property string themeName: "retro_pixel"
    property int pixelScale: 2

    implicitWidth: 220
    implicitHeight: 215

    // Fill parent if available
    width: parent ? parent.width : implicitWidth
    height: parent ? parent.height : implicitHeight

    color: PixelTheme.windowBg
    radius: PixelTheme.windowRadius
    clip: PixelTheme.windowRadius > 0

    onThemeNameChanged: {
        if (themeName && themeName !== PixelTheme.activeThemeId) {
            PixelTheme.activeThemeId = themeName;
        }
    }
    Component.onCompleted: {
        if (themeName) {
            PixelTheme.activeThemeId = themeName;
        }
    }

    // Retro / Expressive window frame border
    border.color: PixelTheme.frameBorder
    border.width: PixelTheme.frameBorderWidth

    // Top highlight line for 3D bevel retro effect
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 1
        color: PixelTheme.frameHighlight
        visible: PixelTheme.frameHighlight !== "transparent"
        z: 2
    }

    // Proportional dimensions
    readonly property int titleBarHeight: Math.max(22, Math.min(38, Math.round(root.height * 0.11)))
    readonly property int availableBodyHeight: Math.max(50, root.height - titleBarHeight)
    readonly property real spacingScale: Math.max(0.8, Math.min(2.5, root.height / 220.0))

    // Dynamic mascot scale: fills ~38% of available body height and fits within window width
    readonly property int dynamicMascotScale: Math.max(3, Math.min(14, Math.floor(Math.min((root.width - 36) / 14, (availableBodyHeight * 0.38) / 10))))

    // Dynamic font and bar sizes
    readonly property int titleFontSize: Math.max(10, Math.min(16, Math.round(titleBarHeight * 0.50)))
    readonly property int statusFontSize: Math.max(11, Math.min(22, Math.round(dynamicMascotScale * 2.2)))
    readonly property int barFontSize: Math.max(9, Math.min(18, Math.round(dynamicMascotScale * 1.8)))
    readonly property int barHeight: Math.max(10, Math.min(24, Math.round(dynamicMascotScale * 2.0)))
    readonly property int horizPadding: Math.max(10, Math.min(32, Math.round(root.width * 0.055)))

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // 1. Title Bar
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: root.titleBarHeight
            color: PixelTheme.headerBg
            // Rounded top corners for Material 3 / Catppuccin
            radius: PixelTheme.headerRadius

            // Bottom mask for rounded header so only top corners are round
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                height: PixelTheme.headerRadius
                color: PixelTheme.headerBg
                visible: PixelTheme.headerRadius > 0
            }

            Rectangle {
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                height: 1
                color: PixelTheme.headerBorder
                visible: PixelTheme.headerBorder !== "transparent"
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Math.max(8, Math.round(8 * root.spacingScale))
                anchors.rightMargin: Math.max(8, Math.round(8 * root.spacingScale))
                spacing: Math.max(6, Math.round(6 * root.spacingScale))

                // Left mini icon
                Item {
                    readonly property int iconScale: Math.max(1, Math.round(root.titleBarHeight / 22))
                    implicitWidth: 12 * iconScale
                    implicitHeight: 10 * iconScale

                    PixelAntigravityLogo {
                        anchors.centerIn: parent
                        pixelScale: parent.iconScale
                        status: root.statusText
                    }
                }

                Text {
                    text: root.titleText
                    font.family: PixelTheme.pixelFontFamily
                    font.pixelSize: root.titleFontSize
                    font.bold: PixelTheme.isRounded
                    color: PixelTheme.textTitle
                    renderType: Text.NativeRendering
                    antialiasing: !PixelTheme.isPixelFont
                }

                Item {
                    Layout.fillWidth: true
                }

                // Interactive Theme Switcher Button
                Rectangle {
                    implicitWidth: Math.max(18, Math.round(20 * root.spacingScale))
                    implicitHeight: Math.max(16, Math.round(18 * root.spacingScale))
                    color: themeBtnArea.containsMouse ? Qt.rgba(1, 1, 1, 0.15) : "transparent"
                    radius: PixelTheme.isRounded ? 4 : 0

                    Text {
                        anchors.centerIn: parent
                        text: "◒"
                        font.pixelSize: Math.max(10, Math.round(12 * root.spacingScale))
                        color: themeBtnArea.containsMouse ? PixelTheme.activeColor : PixelTheme.textMuted
                    }

                    MouseArea {
                        id: themeBtnArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            const next = PixelTheme.getNextTheme(PixelTheme.activeThemeId);
                            PixelTheme.activeThemeId = next;
                            if (typeof Plasmoid !== "undefined" && Plasmoid.configuration) {
                                Plasmoid.configuration.theme = next;
                            }
                        }
                    }
                }

                // Minimize dash
                Rectangle {
                    implicitWidth: Math.max(7, Math.round(8 * root.spacingScale))
                    implicitHeight: Math.max(2, Math.round(2 * root.spacingScale))
                    color: PixelTheme.textMuted
                    radius: PixelTheme.isRounded ? 1 : 0
                }
            }
        }

        // 2. Main Window Body
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: root.horizPadding
                anchors.rightMargin: root.horizPadding
                spacing: 0

                // Top flexible spacer
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 2
                    Layout.maximumHeight: Math.round(20 * root.spacingScale)
                }

                // Mascot & Status Area
                ColumnLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: Math.max(4, Math.round(6 * root.spacingScale))

                    Item {
                        Layout.alignment: Qt.AlignHCenter
                        implicitWidth: mascot.implicitWidth
                        implicitHeight: mascot.implicitHeight

                        PixelAntigravityLogo {
                            id: mascot
                            anchors.centerIn: parent
                            status: root.statusText
                            pixelScale: root.dynamicMascotScale
                        }
                    }

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: root.statusText
                        font.family: PixelTheme.pixelFontFamily
                        font.pixelSize: root.statusFontSize
                        font.bold: PixelTheme.isRounded
                        color: PixelTheme.textPrimary
                        renderType: Text.NativeRendering
                        antialiasing: !PixelTheme.isPixelFont
                    }
                }

                // Middle flexible spacer (between status and bars)
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 6
                    Layout.maximumHeight: Math.round(28 * root.spacingScale)
                }

                // Progress Bars Section
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Math.max(4, Math.round(6 * root.spacingScale))

                    PixelProgressBar {
                        Layout.fillWidth: true
                        isSecondBar: false
                        label: root.bar1Label
                        percent: root.bar1Percent
                        colorScheme: root.colorScheme
                        fontSize: root.barFontSize
                        barHeight: root.barHeight
                    }

                    PixelProgressBar {
                        Layout.fillWidth: true
                        isSecondBar: true
                        label: root.bar2Label
                        percent: root.bar2Percent
                        colorScheme: root.colorScheme
                        fontSize: root.barFontSize
                        barHeight: root.barHeight
                    }
                }

                // Bottom flexible spacer
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 4
                    Layout.maximumHeight: Math.round(20 * root.spacingScale)
                }
            }
        }
    }
}
