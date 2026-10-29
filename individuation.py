from PyQt6.QtCore import QTimer, QPoint, QPropertyAnimation, QEasingCurve, Qt, pyqtProperty, QRectF, QSize, QRect, QRegularExpression, QUrl
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsScale, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QComboBox, QFrame, QListView, QPlainTextEdit, QTextEdit
from PyQt6.QtGui import QPixmap, QPainter, QColor, QMovie, QImageReader, QPalette, QTextDocument, QTextCursor, QTextCharFormat, QFont, QTextBlockFormat, QPainterPath, QDesktopServices, QMouseEvent
from math import ceil
import sys
import os

# 资源路径统一处理：兼容打包后的程序目录结构。
def resource_path(path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, 'ArcanistsHuman', 'component_pic', path).replace('\\','/')

# 资源函数：用于定位任务资源目录中的图片、动画和文本文件。
def resource_showgif(path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, 'ArcanistsHuman', path, 'GIF', 'idle.gif').replace('\\','/')

# 文本资源路径：按项目目录结构返回配置与日志文件路径。
def resource_txt(txt):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, txt)

# 提示浮窗：在锁定状态下弹出提示信息。
class Hint(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.btn_layout = QHBoxLayout()
        self.hint_info = QPushButton('请“解锁”后再切换角色哟~')
        self.hint_info.setDisabled(True)
        self.hint_info.setFixedSize(200, 50)
        self.hint_info.setStyleSheet("""
            QPushButton:disabled {
                background-color: rgba(255, 85, 0, 150);
                color: white;
                border: 1px solid rgba(175, 58, 0, 150);
                border-radius: 6px;
                padding: 4px 10px;

                font-size: 14px
            }
            """)
        self.btn_layout.addWidget(self.hint_info)
        self.setLayout(self.btn_layout)
        self.setFixedSize(300, 80)
        self.resize(self.hint_info.size())

        self.start_pos = QPoint(100, 100)

        self.ani_group = ()
        self.refresh_ani()

    def refresh_ani(self):    
        self.come_ani = QPropertyAnimation(self, b'pos', self)
        self.come_ani.setStartValue(self.start_pos + QPoint(0, 50))
        self.come_ani.setEndValue(self.start_pos)
        self.come_ani.setDuration(200)
        self.come_ani.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.leave_ani = QPropertyAnimation(self, b'pos', self)
        self.leave_ani.setStartValue(self.start_pos)
        self.leave_ani.setEndValue(self.start_pos + QPoint(0, 50))
        self.leave_ani.setDuration(200)
        self.leave_ani.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.come_ani_op = QPropertyAnimation(self, b'windowOpacity', self)
        self.come_ani_op.setStartValue(0.0)
        self.come_ani_op.setEndValue(1.0)
        self.come_ani_op.setDuration(200)
        self.come_ani_op.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.leave_ani_op = QPropertyAnimation(self, b'windowOpacity', self)
        self.leave_ani_op.setStartValue(1.0)
        self.leave_ani_op.setEndValue(0.0)
        self.leave_ani_op.setDuration(200)
        self.leave_ani_op.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.ani_group = (self.come_ani, self.leave_ani, self.come_ani_op, self.leave_ani_op)

# 侧边栏按钮：支持展开/收起状态，并在悬停时更新文字颜色。
class SidebarButton(QPushButton):
    def __init__(self, text = '', parent = None):
        super().__init__(text, parent)
        self._text_color = QColor(255, 255, 255)
        self.set_text_color(self._text_color)
    
        if '=' in self.text():
            self.clicked.connect(lambda checked=False, colume = self: self.colume_unfold(colume))

        self.text_color_animation = QPropertyAnimation(self, b'textColor', self)
        self.text_color_animation.setDuration(220)
        self.text_color_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    @pyqtProperty(QColor)
    def textColor(self):
        return self._text_color

    @textColor.setter
    def textColor(self, color):
        self.set_text_color(color)

    def set_text_color(self, color):
        self._text_color = QColor(color)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.ButtonText, self._text_color)
        self.setPalette(palette)
        self.update()

    def animate_text_color(self, color):
        self.text_color_animation.stop()
        self.text_color_animation.setStartValue(self._text_color)
        self.text_color_animation.setEndValue(color)
        self.text_color_animation.start()

    def colume_unfold(self, colume):
        self.set_expanded('-' not in colume.text())

    def set_expanded(self, expanded):
        if expanded and '=' in self.text():
            self.setText(self.text().replace('=', '-'))
        elif not expanded and '-' in self.text():
            self.setText(self.text().replace('-', '='))

    def enterEvent(self, event):
        self.animate_text_color(QColor(255, 220, 150))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate_text_color(QColor(255, 255, 255))
        super().leaveEvent(event)

