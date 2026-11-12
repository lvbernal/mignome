#!/usr/bin/env python3
"""Temas para VS Code y sus forks (Kiro) desde theme.sh.

  editors                          Lista los editores soportados que están instalados.
  apply <editor> <carpeta>         Empaqueta la extensión de tema de <carpeta>, la instala con
                                   `<cli> --install-extension` y activa su primer tema.
  restore-theme <editor>           Restaura el workbench.colorTheme que el editor tenía antes del
                                   primer `apply` (o quita la clave si no había). Si no hay nada
                                   guardado, no hace nada.
  vsix <carpeta> <salida.vsix>     Empaqueta una extensión local (package.json + archivos) como VSIX.

settings.json es JSONC (comentarios y comas finales), así que se edita como texto para
conservar los comentarios, y el resultado se valida antes de escribirlo.
Respeta XDG_CONFIG_HOME (settings.json) y XDG_STATE_HOME (valor anterior guardado).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from xml.sax.saxutils import escape

KEY = "workbench.colorTheme"
UNSET = "__unset__"
CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
STATE_HOME = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")

# cli -> (nombre visible, carpeta en ~/.config)
EDITORS = {
    "code": ("VS Code", "Code"),
    "kiro": ("Kiro", "Kiro"),
}


class Editor:
    def __init__(self, cli):
        if cli not in EDITORS:
            raise SystemExit("editor desconocido: %s (soportados: %s)" % (cli, " ".join(EDITORS)))
        self.cli = cli
        self.name, config_dir = EDITORS[cli]
        self.settings = os.path.join(CONFIG_HOME, config_dir, "User", "settings.json")
        self.state = os.path.join(STATE_HOME, "mignome", "%s-previous-theme" % cli)


# ── VSIX ──────────────────────────────────────────────────────────────────

def build_vsix(src, out):
    with open(os.path.join(src, "package.json")) as fh:
        pkg = json.load(fh)
    manifest = f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="{escape(pkg['name'])}" Version="{escape(pkg['version'])}" Publisher="{escape(pkg['publisher'])}"/>
    <DisplayName>{escape(pkg.get('displayName', pkg['name']))}</DisplayName>
    <Description xml:space="preserve">{escape(pkg.get('description', ''))}</Description>
    <Categories>{escape(','.join(pkg.get('categories', [])))}</Categories>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{escape(pkg['engines']['vscode'])}"/>
    </Properties>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>
  </Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>
  </Assets>
</PackageManifest>
"""
    content_types = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension=".json" ContentType="application/json"/><Default Extension=".vsixmanifest" ContentType="text/xml"/></Types>
"""
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("extension.vsixmanifest", manifest)
        for base, _, files in os.walk(src):
            for name in sorted(files):
                path = os.path.join(base, name)
                z.write(path, "extension/" + os.path.relpath(path, src))
    print("extensión %s.%s@%s empaquetada" % (pkg["publisher"], pkg["name"], pkg["version"]))


# ── JSONC ─────────────────────────────────────────────────────────────────

def scan(text):
    """Clasifica cada carácter: 's' cadena, 'c' comentario, 'o' resto."""
    mask = ["o"] * len(text)
    i, n = 0, len(text)
    while i < n:
        if text[i] == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            for k in range(i, min(j + 1, n)):
                mask[k] = "s"
            i = j + 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                mask[k] = "c"
            i = j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                mask[k] = "c"
            i = j
        else:
            i += 1
    return mask


def parse_jsonc(text):
    mask = scan(text)
    plain = "".join(ch for ch, m in zip(text, mask) if m != "c")
    plain = re.sub(r",(\s*[}\]])", r"\1", plain)  # comas finales (no aparecen dentro de cadenas JSON válidas)
    return json.loads(plain or "{}")


def find_key(text):
    """Devuelve el match de "workbench.colorTheme": "..." que no esté comentado, o None."""
    mask = scan(text)
    pattern = re.compile(r'"%s"\s*:\s*"((?:[^"\\]|\\.)*)"' % re.escape(KEY))
    for m in pattern.finditer(text):
        if mask[m.start()] == "s" and (m.start() == 0 or mask[m.start() - 1] != "s"):
            return m
    return None


def read_settings(path):
    if not os.path.exists(path):
        return "{\n}\n"
    with open(path) as fh:
        return fh.read()


def write_settings(path, text, expected):
    data = parse_jsonc(text)  # lanza excepción si quedó inválido
    if data.get(KEY) != expected:
        raise RuntimeError("la edición de settings.json no produjo el valor esperado")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        with open(path) as src, open(path + ".mignome-bak", "w") as bak:
            bak.write(src.read())
    tmp = path + ".mignome-tmp"
    with open(tmp, "w") as fh:
        fh.write(text)
    os.replace(tmp, path)


def current_value(text):
    return parse_jsonc(text).get(KEY)


def set_value(text, value):
    m = find_key(text)
    literal = json.dumps(value, ensure_ascii=False)
    if m:
        return text[:m.start(1) - 1] + literal + text[m.end(1) + 1:]
    mask = scan(text)
    brace = next(i for i, ch in enumerate(text) if ch == "{" and mask[i] == "o")
    rest = text[brace + 1:]
    has_entries = parse_jsonc(text) != {}
    entry = '\n    "%s": %s%s' % (KEY, literal, "," if has_entries else "")
    return text[:brace + 1] + entry + rest


def remove_value(text):
    m = find_key(text)
    if not m:
        return text
    start, end = m.start(), m.end()
    tail = re.match(r"\s*,?[ \t]*", text[end:])
    end += tail.end()
    line_start = text.rfind("\n", 0, start) + 1
    if text[line_start:start].strip() == "" and text[end:end + 1] in ("\n", ""):
        start, end = line_start, end + 1
    return text[:start] + text[end:]


def set_theme(editor, label):
    text = read_settings(editor.settings)
    if not os.path.exists(editor.state):
        previous = current_value(text)
        os.makedirs(os.path.dirname(editor.state), exist_ok=True)
        with open(editor.state, "w") as fh:
            fh.write(previous if previous is not None else UNSET)
    write_settings(editor.settings, set_value(text, label), label)
    print("%s usa el tema %s" % (editor.name, label))


def restore_theme(editor):
    if not os.path.exists(editor.state):
        return
    with open(editor.state) as fh:
        previous = fh.read()
    text = read_settings(editor.settings)
    if previous == UNSET:
        write_settings(editor.settings, remove_value(text), None)
        print("%s vuelve a su tema predeterminado" % editor.name)
    else:
        write_settings(editor.settings, set_value(text, previous), previous)
        print("%s vuelve al tema %s" % (editor.name, previous))
    os.remove(editor.state)


def apply(editor, src):
    with open(os.path.join(src, "package.json")) as fh:
        label = json.load(fh)["contributes"]["themes"][0]["label"]
    with tempfile.TemporaryDirectory() as tmp:
        vsix = os.path.join(tmp, "theme.vsix")
        build_vsix(src, vsix)
        subprocess.run([editor.cli, "--install-extension", vsix, "--force"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("extensión instalada en %s" % editor.name)
    set_theme(editor, label)


def main():
    args = sys.argv[1:]
    if args == ["editors"]:
        print(" ".join(cli for cli in EDITORS if shutil.which(cli)))
    elif len(args) == 3 and args[0] == "apply":
        apply(Editor(args[1]), args[2])
    elif len(args) == 2 and args[0] == "restore-theme":
        restore_theme(Editor(args[1]))
    elif len(args) == 3 and args[0] == "vsix":
        build_vsix(args[1], args[2])
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
