-- #######################################################################################
-- HYPRLAND CONFIG — Lua format (Hyprland >= 0.55)
-- Ported from a hyprlang hyprland.conf.
-- Refer to the wiki for more information: https://wiki.hypr.land/Configuring/Start/
--
-- NOTE: your old config had `source = ~/.config/hypr/monitors.conf` and
-- `source = ~/.config/hypr/workspaces.conf`. Those files' contents weren't provided,
-- so they've been converted to `require()` calls below, pointing at monitors.lua and
-- workspaces.lua. You'll need to hand-port those two files into Lua yourself (or send
-- me their contents and I'll do it).
-- #######################################################################################

------------------
---- MONITORS ----
------------------
-- See https://wiki.hypr.land/Configuring/Basics/Monitors/
-- Real monitor layout lives in monitors.lua (generated/maintained by nwg-displays) —
-- required at the bottom of this file to avoid duplicate/conflicting hl.monitor() calls.

-- Fallback profile for any unmapped or temporary displays
hl.monitor({
	output = "",
	mode = "preferred",
	position = "auto",
	scale = 1,
})

-- Disable hardware cursor to avoid DMABUF crash
hl.config({
	cursor = {
		no_hardware_cursors = true,
	},
})

---------------------
---- MY PROGRAMS ----
---------------------

local terminal = "kitty"
local fileManager = "thunar"
local menu = "wofi --show drun --style /home/alzrag/.config/wofi/themes/neon.css"

-------------------
---- AUTOSTART ----
-------------------
-- See https://wiki.hypr.land/Configuring/Basics/Autostart/
-- hl.on("hyprland.start", ...) ensures these only run once at boot, instead of on
-- every config reload (unlike exec-once in old hyprlang, this is the Lua equivalent).

hl.on("hyprland.start", function()
	hl.exec_cmd("/usr/lib/polkit-kde-authentication-agent-1")
	hl.exec_cmd("/usr/bin/gnome-keyring-daemon --start --components=secrets")
	hl.exec_cmd("/usr/bin/nm-applet")

	hl.exec_cmd("/usr/bin/gnome-keyring-daemon --start --components=secrets,pkcs11,ssh,gpg")
	hl.exec_cmd("nm-applet --indicator")

	hl.exec_cmd("dbus-update-activation-environment --systemd --all")
	hl.exec_cmd("swww-daemon &")
	hl.exec_cmd("swww img ~/Downloads/wallpaper.jpg")
	hl.exec_cmd("mako &")
	hl.exec_cmd("waybar &")
	hl.exec_cmd("hyprpaper &")
	hl.exec_cmd("hyprctl reload")
	hl.exec_cmd("kando &")

	-- hl.exec_cmd(terminal)
	-- hl.exec_cmd("nm-applet &")
	-- hl.exec_cmd("waybar & hyprpaper & firefox")
end)

-------------------------------
---- ENVIRONMENT VARIABLES ----
-------------------------------
-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Environment-variables/

hl.env("QT_QPA_PLATFORMTHEME", "kvantum")
hl.env("QT_STYLE_OVERRIDE", "Kvantum")
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("ELECTRON_OZONE_PLATFORM_HINT", "auto")

-----------------------
----- PERMISSIONS -----
-----------------------
-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Permissions/
-- None active in your original config — left commented for reference.

-- hl.config({
--     ecosystem = {
--         enforce_permissions = true,
--     },
-- })
-- hl.permission("/usr/(bin|local/bin)/grim", "screencopy", "allow")
-- hl.permission("/usr/(lib|libexec|lib64)/xdg-desktop-portal-hyprland", "screencopy", "allow")
-- hl.permission("/usr/(bin|local/bin)/hyprpm", "plugin", "allow")

-----------------------
---- LOOK AND FEEL ----
-----------------------
-- Refer to https://wiki.hypr.land/Configuring/Basics/Variables/

