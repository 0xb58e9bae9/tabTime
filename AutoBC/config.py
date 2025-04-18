APP_NAME = "BC受付自動印刷"
APP_VERSION = "1.0"

LOGIN_URL = ""

ICON_PATH = "./resources/python_logo.ico"
LOGO_PATH = "./resources/python_logo.png"

PRINT_TARGET_DATA = {
    "FSP": ("K11K2", "K11K4"),
    "#7": ("K11J2", "K11J5"),
    "#8": ("K11J8", "K11J9"),
    "基材識別票": ("K11K2", "K11J2", "K11J5", "K11J8"),
}

DATE_RANGE = 7
START_DATE_DEFAULT = 0
END_DATE_DEFAULT = DATE_RANGE - 1

INPUT_LIMIT = 14

CHECKBOX_DEFAULT = 1

PROGRESSBAR_SPEED = 10
