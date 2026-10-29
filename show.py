from PyQt6.QtWidgets import QApplication, QVBoxLayout, QMenu, QSystemTrayIcon, QMessageBox, QWidget, QLabel, QPushButton, QGraphicsOpacityEffect
import sys
import os
import random
import ctypes
import tempfile
from clock import Clock
from music import CD_show
from individuation import Individuation
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
from PyQt6.QtGui import QMovie, QPainter, QIcon, QMouseEvent, QPixmap, QCursor, QActionGroup, QWheelEvent, QFont
from PyQt6.QtCore import Qt, QEvent, QPoint, QTimer, QElapsedTimer, QPropertyAnimation, QAbstractAnimation, QEasingCurve, QSize, QUrl, QRect, QSequentialAnimationGroup, QSettings, QLockFile

# 角色取向
DEFAULT_CHARACTER = 'Sonetto'
SETTINGS_ORGANIZATION = 'ArcanistsHuman'
SETTINGS_APPLICATION = 'DesktopRole'


def load_character():
    settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
    saved_character = settings.value('character', DEFAULT_CHARACTER, type=str)
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    character_path = os.path.join(base_path, 'ArcanistsHuman', saved_character)
    if os.path.isdir(character_path):
        return saved_character
    return DEFAULT_CHARACTER


character = load_character()

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]

def system_idle_seconds():
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(info)

    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
        return 0

    now = ctypes.windll.kernel32.GetTickCount()
    return ((now - info.dwTime) & 0xFFFFFFFF) / 1000

def resource_path(relative_path):
    # 兼容源码运行和 PyInstaller 打包后的资源路径
    relative_path = 'ArcanistsHuman'+'/'+character+'/'+relative_path
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path,relative_path).replace('\\','/')

# icon取用
def resource_icon():
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, 'ArcanistsHuman', 'component_pic', 'icon.ico').replace('\\','/')

class Chat_wait(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

        self.chat_bkgds = []
        for path in ['chat_1.png', 'chat_2.png', 'chat_3.png'] :
            background = QPixmap(self.path_get(path))
            background = background.scaled(
                500, 500,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
                )
            self.chat_bkgds.append(background)
        self.setFixedSize(50, 33)

        self.index = 0
        self.change_chat = QTimer()
        self.change_chat.setInterval(500)
        self.change_chat.start()
        self.change_chat.timeout.connect(lambda: self.index_plus())

    def index_plus(self):
        self.index = (self.index + 1) % len(self.chat_bkgds)
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.chat_bkgds[self.index])

    def path_get(self, file):
        return os.path.join(self.base_path, 'ArcanistsHuman', 'component_pic', file)
    
