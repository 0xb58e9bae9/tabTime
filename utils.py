import datetime
import getpass
import locale


# 日本語のロケールを設定
locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')

def greet(name):
    """ユーザーに挨拶する関数"""
    message = (f"{name}さん、おつかれさまです！\n"
               "BC受付のパスワードと印刷範囲を入力してください。")
    print(message)
    return message


userId = getpass.getuser()


def get_today():
    today = datetime.date.today()
    return today


def set_max_date():
    """最大日付を今日から8日後に設定する関数"""
    today = datetime.date.today()
    max_date = today + datetime.timedelta(days=8)
    return max_date

def create_date_list():
    """8日分の日付リストを作成する関数"""
    today = datetime.date.today()
    date_list = [today + datetime.timedelta(days=i) for i in range(8)]
    # 日付を日本語の形式に変換
    date_list = [date.strftime("%Y/%m/%d (%a)") for date in date_list]
    return date_list