hl.config({
	general = {
		gaps_in = 5,
		gaps_out = 20,

		border_size = 3,

		col = {
			-- single-color active border (rgba, no gradient in your original)
			active_border = "rgba(00ff00aa)",
			-- gradient inactive border, 45deg
			inactive_border = { colors = { "rgba(000000aa)", "rgba(00ab06aa)" }, angle = 45 },
		},

		-- Set to true to enable resizing windows by clicking and dragging on borders/gaps
		resize_on_border = false,

		-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Tearing/ before enabling
		allow_tearing = false,

		layout = "dwindle",
	},

	decoration = {
		rounding = 10,
		rounding_power = 2,

		active_opacity = 1.0,
		inactive_opacity = 1.0,

		shadow = {
			enabled = true,
			range = 4,
			render_power = 3,
			-- rgba(00000088) -> 0xAARRGGBB
			color = 0x88000000,
		},

		blur = {
			enabled = true,
			size = 3,
			passes = 1,
			vibrancy = 0.1696,
		},
	},

	animations = {
		enabled = true,
	},
})

-- Bezier curves, see https://wiki.hypr.land/Configuring/Advanced-and-Cool/Animations/
hl.curve("easeOutQuint", { type = "bezier", points = { { 0.23, 1 }, { 0.32, 1 } } })
hl.curve("easeInOutCubic", { type = "bezier", points = { { 0.65, 0.05 }, { 0.36, 1 } } })
hl.curve("linear", { type = "bezier", points = { { 0, 0 }, { 1, 1 } } })
hl.curve("almostLinear", { type = "bezier", points = { { 0.5, 0.5 }, { 0.75, 1 } } })
hl.curve("quick", { type = "bezier", points = { { 0.15, 0 }, { 0.1, 1 } } })

hl.animation({ leaf = "global", enabled = true, speed = 10, bezier = "default" })
hl.animation({ leaf = "border", enabled = true, speed = 5.39, bezier = "easeOutQuint" })
hl.animation({ leaf = "windows", enabled = true, speed = 4.79, bezier = "easeOutQuint" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 4.1, bezier = "easeOutQuint", style = "popin 87%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 1.49, bezier = "linear", style = "popin 87%" })
hl.animation({ leaf = "fadeIn", enabled = true, speed = 1.73, bezier = "almostLinear" })
hl.animation({ leaf = "fadeOut", enabled = true, speed = 1.46, bezier = "almostLinear" })
hl.animation({ leaf = "fade", enabled = true, speed = 3.03, bezier = "quick" })
hl.animation({ leaf = "layers", enabled = true, speed = 3.81, bezier = "easeOutQuint" })
hl.animation({ leaf = "layersIn", enabled = true, speed = 4, bezier = "easeOutQuint", style = "fade" })
hl.animation({ leaf = "layersOut", enabled = true, speed = 1.5, bezier = "linear", style = "fade" })
hl.animation({ leaf = "fadeLayersIn", enabled = true, speed = 1.79, bezier = "almostLinear" })
hl.animation({ leaf = "fadeLayersOut", enabled = true, speed = 1.39, bezier = "almostLinear" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 1.94, bezier = "almostLinear", style = "fade" })
hl.animation({ leaf = "workspacesIn", enabled = true, speed = 1.21, bezier = "almostLinear", style = "fade" })
hl.animation({ leaf = "workspacesOut", enabled = true, speed = 1.94, bezier = "almostLinear", style = "fade" })

-- Ref https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/
-- "Smart gaps" / "No gaps when only" — uncomment if you want it.
-- hl.workspace_rule({ workspace = "w[tv1]", gaps_out = 0, gaps_in = 0 })
-- hl.workspace_rule({ workspace = "f[1]", gaps_out = 0, gaps_in = 0 })
-- hl.window_rule({
--     name = "no-gaps-wtv1",
--     match = { float = false, workspace = "w[tv1]" },
--     border_size = 0,
--     rounding = 0,
-- })
-- hl.window_rule({
--     name = "no-gaps-f1",
--     match = { float = false, workspace = "f[1]" },
--     border_size = 0,
--     rounding = 0,
-- })

-- See https://wiki.hypr.land/Configuring/Layouts/Dwindle-Layout/
hl.config({
	dwindle = {
		preserve_split = true, -- You probably want this
	},
})

-- See https://wiki.hypr.land/Configuring/Layouts/Master-Layout/
hl.config({
	master = {
		new_status = "master",
	},
})

----------------
---- MISC ----
----------------

hl.config({
	misc = {
		force_default_wallpaper = -1, -- Set to 0 or 1 to disable the anime mascot wallpapers
		disable_hyprland_logo = false, -- If true, disables the random hyprland logo / anime girl background
	},
})

---------------
---- INPUT ----
---------------

hl.config({
	input = {
		kb_layout = "us",
		kb_variant = "",
		kb_model = "",
		kb_options = "",
		kb_rules = "",

		follow_mouse = 1,

		sensitivity = 0, -- -1.0 - 1.0, 0 means no modification

		touchpad = {
			natural_scroll = false,
		},
	},
})

-- gestures
-- hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })

-- Example per-device config
-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Devices/
hl.device({
	name = "epic-mouse-v1",
	sensitivity = -0.5,
})

---------------------
---- KEYBINDINGS ----
---------------------
-- See https://wiki.hypr.land/Configuring/Basics/Binds/

local mainMod = "SUPER" -- Sets "Windows" key as main modifier

hl.bind(mainMod .. " + Q", hl.dsp.exec_cmd(terminal))
hl.bind(mainMod .. " + C", hl.dsp.window.close())

-- NOTE: the Hyprland wiki now recommends NOT using the raw `exit` dispatcher if you use
-- uwsm, since it can interfere with graceful session shutdown. Consider replacing this
-- with hl.dsp.exec_cmd("uwsm stop") instead.
hl.bind(mainMod .. " + M", hl.dsp.exit())

hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(fileManager))
hl.bind(mainMod .. " + V", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mainMod .. " + R", hl.dsp.exec_cmd(menu))
hl.bind(mainMod .. " + P", hl.dsp.window.pseudo()) -- dwindle
hl.bind(mainMod .. " + J", hl.dsp.layout("togglesplit")) -- dwindle

-- Kando global menu bind.
-- NOTE: `hl.dsp.global` mirrors hyprlang's `global` dispatcher, but this corner of the
-- Lua API is very new/sparsely documented — verify this call works as expected, and
-- check `hyprctl binds` / the Lua stubs if it doesn't register.
hl.bind(mainMod .. " + Space", hl.dsp.global("menu.kando.Kando:hyprland-menu"))

hl.bind("SUPER + minus", hl.dsp.exec_cmd("/home/alzrag/.config/waybar/scripts/waymin/waymin --minimize"))

-- Lock screen with SUPER + L
hl.bind(mainMod .. " + L", hl.dsp.exec_cmd("hyprlock"))

hl.bind(mainMod .. " + F", hl.dsp.window.fullscreen({ mode = 0 }))

-- Move focus with mainMod + arrow keys
hl.bind(mainMod .. " + left", hl.dsp.focus({ direction = "left" }))
hl.bind(mainMod .. " + right", hl.dsp.focus({ direction = "right" }))
hl.bind(mainMod .. " + up", hl.dsp.focus({ direction = "up" }))
hl.bind(mainMod .. " + down", hl.dsp.focus({ direction = "down" }))

hl.bind("SUPER + 1", hl.dsp.exec_cmd("~/.config/hypr/scripts/switch-workspaces.sh 1"))
hl.bind("SUPER + 2", hl.dsp.exec_cmd("~/.config/hypr/scripts/switch-workspaces.sh 2"))
hl.bind("SUPER + 3", hl.dsp.exec_cmd("~/.config/hypr/scripts/switch-workspaces.sh 3"))

hl.bind("SUPER + SHIFT + P", hl.dsp.exec_cmd("~/.config/hypr/scripts/screenshot.sh"))

hl.bind("SUPER + SHIFT + left", hl.dsp.exec_cmd("~/.config/hypr/scripts/move-window-left.sh"))
hl.bind("SUPER + SHIFT + right", hl.dsp.exec_cmd("~/.config/hypr/scripts/move-window-right.sh"))

