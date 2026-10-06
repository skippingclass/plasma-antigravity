/*
 * SPDX-FileCopyrightText: 2026 pirkov
 * SPDX-License-Identifier: MIT
 */
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore

PlasmoidItem {
    id: root

    readonly property bool isPlanar: Plasmoid.formFactor === PlasmaCore.Types.Planar
    
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    // Antigravity background monitor
    AntigravityMonitor {
        id: monitor
    }

    readonly property string currentTitle: Plasmoid.configuration.titleText
    readonly property string currentStatus: monitor.currentStatus
    readonly property string currentBar1Label: monitor.bar1Label
    readonly property int currentBar1Val: monitor.bar1Val
    readonly property real currentBar1Exact: monitor.bar1Exact
    readonly property string currentBar1Reset: monitor.bar1Reset
    readonly property string currentBar2Label: monitor.bar2Label
    readonly property int currentBar2Val: monitor.bar2Val
    readonly property real currentBar2Exact: monitor.bar2Exact
    readonly property string currentBar2Reset: monitor.bar2Reset
    readonly property string currentColorScheme: Plasmoid.configuration.colorScheme
    readonly property string currentTheme: Plasmoid.configuration.theme ? Plasmoid.configuration.theme : "retro_pixel"
    readonly property int currentPixelScale: Plasmoid.configuration.pixelScale

    Component.onCompleted: {
        PixelTheme.activeThemeId = root.currentTheme;
    }

    Connections {
        target: Plasmoid.configuration
        function onThemeChanged() {
            PixelTheme.activeThemeId = Plasmoid.configuration.theme ? Plasmoid.configuration.theme : "retro_pixel";
        }
    }

    preferredRepresentation: isPlanar ? fullRepresentation : compactRepresentation

    compactRepresentation: CompactRepresentation {
        statusText: root.currentStatus
        bar1Val: root.currentBar1Val
        colorScheme: root.currentColorScheme
    }

    fullRepresentation: FullRepresentation {
        titleText: root.currentTitle
        statusText: root.currentStatus
        bar1Label: root.currentBar1Label
        bar1Percent: root.currentBar1Val
        bar2Label: root.currentBar2Label
        bar2Percent: root.currentBar2Val
        colorScheme: root.currentColorScheme
        themeName: root.currentTheme
        pixelScale: root.currentPixelScale
    }
}
