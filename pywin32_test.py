import win32com.client
import time

# IE起動＆ページ遷移
ie = win32com.client.Dispatch("InternetExplorer.Application")
ie.Visible = True
ie.Navigate("https://www.google.co.jp/")

# ページ読み込み待ち
while ie.Busy or ie.ReadyState != 4:
    time.sleep(1)

# ドキュメント取得
doc = ie.Document

# フォーム取得（name="f"）
form = doc.forms("f")

# 検索ワードを入力（name="q"）
form.elements("q").value = "pywinauto"

# 「Google 検索」ボタンをクリック（name="btnG"）
form.elements("btnG").click()
