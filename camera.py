
class Camera:
    def __init__(self, id, name, status, locations, record, mic, ipaddress, port_onvif, port_http, speed, login, password, model, stream, videocodec):
        self.id = id
        self.name = name
        self.status = status
        self.locations = locations
        self.record = record
        self.mic = mic
        self.ipaddress = ipaddress
        self.port_onvif = port_onvif
        self.port_http = port_http
        self.speed = speed
        self.login = login
        self.password = password
        self.model = model
        self.stream = stream
        self.videocodec = videocodec


    def toggle_status(self):
        self.status = not self.status


    def edit_settings(self, settings):
        # Изменение настроек камеры
        pass


    def __str__(self):
        return f'Camera {self.name}, ID: {self.id}, Status: {self.status}, Location: {self.locations}' \
               f'Запись: {self.record}, MIC: {self.mic}' \
               f'IP: {self.ipaddress}, Port Onvif: {self.port_onvif}, Port http: {self.port_http}' \
               f'SPEED: {self.speed}, login: {self.login}, pass: {self.password}'