from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl, pyqtSignal
from bs4 import BeautifulSoup
import os


class LayeredImageViewer(QWebEngineView):
    loadFinishedSignal = pyqtSignal(bool)

    def __init__(self, exe_dir, parent=None):
        super(LayeredImageViewer, self).__init__(parent)
        self.html_code = ""
        self.setColor("#b8cdee")
        self.is_loaded = False
        self.loadFinished.connect(self.on_load_finished)

        settings = self.page().settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)

        self.file = os.path.join(exe_dir, 'Viewer', 'viewer.html')
        self.file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.file)

        self.updateImages()

    def on_load_finished(self, result: bool):
        self.is_loaded = result
        self.loadFinishedSignal.emit(result)

    def setColor(self, color):
        self.page().runJavaScript(f'document.body.style.backgroundColor = "{color}";')

    def reload(self):
        self.is_loaded = False
        self.load(QUrl.fromLocalFile(self.file))

    def updateImages(self, image_list=None, bg_color="#b8cdee"):
        with open(self.file, 'r') as html_file:
            self.html_code = html_file.read()

        try:
            soup = BeautifulSoup(self.html_code, 'html.parser')
            body_tag = soup.body
            body_tag['style'] = f'background-color: {bg_color};'
            image_div = soup.find('div', id='image-wrapper')
            image_div.clear()

            self.page().toHtml(lambda html: self.handle_runtime_html(html, soup, image_div, image_list))
        except BaseException as err:
            print(f"HTML ERROR: {err}")

    def handle_runtime_html(self, runtime_page, soup, image_div, image_list):
        soup_runtime = BeautifulSoup(runtime_page, 'html.parser')
        input_element = soup_runtime.find('input', {'id': 'scaleFactorInput'})
        if input_element:
            value = input_element.get('value')
            if value:
                scale_factor = float(value)
            else:
                scale_factor = 1.0
        else:
            scale_factor = 1.0

        if image_list is not None:
            for layer in sorted(image_list, key=lambda x: x['posZ']):
                controller_wheel_div = soup.new_tag('div', style=f"""
                    position: absolute !important; 
                    transform-origin: calc(50% + {layer.get('originX', 0)}px) calc(50% + {layer.get('originY', 0)}px);
                    transform: rotate(0deg);
                """)
                controller_wheel_div['class'] = ["controller_wheel" if "controller_wheel" in layer.get('controller', ["ignore"]) else "ignore"]
                controller_wheel_div['player'] = layer.get("player", 1) - 1
                controller_wheel_div['deg'] = layer.get('deg', -90)
                controller_wheel_div['deadzone'] = layer.get("deadzone", 0.0550)

                controller_buttons_div = soup.new_tag('div', style=f"""
                    position: absolute !important; 
                    left: calc(50% + {layer.get('posIdleX', 0)}px);
                    top: calc(50% + {layer.get('posIdleY', 0)}px);
                    transform: rotate({layer.get('rotationIdle', 0)}deg);
                    display: {("block" if layer.get("buttons", 0) == 0 else "none") if layer.get("mode", 'display') else "block"};
                """)

                controller_buttons_div['class'] = ["controller_buttons" if "controller_buttons" in layer.get('controller', ["ignore"]) else "ignore"]
                controller_buttons_div['player'] = layer.get("player", 1) - 1

                controller_buttons_div['mode'] = layer.get("mode", 'display')
                controller_buttons_div['buttons'] = layer.get("buttons", 0)

                controller_buttons_div['posBothX'] = layer.get("posBothX", 0)
                controller_buttons_div['posBothY'] = layer.get("posBothY", 0)
                controller_buttons_div['rotationBoth'] = layer.get("rotationBoth", 0)

                controller_buttons_div['posLeftX'] = layer.get("posLeftX", 0)
                controller_buttons_div['posLeftY'] = layer.get("posLeftY", 0)
                controller_buttons_div['rotationLeft'] = layer.get("rotationLeft", 0)

                controller_buttons_div['posRightX'] = layer.get("posRightX", 0)
                controller_buttons_div['posRightY'] = layer.get("posRightY", 0)
                controller_buttons_div['rotationRight'] = layer.get("rotationRight", 0)

                img_tag = soup.new_tag('img', src=f"../{layer['route']}", style=f"""
                        position: absolute !important;
                        left: calc(50% + {layer['posX']}px);
                        top: calc(50% + {layer['posY']}px);
                        z-index: {layer['posZ']};
                        transform: translate(-50%, -50%) scale({scale_factor}) rotate({layer['rotation']}deg);
                        width: {layer['sizeX']}px; 
                        height: {layer['sizeY']}px;
                        {"opacity: 0" if layer['talking'] not in ['ignore', 'talking_closed'] else ""};
                        {layer['css']}
                    """)
                img_tag['class'] = [layer['blinking'], layer['talking']]

                controller_buttons_div.append(img_tag)
                controller_wheel_div.append(controller_buttons_div)

                image_div.append(controller_wheel_div)

        beautiful_html = soup.prettify()
        with open('Viewer/viewer.html', 'w') as html_file:
            html_file.write(beautiful_html)
        self.reload()
