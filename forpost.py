import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Optional, Dict
import re, json
from write_log import write_log
from auth import Auth
from account import Account
from camera import Camera
from user import User
from conf import login, password, target #conf.py -> target = 'https://cctv.my-forpost.ru' login = 'login' password ='pass'



class Forpost:
    '''
    Класс для работы с платформой видеонаблюдения forpost

    '''
    def __init__(self, target, login, password):
        '''
        Функция логина на сайт форпоста.

        :param target:
        :param login:
        :param password:
        '''
        self.target = target
        self.login_url = f"{target}/login.html"
        self.login_data = {
            'User[Login]': login,
            'User[Password]': password,
            'User[Remember]': '1',
        }
        self.session = None


    async def initialize(self):
        self.session = aiohttp.ClientSession()
        auth = Auth(self.session)
        if await auth.login(self.login_url, self.login_data):
            print("Логин выполнен успешно!")
        else:
            print("Не удалось выполнить логин.")


    async def search_account(self, contract_number):
        '''
        Функция поиска аккаунта по договору. на форпосте договор вводится в поле -Номер счета-
        Если аккаунт не найден возвращается переменная с текстом "Аккаунт не найден."
        Здесь же вызывается get_account(account.id) чтоб заполнить поля по аккаунту.
        Здесь же вызывается get_users(account.id) чтоб выяснить есть ли привязанные к аккаунту учетки пользователей,
        и если учетки есть то они добавляются к списку в аккаунт self.users = [].
        :param contract_number:
        :return: обьект Account с неполными данными(пока).
        в Account данные о id, Название, Номер счета и состояние (вкл\выкл), users = []
        '''
        accounts_url = f"{target}/admin/accounts.html"
        params = {
            'Account[ID]': '',
            'Account[Name]': '',
            'Account[CreationDate][from]': '',
            'Account[CreationDate][to]': '',
            'Account[ContractNumber]': contract_number,
            'Account[IsActive]': '',
            'Account_page': '1'
        }
        async with self.session.get(accounts_url, params=params) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')

                # Парсим таблицу аккаунтов
                accounts_table = soup.find('table')
                if accounts_table:
                    empty_message = accounts_table.find('td', class_='empty')
                    if empty_message and "Нет результатов" in empty_message.text:
                        account = "Аккаунт не найден."
                        print(f'{contract_number} - Аккаунт не найден.')
                        return account
                    else:
                        for row in accounts_table.find_all('tr'):
                            if 'filters' in row.get('class', []):
                                continue
                            columns = row.find_all('td')
                            if len(columns) >= 5:
                                account = Account()
                                account.id = columns[0].text.strip()
                                account.name = columns[1].text.strip()
                                account.contract = columns[3].text.strip()
                                account.status = columns[4].text.strip()
                                acc_info = await self.get_account(account.id)
                                account.max_cameras = acc_info.get('max_cameras')
                                account.max_users = acc_info.get('max_users')
                                account.num_users = acc_info.get('num_users')
                                account.num_cameras = acc_info.get('num_cameras')
                                users_table = await self.get_users(account.id)
                                if users_table:
                                    for user in users_table:
                                        account.add_user(user)
                                cameras_table = await self.get_cameras(account.id)
                                if cameras_table:
                                    for camera in cameras_table:
                                        account.add_camera(camera)
                                return account
                else:
                    account = "Не удалось найти таблицу аккаунтов."
                    return account
            else:
                account = "Не удалось получить страницу аккаунтов."
                return account


    async def get_account(self, id_account):
        '''
        Функция по ID аккаунту извлекает из форпоста информацию о количестве камер, учеток,
        максимальных лимитах камер и учеток.

        :param id_account: ID аккаунта
        :return: словарь
                        'max_cameras': max_cameras,
                        'max_users': max_users,
                        'num_users': num_users,
                        'num_cameras': num_cameras
        '''
        url = f"{target}/admin/account/{id_account}/view.html"
        async with self.session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                account_table = soup.find('table', class_='account')
                if account_table:
                    data = {}
                    for row in account_table.find_all('tr'):
                        th = row.find('th')
                        td = row.find('td')
                        if th and td:
                            key = th.text.strip()
                            value = td.text.strip()
                            data[key] = value
                    max_cameras = data.get('Максимальное количество камер', 'Не найдено')
                    max_users = data.get('Максимальное количество пользователей', 'Не найдено')
                    num_users = data.get('Количество пользователей', 'Не найдено')
                    num_cameras = data.get('Количество камер', 'Не найдено')

                    return {
                        'max_cameras': max_cameras,
                        'max_users': max_users,
                        'num_users': num_users,
                        'num_cameras': num_cameras
                    }
                else:
                    print("Не удалось найти таблицу аккаунта.")
            else:
                print("Не удалось получить страницу аккаунта.")


    async def get_users(self, id_account) -> dict[User]:
        """
        Функция по ID аккаунту извлекает из форпоста информацию о пользователях этого аккаунта,
        и возвращает словарь с обьектами User. пользователей может быть один, а может быть несколько.
        :param id_account:
        :return: пустой список если нет, или список с обьектами пользователями для данного аккаунта
        """
        url = f"{target}/admin/account/{id_account}/users.html"
        async with self.session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                users_table = soup.find('table', class_='table table-bordered table-striped')
                if users_table:
                    rows = users_table.find_all('tr')
                    user_rows = [row for row in rows if 'filters' not in row.get('class', []) and row.find('td')]
                    users = []
                    for row in user_rows:
                        columns = row.find_all('td')
                        if len(columns) >= 4:
                            user_id = columns[0].text.strip()
                            status = columns[1].text.strip()
                            date = columns[2].text.strip()
                            login = columns[3].text.strip()
                            user = User(id=user_id, login=login, status=status, password="Hide")
                            users.append(user)
                    return users
                else:
                    print("Не удалось найти таблицу пользователей.")
                    return []
            else:
                print("Не удалось получить страницу пользователей.")
                return []


    async def get_cameras(self, id_account) -> dict[Camera]:
        """
        Функция по ID аккаунту извлекает из форпоста информацию о камерах для заданого аккаунта.
        Камер может быть ноль, одна или несколько. Попутно вызывается еще одна функция которая по каждой камере
        извлекает дополнительные поля.
        Возвращает словарь с обьектами типа Camera

        :param id_account:
        :return: dict[Camera] словарь с камерами, или пустой словарь если на аккаунте нет камер.
        """
        url = f"{self.target}/admin/account/{id_account}/cameras.html"
        async with self.session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                cameras_table = soup.find('table', class_='table table-bordered table-striped')
                if not cameras_table:
                    return []
                rows = cameras_table.find_all('tr')
                camera_rows = [row for row in rows if 'filters' not in row.get('class', []) and row.find('td')]
                cameras = []
                for row in camera_rows:
                    columns = row.find_all('td')
                    if len(columns) >= 7:
                        camera_id = columns[0].text.strip()
                        name_tag = columns[1].find('a')
                        name = name_tag.text.strip() if name_tag else "Без названия"
                        camera_detail = await self.get_camera(id_account, camera_id)
                        camera = Camera(
                            id=camera_id,
                            name=name,
                            status= camera_detail.get('status'),
                            locations= camera_detail.get('location'),
                            record= camera_detail.get('record'),
                            mic= camera_detail.get('mic'),
                            ipaddress= camera_detail.get('ipaddress'),
                            port_onvif= camera_detail.get('port_onvif'),
                            port_http= camera_detail.get('port_http'),
                            speed= camera_detail.get('speed'),
                            login= camera_detail.get('login'),
                            password= camera_detail.get('password'),
                            model= camera_detail.get('model'),
                            stream= camera_detail.get('stream'),
                            videocodec= camera_detail.get('videocodec')
                        )
                        cameras.append(camera)
                return cameras
            else:
                print("Не удалось получить страницу камер.")
                return []


    async def get_camera(self, id_account, id_camera) -> dict:
        """
    Функция извлекает из форпоста все настройки камеры.

    Args:
        id_account (str): ID аккаунта
        id_camera (str): ID камеры

    Returns:
        dict: Словарь с параметрами камеры:
            - name (str)
            - status (str)
            - location (str)
            - record (str)
            - mic (str)
            - model (str)
            - speed (str)
            - ipaddress (str)
            - port_onvif (str)
            - port_http (str)
            - login (str)
            - password (str)
            - stream (str)
            - videocodec (str)
    """
        url = f"{target}/admin/account/{id_account}/camera/{id_camera}/view.html"
        name = "ХЗ"
        status = "ХЗ"
        locations = "ХЗ"
        record = "ХЗ"
        mic = "ХЗ"
        model = "ХЗ"
        speed = "ХЗ"
        ip_camera = 'ХЗ'
        port_onvif = 'ХЗ'
        port_http = 'ХЗ'
        login = 'ХЗ'
        password = 'ХЗ'
        stream = 'ХЗ'
        videocodec = 'ХЗ'
        async with self.session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                table = soup.find('table', {'id': 'yw2'})
                if not table:
                    return None
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if not th or not td:
                        continue
                    th_text = th.get_text(strip=True)
                    td_text = td.get_text(strip=True)
                    if th_text == "Состояние":
                        span = td.find('span')
                        if span:
                            status = span.get_text(strip=True)
                        else:
                            status = td.get_text(strip=True)
                    elif th_text == "Название":
                        name = td_text
                    elif th_text == "Адрес местонахождения":
                        locations = td_text
                    elif th_text == "Запись":
                        record = td_text
                    elif th_text == "Использовать микрофон":
                        mic = td_text
                    elif th_text == "Модель камеры":
                        model = td_text
            else:
                print(f"Не удалось получить страницу камеры {id_camera}. Статус: {response.status}")
                return None
        url_edit = f"{target}/admin/account/{id_account}/camera/{id_camera}/edit.html"
        async with self.session.get(url_edit) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                max_bandwidth_select = soup.find('select', {'id': 'Camera_MaxBandwidth'})
                if max_bandwidth_select:
                    selected_option = max_bandwidth_select.find('option', {'selected': 'selected'})
                    if selected_option:
                        speed = selected_option.get('value')
                    else:
                        speed = "ХЗ"
                else:
                    speed = "ХЗ"
                ip_camera_input = soup.find('input', {'id': 'Camera_IP'})
                if ip_camera_input:
                    ip_camera = ip_camera_input.get('value', 'ХЗ')
                else:
                    ip_camera = 'ХЗ'
                port_onvif_input = soup.find('input', {'id': 'Camera_Port'})
                if port_onvif_input:
                    port_onvif = port_onvif_input.get('value', 'ХЗ')
                else:
                    port_onvif = 'ХЗ'
                port_http_input = soup.find('input', {'id': 'Camera_HTTPPort'})
                if port_http_input:
                    port_http = port_http_input.get('value', 'ХЗ')
                else:
                    port_http = 'ХЗ'
                camera_Login_input = soup.find('input', {'id': 'Camera_Login'})
                if camera_Login_input:
                    login = camera_Login_input.get('value', 'ХЗ')
                else:
                    login = 'ХЗ'
                Camera_Password_input = soup.find('input', {'id': 'Camera_Password'})
                if Camera_Password_input:
                    password = Camera_Password_input.get('value', 'ХЗ')
                else:
                    password = 'ХЗ'
                stream_input = soup.find('input', {'id': 'Camera_MJPEG'})
                if stream_input:
                    stream = stream_input.get('value', 'ХЗ')
                else:
                    stream = 'ХЗ'
                videocodec_input = soup.find('select', {'id': 'Camera_VideoCodec'})
                if videocodec_input:
                    videocodec_select = videocodec_input.find('option', {'selected': True})
                    if videocodec_select:
                        videocodec = videocodec_select.get('value', 'h.264')
                    else:
                        videocodec  = 'h.264'
                else:
                    videocodec = 'h.264'

        return {
                'name': name,
                'status': status,
                'location': locations,
                'record': record,
                'mic': mic,
                'model': model,
                'speed': speed,
                'ipaddress': ip_camera,
                'port_onvif': port_onvif,
                'port_http': port_http,
                'login': login,
                'password': password,
                'stream': stream,
                'videocodec': videocodec
            }


