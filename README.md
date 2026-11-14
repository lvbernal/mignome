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
| `cursor` | Descarga el tema de cursor Bibata Modern Classic (v2.0.7, no está empaquetado) a `~/.local/share/icons`, verifica su SHA-256 y lo enlaza en `~/.icons` para apps X11 como el snap de VS Code |
| `sounds` | Tema de sonido `__custom` (hereda de Yaru, campana = `click.ogg`) |
| `extensions` | Instala desde extensions.gnome.org la versión compatible con el GNOME instalado y fija las extensiones habilitadas y deshabilitadas según `config/extensions.txt` |
| `dconf` | Valida `dconf/*.ini` contra los esquemas instalados y los carga con `dconf load` |
| `theme` | Aplica el tema activo (`default` si nunca elegiste otro). Ver [Temas](#temas) |

`MIGNOME_UPGRADE=1 ./install.sh extensions` reinstala las extensiones de EGO aunque ya estén instaladas.

## Qué incluye

- **Apariencia**: tema `default` (modo oscuro, acento teal, tema/iconos Yaru-prussiangreen-dark) o uno de los de `themes/`, fuentes Atkinson Hyperlegible Next/Mono 11, cursor Bibata Modern Classic, fondo (Bing Wall) y bloqueo de pantalla, sonidos.
- **Entrada**: distribuciones latam/es/us, Bloq Num activado, desplazamiento con dos dedos.
- **Atajos**: `Super+1..4` cambia de espacio de trabajo, `Shift+Super+1..4` mueve la ventana, `Super+A` abre la cuadrícula de apps, `Super+E` abre la carpeta personal, mosaico con Tiling Assistant (`Super+flechas`, `Super+teclado numérico`). Quitados los atajos `Super+N` de apps del dock.
- **Escritorio**: 4 espacios de trabajo fijos, sin edge-tiling de mutter (lo maneja Tiling Assistant), No molestar, suspensión desactivada, bloqueo a los 5 min, sin envío de informes de errores, recordatorios de descanso.
- **Extensiones**: Blur my Shell, Color Picker, Just Perfection, TopHat, Advanced Media Controller, Dash2Dock Animated (dock con magnificación al estilo macOS; reemplaza a Ubuntu Dock, que queda deshabilitado) y las de Ubuntu (Tiling Assistant, AppIndicators, iconos del escritorio), con su configuración.
- **Apps**: paleta del tema y tamaño de ventana en Ptyxis, vista de iconos en Nautilus, Text Editor sin restaurar sesión.

## Temas

```bash
./theme.sh               # lista los temas; * marca el activo
./theme.sh anniq-light   # cambia a anniq-light
./theme.sh default       # vuelve al tema por defecto
```

| Tema | Qué es |
|---|---|
| `default` | El tema actual: oscuro, acento teal, Yaru-prussiangreen-dark, paleta Horizon en Ptyxis |
| `anniq-light` | Claro, con los colores de la app web anniq (tema Vuetify): fondo `#F1F8F6`, texto `#1B2528`, acento `#0D5F18`, barra lateral oscura `#0B2211`, paleta Anniq en Ptyxis y tema Anniq en VS Code y Kiro. Base del sistema: acento verde (Yaru-olive) |
| `anniq-dark` | Variante oscura derivada de la misma paleta (Vuetify solo define el modo claro): ventana `#0B2211` (`menu-bg`), contenido `#081A0D`, barra lateral `#06140A`, texto `#F1F8F6`, acento `#C7FC8B` (`secondary`), sección oscura de la paleta Anniq en Ptyxis y tema Anniq Dark en VS Code y Kiro. Base del sistema: Yaru-olive-dark |
| `everforest-dark` | [Everforest](https://github.com/sainnhe/everforest) oscuro, contraste medio: ventana `#2D353B` (`bg0`), contenido `#232A2E` (`bg_dim`), barras `#343F44` (`bg1`), texto `#D3C6AA`, acento `#A7C080` (`green`), paleta Everforest de Ptyxis (ya viene con Ptyxis) y tema Everforest Dark en VS Code y Kiro. Base del sistema: Yaru-olive-dark |
| `everforest-light` | Everforest claro, contraste medio: ventana `#FDF6E3` (`bg0`), contenido `#FFFBEF`, barra lateral `#EFEBD4`, texto `#5C6A72`, acento `#8DA101` con texto oscuro. Los colores de Everforest claro no llegan a 4.5:1 como texto, así que enlaces y estados usan una versión oscurecida del mismo tono (p. ej. `#677618` para el verde). Panel superior oscuro (`#2D353B`), como en Yaru. Paleta Everforest de Ptyxis y tema Everforest Light en VS Code y Kiro. Base del sistema: Yaru-olive |
| `eyes-dark` | Oscuro pensado para reducir la fatiga visual, con paleta propia: fondo marrón cálido en vez de negro (ventana `#211D1A`, contenido `#1A1713`, barras `#282521`), texto crema `#D9D0C1` a 10.9:1 en vez de blanco puro, y acentos cálidos y apagados (ámbar `#D3A974` como acento, todos entre 7:1 y 8:1). Los enlaces van en azul apagado para distinguirlos del acento. Paleta EyesDark en Ptyxis y tema Eyes Dark en VS Code y Kiro. Base del sistema: acento marrón (Yaru-wartybrown-dark) |

Cada tema es una carpeta en `themes/`:

- `interface.ini`: acento, esquema claro/oscuro, tema GTK e iconos (claves dconf).
- `gtk-4.0.css` (opcional): colores exactos para las apps GTK4/libadwaita (Archivos, Configuración, Text Editor…). Se copia a `~/.config/gtk-4.0/gtk.css`. Si ya había un `gtk.css` que no creó `theme.sh`, se respalda como `gtk.css.bak-<fecha>`.
- `*.palette` y `ptyxis-palette` (opcional): paletas de Ptyxis que se instalan y la paleta del perfil por defecto.
- `vscode/` (opcional): extensión de tema para VS Code y Kiro. Se empaqueta como VSIX, se instala con `code`/`kiro --install-extension` en los editores que estén presentes y se activa en el `settings.json` de cada uno, editando solo `workbench.colorTheme` y conservando tus comentarios. Se guarda el tema que tenía cada editor, y un tema sin `vscode/` (como `default`) lo restaura. Los editores que no estén instalados se omiten; los scripts nunca los instalan. La extensión trae los dos temas (Anniq y Anniq Dark), y `vscode-theme` indica cuál activar.

`anniq-dark` no duplica archivos: `Anniq.palette` y `vscode/` son enlaces simbólicos a los de `anniq-light`. Igual, `everforest-light/vscode` es un enlace a la extensión de `everforest-dark`, que trae los dos temas.

- `gnome-shell.json` (opcional): mapa de colores para el shell (panel superior, menús, quick settings, notificaciones, calendario, dash, OSD). `tools/shelltheme.py` toma la hoja de Yaru instalada (clara u oscura), reemplaza sus colores según el mapa y escribe solo las reglas que cambian en `~/.local/share/themes/<Nombre>/gnome-shell/gnome-shell.css`. La extensión User Themes carga ese CSS encima de Yaru. Como se genera al aplicar el tema, sigue a la versión de GNOME/Yaru instalada.

Las apps GTK4 abiertas toman el CSS nuevo al reiniciarlas; el shell cambia al instante. Las apps GTK3 todavía muestran el verde de Yaru-olive.

**Shell:**
- **Modo claro/oscuro:** cambia de tema con `theme.sh`, no con el botón "Estilo oscuro" de los quick settings. El tema del shell se genera para la variante (clara u oscura) de su tema, y ese botón cambia la base de Yaru por debajo.
- **Fuera de alcance:** la pantalla de inicio de sesión (GDM) no cambia, porque es del sistema y no de tu usuario.
- **Indicadores del sistema:** los de grabación y compartir pantalla, y los avisos de batería, conservan sus colores.
- **Dock:** los íconos del dock y el fondo del dash quedan a cargo de la extensión del dock (Dash2Dock Animated, con fondo transparente según su configuración). El mapa los excluye con `skip`, porque el tema del shell tiene más prioridad que los estilos de las extensiones y, si no, les pondría fondo.
- **Tras actualizar el sistema:** vuelve a aplicar el tema (`./theme.sh anniq-light`) para regenerarlo desde el Yaru nuevo. `python3 tools/shelltheme.py colors themes/anniq-light/gnome-shell.json` lista los colores de la hoja base que el mapa no cubre.

`./export.sh` no captura las claves que define el tema (acento, esquema de color, tema GTK, iconos, paleta de Ptyxis, tema del shell), así que exportar con anniq-light activo no altera el tema `default`.

## Qué no incluye (a propósito)

Aplicaciones: no se instalan (salvo Bing Wall, para el fondo) ni se fijan en el dock. Tampoco contraseñas, llaves, redes Wi-Fi/VPN (`nm-applet`), marcadores de Nautilus, historiales, tamaños de ventana, disposición de la cuadrícula de apps, monitores (`monitors.xml`), permisos de notificaciones por app, atajos globales que registran las propias apps (p. ej. Claude) y las extensiones Vicinae y Open Bar.

## Iterar (al actualizar el sistema o cambiar algo)

1. En el equipo de referencia: `./export.sh`. Vuelca las secciones de dconf de la lista blanca a `dconf/*.ini` y avisa si las extensiones habilitadas no coinciden con `config/extensions.txt`.
2. Revisa `git diff`: descarta lo que no quieras versionar o ajusta las reglas en `tools/mignome.py` (`RULES`, `GLOBAL_EXCLUDE_KEYS`).
3. `./check.sh`: marca las claves que ya no existen en la versión de GNOME instalada, o los valores enum inválidos. Quítalas o cámbialas.
4. Si cambiaste de versión mayor de GNOME, actualiza `MIGNOME_TESTED_GNOME` en `lib/common.sh`.
