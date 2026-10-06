pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts

import org.kde.kcmutils as KCM
import org.kde.kirigami as Kirigami

KCM.SimpleKCM {
    id: root

    property alias cfg_statusText: statusTextField.text
    property alias cfg_bar1Label: bar1LabelField.text
    property alias cfg_bar1Percent: bar1PercentSpin.value
    property alias cfg_bar2Label: bar2LabelField.text
    property alias cfg_bar2Percent: bar2PercentSpin.value
    property alias cfg_enableCliMonitoring: enableCliCheckBox.checked
    property alias cfg_pollInterval: pollIntervalSpin.value
    property alias cfg_customScriptPath: customScriptField.text

    Kirigami.FormLayout {

        QQC2.CheckBox {
            id: enableCliCheckBox
            Kirigami.FormData.label: i18n("CLI Monitoring:")
            text: i18n("Auto-detect status from Antigravity CLI (agy)")
        }

        QQC2.SpinBox {
            id: pollIntervalSpin
            Kirigami.FormData.label: i18n("Poll Interval:")
            from: 1
            to: 60
            stepSize: 1
            enabled: enableCliCheckBox.checked
            textFromValue: value => value + " " + i18n("sec")
            valueFromText: text => parseInt(text) || 1
        }

        QQC2.TextField {
            id: statusTextField
            Kirigami.FormData.label: i18n("Default Status:")
            placeholderText: "отдыхает"
            Layout.fillWidth: true
        }

        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Kirigami.FormData.label: i18n("Progress Bars")
        }

        QQC2.TextField {
            id: bar1LabelField
            Kirigami.FormData.label: i18n("Upper Bar Label:")
            placeholderText: "5 часов"
            Layout.fillWidth: true
        }

        QQC2.SpinBox {
            id: bar1PercentSpin
            Kirigami.FormData.label: i18n("Upper Bar (%):")
            from: 0
            to: 100
            stepSize: 1
            textFromValue: value => value + "%"
            valueFromText: text => parseInt(text) || 0
        }

        QQC2.TextField {
            id: bar2LabelField
            Kirigami.FormData.label: i18n("Lower Bar Label:")
            placeholderText: "неделя"
            Layout.fillWidth: true
        }

        QQC2.SpinBox {
            id: bar2PercentSpin
            Kirigami.FormData.label: i18n("Lower Bar (%):")
            from: 0
            to: 100
            stepSize: 1
            textFromValue: value => value + "%"
            valueFromText: text => parseInt(text) || 0
        }

        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Kirigami.FormData.label: i18n("Custom Data Hook")
        }

        QQC2.TextField {
            id: customScriptField
            Kirigami.FormData.label: i18n("Script / Command Path:")
            placeholderText: i18n("/path/to/quota_script.py (outputs JSON)")
            Layout.fillWidth: true
        }
    }
}
