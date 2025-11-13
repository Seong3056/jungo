#include "lock_module.h"

LiquidCrystal lcd(11, 12, A5, A4, A3, A2);

void lcdInit() {
  lcd.begin(16, 2);
  lcd.clear();
}

void showMessage(const String &msg, int delayTime) {
  lcd.clear();
  lcd.print(msg);
  delay(delayTime);
}

void showPrompt() {
  lcd.clear();
  lcd.print("Enter ID:");
  lcd.setCursor(0, 1);
}
