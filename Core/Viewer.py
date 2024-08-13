from PyQt6.QtCore import QUrl, pyqtSignal, QThreadPool, pyqtSlot, QRunnable, QObject
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from bs4 import BeautifulSoup
import traceback
import asyncio
import copy
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
    failed_to_load_images = pyqtSignal()

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        if "update_images is not defined" in message or "addImagesToCanvas is not defined" in message:
            self.failed_to_load_images.emit()
            print("failed to load images, retrying...")
        else:
            print(
                f"\njavaScriptConsoleMessage:\n"
                f"\tlevel:\t\t'{level}'\n"
                f"\tmessage:\t'{message}'\n"
                f"\tlineNumber:\t'{lineNumber}'\n"
                f"\tsourceID:\t'{sourceID}'\n"
            )


class LayeredImageViewer(QWebEngineView):
    loadFinishedSignal = pyqtSignal(bool)
    div_count_signal = pyqtSignal(str)
    failed_to_load_images = pyqtSignal()

    def __init__(self, exe_dir, enabled=True, hw_acceleration=False, parent=None):
        super(LayeredImageViewer, self).__init__(parent)
        self.res_dir = exe_dir
        self.obs_websocket = None
        self.obs_websocket_remote = None
        self.enabled = enabled
        page = WebEnginePage(self)
        page.failed_to_load_images.connect(self.failed_to_load_images.emit)
        self.setPage(page)
        self.html_code = ""
        self.setColor("#b8cdee")
        self.force_local_last = False
        self.is_loaded = False
        self.loadFinished.connect(self.on_load_finished)

        self.threadpool = QThreadPool()

        self.oldIds = []

        self.update_settings(hw_acceleration=hw_acceleration)

        self.file = os.path.join(self.res_dir, 'Viewer', 'viewer.html')
        self.file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.file)

        self.reload()

    def runJavaScript(self, js_code, force_local=None):
        if js_code:
            if self.obs_websocket is not None:
                try:
                    asyncio.run(self.obs_websocket.send_js_command(js_code))
                except RuntimeError as err:
                    print(err)
            if self.obs_websocket_remote is not None:
                try:
                    asyncio.run(self.obs_websocket.send_js_command(js_code))
                except RuntimeError as err:
                    print(err)
            if self.enabled or force_local is True:
                self.page().runJavaScript(js_code)
            elif force_local != self.force_local_last and force_local is not None:
                self.page().runJavaScript(f'document.body.style.zoom = "100%";')
                self.page().runJavaScript(f'addImagesToCanvas({str([])}, null)')
            if force_local is not None:
                self.force_local_last = force_local

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

    def updateImages_(self, image_list=None, bg_color="#b8cdee", scale=100, edited=None, performance=False):
        images = copy.deepcopy(image_list)

        if images is not None:
            for layer in sorted(images, key=lambda x: x['posZ']):
                path_webp = os.path.basename(layer['route'])
                path_webp, uncompressed_extension = os.path.splitext(path_webp)
                path_webp = os.path.join(os.path.dirname(layer['route']), "webp", path_webp + ".webp")
                path_webp = str(os.path.join(self.res_dir, path_webp)).replace("\\", "/")
                if not os.path.isfile(path_webp):
                    path_webp = str(os.path.join(self.res_dir, layer["route"]))

                layer["routeOg"] = copy.deepcopy(layer["route"])
                layer["route"] = path_webp
                layer["routeRemote"] = os.path.join(
                    "..", "Assets", copy.deepcopy(path_webp).split(f"Assets{os.path.sep}")[-1]
                )

            self.runJavaScript(f'document.body.style.zoom = "{scale}%";')
            self.runJavaScript(f'addImagesToCanvas({str(images)}, {edited})', force_local=edited is not None)
            self.div_count_signal.emit(f"{len(images)}")
            self.page().runJavaScript(f'document.body.style.backgroundColor = "{bg_color}";')

    def updateImages(
            self, image_list=None, bg_color="#b8cdee", scale=100, edited=None, performance=False,
            filters=None, shadow=None
    ):
        worker = Worker(self.update_thread, image_list, bg_color, scale, edited, performance, filters, shadow)
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)

    def print_output(self, result):
        self.page().runJavaScript(f'document.body.style.backgroundColor = "{result["bg_color"]}";')
        self.runJavaScript(f'document.body.style.zoom = "{result["scale"]}%";')
        self.runJavaScript(f'update_images(`{result["html_content"]}`);')
        self.div_count_signal.emit(result["div_count"])

    def thread_complete(self):
        self.images_loaded = True

    def update_thread(
            self, image_list=None, bg_color="#b8cdee", scale=100, edited=None, performance=False,
            filters=None, shadow=None
    ):
        soup = BeautifulSoup('<div id="image-wrapper"></div>', 'html.parser')
        image_wrapper = soup.find(id="image-wrapper")
        if performance:
            image_wrapper['class'] = ["flipper", "idle_animation"]

        flipper_div = soup.new_tag("div", style=f"""
            position: absolute !important;
            animation-direction: normal;
            transition = 'all 0.5s ease-in-out';
        """)
        flipper_div['class'] = ["flipper"]

        general_shadow = None
        general_filters = None

        if filters is not None:
            general_filters = soup.new_tag(
                "div",
                style=f"filter: "
                      f"blur({filters.get('blur', 0.0)}px) "
                      f"brightness({filters.get('brightness', 100.0)}%) "
                      f"contrast({filters.get('contrast', 100.0)}%) "
                      f"grayscale({filters.get('grayscale', 0.0)}%) "
                      f"hue-rotate({filters.get('hue', 0.0)}deg) "
                      f"invert({filters.get('invert', 0.0)}%) "
                      f"opacity({filters.get('opacity', 100.0)}%) "
                      f"saturate({filters.get('saturate', 100.0)}%) "
                      f"sepia({filters.get('sepia', 0.0)}%);"
            )

        if shadow is not None:
            color = [int(i) for i in shadow.get('shadowColor', '0, 0, 0, 255').replace("(", "").replace(")", "").split(", ")]
            color = f"({color[0]}, {color[1]}, {color[2]}, {color[3] / 255})"
            general_shadow = soup.new_tag(
                "div",
                style=f"filter: drop-shadow("
                      f"{shadow.get('shadowX', 5)}px "
                      f"{shadow.get('shadowY', -5) * -1}px "
                      f"{shadow.get('shadowBlur', 0)}px "
                      f"rgba{color if '#' not in color else '(0, 0, 0, 255)'});"
            )

        div_count = 0
        if image_list is not None:
            for layer in sorted(image_list, key=lambda x: x['posZ']):
                animation_idle_div = None
                animation_added_div = None
                cursor_div = None
                controller_buttons_div = None
                guitar_buttons_div = None
                controller_wheelY_div = None
                controller_wheelZ_div = None
                controller_wheelX_div = None
                controller_wheelWhammy_div = None
                animation_blinking_div = None
                animation_talking_div = None
                shadow_div = None
                filters_div = None
                editing = "not_in_editor"

                if edited is not None:
                    if edited["type"] == "general":
                        editing = "being_edited" \
                            if f'assets/{edited["collection"].lower()}/{edited["value"].lower()}/' in layer[
                            'route'].replace("\\", "/").lower() \
                            else "not_being_edited"
                    else:
                        editing = "being_edited" if layer['route'] == edited["value"] else "not_being_edited"

                if not performance:
                    if layer.get("animation_idle", True):
                        animation_idle_div = soup.new_tag('div', style=f"""
                            position: absolute !important;
                            animation-direction: normal;
                            z-index: {layer['posZ']}0;
                        """)
                        animation_idle_div['class'] = ["idle_animation"]

                    if (layer.get("animation_name_idle", "None") != "None" or
                            layer.get("animation_name_talking", "None") != None):
                        animation_added_div = soup.new_tag('div', style=f"""
                            position: absolute !important; 
                            animation-direction: normal;
                            z-index: {layer['posZ']}0;
                        """)
                        animation_added_div['class'] = ["added_animation"]
                        animation_added_div['animation_name_idle'] = layer.get("animation_name_idle", "None")
                        animation_added_div['animation_name_talking'] = layer.get("animation_name_talking", "None")
                        animation_added_div['animation_name_screaming'] = layer.get(
                            "animation_name_screaming", animation_added_div['animation_name_talking']
                        )

                        animation_added_div['animation_speed_idle'] = layer.get("animation_speed_idle", 6)
                        animation_added_div['animation_speed_talking'] = layer.get("animation_speed_talking", 0.5)
                        animation_added_div['animation_speed_screaming'] = layer.get(
                            "animation_speed_screaming", animation_added_div['animation_speed_talking']
                        )

                        animation_added_div['animation_direction_idle'] = layer.get(
                            'animation_direction_idle', "normal"
                        )
                        animation_added_div['animation_direction_talking'] = layer.get(
                            'animation_direction_talking', "normal"
                        )
                        animation_added_div['animation_direction_screaming'] = layer.get(
                            'animation_direction_screaming', animation_added_div['animation_direction_talking']
                        )

                        animation_added_div['animation_iteration_idle'] = layer.get("animation_iteration_idle", 0)
                        animation_added_div['animation_iteration_talking'] = layer.get("animation_iteration_talking", 0)
                        animation_added_div['animation_iteration_screaming'] = layer.get(
                            "animation_iteration_screaming", animation_added_div['animation_iteration_talking']
                        )

                        animation_added_div['animation_pacing_idle'] = layer.get('animation_pacing_idle', "ease-in-out")
                        animation_added_div['animation_pacing_talking'] = layer.get('animation_pacing_talking',
                                                                                    "ease-in-out")
                        animation_added_div['animation_pacing_screaming'] = layer.get(
                            'animation_pacing_screaming', animation_added_div['animation_pacing_talking']
                        )

                    if layer.get("cursor", False):
                        cursor_div = soup.new_tag('div', style=f"""
                            position: absolute !important; 
                            z-index: {layer['posZ']}0;
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

                        cursor_div['forced_mouse_tracking'] = layer.get("forced_mouse_tracking", 0)

                    controller = layer.get('controller', ["ignore"])
                    if controller != ["ignore"]:
                        if "controller_buttons" in controller:
                            controller_buttons_div = soup.new_tag('div', style=f"""
                                position: absolute !important; 
                                z-index: {layer['posZ']}0;
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
                                z-index: {layer['posZ']}0;
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
                                z-index: {layer['posZ']}0;
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
                                z-index: {layer['posZ']}0;
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
                                z-index: {layer['posZ']}0;
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
                            z-index: {layer['posZ']}0;
                            transform-origin: calc(50% + {layer.get('originXwhammy', 0)}px) calc(50% + {layer.get('originYwhammy', 0)}px);
                            transform: rotateZ(0deg);
                        """)
                            controller_wheelWhammy_div['class'] = ["Whammywheel"]
                            controller_wheelWhammy_div['player'] = layer.get("player", 1) - 1
                            controller_wheelWhammy_div['deg'] = layer.get('degWhammy', 0)
                            controller_wheelWhammy_div['invertAxis'] = layer.get('invertAxis', 0)
                            controller_wheelWhammy_div['deadzone'] = layer.get("deadzone", 0.0550)

                if str(layer.get("blinking", ["ignore"])) != "ignore":
                    animation_blinking_div = soup.new_tag(
                        'div', style=f"position: absolute !important; z-index: {layer['posZ']}0;"
                    )
                    blinking = str(layer.get("blinking", "ignore"))
                    animation_blinking_div["class"] = ["editing_div"]
                    animation_blinking_div["editing"] = blinking + ("" if editing == "not_in_editor" else f"_{editing}")
                    animation_blinking_div["default"] = blinking

                talking = layer.get("talking", ["ignore"])
                if type(talking) == str:
                    talking = [talking]
                if talking != ["ignore"]:
                    animation_talking_div = soup.new_tag('div', style=f"""
                        position: absolute !important;
                        z-index: {layer['posZ']}0;
                        {"opacity: 0" if 'talking_closed' not in talking else ""};
                    """)

                    animation_talking_div['class'] = ["editing_div"]
                    animation_talking_div["editing"] = "talking" + ("" if editing == "not_in_editor" else f"_{editing}")
                    animation_talking_div["default"] = "talking"

                    animation_talking_div["talking"] = " ".join(talking)

                editing_div = soup.new_tag("div")
                editing_div["class"] = ["editing_div"]
                editing_div["editing"] = editing
                editing_div["default"] = "editing_div_nope"

                if layer.get("filters", False):
                    filters_div = soup.new_tag(
                        "div",
                        style=f"filter: "
                              f"blur({layer.get('blur', 0.0)}px) "
                              f"brightness({layer.get('brightness', 100.0)}%) "
                              f"contrast({layer.get('contrast', 100.0)}%) "
                              f"grayscale({layer.get('grayscale', 0.0)}%) "
                              f"hue-rotate({layer.get('hue', 0.0)}deg) "
                              f"invert({layer.get('invert', 0.0)}%) "
                              f"opacity({layer.get('opacity', 100.0)}%) "
                              f"saturate({layer.get('saturate', 100.0)}%) "
                              f"sepia({layer.get('sepia', 0.0)}%);"
                    )

                if layer.get("shadow", False):
                    color = [int(i) for i in layer.get('shadowColor', '0, 0, 0, 255').replace("(", "").replace(")", "").split(", ")]
                    color = f"({color[0]}, {color[1]}, {color[2]}, {color[3] / 255})"
                    shadow_div = soup.new_tag(
                        "div",
                        style=f"filter: drop-shadow("
                              f"{layer.get('shadowX', 5)}px "
                              f"{layer.get('shadowY', -5) * -1}px "
                              f"{layer.get('shadowBlur', 0)}px "
                              f"rgba{color if '#' not in color else '(0, 0, 0, 255)'});"
                    )

                img_tag = soup.new_tag(
                    'img',
                    src=f"{layer['route']}",
                    style=f"""
                        position: absolute !important;
                        left: calc(50% + {layer['posX']}px);
                        top: calc(50% + {layer['posY']}px);
                        z-index: {layer['posZ']}0;
                        transform: translate(-50%, -50%) rotate({layer['rotation']}deg);
                        width: {layer['sizeX']}px; 
                        height: {layer['sizeY']}px;
                        {layer['css']}
                    """
                )

                img_tag["class"] = ["asset"]
                img_tag["sizeX"] = layer['sizeX']
                img_tag["sizeY"] = layer['sizeY']
                img_tag["posX"] = layer['posX']
                img_tag["posY"] = layer['posY']
                img_tag["rotation"] = layer['rotation']

                if not performance:
                    img_tag["idle_position_pacing"] = layer.get('idle_position_pacing', "ease-in-out")
                    img_tag["idle_position_speed"] = layer.get('idle_position_speed', 0.2)

                    img_tag["sizeX_talking"] = layer.get('sizeX_talking', img_tag["sizeX"])
                    img_tag["sizeY_talking"] = layer.get('sizeY_talking', img_tag["sizeY"])
                    img_tag["posX_talking"] = layer.get('posX_talking', img_tag["posX"])
                    img_tag["posY_talking"] = layer.get('posY_talking', img_tag["posY"])
                    img_tag["rotation_talking"] = layer.get('rotation_talking', img_tag["rotation"])

                    img_tag["talking_position_pacing"] = layer.get('talking_position_pacing',
                                                                   img_tag["idle_position_pacing"])
                    img_tag["talking_position_speed"] = layer.get('talking_position_speed',
                                                                  img_tag["idle_position_speed"])

                    img_tag["sizeX_screaming"] = layer.get('sizeX_screaming', img_tag["sizeX_talking"])
                    img_tag["sizeY_screaming"] = layer.get('sizeY_screaming', img_tag["sizeY_talking"])
                    img_tag["posX_screaming"] = layer.get('posX_screaming', img_tag["posX_talking"])
                    img_tag["posY_screaming"] = layer.get('posY_screaming', img_tag["posY_talking"])
                    img_tag["rotation_screaming"] = layer.get('rotation_screaming', img_tag["rotation_talking"])

                    img_tag["screaming_position_pacing"] = layer.get('screaming_position_pacing',
                                                                     img_tag["talking_position_pacing"])
                    img_tag["screaming_position_speed"] = layer.get('screaming_position_speed',
                                                                    img_tag["talking_position_speed"])
                elements_in_order = [
                    flipper_div,
                    general_filters,
                    general_shadow,
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
                    editing_div,
                    filters_div,
                    shadow_div,
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
            div_count = f"{len(image_list if image_list is not None else [])} | {div_count} divs | {div_count / len(image_list if image_list is not None else []):.2}avrg. divs"
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


