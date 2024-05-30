import copy

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PyQt6.QtCore import QUrl, pyqtSignal, QThreadPool, pyqtSlot, QRunnable, QObject
from bs4 import BeautifulSoup
import traceback
import sys
import re
import os


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(
                *self.args, **self.kwargs
            )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class WebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print("javaScriptConsoleMessage: ", level, message, lineNumber, sourceID)


class LayeredImageViewer(QWebEngineView):
    loadFinishedSignal = pyqtSignal(bool)
    div_count_signal = pyqtSignal(str)

    def __init__(self, exe_dir, hw_acceleration=False, parent=None):
        super(LayeredImageViewer, self).__init__(parent)
        self.res_dir = exe_dir
        self.setPage(WebEnginePage(self))
        self.html_code = ""
        self.setColor("#b8cdee")
        self.is_loaded = False
        self.loadFinished.connect(self.on_load_finished)

        self.threadpool = QThreadPool()

        self.oldIds = []

        self.update_settings(hw_acceleration=hw_acceleration)

        self.file = os.path.join(self.res_dir, 'Viewer', 'viewer.html')
        self.file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.file)

        self.reload()

        self.updateImages()

    def update_settings(self, hw_acceleration=False):
        settings = self.page().settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
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
        self.is_loaded = True

        with open(self.file, 'r') as html_file:
            self.html_code = html_file.read()

    def updateImages(self, image_list=None, bg_color="#b8cdee", scale=100, edited=None):
        worker = Worker(self.update_thread, image_list, bg_color, scale, edited)
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)

    def print_output(self, result):
        self.page().runJavaScript(f'document.body.style.backgroundColor = "{result["bg_color"]}";')
        self.page().runJavaScript(f'document.body.style.zoom = "{result["scale"]}%";')
        self.page().runJavaScript(f'update_images(`{result["html_content"]}`);')
        self.div_count_signal.emit(result["div_count"])

    def thread_complete(self):
        self.images_loaded = True

    def update_thread(self, image_list=None, bg_color="#b8cdee", scale=100, edited=None):
        soup = BeautifulSoup('<div id="image-wrapper"></div>', 'html.parser')
        image_wrapper = soup.find(id="image-wrapper")

        flipper_div = soup.new_tag("div", style=f"""
            position: absolute !important;
            animation-direction: normal;
            transition = 'all 0.5s ease-in-out';
        """)
        flipper_div['class'] = ["flipper"]

        div_count = 0
        if image_list is not None:
            for layer in sorted(image_list, key=lambda x: x['posZ']):
                editing = "not_in_editor"
                if edited is not None:
                    if edited["type"] == "general":
                        editing = "being_edited" if f'assets/{edited["value"].lower()}/' in layer['route'].replace("\\", "/").lower() else "not_being_edited"
                    else:
                        editing = "being_edited" if layer['route'] == edited["value"] else "not_being_edited"

                animation_idle_div = None
                if layer.get("animation_idle", True):
                    animation_idle_div = soup.new_tag('div', style=f"""
                        position: absolute !important;
                        animation-direction: normal;
                        z-index: {layer['posZ']};
                    """)
                    animation_idle_div['class'] = ["idle_animation"]

                animation_added_div = None
                if layer.get("animation_name_idle", "None") != "None" or layer.get("animation_name_talking", "None") != None:
                    animation_added_div = soup.new_tag('div', style=f"""
                                        position: absolute !important; 
                                        animation-direction: normal;
                                        z-index: {layer['posZ']};
                                    """)
                    animation_added_div['class'] = ["added_animation"]
                    animation_added_div['animation_name_idle'] = layer.get("animation_name_idle", "None")
                    animation_added_div['animation_name_talking'] = layer.get("animation_name_talking", "None")
                    animation_added_div['animation_name_screaming'] = layer.get("animation_name_screaming", animation_added_div['animation_name_talking'])

                    animation_added_div['animation_speed_idle'] = layer.get("animation_speed_idle", 6)
                    animation_added_div['animation_speed_talking'] = layer.get("animation_speed_talking", 0.5)
                    animation_added_div['animation_speed_screaming'] = layer.get("animation_speed_screaming", animation_added_div['animation_speed_talking'])

                    animation_added_div['animation_direction_idle'] = layer.get('animation_direction_idle',  "normal")
                    animation_added_div['animation_direction_talking'] = layer.get('animation_direction_talking',  "normal")
                    animation_added_div['animation_direction_screaming'] = layer.get('animation_direction_screaming',  animation_added_div['animation_direction_talking'])

                    animation_added_div['animation_iteration_idle'] = layer.get("animation_iteration_idle", 0)
                    animation_added_div['animation_iteration_talking'] = layer.get("animation_iteration_talking", 0)
                    animation_added_div['animation_iteration_screaming'] = layer.get("animation_iteration_screaming", animation_added_div['animation_iteration_talking'])

                    animation_added_div['animation_pacing_idle'] = layer.get('animation_pacing_idle',  "ease-in-out")
                    animation_added_div['animation_pacing_talking'] = layer.get('animation_pacing_talking',  "ease-in-out")
                    animation_added_div['animation_pacing_screaming'] = layer.get('animation_pacing_screaming',  animation_added_div['animation_pacing_talking'])

                cursor_div = None
                if layer.get("cursor", False):
                    cursor_div = soup.new_tag('div', style=f"""
                                        position: absolute !important; 
                                        z-index: {layer['posZ']};
                                        left: calc(50% + {layer.get('posIdleX', 0)}px);
                                        top: calc(50% + {layer.get('posIdleY', 0)}px);
                                    """)
                    cursor_div['class'] = ["cursor_div"]
                    cursor_div['cursorScaleX'] = layer.get("cursorScaleX", layer.get("cursorScale", 0.01))
                    cursor_div['cursorScaleY'] = layer.get("cursorScaleY", layer.get("cursorScale", 0.01))
                    cursor_div['invert_mouse_x'] = layer.get("invert_mouse_x", 1)
                    cursor_div['invert_mouse_y'] = layer.get("invert_mouse_y", 0)
                    cursor_div['track_mouse_x'] = layer.get("track_mouse_x", 1)
                    cursor_div['track_mouse_y'] = layer.get("track_mouse_y", 1)

                controller_buttons_div = None
                guitar_buttons_div = None
                controller_wheelX_div = None
                controller_wheelY_div = None
                controller_wheelZ_div = None
                controller_wheelWhammy_div = None

                controller = layer.get('controller', ["ignore"])
                if controller != ["ignore"]:

                    if "controller_buttons" in controller:
                        controller_buttons_div = soup.new_tag('div', style=f"""
                                        position: absolute !important; 
                                        z-index: {layer['posZ']};
                                        left: calc(50% + {layer.get('posIdleX', 0)}px);
                                        top: calc(50% + {layer.get('posIdleY', 0)}px);
                                        transform: rotate({layer.get('rotationIdle', 0)}deg);
                                        display: {("block" if layer.get("buttons", 0) == 0 else "none") if layer.get("mode", 'display') else "block"};
                                    """)
                        controller_buttons_div['class'] = ["controller_buttons"]
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

                    if "controller_buttons" in controller:
                        guitar_buttons_div = soup.new_tag('div', style=f"""
                                        position: absolute !important; 
                                        z-index: {layer['posZ']};
                                        left: calc(50% + {layer.get('posIdleX', 0)}px);
                                        top: calc(50% + {layer.get('posIdleY', 0)}px);
                                        transform: rotate({layer.get('rotationIdle', 0)}deg);
                                        display: {("block" if "None" in layer.get("chords", []) else "none") if layer.get("chords", []) != [] else "block"};
                                    """)
                        guitar_buttons_div['class'] = ["guitar_buttons"]
                        guitar_buttons_div['player'] = layer.get("player", 1) - 1
                        guitar_buttons_div['chords'] = layer.get("chords", [])

                        guitar_buttons_div['posGuitarUpX'] = layer.get("posGuitarUpX", 0)
                        guitar_buttons_div['posGuitarUpY'] = layer.get("posGuitarUpY", 0)
                        guitar_buttons_div['rotationGuitarUp'] = layer.get("rotationGuitarUp", 0)
                        guitar_buttons_div['posGuitarDownX'] = layer.get("posGuitarDownX", 0)
                        guitar_buttons_div['posGuitarDownY'] = layer.get("posGuitarDownY", 0)
                        guitar_buttons_div['rotationGuitarDown'] = layer.get("rotationGuitarDown", 0)

                    if "controller_wheel" in controller:
                        controller_wheelX_div = soup.new_tag('div', style=f"""
                            position: absolute !important; 
                            z-index: {layer['posZ']};
                            transform-origin: calc(50% + {layer.get('originX', 0)}px) calc(50% + {layer.get('originY', 0)}px);
                            transform: rotateZ(0deg);
                        """)
                        controller_wheelX_div['class'] = ["controller_wheelX"]
                        controller_wheelX_div['player'] = layer.get("player2", 1) - 1
                        controller_wheelX_div['deg'] = layer.get('deg', -90)
                        controller_wheelX_div['invertAxis'] = layer.get('invertAxis', 0)
                        controller_wheelX_div['deadzone'] = layer.get("deadzone", 0.0550)

                    if "controller_wheel" in controller:
                        controller_wheelY_div = soup.new_tag('div', style=f"""
                            position: absolute !important; 
                            z-index: {layer['posZ']};
                            transform-origin: calc(50% + {layer.get('originXzoom', layer.get('originX', 0))}px) calc(50% + {layer.get('originYzoom', layer.get('originY', 0))}px);
                            transform: rotateX(0deg) scale(100%);
                        """)
                        controller_wheelY_div['class'] = ["controller_wheelY"]
                        controller_wheelY_div['player'] = layer.get("player2", 1) - 1
                        controller_wheelY_div['deg'] = layer.get('degZoom', layer.get('deg', -90))
                        controller_wheelY_div['invertAxis'] = layer.get('invertAxis', 0)
                        controller_wheelY_div['deadzone'] = layer.get("deadzone", 0.0550)

                    if "controller_wheel" in controller:
                        controller_wheelZ_div = soup.new_tag('div', style=f"""
                        position: absolute !important; 
                        z-index: {layer['posZ']};
                        transform-origin: calc(50% + {layer.get('originXright', layer.get('originX', 0))}px) calc(50% + {layer.get('originYright', layer.get('originY', 0))}px);
                        transform: rotateY(0deg) rotateX(0deg);
                    """)
                        controller_wheelZ_div['class'] = ["controller_wheelZ"]
                        controller_wheelZ_div['player'] = layer.get("player", 1) - 1
                        controller_wheelZ_div['deg'] = layer.get('degRight', layer.get('deg', -90))
                        controller_wheelZ_div['invertAxis'] = layer.get('invertAxis', 0)
                        controller_wheelZ_div['deadzone'] = layer.get("deadzone", 0.0550)

                    if "controller_wheel" in controller:
                        controller_wheelWhammy_div = soup.new_tag('div', style=f"""
                            position: absolute !important; 
                            z-index: {layer['posZ']};
                            transform-origin: calc(50% + {layer.get('originXwhammy', 0)}px) calc(50% + {layer.get('originYwhammy', 0)}px);
                            transform: rotateZ(0deg);
                        """)
                        controller_wheelWhammy_div['class'] = ["Whammywheel"]
                        controller_wheelWhammy_div['player'] = layer.get("player", 1) - 1
                        controller_wheelWhammy_div['deg'] = layer.get('degWhammy', 0)
                        controller_wheelWhammy_div['invertAxis'] = layer.get('invertAxis', 0)
                        controller_wheelWhammy_div['deadzone'] = layer.get("deadzone", 0.0550)

                animation_blinking_div = None
                if str(layer.get("blinking", "ignore")) != "ignore":
                    animation_blinking_div = soup.new_tag('div', style="position: absolute !important;")
                    blinking = str(layer.get("blinking", "ignore"))
                    animation_blinking_div['class'] = [
                        blinking + ("" if editing == "not_in_editor" else f"_{editing}")
                    ]

                animation_talking_div = None
                if str(layer.get("talking", "ignore")) != "ignore":
                    animation_talking_div = soup.new_tag('div', style=f"""
                        position: absolute !important;
                        z-index: {layer['posZ']};
                        {"opacity: 0" if layer['talking'] not in ['ignore', 'talking_closed'] else ""};
                    """)
                    talking = str(layer.get("talking", "ignore"))
                    animation_talking_div['class'] = [
                        talking + ("" if editing == "not_in_editor" else f"_{editing}")
                    ]

                if layer['route'].startswith("$url/"):

                    if "/file/" in layer['route']:
                        add = layer['route'].split('/file/')[-1].replace('\\', '/')
                        src = "file:///"
                    else:
                        add = layer['route'].split('/url/')[-1].replace('\\', '/')
                        src = "https://"

                    print(f"{src}{add}")
                    img_tag = soup.new_tag(
                        'iframe',
                        src=f"{src}{add}",
                        style=f"""
                            position: absolute !important;
                            left: calc(50% + {layer['posX']}px);
                            top: calc(50% + {layer['posY']}px);
                            z-index: {layer['posZ']};
                            transform: translate(-50%, -50%) rotate({layer['rotation']}deg);
                            width: {layer['sizeX']}px; 
                            height: {layer['sizeY']}px;
                            {layer['css']}
                        """)
                else:
                    img_tag = soup.new_tag(
                        'img',
                        src=str(os.path.join(self.res_dir, layer['route'])).replace("\\", "/"),
                        style=f"""
                            position: absolute !important;
                            left: calc(50% + {layer['posX']}px);
                            top: calc(50% + {layer['posY']}px);
                            z-index: {layer['posZ']};
                            transform: translate(-50%, -50%) rotate({layer['rotation']}deg);
                            width: {layer['sizeX']}px; 
                            height: {layer['sizeY']}px;
                            {layer['css']}
                        """)
                img_tag["class"] = ["asset", editing]

                elements_in_order = [
                    flipper_div,
                    animation_idle_div,
                    animation_added_div,
                    cursor_div,
                    controller_buttons_div,
                    guitar_buttons_div,
                    controller_wheelY_div,
                    controller_wheelZ_div,
                    controller_wheelX_div,
                    controller_wheelWhammy_div,
                    animation_blinking_div,
                    animation_talking_div,
                    img_tag
                ]

                next_parent = None
                for element in elements_in_order:
                    if element is not None:
                        if next_parent is not None:
                            next_parent.append(element)
                        next_parent = element

                for element in elements_in_order[1:]:
                    if element is not None:
                        div_count += 1

        try:
            div_count = f"{div_count} | {div_count / len(image_list if image_list is not None else []):.2}avrg."
        except ZeroDivisionError:
            div_count = "No Layers"
        image_wrapper.append(flipper_div)

        html_content = str(image_wrapper.prettify())
        return {"bg_color": bg_color, "scale": scale, "html_content": html_content, "div_count": div_count}

    def get_animations(self, file_path, get_all=False):
        with open(file_path, 'r') as file:
            css_text = file.read()

        if get_all:
            animations = re.findall(r'@keyframes\s+([\w-]+)\s*{[^}]*}', css_text)
        else:
            animations = re.findall(r'@keyframes\s+([\w-]+)\s*{[^}]*\/\*\s*Avatar Animation\s*\*\/[^}]*}', css_text)
        # print(animations)
        return animations
