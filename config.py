 # config.py
 import os
 from dotenv import load_dotenv
 load_dotenv()
 MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
 MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
 # When computed priority exceeds this, auto-create a work order
 PRIORITY_THRESHOLD = float(os.getenv("PRIORITY_THRESHOLD", "70"))
 # Mock Maximo REST API base
 MOCK_MAXIMO_URL = os.getenv("MOCK_MAXIMO_URL", "http://127.0.0.1:8000")