#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import subprocess
import json
import re
from pathlib import Path

class AudioMenu(Gtk.Window):
    def __init__(self):
        super().__init__(title="Audio Control")
        self.set_decorated(False)
        self.set_default_size(700, 600)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        
        # Make window appear above other windows
        self.set_keep_above(True)
        
        # Position at cursor or center
        self.set_position(Gtk.WindowPosition.MOUSE)
        
        # Connect focus-out to close
        self.connect("focus-out-event", lambda w, e: self.destroy())
        self.connect("key-press-event", self.on_key_press)
        
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)
        
        # Apply CSS styling
        self.apply_styling()
        
        # Create all sections
        self.create_media_section(main_box)
        self.create_playlists_section(main_box)
        self.create_mixer_section(main_box)
        
        self.show_all()
        
        # Start periodic updates
        GLib.timeout_add(1000, self.update_all)
    
    def apply_styling(self):
        css_provider = Gtk.CssProvider()
        css = b"""
        window {
            background-color: #1e1e2e;
            border: 2px solid #89b4fa;
            border-radius: 10px;
        }
        .section {
            padding: 10px;
            margin: 5px;
            background-color: #181825;
            border-radius: 8px;
        }
        .media-box {
            background-color: #11111b;
            border-radius: 6px;
            padding: 10px;
        }
        label {
            color: #cdd6f4;
        }
        button {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 8px;
            min-width: 40px;
            min-height: 40px;
        }
        button:hover {
            background-color: #45475a;
        }
        scale {
            min-width: 200px;
        }
        scale trough {
            min-height: 8px;
            background-color: #313244;
            border-radius: 4px;
        }
        scale highlight {
            background-color: #89b4fa;
            border-radius: 4px;
        }
        """
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def create_media_section(self, parent):
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        section.get_style_context().add_class('section')
        parent.pack_start(section, False, False, 0)
        
        media_grid = Gtk.Grid()
        media_grid.set_column_spacing(10)
        media_grid.set_row_spacing(5)
        section.pack_start(media_grid, False, False, 0)
        
        # Album art / thumbnail (left side)
        self.album_art = Gtk.Image()
        self.album_art.set_from_icon_name("audio-x-generic", Gtk.IconSize.DIALOG)
        self.album_art.set_pixel_size(128)
        art_box = Gtk.Box()
        art_box.get_style_context().add_class('media-box')
        art_box.set_size_request(150, 200)
        art_box.pack_start(self.album_art, True, True, 0)
        media_grid.attach(art_box, 0, 0, 1, 4)
        
        # Media info and controls (right side)
        controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        media_grid.attach(controls_box, 1, 0, 1, 4)
        
        # Title and artist
        self.title_label = Gtk.Label(label="No media playing")
        self.title_label.set_markup("<b>No media playing</b>")
        self.title_label.set_line_wrap(True)
        controls_box.pack_start(self.title_label, False, False, 0)
        
        # Playback controls
        playback_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        playback_box.set_halign(Gtk.Align.CENTER)
        controls_box.pack_start(playback_box, False, False, 0)
        
        self.prev_btn = Gtk.Button(label="⏮")
        self.prev_btn.connect("clicked", lambda b: self.playerctl_cmd("previous"))
        playback_box.pack_start(self.prev_btn, False, False, 0)
        
        self.play_pause_btn = Gtk.Button(label="⏯")
        self.play_pause_btn.connect("clicked", lambda b: self.playerctl_cmd("play-pause"))
        playback_box.pack_start(self.play_pause_btn, False, False, 0)
        
        self.next_btn = Gtk.Button(label="⏭")
        self.next_btn.connect("clicked", lambda b: self.playerctl_cmd("next"))
        playback_box.pack_start(self.next_btn, False, False, 0)
        
        # Progress bar
        self.progress = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.progress.set_range(0, 100)
        self.progress.set_draw_value(False)
        self.progress.connect("change-value", self.on_seek)
        controls_box.pack_start(self.progress, False, False, 0)
        
        # Audio visualizer placeholder
        visualizer_box = Gtk.Box()
        visualizer_box.get_style_context().add_class('media-box')
        visualizer_box.set_size_request(400, 80)
        visualizer_label = Gtk.Label(label="🎵 Audio Visualizer")
        visualizer_box.pack_start(visualizer_label, True, True, 0)
        controls_box.pack_start(visualizer_box, False, False, 0)
    
    def create_playlists_section(self, parent):
        section = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        section.get_style_context().add_class('section')
        parent.pack_start(section, False, False, 0)
        
        # Current playlist
        current_box = self.create_playlist_box("Current Playlist", "🎵")
        section.pack_start(current_box, True, True, 0)
        
        # Last played
        last_box = self.create_playlist_box("Last Played", "⏮")
        section.pack_start(last_box, True, True, 0)
        
        # Second to last
        second_box = self.create_playlist_box("Recent", "⏮⏮")
        section.pack_start(second_box, True, True, 0)
        
        # Scroll arrow for more
        scroll_btn = Gtk.Button(label="→")
        scroll_btn.set_tooltip_text("More playlists")
        section.pack_start(scroll_btn, False, False, 0)
    
    def create_playlist_box(self, title, icon):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.get_style_context().add_class('media-box')
        
        icon_label = Gtk.Label(label=icon)
        icon_label.set_markup(f"<span size='xx-large'>{icon}</span>")
        box.pack_start(icon_label, True, True, 0)
        
        title_label = Gtk.Label(label=title)
        box.pack_start(title_label, False, False, 0)
        
        return box
    
    def create_mixer_section(self, parent):
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        section.get_style_context().add_class('section')
        parent.pack_start(section, True, True, 0)
        
        # Get audio applications and devices
        apps = self.get_audio_applications()
        devices = self.get_audio_devices()
        
        # Create sliders for applications
        for app in apps[:2]:  # Limit to 2 apps as per mockup
            app_box = self.create_volume_slider(
                app['name'],
                app['volume'],
                lambda v, id=app['id']: self.set_app_volume(id, v),
                app.get('devices', [])
            )
            section.pack_start(app_box, False, False, 0)
        
        section.pack_start(Gtk.Separator(), False, False, 5)
        
        # Create sliders for output devices
        for device in devices[:2]:  # Limit to 2 devices as per mockup
            device_box = self.create_volume_slider(
                device['name'],
                device['volume'],
                lambda v, id=device['id']: self.set_device_volume(id, v),
                None,
                device.get('is_default', False)
            )
            section.pack_start(device_box, False, False, 0)
    
    def create_volume_slider(self, name, volume, callback, devices=None, is_default=False):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_top(5)
        box.set_margin_bottom(5)
        
        # Name label
        label = Gtk.Label(label=name)
        label.set_size_request(150, -1)
        label.set_xalign(0)
        box.pack_start(label, False, False, 0)
        
        # Volume slider
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        scale.set_range(0, 100)
        scale.set_value(volume)
        scale.set_draw_value(True)
        scale.set_value_pos(Gtk.PositionType.RIGHT)
        scale.connect("value-changed", lambda s: callback(s.get_value()))
        box.pack_start(scale, True, True, 0)
        
        # Device dropdown or set active button
        if devices is not None:
            combo = Gtk.ComboBoxText()
            for device in devices:
                combo.append_text(device)
            if devices:
                combo.set_active(0)
            box.pack_start(combo, False, False, 0)
        else:
            btn = Gtk.Button(label="★" if is_default else "☆")
            btn.set_tooltip_text("Set as active device")
            box.pack_start(btn, False, False, 0)
        
        return box
    
    def get_audio_applications(self):
        """Get list of audio applications using wpctl"""
        apps = []
        try:
            result = subprocess.run(['wpctl', 'status'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            in_sinks = False
            for line in lines:
                if 'Sink inputs:' in line or 'Streams:' in line:
                    in_sinks = True
                    continue
                elif in_sinks and line.strip().startswith('│'):
                    continue
                elif in_sinks and '.' in line:
                    match = re.search(r'(\d+)\.\s+(.+?)\s+\[.*vol:\s+([\d.]+)', line)
                    if match:
                        apps.append({
                            'id': match.group(1),
                            'name': match.group(2).strip(),
                            'volume': float(match.group(3)) * 100
                        })
                elif in_sinks and (line.strip() == '' or not line.startswith(' ')):
                    break
        except Exception as e:
            print(f"Error getting applications: {e}")
        
        return apps if apps else [
            {'id': '0', 'name': 'Spotify', 'volume': 80},
            {'id': '1', 'name': 'Application 2', 'volume': 60}
        ]
    
    def get_audio_devices(self):
        """Get list of audio output devices"""
        devices = []
        try:
            result = subprocess.run(['wpctl', 'status'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            in_sinks = False
            for line in lines:
                if 'Sinks:' in line:
                    in_sinks = True
                    continue
                elif in_sinks and ('*' in line or '.' in line):
                    is_default = '*' in line
                    match = re.search(r'(\d+)\.\s+(.+?)\s+\[.*vol:\s+([\d.]+)', line)
                    if match:
                        devices.append({
                            'id': match.group(1),
                            'name': match.group(2).strip(),
                            'volume': float(match.group(3)) * 100,
                            'is_default': is_default
                        })
                elif in_sinks and line.strip() == '':
                    break
        except Exception as e:
            print(f"Error getting devices: {e}")
        
        return devices if devices else [
            {'id': '0', 'name': 'Output Device 1', 'volume': 75, 'is_default': True},
            {'id': '1', 'name': 'Output Device 2', 'volume': 50, 'is_default': False}
        ]
    
    def playerctl_cmd(self, cmd):
        try:
            subprocess.run(['playerctl', cmd], check=True)
        except Exception as e:
            print(f"Playerctl error: {e}")
    
    def set_app_volume(self, app_id, volume):
        try:
            subprocess.run(['wpctl', 'set-volume', app_id, f'{volume/100:.2f}'])
        except Exception as e:
            print(f"Error setting app volume: {e}")
    
    def set_device_volume(self, device_id, volume):
        try:
            subprocess.run(['wpctl', 'set-volume', device_id, f'{volume/100:.2f}'])
        except Exception as e:
            print(f"Error setting device volume: {e}")
    
    def on_seek(self, scale, scroll_type, value):
        # Implement seeking with playerctl
        try:
            subprocess.run(['playerctl', 'position', str(value)])
        except:
            pass
        return False
    
    def update_all(self):
        self.update_media_info()
        return True
    
    def update_media_info(self):
        try:
            # Get current track info
            title = subprocess.run(['playerctl', 'metadata', 'title'], 
                                 capture_output=True, text=True).stdout.strip()
            artist = subprocess.run(['playerctl', 'metadata', 'artist'], 
                                  capture_output=True, text=True).stdout.strip()
            
            if title:
                self.title_label.set_markup(f"<b>{title}</b>\n{artist}")
            
            # Get position and length
            position = subprocess.run(['playerctl', 'position'], 
                                    capture_output=True, text=True).stdout.strip()
            length = subprocess.run(['playerctl', 'metadata', 'mpris:length'], 
                                  capture_output=True, text=True).stdout.strip()
            
            if position and length:
                pos_sec = float(position)
                len_sec = float(length) / 1000000
                if len_sec > 0:
                    self.progress.set_value((pos_sec / len_sec) * 100)
        except:
            pass
    
    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
        return False

def main():
    win = AudioMenu()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()

if __name__ == '__main__':
    main()
