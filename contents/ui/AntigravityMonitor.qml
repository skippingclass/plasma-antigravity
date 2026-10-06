pragma ComponentBehavior: Bound

import QtQuick
import org.kde.plasma.plasma5support as Plasma5Support
import org.kde.plasma.plasmoid

Item {
    id: root

    property bool monitoringEnabled: Plasmoid.configuration.enableCliMonitoring
    property int intervalSec: Math.max(1, Plasmoid.configuration.pollInterval)
    property string customScript: Plasmoid.configuration.customScriptPath

    property string currentStatus: Plasmoid.configuration.statusText
    property int bar1Val: Plasmoid.configuration.bar1Percent
    property int bar2Val: Plasmoid.configuration.bar2Percent
    property string bar1Label: Plasmoid.configuration.bar1Label
    property string bar2Label: Plasmoid.configuration.bar2Label
    property real bar1Exact: bar1Val
    property real bar2Exact: bar2Val
    property string bar1Reset: ""
    property string bar2Reset: ""

    readonly property string scriptPath: Qt.resolvedUrl("../scripts/status_provider.py").toString().replace(/^file:\/\//, "")

    Plasma5Support.DataSource {
        id: execSource
        engine: "executable"
        connectedSources: []

        onNewData: (sourceName, data) => {
            const stdout = data["stdout"] ? data["stdout"].trim() : "";
            disconnectSource(sourceName);

            if (stdout.length > 0) {
                try {
                    const parsed = JSON.parse(stdout);
                    if (parsed.status !== undefined && root.monitoringEnabled) {
                        root.currentStatus = parsed.status;
                    }
                    if (parsed.bar1_percent !== undefined) {
                        root.bar1Val = parseInt(parsed.bar1_percent);
                    }
                    if (parsed.bar2_percent !== undefined) {
                        root.bar2Val = parseInt(parsed.bar2_percent);
                    }
                    if (parsed.bar1_exact !== undefined) {
                        root.bar1Exact = parseFloat(parsed.bar1_exact);
                    }
                    if (parsed.bar2_exact !== undefined) {
                        root.bar2Exact = parseFloat(parsed.bar2_exact);
                    }
                    if (parsed.bar1_reset !== undefined) {
                        root.bar1Reset = parsed.bar1_reset;
                    }
                    if (parsed.bar2_reset !== undefined) {
                        root.bar2Reset = parsed.bar2_reset;
                    }
                    if (parsed.bar1_label !== undefined) {
                        root.bar1Label = parsed.bar1_label;
                    }
                    if (parsed.bar2_label !== undefined) {
                        root.bar2Label = parsed.bar2_label;
                    }
                } catch (e) {
                    // Fallback to configured settings on parse error
                }
            }
        }
    }

    Timer {
        id: pollTimer
        interval: root.intervalSec * 1000
        running: root.monitoringEnabled
        repeat: true
        triggeredOnStart: true

        onTriggered: {
            const cmd = "python3 \"" + root.scriptPath + "\" \"" + root.customScript + "\"";
            execSource.connectSource(cmd);
        }
    }

    // React to configuration changes
    Connections {
        target: Plasmoid.configuration

        function onStatusTextChanged() {
            if (!root.monitoringEnabled) {
                root.currentStatus = Plasmoid.configuration.statusText;
            }
        }
        function onBar1PercentChanged() {
            root.bar1Val = Plasmoid.configuration.bar1Percent;
        }
        function onBar2PercentChanged() {
            root.bar2Val = Plasmoid.configuration.bar2Percent;
        }
        function onBar1LabelChanged() {
            root.bar1Label = Plasmoid.configuration.bar1Label;
        }
        function onBar2LabelChanged() {
            root.bar2Label = Plasmoid.configuration.bar2Label;
        }
    }
}
