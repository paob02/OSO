import serial
import time

print("Starting...")

ser = serial.Serial("COM5", 9600, timeout=1)

time.sleep(2)  # Allow Arduino to reset

print("Connected!")

while True:
    line = ser.readline().decode("utf-8", errors="ignore").strip()

    if line:
        print(f"Received: {line}")

        if line == "blå":
            print("BLUE BUTTON PRESSED")

        elif line == "röd":
            print("RED BUTTON PRESSED")

        elif line == "svart":
            print("BLACK BUTTON PRESSED")