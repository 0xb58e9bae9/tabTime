import tkinter as tk
from tkinter import ttk
from ctypes import windll

from utils import greet, generate_date_data, userId

# 高解像度表示対応
windll.shcore.SetProcessDpiAwareness(1)


class MainGui:
    def __init__(self):
        self._updating = False
        self.setup_root()
        self.setup_style()
        self.create_frames()
        self.create_widgets()
        self.arrange_widgets()

    def setup_root(self):
        """ルートウィンドウの初期設定"""
        self.root = tk.Tk()
        self.root.title("BC受付自動印刷")
        self.root.resizable(False, False)
        self.image_path = "./resources/python_logo.png"

    def setup_style(self):
        """ウィジェットのスタイル設定"""
        self.style = ttk.Style(self.root)
        self.style.theme_use("vista")
        self.style.theme_settings("vista", {
            "Main.TFrame": {"configure": {"background": "#ffffff"}},
            "Bottom.TFrame": {"configure": {"background": "#f0f0f0"}},
            "Separator.TFrame": {"configure": {"background": "#8d8d8d"}},
            "TCheckbutton": {"configure": {"background": "#ffffff"}},
            "TLabel": {"configure": {"background": "#ffffff", "foreground": "#000000"}},
            "Progress.TLabel": {"configure": {"background": "#f0f0f0", "foreground": "#000000"}},
        })

    def create_frames(self):
        """フレームの生成"""
        self.main_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.main_frame.pack(side="top", fill="x", ipadx=10, ipady=7)

        self.bottom_frame = ttk.Frame(self.root, style="Bottom.TFrame")
        self.bottom_frame.pack(side="bottom", fill="x", padx=22, pady=18)

        # 日付選択欄の間の線
        self.separator_frame = ttk.Frame(self.main_frame, style="Separator.TFrame")
        self.separator_frame.grid(row=2, column=1, columnspan=4, pady=(0, 12), ipadx=6)

    def create_widgets(self):
        """ウィジェットの生成"""
        # ロゴ画像用キャンバス
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
                                   highlightbackground="#8d8d8d",
                                   highlightcolor="#0078d4")
        self.input_pass.focus_set()
        self.input_pass.bind("<Return>", lambda event: self.start_date.focus_set())
        self.input_pass.bind("<Shift-Return>", self.return_focus)

        # 日付選択欄（開始日・終了日）
        self.date_data = generate_date_data()
        self.display_list = [self.date_data[i]["display"] for i in range(7)]

        self.start_date_var = tk.StringVar()
        self.start_date = ttk.Combobox(self.main_frame,
                                       value=self.display_list,
                                       textvariable=self.start_date_var,
                                       state="readonly", justify="center",
                                       width=14)
        self.start_date.current(0)
        self.start_date.bind("<<ComboboxSelected>>", self.change_end_date_min)
        self.start_date.bind("<Return>", lambda event: self.end_date.focus_set())
        self.start_date.bind("<Shift-Return>", self.return_focus)

        self.end_date_var = tk.StringVar()
        self.end_date = ttk.Combobox(self.main_frame,
                                     values=self.display_list,
                                     textvariable=self.end_date_var,
                                     state="readonly", justify="center",
                                     width=14)
        self.end_date.current(6)
        self.end_date.bind("<Return>", lambda event: self.checkboxes[0].focus_set())
        self.end_date.bind("<Shift-Return>", self.return_focus)

        # 印刷対象選択チェックボックス
        self.checkbox_texts = ["FSP", "#7", "#8", "基材識別票"]
        self.checkbox_vars = []
        self.checkboxes = []
        for i, text in enumerate(self.checkbox_texts):
            var = tk.IntVar(value=1)
            self.checkbox_vars.append(var)
            checkbox = ttk.Checkbutton(self.main_frame, text=text,
                                       variable=var,
                                       command=self.update_button_state)
            checkbox.bind("<Return>", lambda event, idx=i: self.move_focus_cb(idx))
            checkbox.bind("<Shift-Return>", self.return_focus)
            self.checkboxes.append(checkbox)

        # 各ラベル（グリーティング、パスワード、印刷範囲）
        self.labels = [
            (ttk.Label(self.main_frame, text=greet(userId)), 0, 1, 4, "w"),
            (ttk.Label(self.main_frame, text="パスワード："), 1, 0, None, "e"),
            (ttk.Label(self.main_frame, text="印刷範囲："), 2, 0, None, "e"),
        ]

        # プログレスバー
        self.progressbar_var = tk.IntVar()
        self.progressbar = ttk.Progressbar(self.bottom_frame,
                                           variable=self.progressbar_var,
                                           orient="horizontal",
                                           mode="determinate",
                                           maximum=100)

        # 実行ボタン
        self.execute_button = ttk.Button(self.bottom_frame, text="実行",
                                         default="active", state="disabled",
                                         width=13, command=self.execute_action)
        self.execute_button.bind("<Return>", lambda event: self.execute_action())
        self.execute_button.bind("<Shift-Return>", self.return_focus)

    def arrange_widgets(self):
        """ウィジェットの配置"""
        self.canvas.grid(row=0, column=0, padx=7)
        self.input_pass.grid(row=1, column=1, columnspan=4, sticky="ew",
                             padx=3, pady=(1, 18), ipady=1)
        self.start_date.grid(row=2, column=1, columnspan=4, sticky="w",
                             padx=3, pady=(0, 14))
        self.end_date.grid(row=2, column=1, columnspan=4, sticky="e",
                           padx=3, pady=(0, 14))

        for i, checkbox in enumerate(self.checkboxes):
            checkbox.grid(row=3, column=i+1, sticky="w", padx=(1, 0))

        for label, row, col, colspan, sticky in self.labels:
            padx_value = (24, 0) if row == 1 else 0
            pady_value = (14, 13) if row == 0 else (0, 14)
            label.grid(row=row, column=col, columnspan=colspan, sticky=sticky,
                       padx=padx_value, pady=pady_value)

        self.execute_button.pack(side="right")

    def move_focus_cb(self, index):
        """チェックボックス群におけるフォーカス移動（次の項目、もしくは実行ボタンへ）"""
        if index < len(self.checkboxes) - 1:
            self.checkboxes[index + 1].focus_set()
        elif self.execute_button.instate(['!disabled']):
            self.execute_button.focus_set()
        else:
            self.input_pass.focus_set()

    def return_focus(self, event):
        """
        Shift+Enter の入力で前のウィジェットにフォーカスを戻す
        （tkinter の tk_focusPrev() を用いて、現在のウィジェットの前のウィジェットに移動）
        """
        prev_widget = event.widget.tk_focusPrev()
        if prev_widget:
            prev_widget.focus_set()

    def update_button_state(self, *args):
        """パスワードの文字数とチェックボックスの選択状況により実行ボタンの有効／無効を切り替え"""
        password = self.input_pass_var.get()
        checkbox_selected = any(var.get() for var in self.checkbox_vars)
        if 8 <= len(password) <= 14 and checkbox_selected:
            self.execute_button.config(state="normal")
        elif len(password) > 14:
            self.input_pass_var.set(password[:14])
        else:
            self.execute_button.config(state="disabled")

    def change_end_date_min(self, event):
        """日付入力欄（終了日）のリストの最小値を開始日に合わせて変更する"""
        if self._updating:
            return
        self._updating = True

        index = self.start_date.current()
        self.new_values = self.display_list[index:]
        self.end_date["values"] = self.new_values

        # 終了日の選択がリストの範囲外になっていれば調整
        end_index = self.end_date.current()

        if end_index >= len(self.new_values) or end_index < 0:
            self.end_date.current(0)

        self._updating = False

    def disable_widgets(self):
        """入力ウィジェット類を無効化（グレーアウト）する"""
        self.style.configure("Separator.TFrame", background="#c8c8c8")
        self.style.configure("TLabel", foreground="#6d6d6d")
        self.input_pass.config(state="disabled", highlightbackground="#c8c8c8")
        self.start_date.config(state="disabled")
        self.end_date.config(state="disabled")
        for checkbox in self.checkboxes:
            checkbox.config(state="disabled")

    def execute_action(self):
        """実行ボタン押下時の処理"""
        self.disable_widgets()

        password = self.input_pass.get()
        start_date_value = self.start_date.get()
        end_date_value = self.end_date.get()

        selected_options = [
            text for var, text in zip(self.checkbox_vars, self.checkbox_texts) if var.get()
        ]

        self.status_label = ttk.Label(self.bottom_frame, text="実行中...",
                                       style="Progress.TLabel", width=8)
        self.status_label.pack(side="left", padx=(0, 13))
        self.progressbar.pack(side="right", padx=(0, 13), fill="x", expand=True)

        print(f"パスワード: {password}")
        print(f"開始日: {start_date_value}")
        print(f"終了日: {end_date_value}")
        print(f"選択オプション: {selected_options}")
        print(self.new_values)

    def run(self):
        """アプリケーションの実行"""
        self.root.mainloop()
