import requests
import time
import random

class PixelaUser:
    def __init__(self, username, token):
        self.username = username
        self.token = token
        self.endpoint = "https://pixe.la/v1/users"

    def create_user(self):
        params = {"token": self.token, "username": self.username, "agreeTermsOfService": "yes", "notMinor": "yes"}
        try:
            response = requests.post(url=self.endpoint, json=params)
            return response.json()
        except Exception as e:
            return {"message": str(e), "isSuccess": False}

    def get_graphs(self):
        headers = {"X-USER-TOKEN": self.token}
        url = f"{self.endpoint}/{self.username}/graphs"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json().get("graphs", [])
            return []
        except:
            return []

class PixelaGraph:
    def __init__(self, user):
        self.user = user
        self.graph_endpoint = f"https://pixe.la/v1/users/{self.user.username}/graphs"

    def create(self, graph_id, name, color, unit):
        headers = {"X-USER-TOKEN": self.user.token}
        params = {
            "id": graph_id, "name": name, "unit": unit,
            "type": "float", "color": color, "timezone": "UTC"
        }
        for _ in range(5):
            response = requests.post(url=self.graph_endpoint, json=params, headers=headers)
            if response.status_code == 200 or "already exists" in response.text:
                return True
            time.sleep(1)
        return False

class PixelaPixel:
    def __init__(self, user, graph_id):
        self.user = user
        self.graph_id = graph_id
        self.pixel_endpoint = f"https://pixe.la/v1/users/{self.user.username}/graphs/{self.graph_id}"

    def update(self, quantity):
        headers = {"X-USER-TOKEN": self.user.token}
        today = time.strftime("%Y%m%d")
        params = {"date": today, "quantity": str(quantity)}
        for _ in range(10):
            if random.random() > 0.25:
                response = requests.post(url=self.pixel_endpoint, json=params, headers=headers)
                if response.status_code == 200:
                    return True
            time.sleep(0.5)
        return False