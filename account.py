from camera import Camera
from user import User

class Account:
    def __init__(self, id=0, name='', contract='', status='',
                 max_cameras=0, max_users=0):
        self.id = id
        self.name = name
        self.contract = contract
        self.status = status
        self.max_cameras = self._to_int(max_cameras)
        self.max_users = self._to_int(max_users)
        self.cameras = []
        self.users = []

    @property
    def num_cameras(self):
        return len(self.cameras)

    @property
    def num_users(self):
        return len(self.users)

    def _to_int(self, value):
        try:
            return int(value)
        except ValueError:
            return 0

    def add_camera(self, camera: Camera):
        self.cameras.append(camera)

    def remove_camera(self, camera_id: int):
        self.cameras = [cam for cam in self.cameras if cam.id != camera_id]

    def add_user(self, user: User):
        self.users.append(user)

    def remove_user(self, user_id: int):
        self.users = [usr for usr in self.users if usr.id != user_id]

    def __str__(self):
        return (f'ID: {self.id}, Name: {self.name}, Договор: {self.contract}, Status: {self.status}\n'
                f'MAX Cameras: {self.max_cameras}, Cameras: {self.num_cameras}\n'
                f'MAX Users: {self.max_users}, Users: {self.num_users}')

    @property
    def max_cameras(self):
        return self._max_cameras

    @max_cameras.setter
    def max_cameras(self, value):
        self._max_cameras = self._to_int(value)
        if self._max_cameras < 0:
            self._max_cameras = 0

    @property
    def max_users(self):
        return self._max_users

    @max_users.setter
    def max_users(self, value):
        self._max_users = self._to_int(value)
        if self._max_users < 0:
            self._max_users = 0

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contract': self.contract,
            'status': self.status,
            'max_cameras': self.max_cameras,
            'max_users': self.max_users,
            'cameras': [camera.to_dict() for camera in self.cameras],
            'users': [user.to_dict() for user in self.users]
        }

    @classmethod
    def from_dict(cls, data):
        account = cls(
            id=data.get('id'),
            name=data.get('name'),
            contract=data.get('contract'),
            status=data.get('status'),
            max_cameras=data.get('max_cameras'),
            max_users=data.get('max_users')
        )
        account.cameras = [Camera.from_dict(camera) for camera in data.get('cameras', [])]
        account.users = [User.from_dict(user) for user in data.get('users', [])]
        return account