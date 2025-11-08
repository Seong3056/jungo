#include "lock_module_setup.h"

// ===== LCD =====
LiquidCrystal lcd(11, 12, A3, A2, A1, A0); // RS E D4 D5 D6 D7
void lcdInit() {
  lcd.begin(16, 2);
  delay(50);
  lcd.clear();
}

// ===== Keypad =====
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
byte rowPins[ROWS] = {6, 7, 8, 9};  // LINE0 ~ LINE3
byte colPins[COLS] = {2, 3, 4, 5};  // IN0 ~ IN3
//     IN0   IN3   LINE1  LINE3
//     IN1   IN2   LINE0  LINE2

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

void keypadInit() {
  keypad.setDebounceTime(20);
  keypad.setHoldTime(50);
  // Serial.println("Keypad initialized");
}

// ===== Servo =====
Servo motor;
void motorInit() {
  motor.attach(MOTOR_PIN);
  delay(300);
  motor.write(90);
}
