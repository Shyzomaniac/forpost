
class User:
    def __init__(self, id=0, login=0, status=0, password=0):
        self.id = id
        self.login = login
        self.status = status
        self.password = password

    def edit_user(self, status, username, password):
        self.status = status
        self.username = username
        self.password =password

    def __str__(self):
        return f'ID: {self.id}, Status: {self.status}, Login: {self.login}, pass: {self.password}'

    def to_dict(self):
        return {
            'id': self.id,
            'login': self.login,
            'password': self.password,
            'status': self.status
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)