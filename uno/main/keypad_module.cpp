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

void keypadInit() {
  keypad.setDebounceTime(20);
  keypad.setHoldTime(50);
  resetInputState();
}

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

static void resetInputState() {
  inputId = "";
  inputCode = "";
  enteringId = true;
  showEnterIdPrompt();
}

static void handleStarKey() {
  resetInputState();
}

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

void handleKeypad() {
  char key = keypad.getKey();
  if (!key) return;

  if (key == 'A' || key == 'B' || key == 'C' || key == 'D') {
    Serial.println("OPEN:1");
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
