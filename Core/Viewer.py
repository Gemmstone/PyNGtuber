from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication
import sys

class LayeredImageViewer(QWebEngineView):
    def __init__(self, image_list, color="#b8cdee", parent=None):
        super(LayeredImageViewer, self).__init__(parent)
        self.image_list = image_list
        self.color = color
        self.initUI()

    def initUI(self):
        # Disable right-click context menu and zooming
        # self.page().settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        # self.page().settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

        # Load an HTML file that displays the images in layers immediately
        self.setHtml(self.generate_html())
        # self.setUrl("www.google.com")
        # self.load(QUrl.fromUserInput("https://www.google.com"))

    def setColor(self, color):
        self.color = color
        self.setHtml(self.generate_html())

    def generate_html(self):
        # Generate the HTML content dynamically based on your image_list, JS, and CSS
        html = """
        <html>
        <head>
            <style>
                body {
                    margin: 0;
                    overflow: hidden;
                    background-color: """ + self.color + """; /* Set your background color here */
                }
                /* Define CSS animations here */
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
            </style>
            <script>
                // Define JavaScript animations and interactions here
                // Example: Animate an element with id "image1" using the "fadeIn" animation
                document.addEventListener("DOMContentLoaded", function () {
            """

        for layer in sorted(self.image_list, key=lambda x: x['posZ']):
            animation_string = ', '.join(layer['animation'])  # Join the animation names into a single string
            html += f"""
            var image{layer['posZ']} = document.getElementById("image{layer['posZ']}");
            image{layer['posZ']}.style.animation = "{animation_string} 2s ease-in-out";
            """

        html += """
            });
            </script>
        </head>
        <body>
        """

        for layer in sorted(self.image_list, key=lambda x: x['posZ']):
            html += f"""
            <img src="{layer['route']}" style="
                position: absolute;
                left: calc(50% + {layer['posX']}px);
                top: calc(50% + {layer['posY']}px);
                transform: translate(-50%, -50%);
                z-index: {layer['posZ']};
            " id="image{layer['posZ']}">
            """

        html += """
        </body>
        </html>
        """
        return html


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gallery = LayeredImageViewer()
    gallery.show()
    sys.exit(app.exec())