# 入口按钮：用于首页的功能分组卡片，带 hover 放大动画。
class Entry_set(QWidget):
    def __init__(self, text = '', parent = None):
        super().__init__(parent)
        self.entry = QPushButton(text, self)
        self.origin = QSize(650, 50)
        self.setFixedSize(self.origin * 1.02)
        self.center = self.rect().center()
        self.center_x = self.center.x()
        self.center_y = self.center.y()
        self.entry.setGeometry(
            self.center_x - self.origin.width() // 2,
            self.center_y - self.origin.height() // 2,
            self.origin.width(),
            self.origin.height(),
            )
        self.entry.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 182, 98, 150);
                border: 2px solid rgba(218, 145, 63, 150);
                border-radius: None;
                font-size: 22px;
                text-align: left;
                padding: 1px 1px 1px 50px;
                font-family: "SongTi";
                font-weight: bold;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self.entry)
        shadow.setBlurRadius(5)
        shadow.setOffset(5, 5)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.entry.setGraphicsEffect(shadow)

        self.geo_ani = QPropertyAnimation(self.entry, b'geometry')
        self.geo_ani.setDuration(180)
        self.geo_ani.setEasingCurve(QEasingCurve.Type.OutCubic)

    def ani_play(self, width, height):
        new_width = self.origin.width() * width
        new_height = self.origin.height() * height
        target = QRect(
            int(self.center_x - new_width // 2),
            int(self.center_y - new_height // 2),
            int(new_width),
            int(new_height),
        )

        self.geo_ani.stop()
        self.geo_ani.setStartValue(self.entry.geometry())
        self.geo_ani.setEndValue(target)
        self.geo_ani.start()

    def enterEvent(self, event):
        self.ani_play(1.02, 1.02)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.ani_play(1.0, 1.0)
        super().leaveEvent(event)

# 角色头像按钮：带 GIF 动画和悬停发光效果。
class HoverButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_size = QSize(160, 160)
        self.gif_label = None
        self.gif_movie = None
        self.gif_size = None

        self.hover_shadow = QGraphicsDropShadowEffect(self)
        self.hover_shadow.setOffset(0, 0)
        self.hover_shadow.setColor(QColor(255, 220, 150, 190))
        self.hover_shadow.setBlurRadius(0)
        self.setGraphicsEffect(self.hover_shadow)

        self.hover_animation = QPropertyAnimation(self.hover_shadow, b"blurRadius", self)
        self.hover_animation.setDuration(180)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.zoom_animation = QPropertyAnimation(self, b"geometry", self)
        self.zoom_animation.setDuration(180)
        self.zoom_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def set_hover_glow(self, blur_radius):
        self.hover_animation.stop()
        self.hover_animation.setStartValue(self.hover_shadow.blurRadius())
        self.hover_animation.setEndValue(blur_radius)
        self.hover_animation.start()

    def set_zoom(self, scale):
        container = self.parentWidget()
        if container is None:
            return
        width = round(self.base_size.width() * scale / 2) * 2
        height = round(self.base_size.height() * scale / 2) * 2
        target = QRect(
            (container.width() - width) // 2,
            (container.height() - height) // 2,
            width,
            height,
        )
        self.zoom_animation.stop()
        self.zoom_animation.setStartValue(self.geometry())
        self.zoom_animation.setEndValue(target)
        self.zoom_animation.start()

    def set_gif(self, gif_path, display_size):
        self.gif_label = QLabel(self)
        self.gif_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gif_label.setStyleSheet("background: transparent;")
        self.gif_movie = QMovie(gif_path, parent=self.gif_label)
        self.gif_size = display_size
        self.gif_movie.frameChanged.connect(self.update_gif_frame)
        self.update_gif_geometry()
        self.gif_movie.start()
        self.gif_movie.setPaused(True)
        self.gif_movie.jumpToFrame(0)
        self.update_gif_frame()
        self.gif_label.raise_()

    def update_gif_geometry(self):
        if self.gif_label is None or self.gif_movie is None or self.gif_size is None:
            return
        scale = min(
            self.width() / self.base_size.width(),
            self.height() / self.base_size.height(),
        )
        width = round(self.gif_size.width() * scale)
        height = round(self.gif_size.height() * scale)
        self.gif_label.setGeometry(
            (self.width() - width) // 2,
            (self.height() - height) // 2,
            width,
            height,
        )
        self.update_gif_frame()

    def update_gif_frame(self, *_):
        if self.gif_label is None or self.gif_movie is None:
            return
        frame = self.gif_movie.currentPixmap()
        if frame.isNull() or self.gif_label.size().isEmpty():
            return
        self.gif_label.setPixmap(frame.scaled(
            self.gif_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))

    def resizeEvent(self, event):
        self.update_gif_geometry()
        super().resizeEvent(event)

    def enterEvent(self, event):
        self.set_hover_glow(18)
        self.set_zoom(1.08)
        if self.gif_movie :
            self.gif_movie.setPaused(False)

            self.update_gif_frame()
    
    def leaveEvent(self, event):
        self.set_hover_glow(0)
        self.set_zoom(1.0)
        if self.gif_movie :
            self.gif_movie.setPaused(True)
            self.gif_movie.jumpToFrame(0)
        super().leaveEvent(event)

class Individuation(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.wholelayout = QHBoxLayout(self)
        
        self.sidebar = QVBoxLayout(self)
        self.sidebar.setContentsMargins(0, 0, 0, 0)

        self.mainlayout = QVBoxLayout(self)
        title_bar = QHBoxLayout()

        title_bar.addStretch()
        
        self.background = QPixmap(resource_path('background.png'))

        exit_button = QPushButton()
        exit_button.setStyleSheet("""
            QPushButton {{
                border-image: url("{exit_btn}") 0 0 0 0 stretch stretch;
                padding: 5px
            }}
        """.format(exit_btn = resource_path('exit_btn.png')))
        exit_button.setFixedSize(36, 36)
        exit_button.clicked.connect(self.close)

        self.back_button = QPushButton()
        self.back_button.setStyleSheet("""
            QPushButton {{
                border-image: url("{back_btn}") 0 0 0 0 stretch stretch;
                padding: 5px
            }}
        """.format(back_btn = resource_path('back_btn.png')))
        self.back_button.setFixedSize(30, 36)
        self.back_button.clicked.connect(lambda: self.page_choose('operate'))
        self.back_button.hide()

        title_bar.addWidget(self.back_button)
        title_bar.addWidget(exit_button)

        self.mainlayout.addLayout(title_bar)

        # 侧栏设置
        self.sidebar.addSpacing(150)
        self.sidebar.setSpacing(0)

        # 锁定状态
        self.lock_event = False
        self.hint = Hint()
        (self.come_ani, self.leave_ani, self.appear_ani, self.disapp_ani) = self.hint.ani_group
        self.empty_timer = QTimer()
        self.empty_timer.setSingleShot(True)
        self.empty_timer.setInterval(3000)

        self.empty_timer.timeout.connect(self.leave_ani.start)
        self.empty_timer.timeout.connect(self.disapp_ani.start)
        self.leave_ani.finished.connect(self.hint.close)

        self.module_show = False
        self.other_show = False

        self.opacity_ani_lst = []

        # 展示页面
        self.page_show = 'character'

        character_colume = SidebarButton('角 色')
        module_colume = SidebarButton('组 件    =')
        clock_colume = SidebarButton('  时 钟')
        disc_colume = SidebarButton('  音 乐')
        other_colume = SidebarButton('其 他    =')
        self.module_colume = module_colume
        self.other_colume = other_colume
        operate_colume = SidebarButton(' 基 础 操 作')
        update_colume = SidebarButton(' 更 新 日 志')
        link_colume = SidebarButton(' 相 关 链 接')
        character_colume.clicked.connect(lambda : self.page_choose('character'))
        clock_colume.clicked.connect(lambda: self.page_choose('clock'))
        disc_colume.clicked.connect(lambda: self.page_choose('music'))
        operate_colume.clicked.connect(lambda: self.page_choose('operate'))
        update_colume.clicked.connect(lambda: self.page_choose('update'))
        link_colume.clicked.connect(lambda: self.page_choose('link'))
        side_columes = [character_colume, module_colume, clock_colume, disc_colume, other_colume, operate_colume, update_colume, link_colume]
        side_blocks = []
        for colume in side_columes:
            block = QWidget()
            mod = QVBoxLayout(block)
            mod.setContentsMargins(0, 0, 0, 0)
            mod.setSpacing(0)
            if colume in [clock_colume, disc_colume, operate_colume, update_colume, link_colume]:
                colume.setFixedSize(160, 30)
                colume.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: transparent;
                    padding: 1 1 1 1px;
                    text-align: left;
                    font-family: "KaiTi";
                    font-size: 22px;
                }
                """)
            else:
                colume.setFixedSize(160, 40)
                colume.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        border: transparent;
                        padding: 1 1 1 1px;
                        text-align: left;
                        font-family: "KaiTi";
                        font-size: 30px;
                    }
                """)
            seperate_line = QLabel('—————————')
            seperate_line.setStyleSheet("""
                QLabel {
                    font-family: "FangTi";
                    font-size: 20px;
                    color: white;
                }
                """)
            mod.addWidget(colume, alignment=Qt.AlignmentFlag.AlignLeft)
            mod.addWidget(seperate_line, alignment=Qt.AlignmentFlag.AlignLeft)
            if colume in [clock_colume, disc_colume, operate_colume, update_colume, link_colume]: 
                block_opacity = QGraphicsOpacityEffect(block)
                block_opacity.setOpacity(0.0)
                block.setGraphicsEffect(block_opacity)
                opacity_ani = QPropertyAnimation(block_opacity, b'opacity', block)
                opacity_ani.setDuration(180)
                opacity_ani.setEasingCurve(QEasingCurve.Type.OutCubic)
                self.opacity_ani_lst.append(opacity_ani)
            side_blocks.append(block)

        character_block = QWidget()
        self.character_group = QVBoxLayout(character_block)
        self.character_group.setContentsMargins(0, 0, 0, 0)
        self.character_group.addWidget(side_blocks[0])
        
        self.module_block = QWidget()
        self.module_group = QVBoxLayout(self.module_block)
        self.module_group.setContentsMargins(0, 0, 0, 0)
        self.module_group.setSpacing(0)
        self.module_group.addWidget(side_blocks[1])
        self.module_group.addWidget(side_blocks[2])
        self.module_group.addWidget(side_blocks[3])

        self.other_block = QWidget()
        self.other_group = QVBoxLayout(self.other_block)
        self.other_group.setContentsMargins(0, 0, 0, 0)
        self.other_group.setSpacing(0)
        self.other_group.addWidget(side_blocks[4])
        self.other_group.addWidget(side_blocks[5])
        self.other_group.addWidget(side_blocks[6])
        self.other_group.addWidget(side_blocks[7])

        self.sidebar.addWidget(character_block)
        self.sidebar.addWidget(self.module_block)
        self.sidebar.addWidget(self.other_block)

        self.sidebar.addStretch()

        self.module_buttons = [
            (self.module_group.indexOf(side_blocks[2]), side_blocks[2]),
            (self.module_group.indexOf(side_blocks[3]), side_blocks[3]),
        ]

        self.other_buttons = [
            (self.other_group.indexOf(side_blocks[5]), side_blocks[5]),
            (self.other_group.indexOf(side_blocks[6]), side_blocks[6]),
            (self.other_group.indexOf(side_blocks[7]), side_blocks[7]),
        ]

        self.opacity_module_ani_lst = self.opacity_ani_lst[0:2]
        self.opacity_other_ani_lst = self.opacity_ani_lst[2:]

        for group, buttons in (
            (self.module_group, self.module_buttons),
            (self.other_group, self.other_buttons),
        ):
            for _, button in buttons:
                group.removeWidget(button)
                button.hide()

        self.Title_selected()
        self.wholelayout.addLayout(self.sidebar)
        self.wholelayout.addLayout(self.mainlayout)
        self.setLayout(self.wholelayout)

        # 统一按键样式        
        self.cha_btns = []
        self.clock_btns = []

        # intro文本拆分
        with open(resource_txt("operate_intro.txt"), "r", encoding="utf-8") as f:
            whole_intro = f.read()
        self.intro_lst = [text.removeprefix('\n') for text in whole_intro.split('§')]

        self.page_dic = {
            'character': self.character_lst(), 
            'clock': self.clock_event(), 
            'music': self.music_event(),
            'operate': self.operate_event_home(), 
            'update': self.update_event(), 
            'link': self.link_event(),
            }
        self.in_page = self.page_dic['character']
        self.mainlayout.addWidget(self.in_page)

        self.setFixedSize(900, 650)
        screen = QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            self.move(available.center() - self.rect().center())

        self.chosen_character = None

        for (index, button), ani in zip(self.module_buttons, self.opacity_module_ani_lst):
            ani.finished.connect(lambda button = button: self.opacity_module_ani_over(button))

        for (index, button), ani in zip(self.other_buttons, self.opacity_other_ani_lst):
            ani.finished.connect(lambda button = button: self.opacity_other_ani_over(button))

        self.module_height_animation = QPropertyAnimation(
            self.module_block, b'maximumHeight', self
        )
        self.module_height_animation.setDuration(180)
        self.module_height_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        module_colume.clicked.connect(self.opacitied_module)
        other_colume.clicked.connect(self.opacitied_other)

        self.drag_start_pos = QPoint()
        self.press_pos = None
        self.pressing = False

        self.top_at_pos = False

    # 窗口顶端判定
    def mousePos(self, event: QMouseEvent):
        mouse_pos = event.position().toPoint()
        top_rect = QRect(0, 0, self.width(), 50)
        self.top_at_pos = top_rect.contains(mouse_pos)
    
    # 窗口拖动
    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if not self.pressing :
                self.mousePos(event)
                self.pressing = True
            if not self.top_at_pos:
                return

            current_pos = event.globalPosition().toPoint()
            if self.press_pos is None:
                return
            self.move(current_pos - self.drag_start_pos)
            event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            self.press_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = QPoint()
            self.press_pos = None
            self.pressing = False

    def opacitied_module(self):
        self.module_show = not self.module_show
        self.other_show = False
        self.module_colume.set_expanded(self.module_show)
        self.other_colume.set_expanded(False)
        self.prepare_module_height_animation()
        self.set_group_expanded(
            self.module_group,
            self.module_buttons,
            self.opacity_module_ani_lst,
            self.module_show,
        )
        self.set_group_expanded(
            self.other_group,
            self.other_buttons,
            self.opacity_other_ani_lst,
            False,
        )
        self.animate_module_height(self.module_show)

    def opacitied_other(self):
        self.other_show = not self.other_show
        self.module_show = False
        self.module_colume.set_expanded(False)
        self.other_colume.set_expanded(self.other_show)
        self.prepare_module_height_animation()
        self.set_group_expanded(
            self.module_group,
            self.module_buttons,
            self.opacity_module_ani_lst,
            False,
        )
        self.set_group_expanded(
            self.other_group,
            self.other_buttons,
            self.opacity_other_ani_lst,
            self.other_show,
        )
        self.animate_module_height(False)

    def prepare_module_height_animation(self):
        self.module_height_animation.stop()
        self.module_block.setMaximumHeight(self.module_block.height())

    def animate_module_height(self, expanded):
        if expanded:
            target_height = self.module_group.sizeHint().height()
        else:
            target_height = self.module_group.itemAt(0).sizeHint().height()

        self.module_height_animation.setStartValue(self.module_block.height())
        self.module_height_animation.setEndValue(target_height)
        self.module_height_animation.start()

    def set_group_expanded(self, group, buttons, animations, expanded):
        end_opacity = 1.0 if expanded else 0.0
        for (index, button), ani in zip(buttons, animations):
            ani.stop()
            ani.setEndValue(end_opacity)
            ani.start()
            if expanded:
                group.insertWidget(index, button)
                button.show()

    def opacity_module_ani_over(self, button):
        if self.module_show:
            return

        self.module_group.removeWidget(button)
        button.hide()

    def opacity_other_ani_over(self, button):
        if self.other_show:
            return

        self.other_group.removeWidget(button)
        button.hide()

    # 主标题
    def Title_selected(self):
        self.title_option = QHBoxLayout()
        title_group = QHBoxLayout()
        title_group.setContentsMargins(0, 0, 0, 0)
        title_group.setSpacing(0)

        self.title_dic = {'character':['|角色', '<br>Characters'], 
                          'clock':['|时钟', '<br>Clock'], 
                          'music':['|音乐', '<br>Music'],
                          'operate':['|基础操作', '<br>Basic Operation'], 
                          'update':['|更新日志', '<br>Update Log'], 
                          'link':['|相关链接', '<br>Related Links'],
                          }
        
        self.title_1 = QLabel(self.title_dic['character'][0])
        self.title_1.setStyleSheet("""
            QLabel {
                font-family: "FangTi";
                font-size: 60px;
                color: white;
            }
        """)
        self.set_shadow(self.title_1)

        self.title_2 = QLabel(self.title_dic['character'][1])
        self.title_2.setStyleSheet("""
            QLabel {
                font-family: "FangTi";
                font-size: 20px;
                color: white;
            }
        """)
        self.set_shadow(self.title_2)

        title_group.addWidget(self.title_1, alignment=Qt.AlignmentFlag.AlignLeft)
        title_group.addWidget(self.title_2, alignment=Qt.AlignmentFlag.AlignLeft)

        self.title_option.addSpacing(40)
        self.title_option.addLayout(title_group)
        self.title_option.addStretch()
        
        self.mainlayout.addLayout(self.title_option)

    # 角色选择
    def character_lst(self):
        characters = ['Coppélia', 'Rubuska', 'Sonetto', 'X']
        characters_page = QWidget()
        characters_page.setContentsMargins(0, 0, 0, 0)
        characters_scroll = QVBoxLayout(characters_page)
        characters_scroll.setSpacing(60)
        for time in range(len(characters)//3 + 1):
            btn_line = QHBoxLayout()
            btn_line.addSpacing(20)
            btn_line.setSpacing(30)
            for cha in range(time*3, (time+1)*3):
                if cha >= len(characters):
                    btn_line.addSpacing(230)
                else:
                    button_cell = QWidget()
                    button_cell.setFixedSize(200, 200)
                    cha_btn = HoverButton(button_cell)
                    role = characters[cha]
                    cha_btn.clicked.connect(lambda checked = False, role = role: self.choose_character(role))
                    cha_btn.setGeometry(20, 20, 160, 160)
                    cha_btn.setStyleSheet("""
                    QPushButton {{
                        border-image: url("{character_btn}") 0 0 0 0 stretch stretch;
                        padding: 5px
                    }}
                    """.format(character_btn = resource_path('character_btn.png')))
                    gif_path = resource_showgif(characters[cha])
                    if os.path.exists(gif_path):
                        source_size = QImageReader(gif_path).size()
                        if source_size.isValid():
                            display_size = source_size.scaled(
                                QSize(270, 270), Qt.AspectRatioMode.KeepAspectRatio
                            )
                        else:
                            display_size = QSize(270, 270)
                        cha_btn.set_gif(gif_path, display_size)
                    self.cha_btns.append(cha_btn)
                    btn_line.addWidget(button_cell)
            characters_scroll.addLayout(btn_line)
        characters_scroll.addSpacing(100)
        return characters_page

    def page_set(self, width, height, color, margin_1, margin_2, shadow=True):
        page = QWidget()
        a, b, c, d = margin_1
        page.setContentsMargins(a, b, c, d)

        layout = QVBoxLayout(page)
        layout.setSpacing(0)

        _widget = QWidget()
        _widget.setFixedSize(width, height)
        _widget.setStyleSheet("""
            QWidget {{
                background-color: {color_};
                border-radius: 16px;
            }}
            """.format(color_ = color))
        x, y, z, h = margin_2
        _widget.setContentsMargins(x, y, z, h)

        if shadow:
            widget_shadow = QGraphicsDropShadowEffect(_widget)
            widget_shadow.setOffset(5, 5)
            widget_shadow.setColor(QColor(50, 50, 50, 190))
            widget_shadow.setBlurRadius(20)
            _widget.setGraphicsEffect(widget_shadow)

        _layout = QVBoxLayout(_widget)
        
        layout.addWidget(_widget)

        return page, _layout

    def clock_event(self):
        color = 'rgba(102, 51, 0, 15)'
        page, clock_layout = self.page_set(672, 490, color, (15, 0, 18, 20), (20, 30, 10, 10))

        box_lst = []
        self.clock_theme = QVBoxLayout()
        theme_line = QLabel('——Theme——————')
        theme_line.setStyleSheet("""
            QLabel {
                background: transparent;
                font-family: "FangTi";
                font-size: 16px;
                color: rgba(100, 100, 100, 130);
            }""")
        theme_set = QHBoxLayout()
        self.clock_theme.addWidget(theme_line)
        self.clock_theme.addLayout(theme_set)

        theme_title = QLabel('主题设置')
        theme_title.setFixedSize(120, 30)
        box_lst.append(theme_title)

        theme_combo = QComboBox()
        theme_combo.setFixedSize(115, 30)
        theme_combo.addItems(["默认白框"])
        theme_combo.currentTextChanged.connect(lambda text: self.theme_change(text))
        box_lst.append(theme_combo)

        theme_set.addSpacing(30)
        theme_set.addWidget(theme_title)
        theme_set.addStretch()
        theme_set.addWidget(
            theme_combo,
            alignment=Qt.AlignmentFlag.AlignLeft
            )

        if theme_combo.currentText() == "默认白框" :
            self.theme_font_widget = QWidget()
            self.theme_font_widget.setContentsMargins(0, 0, 0, 0)
            self.theme_font_widget.setStyleSheet("background-color: rgba(0, 0, 0, 0)")
            self.theme_font_widget.setFixedWidth(634)

            theme_color = QVBoxLayout(self.theme_font_widget)
            
            theme_font = QHBoxLayout()
            theme_subtitle_1 = QLabel('字体颜色')
            theme_subtitle_1.setFixedSize(120, 30)
            box_lst.append(theme_subtitle_1)

            self.theme_combo_1 = QComboBox()
            self.theme_combo_1.setFixedSize(115, 30)
            self.theme_combo_1.addItems(['白色', '黑色', '红色', '黄色', '蓝色', '绿色'])
            box_lst.append(self.theme_combo_1)

            theme_font.addSpacing(21)
            theme_font.addWidget(theme_subtitle_1)
            theme_font.addStretch()
            theme_font.addWidget(
                self.theme_combo_1,
                alignment=Qt.AlignmentFlag.AlignRight
                )

            theme_back = QHBoxLayout()
            theme_subtitle_2 = QLabel('背景颜色')
            theme_subtitle_2.setFixedSize(120, 30)
            box_lst.append(theme_subtitle_2)

            self.theme_combo_2 = QComboBox()
            self.theme_combo_2.setFixedSize(115, 30)
            self.theme_combo_2.addItems(['白色', '黑色', '红色', '黄色', '蓝色', '绿色'])
            box_lst.append(self.theme_combo_2)

            theme_back.addSpacing(21)
            theme_back.addWidget(theme_subtitle_2)
            theme_back.addStretch()
            theme_back.addWidget(
                self.theme_combo_2,
                alignment=Qt.AlignmentFlag.AlignRight
                )
            
            theme_color.addLayout(theme_font)
            theme_color.addLayout(theme_back)
            
            self.clock_theme.addWidget(self.theme_font_widget)
            
            end_line = QLabel('————更多功能正在开发中捏*~(￣▽￣)~*————')
            end_line.setStyleSheet("""
                QLabel {
                    color: rgb(180, 149, 121);
                    background: transparent;
                    }
                """)

        for font in box_lst :
            font.setStyleSheet("""
                QLabel {
                    background: transparent;
                    font-family: "FangTi";
                    font-size: 20px;
                    color: white;
                }
                QComboBox {
                    font-family: "FangTi";
                    font-size: 20px;
                    padding-left: 10px;
                    color: white;
                    background-color: rgba(100, 100, 100, 20)
                }

                QComboBox QAbstractItemView {
                    color: white;
                    background-color: rgb(60, 45, 35);
                    border: none;
                    outline: none;
                    border-radius: 0px;
                }
                QComboBox QAbstractItemView::item {
                    border: none;
                    outline: none;
                    padding-left: 10px;
                }
                QComboBox QAbstractItemView::item:selected {
                    border: none;
                    outline: none;
                    background-color: rgb(153, 76, 40)
                }
            """)
            self.set_shadow(font)

        clock_layout.addLayout(self.clock_theme)
        clock_layout.addWidget(
            end_line,
            alignment=Qt.AlignmentFlag.AlignCenter
        )
        clock_layout.addStretch()

        return page

    def music_event(self):
        color = 'rgba(102, 51, 0, 15)'
        page, music_layout = self.page_set(672, 490, color, (15, 0, 18, 20), (20, 30, 10, 10))
        
        box_lst = []
        self.music_theme = QVBoxLayout()
        theme_line = QLabel('——Theme——————')
        theme_line.setStyleSheet("""
            QLabel {
                background: transparent;
                font-family: "FangTi";
                font-size: 16px;
                color: rgba(100, 100, 100, 130);
            }""")
        theme_set = QHBoxLayout()
        self.music_theme.addWidget(theme_line)
        self.music_theme.addLayout(theme_set)

        theme_title = QLabel('主题设置')
        theme_title.setFixedSize(120, 30)
        box_lst.append(theme_title)

        theme_combo = QComboBox()
        theme_combo.setFixedSize(115, 30)
        theme_combo.addItems(["默认白框"])
        box_lst.append(theme_combo)

        theme_set.addSpacing(30)
        theme_set.addWidget(theme_title)
        theme_set.addStretch()
        theme_set.addWidget(
            theme_combo,
            alignment=Qt.AlignmentFlag.AlignLeft
            )
        
        end_line = QLabel('————更多功能正在开发中捏*~(￣▽￣)~*————')
        end_line.setStyleSheet("""
            QLabel {
                color: rgb(180, 149, 121);
                background: transparent;
                }
            """)

        for font in box_lst :
            font.setStyleSheet("""
                QLabel {
                    background: transparent;
                    font-family: "FangTi";
                    font-size: 20px;
                    color: white;
                }
                QComboBox {
                    font-family: "FangTi";
                    font-size: 20px;
                    padding-left: 10px;
                    color: white;
                    background-color: rgba(100, 100, 100, 20)
                }

                QComboBox QAbstractItemView {
                    color: white;
                    background-color: rgb(60, 45, 35);
                    border: none;
                    outline: none;
                    border-radius: 0px;
                }
                QComboBox QAbstractItemView::item {
                    border: none;
                    outline: none;
                    padding-left: 10px;
                }
                QComboBox QAbstractItemView::item:selected {
                    border: none;
                    outline: none;
                    background-color: rgb(153, 76, 40)
                }
            """)
            self.set_shadow(font)

        music_layout.addLayout(self.music_theme)
        music_layout.addWidget(
            end_line,
            alignment=Qt.AlignmentFlag.AlignCenter
        )
        music_layout.addStretch()

        return page
    
    def operate_event_home(self):
        page, update_layout = self.page_set(672, 490, 'transparent', (15, 0, 18, 20), (0, 0, 0, 0), False)
        update_layout.setSpacing(0)
        interaction_entry = Entry_set('互 动 功 能')
        lock_entry = Entry_set('锁 定 功 能')
        bug_entry = Entry_set('存 在 问 题')
        entry_lst_1 = [interaction_entry, lock_entry, bug_entry]
        for entry in entry_lst_1:
            update_layout.addWidget(entry, alignment = Qt.AlignmentFlag.AlignCenter)
        update_layout.addStretch()

        # 页面切换
        interaction_entry.entry.clicked.connect(lambda: self.intro_shift(self.operate_event_inter(0)))
        lock_entry.entry.clicked.connect(lambda: self.intro_shift(self.operate_event_inter(1)))
        bug_entry.entry.clicked.connect(lambda: self.intro_shift(self.operate_event_inter(2)))

        return page

    # 互动操作索引页面
    def operate_event_inter(self, num):
        page, update_layout = self.page_set(672, 490, 'transparent', (15, 0, 18, 20), (0, 0, 0, 0), False)
        update_layout.setSpacing(0)
        text = QTextEdit()
        text.setPlainText(self.intro_lst[num])
        text.setReadOnly(True)
        self.style_text(text)
        update_layout.addWidget(text)

        return page
   
    def update_event(self):
        color = 'rgba(102, 51, 0, 15)'
        page, update_layout = self.page_set(672, 490, 'transparent', (15, 0, 18, 20), (0, 0, 0, 0), False)
        update_layout.setSpacing(0)
        with open(resource_txt('update_log.txt'), 'r', encoding='utf-8') as f:
            whole_content = f.read()
        content_lst = [text.removeprefix("\n") for text in whole_content.split('§')]
        content_lst.reverse()

        card_width = 620

        for content in content_lst:
            update = QPlainTextEdit()
            update.setPlainText(content)
            update.setReadOnly(True)
            update.setStyleSheet("""
                QPlainTextEdit {
                    color: rgb(64, 64, 64);
                    font: "FangTi";
                    font-size: 15px;
                    background: transparent;
                    text-align: left;
                }
                """)

            update.setFixedWidth(card_width)
            measured_document = QTextDocument()
            measured_document.setDefaultFont(update.font())
            measured_document.setPlainText(content)
            measured_document.setTextWidth(card_width - 2 * update.frameWidth())
            height = max(
                update.minimumSizeHint().height(),
                ceil(measured_document.size().height()) + 14 * update.frameWidth(),
            )

            v_block, v_layout = self.page_set(640, height, color, (0, 0, 0, 0), (0, 0, 0, 0))

            v_layout.addWidget(update, 1)
            update_layout.addWidget(
                v_block,
                alignment = Qt.AlignmentFlag.AlignTop |
                    Qt.AlignmentFlag.AlignCenter
                )
        
        end_line = QLabel('————Ĉio komenciĝas ĉi tie————')
        end_line.setStyleSheet("""
            QLabel {
                color: rgb(255, 209, 159);
                background: transparent;
                }
            """)

        update_layout.addWidget(
            end_line,
            alignment = Qt.AlignmentFlag.AlignTop |
                Qt.AlignmentFlag.AlignCenter
            )
        update_layout.addStretch()

        return page
    
    def link_event(self):
        color = 'rgba(102, 51, 0, 15)'
        page, link_layout = self.page_set(672, 490, 'transparent', (15, 0, 15, 20), (0, 0, 0, 0), False)

        size = 170
        pixmap_profile = QPixmap(resource_path('profile.png'))

        circle_pixmap = QPixmap(size, size)
        circle_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(circle_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)

        scaled = pixmap_profile.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawPixmap(
            (size - scaled.width()) // 2,
            (size - scaled.height()) // 2,
            scaled,
        )
        painter.end()

        label_profile = QLabel()
        label_profile.setPixmap(circle_pixmap)
        link_layout.addWidget(
            label_profile,
            alignment = Qt.AlignmentFlag.AlignCenter
            )
        
        bili_a = QLabel('问题反馈、内容咨询')
        bili_a.setStyleSheet("""
            QLabel {
                color: "#818181";
                font-size: 20px;
                font-family: "KaiTi";
            }
        """)
        link_layout.addWidget(
            bili_a,
            alignment = Qt.AlignmentFlag.AlignCenter
        )

        bili_b = QLabel('或者可以给我一点小小的支持')
        bili_b.setStyleSheet("""
            QLabel {
                color: "#818181";
                font-size: 20px;
                font-family: "KaiTi";
            }
        """)
        link_layout.addWidget(
            bili_b,
            alignment = Qt.AlignmentFlag.AlignCenter
        )

        bili_path = QPushButton('bilibili@stelo_')
        bili_path.setFixedSize(200, 50)
        bili_path.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ff97cb,
                    stop: 1 #ff47a4
                );
                border-radius: 15px;
                border: 2px solid white;
                font-size: 20px;
            }

            QPushButton:hover {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffb0d8,
                    stop: 1 #ff5fb0
                )
            }
        """)
        bili_path.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl('https://space.bilibili.com/3546700536875231?spm_id_from=333.337.0.0'))
        )
        link_layout.addWidget(
            bili_path,
            alignment = Qt.AlignmentFlag.AlignCenter
        )

        bili_c = QLabel('任何bug都可以及时反馈，我会尽力尽快维修')
        bili_c.setStyleSheet("""
            QLabel {
                color: "#818181";
                font-size: 20px;
                font-family: "KaiTi";
            }
        """)
        link_layout.addWidget(
            bili_c,
            alignment = Qt.AlignmentFlag.AlignCenter
        )

        source_ = QHBoxLayout()
        source_a = QLabel('gif与语音素材取用自')
        source_a.setStyleSheet("""
            QLabel {
                color: "#818181";
                font-size: 20px;
                font-family: "KaiTi";
            }
        """)
        source_path = QPushButton('https://uttu.merui.net/')
        source_path.setContentsMargins(0, 0, 0, 0)
        source_path.setStyleSheet("""
            QPushButton {
                color: "#0080ff";
                background: transparent;
                font-size: 20px;
                font-family: "KaiTi";
                text-align: Left;
            }
        """)
        source_path.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl('https://uttu.merui.net/'))
        )
        source_.addStretch()
        source_.addWidget(source_a)
        source_.addWidget(source_path)
        source_.addStretch()
        link_layout.addLayout(
            source_
        )

        link_layout.setSpacing(20)
        link_layout.addStretch()

        return page

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.background)

    def set_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(8)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 160))
        widget.setGraphicsEffect(shadow)

    def choose_character(self, role):
        if self.lock_event :
            self.hint.show()
            self.hint.start_pos = self.mapToGlobal(
                QPoint(
                    (self.width() - self.hint.width()) // 2, 
                    (self.height() - self.hint.height()) // 2
                    )
                )
            self.come_ani.stop()
            self.appear_ani.stop()
            self.empty_timer.stop()
            self.leave_ani.stop()
            self.disapp_ani.stop()
            self.hint.refresh_ani()
            (self.come_ani, self.leave_ani, self.appear_ani, self.disapp_ani) = self.hint.ani_group
            self.come_ani.start()
            self.appear_ani.start()
            self.empty_timer.start()
            return
        self.chosen_character = role

    def page_choose(self, page):
        if self.page_show == page :
            return
        self.page_show = page
        if self.back_button.isVisible():
            self.back_button.hide()
        self.title_1.setText(self.title_dic[page][0])
        self.title_2.setText(self.title_dic[page][1])
        if self.in_page :
            self.mainlayout.removeWidget(self.in_page)
            self.in_page.hide()
        self.in_page = self.page_dic[page]
        if self.in_page :
            self.mainlayout.addWidget(self.in_page)
            self.in_page.show()

    def theme_change(self, text):
        self.theme_choice = text
        if self.theme_choice == "默认白框":
            self.clock_theme.addWidget(self.theme_font_widget)
            self.theme_font_widget.show()
        else:
            self.clock_theme.removeWidget(self.theme_font_widget)
            self.theme_font_widget.hide()

    # intro页面切换函数
    def intro_shift(self, page):
        if self.page_show == page :
            return
        self.page_show = page
        if not self.back_button.isVisible():
            self.back_button.show()
        if self.in_page :
            self.mainlayout.removeWidget(self.in_page)
            self.in_page.hide()
        self.in_page = page
        if self.in_page :
            self.mainlayout.addWidget(self.in_page)
            self.in_page.show()

    def home_page_ani(self, start, end, out = True):
        self.home_page_opacity = QGraphicsOpacityEffect(self.in_page)
        self.in_page.setGraphicsEffect(self.home_page_opacity)
        self.home_ani = QPropertyAnimation(self.home_page_opacity, b'opacity', self.in_page)
        self.home_ani.setDuration(240)
        self.home_ani.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.home_ani.setStartValue(start)
        self.home_ani.setEndValue(end)

        if out :
            self.home_ani.finished.connect(self.in_page.hide)

        self.home_ani.stop()
        self.home_ani.start()

    def style_text(self, editor):
        document = editor.document()

        # 全局字体设置
        global_style = QTextCharFormat()
        global_style.setForeground(QColor("#929292"))
        global_style.setFontPointSize(13)
        global_block_style = QTextBlockFormat()
        global_block_style.setLineHeight(
            150,
            QTextBlockFormat.LineHeightTypes.ProportionalHeight.value,
        )
        
        cursor = QTextCursor(document)
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeCharFormat(global_style)
        cursor.mergeBlockFormat(global_block_style)

        # 副标题字号与字色
        subtitle_style = QTextCharFormat()
        subtitle_style.setForeground(QColor("#818181"))
        subtitle_style.setFontPointSize(16)

        # 粗体字
        bold_style = QTextCharFormat()
        bold_style.setFontWeight(QFont.Weight.Bold)

        # 粗体字（针对英文）
        enbold_style = QTextCharFormat()
        enbold_style.setFontWeight(QFont.Weight.Bold)

        # 划线字
        erase_style = QTextCharFormat()
        erase_style.setFontStrikeOut(True)

        # 小字
        tiny_style = QTextCharFormat()
        tiny_style.setFontPointSize(5)

        subtitle_pattern = QRegularExpression(r"//[^////]+//")
        bold_pattern = QRegularExpression(r"bo[^bold]+ld")
        enbold_pattern = QRegularExpression(r"@@[^@@@@]+@@")
        erase_pattern = QRegularExpression(r"\*\*[^****]+\*\*")
        tiny_pattern = QRegularExpression(r"ti[^tiny]+ny")

        self.pattern_find(document, subtitle_pattern, subtitle_style)
        self.pattern_find(document, bold_pattern, bold_style)
        self.pattern_find(document, enbold_pattern, enbold_style)
        self.pattern_find(document, erase_pattern, erase_style)
        self.pattern_find(document, tiny_pattern, tiny_style)

    def pattern_find(self, document, pattern, style):
        cursor = QTextCursor(document)

        while True:
            cursor = document.find(pattern, cursor)
            if cursor.isNull() :
                break

            matched_text = cursor.selectedText()
            inner_text = matched_text[2:-2]
            
            cursor.mergeCharFormat(style)
            cursor.insertText(inner_text)

if __name__ == "__main__" :
    app = QApplication(sys.argv)
    window = Individuation()
    window.show()
    sys.exit(app.exec())