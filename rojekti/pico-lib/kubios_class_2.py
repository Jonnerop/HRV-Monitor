import urequests as requests
import ujson
import network
from time import sleep
from umqtt.simple import MQTTClient

class Kubios:
    def __init__(self):
        self.apikey = "pbZRUi49X48I56oL1Lq8y8NDjq6rPfzX3AQeNo3a"
        self.client_id = "3pjgjdmamlj759te85icf0lucv"
        self.client_secret = "111fqsli1eo7mejcrlffbklvftcnfl4keoadrdv1o45vt9pndlef"
        self.token_url = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token"

        self.ssid = "KMD657_Group_3" 
        self.psw = "salasana"
        self.broker = "192.168.3.253"

        self.login_url = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/login"
        self.redirect_url = "https://analysis.kubioscloud.com/v1/portal/login"

    def connect_wlan(self):
        max_attempts = 10
        attempt = 0

        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(self.ssid, self.psw)
        
        while not wlan.isconnected() and attempt < max_attempts:
            print("Connecting to WiFi...")
            attempt += 1
            sleep(1)
        if wlan.isconnected():
            print("Connected to WiFi. Pico IP:", wlan.ifconfig()[0])
        else:
            print(f'Failed to connect to Wifi')
                    
    def connect_mqtt(self):
        try:
            mqtt_client=MQTTClient(self.client_id, self.broker)
            mqtt_client.connect(clean_session=True)
            return mqtt_client
        except Exception as e:
            print(f'Failed to connect to MQTT: {e}')
            return None

    def json(self, intervals):
        self.connect_wlan() 
        try:
            response = requests.post(
                url=self.token_url,
                data='grant_type=client_credentials&client_id={}'.format(self.client_id),
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                auth = (self.client_id, self.client_secret))
            
            response = response.json()
            access_token = response["access_token"]
            
        except Exception as e:
            print(f"Failed to fetch access token: {e}")
            return None
    
        try:
            dataset = {
                "type": "RRI",
                "data": intervals,
                "analysis": {"type": "readiness"}
            }

            response = requests.post(
                url="https://analysis.kubioscloud.com/v2/analytics/analyze",
                headers={
                    "Authorization": "Bearer {}".format(access_token),
                    "X-Api-Key": self.apikey},
                json=dataset)
            
            response = response.json()

            results = {
                'date': response["analysis"].get('create_timestamp'),
                'average_ppi': None,
                'mean_hr': response["analysis"].get('mean_hr_bpm'),
                'sdnn': response["analysis"].get('sdnn_ms'),
                'rmssd': response["analysis"].get('rmssd_ms'),
                'sns': response["analysis"].get('sns_index'),
                'pns': response["analysis"].get('pns_index')
                }
            return results
        except Exception as e:
            print(f"Failed to analyze data: {e}")
            return None

    def publish(self, stats):

        try:
            mqtt_client=self.connect_mqtt()
        except Exception as e:
            print(f"Failed to connect to MQTT: {e}")   
        
        if mqtt_client == None:
            return False
        
        message = ujson.dumps(stats)   
            
        try:
            topic = "kubios"
            mqtt_client.publish(topic, message)
            return True
                
        except Exception as e:
            print(f"Failed to send MQTT message: {e}")
            return False
        
            
        




