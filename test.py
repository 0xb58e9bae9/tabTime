import getpass
import datetime
import tkinter as tk
from tkinter import ttk
from tkinter.font import Font

from tkcalendar import DateEntry


class MainGui:
    def __init__(self):
        # 環境変数からユーザーIDを取得
        self.userId = getpass.getuser()

        # 現在の日付を取得
        self.today = datetime.date.today()

        # GUI初期化
        self.root = tk.Tk()

        # ウィンドウタイトル設定
        self.root.title("BC受付自動印刷")

        # 画面サイズ設定
        self.window_width = 334
        self.window_height = 230

        # ウィンドウを画面中央に配置
        self.center_window()

        # リサイズ不可に設定
        self.root.resizable(False, False)

        # フォント設定
        self.font = Font(family="Yu Gothic UI", size=9)

        # 日付ピッカー用のフォント設定
        self.date_picker_font = Font(family="Yu Gothic", size=9)

        # スタイル設定を適用
        self.setup_style()

        # フレーム作成
        self.create_frames()

        # ウィジェット作成
        self.create_widgets()

        # ウィジェット配置
        self.arrange_widgets()

    def center_window(self):
        """ウィンドウを画面中央に配置する"""
        center_x = (
            self.root.winfo_screenwidth() // 2
            - self.window_width // 2
        )
        center_y = (
            self.root.winfo_screenheight() // 2
            - self.window_height // 2
        )
        self.root.geometry(
            f"{self.window_width}x{self.window_height}+{center_x}+{center_y}"
        )

    def setup_style(self):
        """スタイル設定"""
        self.style = ttk.Style(self.root)
        self.style.theme_use("vista")
        self.style.theme_settings("vista", {
            ".": {
                "configure": {"font": self.font}
            },
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
            }
        })

    def create_frames(self):
        """フレーム作成"""
        self.frame1 = ttk.Frame(self.root, style="White.TFrame")
        self.frame1.pack(fill="x")

        self.frame2 = ttk.Frame(self.root, style="Gray.TFrame")
        self.frame2.pack(fill="x")

    def create_widgets(self):
        """ウィジェット作成"""
        # キャンバスとロゴ画像
        self.canvas = tk.Canvas(self.frame1, width=60, height=60,
                                highlightthickness=0, background="#ffffff")
        self.img = tk.PhotoImage(file="python_logo.png")
        self.canvas.create_image(31, 31, image=self.img)

        # パスワード入力欄
        self.input_pass = tk.Entry(self.frame1, show="●", width=40,
                                   relief="solid", borderwidth=0,
                                   highlightthickness=1,
                                   highlightbackground="#8c8c8c",
                                   highlightcolor="#0078d4",
                                   font=self.font)
        self.input_pass.focus_set()

        # 日付選択欄の共通設定
        self.date_entry_config = {
            "width": 12,
            "background": "#ffffff",
            "foreground": "#000000",
            "borderwidth": 0,
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
            "mindate": self.today,
            "maxdate": self.today + datetime.timedelta(days=8),
            "font": self.date_picker_font
        }

        # 日付選択欄
        self.start_date = DateEntry(self.frame1, **self.date_entry_config)
        self.end_date = DateEntry(self.frame1, **self.date_entry_config)

        # チェックボックス
        self.checkbox_texts = ["FSP", "#7", "#8", "基材識別票"]
        self.checkbox_vars = []
        self.checkboxes = []
        for text in self.checkbox_texts:
            var = tk.IntVar(value=1)
            checkbox = ttk.Checkbutton(self.frame1, text=text, variable=var)
            self.checkbox_vars.append(var)
            self.checkboxes.append(checkbox)

        # ラベル
        self.labels = [
            (
                ttk.Label(
                    self.frame1,
                    text=(
                        f"{self.userId}さん、おつかれさまです！\n"
                        "BC受付のパスワードと印刷範囲を入力してください。"
                    )
                ), 1, 0, "w"
            ),
            (ttk.Label(self.frame1, text="パスワード："), 0, 1, "e"),
            (ttk.Label(self.frame1, text="印刷範囲："), 0, 2, "e"),
            (ttk.Label(self.frame1, text="―"), 1, 2, None)
        ]

        # 実行ボタン
        self.button = ttk.Button(self.frame2,
                                 text="実行", width=13, default="active")
        # ボタンクリック時のイベントハンドラを設定
        self.button.config(command=self.execute_action)

    def arrange_widgets(self):
        """ウィジェット配置"""
        # キャンバス配置
        self.canvas.grid(column=0, row=0, padx=7)

        # 入力欄配置
        self.input_pass.grid(column=1, row=1, sticky="w", padx=3, pady=(1, 18))

        # 日付選択欄配置
        self.start_date.grid(column=1, row=2, sticky="w", padx=3, pady=(0, 14))
        self.end_date.grid(column=1, row=2, sticky="e", padx=3, pady=(0, 14))

        # チェックボックス配置
        for i, checkbox in enumerate(self.checkboxes):
            padx_value = 1 + i * 48 if i > 0 else 1
            checkbox.grid(column=1, row=3, sticky="w",
                          padx=(padx_value, 0), pady=(0, 14))

        # ラベル配置
        for label, col, row, sticky in self.labels:
            pady_value = (1, 18) if row == 1 else (0, 14)
            label.grid(column=col, row=row, sticky=sticky, pady=pady_value)

        # ボタン配置
        self.button.pack(side="right", padx=12, pady=18)

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

        # ここに印刷処理などの実装を追加
        print(f"パスワード: {password}")
        print(f"開始日: {start_date_value}")
        print(f"終了日: {end_date_value}")
        print(f"選択オプション: {selected_options}")

        # 実際のアプリケーションでは、ここで印刷処理や他の操作を実行します

    def run(self):
        """アプリケーション実行"""
        self.root.mainloop()


# アプリケーション実行
if __name__ == "__main__":
    app = MainGui()
    app.run()
