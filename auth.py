from conf import login, password
import asyncio
import aiohttp
from bs4 import BeautifulSoup

class Auth:
    def __init__(self, session):
        self.session = session

    async def login(self, login_url, login_data):
        async with self.session.post(login_url, data=login_data) as response:
            return response.status == 200

    async def logout(self):
        # Реализация выхода пока нахуй ее...
        pass