class Lock(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout()
        
        self.btn_lock = QPushButton(chr(0xE785))

        self.btn_lock.setFixedSize(30,30)

        font = QFont("Segoe MDL2 Assets")
        font.setPixelSize(10)
        self.btn_lock.setFont(font)

        self.Top_stick = False
        self.btn_lock.setCheckable(True)

        self.btn_lock.setStyleSheet("""
        QPushButton {
            background-color: rgba(255, 255, 255, 10);
            color: white;
            border: 1px solid rgba(255, 255, 255, 20);
            border-radius: 6px;
            padding: 4px 10px;

            /*字体设置*/
            font-weight: normal;
            color: white;
        }
        QPushButton:checked {
            background-color: rgba(255, 255, 255, 30);
            color: white;
            border: 1px solid rgba(255, 255, 255, 60);
            border-radius: 6px;
            padding: 4px 10px;
        }
        """)
        layout.addWidget(self.btn_lock)

        self.setLayout(layout)

        self.lock_btn_in = QPropertyAnimation(self, b'windowOpacity', self)
        self.lock_btn_in.setDuration(100)
        self.lock_btn_in.setEndValue(1.0)
        self.lock_btn_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.lock_btn_out = QPropertyAnimation(self, b'windowOpacity', self)
        self.lock_btn_out.setDuration(200)
        self.lock_btn_out.setEndValue(0.0)
        self.lock_btn_out.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.lock_btn_out.finished.connect(self.close)
        
        self.resize(30,30)
        self.move(100,100)

class Chatting(QWidget):
    # 设置聊天窗口
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        main_layout = QVBoxLayout()

        # 语音条目
        self.chat_btn_1 = QPushButton('问候')
        self.chat_btn_2 = QPushButton('帽檐与发鬓')
        self.chat_btn_3 = QPushButton('袖与手')
        self.chat_btn_4 = QPushButton('衣着与身形')
        self.chat_btn_5 = QPushButton('嗜好')
        self.chat_btn_6 = QPushButton('赞赏')
        self.chat_btn_7 = QPushButton('初遇')
        self.chat_btn_8 = QPushButton('气候')
        self.chat_btn_9 = QPushButton('未来')
        self.chat_btn_10 = QPushButton('亲昵')
        self.chat_btn_11 = QPushButton('闲谈')
        self.chat_btn_12 = QPushButton('独白')
        self.chat_btn_13 = QPushButton('洞悉')
        self.chat_btn_14 = QPushButton('洞悉之底')
        self.lst_1st = 0
        self.lst_6rd = 7
        
        self.btn_all_lst = [self.chat_btn_1, self.chat_btn_2, self.chat_btn_3, 
                            self.chat_btn_4, self.chat_btn_5, self.chat_btn_6, 
                            self.chat_btn_7, self.chat_btn_8, self.chat_btn_9, 
                            self.chat_btn_10, self.chat_btn_11, self.chat_btn_12,
                            self.chat_btn_13, self.chat_btn_14]

        self.btn_lst = []
        self.button_effects_temp = []
        self.in_animations_temp = []
        self.out_animations_temp = []
        self.appear_animations_temp = []
        self.disapp_animations_temp = []
        self.appear_temp = []
        self.disapp_temp = []

        self.btn_ani_start = 0

        self.chat_time_show = QTimer(self)
        self.chat_time_show.setInterval(50)
        self.chat_time_show.timeout.connect(self.show_animated)

        self.chat_time_hide = QTimer(self)
        self.chat_time_hide.setInterval(50)
        self.chat_time_hide.timeout.connect(self.hide_animated)

        addition = 0
        
        for chat in self.btn_all_lst:
            chat.setFixedSize(180,28)
            effect = QGraphicsOpacityEffect(chat)
            effect.setOpacity(0.0)
            chat.setGraphicsEffect(effect)
            self.button_effects_temp.append(effect)

            in_ani = QPropertyAnimation(effect, b"opacity", chat)
            in_ani.setDuration(180)
            in_ani.setStartValue(0.0)
            in_ani.setEndValue(1.0)
            in_ani.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.in_animations_temp.append(in_ani)

            out_ani = QPropertyAnimation(effect, b"opacity", chat)
            out_ani.setDuration(180)
            out_ani.setStartValue(1.0)
            out_ani.setEndValue(0.0)
            out_ani.setEasingCurve(QEasingCurve.Type.InCubic)
            self.out_animations_temp.append(out_ani)

            appear_ani = QPropertyAnimation(chat, b"pos", chat)
            appear_ani.setDuration(180)
            appear_ani.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.appear_animations_temp.append(appear_ani)

            disapp_ani = QPropertyAnimation(chat, b"pos", chat)
            disapp_ani.setDuration(180)
            disapp_ani.setEasingCurve(QEasingCurve.Type.InCubic)
            self.disapp_animations_temp.append(disapp_ani)

            main_layout.addWidget(chat)

            self.appear_pos = chat.pos() + QPoint(10, int(addition))
            self.disapp_pos = chat.pos() + QPoint(0, int(addition))

            chat.move(self.appear_pos)

            addition += 35

            self.appear_temp.append(self.appear_pos)
            self.disapp_temp.append(self.disapp_pos)
        
        self.appear = self.appear_temp[int(self.lst_1st):int(self.lst_6rd)]
        self.disapp = self.disapp_temp[int(self.lst_1st):int(self.lst_6rd)]

        self.lst_load()

        self.setLayout(main_layout)
        self.setFixedSize(200,260)
        self.move(300,200)

    def come_in_ani(self, index):
        
        self.out_animations[index].stop()
        self.disapp_animations[index].stop()
        
        self.in_animations[index].setStartValue(self.button_effects[index].opacity())
        self.in_animations[index].start()

        self.appear_animations[index].setEndValue(self.disapp[index])
        self.appear_animations[index].start()

    def come_out_ani(self, index):

        self.in_animations[index].stop()
        self.appear_animations[index].stop()

        self.out_animations[index].setStartValue(self.button_effects[index].opacity())
        self.out_animations[index].start()

        self.disapp_animations[index].setEndValue(self.appear[index])
        self.disapp_animations[index].start()

    def lst_load(self):
        self.btn_lst = self.btn_all_lst[int(self.lst_1st):int(self.lst_6rd)]
        self.in_animations = self.in_animations_temp[int(self.lst_1st):int(self.lst_6rd)]
        self.out_animations = self.out_animations_temp[int(self.lst_1st):int(self.lst_6rd)]
        self.appear_animations = self.appear_animations_temp[int(self.lst_1st):int(self.lst_6rd)]
        self.disapp_animations = self.disapp_animations_temp[int(self.lst_1st):int(self.lst_6rd)]
        self.button_effects = self.button_effects_temp[int(self.lst_1st):int(self.lst_6rd)]

    def scroll_mov(self):
        for btn, pos in zip(self.btn_lst, self.disapp) :
            btn.scroll_to = QPropertyAnimation(btn, b'pos', btn)
            btn.scroll_to.setDuration(180)
            btn.scroll_to.setEasingCurve(QEasingCurve.Type.OutCubic)
            btn.scroll_to.setEndValue(pos)
            btn.scroll_to.start()

    def show_animated(self):
        if not self.isVisible():
            self.show()
        
        index = self.btn_ani_start
        if index >= len(self.btn_lst) :
            return

        self.come_in_ani(index)

        self.btn_ani_start += 1
        index = self.btn_ani_start

    def hide_animated(self):
        
        index = self.btn_ani_start
        if index <= 0 :
            return
        
        if not self.isVisible():
            return
        
        self.btn_ani_start -= 1
        index = self.btn_ani_start
        
        self.come_out_ani(index)

    def wheelEvent(self, event: QWheelEvent):
        delta_y = event.angleDelta().y()

        if delta_y > 0 :
            if self.lst_1st <= 0 :
                return
            
            self.lst_1st -= 1
            self.lst_6rd -= 1
            self.come_out_ani(len(self.btn_lst)-1)
            self.lst_load()
            self.come_in_ani(0)
            self.scroll_mov()
        elif delta_y < 0 :
            if self.lst_6rd >= len(self.btn_all_lst) :
                return

            self.lst_1st += 1
            self.lst_6rd += 1
            self.come_out_ani(0)
            self.lst_load()
            self.come_in_ani(len(self.btn_lst)-1)
            self.scroll_mov()

class Skill(QWidget):
    # 技能图片窗口：负责显示图片以及图片的缩放、移动动画
    def __init__(self, png1_path):
        super().__init__()
        self.pixmap_ = QPixmap(png1_path)
        if self.pixmap_.isNull():
            raise FileNotFoundError(f"无法加载图片：{png1_path}")

        self.resize(self.pixmap_.size())

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.resize(100,125)
        self.current_image_path = png1_path

        # 鼠标移入或移出图片时使用平滑缩放动画
        self.size_animation = QPropertyAnimation(self, b"size", self)
        self.size_animation.setDuration(150)
        self.size_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 鼠标移入或移出图片时使用平滑位置动画
        self.point_animation = QPropertyAnimation(self, b"pos", self)
        self.point_animation.setDuration(150)
        self.point_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity", self)
        self.fade_in_animation.setDuration(250)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity", self)
        self.fade_out_animation.setDuration(250)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.fade_out_animation.finished.connect(self.close)

    def fade_in(self):
        self.fade_out_animation.stop()

        self.setWindowOpacity(0.0)
        self.show()

        self.fade_in_animation.stop()
        self.fade_in_animation.start()

    def fade_out(self):
        self.fade_in_animation.stop()

        self.fade_out_animation.stop()
        self.fade_out_animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.pixmap_)

    def set_image_light(self, image_path):
        # 切换为亮色图片；如果当前已经是该图片，则不重复刷新
        if self.current_image_path == image_path:
            return
        self.pixmap_ = QPixmap(image_path)
        self.current_image_path = image_path
        self.animate_size(QSize(104, 130))
        self.update()

    def set_image_dark(self, image_path):
        # 切换为暗色图片；如果当前已经是该图片，则不重复刷新
        if self.current_image_path == image_path:
            return
        self.pixmap_ = QPixmap(image_path)
        self.current_image_path = image_path
        self.animate_size(QSize(100, 125))
        self.update()

    def animate_size(self, target_size):
        # 从当前窗口大小平滑过渡到目标大小
        self.size_animation.stop()
        self.size_animation.setStartValue(self.size())
        self.size_animation.setEndValue(target_size)
        self.size_animation.start()

    def animate_point(self, target_point):
        # 从当前位置平滑移动到目标位置
        self.point_animation.stop()
        self.point_animation.setStartValue(self.pos())
        self.point_animation.setEndValue(target_point)
        self.point_animation.start()

