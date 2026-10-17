#!/usr/bin/env bash
set -euo pipefail
/usr/bin/python3 - <<'PY'
import gi
gi.require_foreign('cairo')
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Shumate', '1.0')
from gi.repository import Gtk, Adw, Shumate
print(f'GTK {Gtk.get_major_version()}.{Gtk.get_minor_version()}')
print(f'libadwaita {Adw.get_major_version()}.{Adw.get_minor_version()}')
print('Shumate map class:', Shumate.SimpleMap.__name__)
print('User agent support:', hasattr(Shumate, 'set_user_agent'))
print('All runtime imports successful')
PY
