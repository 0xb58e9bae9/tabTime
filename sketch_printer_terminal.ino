/**********************************************************************
 *  LCD + Keypad + RTC + IR sensors  +  WS-S300M thermal printer
 *  Board  : Arduino Nano Every
 *  Printer: 9600 bps / 8N1 / XON-XOFF ON / RTS-CTS OFF
 *********************************************************************/
#include <Wire.h>
#include <ST7032_asukiaaa.h>
#include <Adafruit_Keypad.h>
#include <RTClib.h>
#include <Arduino.h>

/* ---------- LCD ---------- */
ST7032_asukiaaa lcd(0x3F);
const uint8_t   BL_PIN      = 10;

/* ---------- Back-light timer ---------- */
const uint32_t  BL_TIMEOUT_MS = 60000UL;   // 無操作30 s で消灯
const uint8_t   BL_DUTY_ON    = 128;
bool     blOn        = false;
uint32_t blLastOn_ms = 0;

/* ---------- Keypad ---------- */
#define ROWS 4
#define COLS 4
char keys[ROWS][COLS] = {
  { '1', '2', '3', 'A' },
  { '4', '5', '6', 'B' },
  { '7', '8', '9', 'C' },
  { 'E', '0', 'F', 'D' }           // ←★ E ボタンで印刷
};
uint8_t rowPins[ROWS] = { 6, 7, 8, 9 };
uint8_t colPins[COLS] = { 2, 3, 4, 5 };
Adafruit_Keypad keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

/* ---------- Speaker ---------- */
const uint8_t PIEZO_PIN_A = 11;
const uint8_t PIEZO_PIN_B = 12;

/* ---------- RTC ---------- */
RTC_DS3231 rtc;

/* ---------- Data (品名と既定 Qty) ---------- */
struct VarInfo { const char* name; uint8_t qtyInit; };
const VarInfo vars[] = {
  { "R_BENI"    , 70 },
  { "R_BENI"    , 70 },
  { "R_KISYU"   , 70 },
  { "R_TARZAN40", 40 },
  { "R_PHIN"    , 40 },
};
const uint8_t VAR_CNT = sizeof(vars) / sizeof(vars[0]);

/* 変数群 ---------------------------------------------------------------- */
uint8_t qtyVals[VAR_CNT];
uint8_t lotVals[VAR_CNT];

int confirmedIdx = 0, pendingIdx = -1;
int pendingNumC = 0, pendingNumD = 0;

/* 編集ステート */
enum State { IDLE, SELECT_VAR, EDIT_VAL, EDIT_CNT };
State state = IDLE;

/* 点滅制御 */
const uint16_t BLINK_MS = 500;
unsigned long  blinkTimer = 0;
bool           blinkOn    = true;

/* 二桁入力フラグ */
bool firstDigitVal = false;
bool firstDigitCnt = false;

/* ボタン列位置（LCD 20 桁） */
const uint8_t BTN_COL = 17;

/* ---------- IR センサー ---------- */
enum IRState { CLEAR, COUNTDOWN, TRIGGERED };
const uint8_t NUM_IR        = 2;
const uint8_t SENSOR_PINS[] = { A0, A1 };   // CH0:BL, CH1:Lot++
const uint32_t COOLDOWN_MS[NUM_IR] = { 3000000UL, 30000UL };
const uint16_t LOT_THR_ADC  = 320;
const uint16_t BL_THR_ADC   = 160;
const uint16_t HYST         = 20;
const uint32_t DWELL_MS     = 3000;

IRState  irStates[NUM_IR];
uint32_t dwellStarts[NUM_IR], coolUntil[NUM_IR];
bool     objNearForBL = false;

/* ---------- Thermal printer ---------- */
#define PRINTER   Serial1
#define MAX_DOTS  576
#define FONT_A_W  12
#define CHUNK     256

bool printerReady() {
  static bool busy = false;
  while (PRINTER.available()) {
    uint8_t c = PRINTER.read();
    if (c == 0x13) busy = true;      // XOFF
    if (c == 0x11) busy = false;     // XON
  }
  return !busy;
}
void waitReady() { while (!printerReady()) delay(5); }

