import getpass
import locale
from datetime import datetime, timedelta


userId = getpass.getuser()

locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')

def greet(name):
    """ユーザーに挨拶する関数"""
    message = (f"{name}さん、おつかれさまです！\n"
               "BC受付のパスワードと印刷範囲を入力してください。")
    print(message)
    return message

def generate_date_data():
    """日付リストの生成"""
    today = datetime.today()
    data = []

    for i in range(7):
        date = today + timedelta(days=i)
        display = date.strftime("%#m月%#d日（%a）")
        value = date.strftime("%y/%m/%d")
        data.append({"display": display, "value": value})

    return data
