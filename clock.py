from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QPushButton, QLabel, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt
import sys
from datetime import datetime

# 时钟窗口：以悬浮透明样式显示当前时间和日期。
class Clock(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        main_layout = QHBoxLayout()
        side_layout = QHBoxLayout()
        all_layout = QVBoxLayout()
        
        self.week_count = ['星期一','星期二','星期三','星期四','星期五','星期六','星期日']
        
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.time_update)
        self.clock_timer.start(125)
        
        btn_hour = QPushButton('00')
        btn_min = QPushButton('00')
        btn_sec = QPushButton('00')
        self.btn_date = QPushButton('1900   -   01   -   01   星期一')
        self.time_lst = [btn_hour, btn_min, btn_sec]
        self.time_update()
        for time in self.time_lst:
            time.setDisabled(True)
            time.setFixedSize(80,90)
            time.setStyleSheet("""
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 10);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 6px;
                padding: 4px 10px;

                /*字体设置*/
                font-family: "Arial Rounded MT Bold", "Arial", sans-serif;
                font-size: 48px;
                font-weight: noraml;
                color: white;
            }
            """)
            main_layout.addWidget(time)

        all_layout.addLayout(main_layout)
        self.btn_date.setDisabled(True)
        self.btn_date.setFixedSize(260,30)
        self.btn_date.setStyleSheet("""
        QPushButton:disabled {
            background-color: rgba(255, 255, 255, 10);
            border: 1px solid rgba(255, 255, 255, 20);
            border-radius: 6px;
            padding: 2px 10px;

            /*字体设置*/
            font-family: "Arial Rounded MT Bold", "Arial", sans-serif;
            font-size: 15px;
            font-weight: normal;
            color: white;
        }
        """)
        side_layout.addStretch(1)
        side_layout.addWidget(self.btn_date)
        side_layout.addStretch(1)
        
        all_layout.addLayout(side_layout)

        self.setLayout(all_layout)
        self.setFixedSize(300,200)
        self.move(500,500)

    def time_update(self):
        now = datetime.now()
        sys_time_lst = [now.hour, now.minute, now.second]
        today_weekday = self.week_count[now.weekday()]
        self.hour = now.hour
        self.date_time = now.strftime("%Y   -   %m   -   %d   ") + f"{today_weekday}"
        
        for time, sys_time in zip(self.time_lst, sys_time_lst):            
            display_time = f"{sys_time:02d}"
            if time.text() != display_time:
                time.setText(display_time)

        if self.btn_date.text() != self.date_time :
            self.btn_date.setText(f'{self.date_time}')


if __name__ == "__main__" :
    app = QApplication(sys.argv)
    window = Clock()
    window.show()
    sys.exit(app.exec()) 