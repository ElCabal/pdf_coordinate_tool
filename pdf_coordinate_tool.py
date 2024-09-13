import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QListWidget, QScrollArea
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QCursor
from PyQt5.QtCore import Qt, QRect
import fitz  # PyMuPDF

class PDFCoordinateTool(QMainWindow): 
    def __init__(self):
        super().__init__()
        self.initUI()
        self.pdf_document = None
        self.current_page = 0
        self.coordinates = []
        self.hover_position = None  # Guardar posición del cursor para el hover
        self.scale_factor = 2  # Ajuste el factor de escala según sea necesario

    def initUI(self):
        self.setWindowTitle('PDF Coordinate Tool')
        self.setGeometry(100, 100, 1000, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Scroll area para PDF display
        self.scroll_area = QScrollArea()
        layout.addWidget(self.scroll_area)

        # PDF label para mostrar el PDF dentro del scroll area
        self.pdf_label = QLabel()
        self.pdf_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.pdf_label)
        self.scroll_area.setWidgetResizable(True)

        # Cambiar el cursor por un cuadrado (estilo hover)
        self.pdf_label.setCursor(QCursor(Qt.CrossCursor))

        # Right side - Controls and coordinate list
        right_layout = QVBoxLayout()

        self.load_button = QPushButton('Cargar PDF')
        self.load_button.clicked.connect(self.load_pdf)
        right_layout.addWidget(self.load_button)

        self.prev_button = QPushButton('Página Anterior')
        self.prev_button.clicked.connect(self.prev_page)
        right_layout.addWidget(self.prev_button)

        self.next_button = QPushButton('Página Siguiente')
        self.next_button.clicked.connect(self.next_page)
        right_layout.addWidget(self.next_button)

        self.coordinate_list = QListWidget()
        right_layout.addWidget(self.coordinate_list)

        self.clear_button = QPushButton('Limpiar Lista')
        self.clear_button.clicked.connect(self.clear_coordinates)
        right_layout.addWidget(self.clear_button)

        self.save_button = QPushButton('Guardar Coordenadas')
        self.save_button.clicked.connect(self.save_coordinates)
        right_layout.addWidget(self.save_button)

        layout.addLayout(right_layout)

    def load_pdf(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF", "", "PDF Files (*.pdf)")
        if file_name:
            self.pdf_document = fitz.open(file_name)
            self.current_page = 0
            self.coordinates.clear()  # Limpiar las coordenadas al cargar un nuevo PDF
            self.coordinate_list.clear()  # Limpiar la lista de coordenadas visibles
            self.display_page()

    def display_page(self):
        if self.pdf_document:
            page = self.pdf_document[self.current_page]
            pix = page.get_pixmap(matrix=fitz.Matrix(self.scale_factor, self.scale_factor))
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

            # Crear el QPixmap desde el QImage
            pixmap = QPixmap.fromImage(img)

            # Crear un QPainter para dibujar las marcas
            painter = QPainter(pixmap)
            pen = QPen(QColor(255, 0, 0), 3)  # Color rojo para el rectángulo
            painter.setPen(pen)

            # Dibujar las marcas en las coordenadas almacenadas
            for coord in self.coordinates:
                if coord[0] == self.current_page + 1:
                    pdf_x, pdf_y = coord[1], coord[2]
                    # Escalar las coordenadas a la vista del PDF
                    x = (pdf_x / page.rect.width) * pix.width
                    y = (pdf_y / page.rect.height) * pix.height
                    painter.drawRect(int(x) - 10, int(y) - 10, 20, 20)  # Dibujar un rectángulo

            # Dibujar el rectángulo del hover si está definido
            if self.hover_position:
                hover_x, hover_y = self.hover_position
                painter.drawRect(hover_x - 10, hover_y - 10, 20, 20)  # Cuadrado de hover

            painter.end()

            self.pdf_label.setPixmap(pixmap)
            self.pdf_label.mousePressEvent = self.get_click_coordinates
            self.pdf_label.mouseMoveEvent = self.show_hover  # Conectar evento de mover el ratón

    def prev_page(self):
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            self.hover_position = None  # Limpiar la posición del hover al cambiar de página
            self.display_page()

    def next_page(self):
        if self.pdf_document and self.current_page < len(self.pdf_document) - 1:
            self.current_page += 1
            self.hover_position = None  # Limpiar la posición del hover al cambiar de página
            self.display_page()

    def get_click_coordinates(self, event):
        if self.pdf_document:
            x = event.pos().x()
            y = event.pos().y()
            page_width = self.pdf_label.pixmap().width()
            page_height = self.pdf_label.pixmap().height()
            pdf_width = self.pdf_document[self.current_page].rect.width
            pdf_height = self.pdf_document[self.current_page].rect.height

            # Ajustar las coordenadas a la escala del PDF
            pdf_x = (x / page_width) * pdf_width
            pdf_y = (y / page_height) * pdf_height

            coordinate = (self.current_page + 1, round(pdf_x, 2), round(pdf_y, 2))
            self.coordinates.append(coordinate)
            self.coordinate_list.addItem(f"Página {coordinate[0]}: ({coordinate[1]}, {coordinate[2]})")

            # Redibujar la página con la nueva marca
            self.display_page()

    def show_hover(self, event):
        """ Mostrar el rectángulo de hover donde el mouse esté posicionado """
        if self.pdf_document:
            x = event.pos().x()
            y = event.pos().y()

            # Almacenar la posición actual del hover
            self.hover_position = (x, y)

            # Redibujar la página para mostrar el rectángulo de hover
            self.display_page()

    def clear_coordinates(self):
        self.coordinates.clear()  # Limpiar la lista de coordenadas
        self.coordinate_list.clear()  # Limpiar la vista de la lista
        self.hover_position = None  # Limpiar el hover también
        self.display_page()  # Redibujar la página sin marcas

    def save_coordinates(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Guardar Coordenadas", "", "Text Files (*.txt)")
        if file_name:
            with open(file_name, 'w') as f:
                for coord in self.coordinates:
                    f.write(f"Página {coord[0]}: ({coord[1]}, {coord[2]})\n")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PDFCoordinateTool()
    ex.show()
    sys.exit(app.exec_())

