#include "lock_module.h"

char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};

byte rowPins[ROWS] = {6, 7, 8, 9};
byte colPins[COLS] = {2, 3, 4, 5};

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

String inputCode = "";
const int CODE_LEN = 4;

void keypadInit() {
  keypad.setDebounceTime(20);
  keypad.setHoldTime(50);
}

void handleKeypad() {
  char key = keypad.getKey();
  if (!key) return;

  if (key == '*') {
    inputCode = "";
    showPrompt();
  } 
  else if (key == '#') {
    if (inputCode.length() == CODE_LEN) {
      Serial.print("CODE:");
      Serial.println(inputCode);
      showMessage("Checking...", 800);
    } else {
      showMessage("Code too short", 800);
    }
    inputCode = "";
    showPrompt();
  } 
  else if (isdigit(key)) {
    if (inputCode.length() < CODE_LEN) {
      inputCode += key;
      lcd.print(key);
    }
  }
}
