
class Camera:
    def __init__(self, id, name: str = "", status: str = "", locations: str = "", record: int = 0, mic: bool = False,
                 ipaddress: str = "",
                 port_onvif: int = 554, port_http: int = 8080, speed: int = 2048, login: str = "admin",
                 password: str = "paswr",
                 model: str = "ХЗ", stream: str = "/media/video1", videocodec: str = "H.264"):
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


    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'locations': self.locations,
            'record': self.record,
            'ipaddress': self.ipaddress,
            'port_http': self.port_http,
            'port_onvif': self.port_onvif,
            'speed': self.speed,
            'login': self.login,
            'password': self.password,
            'model': self.model,
            'stream': self.stream,
            'videocodec': self.videocodec,
            'mic': self.mic
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)