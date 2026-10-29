from PyQt6.QtWidgets import QApplication, QPushButton, QWidget, QGridLayout, QLabel, QSlider, QGraphicsOpacityEffect, QHBoxLayout
import sys
import os
import random
from pathlib import Path
from PyQt6.QtGui import QPixmap, QPainter, QFont, QCursor, QPainterPath
from PyQt6.QtCore import QEvent, QPropertyAnimation, QEasingCurve, QPoint, QTimer, Qt, pyqtSignal, QUrl, QRectF, QFileSystemWatcher
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer, QMediaMetaData, QMediaDevices

# 音乐界面的提示浮窗：提示当前没有放入歌曲。
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
        self.hint_info = QPushButton('还没有放入歌曲哦~')
        self.hint_info.setDisabled(True)
        self.hint_info.setFixedSize(170, 30)
        self.hint_info.setStyleSheet("""
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 10);
                color: white;
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 6px;
                padding: 4px 10px;

                font-size: 14px
            }
            """)
        self.btn_layout.addWidget(self.hint_info)
        self.setLayout(self.btn_layout)
        self.setFixedSize(200, 50)
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

# 可双击的按钮：用于播放列表中的歌曲切换。
class DoubleClickButton(QPushButton):
    doubleClicked = pyqtSignal()

    def __init__(self, text='', parent=None):
        super().__init__(text, parent)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)


# 转盘封面：负责旋转唱片和绘制圆形封面效果。
class RotatingImageLabel(QLabel):
    def __init__(self, pixmap):
        super().__init__()
        self.pixmap_image = pixmap
        self.cover_pixmap = QPixmap()
        self.rotation_angle = 0
        self.setFixedSize(pixmap.size())
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: transparent;")

    def set_cover_image(self, image):
        cover_size = round(min(self.width(), self.height()) * 0.8)
        cover = QPixmap.fromImage(image).scaled(
            cover_size,
            cover_size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        offset_x = (cover.width() - cover_size) // 2
        offset_y = (cover.height() - cover_size) // 2
        self.cover_pixmap = cover.copy(offset_x, offset_y, cover_size, cover_size)
        self.update()

    def clear_cover_image(self):
        self.cover_pixmap = QPixmap()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.rotation_angle)
        painter.translate(-self.pixmap_image.width() / 2, -self.pixmap_image.height() / 2)
        painter.drawPixmap(0, 0, self.pixmap_image)

        if not self.cover_pixmap.isNull():
            cover_size = self.cover_pixmap.width()
            cover_rect = QRectF(
                (self.width() - cover_size) / 2,
                (self.height() - cover_size) / 2,
                cover_size,
                cover_size,
            )
            cover_path = QPainterPath()
            cover_path.addEllipse(cover_rect)

            hole_size = cover_size * 0.08
            hole_path = QPainterPath()
            hole_path.addEllipse(QRectF(
                cover_rect.center().x() - hole_size / 2,
                cover_rect.center().y() - hole_size / 2,
                hole_size,
                hole_size,
            ))

            painter.save()
            painter.setClipPath(cover_path.subtracted(hole_path))
            painter.drawPixmap(cover_rect, self.cover_pixmap, QRectF(self.cover_pixmap.rect()))
            painter.restore()

