import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import sys

reader = SimpleMFRC522()
while True:
    try:
        id = reader.read_id()
        print(id)
        time.sleep(0.5)
    except:
        break
GPIO.cleanup()
