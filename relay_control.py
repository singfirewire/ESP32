#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import time
import argparse

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
DEVICE_ID = "termux_controller"

# Topics
TOPIC_RELAY1_CONTROL = "home/relay1/control"
TOPIC_RELAY2_CONTROL = "home/relay2/control"
TOPIC_STATUS = "home/relay/status"

class RelayController:
    def __init__(self):
        self.client = mqtt.Client(DEVICE_ID)
        self.status = {}
        
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # Connect to broker
        print(f"Connecting to {MQTT_BROKER}...")
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        self.client.subscribe(TOPIC_STATUS)

    def on_message(self, client, userdata, msg):
        if msg.topic == TOPIC_STATUS:
            self.status = json.loads(msg.payload.decode())
            self._print_status()

    def _print_status(self):
        print("\n=== Device Status ===")
        print(f"Device ID: {self.status.get('device_id', 'Unknown')}")
        print(f"WiFi: {'Connected' if self.status.get('wifi_connected', False) else 'Disconnected'}")
        print(f"Signal Strength: {self.status.get('wifi_rssi', 'N/A')} dBm")
        
        relay1 = self.status.get('relay1', {})
        print("\nRelay 1:")
        print(f"  Status: {'ON' if relay1.get('active', False) else 'OFF'}")
        if relay1.get('active', False):
            remaining = relay1.get('remaining_seconds', 0)
            print(f"  Remaining: {remaining//60}:{remaining%60:02d}")
            
        relay2 = self.status.get('relay2', {})
        print("\nRelay 2:")
        print(f"  Status: {'ON' if relay2.get('active', False) else 'OFF'}")
        if relay2.get('active', False):
            remaining = relay2.get('remaining_seconds', 0)
            print(f"  Remaining: {remaining//60}:{remaining%60:02d}")

    def control_relay(self, relay_num, action):
        topic = TOPIC_RELAY1_CONTROL if relay_num == 1 else TOPIC_RELAY2_CONTROL
        command = {"action": action}
        self.client.publish(topic, json.dumps(command))
        print(f"Sent command: Relay {relay_num} {action}")
        time.sleep(1)  # Wait for status update

def main():
    parser = argparse.ArgumentParser(description='Control ESP32 Relay via MQTT')
    parser.add_argument('relay', type=int, choices=[1, 2], help='Relay number (1 or 2)')
    parser.add_argument('action', type=str.upper, choices=['ON', 'OFF', 'RESET', 'STATUS'],
                      help='Action to perform')
    
    args = parser.parse_args()
    
    controller = RelayController()
    
    if args.action == 'STATUS':
        time.sleep(1)  # Wait for status update
    else:
        controller.control_relay(args.relay, args.action)
    
    time.sleep(1)  # Wait for final status
    controller.client.loop_stop()

if __name__ == "__main__":
    main()