# 跑马灯标签：滚动显示过长的歌曲名。
class MarqueeLabel(QLabel):
    def __init__(self, text='', parent=None):
        super().__init__('', parent)
        self._scroll_offset = 0
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setInterval(30)
        self._scroll_timer.timeout.connect(self.advance_scroll)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setText(text)

    def setText(self, text):
        super().setText(str(text))
        self._scroll_offset = 0
        if hasattr(self, '_scroll_timer'):
            if self.fontMetrics().horizontalAdvance(self.text()) > self.contentsRect().width():
                self._scroll_timer.start()
            else:
                self._scroll_timer.stop()
        self.update()

    def advance_scroll(self):
        text_width = self.fontMetrics().horizontalAdvance(self.text())
        self._scroll_offset = (self._scroll_offset + 1) % (text_width + 36)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setClipRect(self.contentsRect())
        painter.setPen(self.palette().color(self.foregroundRole()))

        text = self.text()
        metrics = self.fontMetrics()
        text_width = metrics.horizontalAdvance(text)
        content_rect = self.contentsRect()

        if text_width <= content_rect.width():
            painter.drawText(content_rect, Qt.AlignmentFlag.AlignCenter, text)
            return

        baseline = content_rect.top() + (content_rect.height() - metrics.height()) // 2 + metrics.ascent()
        x = content_rect.left() - self._scroll_offset
        painter.drawText(x, baseline, text)
        painter.drawText(x + text_width + 36, baseline, text)

