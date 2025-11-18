#include "lock_module.h"

char keys[ROWS][COLS] = {
  { '1', '2', '3', 'A' },
  { '4', '5', '6', 'B' },
  { '7', '8', '9', 'C' },
  { '*', '0', '#', 'D' }
};

byte rowPins[ROWS] = { 8, 4, 9, 5 };
byte colPins[COLS] = { 6, 2, 7, 3 };

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

String inputId = "";
String inputCode = "";
bool enteringId = true;
const int CODE_LEN = 4;

// ---------------------------------------------------
// LCD Helper
// ---------------------------------------------------
static void showEnterIdPrompt() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Enter ID:");
  lcd.setCursor(0, 1);
}

static void showEnterCodePrompt() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Enter Code:");
  lcd.setCursor(0, 1);
}

static void showTempMessage(const char* msg, unsigned long delayMs = 800) {
  lcd.clear();
  lcd.print(msg);
  delay(delayMs);
}

// ---------------------------------------------------
// 입력 초기화
// ---------------------------------------------------
static void resetInputState() {
  inputId = "";
  inputCode = "";
  enteringId = true;
  showEnterIdPrompt();
}

// ---------------------------------------------------
// * 키 처리
// ---------------------------------------------------
static void handleStarKey() {
  resetInputState();
}

// ---------------------------------------------------
// # 키 처리
// ---------------------------------------------------
static void handleHashKey() {
  if (enteringId) {
    if (inputId.length() > 0) {
      enteringId = false;
      showEnterCodePrompt();
    } else {
      showTempMessage("Enter ID first");
      showEnterIdPrompt();
    }
  } else {
    if (inputCode.length() == CODE_LEN && inputId.length() > 0) {
      String message = "CHECK:" + inputId + ":" + inputCode;
      Serial.println(message);
      delay(10);

      lcd.clear();
      lcd.print("Checking...");
      delay(800);

      resetInputState();
    } else {
      showTempMessage("Incomplete");
      showEnterIdPrompt();
    }
  }
}

// ---------------------------------------------------
// 숫자키 처리
// ---------------------------------------------------
static void handleDigitKey(char key) {
  if (enteringId) {
    if (inputId.length() < 8) {
      inputId += key;
      lcd.print(key);
    }
  } else {
    if (inputCode.length() < CODE_LEN) {
      inputCode += key;
      lcd.print(key);
    }
  }
}

// ---------------------------------------------------
// 🔥 A 키 → 초음파 → 문 강제 오픈
// ---------------------------------------------------
static void handleAKey() {
  extern float getUltrasonicDistance();
  extern void openDoor();
  extern bool doorLocked;   // ⭐ main.ino 변수 가져오기
  extern bool doorOpen;

  float d = getUltrasonicDistance();

  if (d > 26) {
    // 🔥 강제 문 열기 (마그네틱 감지와 상관없이)
    openDoor();
    doorLocked = false;   // ⭐ 강제로 문이 열린 상태로 전환
    doorOpen = true;

    showTempMessage("Force Open", 800);
    showEnterIdPrompt();
  } else {
    showTempMessage("Object Detected", 800);
    showEnterIdPrompt();
  }
}


// ---------------------------------------------------
void keypadInit() {
  keypad.setDebounceTime(20);
  keypad.setHoldTime(50);
  resetInputState();
}

// ---------------------------------------------------
void handleKeypad() {
  char key = keypad.getKey();
  if (!key) return;

  if (key == 'A') {
    handleAKey();
    return;
  }

  if (key == '*') {
    handleStarKey();
    return;
  }

  if (key == '#') {
    handleHashKey();
    return;
  }

  if (isdigit(key)) {
    handleDigitKey(key);
  }
}
