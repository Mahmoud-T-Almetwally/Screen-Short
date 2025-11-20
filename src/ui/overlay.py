import io
import math
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QRect, QPoint, QBuffer
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QCursor, QImage

from .toolbar import EditingToolbar
from PIL import Image, ImageDraw

from datetime import datetime
from pathlib import Path

class ScreenshotOverlay(QWidget):
    def __init__(self, fullscreen_capture_data, conf):
        super().__init__()
        self.conf = conf

        self.background_pixmap = QPixmap()
        self.background_pixmap.loadFromData(fullscreen_capture_data)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        self.selection_rect = None
        self.shape_edits = []
        self.current_drawing_shape = None
        
        self.current_action = 'selecting' 
        self.drag_start_position = None

        self.toolbar = EditingToolbar(self.conf, self)
        self.toolbar.hide()

    def set_active_tool(self, tool_name):
        if self.current_action == tool_name:
            self.current_action = None
            self.toolbar.uncheck_all_except(None)
        else:
            self.current_action = tool_name
            self.toolbar.uncheck_all_except(tool_name)
        self.update_cursor()

    def update_toolbar_position(self):
        if not self.selection_rect or not self.selection_rect.isValid():
            return
        
        pos_x = self.selection_rect.left()
        pos_y = self.selection_rect.bottom() + 10
        
        if pos_y + self.toolbar.height() > self.height():
            pos_y = self.selection_rect.top() - self.toolbar.height() - 10

        self.toolbar.move(pos_x, pos_y)
        if not self.toolbar.isVisible():
            self.toolbar.show()

    def get_handle_at_pos(self, pos):
        if not self.selection_rect:
            return None
        
        handle_margin = 5
        if QRect(self.selection_rect.bottomRight() - QPoint(handle_margin, handle_margin), self.selection_rect.bottomRight() + QPoint(handle_margin, handle_margin)).contains(pos):
            return 'resize_br'
        if QRect(self.selection_rect.topLeft() - QPoint(handle_margin, handle_margin), self.selection_rect.topLeft() + QPoint(handle_margin, handle_margin)).contains(pos):
            return 'resize_tl'
        if self.selection_rect.contains(pos):
            return 'move'
        return None

    def update_cursor(self):
        if self.current_action and 'draw' in self.current_action:
            if self.selection_rect and self.selection_rect.contains(self.mapFromGlobal(QCursor.pos())):
                 self.setCursor(Qt.CursorShape.CrossCursor)
            else:
                 self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        hover_handle = self.get_handle_at_pos(self.mapFromGlobal(QCursor.pos()))
        if hover_handle == 'resize_br' or hover_handle == 'resize_tl':
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif hover_handle == 'move':
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)

    def _clamp_point_to_selection(self, point):
        if not self.selection_rect:
            return point

        clamped_x = max(self.selection_rect.left(), min(point.x(), self.selection_rect.right()))
        clamped_y = max(self.selection_rect.top(), min(point.y(), self.selection_rect.bottom()))
        return QPoint(clamped_x, clamped_y)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.selection_rect and self.selection_rect.isValid():
                self.capture_and_exit()
        elif event.key() == Qt.Key.Key_Escape:
            QApplication.quit()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        self.drag_start_position = event.pos()

        if self.current_action and 'draw' in self.current_action:
            if not self.selection_rect or not self.selection_rect.contains(event.pos()):
                self.drag_start_position = None
                return

            shape_type = self.current_action.split('_')[1]
            self.current_drawing_shape = {
                'type': shape_type,
                'start_pos': event.pos(),
                'end_pos': event.pos()
            }
        else:
            handle = self.get_handle_at_pos(event.pos())
            if handle:
                self.current_action = handle
            else:
                self.current_action = 'selecting'
                self.selection_rect = QRect(self.drag_start_position, self.drag_start_position)
                self.toolbar.hide()
        
        self.update()


    def mouseMoveEvent(self, event):
        if not self.drag_start_position:
            self.update_cursor()
            return
        
        delta = event.pos() - self.drag_start_position

        if self.current_drawing_shape:
            clamped_pos = self._clamp_point_to_selection(event.pos())
            self.current_drawing_shape['end_pos'] = clamped_pos
        elif self.current_action == 'selecting':
            self.selection_rect = QRect(self.drag_start_position, event.pos()).normalized()
        elif self.current_action == 'move':
            self.selection_rect.translate(delta)
            self.drag_start_position = event.pos()
        elif self.current_action == 'resize_br':
            self.selection_rect.setBottomRight(self.selection_rect.bottomRight() + delta)
            self.drag_start_position = event.pos()
        elif self.current_action == 'resize_tl':
            self.selection_rect.setTopLeft(self.selection_rect.topLeft() + delta)
            self.drag_start_position = event.pos()
            
        if self.selection_rect and self.selection_rect.isValid():
             self.update_toolbar_position()

        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        if self.current_drawing_shape:
            self.shape_edits.append(self.current_drawing_shape)
            self.current_drawing_shape = None
            self.toolbar.uncheck_all_except(None)
        elif self.current_action == 'selecting':
             if not self.selection_rect or not self.selection_rect.isValid():
                 self.selection_rect = None
        
        self.current_action = None
        self.drag_start_position = None
        self.update_cursor()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.drawPixmap(self.rect(), self.background_pixmap)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        if self.selection_rect and self.selection_rect.isValid():
            painter.drawPixmap(self.selection_rect, self.background_pixmap, self.selection_rect)
            
            border_color = QColor(self.conf['appearance']['selection_border_color'])
            border_width = self.conf['appearance']['selection_border_width']
            painter.setPen(QPen(border_color, border_width))
            painter.drawRect(self.selection_rect)

        shape_pen = QPen(
            QColor(self.conf['editing']['shape_border_color']), 
            self.conf['editing']['shape_border_width']
        )
        painter.setPen(shape_pen)

        for shape in self.shape_edits:
            self.draw_shape(painter, shape)
        if self.current_drawing_shape:
            self.draw_shape(painter, self.current_drawing_shape)

    def draw_shape(self, painter, shape_data):
        start = shape_data['start_pos']
        end = shape_data['end_pos']
        rect = QRect(start, end).normalized()
        
        if shape_data['type'] == 'rect':
            painter.drawRect(rect)
        elif shape_data['type'] == 'circle':
            painter.drawEllipse(rect)
        elif shape_data['type'] == 'arrow':
            painter.drawLine(start, end)
            angle = math.atan2(start.y() - end.y(), start.x() - end.x())
            arrow_head_length = 15
            arrow_head_angle = math.pi / 6
            p1 = QPoint(
                end.x() + arrow_head_length * math.cos(angle + arrow_head_angle),
                end.y() + arrow_head_length * math.sin(angle + arrow_head_angle)
            )
            p2 = QPoint(
                end.x() + arrow_head_length * math.cos(angle - arrow_head_angle),
                end.y() + arrow_head_length * math.sin(angle - arrow_head_angle)
            )
            painter.drawLine(end, p1)
            painter.drawLine(end, p2)

    def capture_and_exit(self):
        self.hide()
        self.toolbar.close()
        
        try:
            cropped_pixmap = self.background_pixmap.copy(self.selection_rect.normalized())

            buffer = QBuffer()
            buffer.open(QBuffer.OpenModeFlag.ReadWrite)
            cropped_pixmap.save(buffer, "PNG")
            image_data = buffer.data()
            
            image = Image.open(io.BytesIO(image_data))
            draw = ImageDraw.Draw(image)

            crop_x, crop_y = self.selection_rect.x(), self.selection_rect.y()
            color = self.conf['editing']['shape_border_color']
            width = self.conf['editing']['shape_border_width']

            for shape in self.shape_edits:
                start_local = (shape['start_pos'].x() - crop_x, shape['start_pos'].y() - crop_y)
                end_local = (shape['end_pos'].x() - crop_x, shape['end_pos'].y() - crop_y)
                
                if shape['type'] == 'rect':
                    draw.rectangle([start_local, end_local], outline=color, width=width)
                elif shape['type'] == 'circle':
                    draw.ellipse([start_local, end_local], outline=color, width=width)
                elif shape['type'] == 'arrow':
                    draw.line([start_local, end_local], fill=color, width=width)
            
            final_image_buffer = io.BytesIO()
            image.save(final_image_buffer, format="PNG")
            final_image_data = final_image_buffer.getvalue()

            if self.conf['behavior'].get('copy_to_clipboard', True):
                q_img = QImage.fromData(final_image_data)
                QApplication.clipboard().setImage(q_img)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            image_name = f"screenshot-{timestamp}.png"

            config_save_dir = self.conf['paths']['save_dir']
            
            save_path_obj = Path(config_save_dir).expanduser()

            if not save_path_obj.is_absolute():
                full_directory = Path.home() / save_path_obj
            else:
                full_directory = save_path_obj

            full_directory.mkdir(parents=True, exist_ok=True)

            save_path = full_directory / image_name
            with open(save_path, "wb") as f:
                f.write(final_image_data)
            
            print(f"Screenshot saved to: {save_path}")

        except Exception as e:
            print(f"Error saving screenshot: {e}")
        
        QApplication.quit()