#------------- Парсим все аккаунты ---------------------------
    async def get_all_accounts(self) -> dict:
        '''
        отдает все аккаунты из форпоста
        :return: словарь
        '''
        first_page_url = f"{target}/admin/accounts.html"
        all_accounts = {}
        first_page_data = await self._get_page(first_page_url)
        if not first_page_data:
            return None

        first_page_accounts = self._parse_account_page(first_page_data)
        if not first_page_accounts:
            return None

        all_accounts.update(first_page_accounts)
        pagination = first_page_data.select_one("div.pagination")
        if pagination:
            last_page_link = pagination.select_one("li.last a")
            if last_page_link:
                last_page_url = self.target + last_page_link["href"]
                last_page_number = int(re.search(r"Account_page=(\d+)", last_page_url).group(1))

                for page in range(2, last_page_number + 1):
                    page_url = f"{self.target}/admin/accounts.html?Account_page={page}"
                    page_data = await self._get_page(page_url)
                    if not page_data:
                        continue
                    page_accounts = self._parse_account_page(page_data)
                    if page_accounts:
                        all_accounts.update(page_accounts)

        return all_accounts


    async def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        async with self.session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                return BeautifulSoup(text, 'html.parser')
            return None


    def _parse_account_page(self, soup: BeautifulSoup) -> dict:
        '''
        Парсинг таблицы аккаунтов на элементы.
        :param soup:
        :return:
        '''
        table = soup.select_one("table.table")
        if not table:
            return {}
        accounts = {}
        rows = table.select("tr")
        for row in rows:
            if "filters" in row.get("class", []):
                continue

            cells = row.select("td")
            if len(cells) < 5:
                continue

            try:
                account_id = int(cells[0].get_text(strip=True))
            except ValueError:
                continue

            name_cell = cells[1]
            name_link = name_cell.select_one("a")
            name = name_link.get_text(strip=True) if name_link else name_cell.get_text(strip=True)
            created = cells[2].get_text(strip=True)
            contract = cells[3].get_text(strip=True)
            status = cells[4].get_text(strip=True)

            accounts[account_id] = {
                'name': name,
                'created': created,
                'contract': contract,
                'status': status
            }

        return accounts