void safeWrite(const uint8_t* p, size_t len) {
  while (len) {
    size_t n = (len > CHUNK) ? CHUNK : len;
    PRINTER.write(p, n);
    PRINTER.flush();
    waitReady();
    p   += n;
    len -= n;
  }
}
/* ---- text styles ---- */
void setScale(uint8_t w, uint8_t h) {
  if (w == 2 && h == 2) PRINTER.write("\x1B\x21\x30", 3);
  else {
    uint8_t n[3] = { 0x1D, 0x21, uint8_t(((w-1)<<4)|(h-1)) };
    PRINTER.write(n, 3);
  }
}
void resetScale() { PRINTER.write("\x1D\x21\x00", 3); }
void setAlign(uint8_t n) { uint8_t c[3]={0x1B,0x61,n}; PRINTER.write(c,3); }
void setMargins(uint16_t left, uint16_t right) {
  uint8_t gsL[4]={0x1D,0x4C,uint8_t(left),uint8_t(left>>8)};
  PRINTER.write(gsL,4);
  uint16_t width = MAX_DOTS - left - right;
  uint8_t gsW[4]={0x1D,0x57,uint8_t(width),uint8_t(width>>8)};
  PRINTER.write(gsW,4);
}
void safePrint(const char* txt, uint8_t wMul) {
  uint16_t maxChars = MAX_DOTS/(FONT_A_W*wMul), col=0;
  while (*txt) {
    PRINTER.write(*txt++);
    if (++col >= maxChars && *txt) { PRINTER.write("\r\n"); col=0; waitReady(); }
  }
  PRINTER.write("\r\n");
  waitReady();
}
void heading(const char* txt,uint8_t w,uint8_t h,uint8_t align=0){
  setAlign(align); setScale(w,h); safePrint(txt,w); resetScale(); setAlign(0);
}
/* ---- レシート１枚印刷 ---- */
void printReceipt() {
  waitReady();
  setMargins(48,0);

  heading("===========",4,3,1);
  heading(vars[confirmedIdx].name,4,3,1);
  heading("===========",4,3,1);

  DateTime now = rtc.now();
  char buf[16];
  sprintf(buf,"%04d/%02d/%02d",now.year(),now.month(),now.day());
  heading(buf,4,3,0);
  PRINTER.println();

  sprintf(buf,"%02d:%02d",now.hour(),now.minute());
  heading(buf,4,3,2);

  heading("-----------",4,3,1);

  sprintf(buf,"Qty: %02d",qtyVals[confirmedIdx]);
  heading(buf,4,3,0);
  PRINTER.println();

  sprintf(buf,"Lot: %02d",lotVals[confirmedIdx]);
  heading(buf,4,3,0);

  heading("-----------",4,3,1);

  uint8_t cut[]={0x1D,0x56,0x42,0x00};
  safeWrite(cut,sizeof(cut));
}

/* ---------- 共通ユーティリティ ---------- */
inline void backlightOn(){ analogWrite(BL_PIN,BL_DUTY_ON); blOn=true; blLastOn_ms=millis(); }
inline void backlightOff(){ analogWrite(BL_PIN,0); blOn=false; }

/* 元からあった “Qty 上限チェック” */
inline bool isWithinMaxQty(uint8_t idx, uint8_t val){
  return val <= vars[idx].qtyInit;
}

/* ---------- beep（プッシュプル駆動） ---------- */
void beep(uint16_t freq,uint16_t durMs){
  const uint32_t half_us = 500000UL / freq;
  uint32_t cycles = (uint32_t)freq * durMs / 1000;
  for (uint32_t i=0;i<cycles;i++){
    digitalWrite(PIEZO_PIN_A,HIGH); digitalWrite(PIEZO_PIN_B,LOW);
    delayMicroseconds(half_us);
    digitalWrite(PIEZO_PIN_A,LOW);  digitalWrite(PIEZO_PIN_B,HIGH);
    delayMicroseconds(half_us);
  }
  digitalWrite(PIEZO_PIN_A,LOW); digitalWrite(PIEZO_PIN_B,LOW);
}

bool lotResetDoneToday = false;   // 今日の 00:00 リセット済みか

/* =========================  setup  ============================ */
void setup() {
  delay(500);

  PRINTER.begin(9600);
  PRINTER.write("\x1B@");
  waitReady();

  Wire.begin();

  lcd.begin(20, 4);
  lcd.setContrast(40);
  pinMode(BL_PIN, OUTPUT);
  backlightOn();

  keypad.begin();
  pinMode(PIEZO_PIN_A, OUTPUT);
  pinMode(PIEZO_PIN_B, OUTPUT);

  for (uint8_t i=0;i<NUM_IR;i++){
    pinMode(SENSOR_PINS[i],INPUT);
    irStates[i]=CLEAR;
  }

  if (!rtc.begin()) { lcd.print("RTC not found"); while(1); }
  if (rtc.lostPower()) rtc.adjust(DateTime(F(__DATE__),F(__TIME__)));

  beep(2026,60); delay(20); beep(1026,50);

  for (uint8_t i=0;i<VAR_CNT;i++){
    qtyVals[i]=vars[i].qtyInit;
    lotVals[i]=1;
  }

  delay(500);
  printVariable(); printDate(); printVAL(); printCNT(); printButtonLabels();
}

