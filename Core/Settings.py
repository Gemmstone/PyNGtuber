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

    def __init__(self, parameters):
        super().__init__()
        uic.loadUi("UI/settingsWidget.ui", self)
        self.parameters = parameters
        self.sizeX.setValue(self.parameters["sizeX"])
        self.sizeY.setValue(self.parameters["sizeY"])
        self.posX.setValue(self.parameters["posX"])
        self.posY.setValue(self.parameters["posY"])
        self.posZ.setValue(self.parameters["posZ"])
        self.rotation.setValue(self.parameters["rotation"])
        self.check_hotkeys()

        self.sizeX.valueChanged.connect(self.save_current)
        self.sizeY.valueChanged.connect(self.save_current)
        self.posX.valueChanged.connect(self.save_current)
        self.posY.valueChanged.connect(self.save_current)
        self.posZ.valueChanged.connect(self.save_current)
        self.rotation.valueChanged.connect(self.save_current)
        self.setShortcut.clicked.connect(self.request_shortcut)

        self.blinkingGroup.setChecked(self.parameters["blinking"] != "ignore")
        self.talkingGroup.setChecked(self.parameters["talking"] != "ignore")
        self.cssGroup.setChecked(self.parameters["use_css"])

        self.css.setPlainText(self.parameters["css"])

        self.blinkingGroup.toggled.connect(self.hide_blinking)
        self.talkingGroup.toggled.connect(self.hide_talking)
        self.cssGroup.toggled.connect(self.hide_css)

        self.blinkOpen.setChecked(self.parameters["blinking"] == "blinking_open")
        self.blinkClosed.setChecked(self.parameters["blinking"] == "blinking_closed")

        self.talkOpen.setChecked(self.parameters["talking"] == "talking_open")
        self.talkClosed.setChecked(self.parameters["talking"] == "talking_closed")
        self.talkScreaming.setChecked(self.parameters["talking"] == "talking_screaming")

        self.blinkOpen.toggled.connect(self.save_current)
        self.blinkClosed.toggled.connect(self.save_current)
        self.talkOpen.toggled.connect(self.save_current)
        self.talkClosed.toggled.connect(self.save_current)
        self.talkScreaming.toggled.connect(self.save_current)

        self.css.textChanged.connect(self.css_finished_edit)

        self.saveDefault.clicked.connect(self.save_default)

        self.hide_blinking()
        self.hide_talking()
        self.hide_css()

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

    def hide_talking(self):
        if self.talkingGroup.isChecked():
            self.frame_4.show()
            self.talkingGroup.setStyleSheet("")
        else:
            self.frame_4.hide()
            self.talkingGroup.setStyleSheet(
                "QGroupBox::title{border-bottom-left-radius: 9px;border-bottom-right-radius: 9px;}")
        self.save_current()

    def hide_css(self):
        if self.cssGroup.isChecked():
            self.frame_5.show()
            self.cssGroup.setStyleSheet("")
        else:
            self.frame_5.hide()
            self.cssGroup.setStyleSheet(
                "QGroupBox::title{border-bottom-left-radius: 9px;border-bottom-right-radius: 9px;}")
        self.save_current()

    def save(self):
        self.parameters["sizeX"] = self.sizeX.value()
        self.parameters["sizeY"] = self.sizeY.value()
        self.parameters["posX"] = self.posX.value()
        self.parameters["posY"] = self.posY.value()
        self.parameters["posZ"] = self.posZ.value()
        self.parameters["use_css"] = True if self.cssGroup.isChecked() else False
        self.parameters["css"] = self.css.toPlainText()
        self.parameters["rotation"] = self.rotation.value()
        self.parameters["blinking"] = self.getBlinking() if self.blinkingGroup.isChecked() else "ignore"
        self.parameters["talking"] = self.getTalking() if self.talkingGroup.isChecked() else "ignore"

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


class SettingsToolBox(QToolBox):
    settings_changed = pyqtSignal(dict)
    shortcut = pyqtSignal(dict)
    delete_shortcut = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

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

    def set_items(self, items):
        routes = [i["route"] for i in items]
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

        filtered_items = [i for i in items if i["route"] not in used_routes]

        for item in filtered_items:
            route = item["route"]

            filename = os.path.basename(route)
            parent_folder = os.path.basename(os.path.dirname(route))

            title = f"{filename} {parent_folder}"

            thumbnail_path = os.path.join(
                os.path.dirname(route), "thumbs", os.path.basename(
                    route.replace(".gif", ".png").replace(".webp", ".png")
                )
            )

            settings_widget = Settings(item)
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