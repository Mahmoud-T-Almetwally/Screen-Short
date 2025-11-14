from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

class EditingToolbar(QWidget):
    def __init__(self, conf, parent=None):
        super().__init__(parent)
        self.conf = conf['editing']
        self.parent_widget = parent

        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        if self.conf.get('shape_rect', False):
            self.rect_button = QPushButton("Rectangle")
            self.rect_button.setCheckable(True) 
            self.rect_button.clicked.connect(lambda: self.parent_widget.set_active_tool('draw_rect'))
            layout.addWidget(self.rect_button)
            
        if self.conf.get('shape_arrow', False):
            self.arrow_button = QPushButton("Arrow")
            self.arrow_button.setCheckable(True)
            self.arrow_button.clicked.connect(lambda: self.parent_widget.set_active_tool('draw_arrow'))
            layout.addWidget(self.arrow_button)

        if self.conf.get('shape_circle', False):
            self.circle_button = QPushButton("Circle")
            self.circle_button.setCheckable(True)
            self.circle_button.clicked.connect(lambda: self.parent_widget.set_active_tool('draw_circle'))
            layout.addWidget(self.circle_button)

        layout.addStretch() 
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.parent_widget.capture_and_exit)
        layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.parent_widget.close)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #2E3440;
                color: #ECEFF4;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #4C566A;
                border: 1px solid #5E81AC;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5E81AC;
            }
            QPushButton:checked {
                background-color: #88C0D0;
                color: #2E3440;
            }
        """)

    def uncheck_all_except(self, tool_name):
        """Ensures only one tool button is active at a time."""
        buttons = {
            'draw_rect': getattr(self, 'rect_button', None),
            'draw_arrow': getattr(self, 'arrow_button', None),
            'draw_circle': getattr(self, 'circle_button', None)
        }
        for name, button in buttons.items():
            if button and name != tool_name:
                button.setChecked(False)