/* =========================  main loop  ============================ */
void loop() {
  handleKeys();
  handleBlink();
  printDateTimeLine();
  printButtonLabels();

  /* ---- IR sensors ---- */
  for (uint8_t ch=0; ch<NUM_IR; ch++) {
    uint16_t adc = analogRead(SENSOR_PINS[ch]);

    /* back-light (CH0) */
    if (ch==0){
      bool blNear = adc > BL_THR_ADC+HYST, blFar = adc < BL_THR_ADC-HYST;
      if (!objNearForBL && blNear){ backlightOn(); objNearForBL=true; }
      else if (objNearForBL && blFar){ objNearForBL=false; }
    }
    /* common Lot++ 判定 */
    bool lotNear = adc > LOT_THR_ADC+HYST, lotFar = adc < LOT_THR_ADC-HYST;
    switch (irStates[ch]){
      case CLEAR:
        if (millis()<coolUntil[ch]) break;
        if (lotNear){ if (ch==0) backlightOn();
          irStates[ch]=COUNTDOWN; dwellStarts[ch]=millis(); }
        break;
      case COUNTDOWN:
        if (lotFar) {
          irStates[ch] = CLEAR;

        } else if (millis() - dwellStarts[ch] >= DWELL_MS) {

          if (ch == 1) {                // 印刷実行
            printReceipt();
          }

          // ── 印刷が終わったら Lot++ ──
          lotVals[confirmedIdx]++;
          if (lotVals[confirmedIdx] > 99) lotVals[confirmedIdx] = 1;

          printCNT();                   // LCD を更新

          qtyVals[confirmedIdx] = vars[confirmedIdx].qtyInit; // 既定 Qty に戻す
          printVAL();                      //   ← LCD の Qty を更新

          beep(1500, 40);
          if (ch == 0) backlightOn();

          irStates[ch] = TRIGGERED;
        }
        break;
      case TRIGGERED:
        if (lotFar){ irStates[ch]=CLEAR; coolUntil[ch]=millis()+COOLDOWN_MS[ch]; }
        break;
    }
  }
  if (blOn && millis()-blLastOn_ms>=BL_TIMEOUT_MS) backlightOff();
  delay(30);
}

/* =========================  LCD / Keypad 関数群 ==================== */
void print2digits(int n){ if (n<10) lcd.print('0'); lcd.print(n); }

void printDate(){
  lcd.setCursor(0,1); lcd.print("Date:01/01 00:00");
}
void printDateTimeLine(){
  DateTime now=rtc.now();

  /*  00:00 で一度だけ Lot をリセット ------------ */
  static uint8_t lastResetDay = 255;          // 前回リセットした日 (1-31)

  if (now.hour() == 0 && now.minute() == 0) { // 00:00台
    if (lastResetDay != now.day()) {          // まだ今日のリセット未実行
      for (uint8_t i = 0; i < VAR_CNT; ++i) { lotVals[i] = 1; }
      if (state != EDIT_CNT) printCNT();      // 画面更新 (編集中はスキップ)
      lastResetDay = now.day();               // 二重実行防止
    }
  } else {
      lastResetDay = 255;                     // 00:01以降に解放

  lcd.setCursor(0,1); lcd.print("Date:");
  lcd.setCursor(5,1); print2digits(now.month());
  lcd.setCursor(7,1); lcd.print('/');
  lcd.setCursor(8,1); print2digits(now.day());
  lcd.setCursor(11,1); print2digits(now.hour());
  lcd.print(now.second()%2?' ' : ':');
  lcd.setCursor(14,1); print2digits(now.minute());
  }
}

/* ---- LCD 表示ユーティリティ ---- */
void printVariable(){
  lcd.setCursor(0,0); lcd.print("Item:");
  uint8_t idx=(state==SELECT_VAR)?pendingIdx:confirmedIdx;
  lcd.setCursor(5,0); lcd.print("            ");
  lcd.setCursor(5,0); lcd.print(vars[idx].name);
}
void clearVariable(){ lcd.setCursor(5,0); lcd.print("            "); }

void printVAL(){
  lcd.setCursor(0,2);
  uint8_t idx=confirmedIdx;
  uint8_t v=(state==EDIT_VAL)?pendingNumC:qtyVals[idx];
  lcd.print("Qty :"); if (v<10) lcd.print('0'); lcd.print(v);
}
void clearVAL(){ lcd.setCursor(5,2); lcd.print("  "); }

void printCNT(){
  lcd.setCursor(0,3);
  uint8_t idx=confirmedIdx;
  uint8_t c=(state==EDIT_CNT)?pendingNumD:lotVals[idx];
  lcd.print("Lot :"); if (c<10) lcd.print('0'); lcd.print(c);
}
void clearCNT(){ lcd.setCursor(5,3); lcd.print("  "); }

