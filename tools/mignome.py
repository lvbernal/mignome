#!/usr/bin/env python3
"""Exporta y valida la configuración dconf versionada en dconf/*.ini.

  export  Vuelca de este equipo las secciones dconf de la lista blanca (RULES)
          a dconf/*.ini, quitando claves personales o volátiles.
  check   Comprueba que cada clave de dconf/*.ini y themes/*/*.ini exista en los esquemas
          GSettings instalados (incluidos los de las extensiones) y que los
          valores de tipo enum sean válidos para esta versión de GNOME.
"""

import fnmatch
import glob
import os
import re
import subprocess
import sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DCONF_DIR = os.path.join(ROOT, "dconf")
EXTENSIONS_CONF = os.path.join(ROOT, "config", "extensions.txt")
HOME_TOKEN = "@HOME@"

# Claves que nunca se exportan, estén en la sección que estén.
GLOBAL_EXCLUDE_KEYS = {
    "last-save-directory", "command-history", "color-history",
    "welcome-dialog-last-shown-version", "migrated-gtk-settings",
}

# Claves de org/gnome/desktop/interface que define cada tema en themes/<nombre>/interface.ini.
THEME_KEYS = ["accent-color", "color-scheme", "gtk-theme", "icon-theme"]

# Archivo de salida -> lista de reglas.
# "path" es una sección dconf; con "/*" al final incluye la sección y todo su subárbol.
RULES = OrderedDict([
    ("appearance.ini", [
        # Acento, esquema de color, tema GTK e iconos los maneja el tema activo (themes/).
        {"path": "org/gnome/desktop/interface", "exclude": THEME_KEYS},
        {"path": "org/gnome/desktop/background"},
        {"path": "org/gnome/desktop/screensaver"},
        {"path": "org/gnome/desktop/sound"},
        {"path": "org/gnome/settings-daemon/plugins/color"},
    ]),
    ("input.ini", [
        {"path": "org/gnome/desktop/input-sources", "exclude": ["mru-sources"]},
        {"path": "org/gnome/desktop/peripherals/*"},
    ]),
    ("shortcuts.ini", [
        {"path": "org/gnome/desktop/wm/keybindings"},
        {"path": "org/gnome/mutter/keybindings"},
        {"path": "org/gnome/mutter/wayland/keybindings"},
        {"path": "org/gnome/shell/keybindings"},
        {"path": "org/gnome/settings-daemon/plugins/media-keys/*"},
    ]),
    ("desktop.ini", [
        {"path": "org/gnome/desktop/wm/preferences"},
        {"path": "org/gnome/mutter"},
        {"path": "org/gnome/desktop/session"},
        {"path": "org/gnome/desktop/notifications", "exclude": ["application-children"]},
        {"path": "org/gnome/desktop/privacy"},
        {"path": "org/gnome/desktop/screen-time-limits"},
        {"path": "org/gnome/desktop/break-reminders/*"},
        {"path": "org/gnome/desktop/search-providers"},
        {"path": "org/gnome/settings-daemon/plugins/power"},
    ]),
    ("shell.ini", [
        # Las extensiones habilitadas se gestionan en config/extensions.txt.
        # Las apps no forman parte de la configuración: ni favoritas del dock ni cuadrícula.
        {"path": "org/gnome/shell", "exclude": [
            "enabled-extensions", "disabled-extensions", "app-picker-layout",
            "favorite-apps", "last-selected-power-profile",
        ]},
    ]),
    ("extensions.ini", [
        {"path": "org/gnome/shell/extensions/*",
         "exclude": [
             "last-version-installed",  # tiling-assistant: marca de migración
             "overridden-settings",     # tiling-assistant: valores a restaurar al deshabilitar
             "rounded-blur-found",      # blur-my-shell: bandera interna
         ],
         "exclude_sections": [
             "org/gnome/shell/extensions/vicinae",
             "org/gnome/shell/extensions/user-theme",  # el nombre lo pone el tema activo
         ]},
    ]),
    ("apps.ini", [
        {"path": "org/gnome/Ptyxis/*", "exclude": ["palette"]},  # la paleta es del tema
        {"path": "org/gnome/nautilus/preferences"},
        {"path": "org/gnome/nautilus/icon-view"},
        {"path": "org/gnome/nautilus/list-view"},
        {"path": "org/gnome/TextEditor"},
    ]),
])

# Esquemas relocalizables: regex de la ruta -> id del esquema.
RELOCATABLE = [
    (re.compile(r"^/org/gnome/Ptyxis/Profiles/[^/]+/$"), "org.gnome.Ptyxis.Profile"),
    (re.compile(r"^/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/[^/]+/$"),
     "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"),
]


def parse_ini(text):
    sections = OrderedDict()
    current = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("[") and line.rstrip().endswith("]"):
            current = line.strip()[1:-1]
            sections.setdefault(current, OrderedDict())
        elif current is not None and "=" in line:
            key, value = line.split("=", 1)
            sections[current][key] = value
    return sections


