pragma ComponentBehavior: Bound

import QtQuick
import org.kde.plasma.configuration as PlasmaConfiguration

PlasmaConfiguration.ConfigModel {
    id: root

    PlasmaConfiguration.ConfigCategory {
        name: i18n("General")
        icon: "preferences-system"
        source: "configGeneral.qml"
    }

    PlasmaConfiguration.ConfigCategory {
        name: i18n("Appearance")
        icon: "preferences-desktop-theme"
        source: "configAppearance.qml"
    }
}
