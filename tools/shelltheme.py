#!/usr/bin/env python3
"""Genera un tema de GNOME Shell (para la extensión User Themes) a partir del tema base instalado.

  generate <mapa.json> <salida.css>   Lee la hoja de estilo base del shell (la del modo de sesión
                                      actual, p. ej. Yaru en Ubuntu, en la variante clara u oscura
                                      que pide el mapa), reemplaza sus colores según el mapa y
                                      escribe solo las reglas que cambian.
  colors <mapa.json>                  Lista los colores de la hoja base que el mapa no cubre
                                      (para ajustar el mapa en futuras versiones de GNOME).

El shell carga el tema de User Themes como application_stylesheet, *encima* de la hoja base
(default_stylesheet), así que basta con sobrescribir las declaraciones que llevan color.
Se genera al aplicar el tema, de modo que sigue a la versión de GNOME/Yaru instalada.

Formato del mapa (JSON):
  "variant":  "light" | "dark"          variante de la hoja base
  "accent":   {"color": "#..", "fg": "#.."}   reemplazan -st-accent-color / -st-accent-fg-color
  "colors":   {"#rrggbb": "#rrggbb", ...}     por RGB: también aplica a rgba(r, g, b, a) con ese RGB
  "tint":     {"hue": 140, "saturation": 0.3, "tolerance": 8}
                                              tiñe los grises que no estén en "colors", conservando su
                                              luminosidad; "tolerance" es la diferencia máxima entre
                                              canales para considerar gris un color (0 = solo r = g = b).
                                              El blanco y el negro puros no se tiñen.
"""

import colorsys
import glob
import json
import os
import re
import subprocess
import sys

GS_DATA = "/usr/share/gnome-shell"
KEYWORDS = {"white": (255, 255, 255), "black": (0, 0, 0)}
COLOR_RE = re.compile(
    r"-st-accent-fg-color|-st-accent-color|#[0-9a-fA-F]{3,8}\b|rgba?\([^()]*\)|\b(?:white|black)\b")


# ── Hoja base ─────────────────────────────────────────────────────────────

def session_mode():
    if os.environ.get("GNOME_SHELL_SESSION_MODE"):
        return os.environ["GNOME_SHELL_SESSION_MODE"]
    for cmdline in glob.glob("/proc/[0-9]*/cmdline"):
        try:
            with open(cmdline, "rb") as fh:
                args = fh.read().split(b"\0")
        except OSError:
            continue
        if args and args[0].endswith(b"/gnome-shell"):
            for arg in args:
                if arg.startswith(b"--mode="):
                    return arg[7:].decode()
            return "user"
    desktop = os.environ.get("XDG_SESSION_DESKTOP", "")
    return desktop if os.path.exists(f"{GS_DATA}/modes/{desktop}.json") else "user"


def base_stylesheet(variant):
    mode = session_mode()
    stylesheet, resource = "gnome-shell.css", "gnome-shell-theme.gresource"
    mode_file = f"{GS_DATA}/modes/{mode}.json"
    if os.path.exists(mode_file):
        with open(mode_file) as fh:
            data = json.load(fh)
        stylesheet = data.get("stylesheetName", stylesheet)
        resource = data.get("themeResourceName", resource)
    candidates = [stylesheet.replace(".css", f"-{variant}.css"), stylesheet]
    for name in candidates:
        res = subprocess.run(["gresource", "extract", f"{GS_DATA}/{resource}",
                              f"/org/gnome/shell/theme/{name}"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout:
            return res.stdout, f"{resource}:{name} (modo {mode})"
        path = f"{GS_DATA}/theme/{name}"
        if os.path.exists(path):
            with open(path) as fh:
                return fh.read(), f"{path} (modo {mode})"
    raise SystemExit("no se encontró la hoja base del shell (%s)" % ", ".join(candidates))


# ── Colores ───────────────────────────────────────────────────────────────

def parse_hex(value):
    h = value.lstrip("#")
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)), (int(h[6:8], 16) / 255 if len(h) == 8 else None)


