/*
 * Jungo door lock Arduino UNO sketch
 * -----------------------------------
 * - Reads a 4x4 keypad (update the pin assignments below to match your keypad)
 * - Sends the entered 4-digit code to the Raspberry Pi via Serial in the form `CODE:1234`
 * - Waits for the Pi to respond with `UNLOCK` or `LOCK` commands to drive a motor/relay
 *
 * Dependencies:
 *   Install the Keypad library via Arduino Library Manager (Tools > Manage Libraries).
 */

#include <Keypad.h>
#include <Servo.h>

// --------- USER CONFIGURABLE SECTION ---------------------------------------
// Adjust these arrays to match your keypad wiring (default: 4x4 matrix keypad)
const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};

byte rowPins[ROWS] = {2, 3, 4, 5};          // ROW0 ~ ROW3
byte colPins[COLS] = {6, 7, 11, 12};        // COL0 ~ COL3  (adjust to avoid motor pins)

// Motor / relay pins
const int RELAY_PIN = 8;    // relay controlling the strike / motor power
const int MOTOR_PWM = 9;    // PWM pin driving a motor controller (servo signal)
const int MOTOR_DIR = 10;   // optional direction pin (can be unused)
// ---------------------------------------------------------------------------

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);
Servo motor;

String enteredCode = "";
bool isUnlocked = false;

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ;  // wait for serial port to connect.
  }

  pinMode(RELAY_PIN, OUTPUT);
  pinMode(MOTOR_PWM, OUTPUT);
  pinMode(MOTOR_DIR, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH);  // HIGH -> locked (for active-low relays)
  digitalWrite(MOTOR_PWM, LOW);
  digitalWrite(MOTOR_DIR, LOW);

  motor.attach(MOTOR_PWM);
  motor.writeMicroseconds(1500);  // stop

  Serial.println(F("UNO ready. Enter 4-digit code on keypad."));
}

void loop() {
  handleKeypad();
  handleSerialCommands();
}

void handleKeypad() {
  char key = keypad.getKey();
  if (!key) {
    return;
  }

  if (key == '*') {  // clear buffer
    enteredCode = "";
    Serial.println(F("CODE:CLEAR"));
    return;
  }

  if (key == '#') {  // force submit even if length != 4
    sendCodeToPi();
    return;
  }

  if (isDigit(key)) {
    enteredCode += key;
    Serial.print(F("CODE:PARTIAL:"));
    Serial.println(enteredCode);
    if (enteredCode.length() == 4) {
      sendCodeToPi();
    }
  }
}

void sendCodeToPi() {
  if (enteredCode.length() == 4) {
    Serial.print(F("CODE:"));
    Serial.println(enteredCode);
  } else {
    Serial.print(F("CODE:SHORT:"));
    Serial.println(enteredCode);
  }
  enteredCode = "";
}

void handleSerialCommands() {
  if (Serial.available() <= 0) {
    return;
  }

  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line.equalsIgnoreCase("UNLOCK")) {
    unlockDoor();
    Serial.println(F("ACK UNLOCK"));
  } else if (line.equalsIgnoreCase("LOCK")) {
    lockDoor();
    Serial.println(F("ACK LOCK"));
  } else if (line.length() > 0) {
    Serial.print(F("UNKNOWN COMMAND: "));
    Serial.println(line);
  }
}

void unlockDoor() {
  if (isUnlocked) return;
  isUnlocked = true;
  digitalWrite(RELAY_PIN, LOW);       // energize relay (active-low example)
  motor.writeMicroseconds(1700);      // spin forward briefly
  delay(1000);
  motor.writeMicroseconds(1500);      // stop
}

void lockDoor() {
  if (!isUnlocked) return;
  isUnlocked = false;
  motor.writeMicroseconds(1300);      // reverse briefly if needed
  delay(500);
  motor.writeMicroseconds(1500);      // stop
  digitalWrite(RELAY_PIN, HIGH);      // de-energize relay -> locked
}
