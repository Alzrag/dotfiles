#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <array>
#include <memory>
#include <filesystem>
#include <algorithm>
#include <cctype>
#include <unistd.h>

namespace fs = std::filesystem;

// System Execution Helper
std::string exec_cmd(const std::string& cmd) {
    std::array<char, 128> buffer;
    std::string result;
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd.c_str(), "r"), pclose);
    if (!pipe) return "";
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }
    return result;
}

// Flat JSON Parsing Utilities for Hyprland Output
std::vector<std::string> split_json_objects(const std::string& json_array) {
    std::vector<std::string> objects;
    int brace_count = 0;
    std::string current_obj = "";
    bool in_quotes = false;

    for (size_t i = 0; i < json_array.length(); ++i) {
        char c = json_array[i];
        if (c == '"' && (i == 0 || json_array[i-1] != '\\')) {
            in_quotes = !in_quotes;
        }
        if (!in_quotes) {
            if (c == '{') brace_count++;
        }
        if (brace_count > 0) current_obj += c;
        if (!in_quotes) {
            if (c == '}') {
                brace_count--;
                if (brace_count == 0) {
                    objects.push_back(current_obj);
                    current_obj = "";
                }
            }
        }
    }
    return objects;
}

std::string extract_key_string(const std::string& obj, const std::string& key) {
    std::string search_key = "\"" + key + "\":";
    size_t pos = obj.find(search_key);
    if (pos == std::string::npos) return "";
    size_t start_quote = obj.find("\"", pos + search_key.length());
    if (start_quote == std::string::npos) return "";
    size_t end_quote = obj.find("\"", start_quote + 1);
    while (end_quote != std::string::npos && obj[end_quote - 1] == '\\') {
        end_quote = obj.find("\"", end_quote + 1);
    }
    if (end_quote == std::string::npos) return "";
    return obj.substr(start_quote + 1, end_quote - start_quote - 1);
}

int extract_key_int(const std::string& obj, const std::string& key) {
    std::string search_key = "\"" + key + "\":";
    size_t pos = obj.find(search_key);
    if (pos == std::string::npos) return -1;
    size_t val_start = pos + search_key.length();
    while (val_start < obj.length() && (obj[val_start] == ' ' || obj[val_start] == ':')) val_start++;
    size_t val_end = val_start;
    while (val_end < obj.length() && std::isdigit(obj[val_end])) val_end++;
    if (val_end == val_start) return -1;
    return std::stoi(obj.substr(val_start, val_end - val_start));
}

int extract_workspace_id(const std::string& obj) {
    size_t ws_pos = obj.find("\"workspace\":");
    if (ws_pos == std::string::npos) return -1;
    size_t id_pos = obj.find("\"id\":", ws_pos);
    if (id_pos == std::string::npos) return -1;
    size_t val_start = id_pos + 5;
    while (val_start < obj.length() && (obj[val_start] == ' ' || obj[val_start] == ':')) val_start++;
    size_t val_end = val_start;
    while (val_end < obj.length() && std::isdigit(obj[val_end])) val_end++;
    return std::stoi(obj.substr(val_start, val_end - val_start));
}

// Logic for mapping Steam and Heroic game launches accurately
std::string get_app_id(const std::string& win_class, const std::string& win_title) {
    std::string cl = win_class;
    std::transform(cl.begin(), cl.end(), cl.begin(), [](unsigned char c){ return std::tolower(c); });
    if (cl.find("steam") != std::string::npos || cl.find("steam_app_") != std::string::npos) {
        return "steam";
    }
    if (cl.find("heroic") != std::string::npos) {
        return "heroic";
    }

    // Normalize to the lowercase, hyphenated form that .desktop filenames
    // and icon files conventionally use (e.g. "Opera GX" -> "opera-gx").
    // This is the SAME id used as the apps map key, passed to find_icon,
    // and passed on the command line to --status/--menu/--maximize, so it
    // has to match desktop-file/icon-file naming conventions consistently.
    std::replace(cl.begin(), cl.end(), ' ', '-');
    std::replace(cl.begin(), cl.end(), '.', '-');
    std::replace(cl.begin(), cl.end(), '/', '-');
    cl.erase(std::remove_if(cl.begin(), cl.end(), [](char c) {
        return !std::isalnum(static_cast<unsigned char>(c)) && c != '-';
    }), cl.end());

    return cl;
}

