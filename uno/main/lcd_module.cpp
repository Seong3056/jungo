#include "lock_module.h"

LiquidCrystal_I2C lcd(0x27, 16, 2);

void lcdInit() {
    lcd.init();
    lcd.backlight();
    lcd.clear();
}

void showMessage(const String &msg, int delayTime) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(msg);
    delay(delayTime);
}

void showPrompt() {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Enter ID:");
    lcd.setCursor(0, 1);
}
