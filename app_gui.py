import getpass
import datetime
import tkinter as tk
from tkinter import ttk
from tkinter import font

from tkcalendar import DateEntry
from ctypes import windll
windll.shcore.SetProcessDpiAwareness(1)


class MainGui:
    def __init__(self):
        self.root = tk.Tk()

        self.root.title("BC受付自動印刷")

        self.root.resizable(False, False)

        self.date_picker_font = font.Font(family="Yu Gothic", size=9)

        self.image_path = "python_logo.png"

        self.setup_style()

        self.create_frames()

        self.create_widgets()

        self.arrange_widgets()

    def setup_style(self):
        """スタイル設定"""
        self.style = ttk.Style(self.root)
        self.style.theme_use("vista")
        self.style.theme_settings("vista", {
            "White.TFrame": {
                "configure": {"background": "#ffffff"}
            },
            "Gray.TFrame": {
                "configure": {"background": "#f0f0f0"}
            },
            "TCheckbutton": {
                "configure": {"background": "#ffffff"}
            },
            "TLabel": {
                "configure": {"background": "#ffffff"}
            },
        })

    def create_frames(self):
        """フレーム作成"""
        self.frame1 = ttk.Frame(self.root, style="White.TFrame")
        self.frame1.pack(fill="x", ipadx=10, ipady=7)

        self.frame2 = ttk.Frame(self.root, style="Gray.TFrame")
        self.frame2.pack(fill="x", padx=22, pady=18)

    def create_widgets(self):
        """ウィジェット作成"""
        # ロゴ画像
        self.canvas = tk.Canvas(self.frame1, width=60, height=60,
                                highlightthickness=0, background="#ffffff")
        self.img = tk.PhotoImage(file=self.image_path)
        self.canvas.create_image(31, 31, image=self.img)

        # パスワード入力欄
        self.input_pass = tk.Entry(self.frame1, show="●",
                                   relief="solid", borderwidth=0,
                                   highlightthickness=1,
                                   highlightbackground="#8c8c8c",
                                   highlightcolor="#0078d4")
        self.input_pass.focus_set()

        # 日付選択欄の共通設定
        self.date_entry_config = {
            "background": "#f0f0f0",
            "foreground": "#000000",
            "borderwidth": 2,
            "bordercolor": "#ffffff",
            "headersbackground": "#ffffff",
            "weekendbackground": "#ffffff",
            "weekendforeground": "#000000",
            "othermonthbackground": "#ffffff",
            "othermonthwebackground": "#ffffff",
            "date_pattern": "yyyy/mm/dd",
            "firstweekday": "sunday",
            "showweeknumbers": False,
            "locale": "ja_JP",
            "state": "readonly",
            "mindate": today,
            "maxdate": today + datetime.timedelta(days=8),
            "font": self.date_picker_font,
        }

        # 日付選択欄
        self.start_date = DateEntry(self.frame1, **self.date_entry_config)
        self.end_date = DateEntry(self.frame1, **self.date_entry_config)

        # チェックボックス
        self.checkbox_texts = ["FSP", "#7", "#8", "基材識別票"]
        self.checkbox_vars = []     # チェックボックスの状態を保持する変数
        self.checkboxes = []        # チェックボックスのウィジェットを保持するリスト
        for text in self.checkbox_texts:
            var = tk.IntVar(value=1)    # デフォルトで選択状態
            checkbox = ttk.Checkbutton(self.frame1, text=text, variable=var)
            self.checkbox_vars.append(var)
            self.checkboxes.append(checkbox)

        # ラベル
        self.labels = [
            (ttk.Label(self.frame1, text=greet(userId)), 0, 1, 4, "w"),
            (ttk.Label(self.frame1, text="パスワード："), 1, 0, None, "e"),
            (ttk.Label(self.frame1, text="印刷範囲："), 2, 0, None, "e"),
            (ttk.Label(self.frame1, text="―"), 2, 1, 4, None),
        ]

        # 実行ボタン
        self.button = ttk.Button(self.frame2, text="実行", width=13,
                                 default="active", state=tk.DISABLED)
        # ボタンクリック時のイベントハンドラを設定
        self.button.config(command=self.execute_action)

    def arrange_widgets(self):
        """ウィジェット配置"""
        # キャンバス配置
        self.canvas.grid(row=0, column=0, padx=7)

        # 入力欄配置
        self.input_pass.grid(row=1, column=1, columnspan=4, sticky="ew",
                             padx=3, pady=(1, 18), ipady=1)
        self.input_pass.bind("<Return>",
                             lambda event: self.move_focus(self.start_date))

        # 日付選択欄配置
        self.start_date.grid(row=2, column=1, columnspan=4,
                             sticky="w", padx=3, pady=(0, 14))
        self.end_date.grid(row=2, column=1, columnspan=4,
                           sticky="e", padx=3, pady=(0, 14))

        # チェックボックス配置
        for i, checkbox in enumerate(self.checkboxes):
            checkbox.grid(row=3, column=i+1, sticky="w")

        # ラベル配置
        for label, row, col, colspan, sticky in self.labels:
            padx_value = (24, 0) if row == 1 else 0
            pady_value = (14, 13) if row == 0 else (0, 14)
            label.grid(row=row, column=col, columnspan=colspan, sticky=sticky,
                       padx=padx_value, pady=pady_value)

        # ボタン配置
        self.button.pack(side="right")

    def execute_action(self):
        """実行ボタンが押されたときの処理"""
        password = self.input_pass.get()
        start_date_value = self.start_date.get_date()
        end_date_value = self.end_date.get_date()

        # チェックボックスの状態を取得（選択されているかどうか）
        selected_options = []
        for i, checkbox in enumerate(self.checkboxes):
            if str(checkbox.instate(['selected'])) == 'True':
                selected_options.append(self.checkbox_texts[i])

        # ウィジェットの値をコマンドラインに表示（デバッグ用）
        print(f"パスワード: {password}")
        print(f"開始日: {start_date_value}")
        print(f"終了日: {end_date_value}")
        print(f"選択オプション: {selected_options}")

    def move_focus(event, next_widget):
        """フォーカス移動イベントハンドラ"""
        # フォーカスを次のウィジェットに移動
        next_widget.focus_set()

    def run(self):
        """アプリケーション実行"""
        self.root.mainloop()


def greet(name):
    """ユーザーに挨拶する関数"""
    message = (f"{name}さん、おつかれさまです！\n"
               "BC受付のパスワードと印刷範囲を入力してください。")
    print(message)
    return message


userId = getpass.getuser()

today = datetime.date.today()

# アプリケーション実行
app = MainGui()
app.run()
