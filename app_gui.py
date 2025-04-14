import tkinter as tk
from tkinter import ttk

from ctypes import windll

from utils import greet, create_date_list, userId

windll.shcore.SetProcessDpiAwareness(1)


class MainGui:
    def __init__(self):
        self.root = tk.Tk()

        self.root.title("BC受付自動印刷")

        self.root.resizable(False, False)

        self.image_path = "./resources/python_logo.png"

        self.setup_style()

        self.create_frames()

        self.create_widgets()

        self.arrange_widgets()

    def setup_style(self):
        """スタイル設定"""
        self.style = ttk.Style(self.root)
        self.style.theme_use("vista")
        self.style.theme_settings("vista", {
            "Main.TFrame": {
                "configure": {"background": "#ffffff"}
            },
            "Bottom.TFrame": {
                "configure": {"background": "#f0f0f0"}
            },
            "TCheckbutton": {
                "configure": {"background": "#ffffff"}
            },
            "TLabel": {
                "configure": {"background": "#ffffff",
                              "foreground": "#000000"}
            },
            "Progress.TLabel": {
                "configure": {"background": "#f0f0f0",
                              "foreground": "#000000"}
            }
        })

    def create_frames(self):
        """フレーム作成"""
        self.main_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.main_frame.pack(side="top", fill="x", ipadx=10, ipady=7)

        self.bottom_frame = ttk.Frame(self.root, style="Bottom.TFrame")
        self.bottom_frame.pack(side="bottom", fill="x", padx=22, pady=18)

    def create_widgets(self):
        """ウィジェット作成"""
        # ロゴ画像
        self.canvas = tk.Canvas(self.main_frame, width=60, height=60,
                                highlightthickness=0, background="#ffffff")
        self.img = tk.PhotoImage(file=self.image_path)
        self.canvas.create_image(31, 31, image=self.img)

        # パスワード入力欄
        self.input_pass_var = tk.StringVar()
        self.input_pass_var.trace_add("write", self.update_button_state)
        self.input_pass = tk.Entry(self.main_frame, show="●",
                                   textvariable=self.input_pass_var,
                                   relief="solid", borderwidth=0,
                                   highlightthickness=1,
                                   highlightbackground="#8c8c8c",
                                   highlightcolor="#0078d4")
        self.input_pass.focus_set()
        self.input_pass.bind("<Return>",
                             lambda event: self.move_focus(self.start_date))

        # 日付選択欄
        self.start_date_var = tk.StringVar()
        self.start_date = ttk.Combobox(self.main_frame, values=create_date_list(),
                                       textvariable=self.start_date_var,
                                       state="readonly", justify="center",
                                       width=14)
        self.start_date.current(0)
        self.start_date.bind("<Return>",
                             lambda event: self.move_focus(self.end_date))

        self.end_date_var = tk.StringVar()
        self.end_date = ttk.Combobox(self.main_frame, values=create_date_list(),
                                     textvariable=self.end_date_var,
                                     state="readonly", justify="center",
                                     width=14)
        self.end_date.current(0)
        self.end_date.bind("<Return>",
                           lambda event: self.move_focus(self.checkboxes[0]))

        # チェックボックス
        self.checkbox_texts = ["FSP", "#7", "#8", "基材識別票"]
        self.checkbox_vars = []     # チェックボックスの状態を保持する変数
        self.checkboxes = []        # チェックボックスのウィジェットを保持するリスト
        for i, text in enumerate(self.checkbox_texts):
            var = tk.IntVar(value=1)    # デフォルトで選択状態
            self.checkbox_vars.append(var)
            checkbox = ttk.Checkbutton(self.main_frame, text=text, variable=var,
                                       command=self.update_button_state)
            checkbox.bind("<Return>",
                          lambda event, idx=i: self.move_focus_cb(idx))
            self.checkboxes.append(checkbox)    # チェックボックスをリストに追加

        # ラベル
        self.labels = [
            (ttk.Label(self.main_frame, text=greet(userId)), 0, 1, 4, "w"),
            (ttk.Label(self.main_frame, text="パスワード："), 1, 0, None, "e"),
            (ttk.Label(self.main_frame, text="印刷範囲："), 2, 0, None, "e"),
            (ttk.Label(self.main_frame, text="―"), 2, 1, 4, None),
        ]

        # プログレスバー
        self.progress_var = tk.IntVar()
        self.progressbar = ttk.Progressbar(self.bottom_frame,
                                           variable=self.progress_var,
                                           orient="horizontal",
                                           mode="determinate",
                                           maximum=100)

        # 実行ボタン
        self.execute_button = ttk.Button(self.bottom_frame, text="実行", width=13,
                                         default="active", state="disabled")
        self.execute_button.bind("<Return>",
                                 lambda event: self.execute_action())
        # ボタンクリック時のイベントハンドラを設定
        self.execute_button.config(command=self.execute_action)

    def arrange_widgets(self):
        """ウィジェット配置"""
        # キャンバス配置
        self.canvas.grid(row=0, column=0, padx=7)

        # 入力欄配置
        self.input_pass.grid(row=1, column=1, columnspan=4, sticky="ew",
                             padx=3, pady=(1, 18), ipady=1)

        # 日付選択欄配置
        self.start_date.grid(row=2, column=1, columnspan=4, sticky="w",
                             padx=3, pady=(0, 14))
        self.end_date.grid(row=2, column=1, columnspan=4, sticky="e",
                           padx=3, pady=(0, 14))

        # チェックボックス配置
        for i, checkbox in enumerate(self.checkboxes):
            checkbox.grid(row=3, column=i+1, sticky="w", padx=(1, 0))

        # ラベル配置
        for label, row, col, colspan, sticky in self.labels:
            padx_value = (24, 0) if row == 1 else 0
            pady_value = (14, 13) if row == 0 else (0, 14)
            label.grid(row=row, column=col, columnspan=colspan, sticky=sticky,
                       padx=padx_value, pady=pady_value)

        # ボタン配置
        self.execute_button.pack(side="right")

    def execute_action(self):
        """実行ボタンが押されたときの処理"""
        password = self.input_pass.get()
        start_date_value = self.start_date.get()
        end_date_value = self.end_date.get()

        self.status_label = ttk.Label(self.bottom_frame, text="実行中...",
                                      style="Progress.TLabel", width=8)
        self.status_label.pack(side="left", padx=(0, 13))
        self.progressbar.pack(side="right", fill="x", expand=True, padx=(0, 13))

        # ウィジェットを無効化
        self.style.configure("TLabel", foreground="#6d6d6d")
        self.input_pass.config(state="disabled")
        self.start_date.config(state="disabled")
        self.end_date.config(state="disabled")
        for checkbox in self.checkboxes:
            checkbox.config(state="disabled")

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

    def update_button_state(self, *args):
        """実行ボタンの状態を更新する関数"""
        # パスワード入力欄の文字列取得
        password = self.input_pass_var.get()
        # チェックボックスのうち、一つでも選択されているかどうかを確認
        checkbox_selected = any(var.get() for var in self.checkbox_vars)
        # パスワードが8以上14以下で、チェックボックスが選択されている場合
        if 8 <= len(password) <= 14 and checkbox_selected:
            # ボタンを有効化
            self.execute_button.config(state="normal")
        elif len(password) > 14:
            # パスワードが長すぎる場合、入力できなくする
            self.input_pass_var.set(password[:14])
        else:
            # ボタンを無効化
            self.execute_button.config(state="disabled")

    def move_focus(event, next_widget):
        """フォーカス移動イベントハンドラ"""
        # フォーカスを次のウィジェットに移動
        next_widget.focus_set()

    def move_focus_cb(self, index):
        """チェックボックスのフォーカス移動"""
        if index < len(self.checkboxes) - 1:
            self.checkboxes[index + 1].focus_set()
        else:
            if self.execute_button.instate(['!disabled']):
                self.execute_button.focus_set()
            else:
                pass

    def run(self):
        """アプリケーション実行"""
        self.root.mainloop()
