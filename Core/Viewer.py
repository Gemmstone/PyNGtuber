from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PyQt6.QtCore import QUrl, pyqtSignal
from bs4 import BeautifulSoup
import re
import os


class WebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print("javaScriptConsoleMessage: ", level, message, lineNumber, sourceID)


class LayeredImageViewer(QWebEngineView):
    loadFinishedSignal = pyqtSignal(bool)

    def __init__(self, exe_dir, hw_acceleration=False, parent=None):
        super(LayeredImageViewer, self).__init__(parent)
        self.setPage(WebEnginePage(self))
        self.html_code = ""
        self.setColor("#b8cdee")
        self.is_loaded = False
        self.loadFinished.connect(self.on_load_finished)

        self.update_settings(hw_acceleration=hw_acceleration)

        self.file = os.path.join(exe_dir, 'Viewer', 'viewer.html')
        self.file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.file)

        self.updateImages()

    def update_settings(self, hw_acceleration=False):
        settings = self.page().settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)

        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, hw_acceleration)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, hw_acceleration)

    def on_load_finished(self, result: bool):
        self.is_loaded = result
        self.loadFinishedSignal.emit(result)

    def setColor(self, color):
        self.page().runJavaScript(f'document.body.style.backgroundColor = "{color}";')

    def reload(self):
        self.is_loaded = False
        self.load(QUrl.fromLocalFile(self.file))

    def updateImages(self, image_list=None, bg_color="#b8cdee", scale=100):
        self.is_loaded = False
        with open(self.file, 'r') as html_file:
            self.html_code = html_file.read()

        try:
            soup = BeautifulSoup(self.html_code, 'html.parser')
            body_tag = soup.body
            body_tag['style'] = f'background-color: {bg_color}; zoom: {scale}%'
            image_div = soup.find('div', id='image-wrapper')
            image_div.clear()

            self.page().toHtml(lambda html: self.handle_runtime_html(soup, image_div, image_list))
        except BaseException as err:
            print(f"HTML ERROR: {err}")

    def handle_runtime_html(self, soup, image_div, image_list):
        if image_list is not None:
            for layer in sorted(image_list, key=lambda x: x['posZ']):
                animation_idle_div = soup.new_tag('div', style=f"""
                    position: absolute !important; 
                """)
                animation_idle_div['class'] = [
                    "idle_animation" if layer.get("animation_idle", True) else "ignore"
                ]

                cursor_div = soup.new_tag('div', style=f"""
                                    position: absolute !important; 
                                    left: calc(50% + {layer.get('posIdleX', 0)}px);
                                    top: calc(50% + {layer.get('posIdleY', 0)}px);
                                """)
                cursor_div['class'] = [
                    "cursor_div" if layer.get("cursor", False) else "ignore"
                ]
                cursor_div['cursorScaleX'] = layer.get("cursorScaleX", layer.get("cursorScale", 0.01))
                cursor_div['cursorScaleY'] = layer.get("cursorScaleY", layer.get("cursorScale", 0.01))
                cursor_div['invert_mouse_x'] = layer.get("invert_mouse_x", 1)
                cursor_div['invert_mouse_y'] = layer.get("invert_mouse_y", 0)
                cursor_div['track_mouse_x'] = layer.get("track_mouse_x", 1)
                cursor_div['track_mouse_y'] = layer.get("track_mouse_y", 1)

                controller_buttons_div = soup.new_tag('div', style=f"""
                                    position: absolute !important; 
                                    left: calc(50% + {layer.get('posIdleX', 0)}px);
                                    top: calc(50% + {layer.get('posIdleY', 0)}px);
                                    transform: rotate({layer.get('rotationIdle', 0)}deg);
                                    display: {("block" if layer.get("buttons", 0) == 0 else "none") if layer.get("mode", 'display') else "block"};
                                """)

                controller_buttons_div['class'] = [
                    "controller_buttons" if "controller_buttons" in layer.get('controller', ["ignore"]) else "ignore"]
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

                guitar_buttons_div = soup.new_tag('div', style=f"""
                                    position: absolute !important; 
                                    left: calc(50% + {layer.get('posIdleX', 0)}px);
                                    top: calc(50% + {layer.get('posIdleY', 0)}px);
                                    transform: rotate({layer.get('rotationIdle', 0)}deg);
                                    display: {("block" if "None" in layer.get("chords", []) else "none") if layer.get("chords", []) != [] else "block"};
                                """)

                guitar_buttons_div['class'] = [
                    "guitar_buttons" if "controller_buttons" in layer.get('controller', ["ignore"]) else "ignore"]
                guitar_buttons_div['player'] = layer.get("player", 1) - 1
                guitar_buttons_div['chords'] = layer.get("chords", [])

                guitar_buttons_div['posGuitarUpX'] = layer.get("posGuitarUpX", 0)
                guitar_buttons_div['posGuitarUpY'] = layer.get("posGuitarUpY", 0)
                guitar_buttons_div['rotationGuitarUp'] = layer.get("rotationGuitarUp", 0)
                guitar_buttons_div['posGuitarDownX'] = layer.get("posGuitarDownX", 0)
                guitar_buttons_div['posGuitarDownY'] = layer.get("posGuitarDownY", 0)
                guitar_buttons_div['rotationGuitarDown'] = layer.get("rotationGuitarDown", 0)

                controller_wheelX_div = soup.new_tag('div', style=f"""
                    position: absolute !important; 
                    transform-origin: calc(50% + {layer.get('originX', 0)}px) calc(50% + {layer.get('originY', 0)}px);
                    transform: rotateZ(0deg);
                """)
                controller_wheelX_div['class'] = [
                    "controller_wheelX" if "controller_wheel" in layer.get('controller', ["ignore"]) else "ignore"
                ]
                controller_wheelX_div['player'] = layer.get("player2", 1) - 1
                controller_wheelX_div['deg'] = layer.get('deg', -90)
                controller_wheelX_div['invertAxis'] = layer.get('invertAxis', 0)
                controller_wheelX_div['deadzone'] = layer.get("deadzone", 0.0550)

                controller_wheelY_div = soup.new_tag('div', style=f"""
                    position: absolute !important; 
                    transform-origin: calc(50% + {layer.get('originXzoom', layer.get('originX', 0))}px) calc(50% + {layer.get('originYzoom', layer.get('originY', 0))}px);
                    transform: rotateX(0deg) scale(100%);
                """)
                controller_wheelY_div['class'] = [
                    "controller_wheelY" if "controller_wheel" in layer.get('controller', ["ignore"]) else "ignore"
                ]
                controller_wheelY_div['player'] = layer.get("player2", 1) - 1
                controller_wheelY_div['deg'] = layer.get('degZoom', layer.get('deg', -90))
                controller_wheelY_div['invertAxis'] = layer.get('invertAxis', 0)
                controller_wheelY_div['deadzone'] = layer.get("deadzone", 0.0550)

                controller_wheelZ_div = soup.new_tag('div', style=f"""
                    position: absolute !important; 
                    transform-origin: calc(50% + {layer.get('originXright', layer.get('originX', 0))}px) calc(50% + {layer.get('originYright', layer.get('originY', 0))}px);
                    transform: rotateY(0deg) rotateX(0deg);
                """)
                controller_wheelZ_div['class'] = [
                    "controller_wheelZ" if "controller_wheel" in layer.get('controller', ["ignore"]) else "ignore"
                ]
                controller_wheelZ_div['player'] = layer.get("player", 1) - 1
                controller_wheelZ_div['deg'] = layer.get('degRight', layer.get('deg', -90))
                controller_wheelZ_div['invertAxis'] = layer.get('invertAxis', 0)
                controller_wheelZ_div['deadzone'] = layer.get("deadzone", 0.0550)

                controller_wheelWhammy_div = soup.new_tag('div', style=f"""
                    position: absolute !important; 
                    transform-origin: calc(50% + {layer.get('originXwhammy', 0)}px) calc(50% + {layer.get('originYwhammy', 0)}px);
                    transform: rotateZ(0deg);
                """)
                controller_wheelWhammy_div['class'] = [
                    "Whammywheel" if "controller_wheel" in layer.get('controller', ["ignore"]) else "ignore"
                ]
                controller_wheelWhammy_div['player'] = layer.get("player", 1) - 1
                controller_wheelWhammy_div['deg'] = layer.get('degWhammy', 0)
                controller_wheelWhammy_div['invertAxis'] = layer.get('invertAxis', 0)
                controller_wheelWhammy_div['deadzone'] = layer.get("deadzone", 0.0550)

                animation_blinking_div = soup.new_tag('div', style="position: absolute !important;")
                animation_blinking_div['class'] = [layer.get("blinking", "ignore")]

                animation_talking_div = soup.new_tag('div', style=f"""
                    position: absolute !important;
                    {"opacity: 0" if layer['talking'] not in ['ignore', 'talking_closed'] else ""};
                """)
                animation_talking_div['class'] = [layer.get("talking", "ignore")]

                img_tag = soup.new_tag('img', src=f"../{layer['route']}", style=f"""
                        position: absolute !important;
                        left: calc(50% + {layer['posX']}px);
                        top: calc(50% + {layer['posY']}px);
                        z-index: {layer['posZ']};
                        transform: translate(-50%, -50%) rotate({layer['rotation']}deg);
                        width: {layer['sizeX']}px; 
                        height: {layer['sizeY']}px;
                        {layer['css']}
                    """)

                animation_talking_div.append(img_tag)
                animation_blinking_div.append(animation_talking_div)
                controller_wheelWhammy_div.append(animation_blinking_div)
                controller_wheelX_div.append(controller_wheelWhammy_div)
                controller_wheelZ_div.append(controller_wheelX_div)
                controller_wheelY_div.append(controller_wheelZ_div)
                guitar_buttons_div.append(controller_wheelY_div)
                controller_buttons_div.append(guitar_buttons_div)
                cursor_div.append(controller_buttons_div)
                animation_idle_div.append(cursor_div)

                image_div.append(animation_idle_div)

        beautiful_html = soup.prettify()
        with open(self.file, 'w') as html_file:
            html_file.write(beautiful_html)
        self.reload()

    def get_animations(self, file_path):
        with open(file_path, 'r') as file:
            css_text = file.read()

        animations = re.findall(r'@keyframes\s+([\w-]+)\s*{[^}]*\/\*\s*Avatar Animation\s*\*\/[^}]*}', css_text)
        # print(animations)
        return animations
