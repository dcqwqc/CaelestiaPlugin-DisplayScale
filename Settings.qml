import Caelestia.Plugins

SettingsObject {
    property bool enabled: true
    SettingMeta on enabled {
        label: "Manage display scale"
        description: "Keep the selected monitor at the configured scale, including after Hyprland reloads."
        icon: "display_settings"
        inputType: SettingMeta.Switch
    }

    property string monitor: "eDP-1"
    SettingMeta on monitor {
        label: "Monitor"
        description: "Hyprland output name. Mirai's internal display is eDP-1."
        icon: "monitor"
        inputType: SettingMeta.TextField
    }

    property string scale: "2"
    SettingMeta on scale {
        label: "Display scale"
        description: "100% is scale 1. Mirai's normal 2880×1800 laptop scale is 200%."
        icon: "zoom_in"
        inputType: SettingMeta.SplitButton
        options: ["auto", "1", "1.25", "1.5", "1.75", "2", "2.25", "2.5"]
    }

    property bool applyOnStart: true
    SettingMeta on applyOnStart {
        label: "Reapply on shell start"
        description: "Reassert the saved scale whenever Caelestia starts, useful after display or tablet-mode changes."
        icon: "restart_alt"
        inputType: SettingMeta.Switch
    }
}