def section_matches(section, pattern):
    if pattern.endswith("/*"):
        base = pattern[:-2]
        return section == base or section.startswith(base + "/")
    return section == pattern


def export():
    dump = subprocess.run(["dconf", "dump", "/"], check=True,
                          capture_output=True, text=True).stdout
    sections = parse_ini(dump)
    home = os.path.expanduser("~")
    os.makedirs(DCONF_DIR, exist_ok=True)

    for filename, rules in RULES.items():
        out = OrderedDict()
        for rule in rules:
            excluded_keys = GLOBAL_EXCLUDE_KEYS | set(rule.get("exclude", []))
            for section, keys in sections.items():
                if not section_matches(section, rule["path"]):
                    continue
                if any(section_matches(section, p) or section_matches(section, p + "/*")
                       for p in rule.get("exclude_sections", [])):
                    continue
                kept = OrderedDict(
                    (k, v.replace(home + "/", HOME_TOKEN + "/"))
                    for k, v in keys.items() if k not in excluded_keys)
                if kept:
                    out[section] = kept

        path = os.path.join(DCONF_DIR, filename)
        with open(path, "w") as fh:
            fh.write("# Generado por ./export.sh — revisa el diff antes de hacer commit.\n")
            fh.write("# %s se reemplaza por $HOME al cargar.\n" % HOME_TOKEN)
            for section, keys in out.items():
                fh.write("\n[%s]\n" % section)
                for k, v in keys.items():
                    fh.write("%s=%s\n" % (k, v))
        print("escrito dconf/%s (%d secciones)" % (filename, len(out)))

    compare_extensions()


def compare_extensions():
    wanted = set()
    with open(EXTENSIONS_CONF) as fh:
        for line in fh:
            parts = line.split("#", 1)[0].split()
            if len(parts) == 3 and parts[2] == "enabled":
                wanted.add(parts[1])
    current = set(subprocess.run(["gnome-extensions", "list", "--enabled"],
                                 check=True, capture_output=True, text=True).stdout.split())
    for uuid in sorted(current - wanted):
        print("aviso: %s está habilitada aquí pero no en config/extensions.txt" % uuid)
    for uuid in sorted(wanted - current):
        print("aviso: %s está en config/extensions.txt pero no habilitada aquí" % uuid)


def gsettings(args, schemadir=None):
    cmd = ["gsettings"] + (["--schemadir", schemadir] if schemadir else []) + args
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout if res.returncode == 0 else None


def schema_index():
    """Mapa ruta -> [(esquema, schemadir)]; varias rutas comparten esquemas (p. ej. mutter)."""
    index = {}
    sources = [None]
    sources += glob.glob(os.path.expanduser("~/.local/share/gnome-shell/extensions/*/schemas"))
    sources += glob.glob("/usr/share/gnome-shell/extensions/*/schemas")
    for d in sources:
        if d and not os.path.exists(os.path.join(d, "gschemas.compiled")):
            continue
        for line in (gsettings(["list-schemas", "--print-paths"], d) or "").splitlines():
            schema, path = line.split()
            candidates = index.setdefault(path, [])
            if schema not in [s for s, _ in candidates]:
                candidates.append((schema, d))
    return index


def check():
    index = schema_index()
    problems = unverified = checked = 0
    inis = sorted(glob.glob(os.path.join(DCONF_DIR, "*.ini")))
    inis += sorted(glob.glob(os.path.join(ROOT, "themes", "*", "*.ini")))
    for ini in inis:
        with open(ini) as fh:
            sections = parse_ini(fh.read())
        name = os.path.relpath(ini, ROOT)
        for section, keys in sections.items():
            path = "/" + section + "/"
            candidates = list(index.get(path, []))
            for regex, reloc in RELOCATABLE:
                if regex.match(path):
                    candidates.append(("%s:%s" % (reloc, path), None))
            if not candidates:
                print("?  %s [%s] sin esquema instalado; no se puede verificar" % (name, section))
                unverified += 1
                continue
            known = [(target, d, set((gsettings(["list-keys", target], d) or "").split()))
                     for target, d in candidates]
            for key, value in keys.items():
                checked += 1
                match = next(((t, d) for t, d, ks in known if key in ks), None)
                if match is None:
                    print("✗  %s [%s] %s: la clave no existe en %s"
                          % (name, section, key, ", ".join(t for t, _, _ in known)))
                    problems += 1
                    continue
                lines = (gsettings(["range", match[0], key], match[1]) or "").splitlines()
                if lines and lines[0] == "enum" and value not in lines[1:]:
                    print("✗  %s [%s] %s=%s: valor fuera del enum (%s)"
                          % (name, section, key, value, " ".join(lines[1:])))
                    problems += 1
    print("\n%d claves verificadas, %d problemas, %d secciones sin verificar"
          % (checked, problems, unverified))
    return 1 if problems else 0


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("export", "check"):
        print("uso: %s export|check" % sys.argv[0], file=sys.stderr)
        return 2
    if sys.argv[1] == "export":
        export()
        return 0
    return check()


if __name__ == "__main__":
    sys.exit(main())
