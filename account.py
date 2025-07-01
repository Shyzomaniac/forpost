from camera import Camera
from user import User


class Account:
    def __init__(self, id=0, name=0, contract=0, status=0, max_cameras=0, max_users=0, num_users=0, num_cameras=0):
        self.id = id
        self.name = name
        self.contract = contract
        self.status = status
        self.max_cameras = max_cameras
        self.max_users = max_users
        self.num_users = num_users
        self.num_cameras = num_cameras
        self.cameras = []
        self.users = []

    def add_camera(self, camera: Camera):
        self.cameras.append(camera)

    def remove_camera(self, camera_id: int):
        self.cameras = [cam for cam in self.cameras if cam.id != camera_id]

    def add_user(self, user: User):
        self.users.append(user)

    def remove_user(self, user_id: int):
        self.users = [usr for usr in self.users if usr.id != user_id]

    def __str__(self):
        return f'ID: {self.id}, Name: {self.name}, Договор: {self.contract}, Status: {self.status}' \
               f'MAX Cameras: {self.max_cameras}, Cameras: {self.num_cameras}' \
               f'MAX Users: {self.max_users}, Users: {self.num_users}'