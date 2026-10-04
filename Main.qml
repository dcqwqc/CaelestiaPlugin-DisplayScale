import QtQuick
import Quickshell
import Quickshell.Io
import Caelestia.Plugins
import qs.utils

Item {
    id: root
    property SettingsObject settings: null
    readonly property string helper: Paths.toLocalFile(Qt.resolvedUrl("scripts/display-scale.py"))
    property string lastKey: ""

    visible: false
    implicitWidth: 0
    implicitHeight: 0

    function key(): string {
        if (!settings) return "";
        return [settings.enabled, settings.monitor, settings.scale].join("|");
    }

    function apply(force = false): void {
        if (!settings || !settings.enabled || applyProc.running) return;
        const k = key();
        if (!force && k === lastKey) return;
        lastKey = k;
        applyProc.command = ["python3", helper, "apply", "--monitor", String(settings.monitor), "--scale", String(settings.scale)];
        applyProc.running = true;
    }

    Component.onCompleted: {
        if (settings?.applyOnStart ?? true)
            startTimer.restart();
    }

    onSettingsChanged: {
        if (settings?.applyOnStart ?? true)
            startTimer.restart();
    }

    Connections {
        target: root.settings
        function onChanged(): void { root.apply(true); }
    }

    Timer {
        id: startTimer
        interval: 350
        repeat: false
        onTriggered: root.apply(true)
    }

    Process {
        id: applyProc
        running: false
        stderr: StdioCollector {
            onStreamFinished: {
                if (text.trim() !== "") console.warn("DisplayScale:", text.trim());
            }
        }
    }
}
