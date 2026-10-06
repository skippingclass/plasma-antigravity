pragma Singleton
import QtQuick

QtObject {
    id: theme

    // Current selected theme ID
    property string activeThemeId: "retro_pixel"

    readonly property var themeList: [
        { id: "retro_pixel", name: "Retro Pixel (Classic)" },
        { id: "material3", name: "Material 3 Expressive" },
        { id: "cyberpunk", name: "Cyberpunk 2077" },
        { id: "win95", name: "Windows 95 Classic" },
        { id: "gruvbox", name: "Gruvbox Retro" },
        { id: "catppuccin", name: "Catppuccin Mocha" },
        { id: "tokyo_night", name: "Tokyo Night" }
    ]

    function getNextTheme(currentId) {
        for (let i = 0; i < themeList.length; i++) {
            if (themeList[i].id === currentId) {
                return themeList[(i + 1) % themeList.length].id;
            }
        }
        return "retro_pixel";
    }

    function getBestFont(preferredList, fallback) {
        const available = Qt.fontFamilies();
        for (let i = 0; i < preferredList.length; i++) {
            if (available.indexOf(preferredList[i]) !== -1) {
                return preferredList[i];
            }
        }
        return fallback;
    }

    function getThemeName(themeId) {
        for (let i = 0; i < themeList.length; i++) {
            if (themeList[i].id === themeId) {
                return themeList[i].name;
            }
        }
        return "Retro Pixel";
    }

    // Dynamic Theme Definitions
    readonly property var currentThemeData: {
        switch (activeThemeId) {
        case "material3":
            return {
                windowBg: "#1c1924",
                windowRadius: 18,
                headerBg: "#252130",
                headerRadius: 18,
                headerBorder: "#352f44",
                frameBorder: "#3a3447",
                frameBorderWidth: 1,
                frameHighlight: "transparent",
                slotBg: "#2d273a",
                slotBorder: "transparent",
                slotRadius: 12,
                textPrimary: "#f5eff7",
                textTitle: "#f5eff7",
                textMuted: "#9a93a6",
                textLabel: "#d0c4de",
                activeColor: "#d0bcff",
                dimColor: "#332c3f",
                activeColor2: "#7cd5ff",
                dimColor2: "#20343f",
                fontFamily: getBestFont(["Google Sans Flex", "Google Sans", "Roboto Flex", "Roboto", "Noto Sans"], "sans-serif"),
                isPixelFont: false,
                isRounded: true
            };
        case "cyberpunk":
            return {
                windowBg: "#0b0c10",
                windowRadius: 0,
                headerBg: "#12141c",
                headerRadius: 0,
                headerBorder: "#00f0ff",
                frameBorder: "#00f0ff",
                frameBorderWidth: 1,
                frameHighlight: "#ffe600",
                slotBg: "#06070a",
                slotBorder: "#1f2233",
                slotRadius: 0,
                textPrimary: "#00f0ff",
                textMuted: "#5e6580",
                textLabel: "#ffe600",
                activeColor: "#ffe600",
                dimColor: "#2b2605",
                activeColor2: "#ff007f",
                dimColor2: "#33001a",
                fontFamily: "xos4 Terminus, Terminus, Monospace, monospace",
                isPixelFont: true,
                isRounded: false
            };
        case "win95":
            return {
                windowBg: "#c0c0c0",
                windowRadius: 0,
                headerBg: "#000080",
                headerRadius: 0,
                headerBorder: "#000080",
                frameBorder: "#808080",
                frameBorderWidth: 1,
                frameHighlight: "#ffffff",
                slotBg: "#808080",
                slotBorder: "#ffffff",
                slotRadius: 0,
                textPrimary: "#000000",
                textTitle: "#ffffff",
                textMuted: "#404040",
                textLabel: "#202020",
                activeColor: "#008080",
                dimColor: "#506060",
                activeColor2: "#000080",
                dimColor2: "#404060",
                fontFamily: "MS Sans Serif, Tahoma, xos4 Terminus, monospace",
                isPixelFont: true,
                isRounded: false
            };
        case "gruvbox":
            return {
                windowBg: "#282828",
                windowRadius: 8,
                headerBg: "#32302f",
                headerRadius: 8,
                headerBorder: "#1d2021",
                frameBorder: "#504945",
                frameBorderWidth: 1,
                frameHighlight: "#665c54",
                slotBg: "#1d2021",
                slotBorder: "#3c3836",
                slotRadius: 4,
                textPrimary: "#ebdbb2",
                textMuted: "#928374",
                textLabel: "#d5c4a1",
                activeColor: "#b8bb26",
                dimColor: "#32361a",
                activeColor2: "#83a598",
                dimColor2: "#1d2b27",
                fontFamily: "xos4 Terminus, Terminus, Monospace, monospace",
                isPixelFont: true,
                isRounded: true
            };
        case "catppuccin":
            return {
                windowBg: "#1e1e2e",
                windowRadius: 14,
                headerBg: "#181825",
                headerRadius: 14,
                headerBorder: "#11111b",
                frameBorder: "#313244",
                frameBorderWidth: 1,
                frameHighlight: "#45475a",
                slotBg: "#11111b",
                slotBorder: "#313244",
                slotRadius: 6,
                textPrimary: "#cdd6f4",
                textMuted: "#6c7086",
                textLabel: "#bac2de",
                activeColor: "#cba6f7",
                dimColor: "#2b243b",
                activeColor2: "#a6e3a1",
                dimColor2: "#1e2e24",
                fontFamily: getBestFont(["Google Sans Flex", "Google Sans", "Inter", "Roboto", "Noto Sans"], "sans-serif"),
                isPixelFont: false,
                isRounded: true
            };
        case "tokyo_night":
            return {
                windowBg: "#1a1b26",
                windowRadius: 10,
                headerBg: "#24283b",
                headerRadius: 10,
                headerBorder: "#15161e",
                frameBorder: "#414868",
                frameBorderWidth: 1,
                frameHighlight: "#565f89",
                slotBg: "#16161e",
                slotBorder: "#292e42",
                slotRadius: 5,
                textPrimary: "#c0caf5",
                textMuted: "#565f89",
                textLabel: "#9aa5ce",
                activeColor: "#7aa2f7",
                dimColor: "#1d2538",
                activeColor2: "#bb9af7",
                dimColor2: "#2a223a",
                fontFamily: getBestFont(["Google Sans Flex", "Google Sans", "Inter", "Roboto", "Noto Sans"], "sans-serif"),
                isPixelFont: false,
                isRounded: true
            };
        default: // "retro_pixel"
            return {
                windowBg: "#222226",
                windowRadius: 0,
                headerBg: "#2b2b31",
                headerRadius: 0,
                headerBorder: "#19191c",
                frameBorder: "#3a3a44",
                frameBorderWidth: 1,
                frameHighlight: "#4e4e5c",
                slotBg: "#17171a",
                slotBorder: "#2a2a30",
                slotRadius: 0,
                textPrimary: "#ffffff",
                textMuted: "#8e8e99",
                textLabel: "#9e9ea8",
                activeColor: "#4cf0a0",
                dimColor: "#193526",
                activeColor2: "#4cf0a0",
                dimColor2: "#193526",
                fontFamily: "xos4 Terminus, Terminus, Monospace, monospace",
                isPixelFont: true,
                isRounded: false
            };
        }
    }

    // Convenience property accessors
    readonly property color windowBg: currentThemeData.windowBg
    readonly property int windowRadius: currentThemeData.windowRadius
    readonly property color headerBg: currentThemeData.headerBg
    readonly property int headerRadius: currentThemeData.headerRadius
    readonly property color headerBorder: currentThemeData.headerBorder
    readonly property color frameBorder: currentThemeData.frameBorder
    readonly property int frameBorderWidth: currentThemeData.frameBorderWidth
    readonly property color frameHighlight: currentThemeData.frameHighlight
    readonly property color slotBg: currentThemeData.slotBg
    readonly property color slotBorder: currentThemeData.slotBorder
    readonly property int slotRadius: currentThemeData.slotRadius
    readonly property color textPrimary: currentThemeData.textPrimary
    readonly property color textTitle: currentThemeData.textTitle !== undefined ? currentThemeData.textTitle : currentThemeData.textPrimary
    readonly property color textMuted: currentThemeData.textMuted
    readonly property color textLabel: currentThemeData.textLabel
    readonly property color activeColor: currentThemeData.activeColor
    readonly property color dimColor: currentThemeData.dimColor
    readonly property color activeColor2: currentThemeData.activeColor2 !== undefined ? currentThemeData.activeColor2 : currentThemeData.activeColor
    readonly property color dimColor2: currentThemeData.dimColor2 !== undefined ? currentThemeData.dimColor2 : currentThemeData.dimColor
    readonly property string pixelFontFamily: currentThemeData.fontFamily
    readonly property bool isPixelFont: currentThemeData.isPixelFont
    readonly property bool isRounded: currentThemeData.isRounded

    // Dynamic warning colors for low quotas
    function getBarColor(isSecondBar, percent) {
        if (percent !== undefined && percent < 15) {
            return "#f0504c";
        }
        if (percent !== undefined && percent < 30) {
            return "#f0b84c";
        }
        return isSecondBar ? activeColor2 : activeColor;
    }

    function getBarDimColor(isSecondBar, percent) {
        if (percent !== undefined && percent < 15) {
            return "#351a19";
        }
        if (percent !== undefined && percent < 30) {
            return "#352919";
        }
        return isSecondBar ? dimColor2 : dimColor;
    }
}