std::string make_acronym(const std::string& name) {
    std::string acronym;
    bool at_word_start = true;
    for (char c : name) {
        if (std::isspace((unsigned char)c) || c == '-' || c == '_') {
            at_word_start = true;
            continue;
        }
        if (at_word_start && std::isalnum((unsigned char)c)) {
            acronym += std::toupper((unsigned char)c);
            at_word_start = false;
            if (acronym.size() == 2) break;
        }
    }
    if (acronym.size() < 2) {
        // Single-word name (e.g. "kitty") — just take its first two letters.
        acronym.clear();
        for (char c : name) {
            if (std::isalnum((unsigned char)c)) acronym += std::toupper((unsigned char)c);
            if (acronym.size() == 2) break;
        }
    }
    return acronym;
}

// Icon Lookup Strategy
std::string find_icon(const std::string& app_id, const std::string& desktop_icon) {
    // If the .desktop file already gave us a usable absolute path, trust it.
    if (!desktop_icon.empty() && desktop_icon.front() == '/' && fs::exists(desktop_icon)) {
        return desktop_icon;
    }

    std::vector<std::string> names;
    if (!desktop_icon.empty()) names.push_back(desktop_icon);
    names.push_back(app_id);

    std::vector<std::string> extensions = {".svg", ".png"};

    // Your custom theme first, so it always wins if present.
    std::vector<std::string> search_paths = {
        "/usr/share/icons/candy/apps/scalable/",
        "/home/alzrag/.local/share/icons/candy/apps/scalable/",
        "/home/alzrag/.icons/candy/apps/scalable/"
    };

    // Every standard hicolor size, not just scalable + 48x48.
    std::vector<std::string> sizes = {
        "scalable", "512x512", "256x256", "192x192", "128x128",
        "96x96", "64x64", "48x48", "32x32", "24x24", "22x22", "16x16"
    };
    for (const auto& size : sizes) {
        search_paths.push_back("/usr/share/icons/hicolor/" + size + "/apps/");
    }

    // Whatever other icon themes are actually installed (Adwaita, Papirus,
    // breeze, etc.) — apps frequently only ship icons in one of these
    // instead of hicolor.
    if (fs::exists("/usr/share/icons")) {
        for (const auto& entry : fs::directory_iterator("/usr/share/icons")) {
            if (!entry.is_directory()) continue;
            std::string base = entry.path().string();
            search_paths.push_back(base + "/apps/");
            for (const auto& size : sizes) {
                search_paths.push_back(base + "/" + size + "/apps/");
            }
        }
    }

    search_paths.push_back("/usr/share/pixmaps/");

    for (const auto& name : names) {
        for (const auto& path : search_paths) {
            for (const auto& ext : extensions) {
                if (fs::exists(path + name + ext)) return path + name + ext;
            }
        }
    }

    return !desktop_icon.empty() ? desktop_icon : app_id;
}
void scan_desktop_files(std::map<std::string, std::pair<std::string, std::string>>& apps) {
    std::vector<std::string> dirs = {
        "/usr/share/applications/",
        "/usr/local/share/applications/",
        "/home/alzrag/.local/share/applications/"
    };
    apps["steam"] = {"Steam", "steam"};
    apps["heroic"] = {"Heroic Games Launcher", "heroic"};

    for (const auto& dir_path : dirs) {
        if (!fs::exists(dir_path)) continue;
        for (const auto& entry : fs::directory_iterator(dir_path)) {
            if (entry.path().extension() == ".desktop") {
                std::string app_id = entry.path().stem().string();
                std::transform(app_id.begin(), app_id.end(), app_id.begin(), [](unsigned char c){ return std::tolower(c); });

                std::ifstream file(entry.path());
                std::string line, name = "", icon = "";
                while (std::getline(file, line)) {
                    if (line.rfind("Name=", 0) == 0 && name.empty()) name = line.substr(5);
                    if (line.rfind("Icon=", 0) == 0 && icon.empty()) icon = line.substr(5);
                }
                if (!name.empty()) apps[app_id] = {name, icon};
            }
        }
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2) return 1;
    std::string arg = argv[1];

    if (arg == "--minimize") {
        std::string active = exec_cmd("hyprctl activewindow -j");
        std::string addr = extract_key_string(active, "address");
        int pid = extract_key_int(active, "pid");
        if (addr.empty() || pid <= 0) return 0;

        exec_cmd("hyprctl dispatch 'hl.dsp.window.move({ workspace = 100, window = \"address:" + addr + "\", follow = false })'");
        exec_cmd("renice -n 19 -p " + std::to_string(pid));
        exec_cmd("ionice -c 3 -p " + std::to_string(pid));

        exec_cmd(std::string(argv[0]) + " --refresh");
        return 0;
    }

    if (arg == "--maximize" && argc > 2) {
        std::string target_addr = argv[2];
        auto clients = split_json_objects(exec_cmd("hyprctl clients -j"));
        int pid = -1;
        for (const auto& c : clients) {
            if (extract_key_string(c, "address") == target_addr) { pid = extract_key_int(c, "pid"); break; }
        }
        if (pid > 0) {
            exec_cmd("renice -n 0 -p " + std::to_string(pid));
            exec_cmd("ionice -c 2 -p " + std::to_string(pid));
        }

        // Ask Hyprland directly for the currently focused workspace —
        // don't infer it from the first monitor in "hyprctl monitors -j".
        std::string active_ws = exec_cmd("hyprctl activeworkspace -j");
        int ws_id = extract_key_int(active_ws, "id");
        if (ws_id <= 0) ws_id = 1; // safety fallback only

        exec_cmd("hyprctl dispatch 'hl.dsp.window.move({ workspace = " + std::to_string(ws_id) + ", window = \"address:" + target_addr + "\", follow = true })'");
        return 0;
    }

    if (arg == "--status" && argc > 2) {
        std::string target_app = argv[2];
        auto clients = split_json_objects(exec_cmd("hyprctl clients -j"));
        std::vector<std::string> instances;

        for (const auto& c : clients) {
            if (extract_workspace_id(c) == 100) {
                if (get_app_id(extract_key_string(c, "class"), extract_key_string(c, "title")) == target_app) {
                    instances.push_back(extract_key_string(c, "title"));
                }
            }
        }

        if (instances.empty()) {
            std::cout << "{\"text\": \"\", \"tooltip\": \"\", \"class\": \"blank\"}\n";
        } else {
            std::map<std::string, std::pair<std::string, std::string>> apps;
            scan_desktop_files(apps);
            std::string app_name = apps.count(target_app) ? apps[target_app].first : target_app;
            std::string icon_path = find_icon(target_app, apps.count(target_app) ? apps[target_app].second : "");

            std::string tooltip = app_name + " (Minimized):\\n";
            for (const auto& inst : instances) {
                std::string esc = ""; for (char c : inst) { if (c == '"' || c == '\\') esc += '\\'; esc += c; }
                tooltip += "• " + esc + "\\n";
            }
            tooltip = tooltip.substr(0, tooltip.length() - 2);

            bool has_icon_file = (icon_path.find('/') != std::string::npos);
            std::string text = has_icon_file ? "." : make_acronym(app_name);
            std::cout << "{\"text\": \"" << text << "\", \"tooltip\": \"" << tooltip << "\", \"class\": \"minimized\"}\n";
        }
        return 0;
    }

    if (arg == "--menu" && argc > 2) {
        std::string target_app = argv[2];
        auto clients = split_json_objects(exec_cmd("hyprctl clients -j"));
        std::vector<std::pair<std::string, std::string>> instances; // {title, address}

        for (const auto& c : clients) {
            if (extract_workspace_id(c) == 100) {
                if (get_app_id(extract_key_string(c, "class"), extract_key_string(c, "title")) == target_app) {
                    instances.push_back({extract_key_string(c, "title"), extract_key_string(c, "address")});
                }
            }
        }

        if (instances.empty()) return 0;

        // Only one minimized window for this app? Skip the picker, just restore it.
        if (instances.size() == 1) {
            exec_cmd(std::string(argv[0]) + " --maximize " + instances[0].second);
            return 0;
        }

        // Numbered list so duplicate window titles stay disambiguated;
        // the "N) " prefix is stripped back out after the pick.
        std::string entries;
        for (size_t i = 0; i < instances.size(); ++i) {
            entries += std::to_string(i + 1) + ") " + instances[i].first + "\n";
        }

        std::string tmp_path = "/tmp/waymin_menu_" + std::to_string(getpid()) + ".txt";
        std::ofstream(tmp_path) << entries;

        std::string selected = exec_cmd(
            "wofi --show dmenu --prompt \"" + target_app + "\" "
            "--conf /home/alzrag/.config/waybar/scripts/waymin/wofi.conf "
            "--style /home/alzrag/.config/waybar/scripts/waymin/wofi-style.css "
            "< " + tmp_path
        );

        fs::remove(tmp_path);

        while (!selected.empty() && (selected.back() == '\n' || selected.back() == '\r')) selected.pop_back();
        if (selected.empty()) return 0;

        size_t paren = selected.find(')');
        if (paren == std::string::npos) return 0;

        int idx = -1;
        try { idx = std::stoi(selected.substr(0, paren)) - 1; } catch (...) { return 0; }
        if (idx < 0 || idx >= (int)instances.size()) return 0;

        exec_cmd(std::string(argv[0]) + " --maximize " + instances[idx].second);
        return 0;
    }

    if (arg == "--refresh") {
        std::map<std::string, std::pair<std::string, std::string>> all_apps;
        scan_desktop_files(all_apps);

        auto clients = split_json_objects(exec_cmd("hyprctl clients -j"));
        std::map<std::string, std::pair<std::string, std::string>> apps;
        for (const auto& c : clients) {
            if (extract_workspace_id(c) == 100) {
                std::string id = get_app_id(extract_key_string(c, "class"), extract_key_string(c, "title"));
                if (all_apps.count(id)) {
                    apps[id] = all_apps[id];
                } else {
                    apps[id] = {id, ""};
                }
            }
        }

        std::string config_p = "/home/alzrag/.config/waybar/config.jsonc";
        std::string style_p = "/home/alzrag/.config/waybar/style.css";

        std::string list_str  = "    \"custom/waymin-refresh\",\n";
        std::string defs_str  =
            "    \"custom/waymin-refresh\": {\n"
            "        \"format\": \"⟳\",\n"
            "        \"on-click\": \"/home/alzrag/.config/waybar/scripts/waymin/waymin --refresh\",\n"
            "        \"tooltip\": \"Refresh Taskbar Entries\"\n"
            "    },\n";
        std::string style_str = "";

        for (const auto& [id, info] : apps) {
            std::string css_id = id;
            std::replace(css_id.begin(), css_id.end(), ' ', '-');
            std::replace(css_id.begin(), css_id.end(), '.', '-');
            std::replace(css_id.begin(), css_id.end(), '/', '-');
            css_id.erase(std::remove_if(css_id.begin(), css_id.end(), [](char c) {
                return !std::isalnum(c) && c != '-';
            }), css_id.end());

            list_str += "    \"custom/waymin-" + css_id + "\",\n";

            defs_str += "    \"custom/waymin-" + css_id + "\": {\n"
                        "        \"return-type\": \"json\",\n"
                        "        \"exec\": \"/home/alzrag/.config/waybar/scripts/waymin/waymin --status " + id + "\",\n"
                        "        \"on-click\": \"/home/alzrag/.config/waybar/scripts/waymin/waymin --menu " + id + "\",\n"
                        "        \"interval\": 2\n"
                        "    },\n";

            std::string icon_path = find_icon(id, info.second);
            bool has_icon_file = (icon_path.find('/') != std::string::npos);

            style_str += "#custom-waymin-" + css_id + ".blank {\n"
                        "    opacity: 0;\n"
                        "    padding: 0;\n"
                        "    margin: 0;\n"
                        "    min-width: 0;\n"
                        "    min-height: 0;\n"
                        "}\n";

            if (has_icon_file) {
              style_str += "#custom-waymin-" + css_id + ".minimized {\n"
                          "    background-image: url(\"file://" + icon_path + "\");\n"
                          "    background-repeat: no-repeat;\n"
                          "    background-size: contain;\n"
                          "    background-position: center;\n"
                          "    min-width: 24px;\n"
                          "    min-height: 24px;\n"
                          "    padding: 0;\n"
                          "}\n";
          } else {
              // No icon file anywhere on disk — fall back to a colored two-letter
              // acronym badge instead of leaving the module visually blank/broken.
              style_str += "#custom-waymin-" + css_id + ".minimized {\n"
                          "    background-color: #44475a;\n"
                          "    color: #ffffff;\n"
                          "    font-weight: bold;\n"
                          "    font-size: 10px;\n"
                          "    border-radius: 50%;\n"
                          "    min-width: 24px;\n"
                          "    min-height: 24px;\n"
                          "    padding: 0;\n"
                          "}\n";
          }
        }

        auto replace_between = [](std::string src, const std::string& start_marker,
                                  const std::string& end_marker, const std::string& body) -> std::string {
            size_t s = src.find(start_marker);
            size_t e = src.find(end_marker);
            if (s == std::string::npos || e == std::string::npos || e < s) return src;
            size_t content_start = s + start_marker.length();
            return src.substr(0, content_start) + "\n" + body + "    " + src.substr(e);
        };

        if (fs::exists(config_p)) {
            std::ifstream f(config_p);
            std::string src((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());

            src = replace_between(src, "// WAYMIN_LIST_START", "// WAYMIN_LIST_END", list_str);
            src = replace_between(src, "// WAYMIN_DEFS_START", "// WAYMIN_DEFS_END", defs_str);

            std::ofstream(config_p) << src;
        }

        if (fs::exists(style_p)) {
            std::ifstream f(style_p);
            std::string src((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
            src = replace_between(src, "/* WAYMIN_STYLES_START */", "/* WAYMIN_STYLES_END */", style_str);
            std::ofstream(style_p) << src;
        }

        exec_cmd("killall -SIGUSR2 waybar");
        return 0;
    }
  return 0;
}
