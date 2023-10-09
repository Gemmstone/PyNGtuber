import os
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QToolBox, QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import pyqtSignal
from PyQt6 import uic


class Settings(QWidget):
    settings_changed = pyqtSignal(dict)

    def __init__(self, parameters):
        super().__init__()
        uic.loadUi("UI/settingsWidget.ui", self)
        self.parameters = parameters
        self.sizeX.setValue(parameters["sizeX"])
        self.sizeY.setValue(parameters["sizeY"])
        self.posX.setValue(parameters["posX"])
        self.posY.setValue(parameters["posY"])
        self.posZ.setValue(parameters["posZ"])
        self.rotation.setValue(parameters["rotation"])

        # Connect numeric field changes to the save method
        self.sizeX.valueChanged.connect(self.save)
        self.sizeY.valueChanged.connect(self.save)
        self.posX.valueChanged.connect(self.save)
        self.posY.valueChanged.connect(self.save)
        self.posZ.valueChanged.connect(self.save)
        self.rotation.valueChanged.connect(self.save)

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


        self.blinkOpen.toggled.connect(self.save)
        self.blinkClosed.toggled.connect(self.save)
        self.talkOpen.toggled.connect(self.save)
        self.talkClosed.toggled.connect(self.save)

        # Connect CSS field finishedit signal to the save method
        self.css.textChanged.connect(self.css_finished_edit)

        self.hide_blinking()
        self.hide_talking()
        self.hide_css()

    def hide_blinking(self):
        if self.blinkingGroup.isChecked():
            self.frame_3.show()
            self.blinkingGroup.setStyleSheet("")
        else:
            self.frame_3.hide()
            self.blinkingGroup.setStyleSheet("QGroupBox::title{border-bottom-left-radius: 9px;border-bottom-right-radius: 9px;}")
        self.save()

    def hide_talking(self):
        if self.talkingGroup.isChecked():
            self.frame_4.show()
            self.talkingGroup.setStyleSheet("")
        else:
            self.frame_4.hide()
            self.talkingGroup.setStyleSheet("QGroupBox::title{border-bottom-left-radius: 9px;border-bottom-right-radius: 9px;}")
        self.save()

    def hide_css(self):
        if self.cssGroup.isChecked():
            self.frame_5.show()
            self.cssGroup.setStyleSheet("")
        else:
            self.frame_5.hide()
            self.cssGroup.setStyleSheet("QGroupBox::title{border-bottom-left-radius: 9px;border-bottom-right-radius: 9px;}")
        self.save()


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

        self.settings_changed.emit(self.parameters)

    def getBlinking(self):
        if self.blinkOpen.isChecked():
            return "blinking_open"
        return "blinking_closed"

    def getTalking(self):
        if self.talkOpen.isChecked():
            return "talking_open"
        return "talking_closed"

    def css_finished_edit(self):
        # When CSS field editing is finished, save it
        self.parameters["css"] = self.css.toPlainText()
        self.save()  # Call save to save all parameters

class SettingsToolBox(QToolBox):
    settings_changed = pyqtSignal(dict)

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
        # Clear all existing items
        while self.count() > 0:
            self.removeItem(0)
        # Loop through your items
        for item in items:
            route = item["route"]

            filename = os.path.basename(route)
            parent_folder = os.path.basename(os.path.dirname(route))

            # Now, add the parent folder to the title
            title = f"{filename} {parent_folder}"

            thumbnail_path = os.path.join(os.path.dirname(route), "thumbs", os.path.basename(route))

            # Create a custom widget using your "Settings" class
            settings_widget = Settings(item)
            settings_widget.settings_changed.connect(self.save)
            # Create a page for the QToolBox
            page = QWidget()
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)

            # Add the "Settings" widget
            layout.addWidget(settings_widget)
            page.setLayout(layout)

            # Add the page to the QToolBox
            self.addItem(page, "")  # Leave the title blank for now
            index = self.count() - 1

            # Add the page to the QToolBox with the thumbnail icon as the title
            thumbnail_label = QLabel()
            thumbnail_pixmap = QPixmap(thumbnail_path)
            thumbnail_label.setPixmap(thumbnail_pixmap.scaledToWidth(15))  # Assuming 64 is a reasonable width
            self.setItemIcon(index, QIcon(thumbnail_pixmap))  # Set the icon for the item
            self.setItemText(index, title)

    def save(self, value):
        self.settings_changed.emit(value)
