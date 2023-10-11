from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, QTimer
from bs4 import BeautifulSoup
import os


class LayeredImageViewer(QWebEngineView):
    def __init__(self, parent=None):
        super(LayeredImageViewer, self).__init__(parent)
        self.setColor("#b8cdee")
        self.initUI()

    def initUI(self):
        self.updateImages()

    def setColor(self, color):
        self.page().runJavaScript(f'document.body.style.backgroundColor = "{color}";')

    def reload(self):
        file = 'Viewer/viewer.html'
        file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file)
        self.load(QUrl.fromLocalFile(file))

    def updateImages(self, image_list=None, bg_color="#b8cdee"):
        with open('Viewer/viewer.html', 'r') as html_file:
            html_code = html_file.read()

        soup = BeautifulSoup(html_code, 'html.parser')
        body_tag = soup.body
        body_tag['style'] = f'background-color: {bg_color};'
        image_div = soup.find('div', id='image-wrapper')
        image_div.clear()

        # Move the runtime_page and soup_runtime here
        self.page().toHtml(lambda html: self.handle_runtime_html(html, soup, image_div, image_list))

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
                img_tag = soup.new_tag('img', src=f"../{layer['route']}", style=f"""
                        position: absolute;
                        left: calc(50% + {layer['posX']}px);
                        top: calc(50% + {layer['posY']}px);
                        transform: translate(-50%, -50%) scale({scale_factor}) rotate({layer['rotation']}deg);
                        width: {layer['sizeX']}px; 
                        height: {layer['sizeY']}px;
                        {"opacity: 0:" if layer['sizeY'] else ""}; 
                        {layer['css']}
                    """)
                img_tag['class'] = [layer['blinking'], layer['talking']]
                # Append the img tag to the div
                image_div.append(img_tag)

        beautiful_html = soup.prettify()
        with open('Viewer/viewer.html', 'w') as html_file:
            html_file.write(beautiful_html)

        QTimer.singleShot(10, self.reload)