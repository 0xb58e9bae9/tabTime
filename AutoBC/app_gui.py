import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
import subprocess
import sys
import os

import config
import utils


class MainGui:
    def __init__(self):
        self.setup_root()
        self.setup_style()
        self.create_frames()
        self.create_widgets()
        self.arrange_frames()
        self.arrange_widgets()

    def setup_root(self):
        """ルートウィンドウの初期設定"""
        # 高解像度対応
        utils.set_per_monitor_dpi_awareness()

        self.root = tk.Tk()

        # 起動時のウィンドウ描画安定化のためウィンドウを一時的に隠す
        self.root.withdraw()

        self.root.title(config.APP_NAME)
        self.root.iconbitmap(config.ICON_PATH)

        self.root.resizable(False, False)

        self.root.bind("<Escape>", lambda event: self.cancel_action())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._is_running = False  # cancel_action, on_close 用フラグ
        self._updating_end_date = False  # change_end_date_min 用フラグ

    def run(self):
        """アプリケーションの実行"""
        self.root.update_idletasks()  # レイアウト確定
        self.root.deiconify()  # ウィンドウを表示

        self.input_pass.focus_set()

        self.root.mainloop()

    def run_process(self):
        """実行中の処理"""
        self.status_label = ttk.Label(
            self.bottom_frame, text="ログイン中…", style="Progress.TLabel", width=12
        )
        self.status_label.pack(side="left", padx=(0, 13))

        self.progressbar.pack(side="right", padx=(0, 13), fill="x", expand=True)
        self.progressbar.start(config.PROGRESSBAR_SPEED)

        self.execute_button.config(
            text="中止", state="normal", command=self.cancel_action
        )
        self.execute_button.bind("<Return>", lambda event: self.cancel_action())

        password = self.input_pass.get()
        end_index = self.end_date.current()
        selected_date_list = [d["value"] for d in self.sublist[: end_index + 1]]
        selected_keys, selected_values = self.get_selected_options()

        cmd = [
            sys.executable,
            "process.py",
            "userId",
            utils.userId,
            "--password",
            password,
            "--selected_date_list",
            selected_date_list,
            "--targets",
            *selected_values,
        ]

    def setup_style(self):
        """ウィジェットのスタイル設定"""
        self.style = ttk.Style(self.root)
        self.style.theme_settings(
            "vista",
            {
                "Main.TFrame": {"configure": {"background": "#ffffff"}},
                "Bottom.TFrame": {"configure": {"background": "#f0f0f0"}},
                "Separator.TFrame": {"configure": {"background": "#8d8d8d"}},
                "TCheckbutton": {"configure": {"background": "#ffffff"}},
                "TLabel": {
                    "configure": {"background": "#ffffff", "foreground": "#000000"}
                },
                "Progress.TLabel": {
                    "configure": {"background": "#f0f0f0", "foreground": "#000000"}
                },
            },
        )

    def create_frames(self):
        """フレームの生成"""
        self.main_frame = ttk.Frame(self.root, style="Main.TFrame")

        self.bottom_frame = ttk.Frame(self.root, style="Bottom.TFrame")

        self.separator_frame = ttk.Frame(self.main_frame, style="Separator.TFrame")

    def create_widgets(self):
        """ウィジェットの生成"""
        # ロゴ画像用キャンバス
        self.canvas = tk.Canvas(
            self.main_frame,
            width=60,
            height=60,
            highlightthickness=0,
            background="#ffffff",
        )
        self.logo = tk.PhotoImage(file=config.LOGO_PATH)
        self.canvas.create_image(31, 31, image=self.logo)

        # パスワード入力欄
        self.input_pass_var = tk.StringVar()
        self.input_pass_var.trace_add("write", self.update_button_state)
        self.input_pass = tk.Entry(
            self.main_frame,
            textvariable=self.input_pass_var,
            insertwidth=1,
            show="●",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#8d8d8d",
            highlightcolor="#0078d4",
        )
        self.input_pass.bind("<Return>", lambda event: self.start_date.focus_set())
        self.input_pass.bind("<Shift-Return>", self.return_focus)

        # 日付選択欄用のデータ
        self.date_data = utils.generate_date_data()
        self.display_list = [self.date_data[i]["display"] for i in range(7)]
        self.sublist = self.date_data[0:]

        # 日付選択欄（開始日）
        self.start_date = ttk.Combobox(
            self.main_frame,
            width=14,
            value=self.display_list,
            justify="center",
            state="readonly",
        )
        self.start_date.current(config.START_DATE_DEFAULT)
        self.start_date.bind("<<ComboboxSelected>>", self.change_end_date_min)
        self.start_date.bind("<Return>", lambda event: self.end_date.focus_set())
        self.start_date.bind("<Shift-Return>", self.return_focus)

        # 日付選択欄（終了日）
        self.end_date = ttk.Combobox(
            self.main_frame,
            width=14,
            values=self.display_list,
            justify="center",
            state="readonly",
        )
        self.end_date.current(config.END_DATE_DEFAULT)
        self.end_date.bind("<Return>", lambda event: self.checkboxes[0].focus_set())
        self.end_date.bind("<Shift-Return>", self.return_focus)

        # 印刷対象選択チェックボックス
        self.checkboxes = []
        self.checkbox_vars = {}
        self.checkbox_widgets = {}

        for i, key in enumerate(config.PRINT_TARGET_DATA):
            var = tk.BooleanVar(value=config.CHECKBOX_DEFAULT)
            checkbox = ttk.Checkbutton(
                self.main_frame,
                text=key,
                variable=var,
                command=self.update_button_state,
            )
            checkbox.bind("<Return>", lambda event, idx=i: self.move_focus_cb(idx))
            checkbox.bind("<Shift-Return>", self.return_focus)

            self.checkbox_vars[key] = var
            self.checkbox_widgets[key] = checkbox
            self.checkboxes.append(checkbox)

        # ラベル（文字列）
        self.labels = [
            (ttk.Label(self.main_frame, text=utils.greet(utils.userId)), 0, 1, 4, "w"),
            (ttk.Label(self.main_frame, text="パスワード："), 1, 0, None, "e"),
            (ttk.Label(self.main_frame, text="印刷範囲："), 2, 0, None, "e"),
        ]

        # プログレスバー
        self.progressbar = ttk.Progressbar(
            self.bottom_frame, variable=0, mode="indeterminate", orient="horizontal"
        )

        # 実行ボタン
        self.execute_button = ttk.Button(
            self.bottom_frame,
            width=11,
            text="実行",
            default="active",
            state="disabled",
            command=self.execute_action,
        )
        self.execute_button.bind("<Return>", lambda event: self.execute_action())
        self.execute_button.bind("<Shift-Return>", self.return_focus)

    def arrange_frames(self):
        """フレームの配置"""
        self.main_frame.pack(side="top", fill="x", ipadx=10, ipady=7)

        self.bottom_frame.pack(side="bottom", fill="x", padx=22, pady=18)

        self.separator_frame.grid(row=2, column=1, columnspan=4, pady=(0, 12), ipadx=6)

    def arrange_widgets(self):
        """ウィジェットの配置"""
        self.canvas.grid(row=0, column=0, padx=7)

        self.input_pass.grid(
            row=1, column=1, columnspan=4, sticky="ew", padx=3, pady=(1, 18), ipady=1
        )

        self.start_date.grid(
            row=2, column=1, columnspan=4, sticky="w", padx=3, pady=(0, 14)
        )

        self.end_date.grid(
            row=2, column=1, columnspan=4, sticky="e", padx=3, pady=(0, 14)
        )

        for i, checkbox in enumerate(self.checkboxes):
            checkbox.grid(row=3, column=i + 1, sticky="w", padx=(1, 0))

        for label, row, col, colspan, sticky in self.labels:
            padx_value = (24, 0) if row == 1 else 0
            pady_value = (14, 13) if row == 0 else (0, 14)
            label.grid(
                row=row,
                column=col,
                columnspan=colspan,
                sticky=sticky,
                padx=padx_value,
                pady=pady_value,
            )

        self.execute_button.pack(side="right")

    def change_end_date_min(self, event):
        """日付入力欄（終了日）のリストの最小値を開始日に合わせて変更する"""
        if self._updating_end_date:
            return
        self._updating_end_date = True

        index = self.start_date.current()
        self.sublist = self.date_data[index:]
        self.end_date["values"] = [d["display"] for d in self.sublist]

        self.end_date.focus_set()

        if index > self.end_date.current():
            self.end_date.current(0)

        self._updating_end_date = False

    def update_button_state(self, *args):
        """パスワードの文字数とチェックボックスの選択状況で実行ボタンの有効／無効を切り替え"""
        password = self.input_pass_var.get()
        checkbox_selected = any(var.get() for var in self.checkbox_vars.values())
        if 8 <= len(password) <= config.INPUT_LIMIT and checkbox_selected:
            self.execute_button.config(state="normal")
        elif len(password) > config.INPUT_LIMIT:
            self.input_pass_var.set(password[: config.INPUT_LIMIT])
        else:
            self.execute_button.config(state="disabled")

    def execute_action(self):
        """実行ボタン押下時の処理"""
        self._is_running = True

        self.disable_widgets()
        self.execute_button.config(state="disable")
        self.root.focus_set()

        self.root.after(300, lambda: (self.run_process()))

    def get_selected_options(self) -> tuple[list, list]:
        """チェックされた項目のキーと、それに対応する処理用の値を取得"""
        selected_keys = [key for key, var in self.checkbox_vars.items() if var.get()]
        selected_values = []
        for key in selected_keys:
            selected_values.extend(config.PRINT_TARGET_DATA[key])
        return selected_keys, selected_values

    def cancel_action(self):
        """中止ボタン押下時の処理"""
        if not self._is_running:
            return

        self.progressbar.stop()
        self.execute_button.config(state="disabled")
        self.root.focus_set()

        confirm = messagebox.askyesno(
            config.APP_NAME, "処理を中止します。よろしいですか？", default="no"
        )
        if confirm:
            self._is_running = False
            if hasattr(self, "status_label"):
                self.status_label.pack_forget()
            if hasattr(self, "progressbar"):
                self.progressbar.pack_forget()

            self.enable_widgets()
            self.execute_button.config(
                text="実行", state="normal", command=self.execute_action
            )
            self.execute_button.bind("<Return>", lambda event: self.execute_action())
        else:
            self.progressbar.start(config.PROGRESSBAR_SPEED)
            self.execute_button.config(state="normal")

    def on_close(self):
        """処理中にウィンドウの閉じるボタンが押下された場合の確認"""
        if self._is_running:
            if messagebox.askyesno(config.APP_NAME, "処理中です。終了しますか？"):
                self.root.destroy()
        else:
            self.root.destroy()

    def disable_widgets(self):
        """入力ウィジェット類を無効化"""
        self.style.configure("Separator.TFrame", background="#c8c8c8")
        self.style.configure("TLabel", foreground="#6d6d6d")
        self.input_pass.config(state="disabled", highlightbackground="#c8c8c8")
        self.start_date.config(state="disabled")
        self.end_date.config(state="disabled")
        for checkbox in self.checkbox_widgets.values():
            checkbox.config(state="disabled")

    def enable_widgets(self):
        """入力ウィジェット類を有効化"""
        self.style.configure("Separator.TFrame", background="#8d8d8d")
        self.style.configure("TLabel", foreground="#000000")
        self.input_pass.config(state="normal", highlightbackground="#8d8d8d")
        self.start_date.config(state="readonly")
        self.end_date.config(state="readonly")
        for checkbox in self.checkbox_widgets.values():
            checkbox.config(state="normal")

    def move_focus_cb(self, index):
        """チェックボックスのフォーカス移動（次の項目、もしくは実行ボタンへ）"""
        if index < len(self.checkboxes) - 1:
            self.checkboxes[index + 1].focus_set()
        elif self.execute_button.instate(["!disabled"]):
            self.execute_button.focus_set()
        else:
            self.input_pass.focus_set()

    def return_focus(self, event):
        """Shift+Enter の入力で前のウィジェットにフォーカスを戻す"""
        prev_widget = event.widget.tk_focusPrev()
        if prev_widget:
            prev_widget.focus_set()
