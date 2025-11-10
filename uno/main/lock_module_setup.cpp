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
}

// ===== Servo =====
Servo motor;
void motorInit() {
  motor.attach(MOTOR_PIN);
  delay(300);
  motor.write(90); // 잠금 상태
}

// ===== Magnet Sensor (SEN030600) =====
void magnetInit() {
  pinMode(MAGNET_PIN, INPUT);
}

bool isMagnetDetected() {
  // SEN030600: 자석이 가까우면 LOW, 떨어지면 HIGH
  return (digitalRead(MAGNET_PIN) == LOW);
}

// ===== Ultrasonic Sensor (HC-SR04) =====
void ultrasonicInit() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
}

float getDistance() {
  long duration;
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  duration = pulseIn(ECHO_PIN, HIGH, 30000); // 30ms timeout
  if (duration == 0) return -1;  // 타임아웃 시 -1 반환

  float distance = (duration * 0.0343) / 2.0; // cm 단위
  return distance;
}

bool isObjectDetected(float range) {
  float d = getDistance();
  return (d > 0 && d < range);
}