-- Move active window to a workspace with mainMod + ALT/SHIFT + [num]
hl.bind(mainMod .. " + ALT + 1", hl.dsp.window.move({ workspace = 3 }))
hl.bind(mainMod .. " + ALT + 2", hl.dsp.window.move({ workspace = 5 }))
hl.bind(mainMod .. " + ALT + 3", hl.dsp.window.move({ workspace = 7 }))

hl.bind(mainMod .. " + SHIFT + 4", hl.dsp.window.move({ workspace = 4 }))
hl.bind(mainMod .. " + SHIFT + 5", hl.dsp.window.move({ workspace = 5 }))
hl.bind(mainMod .. " + SHIFT + 6", hl.dsp.window.move({ workspace = 6 }))
hl.bind(mainMod .. " + SHIFT + 7", hl.dsp.window.move({ workspace = 7 }))
hl.bind(mainMod .. " + SHIFT + 8", hl.dsp.window.move({ workspace = 8 }))
hl.bind(mainMod .. " + SHIFT + 9", hl.dsp.window.move({ workspace = 9 }))
hl.bind(mainMod .. " + SHIFT + 0", hl.dsp.window.move({ workspace = 10 }))

-- Example special workspace (scratchpad)
hl.bind(mainMod .. " + S", hl.dsp.workspace.toggle_special("magic"))
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special:magic" }))

-- Scroll through existing workspaces with mainMod + scroll
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + mouse_up", hl.dsp.focus({ workspace = "e-1" }))

-- Move/resize windows with mainMod + LMB/RMB and dragging
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Laptop multimedia keys for volume and LCD brightness
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("/home/alzrag/.config/hypr/scripts/volume-up.sh"))
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("/home/alzrag/.config/hypr/scripts/volume-down.sh"))

hl.bind(
	"XF86AudioMute",
	hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),
	{ locked = true, repeating = true }
)
hl.bind(
	"XF86AudioMicMute",
	hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"),
	{ locked = true, repeating = true }
)
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%+"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%-"), { locked = true, repeating = true })

-- Requires playerctl
hl.bind("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"), { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"), { locked = true })

--------------------------------
---- WINDOWS AND WORKSPACES ----
--------------------------------
-- See https://wiki.hypr.land/Configuring/Basics/Window-Rules/
-- and https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/

-- Ignore maximize requests from all apps.
hl.window_rule({
	name = "suppress-maximize-events",
	match = { class = ".*" },
	suppress_event = "maximize",
})

-- Fix some dragging issues with XWayland
hl.window_rule({
	name = "fix-xwayland-drags",
	match = {
		class = "^$",
		title = "^$",
		xwayland = true,
		float = true,
		fullscreen = false,
		pin = false,
	},
	no_focus = true,
})

hl.window_rule({
	name = "linux-gremlin",
	match = { title = "ilgwg_desktop_gremlins.py" },
	no_blur = true,
	no_shadow = true,
	border_size = 0,
})

-----------------
-- Force certain classes to always tile
-----------------

hl.window_rule({
	name = "tile-minecraft",
	match = { class = "Minecraft.*" },
	tile = true,
})

hl.window_rule({
	name = "tile-steam",
	match = { class = "steam_app_.*" },
	tile = true,
})

hl.window_rule({
	name = "tile-wine",
	match = { class = "Wine" },
	tile = true,
})

hl.window_rule({
	name = "tile-winexe",
	match = { class = ".*\\.exe" },
	tile = true,
})

-- Kando full-screen overlay menu
hl.window_rule({
	name = "kando",
	match = { class = "menu.kando.Kando", title = "Kando Menu" },
	no_blur = true,
	opaque = true,
	move = "0 0",
	rounding = 0,
	size = "100% 100%",
	border_size = 0,
	no_anim = true,
	float = true,
	pin = true,
})

-----------------------------------
---- SPLIT CONFIG FILES ----
-----------------------------------
-- Old hyprlang used `source = ~/.config/hypr/monitors.conf` / workspaces.conf.
-- monitors.lua (nwg-displays generated) is the single source of truth for monitor
-- layout — required here instead of duplicating hl.monitor() calls above.
-- workspaces.lua still needs porting — paste the old workspaces.conf contents if
-- you'd like help converting it.

require("monitors")
-- require("workspaces")
