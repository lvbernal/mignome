# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

mignome — "Gnome como a mí me gusta". Bash and Python scripts that replicate the user's GNOME desktop setup on other machines. The config was captured on Ubuntu 26.04 / GNOME 50 (Wayland) and is meant to be iterated as the OS gets upgraded. User-facing text (README, script messages, comments) is in Spanish.

## Commands

- `./install.sh [step...]`: apply the config. Steps: `packages fonts sounds extensions dconf` (default: all). Run as the user inside a GNOME session, not as root.
- `./export.sh`: regenerate `dconf/*.ini` from the current machine's dconf database.
- `./check.sh`: validate every key in `dconf/*.ini` against the installed GSettings schemas, extension schemas included. Exits 1 on problems.

There are no tests. To verify a dconf load without touching the live config, load into a throwaway database: `DCONF_PROFILE=<file containing "user-db:mignometest">` → `dconf load /` → `dconf dump /`, then delete `~/.config/dconf/mignometest`.

## Architecture

- `install.sh` runs `steps/NN-<name>.sh` in order. Each step is standalone, sources `lib/common.sh`, and is idempotent.
- `config/` holds plain lists that the steps read with `read_list` (`#` comments allowed): apt/snap packages, and `extensions.txt` (`ego|system  uuid  enabled|disabled`). The extensions step writes `enabled-extensions` and `disabled-extensions` **exactly** from that list, so running it on the reference machine disables anything not listed.
- `dconf/*.ini` is **generated** by `tools/mignome.py export` from a whitelist (`RULES`: output file → dconf section paths, with `/*` meaning a subtree, plus per-rule and global key exclusions). Change what gets captured by editing `RULES`, not by hand-editing the `.ini` files, or the next export overwrites the edits. `$HOME` is stored as `@HOME@` and substituted at load time.
- Extension enablement is deliberately kept out of `dconf/shell.ini`; it lives in `config/extensions.txt`.
- `tools/mignome.py check` maps dconf paths to schemas via `gsettings list-schemas --print-paths`, run once for the system and once per extension `schemas/` dir. Several schemas can share a path (e.g. `org.gnome.mutter` and `org.gnome.mutter.devkit`). Relocatable schemas (Ptyxis profiles, custom keybindings) are matched by regex in `RELOCATABLE`.

## Constraints

- Never run `git commit` (or anything that creates commits, such as `git commit --amend` or `git merge`). The user makes all commits. Leave changes in the working tree.
- No applications: don't install apps (the only exception is the Bing Wall snap, for the wallpaper), and don't capture dock favorites (`favorite-apps`) or the app grid layout. Preferences of Ubuntu's default apps (Ptyxis, Nautilus, Text Editor) are fine.
- Never capture secrets or personal data: network/VPN (`nm-applet`), bookmarks, histories, file-chooser paths, per-app notification lists, monitor layout.
- Shell pipelines run under `set -o pipefail`. Avoid `cmd | grep -q`: grep exits early and the SIGPIPE turns a match into a failure. Capture the output and test it instead (see `has_font` in `steps/20-fonts.sh`).
- Vicinae and Open Bar were removed from the reference machine (Open Bar has no GNOME 50 version). Don't add either one back.
