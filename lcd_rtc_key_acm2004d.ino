#include <Wire.h>
#include <ST7032_asukiaaa.h>      // ★LiquidCrystal_I2C → ST7032
#include <Adafruit_Keypad.h>
#include <RTClib.h>

/* ========== LCD (ACM2004D 20×4) ========== */
ST7032_asukiaaa lcd(0x3F);        // ★I2C アドレスは i2c_scanner の結果に合わせて
                                   //   0x3E の個体もあるので必要なら変更

/* ========== Keypad ========== */
#define ROWS 4
#define COLS 4
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
uint8_t rowPins[ROWS] = {2, 3, 4, 5};
uint8_t colPins[COLS] = {6, 7, 8, 9};
Adafruit_Keypad keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

/* ========== データ ========== */
const char* varNames[] = { "BENI", "BENI", "KISYU", "TAR40" };
const uint8_t VAR_CNT = sizeof(varNames)/sizeof(varNames[0]);

int confirmedIdx = 0, pendingIdx = -1;
int confirmedNumB = 0, pendingNumB = 0;   // VAL
int confirmedNumC = 0, pendingNumC = 0;   // CNT

/* ========== RTC ========== */
RTC_DS3231 rtc;

/* ========== 状態 ========== */
enum State { IDLE, SELECT_VAR, EDIT_VAL, EDIT_CNT };
State state = IDLE;

/* ========== 点滅制御 ========== */
const uint16_t BLINK_MS = 500;
unsigned long  blinkTimer = 0;
bool           blinkOn    = true;

/* ========== 表示位置 ========== */
const uint8_t COL_VAL = 0;   // 「Qty:xx」の開始列
const uint8_t COL_CNT = 9;   // 「Lot:yy」の開始列

/* -------------------------------------------------- */
void setup() {
  Wire.begin();                 // ★必ず先に I²C 初期化
  lcd.begin(20, 4);             // ★20桁4行
  lcd.setContrast(40);          //   0〜63 で調整（40 前後が無難）

  printVariable();
  printVAL();
  printCNT();
  keypad.begin();

  if (!rtc.begin()) {
    lcd.print("RTC not found.");
    while (1);
  }
  if (rtc.lostPower()) {
    lcd.print("RTC lost power.");
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }
}

void loop() {
  handleKeys();
  handleBlink();

  DateTime now = rtc.now();
  /* ---- 20 桁用に右端へ移動（15〜19列目） ---- */
  lcd.setCursor(15, 0);       // HH
  print2digits(now.hour());

  lcd.print(now.second() % 2 ? ' ' : ':');  // コロン点滅

  lcd.setCursor(18, 0);       // MM
  print2digits(now.minute());

  delay(100);
}

void print2digits(int number) {
  if (number < 10) lcd.print('0');
  lcd.print(number);
}

/* ========== キー処理 ========== */
void handleKeys() {
  keypad.tick();
  while (keypad.available()) {
    keypadEvent e = keypad.read();
    if (e.bit.EVENT != KEY_JUST_PRESSED) continue;
    char k = (char)e.bit.KEY;

    /* ---------- A : 変数選択 ---------- */
    if (k == 'A') {
      if (state == IDLE) {
        state = SELECT_VAR;
        pendingIdx = confirmedIdx;
        startBlink();
      } else if (state == SELECT_VAR) {
        confirmedIdx = pendingIdx;
        state = IDLE;
        printVariable();
      }
    }

    /* ---------- B : VAL 編集 ---------- */
    else if (k == 'B') {
      if (state == IDLE) {
        state = EDIT_VAL;
        pendingNumB = confirmedNumB;
        startBlink();
      } else if (state == EDIT_VAL) {
        confirmedNumB = pendingNumB;
        state = IDLE;
        printVAL();
      }
    }

    /* ---------- C : CNT 編集 ---------- */
    else if (k == 'C') {
      if (state == IDLE) {
        state = EDIT_CNT;
        pendingNumC = confirmedNumC;
        startBlink();
      } else if (state == EDIT_CNT) {
        confirmedNumC = pendingNumC;
        state = IDLE;
        printCNT();
      }
    }

    /* ---------- 数字キー ---------- */
    else if (k >= '0' && k <= '9') {
      int d = k - '0';
      if (state == SELECT_VAR) {
        if (d < VAR_CNT) { pendingIdx = d; printVariable(); }
      } else if (state == EDIT_VAL) {
        pendingNumB = (pendingNumB * 10 + d) % 100;
        printVAL();
      } else if (state == EDIT_CNT) {
        pendingNumC = (pendingNumC * 10 + d) % 100;
        printCNT();
      }
    }
  }
}

/* ========== 点滅処理 ========== */
void handleBlink() {
  if (state == IDLE) return;
  if (millis() - blinkTimer < BLINK_MS) return;

  blinkTimer = millis();
  blinkOn = !blinkOn;

  if (state == SELECT_VAR) {
    blinkOn ? printVariable() : clearVariable();
  }
  else if (state == EDIT_VAL) {
    blinkOn ? printVAL() : clearVAL();
  }
  else if (state == EDIT_CNT) {
    blinkOn ? printCNT() : clearCNT();
  }
}

/* ========== 表示ヘルパ ==========
   – 1 行目、VAL 部分、CNT 部分を独立して上書き／クリアする  */
void printVariable() {
  lcd.setCursor(0, 0);
  lcd.print("Type:");
  lcd.setCursor(5, 0);
  lcd.print(varNames[(state==SELECT_VAR)?pendingIdx:confirmedIdx]);
}
void clearVariable() { lcd.setCursor(5,0); lcd.print("      "); }

/* ----------- VAL ------------- */
void printVAL() {
  lcd.setCursor(COL_VAL, 1);
  int v = (state==EDIT_VAL)?pendingNumB:confirmedNumB;
  lcd.print("Qty:");
  lcd.print(v < 10 ? "0" : "");
  lcd.print(v);
}
void clearVAL() {
  lcd.setCursor(4,1);
  lcd.print("  ");          // 「VAL:xx」と同じ 6 文字を空白で
}

/* ----------- CNT ------------- */
void printCNT() {
  lcd.setCursor(COL_CNT, 1);
  int c = (state==EDIT_CNT)?pendingNumC:confirmedNumC;
  lcd.print("Lot:");
  lcd.print(c < 10 ? "0" : "");
  lcd.print(c);
}
void clearCNT() {
  lcd.setCursor(13,1);
  lcd.print("  ");          // 同上
}

/* ----------- 共通 ----------- */
void startBlink() { blinkTimer = millis(); blinkOn = true; }