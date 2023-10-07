from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, QTimer
from bs4 import BeautifulSoup
import os
import cssutils


class LayeredImageViewer(QWebEngineView):
    def __init__(self, parent=None):
        super(LayeredImageViewer, self).__init__(parent)
        self.setColor("#b8cdee")
        self.initUI()

    def initUI(self):
        self.updateImages()

    def setColor(self, color):
        with open('styles.css', 'r') as css_file:
            css_content = css_file.read()

        stylesheet = cssutils.CSSParser().parseString(css_content)

        for rule in stylesheet:
            for prop in rule.style:
                if prop.name == 'background-color':
                    prop.value = color

        with open('styles.css', 'wb') as css_file:
            css_file.write(stylesheet.cssText)
        self.reload()

    def reload(self):
        file = "viewer.html"
        file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file)
        self.load(QUrl.fromLocalFile(file))

    def updateImages(self, image_list=None):
        with open('viewer.html', 'r') as html_file:
            html_code = html_file.read()

        soup = BeautifulSoup(html_code, 'html.parser')
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
                img_tag = soup.new_tag('img', src=layer['route'], style=f"""
                        position: absolute;
                        left: calc(50% + {layer['posX']}px);
                        top: calc(50% + {layer['posY']}px);
                        transform: translate(-50%, -50%) scale({scale_factor}) rotate({layer['rotation']}deg);
                        width: {layer['sizeX']}px; 
                        height: {layer['sizeY']}px;
                    """)
                img_tag['class'] = [layer['blinking'], layer['talking']]
                # Append the img tag to the div
                image_div.append(img_tag)

        beautiful_html = soup.prettify()
        with open('viewer.html', 'w') as html_file:
            html_file.write(beautiful_html)

        QTimer.singleShot(10, self.reload)