import serial, time

# 아두이노가 연결된 포트 (라즈베리파이에서는 보통 /dev/ttyACM0 또는 /dev/ttyUSB0)
PORT = "/dev/ttyACM0"
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=1)
print("🔌 Serial listener started")

CORRECT_CODE = "1234"

while True:
    if ser.in_waiting:
        data = ser.readline().decode().strip()
        print(f"Received: {data}")
        
        if data == CORRECT_CODE:
            ser.write(b"MATCH\n")
            print("→ Sent: MATCH")
        else:
            ser.write(b"FAIL\n")
            print("→ Sent: FAIL")
    time.sleep(0.1)