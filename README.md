# Display Scale

Caelestia plugin for persistent per-monitor Hyprland scaling.

The plugin updates the existing `hl.monitor` rule for the selected output,
keeps the generic Caelestia monitor default on automatic scaling, and applies
the new scale live through Hyprland's Lua API. It does not add duplicate rules
when a monitor already has a rule.

Mirai defaults to `eDP-1` at scale `2` (200%).