# 主播放器界面：展示唱片、播放控制和歌曲列表。
class CD_show(QWidget):
    def __init__(self):
        super().__init__()
        # 唱片贴图路径
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        CD_path = os.path.join(base_path, 'ArcanistsHuman', 'component_pic', 'CD.png')

        self.songs_dir = Path(__file__).resolve().parent / "songs"

        main_layout = QGridLayout()
        main_layout.setVerticalSpacing(10)
        main_layout.setHorizontalSpacing(10)

        font = QFont("Segoe MDL2 Assets")
        font.setPixelSize(18)

        self.song_play_order = 0
        
        # 绘制贴图
        self.pixmap_music = QPixmap(CD_path)
        self.pixmap_music = self.pixmap_music.scaled(
            170,170,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
            )
        self.label_music = RotatingImageLabel(self.pixmap_music)

        # 扫描歌曲列表
        self.song_lst = self.scan_songs()
        if len(self.song_lst) > 0 :
            self.current_song = self.song_lst[0]
            self.current_song_index = self.song_lst.index(self.current_song)
        
        # 歌曲表单键
        self.list_song = DoubleClickButton(chr(0xE700))
        self.list_song.setFont(font)
        self.list_song.doubleClicked.connect(lambda: os.startfile(self.songs_dir))

        # 上一首
        self.last_song = QPushButton(chr(0xE100))
        self.last_song.clicked.connect(self.last_play)

        # 下一首
        self.next_song = QPushButton(chr(0xE101))
        self.next_song.clicked.connect(self.next_play)

        # 暂停
        self.Pause = True
        self.pause_song = QPushButton(chr(0xE102))
        self.pause_song.clicked.connect(self.pause_start)

        # 播放顺序
        self.order_song = QPushButton(chr(0xE8EE))
        self.order_song.setFont(font)
        self.order_song.clicked.connect(self.song_ordering)

        # 声音键
        self.volume_song = QPushButton(chr(0xE994))
        self.volume_song.setFont(font)
        self.volume_song.clicked.connect(self.volume_zero)

        # 音量条
        self.volume_set = QSlider(Qt.Orientation.Vertical)
        self.volume_set.setRange(0, 100)
        self.volume_set.setValue(50)
        self.volume_set.setTickInterval(10)
        self.volume_set.setFixedSize(40, 156)
        self.volume_set.setStyleSheet("""
        QSlider {
            background: rgba(255, 255, 255, 10);
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 20);
            padding: 20px;
        }
        QSlider::groove:vertical {
            width: 6px;
            background: rgba(255, 255, 255, 255);
            border-radius: 3px;    
        }
        QSlider::handle:vertical {
            background: rgba(255, 255, 255, 255);
            height: 10px;
            margin: 0 -6px;
            border-radius: 3px;
        }
        QSlider::sub-page:vertical {
            background: rgba(100, 100, 100, 255);
            border-radius: 3px;
        }
        """)
        self.volume_set.setTickPosition(QSlider.TickPosition.TicksLeft)

        self.volume_set.valueChanged.connect(self.set_volume)

        # 音量条动画
        self.effect = QGraphicsOpacityEffect(self.volume_set)
        self.volume_set.setGraphicsEffect(self.effect)
        self.volume_appear = QPropertyAnimation(self.effect, b'opacity', self.volume_set)
        self.volume_appear.setDuration(200)
        self.volume_appear.setEndValue(1.0)
        self.volume_appear.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.volume_disappear = QPropertyAnimation(self.effect, b'opacity', self.volume_set)
        self.volume_disappear.setDuration(200)
        self.volume_disappear.setEndValue(0.0)
        self.volume_disappear.setEasingCurve(QEasingCurve.Type.InCubic)
        
        self.effect.setOpacity(0.0)

        self.volume_song.installEventFilter(self)
        self.volume_set.installEventFilter(self)
        
        # 音量显示
        self.volume_show = QPushButton(str(self.volume_set.value()))
        self.volume_show.setDisabled(True)
        self.volume_show.setStyleSheet("""
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 10);
                color: white;
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 6px;
                padding: 4px 10px;
            }
            """)
        self.volume_show.hide()
        self.volume_set.sliderReleased.connect(self.volume_show.hide)

        # 曲名显示
        self.title_song = MarqueeLabel('')
        self.title_song.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 10);
                color: white;
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 6px;
                padding: 4px 4px;

                font-size: 15px;
            }
            """)
        self.title_song.setFixedSize(230, 40)

        # 静音前音量存储
        self.volume = 0

        self.song_btns = [self.list_song, self.last_song, self.next_song, self.pause_song, self.order_song, self.volume_song, self.volume_show]

        for btn in self.song_btns :
            if btn == self.list_song:
                btn.setFixedSize(90, 40)
            else:
                btn.setFixedSize(40, 40)
            if btn == self.volume_show:
                btn.setStyleSheet("""
                QPushButton {
                    /*字体设置*/
                    font-size: 12px;
                    font-weight: bold;
                    color: white;
                }
                """)
            else:
                btn.setStyleSheet("""
                QPushButton {
                    /*字体设置*/
                    font-size: 18px;
                    font-weight: bold;
                    color: white;
                }
                """)

        # 排列
        main_layout.addWidget(self.volume_set, 0, 0, 3, 1)
        main_layout.addWidget(self.volume_show, 3, 0)
        main_layout.addWidget(self.list_song, 0, 1, 1, 2)
        main_layout.addWidget(self.last_song, 1, 1)
        main_layout.addWidget(self.next_song, 1, 2)
        main_layout.addWidget(self.pause_song, 2, 2)
        main_layout.addWidget(self.order_song, 2, 1)
        main_layout.addWidget(self.volume_song, 3, 1)
        main_layout.addWidget(self.title_song, 3, 2, 1, 4)
        main_layout.addWidget(self.label_music, 0, 3, 3, 1)
        
        # 转动计时
        self.rotation_angle = 0
        self.rotation_timer = QTimer(self)
        self.rotation_timer.timeout.connect(self.rotate_image)

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.start_pos = QPoint(0,0)
        self.end_pos = QPoint(100,0)

        self.setLayout(main_layout)
        self.adjustSize()

        self.song_output = QAudioOutput(self)
        self.song_output.setVolume(0.5)
        self.audio_devices = QMediaDevices(self)
        self.audio_devices.audioOutputsChanged.connect(self.refresh_audio_output)
        self.song_sound = QMediaPlayer(self)
        self.song_sound.setAudioOutput(self.song_output)

        # 接续播放
        self.song_sound.mediaStatusChanged.connect(self.on_status_changed)

        # 随机播放位数列表，用-1占位
        self.random_lst = [None for time in range(len(self.song_lst)//2)]
        
        # 读取歌曲信息
        self.song_sound.metaDataChanged.connect(self.update_song_metadata)

        # 实时监测文件夹内容删减
        self.song_watcher = QFileSystemWatcher(self)
        if self.songs_dir.is_dir():
            self.song_watcher.addPath(str(self.songs_dir))
        self.song_watcher.directoryChanged.connect(self.refresh_songs)

        # 空文件夹提示
        self.hint = Hint()
        (self.come_ani, self.leave_ani, self.appear_ani, self.disapp_ani) = self.hint.ani_group
        self.empty_timer = QTimer()
        self.empty_timer.setSingleShot(True)
        self.empty_timer.setInterval(3000)

    def refresh_audio_output(self):
        self.song_output.setDevice(self.audio_devices.defaultAudioOutput())

    def on_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.next_play()

    def last_play(self):
        if not self.song_lst:
            return
        if self.song_play_order == 0 :
            last_music = self.current_song
            self.random_lst.append(last_music)
            self.random_lst.remove(self.random_lst[0])
            self.current_song_index = (self.current_song_index - 1) % len(self.song_lst)
            self.current_song = self.song_lst[self.current_song_index]
        elif self.song_play_order == 1 :
            last_music = self.current_song
            self.random_lst.append(last_music)
            self.random_lst.remove(self.random_lst[0])
            result_lst = [song for song in self.song_lst if song not in self.random_lst]
            self.current_song = random.choice(result_lst)
            self.current_song_index = self.song_lst.index(self.current_song)
        elif self.song_play_order == 2 :
            pass

        self.song_sound.stop()
        
        song_path = self.current_song
        self.song_sound.setSource(QUrl.fromLocalFile(str(song_path)))
        self.song_sound.play()
        if self.Pause :
            self.Pause = False
            self.pause_song.setText(chr(0xE103))
            self.rotation_timer.start(20)

    def eventFilter(self, watched, event):
        if watched in (self.volume_song, self.volume_set):
            if event.type() == QEvent.Type.Enter:
                self.volume_disappear.stop()
                self.volume_appear.stop()
                self.volume_appear.setStartValue(self.effect.opacity())
                self.volume_appear.start()
            elif event.type() == QEvent.Type.Leave:
                self.volume_show.hide()
                QTimer.singleShot(50, self.hide_volume_if_outside)

        return super().eventFilter(watched, event)

    def hide_volume_if_outside(self):
        cursor_pos = QCursor.pos()
        inside_volume = any(
            widget.rect().contains(widget.mapFromGlobal(cursor_pos))
            for widget in (self.volume_song, self.volume_set)
        )
        if inside_volume:
            return

        self.volume_appear.stop()
        self.volume_disappear.stop()
        self.volume_disappear.setStartValue(self.effect.opacity())
        self.volume_disappear.start()

    def next_play(self):
        if not self.song_lst:
            return
        if self.song_play_order == 0 :
            last_music = self.current_song
            self.random_lst.append(last_music)
            self.random_lst.remove(self.random_lst[0])
            self.current_song_index = (self.current_song_index + 1) % len(self.song_lst)
            self.current_song = self.song_lst[self.current_song_index]
        elif self.song_play_order == 1 :
            last_music = self.current_song
            self.random_lst.append(last_music)
            self.random_lst.remove(self.random_lst[0])
            result_lst = [song for song in self.song_lst if song not in self.random_lst]
            self.current_song = random.choice(result_lst)
            self.current_song_index = self.song_lst.index(self.current_song)
        elif self.song_play_order == 2 :
            pass

        self.song_sound.stop()
        
        song_path = self.current_song
        self.song_sound.setSource(QUrl.fromLocalFile(str(song_path)))
        self.song_sound.play()
        if self.Pause :
            self.Pause = False
            self.pause_song.setText(chr(0xE103))
            self.rotation_timer.start(20)

    def rotate_image(self):
        self.rotation_angle = (self.rotation_angle + 2) % 360
        self.label_music.rotation_angle = self.rotation_angle
        self.label_music.update()

    def pause_start(self):
        if not self.song_lst:
            self.hint.show()
            self.hint.start_pos = self.pos() + QPoint((self.width() // 4) + 10, (self.height() // 3) + 10)
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
            self.empty_timer.timeout.connect(self.leave_ani.start)
            self.empty_timer.timeout.connect(self.disapp_ani.start)
            self.leave_ani.finished.connect(self.hint.close)
            return

        state = self.song_sound.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.Pause = True
            self.pause_song.setText(chr(0xE102))
            self.rotation_timer.stop()
            self.song_sound.pause()
            return

        if state == QMediaPlayer.PlaybackState.PausedState:
            self.song_sound.play()
        else:
            song_path = self.current_song
            self.song_sound.setSource(QUrl.fromLocalFile(str(song_path)))
            self.song_sound.play()

        self.Pause = False
        self.pause_song.setText(chr(0xE103))
        self.rotation_timer.start(20)

    def song_ordering(self):
        self.song_play_order += 1
        
        if self.song_play_order >= 3 :
            self.song_play_order = 0
        
        if self.song_play_order == 0 :
            self.order_song.setText(chr(0xE8EE))
        elif self.song_play_order == 1 :
            self.order_song.setText(chr(0xE8B1))
        elif self.song_play_order == 2 :
            self.order_song.setText(chr(0xE8ED))

    def scan_songs(self):
        self.supported = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"}

        return sorted(
            (
                path for path in self.songs_dir.iterdir()
                if path.is_file() and path.suffix.lower() in self.supported
            ),
            key=lambda path: path.name.casefold(),
        )

    def set_volume(self, value):
        self.volume_show.show()
        self.song_output.setVolume(value/100)
        self.volume_show.setText(str(value))

        if self.volume_set.value() >= 70 and self.volume_song.text() is not chr(0xE995):
            self.volume_song.setText(chr(0xE995))
        elif self.volume_set.value() >= 30 and self.volume_song.text() is not chr(0xE994):
            self.volume_song.setText(chr(0xE994))
        elif self.volume_set.value() > 0 and self.volume_song.text() is not chr(0xE993):
            self.volume_song.setText(chr(0xE993))
        elif self.volume_set.value() == 0 and self.volume_song.text() is not chr(0xE992):
            self.volume_song.setText(chr(0xE992))

    def volume_zero(self):
        if self.volume_set.value() == 0 :
            self.volume_set.setValue(self.volume)
        elif self.volume_set.value() > 0 :
            self.volume = self.volume_set.value()
            self.volume_set.setValue(0)

    def update_song_metadata(self):
        metadata = self.song_sound.metaData()

        title = metadata.stringValue(QMediaMetaData.Key.Title)
        artist = metadata.stringValue(QMediaMetaData.Key.ContributingArtist)
        cover = metadata.value(QMediaMetaData.Key.CoverArtImage)
        if cover is None or cover.isNull():
            cover = metadata.value(QMediaMetaData.Key.ThumbnailImage)

        fallback_title = Path(self.song_sound.source().fileName()).stem

        song = (title or fallback_title) + ' - ' + (artist or '未知')
        self.title_song.setText(song)

        if cover is not None and not cover.isNull():
            self.label_music.set_cover_image(cover)
        else:
            self.label_music.clear_cover_image()

    def refresh_songs(self):
        last_len = len(self.song_lst)
        self.song_lst = self.scan_songs()
        now_len = len(self.song_lst)
        dis_len = now_len - last_len
        if dis_len >= 0 :
            for time in range(dis_len):
                self.random_lst.append(None)
        elif dis_len < 0 :
            for time in range(-dis_len):
                self.random_lst.remove(self.random_lst[0])
        self.current_song_index = self.song_lst.index(self.current_song)


if __name__ == "__main__" :
    app = QApplication(sys.argv)
    window = CD_show()
    window.show()
    sys.exit(app.exec())