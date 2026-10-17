"""GTK 4/libadwaita main window, libshumate map, drawing and editing workflows."""

from __future__ import annotations

from dataclasses import replace
import math
from pathlib import Path
import sys

import gi

# GTK exposes cairo_t in draw callbacks through PyGObject's pycairo bridge.
gi.require_foreign("cairo")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Shumate", "1.0")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Pango, Shumate

from .constants import (
    APP_ID, APP_NAME, INITIAL_LAT, INITIAL_LON, INITIAL_ZOOM,
    MAX_MAP_LAT, OSM_ATTRIBUTION, OSM_LICENSE, TILE_URL, USER_AGENT,
)
from .exporters import to_csv, to_json
from .models import GeoPoint, LineRecord
from .storage import LineStore


class MapCanvas(Gtk.DrawingArea):
    """Transparent draw-mode input surface above the map.

    No events are intercepted when the user is navigating the map.
    Conversion is delegated to libshumate's map viewport, not approximated.
    """

    def __init__(self, owner: "MainWindow") -> None:
        super().__init__()
        self.owner = owner
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_content_width(2)
        self.set_content_height(2)
        self.set_can_target(False)
        self.set_draw_func(self._draw)
        self.press_xy: tuple[float, float] | None = None
        self.press_point: GeoPoint | None = None
        self.first_point: GeoPoint | None = None
        self.preview_end: GeoPoint | None = None
        self.drawing = False

        click = Gtk.GestureClick.new()
        click.set_button(1)
        click.connect("pressed", self._pressed)
        click.connect("released", self._released)
        self.add_controller(click)
        motion = Gtk.EventControllerMotion.new()
        motion.connect("motion", self._motion)
        self.add_controller(motion)

    def start(self) -> None:
        self.drawing = True
        self.set_can_target(True)
        self.set_cursor_from_name("crosshair")
        self.reset_points()

    def stop(self) -> None:
        self.drawing = False
        self.set_can_target(False)
        self.set_cursor_from_name(None)
        self.reset_points()

    def reset_points(self) -> None:
        self.press_xy = None
        self.press_point = None
        self.first_point = None
        self.preview_end = None
        self.queue_draw()

    def _to_point(self, x: float, y: float) -> GeoPoint:
        # GTK translate_coordinates handles any offsets between SimpleMap's
        # inner ShumateMap and this sibling drawing area.
        map_widget = self.owner.map_widget.get_map()
        translated = self.translate_coordinates(map_widget, x, y)
        if translated is None:
            raise ValueError("Pointer is outside the map")
        map_x, map_y = translated
        latitude, longitude = self.owner.viewport.widget_coords_to_location(map_widget, map_x, map_y)
        return GeoPoint(latitude, longitude)

    def _pressed(self, gesture: Gtk.GestureClick, n_press: int, x: float, y: float) -> None:
        if not self.drawing:
            return
        try:
            self.press_point = self._to_point(x, y)
        except ValueError:
            self.press_point = None
            return
        self.press_xy = (x, y)
        self.preview_end = self.press_point
        self.queue_draw()

    def _motion(self, _controller: Gtk.EventControllerMotion, x: float, y: float) -> None:
        if not self.drawing:
            return
        try:
            point = self._to_point(x, y)
        except ValueError:
            return
        self.owner.set_pointer_status(point)
        self.preview_end = point
        self.queue_draw()

    def _released(self, gesture: Gtk.GestureClick, n_press: int, x: float, y: float) -> None:
        if not self.drawing or self.press_xy is None or self.press_point is None:
            return
        try:
            end = self._to_point(x, y)
        except ValueError:
            self.owner.toast("Release the pointer inside the map")
            self.press_xy = None
            self.press_point = None
            return
        moved = math.hypot(x - self.press_xy[0], y - self.press_xy[1]) >= 5.0
        if moved:
            start = self.first_point if self.first_point is not None else self.press_point
            self.owner.complete_new_line(start, end)
        elif self.first_point is None:
            self.first_point = end
            self.owner.set_instruction("Start selected. Click the end point, or drag to it.")
        else:
            self.owner.complete_new_line(self.first_point, end)
        self.press_xy = None
        self.press_point = None
        self.queue_draw()

    def _project(self, point: GeoPoint) -> tuple[float, float] | None:
        map_widget = self.owner.map_widget.get_map()
        px, py = self.owner.viewport.location_to_widget_coords(
            map_widget, point.latitude, point.longitude,
        )
        result = map_widget.translate_coordinates(self, px, py)
        return result

    def _draw(self, _area: Gtk.DrawingArea, cr, width: int, height: int) -> None:
        if not self.drawing:
            return
        start = self.first_point or self.press_point
        if start is None:
            return
        coords_start = self._project(start)
        if coords_start is None:
            return
        sx, sy = coords_start
        end = self.preview_end
        if end is not None:
            coords_end = self._project(end)
            if coords_end is not None:
                ex, ey = coords_end
                cr.set_source_rgba(0.98, 0.3, 0.11, 0.96)
                cr.set_line_width(3.0)
                cr.move_to(sx, sy)
                cr.line_to(ex, ey)
                cr.stroke()
                cr.arc(ex, ey, 4.0, 0, math.tau)
                cr.fill()
        cr.set_source_rgb(0.05, 0.55, 0.95)
        cr.arc(sx, sy, 5.0, 0, math.tau)
        cr.fill()


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, application: "GPSLineApplication") -> None:
        super().__init__(application=application, title=APP_NAME, default_width=1280, default_height=800)
        self.store = LineStore()
        self.selected_id: str | None = None
        self.line_rows: dict[str, Gtk.ListBoxRow] = {}
        self.path_layers: list[Shumate.PathLayer] = []

        root = Adw.ToastOverlay()
        self.toasts = root
        self.set_content(root)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.set_child(outer)

        header = Adw.HeaderBar()
        outer.append(header)
        self.draw_button = Gtk.ToggleButton(label="Draw line")
        self.draw_button.add_css_class("suggested-action")
        self.draw_button.connect("toggled", self._toggle_drawing)
        header.pack_start(self.draw_button)
        goto_button = Gtk.Button(icon_name="find-location-symbolic", tooltip_text="Go to coordinates")
        goto_button.connect("clicked", lambda *_: self.show_goto())
        header.pack_start(goto_button)

        minus = Gtk.Button(icon_name="zoom-out-symbolic", tooltip_text="Zoom out")
        minus.connect("clicked", lambda *_: self.zoom(-1))
        plus = Gtk.Button(icon_name="zoom-in-symbolic", tooltip_text="Zoom in")
        plus.connect("clicked", lambda *_: self.zoom(1))
        header.pack_end(plus)
        header.pack_end(minus)

        self.instructions = Gtk.Label(label="Navigate the map, then choose Draw line.", xalign=0)
        self.instructions.set_margin_start(12)
        self.instructions.set_margin_top(6)
        self.instructions.set_margin_bottom(6)
        self.instructions.add_css_class("dim-label")
        outer.append(self.instructions)

        split = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        split.set_wide_handle(True)
        split.set_vexpand(True)
        split.set_position(350)
        split.set_shrink_start_child(False)
        split.set_shrink_end_child(False)
        split.set_resize_start_child(False)
        outer.append(split)

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        sidebar.set_size_request(300, -1)
        sidebar.set_margin_start(12)
        sidebar.set_margin_end(12)
        sidebar.set_margin_top(10)
        sidebar.set_margin_bottom(10)
        split.set_start_child(sidebar)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title = Gtk.Label(label="Saved lines", xalign=0)
        title.add_css_class("title-3")
        title.set_hexpand(True)
        row.append(title)
        sidebar.append(row)

        self.list_box = Gtk.ListBox()
        self.list_box.add_css_class("boxed-list")
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.connect("row-selected", self._selected)
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(self.list_box)
        scroll.set_vexpand(True)
        scroll.set_min_content_height(160)
        sidebar.append(scroll)

        action_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.edit_button = Gtk.Button(label="Edit")
        self.edit_button.connect("clicked", lambda *_: self.edit_selected())
        self.delete_button = Gtk.Button(label="Delete")
        self.delete_button.add_css_class("destructive-action")
        self.delete_button.connect("clicked", lambda *_: self.delete_selected())
        action_row.append(self.edit_button)
        action_row.append(self.delete_button)
        sidebar.append(action_row)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sidebar.append(sep)
        subtitle = Gtk.Label(label="Selected line", xalign=0)
        subtitle.add_css_class("heading")
        sidebar.append(subtitle)
        self.detail_label = Gtk.Label(label="Select a saved line", xalign=0, wrap=True)
        self.detail_label.set_selectable(True)
        sidebar.append(self.detail_label)
        self.start_label = self._detail_coordinate_row(sidebar, "Start")
        self.end_label = self._detail_coordinate_row(sidebar, "End")
        self.distance_label = Gtk.Label(label="", xalign=0)
        sidebar.append(self.distance_label)
        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        csv_button = Gtk.Button(label="Export CSV")
        json_button = Gtk.Button(label="Export JSON")
        csv_button.connect("clicked", lambda *_: self.export("csv"))
        json_button.connect("clicked", lambda *_: self.export("json"))
        buttons.append(csv_button)
        buttons.append(json_button)
        sidebar.append(buttons)
        hint = Gtk.Label(label="Exports include every saved line.\nData saves automatically on each change.", xalign=0, wrap=True)
        hint.add_css_class("dim-label")
        sidebar.append(hint)

        map_side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        split.set_end_child(map_side)
        map_overlay = Gtk.Overlay()
        map_overlay.set_hexpand(True)
        map_overlay.set_vexpand(True)
        map_side.append(map_overlay)

        # Identify tile requests before creating any map source or downloader.
        Shumate.set_user_agent(USER_AGENT)
        self.map_widget = Shumate.SimpleMap.new()
        self.map_widget.set_show_zoom_buttons(False)  # header zoom works in draw mode
        self.viewport = self.map_widget.get_viewport()
        self.viewport.set_max_zoom_level(19)
        self.viewport.set_min_zoom_level(1)
        osm = Shumate.RasterRenderer.new_full_from_url(
            "openstreetmap", "OpenStreetMap Standard",
            OSM_ATTRIBUTION, OSM_LICENSE, 0, 19, 256,
            Shumate.MapProjection.MERCATOR, TILE_URL,
        )
        self.map_widget.set_map_source(osm)
        self.map_widget.get_map().center_on(INITIAL_LAT, INITIAL_LON)
        self.viewport.set_zoom_level(INITIAL_ZOOM)
        map_overlay.set_child(self.map_widget)

        self.marker_layer = Shumate.MarkerLayer.new(self.viewport)
        self.map_widget.add_overlay_layer(self.marker_layer)
        self.canvas = MapCanvas(self)
        map_overlay.add_overlay(self.canvas)

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.set_margin_start(12)
        bar.set_margin_end(12)
        bar.set_margin_top(6)
        bar.set_margin_bottom(6)
        map_side.append(bar)
        credit = Gtk.Label(label=f"{OSM_ATTRIBUTION} · EPSG:4326 (WGS84)", xalign=0)
        credit.add_css_class("dim-label")
        credit.set_hexpand(True)
        bar.append(credit)
        self.pointer_status = Gtk.Label(label="", xalign=1)
        self.pointer_status.set_selectable(True)
        bar.append(self.pointer_status)

        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect("key-pressed", self._key_press)
        self.add_controller(key_controller)
        self.refresh_lines()

    @staticmethod
    def _detail_coordinate_row(container: Gtk.Box, label: str) -> Gtk.Label:
        head = Gtk.Label(label=label, xalign=0)
        head.add_css_class("dim-label")
        container.append(head)
        coordinates = Gtk.Label(label="—", xalign=0)
        coordinates.set_selectable(True)
        container.append(coordinates)
        return coordinates

    def toast(self, message: str) -> None:
        self.toasts.add_toast(Adw.Toast.new(message))

    def set_instruction(self, text: str) -> None:
        self.instructions.set_label(text)

    def set_pointer_status(self, point: GeoPoint) -> None:
        self.pointer_status.set_label(f"{point.latitude:.8f}, {point.longitude:.8f}")

    def _toggle_drawing(self, button: Gtk.ToggleButton) -> None:
        if button.get_active():
            self.canvas.start()
            self.draw_button.set_label("Cancel drawing")
            self.set_instruction("Drag from start to end, or click start then end. Esc cancels.")
        else:
            self.canvas.stop()
            self.draw_button.set_label("Draw line")
            self.set_instruction("Navigate the map, then choose Draw line.")
            self.pointer_status.set_label("")

    def _key_press(self, _control, keyval: int, keycode: int, state) -> bool:
        if keyval == Gdk.KEY_Escape and self.draw_button.get_active():
            self.draw_button.set_active(False)
            return True
        return False

    def complete_new_line(self, start: GeoPoint, end: GeoPoint) -> None:
        if start == end:
            self.toast("Choose two different points")
            return
        self.draw_button.set_active(False)
        self.show_line_editor(start, end)

    def zoom(self, direction: int) -> None:
        level = self.viewport.get_zoom_level()
        self.viewport.set_zoom_level(max(1.0, min(19.0, level + direction)))
        self.canvas.queue_draw()

    def _selected(self, _list: Gtk.ListBox, row: Gtk.ListBoxRow | None) -> None:
        self.selected_id = getattr(row, "line_id", None) if row is not None else None
        line = self.selected_line()
        enabled = line is not None
        self.edit_button.set_sensitive(enabled)
        self.delete_button.set_sensitive(enabled)
        self.detail_label.set_label(line.label if line else "Select a saved line")
        self.start_label.set_label(self.format_point(line.start) if line else "—")
        self.end_label.set_label(self.format_point(line.end) if line else "—")
        self.distance_label.set_label(
            f"Straight-line distance: {line.distance_m:,.2f} m" if line else "",
        )
        self.render_lines()
        if line:
            midpoint = self._midpoint(line.start, line.end)
            self.map_widget.get_map().center_on(midpoint.latitude, midpoint.longitude)

    @staticmethod
    def _midpoint(a: GeoPoint, b: GeoPoint) -> GeoPoint:
        # For short and local lines; handle longitude wrap-around across ±180°.
        dx = ((b.longitude - a.longitude + 180) % 360) - 180
        lon = ((a.longitude + dx / 2 + 180) % 360) - 180
        return GeoPoint((a.latitude + b.latitude) / 2, lon)

    @staticmethod
    def format_point(point: GeoPoint) -> str:
        return f"{point.latitude:.9f}, {point.longitude:.9f}"

    def selected_line(self) -> LineRecord | None:
        return next((x for x in self.store.lines if x.id == self.selected_id), None)

    def refresh_lines(self, prefer_id: str | None = None) -> None:
        self.list_box.unselect_all()
        while (child := self.list_box.get_first_child()) is not None:
            self.list_box.remove(child)
        self.line_rows = {}
        for line in self.store.lines:
            row = Gtk.ListBoxRow()
            row.line_id = line.id
            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            content.set_margin_top(9)
            content.set_margin_bottom(9)
            content.set_margin_start(9)
            content.set_margin_end(9)
            primary = Gtk.Label(label=line.label, xalign=0, ellipsize=Pango.EllipsizeMode.END)
            primary.add_css_class("heading")
            content.append(primary)
            small = Gtk.Label(label=f"{line.distance_m:,.1f} m · {self.format_point(line.start)}", xalign=0, ellipsize=Pango.EllipsizeMode.END)
            small.add_css_class("dim-label")
            content.append(small)
            row.set_child(content)
            self.list_box.append(row)
            self.line_rows[line.id] = row
        selected = self.line_rows.get(prefer_id or self.selected_id)
        if selected is not None:
            self.list_box.select_row(selected)
        else:
            self.list_box.unselect_all()
            self._selected(self.list_box, None)

    def render_lines(self) -> None:
        for layer in self.path_layers:
            self.map_widget.remove_overlay_layer(layer)
        self.path_layers.clear()
        self.marker_layer.remove_all()
        for line in self.store.lines:
            layer = Shumate.PathLayer.new(self.viewport)
            color = Gdk.RGBA()
            color.parse("#e65021" if line.id == self.selected_id else "#196bbb")
            layer.set_stroke(True)
            layer.set_stroke_color(color)
            layer.set_stroke_width(5 if line.id == self.selected_id else 3)
            layer.add_node(Shumate.Coordinate.new_full(line.start.latitude, line.start.longitude))
            layer.add_node(Shumate.Coordinate.new_full(line.end.latitude, line.end.longitude))
            self.map_widget.add_overlay_layer(layer)
            self.path_layers.append(layer)
        # Re-add the marker layer above paths so S/E endpoint labels remain visible.
        self.map_widget.remove_overlay_layer(self.marker_layer)
        self.map_widget.add_overlay_layer(self.marker_layer)
        # Keep endpoints visibly distinguishable on the currently selected line.
        selected = self.selected_line()
        if selected:
            for point, text in ((selected.start, "S"), (selected.end, "E")):
                marker = Shumate.Marker.new()
                marker.set_location(point.latitude, point.longitude)
                bubble = Gtk.Label(label=text)
                bubble.add_css_class("endpoint-marker")
                marker.set_child(bubble)
                self.marker_layer.add_marker(marker)

    def show_line_editor(self, start: GeoPoint, end: GeoPoint, existing: LineRecord | None = None) -> None:
        editor = Gtk.Window(title="Edit line" if existing else "Save line", transient_for=self, modal=True)
        editor.set_default_size(480, -1)
        contents = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        contents.set_margin_top(18)
        contents.set_margin_bottom(18)
        contents.set_margin_start(18)
        contents.set_margin_end(18)
        editor.set_child(contents)
        guide = Gtk.Label(label="Give the line a label. Adjust coordinates if you need finer placement.", xalign=0, wrap=True)
        contents.append(guide)
        grid = Gtk.Grid(column_spacing=12, row_spacing=10)
        contents.append(grid)
        line_number = len(self.store.lines) + 1
        fields = (
            ("Label", existing.label if existing else f"Line {line_number}"),
            ("Start latitude", f"{start.latitude:.9f}"),
            ("Start longitude", f"{start.longitude:.9f}"),
            ("End latitude", f"{end.latitude:.9f}"),
            ("End longitude", f"{end.longitude:.9f}"),
        )
        entries: list[Gtk.Entry] = []
        for idx, (name, value) in enumerate(fields):
            label = Gtk.Label(label=name, xalign=0)
            entry = Gtk.Entry(text=value, hexpand=True)
            grid.attach(label, 0, idx, 1, 1)
            grid.attach(entry, 1, idx, 1, 1)
            entries.append(entry)
        error = Gtk.Label(label="", xalign=0, wrap=True)
        error.add_css_class("error")
        contents.append(error)
        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, halign=Gtk.Align.END)
        cancel = Gtk.Button(label="Cancel")
        save = Gtk.Button(label="Save line")
        save.add_css_class("suggested-action")
        buttons.append(cancel)
        buttons.append(save)
        contents.append(buttons)
        cancel.connect("clicked", lambda *_: editor.close())

        def commit(*_args) -> None:
            try:
                label = entries[0].get_text().strip()
                coords = [float(entry.get_text().strip()) for entry in entries[1:]]
                first = GeoPoint(coords[0], coords[1])
                last = GeoPoint(coords[2], coords[3])
                line = (
                    replace(existing, label=label, start=first, end=last)
                    if existing else LineRecord.create(label, first, last)
                )
                self.store.upsert(line)
            except (ValueError, OSError, TypeError) as exc:
                error.set_label(str(exc))
                return
            editor.close()
            self.refresh_lines(line.id)
            self.toast("Line saved")

        save.connect("clicked", commit)
        entries[0].grab_focus()
        editor.present()

    def edit_selected(self) -> None:
        line = self.selected_line()
        if line:
            self.show_line_editor(line.start, line.end, existing=line)

    def delete_selected(self) -> None:
        line = self.selected_line()
        if not line:
            return
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE, text=f"Delete ‘{line.label}’?",
            secondary_text="This removes the line from the local collection.",
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Delete", Gtk.ResponseType.ACCEPT)
        def decided(_dialog, response) -> None:
            dialog.destroy()
            if response != Gtk.ResponseType.ACCEPT:
                return
            try:
                self.store.remove(line.id)
            except OSError as exc:
                self.toast(f"Could not delete: {exc}")
                return
            self.selected_id = None
            self.refresh_lines()
            self.toast("Line deleted")
        dialog.connect("response", decided)
        dialog.present()

    def show_goto(self) -> None:
        dialog = Gtk.Window(title="Go to coordinates", transient_for=self, modal=True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        dialog.set_child(box)
        box.append(Gtk.Label(label="Enter a centre position in decimal WGS84 coordinates.", xalign=0))
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lat = Gtk.Entry(text=f"{self.viewport.get_property("latitude"):.8f}")
        lon = Gtk.Entry(text=f"{self.viewport.get_property("longitude"):.8f}")
        lat.set_placeholder_text("Latitude")
        lon.set_placeholder_text("Longitude")
        row.append(lat)
        row.append(lon)
        box.append(row)
        err = Gtk.Label(label="", xalign=0)
        err.add_css_class("error")
        box.append(err)
        go = Gtk.Button(label="Centre map")
        go.add_css_class("suggested-action")
        box.append(go)
        def execute(*_args) -> None:
            try:
                point = GeoPoint(float(lat.get_text()), float(lon.get_text()))
            except ValueError as exc:
                err.set_label(str(exc))
                return
            self.map_widget.get_map().center_on(point.latitude, point.longitude)
            dialog.close()
        go.connect("clicked", execute)
        dialog.present()

    def export(self, format_name: str) -> None:
        if not self.store.lines:
            self.toast("There are no saved lines to export")
            return
        chooser = Gtk.FileDialog.new()
        chooser.set_title(f"Export {format_name.upper()}")
        chooser.set_initial_name(f"gps-lines.{format_name}")
        def saved(dialog: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
            try:
                file = dialog.save_finish(result)
                if file is None:
                    return
                path = file.get_path()
                if not path:
                    raise OSError("Choose a local filesystem destination")
                content = to_csv(self.store.lines) if format_name == "csv" else to_json(self.store.lines)
                Path(path).write_text(content, encoding="utf-8", newline="")
            except GLib.Error as exc:
                # Dismissing a native file chooser is not an error to report.
                if not exc.matches(Gio.io_error_quark(), Gio.IOErrorEnum.CANCELLED):
                    self.toast(f"Export failed: {exc.message}")
                return
            except OSError as exc:
                self.toast(f"Export failed: {exc}")
                return
            self.toast(f"Exported {len(self.store.lines)} lines to {format_name.upper()}")
        chooser.save(self, None, saved)


class GPSLineApplication(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.window: MainWindow | None = None

    def do_activate(self) -> None:
        if self.window is None:
            try:
                self.window = MainWindow(self)
            except (ValueError, OSError, KeyError, TypeError) as exc:
                # Never silently overwrite a damaged/unsupported JSON file.
                print(f"Failed to load GPS Line Studio data: {exc}", file=sys.stderr)
                self.quit()
                return
        self.window.present()


def main() -> int:
    return GPSLineApplication().run(sys.argv)
