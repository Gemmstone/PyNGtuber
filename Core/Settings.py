import os
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QToolBox, QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import pyqtSignal
from PyQt6 import uic


class Settings(QWidget):
    settings_changed = pyqtSignal(dict)
    settings_changed_default = pyqtSignal(dict)
    shortcut = pyqtSignal(dict)
    delete_shortcut = pyqtSignal(dict)

    def __init__(self, parameters, exe_dir, viewer, anim_file):
        super().__init__()
        uic.loadUi(os.path.join(exe_dir, f"UI", "settingsWidget.ui"), self)
        self.parameters = parameters
        self.viewer = viewer
        self.anim_file = anim_file
        self.sizeX.setValue(self.parameters["sizeX"])
        self.sizeY.setValue(self.parameters["sizeY"])

        self.og_width = self.parameters["sizeX"]
        self.og_height = self.parameters["sizeY"]

        self.posX.setValue(self.parameters["posX"])
        self.posY.setValue(self.parameters["posY"] * -1)
        self.posZ.setValue(self.parameters["posZ"])
        self.rotation.setValue(self.parameters["rotation"])

        self.originX.setValue(self.parameters.get("originX", 0))
        self.originY.setValue(self.parameters.get("originY", 0) * -1)
        self.deg.setValue(self.parameters.get("deg", 90))

        self.originXright.setValue(self.parameters.get("originXright", self.parameters.get("originX", 0)))
        self.originYright.setValue(self.parameters.get("originYright", self.parameters.get("originY", 0)) * -1)
        self.degRight.setValue(self.parameters.get("degRight", self.parameters.get("deg", 90)))
        self.originXzoom.setValue(self.parameters.get("originXzoom", self.parameters.get("originX", 0)))
        self.originYzoom.setValue(self.parameters.get("originYzoom", self.parameters.get("originY", 0)) * -1)
        self.degZoom.setValue(self.parameters.get("degZoom", self.parameters.get("deg", 90)))

        self.originXwhammy.setValue(self.parameters.get("originYwhammy", 0))
        self.originYwhammy.setValue(self.parameters.get("originXwhammy", 0) * -1)
        self.degWhammy.setValue(self.parameters.get("degWhammy", 0))

        self.cursorScaleX.setValue(self.parameters.get("cursorScaleX", self.parameters.get("cursorScale", 0.01)))
        self.cursorScaleY.setValue(self.parameters.get("cursorScaleY", self.parameters.get("cursorScale", 0.01)))
        self.invert_mouse_x.setChecked(self.parameters.get("invert_mouse_x", 1) == 1)
        self.invert_mouse_y.setChecked(self.parameters.get("invert_mouse_y", 0) == 1)
        self.track_mouse_x.setChecked(self.parameters.get("track_mouse_x", 1) == 1)
        self.track_mouse_y.setChecked(self.parameters.get("track_mouse_y", 1) == 1)

        self.deadzone.setValue(self.parameters.get("deadzone", 0.0550))
        self.player.setValue(self.parameters.get("player", 0))
        self.player2.setValue(self.parameters.get("player2", 0))
        self.buttonCombo.setCurrentIndex(self.parameters.get("buttons", 0))

        self.posBothX.setValue(self.parameters.get("posBothX", 0))
        self.posBothY.setValue(self.parameters.get("posBothY", 0) * -1)
        self.rotationBoth.setValue(self.parameters.get("rotationBoth", 0))
        self.posLeftX.setValue(self.parameters.get("posLeftX", 0))
        self.posLeftY.setValue(self.parameters.get("posLeftY", 0) * -1)
        self.rotationLeft.setValue(self.parameters.get("rotationLeft", 0))
        self.posRightX.setValue(self.parameters.get("posRightX", 0))
        self.posRightY.setValue(self.parameters.get("posRightY", 0) * -1)
        self.rotationRight.setValue(self.parameters.get("rotationRight", 0))

        self.posGuitarUpX.setValue(self.parameters.get("posGuitarUpX", 0))
        self.posGuitarUpY.setValue(self.parameters.get("posGuitarUpY", 0) * -1)
        self.rotationGuitarUp.setValue(self.parameters.get("rotationGuitarUp", 0))
        self.posGuitarDownX.setValue(self.parameters.get("posGuitarDownX", 0))
        self.posGuitarDownY.setValue(self.parameters.get("posGuitarDownY", 0) * -1)
        self.rotationGuitarDown.setValue(self.parameters.get("rotationGuitarDown", 0))

        self.guitarNote_Green.setChecked("Green" in self.parameters.get("chords", []))
        self.guitarNote_Red.setChecked("Red" in self.parameters.get("chords", []))
        self.guitarNote_Yellow.setChecked("Yellow" in self.parameters.get("chords", []))
        self.guitarNote_Blue.setChecked("Blue" in self.parameters.get("chords", []))
        self.guitarNote_Orange.setChecked("Orange" in self.parameters.get("chords", []))

        self.animation_idle.setChecked(self.parameters.get("animation_idle", True))
        self.load_animations()

        self.check_hotkeys()

        self.sizeX.valueChanged.connect(self.maintain_aspect_ratio_w)
        self.sizeY.valueChanged.connect(self.maintain_aspect_ratio_h)

        self.sizeX.valueChanged.connect(self.save_current)
        self.sizeY.valueChanged.connect(self.save_current)
        self.posX.valueChanged.connect(self.save_current)
        self.posY.valueChanged.connect(self.save_current)
        self.posZ.valueChanged.connect(self.save_current)
        self.rotation.valueChanged.connect(self.save_current)
        self.originX.valueChanged.connect(self.save_current)
        self.originY.valueChanged.connect(self.save_current)
        self.originXright.valueChanged.connect(self.save_current)
        self.originYright.valueChanged.connect(self.save_current)
        self.originXzoom.valueChanged.connect(self.save_current)
        self.originYzoom.valueChanged.connect(self.save_current)
        self.originXwhammy.valueChanged.connect(self.save_current)
        self.originYwhammy.valueChanged.connect(self.save_current)

        self.posBothX.valueChanged.connect(self.save_current)
        self.posBothY.valueChanged.connect(self.save_current)
        self.rotationBoth.valueChanged.connect(self.save_current)
        self.posLeftX.valueChanged.connect(self.save_current)
        self.posLeftY.valueChanged.connect(self.save_current)
        self.rotationLeft.valueChanged.connect(self.save_current)
        self.posRightX.valueChanged.connect(self.save_current)
        self.posRightY.valueChanged.connect(self.save_current)
        self.rotationRight.valueChanged.connect(self.save_current)

        self.posGuitarUpX.valueChanged.connect(self.save_current)
        self.posGuitarUpY.valueChanged.connect(self.save_current)
        self.rotationGuitarUp.valueChanged.connect(self.save_current)
        self.posGuitarDownX.valueChanged.connect(self.save_current)
        self.posGuitarDownY.valueChanged.connect(self.save_current)
        self.rotationGuitarDown.valueChanged.connect(self.save_current)

        self.cursorScaleX.valueChanged.connect(self.save_current)
        self.cursorScaleY.valueChanged.connect(self.save_current)
        self.invert_mouse_x.toggled.connect(self.save_current)
        self.invert_mouse_y.toggled.connect(self.save_current)
        self.track_mouse_x.toggled.connect(self.save_current)
        self.track_mouse_y.toggled.connect(self.save_current)

        self.deg.valueChanged.connect(self.save_current)
        self.degZoom.valueChanged.connect(self.save_current)
        self.degRight.valueChanged.connect(self.save_current)
        self.degWhammy.valueChanged.connect(self.save_current)
        self.deadzone.valueChanged.connect(self.save_current)
        self.player.valueChanged.connect(self.save_current)
        self.player2.valueChanged.connect(self.save_current)
        self.buttonCombo.currentIndexChanged.connect(self.save_current)
        self.setShortcut.clicked.connect(self.request_shortcut)

        if "controller" not in self.parameters.keys():
            self.parameters["controller"] = ["ignore"]

        self.blinkingGroup.setChecked(self.parameters["blinking"] != "ignore")
        self.talkingGroup.setChecked(self.parameters["talking"] != "ignore")
        self.controllerGroup.setChecked("ignore" not in self.parameters["controller"])
        self.cssGroup.setChecked(self.parameters["use_css"])
        self.invertAxis.setChecked(self.parameters.get("invertAxis", False))

        self.cursorGroup.setChecked(self.parameters.get("cursor", False))

        self.css.setPlainText(self.parameters["css"])

        self.blinkingGroup.toggled.connect(self.hide_blinking)
        self.talkingGroup.toggled.connect(self.hide_talking)
        self.controllerGroup.toggled.connect(self.hide_controller)
        self.cursorGroup.toggled.connect(self.hide_cursor)
        self.cssGroup.toggled.connect(self.hide_css)

        self.blinkOpen.setChecked(self.parameters["blinking"] == "blinking_open")
        self.blinkClosed.setChecked(self.parameters["blinking"] == "blinking_closed")

        self.display.setChecked(self.parameters.get("mode", 'display') == "display")
        self.move.setChecked(self.parameters.get("mode", 'display') == "move")
        self.guitar.setChecked(self.parameters.get("mode", 'display') == "guitar")

        self.talkOpen.setChecked(self.parameters["talking"] == "talking_open")
        self.talkClosed.setChecked(self.parameters["talking"] == "talking_closed")
        self.talkScreaming.setChecked(self.parameters["talking"] == "talking_screaming")

        self.controllerButtons.setChecked("controller_buttons" in self.parameters["controller"])
        self.controllerWheel.setChecked("controller_wheel" in self.parameters["controller"])

        self.blinkOpen.toggled.connect(self.save_current)
        self.blinkClosed.toggled.connect(self.save_current)
        self.talkOpen.toggled.connect(self.save_current)
        self.talkClosed.toggled.connect(self.save_current)
        self.talkScreaming.toggled.connect(self.save_current)
        self.controllerButtons.toggled.connect(self.save_current)
        self.controllerWheel.toggled.connect(self.save_current)
        self.invertAxis.toggled.connect(self.save_current)

        self.guitarNote_Green.toggled.connect(self.save_current)
        self.guitarNote_Red.toggled.connect(self.save_current)
        self.guitarNote_Yellow.toggled.connect(self.save_current)
        self.guitarNote_Blue.toggled.connect(self.save_current)
        self.guitarNote_Orange.toggled.connect(self.save_current)

        self.animation_idle.toggled.connect(self.hide_animations)

        self.idle_animation.currentIndexChanged.connect(self.save_current)
        self.talking_animation.currentIndexChanged.connect(self.save_current)
        self.idle_speed.valueChanged.connect(self.save_current)
        self.talking_speed.valueChanged.connect(self.save_current)

        self.display.toggled.connect(self.save_current)
        self.move.toggled.connect(self.save_current)
        self.guitar.toggled.connect(self.save_current)

        self.css.textChanged.connect(self.css_finished_edit)

        self.saveDefault.clicked.connect(self.save_default)

        self.hide_blinking()
        self.hide_talking()
        self.hide_controller()
        self.hide_cursor()
        self.hide_css()
        self.hide_animations()

    def load_animations(self):
        animations = self.viewer.get_animations(self.anim_file, get_all=True)

        self.idle_animation.clear()
        self.talking_animation.clear()

        for animation in animations:
            self.idle_animation.addItem(animation)
            self.talking_animation.addItem(animation)

        idle_animation = self.parameters.get("animation_name_idle", "None")
        talking_animation = self.parameters.get("animation_name_talking", "None")

        if idle_animation in animations:
            self.idle_animation.setCurrentText(idle_animation)
        if talking_animation in animations:
            self.talking_animation.setCurrentText(talking_animation)

        self.idle_speed.setValue(self.parameters.get("animation_speed_idle", 6))
        self.talking_speed.setValue(self.parameters.get("animation_speed_talking", 0.5))

    def check_hotkeys(self):
        if self.parameters["hotkeys"]:
            shortcuts = []
            for hotkey in self.parameters["hotkeys"]:
                if hotkey["type"] == "Midi":
                    shortcuts.append(f"Midi: {hotkey['command']['note']}")
                elif hotkey["type"] == "Keyboard":
                    shortcuts.append(f"Keyboard {hotkey['command']}")
                else:
                    shortcuts.append(f"{hotkey['type']} {hotkey['command']}")
            self.shortcutList.setText("\n".join(shortcuts))
            self.shortcutList.show()
        else:
            self.shortcutList.hide()

    def request_shortcut(self):
        self.shortcut.emit(self.parameters)

    def hide_blinking(self):
        if self.blinkingGroup.isChecked():
            self.frame_3.show()
            self.blinkingGroup.setStyleSheet("")
        else:
            self.frame_3.hide()
            self.blinkingGroup.setStyleSheet(
                "QGroupBox::title{border-bottom-left-radius: 9px;border-bottom-right-radius: 9px;}")
        self.save_current()

    def hide_animations(self):
        if self.animation_idle.isChecked():
            self.frameAnimations.show()
            self.animation_idle.setStyleSheet("")
        else:
            self.frameAnimations.hide()
            self.animation_idle.setStyleSheet(
                "QGroupBox::title{border-bottom-left-radius: 9px;border-bottom-right-radius: 9px;}")
        self.save_current()

    def hide_talking(self):
        if self.talkingGroup.isChecked():
            self.frame_4.show()
            self.talkingGroup.setStyleSheet("")
        else:
            self.frame_4.hide()
            self.talkingGroup.setStyleSheet(
                "QGroupBox::title{border-bottom-left-radius: 9px;border-bottom-right-radius: 9px;}")
        self.save_current()

    def hide_cursor(self):
        if self.cursorGroup.isChecked():
            self.frameCursor.show()
            self.cursorGroup.setStyleSheet("")
        else:
            self.frameCursor.hide()
            self.cursorGroup.setStyleSheet(
                "QGroupBox::title{border-bottom-left-radius: 9px;border-bottom-right-radius: 9px;}")
        self.save_current()

    def hide_controller(self):
        if self.controllerGroup.isChecked():
            self.frame_6.show()
            self.controllerGroup.setStyleSheet("")
        else:
            self.frame_6.hide()
            self.controllerGroup.setStyleSheet(
                "QGroupBox::title{border-bottom-left-radius: 9px;border-bottom-right-radius: 9px;}")
        self.save_current()

    def hide_css(self):
        if self.cssGroup.isChecked():
            self.frame_5.show()
            self.spacer.hide()
            self.cssGroup.setStyleSheet("")
        else:
            self.frame_5.hide()
            self.spacer.show()
            self.cssGroup.setStyleSheet(
                "QGroupBox::title{border-bottom-left-radius: 9px;border-bottom-right-radius: 9px;}")
        self.save_current()

    def save(self):
        self.parameters["sizeX"] = self.sizeX.value()
        self.parameters["sizeY"] = self.sizeY.value()
        self.parameters["posX"] = self.posX.value()
        self.parameters["posY"] = self.posY.value() * -1
        self.parameters["posZ"] = self.posZ.value()
        self.parameters["originX"] = self.originX.value()
        self.parameters["originY"] = self.originY.value() * -1
        self.parameters["deg"] = self.deg.value()
        self.parameters["originXright"] = self.originXright.value()
        self.parameters["originYright"] = self.originYright.value() * -1
        self.parameters["degRight"] = self.degRight.value()
        self.parameters["originXzoom"] = self.originXzoom.value()
        self.parameters["originYzoom"] = self.originYzoom.value() * -1
        self.parameters["degZoom"] = self.degZoom.value()
        self.parameters["originXwhammy"] = self.originXwhammy.value()
        self.parameters["originYwhammy"] = self.originYwhammy.value() * -1
        self.parameters["degWhammy"] = self.degWhammy.value()
        self.parameters["deadzone"] = self.deadzone.value()
        self.parameters["player"] = self.player.value()
        self.parameters["player2"] = self.player2.value()
        self.parameters["buttons"] = self.buttonCombo.currentIndex()
        self.parameters["invertAxis"] = 1 if self.invertAxis.isChecked() else 0
        self.parameters["chords"] = self.get_chords()

        self.parameters["cursorScaleX"] = self.cursorScaleX.value()
        self.parameters["cursorScaleY"] = self.cursorScaleY.value()
        self.parameters["invert_mouse_x"] = 1 if self.invert_mouse_x.isChecked() else 0
        self.parameters["invert_mouse_y"] = 1 if self.invert_mouse_y.isChecked() else 0
        self.parameters["track_mouse_x"] = 1 if self.track_mouse_x.isChecked() else 0
        self.parameters["track_mouse_y"] = 1 if self.track_mouse_y.isChecked() else 0
        self.parameters["cursor"] = self.cursorGroup.isChecked()

        self.parameters['mode'] = 'display' if self.display.isChecked() else 'move' if self.move.isChecked() else 'guitar'

        self.tabWidget.hide()
        self.frame_10.hide()
        self.frame_11.hide()

        if self.display.isChecked():
            self.frame_10.show()
        elif self.move.isChecked():
            self.tabWidget.show()
        else:
            self.frame_11.show()

        self.parameters['posBothX'] = self.posBothX.value()
        self.parameters['posBothY'] = self.posBothY.value() * -1
        self.parameters['rotationBoth'] = self.rotationBoth.value()
        self.parameters['posLeftX'] = self.posLeftX.value()
        self.parameters['posLeftY'] = self.posLeftY.value() * -1
        self.parameters['rotationLeft'] = self.rotationLeft.value()
        self.parameters['posRightX'] = self.posRightX.value()
        self.parameters['posRightY'] = self.posRightY.value() * -1
        self.parameters['rotationRight'] = self.rotationRight.value()

        self.parameters['posGuitarUpX'] = self.posGuitarUpX.value()
        self.parameters['posGuitarUpY'] = self.posGuitarUpY.value() * -1
        self.parameters['rotationGuitarUp'] = self.rotationGuitarUp.value()
        self.parameters['posGuitarDownX'] = self.posGuitarDownX.value()
        self.parameters['posGuitarDownY'] = self.posGuitarDownY.value() * -1
        self.parameters['rotationGuitarDown'] = self.rotationGuitarDown.value()

        self.parameters['animation_idle'] = self.animation_idle.isChecked()
        self.parameters['animation_name_idle'] = self.idle_animation.currentText()
        self.parameters['animation_name_talking'] = self.talking_animation.currentText()
        self.parameters['animation_speed_idle'] = self.idle_speed.value()
        self.parameters['animation_speed_talking'] = self.talking_speed.value()

        self.parameters["use_css"] = True if self.cssGroup.isChecked() else False
        self.parameters["css"] = self.css.toPlainText()
        self.parameters["rotation"] = self.rotation.value()
        self.parameters["blinking"] = self.getBlinking() if self.blinkingGroup.isChecked() else "ignore"
        self.parameters["talking"] = self.getTalking() if self.talkingGroup.isChecked() else "ignore"
        self.parameters["controller"] = self.getController() if self.controllerGroup.isChecked() else ["ignore"]

    def get_chords(self):
        chords = []
        chords_colors = ["None", "Green", "Red", "Yellow", "Blue", "Orange"]
        for color in chords_colors:
            chord = getattr(self, f"guitarNote_{color}")
            if chord.isChecked():
                chords.append(color)
        return chords

    def save_current(self):
        self.save()
        self.settings_changed.emit(self.parameters)

    def save_default(self):
        self.save()
        self.settings_changed_default.emit(self.parameters)

    def getBlinking(self):
        if self.blinkOpen.isChecked():
            return "blinking_open"
        return "blinking_closed"

    def getController(self):
        checked = []
        if self.controllerButtons.isChecked():
            self.frame_8.show()
            checked.append("controller_buttons")
        else:
            self.frame_8.hide()
        if self.controllerWheel.isChecked():
            self.frame_7.show()
            checked.append("controller_wheel")
        else:
            self.frame_7.hide()
        return checked if checked else ["ignore"]

    def getTalking(self):
        if self.talkOpen.isChecked():
            return "talking_open"
        elif self.talkScreaming.isChecked():
            return "talking_screaming"
        else:
            return "talking_closed"

    def css_finished_edit(self):
        self.parameters["css"] = self.css.toPlainText()
        self.save_current()

    def maintain_aspect_ratio_w(self):
        if self.aspectRatio.isChecked():
            ratio = self.sizeX.value() / self.og_width
            self.sizeY.blockSignals(True)
            self.sizeY.setValue(int(self.sizeY.value() * ratio))
            self.sizeY.blockSignals(False)
            self.og_width = self.sizeX.value()
            self.save_current()

    def maintain_aspect_ratio_h(self):
        if self.aspectRatio.isChecked():
            ratio = self.sizeY.value() / self.og_height
            self.sizeX.blockSignals(True)
            self.sizeX.setValue(int(self.sizeX.value() * ratio))
            self.sizeX.blockSignals(False)
            self.og_height = self.sizeY.value()
            self.save_current()