#------------- Парсим все камеры ---------------------------
    async def get_all_cameras(self) -> Optional[Dict[int, dict]]:
        first_page_url = f"{target}/admin/cameras.html"
        all_cameras = {}

        first_page_data = await self._get_page(first_page_url)
        if not first_page_data:
            return None

        first_page_cameras = self._parse_cameras_page(first_page_data)
        if not first_page_cameras:
            return None

        all_cameras.update(first_page_cameras)
        pagination = first_page_data.select_one("div.pagination")
        if pagination:
            last_page_link = pagination.select_one("li.last a")
            if last_page_link:
                last_page_url = self.target + last_page_link["href"]
                last_page_number = int(re.search(r"Camera_page=(\d+)", last_page_url).group(1))

                for page in range(2, last_page_number + 1):
                    page_url = f"{self.target}/admin/cameras.html?Camera_page={page}"
                    page_data = await self._get_page(page_url)
                    if not page_data:
                        continue
                    page_cameras = self._parse_cameras_page(page_data)
                    if page_cameras:
                        all_cameras.update(page_cameras)

        return all_cameras


    def _parse_cameras_page(self, soup: BeautifulSoup) -> dict:
        '''
        Парсинг таблицы камер на элементы
        :param soup: одна страницы
        :return: словарь камер
        '''
        table = soup.select_one("table.table")
        if not table:
            print("Таблица камер не найдена на странице.")
            return {}

        cameras = {}
        rows = table.select("tr")
        for row in rows:
            if "filters" in row.get("class", []):
                continue

            cells = row.select("td")
            if len(cells) < 7:
                continue

            try:
                camera_id = int(cells[0].get_text(strip=True))
            except ValueError:
                print(f"Не удалось преобразовать ID камеры в число: {cells[0].get_text(strip=True)}")
                continue

            name_cell = cells[1]
            name_link = name_cell.select_one("a")
            if not name_link:
                print("Ссылка на камеру не найдена.")
                continue

            name = name_link.get_text(strip=True)
            href = name_link.get("href")
            if not href:
                print("Ссылка на камеру не содержит href.")
                continue

            match = re.search(r"/admin/account/(\d+)/camera/\d+/view\.html", href)
            if not match:
                print(f"Не удалось извлечь id_account из ссылки: {href}")
                continue
            id_account = int(match.group(1))
            is_on = cells[2].get_text(strip=True)
            is_record = cells[4].get_text(strip=True)
            created = cells[5].get_text(strip=True)
            cameras[camera_id] = {
                "name": name,
                "id_account": id_account,
                "is_on": is_on,
                "is_record": is_record,
                "created": created
            }

        return cameras



