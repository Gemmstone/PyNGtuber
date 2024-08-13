import copy

from PyQt6.QtWidgets import QToolBox, QWidget, QVBoxLayout, QLabel, QSizePolicy, QColorDialog
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QIcon, QPixmap, QColor
from Core.ShortcutsManager import ShortcutsDialog
from copy import deepcopy
from PyQt6 import uic
import json
import os


class Settings(QWidget):
    settings_changed = pyqtSignal(dict)
    settings_changed_default = pyqtSignal(dict)
    shortcut = pyqtSignal(dict)
    delete_shortcut = pyqtSignal(dict)

    def __init__(self, parameters, exe_dir, res_dir, viewer, anim_file, animations):
        super().__init__()
        self.og_height_screaming = 600
        self.og_width_screaming = 600
        self.og_height_talking = 600
        self.og_width_talking = 600
        self.og_height = 600
        self.og_width = 600
        uic.loadUi(os.path.join(exe_dir, f"UI", "settingsWidget.ui"), self)
        self.res_dir = res_dir
        self.exe_dir = exe_dir
        self.parameters = parameters
        self.viewer = viewer
        self.anim_file = anim_file
        self.animations = animations

        if self.parameters["route"] != "General Settings":
            self.warning.hide()
            self.warning_2.hide()
        else:
            self.frame_2.hide()

        self.set_data(changed_keys=[])

        # Idle position and size animation
        self.sizeX.valueChanged.connect(self.maintain_aspect_ratio_w)
        self.sizeY.valueChanged.connect(self.maintain_aspect_ratio_h)
        self.sizeX.valueChanged.connect(self.save_current)
        self.sizeY.valueChanged.connect(self.save_current)
        self.posX.valueChanged.connect(self.save_current)
        self.posY.valueChanged.connect(self.save_current)
        self.posZ.valueChanged.connect(self.save_current)
        self.rotation.valueChanged.connect(self.save_current)
        self.idle_position_pacing.currentIndexChanged.connect(self.save_current)
        self.idle_position_speed.valueChanged.connect(self.save_current)

        # Talking position and size animation
        self.sizeX_talking.valueChanged.connect(self.maintain_aspect_ratio_talking_w)
        self.sizeY_talking.valueChanged.connect(self.maintain_aspect_ratio_talking_h)
        self.sizeX_talking.valueChanged.connect(self.save_current)
        self.sizeY_talking.valueChanged.connect(self.save_current)
        self.posX_talking.valueChanged.connect(self.save_current)
        self.posY_talking.valueChanged.connect(self.save_current)
        self.rotation_talking.valueChanged.connect(self.save_current)
        self.talking_position_pacing.currentIndexChanged.connect(self.save_current)
        self.talking_position_speed.valueChanged.connect(self.save_current)

        # Screaming position and size animation
        self.sizeX_screaming.valueChanged.connect(self.maintain_aspect_ratio_screaming_w)
        self.sizeY_screaming.valueChanged.connect(self.maintain_aspect_ratio_screaming_h)
        self.sizeX_screaming.valueChanged.connect(self.save_current)
        self.sizeY_screaming.valueChanged.connect(self.save_current)
        self.posX_screaming.valueChanged.connect(self.save_current)
        self.posY_screaming.valueChanged.connect(self.save_current)
        self.rotation_screaming.valueChanged.connect(self.save_current)
        self.screaming_position_pacing.currentIndexChanged.connect(self.save_current)
        self.screaming_position_speed.valueChanged.connect(self.save_current)

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

        self.blinkingGroup.toggled.connect(self.hide_blinking)
        # self.talkingGroup.toggled.connect(self.hide_talking)
        self.controllerGroup.toggled.connect(self.hide_controller)
        self.positionGroup.toggled.connect(self.hide_position)
        self.cursorGroup.toggled.connect(self.hide_cursor)
        self.forced_mouse_tracking.toggled.connect(self.save_current)
        self.cssGroup.toggled.connect(self.hide_css)

        self.blinkOpen.toggled.connect(self.save_current)
        self.blinkClosed.toggled.connect(self.save_current)
        self.talkOpen.toggled.connect(self.save_current)
        self.talkClosed.toggled.connect(self.save_current)
        self.talkScreaming.toggled.connect(self.save_current)

        self.talkOpen.toggled.connect(self.show_animations)
        self.talkClosed.toggled.connect(self.show_animations)
        self.talkScreaming.toggled.connect(self.show_animations)

        self.controllerButtons.toggled.connect(self.save_current)
        self.controllerWheel.toggled.connect(self.save_current)
        self.invertAxis.toggled.connect(self.save_current)

        self.guitarNote_Green.toggled.connect(self.save_current)
        self.guitarNote_Red.toggled.connect(self.save_current)
        self.guitarNote_Yellow.toggled.connect(self.save_current)
        self.guitarNote_Blue.toggled.connect(self.save_current)
        self.guitarNote_Orange.toggled.connect(self.save_current)

        self.animation_idle.toggled.connect(self.save_current)

        self.idle_animation.currentIndexChanged.connect(self.save_current)
        self.idle_speed.valueChanged.connect(self.save_current)
        self.idle_animation_easing.currentIndexChanged.connect(self.save_current)
        self.idle_animation_direction.currentIndexChanged.connect(self.save_current)
        self.idle_animation_iteration.valueChanged.connect(self.save_current)

        self.talking_animation_direction.currentIndexChanged.connect(self.save_current)
        self.talking_animation.currentIndexChanged.connect(self.save_current)
        self.talking_speed.valueChanged.connect(self.save_current)
        self.talking_animation_easing.currentIndexChanged.connect(self.save_current)
        self.talking_animation_iteration.valueChanged.connect(self.save_current)

        self.screaming_animation_direction.currentIndexChanged.connect(self.save_current)
        self.screaming_animation.currentIndexChanged.connect(self.save_current)
        self.screaming_speed.valueChanged.connect(self.save_current)
        self.screaming_animation_easing.currentIndexChanged.connect(self.save_current)
        self.screaming_animation_iteration.valueChanged.connect(self.save_current)

        self.display.toggled.connect(self.save_current)
        self.move.toggled.connect(self.save_current)
        self.guitar.toggled.connect(self.save_current)

        self.shadowGroup.toggled.connect(self.hide_shadow)

        self.shadowBlur.valueChanged.connect(self.save_current)
        # self.color.textChanged.connect(self.change_color)
        # self.shadowOpacity.valueChanged.connect(self.save_current)
        self.shadowX.valueChanged.connect(self.save_current)
        self.shadowY.valueChanged.connect(self.save_current)

        self.filtersGroup.toggled.connect(self.hide_filters)

        self.hue.valueChanged.connect(self.save_current)
        self.saturation.valueChanged.connect(self.save_current)
        self.brightness.valueChanged.connect(self.save_current)
        self.contrast.valueChanged.connect(self.save_current)
        self.opacity.valueChanged.connect(self.save_current)
        self.blur.valueChanged.connect(self.save_current)
        self.grayscale.valueChanged.connect(self.save_current)
        self.invert.valueChanged.connect(self.save_current)
        self.sepia.valueChanged.connect(self.save_current)

        self.css.textChanged.connect(self.css_finished_edit)

        self.saveDefault.clicked.connect(self.save_default)

        self.color.clicked.connect(self.showColorDialog)

        self.hide_blinking()
        self.hide_shadow()
        self.hide_filters()
        self.show_animations()
        self.hide_controller()
        self.hide_position()
        self.hide_cursor()
        self.change_color()
        self.hide_css()

    def showColorDialog(self):

        initial = QColor()
        try:
            if "#" in self.color.text():
                raise Exception
            color = [int(i) for i in self.color.text().split(", ")]
            initial.setRed(color[0])
            initial.setGreen(color[1])
            initial.setBlue(color[2])
            initial.setAlpha(color[3])
        except BaseException:
            initial.setRed(0)
            initial.setGreen(0)
            initial.setBlue(0)
            initial.setAlpha(255)

        color = QColorDialog.getColor(
            initial=initial,
            options=QColorDialog.ColorDialogOption.ShowAlphaChannel
        )

        if color.isValid():
            color = color.getRgb()
            self.color.setText(", ".join([str(i) for i in color]))
            self.change_color()

    def change_color(self):
        self.colorFrame.setStyleSheet(f"""
        QFrame{{
            background-color: rgba({self.color.text() if "#" not in self.color.text() else "0, 0, 0, 255"});
            border-bottom-left-radius: 9px;
            border-bottom-right-radius: 5px;
            border-top-left-radius: 9px;
            border-top-right-radius: 5px;
            border-style: outset;
            border-width: 1px;
            border-color: black;
        }}
        """)
        self.save_current()

    def update_value(self, changed_keys, updating, key, function, default, type="normal"):
        if (key in changed_keys) or (not updating):
            obj_name, method_name = function.rsplit('.', 1)
            obj = getattr(self, obj_name)
            method = getattr(obj, method_name)

            if hasattr(obj, 'blockSignals'):
                obj.blockSignals(True)

            match type:
                case "result_ready":
                    method(default)
                case "invert":
                    method(self.parameters.get(key, default) * -1)
                case "compare to 1":
                    method(self.parameters.get(key, default) == 1)
                case "Green" | "Red" | "Yellow" | "Blue" | "Orange":
                    method(type in self.parameters.get(key, default))
                case "is not ignore":
                    method(self.parameters.get(key, default) != "ignore")
                case "ignore not in":
                    method("ignore" not in self.parameters.get(key, default))
                case "controller_buttons" | "controller_wheel":
                    method(type in self.parameters.get(key, default) or "guitar_buttons" in self.parameters.get(key, default))
                case "blinking_open" | "blinking_closed" | "display" | "move" | "guitar":
                    method(type == self.parameters.get(key, default))
                case "talking_open" | "talking_closed" | "talking_screaming":
                    method(
                        type in self.parameters.get(key, default)
                        or self.parameters.get(key, default) == ["ignore"]
                        or self.parameters.get(key, default) == "ignore"
                        or type == self.parameters.get(key, default)
                    )
                case _:
                    method(self.parameters.get(key, default))

            if hasattr(obj, 'blockSignals'):
                obj.blockSignals(False)
            return True
        return False

    def show_animations(self):
        if not self.talkClosed.isChecked() and not self.talkOpen.isChecked() and not self.talkScreaming.isChecked():
            sender = self.sender()
            sender.setChecked(True)
        self.tabWidget_6.setTabVisible(0, False)
        self.tabWidget_6.setTabVisible(1, False)
        self.tabWidget_6.setTabVisible(2, False)
        if self.talkClosed.isChecked():
            self.tabWidget_6.setTabVisible(0, True)
        if self.talkOpen.isChecked():
            self.tabWidget_6.setTabVisible(1, True)
        if self.talkScreaming.isChecked():
            self.tabWidget_6.setTabVisible(2, True)

    def set_data(self, changed_keys, updating=False):
        if self.update_value(changed_keys, updating, "sizeX", "sizeX.setValue", 600):
            if not updating:
                self.og_width = self.parameters["sizeX"]
        if self.update_value(changed_keys, updating, "sizeY", "sizeY.setValue", 600):
            if not updating:
                self.og_height = self.parameters["sizeY"]
        self.update_value(changed_keys, updating, "posX", "posX.setValue", 0)
        self.update_value(changed_keys, updating, "posY", "posY.setValue", 0, "invert")
        self.update_value(changed_keys, updating, "posZ", "posZ.setValue", 0)
        self.update_value(changed_keys, updating, "rotation", "rotation.setValue", 0)
        self.update_value(changed_keys, updating, "idle_position_pacing", "idle_position_pacing.setCurrentText", "EaseInOut")
        self.update_value(changed_keys, updating, "idle_position_speed", "idle_position_speed.setValue", 0.2)

        self.update_value(changed_keys, updating, "move", "positionGroup.setChecked", False)
        # self.update_value(changed_keys, updating, "moveToIDLE", "talkClosed.setChecked", True)
        # self.update_value(changed_keys, updating, "moveToTALKING", "talkOpen.setChecked", True)
        # self.update_value(changed_keys, updating, "moveToSCREAMING", "talkScreaming.setChecked", True)

        if self.update_value(changed_keys, updating, "sizeX_talking", "sizeX_talking.setValue", self.parameters["sizeX"]):
            if not updating:
                self.og_width_talking = self.parameters.get("sizeX_talking", self.og_width)
        if self.update_value(changed_keys, updating, "sizeY_talking", "sizeY_talking.setValue", self.parameters["sizeY"]):
            if not updating:
                self.og_height_talking = self.parameters.get("sizeY_talking", self.og_height)
        self.update_value(changed_keys, updating, "posX_talking", "posX_talking.setValue", self.parameters["posX"])
        self.update_value(changed_keys, updating, "posY_talking", "posY_talking.setValue", self.parameters["posY"], "invert")
        self.update_value(changed_keys, updating, "rotation_talking", "rotation_talking.setValue", self.parameters["rotation"])
        self.update_value(changed_keys, updating, "talking_position_pacing", "talking_position_pacing.setCurrentText", self.parameters.get("idle_position_pacing", "EaseInOut"))
        self.update_value(changed_keys, updating, "talking_position_speed", "talking_position_speed.setValue", self.parameters.get("idle_position_speed", 0.2))

        if self.update_value(changed_keys, updating, "sizeX_screaming", "sizeX_screaming.setValue", self.parameters.get("sizeX_talking", self.parameters["sizeX"])):
            if not updating:
                self.og_width_screaming = self.parameters.get("sizeX_screaming", self.og_width_talking)
        if self.update_value(changed_keys, updating, "sizeY_screaming", "sizeY_screaming.setValue", self.parameters.get("sizeY_talking", self.parameters["sizeY"])):
            if not updating:
                self.og_height_screaming = self.parameters.get("sizeY_screaming", self.og_height_talking)
        self.update_value(changed_keys, updating, "posX_screaming", "posX_screaming.setValue", self.parameters.get("posX_talking", self.parameters["posX"]))
        self.update_value(changed_keys, updating, "posY_screaming", "posY_screaming.setValue", self.parameters.get("posY_talking", self.parameters["posY"]), "invert")
        self.update_value(changed_keys, updating, "rotation_screaming", "rotation_screaming.setValue", self.parameters.get("rotation_talking", self.parameters["rotation"]))
        self.update_value(changed_keys, updating, "screaming_position_pacing", "screaming_position_pacing.setCurrentText", self.parameters.get("talking_position_pacing", self.parameters.get("idle_position_pacing", "EaseInOut")))
        self.update_value(changed_keys, updating, "screaming_position_speed", "screaming_position_speed.setValue", self.parameters.get("talking_position_speed", self.parameters.get("idle_position_speed", 0.2)))

        self.update_value(changed_keys, updating, "originX", "originX.setValue", 0)
        self.update_value(changed_keys, updating, "originY", "originY.setValue", 0, "invert")
        self.update_value(changed_keys, updating, "deg", "deg.setValue", 90)
        self.update_value(changed_keys, updating, "originXright", "originXright.setValue", self.parameters.get("originX", 0))
        self.update_value(changed_keys, updating, "originYright", "originYright.setValue", self.parameters.get("originY", 0), "invert")
        self.update_value(changed_keys, updating, "degRight", "degRight.setValue", self.parameters.get("deg", 90))
        self.update_value(changed_keys, updating, "originXzoom", "originXzoom.setValue", self.parameters.get("originX", 0))
        self.update_value(changed_keys, updating, "originYzoom", "originYzoom.setValue", self.parameters.get("originY", 0), "invert")
        self.update_value(changed_keys, updating, "degZoom", "degZoom.setValue", self.parameters.get("deg", 90))
        self.update_value(changed_keys, updating, "originXwhammy", "originXwhammy.setValue", 0)
        self.update_value(changed_keys, updating, "originYwhammy", "originYwhammy.setValue", 0, "invert")
        self.update_value(changed_keys, updating, "degWhammy", "degWhammy.setValue", 0)
        self.update_value(changed_keys, updating, "cursorScaleX", "cursorScaleX.setValue", self.parameters.get("cursorScale", 0.003))
        self.update_value(changed_keys, updating, "cursorScaleY", "cursorScaleY.setValue", self.parameters.get("cursorScale", 0.004))
        self.update_value(changed_keys, updating, "invert_mouse_x", "invert_mouse_x.setChecked", 1, "compare to 1")
        self.update_value(changed_keys, updating, "invert_mouse_y", "invert_mouse_y.setChecked", 1, "compare to 1")
        self.update_value(changed_keys, updating, "track_mouse_x", "track_mouse_x.setChecked", 1, "compare to 1")
        self.update_value(changed_keys, updating, "track_mouse_y", "track_mouse_y.setChecked", 1, "compare to 1")
        self.update_value(changed_keys, updating, "forced_mouse_tracking", "forced_mouse_tracking.setChecked", 0, "compare to 1")
        self.update_value(changed_keys, updating, "deadzone", "deadzone.setValue", 0.0550)
        self.update_value(changed_keys, updating, "player", "player.setValue", 0)
        self.update_value(changed_keys, updating, "player2", "player2.setValue", 0)
        self.update_value(changed_keys, updating, "buttons", "buttonCombo.setCurrentIndex", 0)
        self.update_value(changed_keys, updating, "posBothX", "posBothX.setValue", 0)
        self.update_value(changed_keys, updating, "posBothY", "posBothY.setValue", 0, "invert")
        self.update_value(changed_keys, updating, "rotationBoth", "rotationBoth.setValue", 0)
        self.update_value(changed_keys, updating, "posLeftX", "posLeftX.setValue", 0)
        self.update_value(changed_keys, updating, "posLeftY", "posLeftY.setValue", 0, "invert")
        self.update_value(changed_keys, updating, "rotationLeft", "rotationLeft.setValue", 0)
        self.update_value(changed_keys, updating, "posRightX", "posRightX.setValue", 0)
        self.update_value(changed_keys, updating, "posRightY", "posRightY.setValue", 0, "invert")
        self.update_value(changed_keys, updating, "rotationRight", "rotationRight.setValue", 0)
        self.update_value(changed_keys, updating, "posGuitarUpX", "posGuitarUpX.setValue", 0)
        self.update_value(changed_keys, updating, "posGuitarUpY", "posGuitarUpY.setValue", 0, "invert")
        self.update_value(changed_keys, updating, "rotationGuitarUp", "rotationGuitarUp.setValue", 0)
        self.update_value(changed_keys, updating, "posGuitarDownX", "posGuitarDownX.setValue", 0)
        self.update_value(changed_keys, updating, "posGuitarDownY", "posGuitarDownY.setValue", 0, "invert")
        self.update_value(changed_keys, updating, "rotationGuitarDown", "rotationGuitarDown.setValue", 0)
        self.update_value(changed_keys, updating, "chords", "guitarNote_Green.setChecked", [], "Green")
        self.update_value(changed_keys, updating, "chords", "guitarNote_Red.setChecked", [], "Red")
        self.update_value(changed_keys, updating, "chords", "guitarNote_Yellow.setChecked", [], "Yellow")
        self.update_value(changed_keys, updating, "chords", "guitarNote_Blue.setChecked", [], "Blue")
        self.update_value(changed_keys, updating, "chords", "guitarNote_Orange.setChecked", [], "Orange")
        self.update_value(changed_keys, updating, "animation_idle", "animation_idle.setChecked", True)
        self.update_value(changed_keys, updating, "blinking", "blinkingGroup.setChecked", "ignore", "is not ignore")
        self.update_value(changed_keys, updating, "talking", "talkingGroup.setChecked", "ignore", "is not ignore")
        self.update_value(changed_keys, updating, "controller", "controllerGroup.setChecked", ["ignore"], "ignore not in")
        self.update_value(changed_keys, updating, "use_css", "cssGroup.setChecked", False)
        self.update_value(changed_keys, updating, "invertAxis", "invertAxis.setChecked", False)
        self.update_value(changed_keys, updating, "cursor", "cursorGroup.setChecked", False)
        self.update_value(changed_keys, updating, "css", "css.setPlainText", "")
        self.update_value(changed_keys, updating, "cursor", "cursorGroup.setChecked", False)
        self.update_value(changed_keys, updating, "blinking", "blinkOpen.setChecked", "ignore", "blinking_open")
        self.update_value(changed_keys, updating, "blinking", "blinkClosed.setChecked", "ignore", "blinking_closed")

        self.update_value(changed_keys, updating, "talking", "talkOpen.setChecked", "ignore", "talking_open")
        self.update_value(changed_keys, updating, "talking", "talkClosed.setChecked", "ignore", "talking_closed")
        self.update_value(changed_keys, updating, "talking", "talkScreaming.setChecked", "ignore", "talking_screaming")

        self.update_value(changed_keys, updating, "mode", "display.setChecked", "display", "display")
        self.update_value(changed_keys, updating, "mode", "move.setChecked", "display", "move")
        self.update_value(changed_keys, updating, "mode", "guitar.setChecked", "display", "guitar")
        self.update_value(changed_keys, updating, "controller", "controllerButtons.setChecked", ["ignore"], "controller_buttons")
        self.update_value(changed_keys, updating, "controller", "controllerWheel.setChecked", ["ignore"], "controller_wheel")

        self.update_value(changed_keys, updating, "shadow", "shadowGroup.setChecked", False)

        self.update_value(changed_keys, updating, "shadowColor", "color.setText", "0, 0, 0, 255")
        self.update_value(changed_keys, updating, "shadowBlur", "shadowBlur.setValue", 0)
        # self.update_value(changed_keys, updating, "shadowOpacity", "shadowOpacity.setValue", 100)
        self.update_value(changed_keys, updating, "shadowX", "shadowX.setValue", 5)
        self.update_value(changed_keys, updating, "shadowY", "shadowY.setValue", -5)

        self.update_value(changed_keys, updating, "filters", "filtersGroup.setChecked", False)

        self.update_value(changed_keys, updating, "hue", "hue.setValue", 0.0)
        self.update_value(changed_keys, updating, "saturation", "saturation.setValue", 100.0)
        self.update_value(changed_keys, updating, "brightness", "brightness.setValue", 100.0)
        self.update_value(changed_keys, updating, "contrast", "contrast.setValue", 100.0)
        self.update_value(changed_keys, updating, "opacity", "opacity.setValue", 100.0)
        self.update_value(changed_keys, updating, "blur", "blur.setValue", 0.0)
        self.update_value(changed_keys, updating, "grayscale", "grayscale.setValue", 0.0)
        self.update_value(changed_keys, updating, "invert", "invert.setValue", 0.0)
        self.update_value(changed_keys, updating, "sepia", "sepia.setValue", 0.0)

        self.load_animations(changed_keys, updating)
        if not updating:
            self.check_hotkeys()

    def load_animations(self, changed_keys, updating):
        if not updating:
            self.idle_animation.clear()
            self.talking_animation.clear()
            self.screaming_animation.clear()

            for animation in self.animations:
                self.idle_animation.addItem(animation)
                self.talking_animation.addItem(animation)
                self.screaming_animation.addItem(animation)
        else:
            animations = []

        idle_animation = self.parameters.get("animation_name_idle", "None")
        talking_animation = self.parameters.get("animation_name_talking", "None")
        screaming_animation = self.parameters.get("animation_name_screaming", talking_animation)

        if idle_animation in self.animations or updating:
            self.update_value(changed_keys, updating, "animation_name_idle", "idle_animation.setCurrentText", idle_animation, "result_ready")
        if talking_animation in self.animations or updating:
            self.update_value(changed_keys, updating, "animation_name_talking", "talking_animation.setCurrentText", talking_animation, "result_ready")
        if screaming_animation in self.animations or updating:
            self.update_value(changed_keys, updating, "animation_name_screaming", "talking_animation.setCurrentText", talking_animation, "result_ready")

        self.update_value(changed_keys, updating, "animation_direction_idle", "idle_animation_direction.setCurrentText", "normal")
        self.update_value(changed_keys, updating, "animation_direction_talking", "talking_animation_direction.setCurrentText", "normal")
        self.update_value(changed_keys, updating, "animation_direction_screaming", "screaming_animation_direction.setCurrentText", "normal")

        self.update_value(changed_keys, updating, "animation_pacing_idle", "idle_animation_easing.setCurrentText", "EaseInOut")
        self.update_value(changed_keys, updating, "animation_pacing_talking", "talking_animation_easing.setCurrentText", "EaseInOut")
        self.update_value(changed_keys, updating, "animation_pacing_screaming", "screaming_animation_easing.setCurrentText", "EaseInOut")

        self.update_value(changed_keys, updating, "animation_speed_idle", "idle_speed.setValue", 6)
        self.update_value(changed_keys, updating, "animation_speed_talking", "talking_speed.setValue", 0.5)
        self.update_value(changed_keys, updating, "animation_speed_screaming", "screaming_speed.setValue", 0.5)

        self.update_value(changed_keys, updating, "animation_iteration_idle", "idle_animation_iteration.setValue", 0)
        self.update_value(changed_keys, updating, "animation_iteration_talking", "talking_animation_iteration.setValue", 0)
        self.update_value(changed_keys, updating, "animation_iteration_screaming", "screaming_animation_iteration.setValue", 0)

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

    def hide_css(self):
        if self.cssGroup.isChecked():
            self.frame_32.show()
            self.cssGroup.setStyleSheet("")
        else:
            self.frame_32.hide()
            self.cssGroup.setStyleSheet(
                "QGroupBox::title{border-bottom-left-radius: 9px;border-bottom-right-radius: 9px;}")
        self.save_current()

    def css_finished_edit(self):
        self.parameters["css"] = self.css.toPlainText()
        self.save_current()

    def hide_shadow(self):
        if self.shadowGroup.isChecked():
            self.frame_28.show()
            self.shadowGroup.setStyleSheet("")
        else:
            self.frame_28.hide()
            self.shadowGroup.setStyleSheet(
                "QGroupBox::title{border-bottom-left-radius: 9px;border-bottom-right-radius: 9px;}")
        self.save_current()

    def hide_filters(self):
        if self.filtersGroup.isChecked():
            self.frame_31.show()
            self.filtersGroup.setStyleSheet("")
        else:
            self.frame_31.hide()
            self.filtersGroup.setStyleSheet(
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

    def hide_position(self):
        if self.positionGroup.isChecked():
            self.frame_25.show()
            self.positionGroup.setStyleSheet("")
        else:
            self.frame_25.hide()
            self.positionGroup.setStyleSheet(
                "QGroupBox::title{border-bottom-left-radius: 9px;border-bottom-right-radius: 9px;}")
        self.save_current()

    def save(self):
        self.parameters["sizeX"] = self.sizeX.value()
        self.parameters["sizeY"] = self.sizeY.value()
        self.parameters["posX"] = self.posX.value()
        self.parameters["posY"] = self.posY.value() * -1
        self.parameters["posZ"] = self.posZ.value()
        self.parameters["rotation"] = self.rotation.value()

        self.parameters['move'] = self.positionGroup.isChecked()
        self.parameters['moveToIDLE'] = self.talkClosed.isChecked()
        self.parameters['moveToTALKING'] = self.talkOpen.isChecked()
        self.parameters['moveToSCREAMING'] = self.talkScreaming.isChecked()

        self.parameters['idle_position_speed'] = self.idle_position_speed.value()
        self.parameters['idle_position_pacing'] = self.idle_position_pacing.currentText()

        self.parameters["sizeX_talking"] = self.sizeX_talking.value()
        self.parameters["sizeY_talking"] = self.sizeY_talking.value()
        self.parameters["posX_talking"] = self.posX_talking.value()
        self.parameters["posY_talking"] = self.posY_talking.value() * -1
        self.parameters["rotation_talking"] = self.rotation_talking.value()

        self.parameters['talking_position_speed'] = self.talking_position_speed.value()
        self.parameters['talking_position_pacing'] = self.talking_position_pacing.currentText()

        self.parameters["sizeX_screaming"] = self.sizeX_screaming.value()
        self.parameters["sizeY_screaming"] = self.sizeY_screaming.value()
        self.parameters["posX_screaming"] = self.posX_screaming.value()
        self.parameters["posY_screaming"] = self.posY_screaming.value() * -1
        self.parameters["rotation_screaming"] = self.rotation_screaming.value()

        self.parameters['screaming_position_speed'] = self.screaming_position_speed.value()
        self.parameters['screaming_position_pacing'] = self.screaming_position_pacing.currentText()

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
        self.parameters['animation_name_screaming'] = self.screaming_animation.currentText()

        self.parameters['animation_speed_idle'] = self.idle_speed.value()
        self.parameters['animation_speed_talking'] = self.talking_speed.value()
        self.parameters['animation_speed_screaming'] = self.screaming_speed.value()

        self.parameters['animation_direction_idle'] = self.idle_animation_direction.currentText()
        self.parameters['animation_direction_talking'] = self.talking_animation_direction.currentText()
        self.parameters['animation_direction_screaming'] = self.screaming_animation_direction.currentText()

        self.parameters['animation_iteration_idle'] = self.idle_animation_iteration.value()
        self.parameters['animation_iteration_talking'] = self.talking_animation_iteration.value()
        self.parameters['animation_iteration_screaming'] = self.screaming_animation_iteration.value()

        self.parameters['animation_pacing_idle'] = self.idle_animation_easing.currentText()
        self.parameters['animation_pacing_talking'] = self.talking_animation_easing.currentText()
        self.parameters['animation_pacing_screaming'] = self.screaming_animation_easing.currentText()

        self.parameters["use_css"] = True if self.cssGroup.isChecked() else False
        self.parameters["css"] = self.css.toPlainText()
        self.parameters["blinking"] = self.getBlinking() if self.blinkingGroup.isChecked() else "ignore"
        self.parameters["talking"] = self.getTalking()
        self.parameters["controller"] = self.getController() if self.controllerGroup.isChecked() else ["ignore"]

        self.parameters["shadow"] = self.shadowGroup.isChecked()

        self.parameters["shadowColor"] = self.color.text()
        self.parameters["shadowBlur"] = self.shadowBlur.value()
        # self.parameters["shadowOpacity"] = self.shadowOpacity.value()
        self.parameters["shadowX"] = self.shadowX.value()
        self.parameters["shadowY"] = self.shadowY.value()

        self.parameters["filters"] = self.filtersGroup.isChecked()

        self.parameters["hue"] = self.hue.value()
        self.parameters["saturation"] = self.saturation.value()
        self.parameters["brightness"] = self.brightness.value()
        self.parameters["contrast"] = self.contrast.value()
        self.parameters["opacity"] = self.opacity.value()
        self.parameters["blur"] = self.blur.value()
        self.parameters["grayscale"] = self.grayscale.value()
        self.parameters["invert"] = self.invert.value()
        self.parameters["sepia"] = self.sepia.value()

        self.parameters["forced_mouse_tracking"] = 1 if self.forced_mouse_tracking.isChecked() else 0

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

        if self.parameters["route"] != "General Settings":
            with open(f'{os.path.join(self.res_dir, self.parameters["route"])}.json', "w") as f:
                save_data = copy.deepcopy(self.parameters)
                save_data.pop("route")
                json.dump(save_data, f, indent=4, ensure_ascii=False)

    def getBlinking(self):
        if self.blinkOpen.isChecked():
            return "blinking_open"
        return "blinking_closed"

    def getController(self):
        checked = []
        if self.controllerButtons.isChecked():
            if self.display.isChecked() or self.move.isChecked():
                checked.append("controller_buttons")
            if self.guitar.isChecked():
                checked.append("guitar_buttons")
            self.frame_8.show()
        else:
            self.frame_8.hide()
        if self.controllerWheel.isChecked():
            self.frame_7.show()
            checked.append("controller_wheel")
        else:
            self.frame_7.hide()
        return checked if checked else ["ignore"]

    def getTalking(self):
        talking = []
        if self.talkClosed.isChecked():
            talking.append("talking_closed")
        if self.talkOpen.isChecked():
            talking.append("talking_open")
        if self.talkScreaming.isChecked():
            talking.append("talking_screaming")

        if len(talking) == 3:
            talking = ["ignore"]
        return talking if talking else ["ignore"]

    def maintain_aspect_ratio(self, value, aspect_ratio, size, og_size):
        if aspect_ratio.isChecked():
            ratio = value / og_size
            size.blockSignals(True)
            result = int(size.value() * ratio)
            size.setValue(result)
            size.blockSignals(False)
            self.save_current()
            return result

    def maintain_aspect_ratio_w(self, value):
        result = self.maintain_aspect_ratio(value, self.aspectRatio, self.sizeY, self.og_width)
        if result is not None:
            self.og_width = result

    def maintain_aspect_ratio_h(self, value):
        result = self.maintain_aspect_ratio(value, self.aspectRatio, self.sizeX, self.og_height)
        if result is not None:
            self.og_height = result

    def maintain_aspect_ratio_talking_w(self, value):
        result = self.maintain_aspect_ratio(value, self.aspectRatio_talking, self.sizeY_talking, self.og_width_talking)
        if result is not None:
            self.og_width_talking = result

    def maintain_aspect_ratio_talking_h(self, value):
        result = self.maintain_aspect_ratio(value, self.aspectRatio_talking, self.sizeX_talking, self.og_height_talking)
        if result is not None:
            self.og_height_talking = result

    def maintain_aspect_ratio_screaming_w(self, value):
        result = self.maintain_aspect_ratio(value, self.aspectRatio_screaming, self.sizeY_screaming, self.og_width_screaming)
        if result is not None:
            self.og_width_screaming = result

    def maintain_aspect_ratio_screaming_h(self, value):
        result = self.maintain_aspect_ratio(value, self.aspectRatio_screaming, self.sizeX_screaming, self.og_height_screaming)
        if result is not None:
            self.og_height_screaming = result

    def update_data(self, value, default=False):
        exclusion_list = ['route', 'filename', "parent_folder", "thumbnail_path", "title", "hotkeys"]
        changed_keys = []
        for key, val in value.items():
            if key not in exclusion_list:
                if self.parameters.get(key) != val:
                    self.parameters[key] = deepcopy(val)
                    changed_keys.append(key)
        self.set_data(changed_keys, True)
        if default:
            self.settings_changed_default.emit(self.parameters)
        else:
            self.settings_changed.emit(self.parameters)


class SettingsToolBox(QToolBox):
    settings_changed = pyqtSignal(dict)
    settings_changed_list = pyqtSignal(list)
    shortcut = pyqtSignal(dict)
    delete_shortcut = pyqtSignal(dict)

    def __init__(self, exe_dir, res_dir, viewer, anim_file):
        super().__init__()

        self.items = []
        self.values = []
        self.page = None
        self.exe_dir = exe_dir
        self.res_dir = res_dir
        self.viewer = viewer
        self.anim_file = anim_file
        self.animations = self.viewer.get_animations(self.anim_file, get_all=True)
        self.childs = {}
        self.general_settings_changed = False

        StyleSheet = """
                QWidget{
                    background: #b8cdee;
                }

                QToolBox::tab {
                    border-radius: 5px;
                    text-align: center;
                    color: white;
                    background-color: rgba(0, 0, 0, 50);
                }

                QToolBox::tab:selected { /* italicize selected tabs */
                    font: italic;
                    font-weight: bold;
                    background: black;
                    text-align: center;
                    color: white;   
                }
                
                QToolBox::tab:hover {  
                    color: white;
                    background-color: rgb(0, 157, 235);
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

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_values)
        self.timer.start(1000)

    def addValue(self, value):
        self.values.append(value)

    def check_values(self):
        if self.values:
            self.settings_changed_list.emit(self.values)
            self.values.clear()

    def set_items(self, items, page):
        self.items = items
        self.page = page
        self.update_()

    def change_page(self, page, force_hide=False):
        self.page = page
        self.update_(force_hide)

    def update_(self, force_hide=False):
        self.blockSignals(True)
        filtered_items_category = []
        for item in self.items:
            route = item["route"]

            filename = os.path.basename(route)
            parent_folder = os.path.basename(os.path.dirname(route))

            if parent_folder.lower() == self.page.lower() and not force_hide:
                title = f"{filename}"

                thumbnail_path = os.path.join(
                    self.res_dir, os.path.dirname(route), "thumbs", os.path.basename(
                        route.replace(".gif", ".png").replace(".webp", ".png")
                    )
                ) if route != "General Settings" else None

                result = deepcopy(item)
                result["filename"] = filename
                result["parent_folder"] = parent_folder
                result["thumbnail_path"] = thumbnail_path
                result["title"] = title

                filtered_items_category.append(result)

        if len(filtered_items_category) > 2:
            general_settings_data = deepcopy(filtered_items_category[0])
            general_settings_data["route"] = "General Settings"
            general_settings_data["filename"] = "General Settings"
            general_settings_data["parent_folder"] = ""
            general_settings_data["thumbnail_path"] = ""
            general_settings_data["title"] = "General Settings"
            filtered_items_category = [general_settings_data] + filtered_items_category
            use_index_0 = False

        filtered_routes = [item["route"] for item in filtered_items_category]

        existing_widgets = {self.widget(index).accessibleName(): self.widget(index) for index in range(self.count())}
        used_routes = []
        for route, widget in existing_widgets.items():
            if route not in filtered_routes:
                for i in range(widget.layout().count()):
                    child_widget = widget.layout().itemAt(i).widget()
                    if child_widget:
                        child_widget.setParent(None)
                widget.setParent(None)
                self.removeItem(self.indexOf(widget))
                if route != "General Settings":
                    self.childs.pop(route)
            else:
                used_routes.append(route)

        index = 0
        for item in filtered_items_category:
            route = item["route"]
            thumbnail_path = item["thumbnail_path"]
            title = item["title"]

            if route in used_routes:
                continue

            settings_widget = Settings(item, exe_dir=self.exe_dir, res_dir=self.res_dir, viewer=self.viewer, anim_file=self.anim_file, animations=self.animations)
            if route == "General Settings":
                settings_widget.settings_changed.connect(self.update_childs)
                settings_widget.settings_changed_default.connect(self.save_as_default_childs)
            else:
                settings_widget.settings_changed.connect(self.save)
                settings_widget.settings_changed_default.connect(self.save_as_default)
                settings_widget.delete_shortcut.connect(self.delete_shortcut_)
                settings_widget.shortcut.connect(self.request_shortcut)
            settings_widget.setAccessibleName(route)

            page = QWidget()
            page.setAccessibleName(route)
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)

            layout.addWidget(settings_widget)
            page.setLayout(layout)
            if route == "General Settings":
                self.insertItem(0, page, None)
                self.setCurrentIndex(0)
                self.setItemText(0, title)
            else:
                self.addItem(page, "")
                index = self.count() - 1
                self.setItemText(index, title)
                if thumbnail_path is not None:
                    thumbnail_label = QLabel()
                    thumbnail_pixmap = QPixmap(thumbnail_path)
                    thumbnail_label.setPixmap(thumbnail_pixmap.scaledToWidth(15))
                    self.setItemIcon(index, QIcon(thumbnail_pixmap))

                self.setCurrentIndex(index)
                self.childs[route] = settings_widget
        self.setCurrentIndex(index)
        self.blockSignals(False)
        self.currentChanged.emit(index)

    def update_childs(self, value):
        self.general_settings_changed = True
        for child in self.childs:
            self.childs[child].update_data(value)
        self.general_settings_changed = False

    def save_as_default_childs(self, value):
        self.general_settings_changed = True
        for child in self.childs:
            self.childs[child].update_data(value, True)
        self.general_settings_changed = False

    def save(self, value):
        if self.general_settings_changed:
            self.addValue({"value": value, "default": False})
        else:
            self.settings_changed.emit({"value": value, "default": False})

    def save_as_default(self, value):
        if self.general_settings_changed:
            self.addValue({"value": value, "default": True})
        else:
            self.settings_changed.emit({"value": value, "default": True})

    def request_shortcut(self, value):
        self.shortcut.emit({"value": value, "type": "Assets"})

    def delete_shortcut_(self, value):
        self.delete_shortcut.emit(value)