class SettingsToolBox(QToolBox):
    settings_changed = pyqtSignal(dict)
    shortcut = pyqtSignal(dict)
    delete_shortcut = pyqtSignal(dict)

    def __init__(self, exe_dir, viewer, anim_file):
        super().__init__()

        self.items = []
        self.page = None
        self.exe_dir = exe_dir
        self.viewer = viewer
        self.anim_file = anim_file

        StyleSheet = """

                QWidget{
                    background: #b8cdee;
                }

                QToolBox::tab {
                    background: #009deb;
                    border-radius: 5px;
                    text-align: center;
                    color: black;
                }

                /* 
                QToolBox::tab:first {
                    background: #4ade00;
                    border-radius: 5px;
                    color: black;
                }

                QToolBox::tab:last {
                    background: #f95300;
                    border-radius: 5px;
                    color: black;
                }
                */

                QToolBox::tab:selected { /* italicize selected tabs */
                    font: italic;
                    font-weight: bold;
                    background: pink;
                    text-align: center;
                    color: black;   
                }

                @QScrollBar:vertical
                {
                    background-color: white;
                    width: 3px;
                    margin: 0px 0px 0px 0px;
                    border: 0px transparent white;
                    border-radius: 5px;
                }

                QScrollBar::handle:vertical
                {
                    background-color: white;
                    min-height: 5px;
                    border-radius: 5px;
                }

                QScrollBar::sub-line:vertical
                {
                    margin: 0px 0px 0px 0px;
                    border-image: url(:/qss_icons/rc/up_arrow_disabled.png);
                    height: 0px;
                    width: 0px;
                    subcontrol-position: top;
                    subcontrol-origin: margin;
                }

                QScrollBar::add-line:vertical
                {
                    margin: 3px 0px 3px 0px;
                    border-image: url(:/qss_icons/rc/down_arrow_disabled.png);
                    height: 0px;
                    width: 0px;
                    subcontrol-position: bottom;
                    subcontrol-origin: margin;
                }

                QScrollBar::sub-line:vertical:hover,QScrollBar::sub-line:vertical:on
                {
                    border-image: url(:/qss_icons/rc/up_arrow.png);
                    height: 0px;
                    width: 0px;
                    subcontrol-position: top;
                    subcontrol-origin: margin;
                }

                QScrollBar::add-line:vertical:hover, QScrollBar::add-line:vertical:on
                {
                    border-image: url(:/qss_icons/rc/down_arrow.png);
                    height: 0px;
                    width: 0px;
                    subcontrol-position: bottom;
                    subcontrol-origin: margin;
                }

                QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical
                {
                    background: none;
                }

                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical
                {
                    background: none;
                }@
                """
        self.setStyleSheet(StyleSheet)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)

    def set_items(self, items, page):
        self.items = items
        self.page = page

        self.update()

    def change_page(self, page):
        self.page = page
        self.update()

    def update(self):
        routes = [i["route"] for i in self.items]

        used_routes = []
        while self.count() > 0:
            index = 0
            widget = self.widget(index)
            if widget:
                for i in range(widget.layout().count()):
                    child_widget = widget.layout().itemAt(i).widget()
                    if child_widget:
                        if child_widget.accessibleName() not in routes:
                            child_widget.setParent(None)
                        else:
                            used_routes.append(child_widget.accessibleName())

                widget.setParent(None)
            self.removeItem(index)

        filtered_items = [i for i in self.items if i["route"] not in used_routes]

        for item in filtered_items:

            route = item["route"]

            filename = os.path.basename(route)
            parent_folder = os.path.basename(os.path.dirname(route)) if not route.startswith("$url") else route.split("/")[1]

            if parent_folder.lower() == self.page.lower():
                title = f"{filename}"

                thumbnail_path = os.path.join(
                    os.path.dirname(route), "thumbs", os.path.basename(
                        route.replace(".gif", ".png").replace(".webp", ".png")
                    )
                ) if not filename.endswith(".html") else None

                settings_widget = Settings(item, exe_dir=self.exe_dir, viewer=self.viewer, anim_file=self.anim_file)
                settings_widget.settings_changed.connect(self.save)
                settings_widget.settings_changed_default.connect(self.save_as_default)
                settings_widget.delete_shortcut.connect(self.delete_shortcut_)
                settings_widget.shortcut.connect(self.request_shortcut)

                page = QWidget()
                page.setAccessibleName(route)
                layout = QVBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)

                layout.addWidget(settings_widget)
                page.setLayout(layout)

                self.addItem(page, "")
                index = self.count() - 1

                if thumbnail_path is not None:
                    thumbnail_label = QLabel()
                    thumbnail_pixmap = QPixmap(thumbnail_path)
                    thumbnail_label.setPixmap(thumbnail_pixmap.scaledToWidth(15))
                    self.setItemIcon(index, QIcon(thumbnail_pixmap))
                self.setItemText(index, title)

    def save(self, value):
        self.settings_changed.emit({"value": value, "default": False})

    def save_as_default(self, value):
        self.settings_changed.emit({"value": value, "default": True})

    def request_shortcut(self, value):
        self.shortcut.emit({"value": value, "type": "Assets"})

    def delete_shortcut_(self, value):
        self.delete_shortcut.emit(value)