def to_hex(rgb):
    return "#%02X%02X%02X" % rgb


class ColorMap:
    def __init__(self, spec):
        self.variant = spec["variant"]
        self.accent = spec["accent"]
        self.colors = {parse_hex(k)[0]: parse_hex(v)[0] for k, v in spec.get("colors", {}).items()}
        self.tint = spec.get("tint")

    def map_rgb(self, rgb):
        if rgb in self.colors:
            return self.colors[rgb]
        if self.tint and rgb not in KEYWORDS.values() \
                and max(rgb) - min(rgb) <= self.tint.get("tolerance", 0):
            lightness = colorsys.rgb_to_hls(*(c / 255 for c in rgb))[1]
            new = colorsys.hls_to_rgb(self.tint["hue"] / 360, lightness, self.tint["saturation"])
            return tuple(round(x * 255) for x in new)
        return rgb

    def replace(self, token):
        """Devuelve el token con el color reemplazado (o el mismo si no cambia)."""
        if token == "-st-accent-color":
            return self.accent["color"]
        if token == "-st-accent-fg-color":
            return self.accent["fg"]
        if token.lower() in KEYWORDS:
            rgb = KEYWORDS[token.lower()]
            new = self.map_rgb(rgb)
            return token if new == rgb else to_hex(new)
        if token.startswith("#"):
            rgb, alpha = parse_hex(token)
            new = self.map_rgb(rgb)
            if new == rgb:
                return token
            return to_hex(new) if alpha is None else "rgba(%d, %d, %d, %.3g)" % (*new, alpha)
        nums = [p.strip() for p in token[token.index("(") + 1:-1].split(",")]
        if len(nums) < 3 or any(not re.fullmatch(r"\d+", n) for n in nums[:3]):
            return token
        rgb = tuple(int(n) for n in nums[:3])
        new = self.map_rgb(rgb)
        if new == rgb:
            return token
        if len(nums) == 4:
            return "rgba(%d, %d, %d, %s)" % (*new, nums[3])
        return to_hex(new)


# ── Generación ────────────────────────────────────────────────────────────

def rules(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        yield " ".join(selector.split()), [d.strip() for d in body.split(";") if d.strip()]


def generate(spec_path, out_path):
    with open(spec_path) as fh:
        spec = json.load(fh)
    cmap = ColorMap(spec)
    css, source = base_stylesheet(cmap.variant)
    out, count = [], 0
    for selector, decls in rules(css):
        changed = []
        for decl in decls:
            new = COLOR_RE.sub(lambda m: cmap.replace(m.group(0)), decl)
            if new != decl:
                changed.append(new)
        if changed:
            count += 1
            out.append("%s {\n  %s; }\n" % (selector.replace(", ", ",\n"), ";\n  ".join(changed)))
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as fh:
        fh.write("/* Generado por mignome/tools/shelltheme.py desde %s\n" % source)
        fh.write(" * con %s. No editar: se regenera al aplicar el tema. */\n\n" % os.path.basename(spec_path))
        fh.write("\n".join(out))
    print("%d reglas sobrescritas sobre %s" % (count, source))


def unmapped(spec_path):
    with open(spec_path) as fh:
        cmap = ColorMap(json.load(fh))
    css, source = base_stylesheet(cmap.variant)
    seen = {}
    for _, decls in rules(css):
        for decl in decls:
            for m in COLOR_RE.finditer(decl):
                tok = m.group(0)
                if tok.startswith("-st-") or cmap.replace(tok) != tok:
                    continue
                seen[tok.lower()] = seen.get(tok.lower(), 0) + 1
    print("colores sin cambio en %s:" % source)
    for tok, n in sorted(seen.items(), key=lambda kv: -kv[1]):
        print("  %4d  %s" % (n, tok))


def main():
    args = sys.argv[1:]
    if len(args) == 3 and args[0] == "generate":
        generate(args[1], args[2])
    elif len(args) == 2 and args[0] == "colors":
        unmapped(args[1])
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
