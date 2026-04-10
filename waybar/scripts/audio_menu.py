#!/usr/bin/env python3

# Force X11 backend for GTK (better compatibility with Hyprland)
import os
os.environ['GDK_BACKEND'] = 'x11'

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
import subprocess
import re
import sys
import json
import os
from pathlib import Path
import struct
import math

# Check for optional imports
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warning: requests module not found, album art from URLs won't work")

# Config file for playlist history
CONFIG_DIR = Path.home() / ".config" / "audio-menu"
PLAYLIST_HISTORY_FILE = CONFIG_DIR / "playlist_history.json"

class AudioVisualizer(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(400, 80)
        self.levels = [0] * 20
        self.connect("draw", self.on_draw)
        GLib.timeout_add(50, self.update_levels)
        
        # Try to monitor audio with pactl
        self.monitor_source = None
        self.setup_audio_monitor()
    
    def setup_audio_monitor(self):
        """Setup audio monitoring from default sink"""
        try:
            # Get default sink monitor
            result = subprocess.run(['pactl', 'get-default-sink'], 
                                  capture_output=True, text=True, timeout=1)
            if result.returncode == 0:
                self.monitor_source = result.stdout.strip() + ".monitor"
        except:
            pass
    
    def update_levels(self):
        """Update visualizer levels from actual audio"""
        try:
            if self.monitor_source:
                # Try to get audio samples
                proc = subprocess.Popen(
                    ['parec', '--format=s16le', '--rate=44100', '--channels=1', 
                     '--device=' + self.monitor_source, '--latency=10'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL
                )
                
                # Read small chunk
                data = proc.stdout.read(4096)
                proc.terminate()
                
                if data:
                    # Convert to 16-bit integers
                    samples = struct.unpack(f'{len(data)//2}h', data)
                    
                    # Split into 20 frequency bands (simplified)
                    chunk_size = len(samples) // 20
                    for i in range(20):
                        start = i * chunk_size
                        end = start + chunk_size
                        chunk = samples[start:end] if end <= len(samples) else samples[start:]
                        
                        # Calculate RMS
                        if chunk:
                            rms = math.sqrt(sum(s*s for s in chunk) / len(chunk))
                            # Normalize to 0-1 range
                            level = min(1.0, rms / 10000)
                            # Smooth transition
                            self.levels[i] = self.levels[i] * 0.7 + level * 0.3
        except Exception as e:
            # Fallback to random for demo purposes
            import random
            for i in range(len(self.levels)):
                change = random.uniform(-0.15, 0.15)
                self.levels[i] = max(0.0, min(1.0, self.levels[i] + change))
        
        self.queue_draw()
        return True
    
    def on_draw(self, widget, cr):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        
        # Background
        cr.set_source_rgb(0.067, 0.067, 0.106)
        cr.rectangle(0, 0, width, height)
        cr.fill()
        
        bar_width = width / 20
        spacing = 2
        
        for i, level in enumerate(self.levels):
            x = i * bar_width
            bar_height = level * height
            
            # Draw gradient from bottom to top
            # Bottom always starts with green
            gradient = cairo.LinearGradient(0, height, 0, height - bar_height)
            
            # Green at bottom (0%)
            gradient.add_color_stop_rgba(0, 0, 1, 0, 1)
            
            if level > 0.2:
                # Blue at 20%
                gradient.add_color_stop_rgba(0.2, 0, 0.5, 1, 1)
            
            if level > 0.4:
                # Yellow at 40%
                gradient.add_color_stop_rgba(0.4, 1, 1, 0, 1)
            
            if level > 0.6:
                # Orange at 60%
                gradient.add_color_stop_rgba(0.6, 1, 0.65, 0, 1)
            
            if level > 0.8:
                # Red at 80%
                gradient.add_color_stop_rgba(0.8, 1, 0, 0, 1)
                # Full red at top
                gradient.add_color_stop_rgba(1.0, 1, 0, 0, 1)
            
            cr.set_source(gradient)
            cr.rectangle(x + spacing/2, height - bar_height, bar_width - spacing, bar_height)
            cr.fill()
        
        return False

# Import cairo for gradient
try:
    import cairo
except ImportError:
    print("Warning: cairo not available for gradients")

class AudioMenu(Gtk.Window):
    def __init__(self):
        super().__init__(title="Audio Control Menu")
        print("Initializing Audio Menu window...")
        
        # Enable decorations temporarily and add close button
        self.set_decorated(True)
        self.set_default_size(700, 650)
        
        # Use NORMAL window type
        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)
        
        # Make window visible
        self.set_keep_above(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        self.connect("key-press-event", self.on_key_press)
        self.connect("delete-event", lambda w, e: Gtk.main_quit())
        
        print("Window properties set...")
        
        print("Window properties set...")
        
        self.current_player = None
        self.seeking = False
        self.app_volumes = {}
        self.playlist_boxes = []
        self.visualizer_bars = []  # Initialize here
        
        # Ensure config directory exists
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        print("Creating main layout...")
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)
        
        self.apply_styling()
        
        print("Creating media section...")
        self.create_media_section(main_box)
        print("Creating playlists section...")
        self.create_playlists_section(main_box)
        print("Creating mixer section...")
        self.create_mixer_section(main_box)
        
        print("Showing window...")
        self.show_all()
        
        # Force window to present itself
        self.present()
        self.present_with_time(Gdk.CURRENT_TIME)
        
        # Grab focus
        self.grab_focus()
        
        print("Window should be visible now!")
        print(f"Window visible: {self.get_visible()}")
        print(f"Window mapped: {self.get_mapped()}")
        print(f"Window size: {self.get_size()}")
        
        GLib.timeout_add(500, self.update_all)
        GLib.timeout_add(5000, self.check_spotify_playlist)
    
    def on_realize(self, widget):
        """Called when window is realized"""
        print("Window realized!")
        # Force window to be visible on Wayland
        window = self.get_window()
        if window:
            window.show()
            window.raise_()
            print("GDK window shown and raised")
    
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
            font-size: 14px;
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
        button.active {
            background-color: #89b4fa;
            color: #11111b;
            font-weight: bold;
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
        
        # Album art
        self.album_art = Gtk.Image()
        self.album_art.set_from_icon_name("audio-x-generic", Gtk.IconSize.DIALOG)
        self.album_art.set_pixel_size(128)
        art_box = Gtk.Box()
        art_box.get_style_context().add_class('media-box')
        art_box.set_size_request(150, 200)
        art_box.pack_start(self.album_art, True, True, 0)
        media_grid.attach(art_box, 0, 0, 1, 4)
        
        controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        media_grid.attach(controls_box, 1, 0, 1, 4)
        
        self.title_label = Gtk.Label(label="No media playing")
        self.title_label.set_markup("<b>No media playing</b>")
        self.title_label.set_line_wrap(True)
        self.title_label.set_max_width_chars(40)
        controls_box.pack_start(self.title_label, False, False, 0)
        
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
        self.progress.connect("button-press-event", self.on_seek_start)
        self.progress.connect("button-release-event", self.on_seek_end)
        controls_box.pack_start(self.progress, False, False, 0)
        
        # Audio visualizer - pixelated gradient bars
        visualizer_box = Gtk.Box()
        visualizer_box.get_style_context().add_class('media-box')
        visualizer_box.set_size_request(400, 80)
        
        # Create 20 vertical bars with pixelated gradient effect
        self.visualizer_bars = []
        bars_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        bars_box.set_halign(Gtk.Align.CENTER)
        bars_box.set_valign(Gtk.Align.END)
        
        for i in range(20):
            bar_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            bar_container.set_size_request(18, 80)
            
            # Create 10 pixel blocks (each 2px wide x variable height)
            pixels = []
            for j in range(10):
                pixel = Gtk.Box()
                pixel.set_size_request(18, 8)  # 2 wide x 8 tall per "pixel"
                
                # Color gradient: Blue -> Blue-Green -> Green -> Green-Yellow -> Yellow -> Orange -> Red
                if j == 0:
                    color = "#0000ff"  # Blue
                elif j == 1:
                    color = "#0088ff"  # Blue-Green
                elif j == 2:
                    color = "#00ff00"  # Green
                elif j == 3:
                    color = "#88ff00"  # Green-Yellow
                elif j == 4:
                    color = "#ffff00"  # Yellow
                elif j == 5:
                    color = "#ffdd00"  # Yellow-Orange
                elif j == 6:
                    color = "#ffaa00"  # Orange
                elif j == 7:
                    color = "#ff8800"  # Orange
                elif j == 8:
                    color = "#ff4400"  # Orange-Red
                else:
                    color = "#ff0000"  # Red
                
                # Use CSS instead of deprecated method
                css_provider = Gtk.CssProvider()
                css = f"box {{ background-color: {color}; }}".encode()
                css_provider.load_from_data(css)
                pixel.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
                
                pixel.set_no_show_all(True)  # Hide by default
                pixels.append(pixel)
                bar_container.pack_end(pixel, False, False, 0)
            
            self.visualizer_bars.append(pixels)
            bars_box.pack_start(bar_container, False, False, 0)
        
        visualizer_box.pack_start(bars_box, True, True, 0)
        controls_box.pack_start(visualizer_box, False, False, 0)
        
        # Start visualizer animation
        GLib.timeout_add(100, self.update_visualizer)
    
    def update_visualizer(self):
        """Update visualizer bars based on actual audio output levels"""
        try:
            # Get the default sink name
            default_sink = self.run_cmd(['pactl', 'get-default-sink'])
            if not default_sink:
                # Fallback to minimal animation
                import random
                for bar_pixels in self.visualizer_bars:
                    height = random.randint(1, 3)
                    for i, pixel in enumerate(bar_pixels):
                        pixel.show() if i < height else pixel.hide()
                return True
            
            # Get volume levels from the monitor source
            monitor_source = default_sink + ".monitor"
            
            # Use pactl to get instantaneous volume/sample data
            # This reads a tiny sample to detect audio activity
            proc = subprocess.Popen(
                ['pacat', '--record', '--device=' + monitor_source, '--format=s16le', 
                 '--rate=44100', '--channels=1', '--latency-msec=50'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            
            # Read a small chunk (0.05 seconds worth)
            chunk_size = 4410  # 44100 samples/sec * 0.05 sec * 2 bytes
            data = proc.stdout.read(chunk_size)
            proc.terminate()
            proc.wait()
            
            if data and len(data) >= 40:
                # Convert bytes to 16-bit integers
                import struct
                samples = struct.unpack(f'{len(data)//2}h', data)
                
                # Split into 20 frequency bands
                band_size = len(samples) // 20
                
                for i, bar_pixels in enumerate(self.visualizer_bars):
                    # Get samples for this band
                    start = i * band_size
                    end = start + band_size
                    band_samples = samples[start:end] if end <= len(samples) else samples[start:]
                    
                    if band_samples:
                        # Calculate RMS (root mean square) for this band
                        import math
                        rms = math.sqrt(sum(s*s for s in band_samples) / len(band_samples))
                        
                        # Normalize to 1-10 range
                        # Typical range for 16-bit audio is ~0-32768
                        normalized = int((rms / 3200) * 10)  # Scale factor adjusted for sensitivity
                        height = max(1, min(10, normalized))
                    else:
                        height = 1
                    
                    # Show pixels up to height
                    for j, pixel in enumerate(bar_pixels):
                        pixel.show() if j < height else pixel.hide()
            else:
                # No data, show minimal
                for bar_pixels in self.visualizer_bars:
                    for j, pixel in enumerate(bar_pixels):
                        pixel.show() if j < 1 else pixel.hide()
                        
        except Exception as e:
            # Fallback animation
            import random
            for bar_pixels in self.visualizer_bars:
                height = random.randint(1, 4)
                for i, pixel in enumerate(bar_pixels):
                    pixel.show() if i < height else pixel.hide()
        
        return True
    
    def create_playlists_section(self, parent):
        self.playlists_section = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.playlists_section.get_style_context().add_class('section')
        parent.pack_start(self.playlists_section, False, False, 0)
        
        self.update_playlists_display()
    
    def update_playlists_display(self):
        """Update playlist display with actual Spotify data"""
        # Clear existing
        for child in self.playlists_section.get_children():
            self.playlists_section.remove(child)
        
        # Load history
        history = self.load_playlist_history()
        
        # Create boxes for current and last 2 playlists
        for i, (label_text, icon) in enumerate([
            ("Current Playlist", "🎵"),
            ("Last Played", "⏮"),
            ("Recent", "⏮⏮")
        ]):
            playlist_data = history[i] if i < len(history) else None
            box = self.create_playlist_box_with_data(playlist_data, label_text, icon)
            self.playlists_section.pack_start(box, True, True, 0)
        
        self.playlists_section.show_all()
    
    def create_playlist_box_with_data(self, playlist_data, default_title, default_icon):
        """Create a playlist box with actual data or defaults"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.get_style_context().add_class('media-box')
        box.set_size_request(150, 120)
        
        # Image or icon
        if playlist_data and 'image_url' in playlist_data and playlist_data['image_url']:
            image = Gtk.Image()
            try:
                if HAS_REQUESTS:
                    response = requests.get(playlist_data['image_url'], timeout=2)
                    loader = GdkPixbuf.PixbufLoader()
                    loader.write(response.content)
                    loader.close()
                    pixbuf = loader.get_pixbuf()
                    scaled = pixbuf.scale_simple(80, 80, GdkPixbuf.InterpType.BILINEAR)
                    image.set_from_pixbuf(scaled)
                else:
                    image.set_from_icon_name("folder-music", Gtk.IconSize.DIALOG)
                    image.set_pixel_size(80)
            except:
                image.set_from_icon_name("folder-music", Gtk.IconSize.DIALOG)
                image.set_pixel_size(80)
            box.pack_start(image, True, True, 0)
        else:
            # Use label for emoji icon
            icon_label = Gtk.Label(label=default_icon)
            icon_label.set_markup(f"<span size='xx-large'>{default_icon}</span>")
            box.pack_start(icon_label, True, True, 0)
        
        # Title
        title = playlist_data['name'] if playlist_data and 'name' in playlist_data else default_title
        title_label = Gtk.Label(label=title[:30])
        title_label.set_line_wrap(True)
        title_label.set_max_width_chars(20)
        title_label.set_ellipsize(3)
        box.pack_start(title_label, False, False, 0)
        
        return box
    
    def load_playlist_history(self):
        """Load playlist history from file"""
        try:
            if PLAYLIST_HISTORY_FILE.exists():
                with open(PLAYLIST_HISTORY_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_playlist_history(self, history):
        """Save playlist history to file"""
        try:
            with open(PLAYLIST_HISTORY_FILE, 'w') as f:
                json.dump(history[:3], f, indent=2)  # Keep only last 3
        except Exception as e:
            print(f"Error saving playlist history: {e}")
    
    def check_spotify_playlist(self):
        """Check current Spotify playlist and update history"""
        try:
            # Check if spotify is playing
            if self.current_player and 'spotify' in self.current_player.lower():
                # Get playlist info from metadata
                playlist_title = self.run_cmd(['playerctl', '-p', self.current_player, 
                                              'metadata', 'xesam:album'])
                art_url = self.run_cmd(['playerctl', '-p', self.current_player, 
                                       'metadata', 'mpris:artUrl'])
                
                if playlist_title:
                    history = self.load_playlist_history()
                    
                    # Check if this is a new playlist
                    if not history or history[0].get('name') != playlist_title:
                        new_entry = {
                            'name': playlist_title,
                            'image_url': art_url if art_url else None
                        }
                        
                        # Add to front, shift others back
                        history.insert(0, new_entry)
                        history = history[:3]  # Keep only 3
                        
                        self.save_playlist_history(history)
                        self.update_playlists_display()
        except Exception as e:
            print(f"Error checking playlist: {e}")
        
        return True
    
    def create_mixer_section(self, parent):
        self.mixer_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.mixer_section.get_style_context().add_class('section')
        parent.pack_start(self.mixer_section, True, True, 0)
        
        self.app_sliders = []
        self.device_sliders = []
        
        self.update_mixer()
    
    def update_mixer(self):
        """Update mixer section with apps and devices"""
        # Get current state
        current_apps = self.get_audio_applications()
        current_devices = self.get_audio_devices()
        
        # Check if we need to rebuild (different number of items)
        rebuild_needed = (len(self.app_sliders) != len(current_apps[:2]) or 
                         len(self.device_sliders) != len(current_devices[:3]))
        
        if not rebuild_needed:
            # Update existing sliders with current values
            for i, (old_app, app_box) in enumerate(self.app_sliders):
                if i < len(current_apps):
                    new_app = current_apps[i]
                    # Find the scale widget and update it
                    for child in app_box.get_children():
                        if isinstance(child, Gtk.Scale):
                            # Only update if value changed significantly (avoid feedback loop)
                            current_val = child.get_value()
                            if abs(current_val - new_app['volume']) > 2:
                                child.set_value(new_app['volume'])
            
            for i, (old_device, device_box) in enumerate(self.device_sliders):
                if i < len(current_devices):
                    new_device = current_devices[i]
                    # Find the scale widget and update it
                    for child in device_box.get_children():
                        if isinstance(child, Gtk.Scale):
                            current_val = child.get_value()
                            if abs(current_val - new_device['volume']) > 2:
                                child.set_value(new_device['volume'])
                        # Update star button
                        if isinstance(child, Gtk.Button):
                            is_default = new_device.get('is_default', False)
                            child.set_label("★" if is_default else "☆")
                            if is_default:
                                child.get_style_context().add_class('active')
                            else:
                                child.get_style_context().remove_class('active')
            return
        
        # Full rebuild only when structure changes
        for child in self.mixer_section.get_children():
            self.mixer_section.remove(child)
        
        self.app_sliders = []
        self.device_sliders = []
        
        # Get and display applications
        apps = current_apps
        if apps:
            app_label = Gtk.Label()
            app_label.set_markup("<b>Applications</b>")
            app_label.set_xalign(0)
            self.mixer_section.pack_start(app_label, False, False, 2)
            
            for i, app in enumerate(apps[:2]):
                try:
                    app_box = self.create_app_volume_slider(app, i)
                    self.mixer_section.pack_start(app_box, False, False, 0)
                    self.app_sliders.append((app, app_box))
                except Exception as e:
                    print(f"Error creating app slider: {e}")
        
        self.mixer_section.pack_start(Gtk.Separator(), False, False, 5)
        
        # Get and display devices
        devices = current_devices
        if devices:
            device_label = Gtk.Label()
            device_label.set_markup("<b>Output Devices</b>")
            device_label.set_xalign(0)
            self.mixer_section.pack_start(device_label, False, False, 2)
            
            for device in devices[:3]:  # Show 3 devices
                try:
                    device_box = self.create_device_volume_slider(device)
                    self.mixer_section.pack_start(device_box, False, False, 0)
                    self.device_sliders.append((device, device_box))
                except Exception as e:
                    print(f"Error creating device slider: {e}")
        
        self.mixer_section.show_all()
    
    def create_app_volume_slider(self, app, index):
        """Create volume slider for application with output device dropdown"""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_top(5)
        box.set_margin_bottom(5)
        
        label = Gtk.Label(label=app['name'][:30])
        label.set_size_request(150, -1)
        label.set_xalign(0)
        label.set_ellipsize(3)
        box.pack_start(label, False, False, 0)
        
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        scale.set_range(0, 100)
        scale.set_value(app['volume'])
        scale.set_draw_value(True)
        scale.set_value_pos(Gtk.PositionType.RIGHT)
        scale.connect("value-changed", lambda s, aid=app['id']: self.set_app_volume(aid, s.get_value()))
        box.pack_start(scale, True, True, 0)
        
        # Get current sink for this app
        current_sink = None
        try:
            sink_output = self.run_cmd(['pactl', 'list', 'sink-inputs'])
            in_our_input = False
            for line in sink_output.split('\n'):
                if f'Sink Input #{app["id"]}' in line:
                    in_our_input = True
                elif in_our_input and 'Sink:' in line:
                    current_sink = line.split('Sink:')[1].strip()
                    break
                elif in_our_input and line.strip().startswith('Sink Input'):
                    break
        except:
            pass
        
        # Device routing dropdown with current selection shown
        menu_button = Gtk.MenuButton()
        
        menu = Gtk.Menu()
        devices = self.get_audio_sinks()
        
        # Find current device name
        current_device_name = "Output"
        for device in devices:
            if current_sink and (device['pactl_name'] == current_sink or device['id'] in current_sink):
                current_device_name = device['name'][:20]
                break
        
        menu_button.set_label(f"{current_device_name} →")
        
        try:
            for device in devices:
                item = Gtk.MenuItem(label=device['name'][:40])
                item.connect("activate", lambda w, aid=app['id'], sid=device['id']: self.route_app_to_sink(aid, sid))
                menu.append(item)
            menu.show_all()
            menu_button.set_popup(menu)
        except Exception as e:
            print(f"Error populating device menu: {e}")
        
        box.pack_start(menu_button, False, False, 0)
        
        return box
    
    def create_device_volume_slider(self, device):
        """Create volume slider for output device with set-default button"""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_top(5)
        box.set_margin_bottom(5)
        
        label = Gtk.Label(label=device['name'][:30])
        label.set_size_request(150, -1)
        label.set_xalign(0)
        label.set_ellipsize(3)
        box.pack_start(label, False, False, 0)
        
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        scale.set_range(0, 100)
        scale.set_value(device['volume'])
        scale.set_draw_value(True)
        scale.set_value_pos(Gtk.PositionType.RIGHT)
        scale.connect("value-changed", lambda s, did=device['id']: self.set_device_volume(did, s.get_value()))
        box.pack_start(scale, True, True, 0)
        
        btn = Gtk.Button(label="★" if device.get('is_default', False) else "☆")
        btn.set_tooltip_text("Set as active device (for volume keys)")
        if device.get('is_default', False):
            btn.get_style_context().add_class('active')
        btn.connect("clicked", lambda b, did=device['id']: self.set_default_sink(did))
        box.pack_start(btn, False, False, 0)
        
        return box
    
    def run_cmd(self, cmd):
        """Safely run a command and return output"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            return result.stdout.strip()
        except Exception as e:
            return ""
    
    def get_active_player(self):
        """Get the most recently active player"""
        try:
            output = self.run_cmd(['playerctl', '-l'])
            if not output:
                return None
            
            players = output.split('\n')
            
            for player in players:
                if player:
                    status = self.run_cmd(['playerctl', '-p', player, 'status'])
                    if status == 'Playing':
                        return player
            
            return players[0] if players and players[0] else None
        except Exception as e:
            print(f"Error getting active player: {e}")
            return None
    
    def get_audio_applications(self):
        """Get list of audio sink-inputs using pactl"""
        apps = []
        try:
            # Use pactl to get sink inputs (playing applications)
            output = self.run_cmd(['pactl', 'list', 'sink-inputs'])
            if not output:
                return apps
            
            # Parse the output
            current_id = None
            current_name = None
            current_volume = 50
            
            for line in output.split('\n'):
                line = line.strip()
                
                # Get sink input ID
                if line.startswith('Sink Input #'):
                    if current_id and current_name:
                        apps.append({
                            'id': current_id,
                            'name': current_name,
                            'volume': current_volume
                        })
                    current_id = line.split('#')[1]
                    current_name = None
                    current_volume = 50
                
                # Get application name
                elif 'application.name =' in line:
                    current_name = line.split('=')[1].strip().strip('"')
                
                # Get volume
                elif 'Volume:' in line and '%' in line:
                    # Extract percentage
                    import re
                    match = re.search(r'(\d+)%', line)
                    if match:
                        current_volume = int(match.group(1))
            
            # Add last app
            if current_id and current_name:
                apps.append({
                    'id': current_id,
                    'name': current_name,
                    'volume': current_volume
                })
                
        except Exception as e:
            print(f"Error getting applications: {e}")
        
        # Sort by current player
        try:
            current_player = self.get_active_player()
            if current_player:
                player_name = current_player.lower().split('.')[0]
                apps.sort(key=lambda x: 0 if player_name in x['name'].lower() else 1)
        except:
            pass
        
        return apps
    
    def get_audio_devices(self):
        """Get audio output devices in specific order: Ryzen HD, OnePlus Buds, HDMI"""
        devices = []
        all_devices = []
        
        try:
            output = self.run_cmd(['wpctl', 'status'])
            if not output:
                return devices
            
            lines = output.split('\n')
            in_sinks = False
            
            for line in lines:
                if 'Sinks:' in line or 'Audio/Sink' in line:
                    in_sinks = True
                    continue
                
                if in_sinks:
                    if line.strip() == '' or (line.strip() and not line.startswith(' ') and ':' in line):
                        break
                    
                    is_default = '*' in line
                    match = re.search(r'(\d+)\.\s+(.+)', line)
                    if match:
                        device_id = match.group(1)
                        device_name = match.group(2).strip()
                        device_name = re.sub(r'<.*?>|\[.*?\]|\*', '', device_name).strip()
                        
                        vol_output = self.run_cmd(['wpctl', 'get-volume', device_id])
                        volume = 50
                        if vol_output:
                            vol_match = re.search(r'([\d.]+)', vol_output)
                            if vol_match:
                                volume = float(vol_match.group(1)) * 100
                        
                        all_devices.append({
                            'id': device_id,
                            'name': device_name if device_name else f"Device {device_id}",
                            'volume': volume,
                            'is_default': is_default
                        })
        except Exception as e:
            print(f"Error getting devices: {e}")
        
        # Find specific devices in order
        priority_order = [
            ('ryzen', 'hd'),
            ('oneplus', 'buds'),
            ('hdmi',)
        ]
        
        for keywords in priority_order:
            for device in all_devices:
                name_lower = device['name'].lower()
                if all(kw in name_lower for kw in keywords) and device not in devices:
                    devices.append(device)
                    break
        
        # Return exactly 3 devices (pad with remaining if needed)
        remaining = [d for d in all_devices if d not in devices]
        devices.extend(remaining)
        
        return devices[:3]
    
    def get_audio_sinks(self):
        """Get all available audio sinks using pactl"""
        sinks = []
        try:
            output = self.run_cmd(['pactl', 'list', 'short', 'sinks'])
            if not output:
                return sinks
            
            for line in output.split('\n'):
                if line.strip():
                    # Format: INDEX NAME DRIVER SAMPLE_SPEC STATE
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        sink_index = parts[0]
                        sink_name = parts[1]
                        
                        # Get human-readable description
                        desc_output = self.run_cmd(['pactl', 'list', 'sinks'])
                        description = sink_name
                        
                        # Parse for description of this sink
                        in_sink = False
                        for desc_line in desc_output.split('\n'):
                            if f'Name: {sink_name}' in desc_line:
                                in_sink = True
                            elif in_sink and 'Description:' in desc_line:
                                description = desc_line.split('Description:')[1].strip()
                                break
                            elif in_sink and desc_line.strip().startswith('Name:'):
                                break
                        
                        sinks.append({
                            'id': sink_index,
                            'name': description,
                            'pactl_name': sink_name
                        })
        except Exception as e:
            print(f"Error getting sinks: {e}")
        
        return sinks
    
    def route_app_to_sink(self, app_id, sink_id):
        """Route app to specific sink using pactl"""
        if sink_id:
            try:
                result = subprocess.run(['pactl', 'move-sink-input', str(app_id), str(sink_id)], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    print(f"Routed app {app_id} to sink {sink_id}")
                    # Force mixer refresh to update button label
                    GLib.timeout_add(100, lambda: (self.update_mixer(), False)[1])
            except Exception as e:
                print(f"Error routing: {e}")
    
    def set_default_sink(self, device_id):
        """Set default sink"""
        try:
            result = subprocess.run(['wpctl', 'set-default', str(device_id)], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                print(f"Set default sink to {device_id}")
                # Force immediate refresh
                GLib.timeout_add(200, self.update_mixer)
        except Exception as e:
            print(f"Error setting default: {e}")
    
    def load_album_art(self, url):
        """Load album art"""
        try:
            if url and url.startswith('http') and HAS_REQUESTS:
                response = requests.get(url, timeout=2)
                loader = GdkPixbuf.PixbufLoader()
                loader.write(response.content)
                loader.close()
                pixbuf = loader.get_pixbuf()
                scaled = pixbuf.scale_simple(128, 128, GdkPixbuf.InterpType.BILINEAR)
                self.album_art.set_from_pixbuf(scaled)
                return
            elif url and url.startswith('file://'):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(url[7:], 128, 128)
                self.album_art.set_from_pixbuf(pixbuf)
                return
        except Exception as e:
            print(f"Error loading album art: {e}")
        
        # Fallback
        if self.current_player:
            player_lower = self.current_player.lower()
            if 'spotify' in player_lower:
                self.album_art.set_from_icon_name("spotify", Gtk.IconSize.DIALOG)
            elif any(browser in player_lower for browser in ['firefox', 'opera', 'chrome', 'chromium']):
                browser = next((b for b in ['firefox', 'opera-browser', 'chromium', 'google-chrome'] if b in player_lower), 'web-browser')
                self.album_art.set_from_icon_name(browser, Gtk.IconSize.DIALOG)
            else:
                self.album_art.set_from_icon_name("audio-x-generic", Gtk.IconSize.DIALOG)
        else:
            self.album_art.set_from_icon_name("audio-x-generic", Gtk.IconSize.DIALOG)
    
    def playerctl_cmd(self, cmd):
        if self.current_player:
            try:
                subprocess.run(['playerctl', '-p', self.current_player, cmd], timeout=2)
            except Exception as e:
                print(f"Playerctl error: {e}")
    
    def set_app_volume(self, app_id, volume):
        try:
            # Use pactl for sink-inputs
            subprocess.run(['pactl', 'set-sink-input-volume', str(app_id), f'{int(volume)}%'], timeout=2)
        except Exception as e:
            print(f"Error setting app volume: {e}")
    
    def set_device_volume(self, device_id, volume):
        try:
            subprocess.run(['wpctl', 'set-volume', str(device_id), f'{volume/100:.2f}'], timeout=2)
        except Exception as e:
            print(f"Error setting device volume: {e}")
    
    def on_seek_start(self, scale, event):
        self.seeking = True
        return False
    
    def on_seek_end(self, scale, event):
        if self.seeking and self.current_player:
            try:
                length_str = self.run_cmd(['playerctl', '-p', self.current_player, 'metadata', 'mpris:length'])
                if length_str and length_str.isdigit():
                    length_sec = int(length_str) / 1000000
                    position_sec = (scale.get_value() / 100) * length_sec
                    subprocess.run(['playerctl', '-p', self.current_player, 'position', str(position_sec)], timeout=2)
            except Exception as e:
                print(f"Seek error: {e}")
        
        self.seeking = False
        return False
    
    def update_all(self):
        try:
            self.update_media_info()
            self.update_mixer()
        except Exception as e:
            print(f"Update error: {e}")
        return True
    
    def update_media_info(self):
        new_player = self.get_active_player()
        if new_player != self.current_player:
            self.current_player = new_player
        
        if not self.current_player:
            self.title_label.set_markup("<b>No media playing</b>")
            self.load_album_art(None)
            return
        
        try:
            title = self.run_cmd(['playerctl', '-p', self.current_player, 'metadata', 'title'])
            artist = self.run_cmd(['playerctl', '-p', self.current_player, 'metadata', 'artist'])
            
            if title:
                markup = f"<b>{GLib.markup_escape_text(title)}</b>"
                if artist:
                    markup += f"\n{GLib.markup_escape_text(artist)}"
                self.title_label.set_markup(markup)
            
            art_url = self.run_cmd(['playerctl', '-p', self.current_player, 'metadata', 'mpris:artUrl'])
            self.load_album_art(art_url if art_url else None)
            
            if not self.seeking:
                position = self.run_cmd(['playerctl', '-p', self.current_player, 'position'])
                length = self.run_cmd(['playerctl', '-p', self.current_player, 'metadata', 'mpris:length'])
                
                if position and length and position.replace('.', '').isdigit() and length.isdigit():
                    pos_sec = float(position)
                    len_sec = int(length) / 1000000
                    if len_sec > 0:
                        self.progress.set_value((pos_sec / len_sec) * 100)
        except Exception as e:
            print(f"Media update error: {e}")
    
    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
        return False

def main():
    print("Starting Audio Menu application...")
    try:
        print("Creating window instance...")
        win = AudioMenu()
        print("Window created successfully!")
        win.connect("destroy", Gtk.main_quit)
        print("Starting GTK main loop...")
        Gtk.main()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
