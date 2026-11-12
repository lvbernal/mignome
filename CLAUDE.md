# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

mignome — "Gnome como a mí me gusta". Bash and Python scripts that replicate the user's GNOME desktop setup on other machines. The config was captured on Ubuntu 26.04 / GNOME 50 (Wayland) and is meant to be iterated as the OS gets upgraded. User-facing text (README, script messages, comments) is in Spanish.

## Commands

- `./install.sh [step...]`: apply the config. Steps: `packages fonts sounds extensions dconf theme` (default: all). Run as the user inside a GNOME session, not as root.
- `./theme.sh [name]`: list themes, or apply `themes/<name>/`. The active theme is stored in `~/.local/state/mignome/theme`.
- `./export.sh`: regenerate `dconf/*.ini` from the current machine's dconf database.
- `./check.sh`: validate every key in `dconf/*.ini` against the installed GSettings schemas, extension schemas included. Exits 1 on problems.

There are no tests. To verify a dconf load without touching the live config, load into a throwaway database: `DCONF_PROFILE=<file containing "user-db:mignometest">` → `dconf load /` → `dconf dump /`, then delete `~/.config/dconf/mignometest`.

## Architecture

- `install.sh` runs `steps/NN-<name>.sh` in order. Each step is standalone, sources `lib/common.sh`, and is idempotent.
- `config/` holds plain lists that the steps read with `read_list` (`#` comments allowed): apt/snap packages, and `extensions.txt` (`ego|system  uuid  enabled|disabled`). The extensions step writes `enabled-extensions` and `disabled-extensions` **exactly** from that list, so running it on the reference machine disables anything not listed.
- `dconf/*.ini` is **generated** by `tools/mignome.py export` from a whitelist (`RULES`: output file → dconf section paths, with `/*` meaning a subtree, plus per-rule and global key exclusions). Change what gets captured by editing `RULES`, not by hand-editing the `.ini` files, or the next export overwrites the edits. `$HOME` is stored as `@HOME@` and substituted at load time.
- Extension enablement is deliberately kept out of `dconf/shell.ini`; it lives in `config/extensions.txt`.
- Themes (`themes/<name>/`) own the keys in `THEME_KEYS` (accent-color, color-scheme, gtk-theme, icon-theme) and the Ptyxis profile `palette`. Export excludes them, so `dconf/` never depends on which theme is active. `default` must keep matching the original setup. A theme can also ship `gtk-4.0.css`, which `theme.sh` writes to `~/.config/gtk-4.0/gtk.css` with a `/* mignome-theme:` marker on the first line. Without that marker, the existing file is treated as the user's own and backed up, never overwritten.
- VS Code theming (`tools/vscode.py`): `themes/<name>/vscode/` is a normal theme extension. `apply` zips it into a VSIX (no `vsce` or npm needed), installs it with `code --install-extension --force`, and sets `workbench.colorTheme` to its first theme label. `settings.json` is JSONC, so it's edited as text: a scanner masks strings and comments, only the `workbench.colorTheme` entry is replaced, inserted, or removed, and the result is re-parsed before an atomic write. The pre-anniq value (or `__unset__`) is saved in `~/.local/state/mignome/vscode-previous-theme`, and `restore-theme` puts it back. To test without touching the real VS Code, set `MIGNOME_VSCODE_SETTINGS` and `XDG_STATE_HOME`, and put a `code` wrapper first in `PATH` that adds `--extensions-dir`/`--user-data-dir` pointing at temp dirs. Unknown color keys are silently ignored by VS Code, so check new keys against `workbench.desktop.main.js` or the built-in extensions' `package.json` (the `gitDecoration.*` keys come from the git extension).
- `themes/anniq/gtk-4.0.css` overrides libadwaita 1.9 CSS variables, plus Ubuntu's `--yaru-accent-*` and `--yaru-link-*`. Surface variables sit inside `@media (prefers-color-scheme: light)`, so apps that force dark mode stay readable. To check a CSS change without touching the desktop, point `XDG_CONFIG_HOME` at a temp dir containing `gtk-4.0/gtk.css`, build an Adw window in Python without showing it, and read `widget.get_color()` under `Adw.ColorScheme.FORCE_LIGHT` and `FORCE_DARK`.
- `tools/mignome.py check` maps dconf paths to schemas via `gsettings list-schemas --print-paths`, run once for the system and once per extension `schemas/` dir. Several schemas can share a path (e.g. `org.gnome.mutter` and `org.gnome.mutter.devkit`). Relocatable schemas (Ptyxis profiles, custom keybindings) are matched by regex in `RELOCATABLE`.

## Constraints

- Never run `git commit` (or anything that creates commits, such as `git commit --amend` or `git merge`). The user makes all commits. Leave changes in the working tree.
- No applications: don't install apps (the only exception is the Bing Wall snap, for the wallpaper), and don't capture dock favorites (`favorite-apps`) or the app grid layout. Preferences of Ubuntu's default apps (Ptyxis, Nautilus, Text Editor) are fine. VS Code is themed only if it's already installed, and never installed.
- Never capture secrets or personal data: network/VPN (`nm-applet`), bookmarks, histories, file-chooser paths, per-app notification lists, monitor layout.
- Shell pipelines run under `set -o pipefail`. Avoid `cmd | grep -q`: grep exits early and the SIGPIPE turns a match into a failure. Capture the output and test it instead (see `has_font` in `steps/20-fonts.sh`).
- Vicinae and Open Bar were removed from the reference machine (Open Bar has no GNOME 50 version). Don't add either one back.
