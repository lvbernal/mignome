# mignome

Gnome como a mí me gusta.

Scripts para replicar mi configuración de GNOME en otro equipo. Capturada en **Ubuntu 26.04 / GNOME 50** (Wayland).

Código generado 100% con IA (salvo esta nota).

## Uso

En el equipo nuevo, dentro de una sesión de GNOME y como tu usuario (no con `sudo`):

```bash
git clone <este-repo> ~/Source/mignome
cd ~/Source/mignome
./install.sh                 # todos los pasos
./install.sh extensions dconf   # solo algunos pasos
```

Al terminar, **cierra sesión y vuelve a entrar**: en Wayland, las extensiones recién instaladas solo se cargan al iniciar sesión. Abre **Bing Wall** una vez para que descargue el fondo de pantalla.

| Paso | Qué hace |
|---|---|
| `packages` | `apt` de `config/packages.apt` (Yaru, fuentes, extensiones de Ubuntu, libgtop, Ptyxis) y `snap` de `config/packages.snap` (Bing Wall) |
| `fonts` | Descarga Atkinson Hyperlegible Mono (no está empaquetada) a `~/.local/share/fonts` |
| `sounds` | Tema de sonido `__custom` (hereda de Yaru, campana = `click.ogg`) |
| `extensions` | Instala desde extensions.gnome.org la versión compatible con el GNOME instalado y fija las extensiones habilitadas y deshabilitadas según `config/extensions.txt` |
| `dconf` | Valida `dconf/*.ini` contra los esquemas instalados y los carga con `dconf load` |

`MIGNOME_UPGRADE=1 ./install.sh extensions` reinstala las extensiones de EGO aunque ya estén instaladas.

## Qué incluye

- **Apariencia**: modo oscuro, acento teal, tema/iconos Yaru-prussiangreen-dark, fuentes Atkinson Hyperlegible Next/Mono 11, fondo (Bing Wall) y bloqueo de pantalla, sonidos.
- **Entrada**: distribuciones latam/es/us, Bloq Num activado, desplazamiento con dos dedos.
- **Atajos**: `Super+1..4` cambia de espacio de trabajo, `Shift+Super+1..4` mueve la ventana, `Super+A` abre la cuadrícula de apps, `Super+E` abre la carpeta personal, mosaico con Tiling Assistant (`Super+flechas`, `Super+teclado numérico`). Quitados los atajos `Super+N` de apps del dock.
- **Escritorio**: 4 espacios de trabajo fijos, sin edge-tiling de mutter (lo maneja Tiling Assistant), No molestar, suspensión desactivada, bloqueo a los 5 min, sin envío de informes de errores, recordatorios de descanso.
- **Extensiones**: Blur my Shell, Color Picker, Just Perfection, TopHat, Advanced Media Controller y las de Ubuntu (dock, Tiling Assistant, AppIndicators, iconos del escritorio), con su configuración.
- **Apps**: paleta Horizon y tamaño de ventana en Ptyxis, vista de iconos en Nautilus, Text Editor sin restaurar sesión.

## Qué no incluye (a propósito)

Aplicaciones: no se instalan (salvo Bing Wall, para el fondo) ni se fijan en el dock. Tampoco contraseñas, llaves, redes Wi-Fi/VPN (`nm-applet`), marcadores de Nautilus, historiales, tamaños de ventana, disposición de la cuadrícula de apps, monitores (`monitors.xml`), permisos de notificaciones por app, atajos globales que registran las propias apps (p. ej. Claude) y las extensiones Vicinae y Open Bar.

## Iterar (al actualizar el sistema o cambiar algo)

1. En el equipo de referencia: `./export.sh`. Vuelca las secciones de dconf de la lista blanca a `dconf/*.ini` y avisa si las extensiones habilitadas no coinciden con `config/extensions.txt`.
2. Revisa `git diff`: descarta lo que no quieras versionar o ajusta las reglas en `tools/mignome.py` (`RULES`, `GLOBAL_EXCLUDE_KEYS`).
3. `./check.sh`: marca las claves que ya no existen en la versión de GNOME instalada, o los valores enum inválidos. Quítalas o cámbialas.
4. Si cambiaste de versión mayor de GNOME, actualiza `MIGNOME_TESTED_GNOME` en `lib/common.sh`.