class InteractiveGif(QWidget):
    # GIF 主窗口：负责播放动画、处理鼠标拖动和长按操作
    def __init__(self, gif_path, click_gif_path, giddy_gif_path, born_gif_path, sleep_gif_path, skill1_gif_path, skill2_gif_path, lock_gif_path):
        super().__init__()
        self.original_movie = QMovie(gif_path)
        self.click_movie = QMovie(click_gif_path)
        self.giddy_movie = QMovie(giddy_gif_path)
        self.born_movie = QMovie(born_gif_path)
        self.sleep_movie = QMovie(sleep_gif_path)
        self.skill1_movie = QMovie(skill1_gif_path)
        self.skill2_movie = QMovie(skill2_gif_path)
        self.lock_movie = QMovie(lock_gif_path)

        # 音频设置
        self.speaking_output = QAudioOutput(self)
        self.speaking_output.setVolume(0.5)
        self.audio_devices = QMediaDevices(self)
        self.audio_devices.audioOutputsChanged.connect(self.refresh_audio_output)
        self.speaking_sound = QMediaPlayer(self)
        self.speaking_sound.setAudioOutput(self.speaking_output)

        # 待机监测
        self.idle_state_after = 900
        self.idle_audio_after = 900
        self.user_is_idle = False

        self.idle_check_timer = QTimer(self)
        self.idle_check_timer.timeout.connect(self.check_user_idle)
        self.idle_check_timer.start(1000)

        # 待机聊天阶段
        self.chat_level = 0

        if not self.original_movie.isValid():
            raise FileNotFoundError(f"无法加载 GIF：{gif_path}")
        if not self.click_movie.isValid():
            raise FileNotFoundError(f"无法加载点击动画 GIF：{click_gif_path}")
        if not self.giddy_movie.isValid():
            raise FileNotFoundError(f"无法加载点击动画 GIF：{giddy_gif_path}")
        if not self.born_movie.isValid():
            raise FileNotFoundError(f"无法加载点击动画 GIF：{born_gif_path}")
        if not self.sleep_movie.isValid():
            raise FileNotFoundError(f"无法加载点击动画 GIF：{sleep_gif_path}")
        if not self.skill1_movie.isValid():
            raise FileNotFoundError(f"无法加载点击动画 GIF：{skill1_gif_path}")
        if not self.skill2_movie.isValid():
            raise FileNotFoundError(f"无法加载点击动画 GIF：{skill2_gif_path}")
        if not self.lock_movie.isValid():
            raise FileNotFoundError(f"无法加载点击动画 GIF：{lock_gif_path}")

        # 待机状态标签与时间
        self.none_action = False
        self.sleep_able = False
        self.sleep_time = 0

        # movie 保存当前正在显示的 GIF 动画
        self.movie = self.original_movie
        self.movie.frameChanged.connect(self.update)

        self.click_movie.frameChanged.connect(self.update)
        self.click_movie.frameChanged.connect(self.check_gif_click_movie_finished)
        self.click_movie.finished.connect(self.restore_original)

        self.skill1_movie.frameChanged.connect(self.update)
        self.skill1_movie.frameChanged.connect(self.check_skill1_movie_finished)
        self.skill1_movie.finished.connect(self.restore_original)\

        self.skill2_movie.frameChanged.connect(self.update)
        self.skill2_movie.frameChanged.connect(self.check_skill2_movie_finished)
        self.skill2_movie.finished.connect(self.restore_original)

        self.giddy_movie.frameChanged.connect(self.update)
        self.giddy_movie.frameChanged.connect(self.giddy)

        self.sleep_movie.frameChanged.connect(self.update)
        self.lock_movie.frameChanged.connect(self.update)

        # 普通点击动画结束后恢复待机动画
        self.restore_timer = QTimer(self)
        self.restore_timer.setSingleShot(True)
        self.restore_timer.timeout.connect(self.restore_original)

        # 特殊动画播放一段时间后恢复待机动画
        self.giddy_timer = QTimer(self)
        self.giddy_timer.setSingleShot(True)
        self.giddy_timer.timeout.connect(self.restore_original)

        # 待机计时器
        self.none_timer = QTimer(self)
        self.none_timer.setSingleShot(True)
        self.none_timer.setInterval(int(self.sleep_time))
        self.none_timer.timeout.connect(self.noneActionTimer)

        self.born_movie.frameChanged.connect(self.update)
        self.born_movie.frameChanged.connect(self.check_born_movie_finished)
        self.born_movie.finished.connect(self.restore_original)

        self.resize(self.movie.currentPixmap().size())

        self.setWindowFlags(
            Qt.WindowType.Window
            |Qt.WindowType.FramelessWindowHint
            |Qt.WindowType.WindowStaysOnTopHint
            |Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(500,300)
        self.move(1300,700)

        # 拖动相关状态
        self.drag_start_pos = QPoint()
        self.press_pos = None
        self.dragging = False
        self.drag_enabled = True
        self.giddy_mode = False

        self.click_time = 0
        self.click_clock = QElapsedTimer()
        self.click_clock.start()
        self.last_click_time = None
        self.click_interval = 0

        # 鼠标方位标签
        self.head_at_pos = False

        # 鼠标左键按住 800 毫秒后触发长按逻辑
        self.long_press_timer = QTimer(self)
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.setInterval(800)
        self.long_press_timer.timeout.connect(self.gif_long_pressed)
        self.long_pressed = False 
        
        # 创建两个长按后出现的技能图片窗口
        self.pixmap_1 = Skill(resource_path('PNG/skill_1_dark.png'))
        self.skill_1_offset = QPoint(-self.pixmap_1.width() + 180, 0)

        self.pixmap_2 = Skill(resource_path('PNG/skill_2_dark.png'))
        self.skill_2_offset = QPoint(self.pixmap_2.width() + 220, 0)
        
        # 入场
        self.gif_start()

        # 创建组件窗口
        self.clock_window = Clock()
        self.music_window = CD_show()
        self.app_index = 0
        self.app_lst = [self.clock_window, self.music_window]
        self.app_in_ani_lst = []
        self.app_out_ani_lst = []
        self.app_off_ani_lst = []
        self.small_app = self.clock_window
        self.small_app.stackUnder(self)

        self.app_pos_refresh()

        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

        # 每个小组件使用自己的进出动画
        for app_widget in self.app_lst:    
            app_in_ani = QPropertyAnimation(app_widget, b'windowOpacity', app_widget)
            app_in_ani.setDuration(200)
            app_in_ani.setEndValue(1.0)
            app_in_ani.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.app_in_ani_lst.append(app_in_ani)

            app_out_ani = QPropertyAnimation(app_widget, b'windowOpacity', app_widget)
            app_out_ani.setDuration(200)
            app_out_ani.setEndValue(0.0)
            app_out_ani.setEasingCurve(QEasingCurve.Type.OutCubic)
            app_out_ani.finished.connect(app_widget.hide)
            self.app_out_ani_lst.append(app_out_ani)

            app_off_ani = QPropertyAnimation(app_widget, b'pos', app_widget)
            app_off_ani.setDuration(200)
            self.app_off_ani_lst.append(app_off_ani)
            
        self.app_in_ani, self.app_out_ani = self.app_in_ani_lst[self.app_index], self.app_out_ani_lst[self.app_index]
        self.app_off_ani = self.app_off_ani_lst[self.app_index]

        # 锁定移动标签
        self.lock_moving = False

        # 鼠标位于聊天框时的标签
        self.on_chatbox = False

        # 是否显示小组件
        self.app_on = True

        self.lock_btn = Lock()

        # 聊天框
        self.chatbox = Chatting()
        self.chatbox_timer = QTimer(self)
        self.chatbox_timer.setInterval(50)
        self.chatbox_timer.timeout.connect(self.check_chatbox_pos)

        self.clockbox_timer = QTimer(self)
        self.clockbox_timer.setInterval(50)
        self.clockbox_timer.timeout.connect(self.check_app_pos)

        # 聊天语音绑定
        self.chat_btns = self.chatbox.btn_all_lst
        morning_lst = [resource_path("WAV/morning_1.wav"),resource_path("WAV/morning_2.wav")]
        night_lst = [resource_path("WAV/night_1.wav"),resource_path("WAV/night_2.wav")]

        self.chat_1_lst = [morning_lst, night_lst]
        self.chat_btns[0].clicked.connect(self.chat_1)
        self.chat_btns[1].clicked.connect(self.chat_2)
        self.chat_btns[2].clicked.connect(self.chat_3)
        self.chat_btns[3].clicked.connect(self.chat_4)
        self.chat_btns[4].clicked.connect(self.chat_5)
        self.chat_btns[5].clicked.connect(self.chat_6)
        self.chat_btns[6].clicked.connect(self.chat_7)
        self.chat_btns[7].clicked.connect(self.chat_8)
        self.chat_btns[8].clicked.connect(self.chat_9)
        self.chat_btns[9].clicked.connect(self.chat_10)
        self.chat_btns[10].clicked.connect(self.chat_11)
        self.chat_btns[11].clicked.connect(self.chat_12)
        self.chat_btns[12].clicked.connect(self.chat_13)
        self.chat_btns[13].clicked.connect(self.chat_14)
        for chat_btn in self.chat_btns:
            chat_btn.clicked.connect(self.chat_clicked)

        # 语音提示
        self.chat_wait = Chat_wait()
        self.speaking_sound.mediaStatusChanged.connect(self.chat_end)

        # 聊天对话标签
        self.if_chatting = True
        self.chat_wait.hide()

        # 栏显示标签
        self.skill_able = True
        self.chat_able = True
        self.idle_chat_able = True

        # 自定义菜单
        self.individual = Individuation()
        for btn in self.individual.cha_btns :
            btn.clicked.connect(lambda checked=False: self.role_change())
        self.color_dic = {'白色': 'white', '黑色': 'black', '红色': 'red', '黄色': 'yellow',  '蓝色': 'blue', '绿色': 'green'}
        self.back_dic = {
            '白色': ['rgba(255, 255, 255, 10)', 'rgba(255, 255, 255, 20)'],
            '黑色': ['rgba(0, 0, 0, 100)', 'rgba(0, 0, 0, 130)'],
            '红色': ['rgba(255, 0, 0, 100)', 'rgba(255, 0, 0, 130)'],
            '黄色': ['rgba(255, 255, 0, 100)', 'rgba(255, 255, 0, 130)'],
            '蓝色': ['rgba(0, 0, 255, 100)', 'rgba(0, 0, 255, 130)'],
            '绿色': ['rgba(0, 255, 0, 100)', 'rgba(0, 255, 0, 130)'],
            }
        settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        saved_font_color = settings.value(
            'clock_font_color',
            self.color_dic['白色'],
            type=str,
        )
        if saved_font_color not in self.color_dic.values():
            saved_font_color = self.color_dic['白色']
        saved_font_label = next(
            label for label, color in self.color_dic.items()
            if color == saved_font_color
        )
        saved_back_color = settings.value(
            'clock_back_color',
            self.back_dic['白色'],
            type=str,
        )
        if saved_back_color not in self.back_dic.values():
            saved_back_color = self.back_dic['白色']
        saved_back_label = next(
            label for label, color in self.back_dic.items()
            if color == saved_back_color
        )
        self.color_font = saved_font_color
        self.color_back = saved_back_color
        self.individual.theme_combo_1.setCurrentText(saved_font_label)
        self.individual.theme_combo_2.setCurrentText(saved_back_label)
        self.individual.theme_combo_1.currentTextChanged.connect(lambda text: self.font_change_color(text))
        self.individual.theme_combo_2.currentTextChanged.connect(lambda text: self.back_change_color(text))
        self.individual.theme_combo_1.currentTextChanged.connect(lambda text: self.clock_color(text))
        self.individual.theme_combo_2.currentTextChanged.connect(lambda text: self.clock_color(text))
        self.clock_color(saved_font_label)
        self.clock_color(saved_back_label)

    def app_pos_refresh(self):
        # 组件位置偏移
        self.clock_pos = self.pos()-QPoint(70,-50)
        self.music_pos = self.pos()-QPoint(120,-20)

    def back_change_color(self, color):
        self.color_back = self.back_dic[color]
        settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        settings.setValue('clock_back_color', self.color_back)
        settings.sync()

    def chat_end(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia :
            self.if_chatting = False
            self.chat_wait.hide()

    def chat_1(self):
        self.speaking_sound.stop()
        time_check = self.clock_window.hour
        day_or_night = abs((time_check - 7) // 12)
        sound_path = random.choice(self.chat_1_lst[day_or_night]) 
        if not os.path.exists(sound_path):
            return
        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def chat_2(self):
        self.speaking_sound.stop()
        sound_path = resource_path("WAV/hat_and_hair.wav")
        if not os.path.exists(sound_path):
            return
        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def chat_3(self):
        self.speaking_sound.stop()
        sound_path = resource_path("WAV/sleeves_and_hands.wav")
        if not os.path.exists(sound_path):
            return
        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def chat_4(self):
        self.speaking_sound.stop()
        sound_path = resource_path("WAV/clothing_and_torso.wav")
        if not os.path.exists(sound_path):
            return
        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def chat_5(self):
        self.speaking_sound.stop()
        sound_path = resource_path("WAV/hobby.wav")
        if not os.path.exists(sound_path):
            return
        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def chat_6(self):
        self.speaking_sound.stop()
        sound_path = resource_path("WAV/praise.wav")
        if not os.path.exists(sound_path):
            return
        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def chat_7(self):
        self.speaking_sound.stop()
        sound_path = resource_path("WAV/first_greeting.wav")
        if not os.path.exists(sound_path):
            return
        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def chat_8(self):
        self.speaking_sound.stop()
        sound_path = resource_path("WAV/climate.wav")
        if not os.path.exists(sound_path):
            return
        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def chat_9(self):
        self.speaking_sound.stop()
        sound_path = resource_path("WAV/future.wav")
        if not os.path.exists(sound_path):
            return
        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def chat_10(self):
        self.speaking_sound.stop()
        sound_path = resource_path("WAV/intimacy.wav")
        if not os.path.exists(sound_path):
            return
        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def chat_11(self):
        self.speaking_sound.stop()
        self.chat_11_lst = [resource_path('WAV/chitchat_1.wav'), resource_path('WAV/chitchat_2.wav')]
        sound_path = random.choice(self.chat_11_lst) 
        if not os.path.exists(sound_path):
            return
        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def chat_12(self):
        self.speaking_sound.stop()
        sound_path = resource_path("WAV/monologue.wav")
        if not os.path.exists(sound_path):
            return
        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def chat_13(self):
        self.speaking_sound.stop()
        sound_path = resource_path("WAV/insight.wav")
        if not os.path.exists(sound_path):
            return
        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def chat_14(self):
        self.speaking_sound.stop()
        sound_path = resource_path("WAV/bottom_of_insight.wav")
        if not os.path.exists(sound_path):
            return
        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def chat_clicked(self):
        self.if_chatting = True
        self.chat_wait.show()

    def check_app_pos(self):
        if not self.app_on :
            return
        
        if self.lock_btn.btn_lock.isChecked():
            self.lock_btn.Top_stick = True
            self.lock_btn.btn_lock.setText(chr(0xE72E))
        else :
            self.lock_btn.Top_stick = False
            self.lock_btn.btn_lock.setText(chr(0xE785))
        
        if self.lock_moving and not self.lock_btn.Top_stick :
            
            cursor_pos = QCursor.pos()
            character_rect = QRect(self.width()*2//5, 0, self.width()//5, self.height())
            
            in_charactor = character_rect.contains(self.mapFromGlobal(cursor_pos))
            self.inside_app = self.small_app.frameGeometry()
            in_appwindow = self.inside_app.contains(cursor_pos)
            in_lockbtn = self.lock_btn.frameGeometry().contains(cursor_pos)
            if in_charactor or in_appwindow or in_lockbtn :
                return

            if self.small_app.isVisible() and self.app_out_ani.state() != QAbstractAnimation.State.Running:
                self.app_out_ani.setStartValue(self.small_app.windowOpacity())
                self.app_out_ani.start()
            if self.lock_btn.isVisible() and self.lock_btn.lock_btn_out.state() != QAbstractAnimation.State.Running:
                self.lock_btn.lock_btn_out.setStartValue(self.lock_btn.windowOpacity())
                self.lock_btn.lock_btn_out.start()

    def check_born_movie_finished(self, frame_number):
        # 检查入场动画是否播放到最后一帧
        if self.movie is not self.born_movie:
            return

        last_frame = self.born_movie.frameCount() - 1
        if last_frame >= 0 and frame_number >= last_frame:
            delay = max(1, self.born_movie.nextFrameDelay())
            self.restore_timer.start(delay)

    # 检查鼠标是否位于角色与聊天框内
    def check_chatbox_pos(self):
        if self.movie is not self.original_movie or self.pixmap_1.isVisible() or self.dragging :
            self.chatbox.chat_time_show.stop()
            self.chatbox.chat_time_hide.stop()
            self.chatbox.chat_time_hide.start()
            self.chatbox_timer.stop()
            return

        cursor_pos = QCursor().pos()

        character_rect = QRect(self.width()*2//5, 0, self.width()//5, self.height())

        in_charactor = character_rect.contains(self.mapFromGlobal(cursor_pos))
        in_exwindow = self.chatbox.frameGeometry().contains(cursor_pos)

        # 鼠标位于聊天框时，标签为True
        if in_exwindow :
            self.on_chatbox = True

        if in_charactor or in_exwindow :
            return

        # 如果不在指定区域内则收起聊天框，并关闭标签
        self.chatbox.chat_time_show.stop()
        self.chatbox.chat_time_hide.stop()
        self.chatbox.chat_time_hide.start()
        self.chatbox_timer.stop()
        self.on_chatbox = False

    def check_giddy_movie_finished(self, frame_number):
        # 检查特殊动画是否播放到最后一帧
        if self.movie not in (self.click_movie, self.giddy_movie, self.born_movie, self.sleep_movie):
            return

        last_frame = self.giddy_movie.frameCount() - 1
        if last_frame >= 0 and frame_number >= last_frame:
            delay = max(1, self.giddy_movie_movie.nextFrameDelay())
            self.restore_timer.start(delay)

    def check_gif_click_movie_finished(self, frame_number):
        # 检查点击动画是否播放到最后一帧
        if self.movie not in (self.click_movie,self.giddy_movie,self.born_movie,self.sleep_movie):
            return

        last_frame = self.click_movie.frameCount() - 1
        if last_frame >= 0 and frame_number >= last_frame :
            delay = max(1, self.click_movie.nextFrameDelay())
            self.restore_timer.start(delay)
            if self.click_interval != None and float(self.click_interval) <= 1000 :
                self.click_time += 1

    # 点击次数累计触发与giddy状态累计时长
        if self.click_time == 3:
            self.restore_timer.stop()
            self.click_movie.stop()
            self.giddy_movie.jumpToFrame(0)
            self.movie = self.giddy_movie
            self.giddy_movie.start()
            self.giddy_timer.start(5000)
            self.click_time = 0
    
    def check_skill1_movie_finished(self, frame_number):
        # 检查入场动画是否播放到最后一帧
        if self.movie is not self.skill1_movie :
            return

        last_frame = self.skill1_movie.frameCount() - 1
        if last_frame >= 0 and frame_number >= last_frame:
            delay = max(1, self.skill1_movie.nextFrameDelay())
            self.restore_timer.start(delay)

    def check_skill2_movie_finished(self, frame_number):
        # 检查入场动画是否播放到最后一帧
        if self.movie is not self.skill2_movie :
            return

        last_frame = self.skill2_movie.frameCount() - 1
        if last_frame >= 0 and frame_number >= last_frame:
            delay = max(1, self.skill2_movie.nextFrameDelay())
            self.restore_timer.start(delay)

    def check_user_idle(self):
        if not self.idle_chat_able :
            return

        idle_seconds = system_idle_seconds()

        if self.lock_moving :
            return

        is_idle = idle_seconds >= self.idle_state_after

        if self.user_is_idle and not is_idle:
            self.chat_level = 0
            self.idle_audio_after = 900

        self.user_is_idle = is_idle

        if not is_idle:
            return

        if idle_seconds < self.idle_audio_after :
            return

        if (
            self.speaking_sound.playbackState()
            != QMediaPlayer.PlaybackState.StoppedState
        ):
            return

        if self.chat_level == 0 :
            time_check = self.clock_window.hour
            day_or_night = abs((time_check - 7) // 12)
            pass_down = random.choice([True, False])
            if pass_down :
                self.chat_level = 1
                self.idle_audio_after = idle_seconds + 900
                return
            sound_path = random.choice(self.chat_1_lst[day_or_night])
            next_chat_level = 1
            next_idle_audio_after = idle_seconds + 900
        elif self.chat_level == 1 :
            sound_path = resource_path('WAV/idle.wav')
            next_chat_level = 2
            next_idle_audio_after = idle_seconds + random.randint(900, 3000)
        elif self.chat_level == 2 :
            sound_path = random.choice([resource_path('WAV/climate.wav'), resource_path('WAV/future.wav'),
                                       resource_path('WAV/chitchat_1.wav'), resource_path('WAV/chitchat_2.wav'),
                                       resource_path('WAV/monologue.wav')])
            next_chat_level = 2
            next_idle_audio_after = idle_seconds + random.randint(900, 3000)
        else:
            return

        if not os.path.exists(sound_path):
            return

        self.chat_clicked()
        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()
        self.chat_level = next_chat_level
        if next_chat_level < 3:
            self.idle_audio_after = next_idle_audio_after
    
    def clock_color(self, color):
        for btn in self.clock_window.time_lst:
            btn.setStyleSheet("""
            QPushButton:disabled {{
                background-color: {back_};
                border: 1px solid {border_};
                border-radius: 6px;
                padding: 4px 10px;

                font-family: "Arial Rounded MT Bold", "Arial", sans-serif;
                font-size: 48px;
                font-weight: noraml;
                color: {color_};
            }}
            """.format(back_ = self.color_back[0], border_ = self.color_back[1], color_ = self.color_font))
        self.clock_window.btn_date.setStyleSheet("""
            QPushButton:disabled {{
                background-color: {back_};
                border: 1px solid {border_};
                border-radius: 6px;
                padding: 2px 10px;

                font-family: "Arial Rounded MT Bold", "Arial", sans-serif;
                font-size: 15px;
                font-weight: noraml;
                color: {color_};
            }}
            """.format(back_ = self.color_back[0], border_ = self.color_back[1], color_ = self.color_font))
    
    def enterEvent(self, event: QMouseEvent):
        
        if self.movie is not self.original_movie :
            if not self.app_on :
                return
            
            if self.lock_moving and not self.lock_btn.Top_stick :
                self.app_in_ani.setStartValue(self.small_app.windowOpacity())
                
                self.app_out_ani.stop()
                self.app_in_ani.stop()
                self.lock_btn.lock_btn_in.stop()
                self.lock_btn.lock_btn_out.stop()
                
                self.small_app.show()
                self.lock_btn.show()
                self.small_app.lower()
                self.app_in_ani.start()
                self.lock_btn.lock_btn_in.start()
                self.raise_()
                self.lock_btn.raise_()
            return

        if not self.chat_able :
            return

        self.chatbox.chat_time_hide.stop()
        self.chatbox.chat_time_show.stop()
        self.chatbox.chat_time_show.start()
        self.chatbox_timer.start()
    
    def eventFilter(self, watched, event):
            if event.type() == QEvent.Type.Wheel and isinstance(watched, QWidget):
                if watched.window() is self.small_app:
                    delta_y = event.angleDelta().y()
                    if delta_y < 0:
                        self.switch_small_app(1)
                    elif delta_y > 0:
                        self.switch_small_app(-1)
                    return True
    
            return super().eventFilter(watched, event)

    def font_change_color(self, color):
        self.color_font = self.color_dic[color]
        settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        settings.setValue('clock_font_color', self.color_font)
        settings.sync()
   
    def giddy(self):
        # 根据当前播放的动画更新特殊动画状态
        if self.movie is not self.giddy_movie:
            self.giddy_mode = False
        else :
            self.giddy_mode = True

    def gif_clicked(self):
        # 处理普通点击，并统计连续点击间隔
        if self.lock_moving :
            return
        
        if self.head_at_pos :
            current_time = self.click_clock.elapsed()
            if self.if_chatting :
                self.speaking_sound.stop()
                self.chat_wait.hide()
                self.if_chatting = False
            
            if self.last_click_time is None:
                self.click_interval = None
            else:
                self.click_interval = current_time - self.last_click_time
            self.last_click_time = current_time

            if self.movie in (self.click_movie, self.giddy_movie, self.born_movie, self.skill1_movie, self.skill2_movie):
                return

            self.movies_stop()
            self.click_movie.jumpToFrame(0)
            self.movie = self.click_movie
            self.click_movie.start()

    def gif_long_pressed(self):
        if self.lock_moving :
            return

        # 长按成功后禁止主窗口拖动，并显示技能图片窗口
        if not self.dragging and self.movie not in (self.skill1_movie, self.skill2_movie, self.born_movie, self.giddy_movie, self.sleep_movie) :
            self.long_pressed = True
            self.drag_enabled = False
            if not self.giddy_mode :
                self.pixmap_1.fade_in()
                self.pixmap_2.fade_in()

    def gif_start(self):
        # 播放入场动画，从第一帧开始
        sound_lst = [resource_path("WAV/born_1.wav"),resource_path("WAV/born_2.wav"),resource_path("WAV/born_3.wav")]
        sound_path = random.choice(sound_lst)

        if not os.path.exists(sound_path):
            return

        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        
        self.speaking_sound.stop()
        self.speaking_sound.play()
        self.movies_stop()
        self.born_movie.jumpToFrame(0)
        self.movie = self.born_movie
        self.setEnabled(False)
        self.born_movie.start()

    def is_mouse_over_skill_1(self):
        # 将屏幕坐标转换为图片窗口坐标，判断鼠标是否在技能图片 1 内
        mouse_pos = self.pixmap_1.mapFromGlobal(QCursor.pos())
        return self.pixmap_1.rect().contains(mouse_pos)

    def is_mouse_over_skill_2(self):
        # 将屏幕坐标转换为图片窗口坐标，判断鼠标是否在技能图片 2 内
        mouse_pos = self.pixmap_2.mapFromGlobal(QCursor.pos())
        return self.pixmap_2.rect().contains(mouse_pos)

    def moveEvent(self, event):
        # 主窗口移动时，让两个技能图片窗口保持相对位置
        super().moveEvent(event)
        if hasattr(self, 'pixmap_1'):
            self.pixmap_1.move(self.pos() + self.skill_1_offset)
        if hasattr(self, 'pixmap_2'):
            self.pixmap_2.move(self.pos() + self.skill_2_offset)
        self.chat_wait.move(self.pos() + QPoint(280, 0))

        self.chatbox.move(self.pos())

        self.pixmap_1.current_pos = self.pixmap_1.pos()
        self.pixmap_1.move_to_pos = self.pixmap_1.pos() - QPoint(2,8)

        self.pixmap_2.current_pos = self.pixmap_2.pos()
        self.pixmap_2.move_to_pos = self.pixmap_2.pos() - QPoint(2,8)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        # 左键按住时：允许拖动主窗口，或在长按状态下检测技能图片悬停
        
        if self.lock_moving :
            return
                
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self.drag_enabled : 
                current_pos = event.globalPosition().toPoint()
                if self.press_pos is None:
                    return
                if (current_pos - self.press_pos).manhattanLength() > 3 :
                    self.dragging = True
                    self.long_press_timer.stop()
                if self.movie is self.sleep_movie :
                    self.sleep_movie.stop()
                    self.movie = self.original_movie
                    self.original_movie.start()
                    self.none_timer.stop()
                    self.none_action = False
                self.move(current_pos - self.drag_start_pos)
                self.pixmap_1
                event.accept()
            else :
                if self.is_mouse_over_skill_1():
                    self.if_chatting = False
                    self.chat_wait.hide()
                    self.speaking_sound.stop()
                    self.pixmap_1.set_image_light(resource_path('PNG/skill_1.png'))
                    self.pixmap_1.animate_point(self.pixmap_1.move_to_pos)
                else :
                    self.pixmap_1.set_image_dark(resource_path('PNG/skill_1_dark.png'))
                    self.pixmap_1.animate_point(self.pixmap_1.current_pos)
                if self.is_mouse_over_skill_2():
                    self.if_chatting = False
                    self.chat_wait.hide()
                    self.speaking_sound.stop()
                    self.pixmap_2.set_image_light(resource_path('PNG/skill_2.png'))
                    self.pixmap_2.animate_point(self.pixmap_2.move_to_pos)
                else:
                    self.pixmap_2.set_image_dark(resource_path('PNG/skill_2_dark.png'))
                    self.pixmap_2.animate_point(self.pixmap_2.current_pos)

    # 鼠标方位判定
    def mousePos(self, event: QMouseEvent) :
        mouse_pos = event.position().toPoint()

        # 判断鼠标是否位于头部部分
        head_rect = QRect(0, self.height()//7, self.width(), 30)
        self.head_at_pos = head_rect.contains(mouse_pos)

    def mousePressEvent(self, event: QMouseEvent):
        # 右键打开菜单，左键开始记录拖动和长按
        if event.button() == Qt.MouseButton.RightButton:
            self.show_menu(event.globalPosition().toPoint())
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton:      
            self.drag_start_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            self.press_pos = event.globalPosition().toPoint()
            if self.skill_able :
                self.dragging = False
                self.long_pressed = False
                self.long_press_timer.start()

            if self.lock_moving :
                self.speaking_sound.stop()
                event.accept()
                return
        
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.press_pos = None

        if self.lock_moving :
            return
        
        # 松开左键时结束拖动或长按，并关闭技能图片窗口
        self.none_timer.start()
        if event.button() == Qt.MouseButton.LeftButton:
            self.long_press_timer.stop()
            if not self.dragging and not self.long_pressed:
                self.mousePos(event)
                self.gif_clicked()
            self.skill = False
            self.long_pressed = False
            self.giddy_mode = False
            self.drag_enabled = True

        # 选择技能
            if self.is_mouse_over_skill_1():
                if self.movie is not self.original_movie:
                    return
                
                self.movie.stop()
                self.movies_stop()
                self.skill1_movie.jumpToFrame(0)
                self.movie = self.skill1_movie
                self.skill1_movie.start()

                self.skill1_playsound()

            if self.is_mouse_over_skill_2():
                if self.movie is not self.original_movie:
                    return

                self.movie.stop()
                self.movies_stop()
                self.skill2_movie.jumpToFrame(0)
                self.movie = self.skill2_movie
                self.skill2_movie.start()

                self.skill2_playsound()

            self.pixmap_1.fade_out()
            self.pixmap_2.fade_out()
            self.pixmap_1.set_image_dark(resource_path('PNG/skill_1_dark.png'))
            self.pixmap_1.animate_point(self.pixmap_1.current_pos)                    
            self.pixmap_2.set_image_dark(resource_path('PNG/skill_2_dark.png'))
            self.pixmap_2.animate_point(self.pixmap_2.current_pos)

            self.dragging = False
            self.drag_start_pos = QPoint()
            event.accept()

    def movies_stop(self):
        self.movies = (
            self.original_movie, self.click_movie, self.giddy_movie, self.born_movie, 
            self.sleep_movie, self.skill1_movie, self.skill2_movie, self.lock_movie,
        )
        for movie in self.movies:
            movie.stop()

# 待机监测
    def noneActionTimer(self):
        if self.lock_moving :
            return
        
        if self.movie is not self.sleep_movie and self.sleep_able :
            self.none_action = True
            self.movie.stop()
            self.sleep_movie.jumpToFrame(0)
            self.movie = self.sleep_movie
            self.none_timer.stop()
            self.speaking_sound.stop()
            self.chat_wait.hide()
            self.if_chatting = False
            self.sleep_movie.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.movie.currentPixmap())

    def refresh_audio_output(self):
        self.speaking_output.setDevice(self.audio_devices.defaultAudioOutput())

    def restore_original(self):
        # 停止临时动画并恢复播放待机动画
        if self.movie not in (self.click_movie,self.giddy_movie,self.born_movie, self.sleep_movie, self.skill1_movie, self.skill2_movie, self.lock_movie):
            return

        if self.lock_moving :
            return
        
        self.restore_timer.stop()
        self.giddy_timer.stop()
        self.movies_stop()
        self.none_action = False
        self.movie = self.original_movie
        self.original_movie.start()
        self.none_timer.start()
        self.setEnabled(True)

    def role_change(self):
        global character

        if self.lock_moving :
            return
        
        new_character = self.individual.chosen_character
        if not new_character:
            return
        if new_character == character:
            return

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        role_path = os.path.join(base_path, 'ArcanistsHuman', new_character)
        gif_names = (
            'idle.gif', 'hit.gif', 'giddy.gif', 'born.gif',
            'sleep.gif', 'skill_1.gif', 'skill_2.gif', 'lock.gif',
        )
        required_paths = [
            os.path.join(role_path, 'GIF', name) for name in gif_names
        ]
        required_paths.extend(
            os.path.join(role_path, 'PNG', name)
            for name in (
                'skill_1.png', 'skill_1_dark.png',
                'skill_2.png', 'skill_2_dark.png',
            )
        )
        required_paths.extend(
            os.path.join(role_path, 'WAV', name)
            for name in (
                'born_1.wav', 'born_2.wav', 'born_3.wav',
                'morning_1.wav', 'morning_2.wav', 'night_1.wav', 'night_2.wav',
            )
        )
        missing_path = next(
            (path for path in required_paths if not os.path.isfile(path)), None
        )
        if missing_path:
            QMessageBox.warning(
                self,
                '角色切换失败',
                f'角色“{new_character}”缺少资源：{os.path.basename(missing_path)}',
            )
            return

        for timer in (self.restore_timer, self.giddy_timer, self.none_timer, self.long_press_timer):
            timer.stop()
        
        self.movies_stop()
        self.speaking_sound.stop()
        self.pixmap_1.hide()
        self.pixmap_2.hide()
        self.pixmap_1.fade_out_animation.stop()
        self.pixmap_2.fade_out_animation.stop()

        character = new_character
        settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        settings.setValue('character', new_character)
        settings.sync()

        for movie, name in zip(self.movies, gif_names):
            movie.setFileName(resource_path(os.path.join('GIF', name)))
            movie.jumpToFrame(0)

        self.pixmap_1.set_image_dark(resource_path('PNG/skill_1_dark.png'))
        self.pixmap_2.set_image_dark(resource_path('PNG/skill_2_dark.png'))
        self.chat_1_lst = [
            [resource_path('WAV/morning_1.wav'), resource_path('WAV/morning_2.wav')],
            [resource_path('WAV/night_1.wav'), resource_path('WAV/night_2.wav')],
        ]
        self.if_chatting = False
        self.chat_wait.hide()
        self.none_action = False
        self.long_pressed = False
        self.drag_enabled = True
        self.setEnabled(True)
        self.gif_start()

    def skill1_playsound(self):
        a_choice = random.randint(0,1)
        if a_choice == 0 :
            sound_path = resource_path('WAV/skill_1_part1.wav')
        elif a_choice == 1 :
            sound_path = resource_path('WAV/skill_1_part2.wav')            
        if not os.path.exists(sound_path):
            return

        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def skill2_playsound(self):
        a_choice = random.randint(0,1)
        if a_choice == 0 :
            sound_path = resource_path('WAV/skill_2_part1.wav')
        elif a_choice == 1 :
            sound_path = resource_path('WAV/skill_2_part2.wav')            
        if not os.path.exists(sound_path):
            return

        self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.speaking_sound.play()

    def setSleepTime_5min(self):
        if self.sleep_time != 300000 :
            self.sleep_time = 300000
            self.sleep_able = True
            self.none_timer.setInterval(int(self.sleep_time))
        if self.movie is not self.born_movie:
            self.none_timer.stop()
            self.sleep_movie.stop()
            self.none_action = False
            self.movie = self.original_movie
            self.original_movie.start()
            self.none_timer.start()

    def setSleepTime_10min(self):
        if self.sleep_time != 600000 :
            self.sleep_time = 600000
            self.sleep_able = True
            self.none_timer.setInterval(int(self.sleep_time))
        if self.movie is not self.born_movie:
            self.none_timer.stop()
            self.none_timer.stop()
            self.sleep_movie.stop()
            self.none_action = False
            self.movie = self.original_movie
            self.original_movie.start()
            self.none_timer.start()

    def setSleepTime_30min(self):
        if self.sleep_time != 1800000 :
            self.sleep_time = 1800000
            self.sleep_able = True
            self.none_timer.setInterval(int(self.sleep_time))
        if self.movie is not self.born_movie:
            self.none_timer.stop()
            self.none_timer.stop()
            self.sleep_movie.stop()
            self.none_action = False
            self.movie = self.original_movie
            self.original_movie.start()
            self.none_timer.start()

    def setSleepTime_1h(self):
        if self.sleep_time != 3600000 :
            self.sleep_time = 3600000
            self.sleep_able = True
            self.none_timer.setInterval(int(self.sleep_time))
        if self.movie is not self.born_movie:
            self.none_timer.stop()
            self.none_timer.stop()
            self.sleep_movie.stop()
            self.none_action = False
            self.movie = self.original_movie
            self.original_movie.start()
            self.none_timer.start()

    def setSleepTime_2h(self):
        if self.sleep_time != 7200000 :
            self.sleep_time = 7200000
            self.sleep_able = True
            self.none_timer.setInterval(int(self.sleep_time))
        if self.movie is not self.born_movie:
            self.none_timer.stop()
            self.none_timer.stop()
            self.sleep_movie.stop()
            self.none_action = False
            self.movie = self.original_movie
            self.original_movie.start()
            self.none_timer.start()

    def setSleepTime_5h(self):
        if self.sleep_time != 18000000 :
            self.sleep_time = 18000000
            self.sleep_able = True
            self.none_timer.setInterval(int(self.sleep_time))
        if self.movie is not self.born_movie:
            self.none_timer.stop()
            self.none_timer.stop()
            self.sleep_movie.stop()
            self.none_action = False
            self.movie = self.original_movie
            self.original_movie.start()
            self.none_timer.start()

    def setSleepTime_Never(self):
        if self.sleep_time != 0 :
            self.sleep_time = 0
            self.none_timer.stop()
        if self.sleep_able :
            self.sleep_able = False
        if self.movie is not self.born_movie:
            self.none_timer.stop()
            self.sleep_movie.stop()
            self.none_action = False
            self.movie = self.original_movie
            self.original_movie.start()

    def show_menu(self, position):
        if self.movie is self.born_movie :
            return

        if self.pixmap_1.isVisible():
            self.pixmap_1.fade_out()
        if self.pixmap_2.isVisible():
            self.pixmap_2.fade_out()

        if self.lock_moving :
            menu = QMenu(self)
            unlock_action = menu.addAction('解锁')
            individual_action = menu.addAction('自定义')
            app_action = menu.addAction('组件')
            app_action.setCheckable(True)
            app_action.setChecked(self.app_on)
            menu.addSeparator()
            close_action = menu.addAction('退出')
            selected_action = menu.exec(position)
            if selected_action == unlock_action : 
                self.idle_check_timer.start(1000)
                self.lock_moving = False
                self.lock_btn.btn_lock.setChecked(False)
                self.speaking_sound.stop()
                self.clockbox_timer.stop()
                self.music_window.Pause = True
                self.music_window.pause_song.setText(chr(0xE102))
                self.music_window.rotation_timer.stop()
                self.music_window.song_sound.pause()
                self.small_app.close()
                self.lock_btn.close()
                self.restore_original()
                self.individual.lock_event = self.lock_moving
            if selected_action == individual_action :
                self.individual.show()
            if selected_action == app_action :
                self.lock_btn.close()
                self.small_app.close()
                self.lock_btn.btn_lock.setChecked(False)
                self.app_on = not self.app_on
                if self.app_on :
                    self.clockbox_timer.start()
                elif not self.app_on :
                    self.clockbox_timer.stop()
                    self.music_window.Pause = True
                    self.music_window.pause_song.setText(chr(0xE102))
                    self.music_window.rotation_timer.stop()
                    self.music_window.song_sound.pause()
            if selected_action == close_action : 
                self.exit_application()

        
        elif not self.lock_moving :
            # 显示右键菜单
            menu = QMenu(self)
            reload_action = menu.addAction('重新入场')
            nonetime_menu = menu.addMenu('休眠时间')
            interact_menu = menu.addMenu('互动功能')
            lock_action = menu.addAction('锁定')
            individual_action = menu.addAction('自定义')

            skill_action = interact_menu.addAction('技能栏')
            chat_action = interact_menu.addAction('聊天栏')
            idle_chat_action = interact_menu.addAction('待机语音')

            skill_action.setCheckable(True)
            chat_action.setCheckable(True)
            idle_chat_action.setCheckable(True)
            
            skill_action.setChecked(self.skill_able)
            chat_action.setChecked(self.chat_able)
            idle_chat_action.setChecked(self.idle_chat_able)

            skill_action.triggered.connect(self.switch_skill)
            chat_action.triggered.connect(self.switch_chat)
            idle_chat_action.triggered.connect(self.switch_idle_chat)

            sleep_time_group = QActionGroup(self)
            sleep_time_group.setExclusive(True)

            sleep_5min_action = nonetime_menu.addAction('5min后')
            sleep_10min_action = nonetime_menu.addAction('10min后')
            sleep_30min_action = nonetime_menu.addAction('30min后')
            sleep_1h_action = nonetime_menu.addAction('1h后')
            sleep_2h_action = nonetime_menu.addAction('2h后')
            sleep_5h_action = nonetime_menu.addAction('5h后')
            sleep_never_action = nonetime_menu.addAction('永不')

            sleep_5s_action = nonetime_menu.addAction('5s后')
            sleep_actions = (sleep_5min_action, sleep_10min_action, sleep_30min_action, 
                            sleep_1h_action, sleep_2h_action, sleep_5h_action, 
                            sleep_never_action, sleep_5s_action)

            for action in sleep_actions:
                action.setCheckable(True)
                sleep_time_group.addAction(action)

            sleep_5min_action.setChecked(self.sleep_time == 300000)
            sleep_10min_action.setChecked(self.sleep_time == 600000)
            sleep_30min_action.setChecked(self.sleep_time == 1800000)
            sleep_1h_action.setChecked(self.sleep_time == 3600000)
            sleep_2h_action.setChecked(self.sleep_time == 7200000)
            sleep_5h_action.setChecked(self.sleep_time == 18000000)
            sleep_never_action.setChecked(self.sleep_time == 0)

            sleep_5s_action.setChecked(self.sleep_time == 5000)

            sleep_5min_action.triggered.connect(self.setSleepTime_5min)
            sleep_10min_action.triggered.connect(self.setSleepTime_10min)
            sleep_30min_action.triggered.connect(self.setSleepTime_30min)
            sleep_1h_action.triggered.connect(self.setSleepTime_1h)
            sleep_2h_action.triggered.connect(self.setSleepTime_2h)
            sleep_5h_action.triggered.connect(self.setSleepTime_5h)
            sleep_never_action.triggered.connect(self.setSleepTime_Never)

            menu.addSeparator()
            close_action = menu.addAction('退出')
            selected_action = menu.exec(position)
            if selected_action == close_action :
                self.exit_application()
            if selected_action == reload_action : 
                self.gif_start()
                self.chat_wait.hide()
                self.if_chatting = True
            if selected_action == individual_action :
                self.individual.show()
            if selected_action == lock_action :
                self.idle_check_timer.stop()
                self.lock_moving = True
                self.chat_wait.hide()
                self.restore_timer.stop()
                self.giddy_timer.stop()
                self.movies_stop()
                self.none_timer.stop()
                self.none_action = False
                self.movie.stop()
                self.movie = self.lock_movie
                self.clockbox_timer.start()
                self.lock_movie.start()
                self.app_pos_refresh()
                self.individual.lock_event = self.lock_moving
                if self.app_index == 0:
                    self.small_app.move(self.clock_pos)
                elif self.app_index == 1:
                    self.small_app.move(self.music_pos)
                self.lock_btn.move(self.pos()+QPoint(170,30))
                self.app_in_ani.setStartValue(0.0)
                self.speaking_sound.stop()
                sound_path = resource_path('WAV/lock.wav')
                if not os.path.exists(sound_path):
                    return

                self.speaking_sound.setSource(QUrl.fromLocalFile(sound_path))
                self.speaking_sound.play()
    
    def switch_small_app(self, step):
        if len(self.app_lst) < 2:
            return

        old_app = self.small_app
        app_pos = old_app.pos()
        self.app_off_ani.setStartValue(app_pos)
        self.app_off_ani.setEndValue(app_pos + QPoint(50, 0))
        self.app_in_ani.stop()
        self.app_out_ani.stop()
        self.app_off_ani.stop()
        self.app_out_ani.setStartValue(old_app.windowOpacity())
        self.app_out_ani.start()
        self.app_off_ani.start()

        self.app_index = (self.app_index + step) % len(self.app_lst)
        self.small_app = self.app_lst[self.app_index]
        self.app_in_ani, self.app_out_ani = self.app_in_ani_lst[self.app_index], self.app_out_ani_lst[self.app_index]
        self.app_off_ani = self.app_off_ani_lst[self.app_index]

        self.app_in_ani.stop()
        self.app_out_ani.stop()
        self.app_off_ani.stop()
        if self.app_index == 0:
            self.small_app.move(self.clock_pos)
        elif self.app_index == 1:
            self.small_app.move(self.music_pos)
        self.small_app.stackUnder(self)
        self.small_app.show()
        self.small_app.lower()
        self.raise_()
        self.lock_btn.raise_()
        self.app_in_ani.setStartValue(0.0)
        self.app_in_ani.start()

    def switch_skill(self):
        self.skill_able = not self.skill_able

    def switch_chat(self):
        self.chat_able = not self.chat_able

    def switch_idle_chat(self):
        self.idle_chat_able = not self.idle_chat_able

    def exit_application(self):
        tray_icon = self.findChild(QSystemTrayIcon)
        if tray_icon is not None:
            tray_icon.hide()

        app = QApplication.instance()
        if app is not None:
            app.quit()


# 程序入口：创建应用和 GIF 主窗口
if __name__ == "__main__" :
    instance_lock = QLockFile(
        os.path.join(tempfile.gettempdir(), "arcanists_human_desktop_role.lock")
    )
    if not instance_lock.tryLock(0):
        if instance_lock.error() == QLockFile.LockError.LockFailedError:
            sys.exit(0)
        app = QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "启动失败",
            f"无法创建单实例锁文件：{instance_lock.error()}",
        )
        sys.exit(1)

    app = QApplication(sys.argv)
    try:
        window = InteractiveGif(
            resource_path('GIF/idle.gif'),
            resource_path('GIF/hit.gif'),
            resource_path('GIF/giddy.gif'),
            resource_path('GIF/born.gif'),
            resource_path('GIF/sleep.gif'),
            resource_path('GIF/skill_1.gif'),
            resource_path('GIF/skill_2.gif'),
            resource_path('GIF/lock.gif'),
        )

        tray_icon = QSystemTrayIcon(QIcon(resource_icon()), window)
        tray_icon.setToolTip('桌面角色')

        tray_menu = QMenu(window)
        exit_action = tray_menu.addAction('退出')

        def show_window():
            window.show()
            window.raise_()
            window.activateWindow()

        def handle_tray_activation(reason):
            if reason in (
                QSystemTrayIcon.ActivationReason.Trigger,
                QSystemTrayIcon.ActivationReason.DoubleClick,
            ):
                show_window()

        exit_action.triggered.connect(window.exit_application)
        tray_icon.setContextMenu(tray_menu)
        tray_icon.activated.connect(handle_tray_activation)
        tray_icon.show()

        window.show()
        sys.exit(app.exec())
    finally:
        instance_lock.unlock()