import adafruit_dht
import board
import time

dhtDevice = adafruit_dht.DHT22(board.D4, use_pulseio=False)

while True:
    try:
        temperature = dhtDevice.temperature
        humidity = dhtDevice.humidity
        print(f"{temperature} {humidity}")
        time.sleep(0.5)
    except:
        dhtDevice.exit()
