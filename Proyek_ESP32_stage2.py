import time
import dht
import network
import ujson
import urequests
import gc
from machine import Pin, PWM
from umqtt.simple import MQTTClient

# **Konfigurasi WiFi**
WIFI_SSID = "BIZNET"
WIFI_PASSWORD = "12345678"

# **Konfigurasi MQTT**
MQTT_BROKER = "broker.emqx.io"
MQTT_CLIENT_ID = "ESP32_Device"
MQTT_TOPIC_PUBLISH = "esp32/sensor/status"

# **Konfigurasi Ubidots & Flask API**
UBIDOTS_DEVICE = "esp32_percobaan1"
UBIDOTS_TOKEN = "BBUS-WKOuBrlCwamKWFak2u8hSMaoCmxtVR"
UBIDOTS_URL = f"http://industrial.api.ubidots.com/api/v1.6/devices/{UBIDOTS_DEVICE}/"
FLASK_SERVER = "http://192.168.18.232:5000/sensor"

# **Konfigurasi Hardware**
led = Pin(4, Pin.OUT)
servo = PWM(Pin(14), freq=50)
sensor = dht.DHT11(Pin(5))

# **Timestamp untuk kontrol pengiriman**
last_send_time = time.time()

# **Fungsi Koneksi WiFi**
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Menghubungkan ke WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        for _ in range(10):
            if wlan.isconnected():
                print("Terhubung ke WiFi! IP:", wlan.ifconfig()[0])
                return
            time.sleep(1)
    print("Gagal terhubung ke WiFi.")

# **Fungsi Koneksi MQTT**
def connect_mqtt():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
    client.connect()
    print("Terhubung ke MQTT!")
    return client

# **Fungsi Menggerakkan Servo**
def set_servo_angle(angle):
    duty = int((angle / 180) * 102 + 26)  # Konversi derajat ke duty PWM
    servo.duty(duty)

# **Fungsi Mengirim Data ke HTTP API**
def send_to_http(temp, hum, led_status, servo_angle):
    try:
        headers = {"X-Auth-Token": UBIDOTS_TOKEN, "Content-Type": "application/json"}
        data = ujson.dumps({
            "temperature": temp,
            "humidity": hum,
            "led_status": led_status,  # Nilai Numerik: 1 = ON, 0 = OFF
            "servo_position": servo_angle  # Mengirimkan Posisi Servo
        })
        
        # Kirim ke Ubidots
        response = urequests.post(UBIDOTS_URL, headers=headers, data=data)
        response.close()
        
        # Kirim ke Flask API
        headers = {"Content-Type": "application/json"}
        response = urequests.post(FLASK_SERVER, headers=headers, data=data)
        response.close()
        
        print("Data berhasil dikirim ke Ubidots & Flask ✅")
    except Exception as e:
        print("Gagal mengirim HTTP:", e)
    
    gc.collect()  # Bersihkan memori

# **Program Utama**
connect_wifi()
mqtt_client = connect_mqtt()

while True:
    try:
        current_time = time.time()

        # **Mengirim data setiap 5 detik**
        if current_time - last_send_time >= 5:
            sensor.measure()
            temp, hum = sensor.temperature(), sensor.humidity()

            # **Menentukan Kondisi LED dan Servo Berdasarkan Suhu**
            if temp > 24.5:
                led.value(1)  # LED Menyala
                set_servo_angle(180)  # Servo bergerak ke 180°
                servo_angle = 180  #180 derajat
                led_status = 1  # LED Menyala
            else:
                led.value(0)  # LED Mati
                set_servo_angle(0)  # Servo tetap di 0°
                servo_angle = 0
                led_status = 0  # LED Mati

            # **Membuat Payload untuk MQTT & HTTP**
            payload = ujson.dumps({
                "temperature": temp,
                "humidity": hum,
                "led_status": led_status,  # Sekarang dalam format 1 atau 0
                "servo_position": servo_angle
            })

            # **Kirim ke MQTT**
            mqtt_client.publish(MQTT_TOPIC_PUBLISH, payload)
            print("Data berhasil dikirim ke MQTT ✅")

            # **Kirim ke Ubidots**
            send_to_http(temp, hum, led_status, servo_angle)

            # **Update timestamp**
            last_send_time = current_time

        time.sleep(0.5)  # Hindari looping berlebihan

    except Exception as e:
        print("Error:", e)
        time.sleep(5)