#------------- Блок функций записи и изменения информации -----------------------
    async def create_account(self, name:str, contract:str, max_cameras, max_users="5", shortname=None):
        '''
        Функция создает на форпосте аккаунт. Для этого требуется минимальное количество данных:
        ФИО, номер договора, и количество камер. max_users - максимальное количество учеток выставляем автоматом 5шт.

        :param name: Название (ФИО)
        :param contract: Договор
        :param max_cameras: Максимально разрешенное количество камер
        :param max_users: Максимально разрешенное количество пользователей, необязательный параметр, по умолчанию 5
        :param shortname: необязательный параметр, если его нет то ФИО укорачивается и складывается с договором.
        :return: возвращаем id_account
        '''
        if shortname == None:
            surname = name.split()[0]
            shortname = f"{surname} {contract}"
        url = f"{target}/admin/account/add.html"
        payload = {
            "Account[Name]": name,
            "Account[ShortName]": shortname,
            "Account[ContractNumber]": contract,
            "Account[MaxCameraCount]": max_cameras,
            "Account[MaxLoginCount]": max_users,
            "Account[MasterID]": "1",
            "Account[NetworkIP]": "0.0.0.0",
            "Account[NetworkMask]": "0.0.0.0",
            "Account[InternalServerAddr]": "",
            "Account[MaxCameraUserOnlineTranslationCount]": "2",
            "Account[MaxCameraUserArchivalTranslationCount]": "2",
            "Account[MaxCameraOnlineTranslationCount]": "2",
            "Account[MaxCameraArchivalTranslationCount]": "2",
            "Account[Quota]": "0",
            "Account[MaxSMSPerMonth]": "0",
            "Account[MaxFacePersonCount]": "0",
            "Account[IsActive]": "1",
            "Account[IsSupportEnabled]": "1",
            "submit": "Создать"
        }

        async with self.session.post(url, data=payload) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')

                account_link = soup.find('a', href=lambda href: href and '/admin/account/' in href)
                if account_link:
                    href = account_link.get('href')
                    id_account = href.split('/admin/account/')[1].split('/')[0]
                    print(f"✅ Аккаунт успешно создан. ID: {id_account}, договор: {contract}")
                    return id_account
                else:
                    print("⚠️ Не удалось извлечь ID аккаунта из ответа.")
                    return None
            else:
                print(f"❌ Ошибка при создании аккаунта. Статус: {response.status}")
                return None


    async def edit_account(self, id_account, name:str, contract:str, max_cameras, max_users, shortname=None):
        """
        Функция редактирует уже существующий аккаунт, для этого нам нужен ID аккаунта, плюс интересующие нас поля


        :param id_account: ID существующего аккаунта
        :param name: Название
        :param contract: Договор
        :param max_cameras: Максимально разрешенное количество камер
        :param max_users: Максимально разрешенное количество пользователей
        :param shortname: необязательный параметр, если его нет то ФИО укорачивается и складывается с договором.
        :return: True если аккаунт удалось изменить, или различные ошибки строкой.
        """
        url = f"{target}/admin/account/{id_account}/edit.html"
        if shortname == None:
            surname = name.split()[0]
            shortname = f"{surname} {contract}"
        payload = {
            "Account[Name]": name,
            "Account[ShortName]": shortname,
            "Account[ContractNumber]": contract,
            "Account[MaxCameraCount]": max_cameras,
            "Account[MaxLoginCount]": max_users,
            "Account[MasterID]": "1",
            "Account[NetworkIP]": "0.0.0.0",
            "Account[NetworkMask]": "0.0.0.0",
            "Account[InternalServerAddr]": "",
            "Account[MaxCameraUserOnlineTranslationCount]": "2",
            "Account[MaxCameraUserArchivalTranslationCount]": "2",
            "Account[MaxCameraOnlineTranslationCount]": "2",
            "Account[MaxCameraArchivalTranslationCount]": "2",
            "Account[Quota]": "0",
            "Account[MaxSMSPerMonth]": "0",
            "Account[MaxFacePersonCount]": "0",
            "Account[IsActive]": "1",
            "Account[IsSupportEnabled]": "1",
            "submit": "Сохранить"
        }
        async with self.session.post(url, data=payload) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')

                # Проверяем, что данные обновились
                account_name = soup.find('td', text=name)
                contract_number = soup.find('td', text=contract)
                max_camera_count = soup.find('td', text=str(max_cameras))
                max_login_count = soup.find('td', text=str(max_users))

                if all([account_name, contract_number, max_camera_count, max_login_count]):
                    print("✅ Аккаунт успешно отредактирован.")
                    return True
                else:
                    print("⚠️ Данные аккаунта не обновились. Проверьте вручную.")
                    return "⚠️ Данные аккаунта не обновились. Проверьте вручную."

            else:
                print(f"❌ Ошибка при редактировании аккаунта. Статус: {response.status}")
                if response.status == 404:
                    print("⚠️ Аккаунт с таким ID не существует.")
                    return "⚠️ Аккаунт с таким ID не существует."
                elif response.status == 403:
                    print("⚠️ Нет прав на редактирование аккаунта.")
                    return "⚠️ Нет прав на редактирование аккаунта."
                else:
                    print("⚠️ Неизвестная ошибка.")
                    return "⚠️ Неизвестная ошибка."


    async def close(self):
        if self.session:
            await self.session.close()


    async def add_user(self, login, password, account_id):
        """
        Создает пользователя в аккаунте.
        :param login: Логин
        :param password: Пароль
        :param account_id: ID аккаунта в котором создаем пользователя.
        :return: при ошибках возращает None, если пользвателя удалось создать возвращает ID
        """
        url = f"{self.target}/admin/account/{account_id}/user/add.html"
        payload = {
            "yform_userForm": "1",  # Скрытый input
            "User[Login]": login,
            "User[Password]": password,
            "User[PasswordRepeat]": password,
            "User[Email]": "",
            "User[Phone]": "",
            "User[Postcode]": "",
            "User[Region]": "",
            "User[Locality]": "",
            "User[Street]": "",
            "User[Home]": "",
            "User[TimeZone]": "",
            "User[IsActive]": "1",
            "User[CanChangeOwnInfo]": "0",
            "User[ChangePasswordAtNextLogin]": "0",
            "AccountUser[IsReadOnly]": "0",
            "User[IsAccessibleNewCameraByDefault]": "0",
            "submit": "Добавить"
        }

        async with self.session.post(url, data=payload) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                error_message = soup.select_one("div.errorMessage")
                if error_message and "уже занят" in error_message.get_text():
                    print(f'❌ Логин "{login}" уже занят. аккаунт: {account_id}')
                    return None
                error_message = soup.select_one("div.alert.alert-error")
                if error_message and "Достигнуто ограничение на количество пользователей." in error_message.get_text():
                    print(f"Ошибка: достигнуто ограничение на количество пользователей. аккаунт: {account_id}")
                    return None
                user_link = soup.find('a', href=lambda href: href and f'/admin/account/{account_id}/user/' in href)
                if user_link:
                    href = user_link.get('href')
                    user_id = href.split(f'/admin/account/{account_id}/user/')[1].split('/')[0]
                    user_id = int(user_id)
                    print(f"✅ Пользователь {login} создан. ID: {user_id}")
                    return user_id
                else:
                    print("⚠️ Не удалось извлечь ID пользователя из ответа.")
                    return None
            elif response.status == 500:
                text = await response.text()
                print(f"Ошибка 500: {text}")
                return None
            else:
                print(f"Ошибка запроса: {response.status} при создании user на аккаунте: {account_id}")
                return None


    async def change_user_password(self, account_id, user_id, password):
        """
        Меняет пароль на пользователе.
        :param account_id: ID аккаунта
        :param user_id: ID пользователя
        :param password: новый пароль
        :return: True\False
        """
        url = f"{self.target}/admin/account/{account_id}/user/{user_id}/password.html"
        payload = {
            "yform_userForm": "1",
            "User[Password]": password,
            "User[PasswordRepeat]": password,
            "User[ChangePasswordAtNextLogin]": "0",
            "User[EmailPassword]": "0",
            "submit": "Изменить пароль"
        }
        async with self.session.post(url, data=payload) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                breadcrumb = soup.select_one("ul.breadcrumb")
                if breadcrumb and f"admin/account/{account_id}/view.html" in str(breadcrumb):
                    print("✅ Пароль успешно изменён.")
                    return True
                print("⚠️ Не удалось определить результат изменения пароля.")
                return False
            elif response.status == 404:
                print("❌ Пользователь или аккаунт не найден.")
                return False
            elif response.status == 500:
                text = await response.text()
                print(f"❌ Ошибка 500: {text[:200]}...")
                return False
            else:
                print(f"❌ Ошибка запроса: {response.status}")
                return False


    async def add_camera(self, account_id, name, locations, ipaddress, port_onvif:int, port_http:int, login, password,
                         stream, videocodec,
                         record:int=0, mic:bool=False, speed:int=2048):
        """
        Функция создает камеру на форпосте под определенным аккаунтом. При успешном создании возвращается ID камеры.

        :param account_id: ID аккаунта, проверяется чтоб это было число.
        :param name: Имя камеры, отображается поверх изображения камеры.
        :param locations: Адрес местонахождения, просто справочная строка.
        :param ipaddress: IP камеры или доменное имя.
        :param port_onvif: порт rstp, стандартный для этого протокола порт 554(настраивается в камере)
        :param port_http: порт управления, обычно веб 80 или 8080(настраивается в камере)
        :param login: Логин для доступа к камере
        :param password: пароль для доступа к камере
        :param stream: Адрес потока. (для st-181 он к примеру /media/video1)
        :param videocodec: Кодек. Допустимые значения: H.264 или H.265
        :param record: Запись архива. Допустимые значения: 0-30, 45, 60, 90 дней. 0 - без хранения.
        :param mic: Используем микрофон - False или True
        :param speed: Битрейт. допустимые значения:
                       (128, 256, 512, 1024, 1536, 2048, 3072, 3584, 4096, 5120, 6144, 7168, 8192)
        :return: ID камеры
        """
        try:
            if not isinstance(account_id, int):
                try:
                    account_id = int(account_id)
                except ValueError:
                    print("Ошибка: account_id должен быть целым числом")
                    return None

            for port in [port_onvif, port_http]:
                if not isinstance(port, int):
                    try:
                        port = int(port)
                    except ValueError:
                        print("Ошибка: порты должны быть целыми числами")
                        return None

            valid_speeds = [128, 256, 512, 1024, 1536, 2048, 3072, 3584, 4096, 5120, 6144, 7168, 8192]
            if speed not in valid_speeds:
                speed = min(valid_speeds, key=lambda x: abs(x - speed))
                print(f"Предупреждение: скорость изменена на ближайшее допустимое значение: {speed}")

            if videocodec.lower() not in ['h.264', 'h.265']:
                print("Ошибка: недопустимый видеокодек. Допустимые значения: H.264 или H.265")
                return None
            videocodec = videocodec.upper()

            valid_record_days = list(range(0, 31)) + [45, 60, 90]
            if record not in valid_record_days:
                print("Ошибка: недопустимое значение записи. Допустимые значения: 0-30, 45, 60, 90 дней")
                return None

        except Exception as e:
            print(f"Ошибка валидации параметров: {str(e)}")
            return None

        url = f"{self.target}/admin/account/{account_id}/camera/wizard.html"

        payload = {
            "Camera[MACSettings]": "",
            "Camera[MasterID]": "1",
            "Camera[IP]": ipaddress,
            "Camera[Port]": str(port_onvif),
            "Camera[HTTPPort]": str(port_http),
            "Camera[Login]": login,
            "Camera[Password]": password,
            "Camera[CameraBrand]": "",
            "Camera[CameraModelID]": "",
            "Camera[Channel]": "",
            "Camera[Protocol]": "rtsp",
            "Camera[RtspTransport]": "",
            "Camera[MJPEG]": stream,
            "Camera[LightPath]": "",
            "Camera[Name]": name,
            "Camera[Address]": locations,
            "Camera[Coordinates][Lat]": "",
            "Camera[Coordinates][Lon]": "",
            "Camera[IsRecord]": "1",
            "Camera[MaxBandwidth]": str(speed),
            "Camera[RecordType]": "0" if record == 0 else "1",
            "Camera[SecretKey]": "0",
            "Camera[Quota]": str(record * 86400) if record > 0 else "",
            "Camera[IsSound]": "1" if mic else "0",
            "Camera[IsPTZEnabled]": "0",
            "Camera[PanOffset]": "",
            "Camera[VideoCodec]": videocodec
        }

        try:
            async with self.session.post(url, data=payload, headers={'Content-Type': 'application/x-www-form-urlencoded'}) as response:
                print(f"Статус ответа: {response.status}")
                print(f"Заголовки ответа: {response.headers}")
                response_text = await response.text()
                print(f"Полный ответ сервера:\n{response_text}")
                try:
                    response_data = json.loads(response_text)
                    if 'id' in response_data:
                        print(f"Успешно получен ID камеры: {response_data['id']}")
                        return int(response_data['id'])
                    elif 'Camera_MJPEG' in response_data:
                        print(f"Ошибка валидации: {response_data['Camera_MJPEG']}")
                        raise Exception("ID камеры не найден в JSON-ответе")
                    else:
                        raise Exception("ID камеры не найден в JSON-ответе")
                except json.JSONDecodeError:
                    soup = BeautifulSoup(response_text, 'html.parser')
                    print("Ответ не в формате JSON, пытаемся парсить HTML")
                    camera_id = None
                    for input_tag in soup.find_all('input', type='hidden'):
                        if 'name' in input_tag.attrs and 'id' in input_tag.attrs['name']:
                            camera_id = input_tag['value']
                            break

                    if camera_id:
                        return int(camera_id)
                    else:
                        raise Exception("Не удалось найти ID камеры в HTML-ответе")

        except Exception as e:
            print(f"Произошла ошибка: {str(e)}")
            return None




############ Сектор отладки ####################
async def main():
    fpost = Forpost(target, login, password)
    await fpost.initialize()
    await fpost.change_user_password(account_id=233, user_id=751, password="43214321")

    await fpost.close()






if __name__ == "__main__":

    asyncio.run(main())