from machine import Pin
import time
import random
import json  #json is built-in in MicroPython
import requests  #imported requests for firebase upload
import network #for connecting to wifi

#set flash parameters
N = 10
sample_ms = 10.0
on_ms = 500


#wifi login info, using BU guest since open network and easy to connect to
SSID = 'BU Guest (unencrypted)'
PASSWORD = ''

def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)  #create station interface
    wlan.active(True)  #activate network interface

    if PASSWORD:
        wlan.connect(SSID, PASSWORD)  #if network has password, take password
    else:
        wlan.connect(SSID)  #if no password (open network), connect without password

    print(f"Connecting to {SSID}...")
    timeout = 10  #10 sec timeout
    while timeout > 0:
        if wlan.isconnected():
            print("Connected to Wi-Fi")
            print("IP address:", wlan.ifconfig()[0])
            return wlan
        else:
            print(f"Waiting for connection... {timeout}")
            time.sleep(1)
            timeout -= 1

    print("Failed to connect to Wi-Fi")
    return None

#firebase config
firebase_config = {
    "apiKey": "AIzaSyDRFKIv1R4_UpWHPUFA10KT0r3f5yrQ4Ns",
    "authDomain": "attempt1-807d4.firebaseapp.com",
    "projectId": "attempt1-807d4",
    "firestoreURL": "https://firestore.googleapis.com/v1/projects/attempt1-807d4/databases/(default)/documents/mini-project/"
}


def upload_to_firestore(data: dict) -> None:
    """Uploads JSON data to Firebase Firestore."""
    try:
        url = firebase_config['firestoreURL']

        #create dict for upload to firestore in same format as expected
        firestore_data = {
            "fields": {
                "Minimum": {"doubleValue": data["Minimum"]} if data["Minimum"] is not None else None,
                "Maximum": {"doubleValue": data["Maximum"]} if data["Maximum"] is not None else None,
                "Average": {"doubleValue": data["Average"]} if data["Average"] is not None else None,
                "Score": {"doubleValue": data["Score"]}
            }
        }

        response = requests.post(url, json=firestore_data, headers={
            'Content-Type': 'application/json'
        })

        if response.status_code == 200: #default firestore success code
            print("Data uploaded successfully to Firestore.")
        else:
            print(f"Failed to upload data. Status code: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Failed to upload data to Firestore: {str(e)}")
        

def random_time_interval(tmin: float, tmax: float) -> float:
    """Return a random time interval between max and min."""
    return random.uniform(tmin, tmax)

def blinker(N: int, led: Pin) -> None:
    """Blink LED to indicate the start/end of the game."""
    for _ in range(N):
        led.on()
        time.sleep(0.1)
        led.off()
        time.sleep(0.1)

def scorer(t: list[int | None]) -> None:
    """Collect and display results, then upload them as JSON data."""
    misses = t.count(None)
    print(f"You missed the light {misses} / {len(t)} times")

    t_good = [x for x in t if x is not None]

    print(t_good)

    #calc min, max, and avg times
    if t_good:
        min_t = min(t_good)
        max_t = max(t_good)
        avg_t = sum(t_good) / len(t_good)
    else:
        min_t = max_t = avg_t = None

    #prepare dict for upload
    data = {
        "Minimum": min_t,
        "Maximum": max_t,
        "Average": avg_t,
        "Score": (len(t_good) / len(t)) if t else 0
    }

    #export json file to firestore
    upload_to_firestore(data)

if __name__ == "__main__":
    led = Pin("LED", Pin.OUT)
    button = Pin(16, Pin.IN, Pin.PULL_UP)

    t: list[int | None] = []

    blinker(3, led)
    
    connect_to_wifi() #connect the pi to wifi

    for i in range(N):
        time.sleep(random_time_interval(0.5, 5.0))

        led.on()

        tic = time.ticks_ms()
        t0 = None
        while time.ticks_diff(time.ticks_ms(), tic) < on_ms:
            if button.value() == 0:
                t0 = time.ticks_diff(time.ticks_ms(), tic)
                led.off()
                break
        t.append(t0)

        led.off()

    blinker(5, led)

    scorer(t)
