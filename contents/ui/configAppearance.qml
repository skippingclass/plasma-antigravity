pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts

import org.kde.kcmutils as KCM
import org.kde.kirigami as Kirigami

KCM.SimpleKCM {
    id: root

    property alias cfg_titleText: titleField.text
    property alias cfg_pixelScale: pixelScaleSpin.value
    property string cfg_colorScheme: colorSchemeCombo.currentValue
    property string cfg_theme: themeCombo.currentValue

    Kirigami.FormLayout {

        QQC2.TextField {
            id: titleField
            Kirigami.FormData.label: i18n("Window Title:")
            placeholderText: "antigravity.exe"
            Layout.fillWidth: true
        }

        QQC2.ComboBox {
            id: themeCombo
            Kirigami.FormData.label: i18n("Theme:")
            textRole: "text"
            valueRole: "value"
            model: [
                { text: i18n("Retro Pixel (Classic)"), value: "retro_pixel" },
                { text: i18n("Material 3 Expressive"), value: "material3" },
                { text: i18n("Cyberpunk 2077"), value: "cyberpunk" },
                { text: i18n("Windows 95 Classic"), value: "win95" },
                { text: i18n("Gruvbox Retro"), value: "gruvbox" },
                { text: i18n("Catppuccin Mocha"), value: "catppuccin" },
                { text: i18n("Tokyo Night"), value: "tokyo_night" }
            ]
            currentIndex: {
                for (let i = 0; i < count; i++) {
                    if (model[i].value === root.cfg_theme) return i;
                }
                return 0;
            }
            onActivated: root.cfg_theme = currentValue
        }

        QQC2.ComboBox {
            id: colorSchemeCombo
            Kirigami.FormData.label: i18n("Segment Accent:")
            textRole: "text"
            valueRole: "value"
            model: [
                { text: i18n("Theme Default"), value: "green" },
                { text: i18n("Neon Cyan"), value: "cyan" },
                { text: i18n("Retro Amber"), value: "amber" }
            ]
            currentIndex: {
                for (let i = 0; i < count; i++) {
                    if (model[i].value === root.cfg_colorScheme) return i;
                }
                return 0;
            }
            onActivated: root.cfg_colorScheme = currentValue
        }

        QQC2.SpinBox {
            id: pixelScaleSpin
            Kirigami.FormData.label: i18n("Pixel Scale:")
            from: 1
            to: 4
            stepSize: 1
            textFromValue: value => value + "x"
            valueFromText: text => parseInt(text) || 2
        }
    }
}