void printButtonLabels(){
  lcd.setCursor(BTN_COL,0); lcd.print("[A]");
  lcd.setCursor(BTN_COL,1); lcd.print("[B]");
  lcd.setCursor(BTN_COL,2); lcd.print("[C]");
  lcd.setCursor(BTN_COL,3); lcd.print("[D]");
}

void startBlink(){ blinkTimer=millis(); blinkOn=true; }

void handleBlink(){
  if (state==IDLE) return;
  if (millis()-blinkTimer<BLINK_MS) return;
  blinkTimer=millis(); blinkOn=!blinkOn;
  if (state==SELECT_VAR) (blinkOn?printVariable:clearVariable)();
  else if (state==EDIT_VAL) (blinkOn?printVAL:clearVAL)();
  else if (state==EDIT_CNT) (blinkOn?printCNT:clearCNT)();
}

/* ------------------------ キーパッド処理 ------------------------- */
void handleKeys(){
  keypad.tick();
  while (keypad.available()){
    backlightOn();
    keypadEvent e=keypad.read();
    if (e.bit.EVENT!=KEY_JUST_PRESSED) continue;
    char k=(char)e.bit.KEY;

    /* ---- A ---- */
    if (k=='A'){
      if (state==IDLE){ state=SELECT_VAR; pendingIdx=confirmedIdx; startBlink(); beep(2000,60); }
      else if (state==SELECT_VAR){
        uint8_t old=confirmedIdx; confirmedIdx=pendingIdx;
        if (confirmedIdx!=old){ lotVals[confirmedIdx]=1; qtyVals[confirmedIdx]=vars[confirmedIdx].qtyInit; }
        state=IDLE; printVariable(); printVAL(); printCNT();
        beep(2026,60); delay(40); beep(4026,60);
      }
    }
    /* ---- B ---- (未使用ならスキップ) */

    /* ---- C : Qty 編集 ---- */
    else if (k=='C'){
      if (state==IDLE){
        state=EDIT_VAL; pendingNumC=qtyVals[confirmedIdx]; firstDigitVal=false; startBlink(); beep(2026,60);
      }else if (state==EDIT_VAL){
        if (!isWithinMaxQty(confirmedIdx,pendingNumC)){ beep(400,120); return; }
        qtyVals[confirmedIdx]=pendingNumC; state=IDLE; printVAL();
        beep(2026,60); delay(40); beep(4026,60);
      }
    }
    /* ---- D : Lot 編集 ---- */
    else if (k=='D'){
      if (state==IDLE){
        state=EDIT_CNT; pendingNumD=lotVals[confirmedIdx]; firstDigitCnt=false; startBlink(); beep(2026,60);
      }else if (state==EDIT_CNT){
        lotVals[confirmedIdx]=pendingNumD; state=IDLE; printCNT();
        beep(2026,60); delay(40); beep(4026,60);
      }
    }
    /* ---- E : 再印刷 ---- */
    else if (k=='E' && state==IDLE){
      printReceipt();
      qtyVals[confirmedIdx] = vars[confirmedIdx].qtyInit;  // ③ Qty 既定値
      printVAL();                                         //   LCD の Qty を更新
      beep(1200,60);
    }
    /* ---- F : 手動印刷（Lot++も行う） ---- */
    else if (k=='F' && state==IDLE){
      printReceipt();
      lotVals[confirmedIdx]++;
      if (lotVals[confirmedIdx] > 99) lotVals[confirmedIdx] = 1;

      printCNT();                       // LCD を更新

      qtyVals[confirmedIdx] = vars[confirmedIdx].qtyInit;  // ③ Qty 既定値
      printVAL();                                         //   LCD の Qty を更新

      beep(1200, 60);
    }
    /* ---- 数字キー ---- */
    else if (k>='0' && k<='9'){
      int d=k-'0';

      if (state==SELECT_VAR){
        if (d<VAR_CNT){ pendingIdx=d; printVariable(); }
      }
      else if (state==EDIT_VAL){
        uint8_t cand;
        if (!firstDigitVal){ cand=d; firstDigitVal=true; }
        else cand=(pendingNumC%10)*10+d;
        if (!isWithinMaxQty(confirmedIdx,cand)){ beep(400,80); return; }
        pendingNumC=cand; printVAL();
      }
      else if (state==EDIT_CNT){
        if (!firstDigitCnt){ pendingNumD=d; firstDigitCnt=true; }
        else pendingNumD=((pendingNumD%10)*10+d)%100;
        printCNT();
      }
      beep(880,60);
    }
  }
}
