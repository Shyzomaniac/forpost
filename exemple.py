import forpost
import asyncio
import datetime
from time import perf_counter
import os
import json
import account
from conf import login, password, target
from write_log import write_log

from account import Account
from camera import Camera
from user import User



async def test_1():
    # Ищем аккаунт по номеру договора или названию
    fpost = forpost.Forpost(target, login, password)
    await fpost.initialize()
    acc = await fpost.search_account('554455')
    if isinstance(acc, account.Account):
        print(f"Аккаунт ID: {acc.id}\n" 
              f"Имя: {acc.name}\n" 
              f"Договор: {acc.contract}\n" 
              f"Статус: {acc.status}\n" 
              f"Максимальное количество камер: {acc.max_cameras}\n" 
              f"Максимальное количество пользователей: {acc.max_users}\n" 
              f"Количество камер: {acc.num_cameras}\n" 
              f"Количество пользователей: {acc.num_users}"
              )
        for user in acc.users:
            print(f"ID: {user.id}, Логин: {user.login}, Статус: {user.status}, Пароль: {user.password}")
        if acc.cameras:
            print("Камеры:")
            for camera in acc.cameras:
                print(f"ID: {camera.id}, Name: {camera.name}, Статус: {camera.status}\n"
                      f"Местонахождение: {camera.locations}, Запись: {camera.record}, Микрофон: {camera.mic}\n"
                      f"IP: {camera.ipaddress}, http port: {camera.port_http}, onvif: {camera.port_onvif}\n"
                      f"Битрейт: {camera.speed}, Логин: {camera.login}, пароль: {camera.password}\n"
                      f"Модель: {camera.model}, адрес потока: {camera.stream}, кодек: {camera.videocodec}")
    else:
        print(acc)
    await fpost.close()


async def test_2():
    # создаем аккаунт, меняем аккаунт
    fpost = forpost.Forpost(target, login, password)
    await fpost.initialize()
    account_id = await fpost.create_account(name="Власов Виктор Сергеевич", contract="556677", max_cameras="2")
    #await forpost.edit_account(account_id=account_id, name="Vasia Pupkin", contract="889900", max_cameras="1", max_users="1")
    print(account_id)
    await fpost.close()


async def test_3():
    #выгребаем все аккаунты и записываем в файл
    now = datetime.datetime.now()
    fpost = forpost.Forpost(target, login, password)
    await fpost.initialize()
    accounts = await fpost.get_all_accounts()
    if accounts:
        print(f'аккаунтов: {len(accounts)}')
        with open("accounts.json", "w", encoding="utf-8") as f:
            json.dump(accounts, f, ensure_ascii=False, indent=4)
        print("Аккаунты успешно записаны в файл 'accounts.json'")
    else:
        print("Аккаунтов нет.")
    await fpost.close()
    end_time = datetime.datetime.now()
    print(f"Время работы функции: {end_time - now}")


async def test_4():
    # выгребаем все камеры и записываем в файл
    fpost = forpost.Forpost(target, login, password)
    await fpost.initialize()
    cameras = await fpost.get_all_cameras()
    if cameras:
        print(f'камер: {len(cameras)}')
        with open("cameras.json", "w", encoding="utf-8") as f:
            json.dump(cameras, f, ensure_ascii=False, indent=4)
        print("Камеры успешно записаны в файл 'cameras.json'")
    else:
        print("Камер нет.")
    await fpost.close()


async  def test_5():
    #читаем список камер из файла, мы его сделали в test_4(), и по списку камер выдергиваем подробности настройки камеры
    #цель - выявить камеры с битрейтом больше 2048
    cameras = {}
    cam_big_bitrate = {}
    try:
        with open('cameras.json', 'r', encoding='utf-8') as file:
            cameras = json.load(file)
    except FileNotFoundError:
        cameras = {}
        print(f'File not found')
    except json.JSONDecodeError:
        cameras = {}
        print('error decode into test_5() -> cameras')
    fpost = forpost.Forpost(target, login, password)
    await fpost.initialize()
    for camera_id, camera_data in cameras.items():
        cam = await fpost.get_camera(camera_data.get("account_id"), camera_id)
        speed = int(cam.get("speed"))
        if speed > 2048:
            print(f'ID камеры: {camera_id}, ID аккаунта: {camera_data.get("account_id")}\n{cam.get("speed")}')
            cam_big_bitrate[camera_id] = {"account_id": camera_data.get("account_id"), "speed":cam.get("speed")}
    if cam_big_bitrate:
        print(f"Количество камер с битрейтом более 2048: {len(cam_big_bitrate)}")
        with open("big_bitrate.json", "w", encoding="utf-8") as f:
            json.dump(cam_big_bitrate, f, ensure_ascii=False, indent=4)

    await fpost.close()


async def test_6():
    # создаем аккаунт, создаем в нем пользователя
    fpost = forpost.Forpost(target, login, password)
    await fpost.initialize()
    #account_id = await fpost.create_account(name="Vasia Pupkin", contract="556677", max_cameras="2")
    #print(f"account ID: {account_id}")
    user_ui = await fpost.add_user(login="1234512345", password="1234512345", account_id=969)
    print(f'user ID: {user_ui}')
    await fpost.close()


async def test_7():
    #Создаем камеру в существующем аккаунте с ID 969
    fpost = forpost.Forpost(target, login, password)
    await fpost.initialize()
    camera_id = await fpost.add_camera(
             account_id=969,
             name="camera1",
             locations="moscow",
             ipaddress="192.168.12.12",
             port_onvif=5541,
             port_http=8081,
             login="admin",
             password="admin",
             stream="/0",
             videocodec="H.264",
             speed=1819
         )
    print(f"ID добавленной камеры: {camera_id}")

    await fpost.close()


async def test_8():
    fpost = forpost.Forpost(target, login, password)
    await fpost.initialize()
    await fpost.edit_camera(
        account_id=969,
        id_camera=1598,
        name="Татаров А id-1493",
        locations="Бассеин",
        ipaddress="100.72.0.22",
        port_onvif=5543,
        port_http=8083,
        login="admin",
        password="1kbt7lbc",
        stream="/0",
        videocodec="H.264",
        OnvifMotionPort=True,
        resolution="1280x1024",
        motion=True,
        record=0,
        mic=True,
        speed=2048,
        isactive=True
    )
    await fpost.close()


async def backup_all_forpost():
    #выгребаем аккаунты, по аккаунтам выгребаем все что в них есть и пишем все это в файл + создаем json файл
    await write_log(f'backup_all_forpost: начинаем бекапить форпост полностью')
    now = datetime.datetime.now()
    date = now.strftime('%Y_%m_%d')
    big_backup:str = f"Бекап с форпоста за {now}\n"
    fpost = forpost.Forpost(target, login, password)
    await fpost.initialize()
    accounts = await fpost.get_all_accounts()
    print(f'Аккаунтов извлечено: {len(accounts)}')
    big_backup += f'{date}. Аккаунтов извлечено: {len(accounts)}\n\n'
    json_data = []
    for account_id, data in accounts.items():
        account: Account = await fpost.search_account(data.get("contract"))
        json_data.append(account.to_dict())
        big_backup += f"Аккаунт ID: {account.id}\n" \
                      f"Имя: {account.name}\n" \
                      f"Договор: {account.contract}\n" \
                      f"Статус: {account.status}\n" \
                      f"Максимальное количество камер: {account.max_cameras}\n" \
                      f"Максимальное количество пользователей: {account.max_users}\n" \
                      f"Количество камер: {account.num_cameras}\n" \
                      f"Количество пользователей: {account.num_users}\n"
        if account.users:
            big_backup += f"Пользователи:\n"
            for user in account.users:
                big_backup += f"ID: {user.id}, Логин: {user.login}, Статус: {user.status}, Пароль: {user.password}\n"
        if account.cameras:
            big_backup += f"Камеры:\n"
            for camera in account.cameras:
                big_backup += f"ID: {camera.id}, Name: {camera.name}, Статус: {camera.status}\n" \
                              f"Местонахождение: {camera.locations}, Запись: {camera.record}, Микрофон: {camera.mic}\n"\
                              f"IP: {camera.ipaddress}, http port: {camera.port_http}, onvif: {camera.port_onvif}\n"\
                              f"Битрейт: {camera.speed}, Логин: {camera.login}, пароль: {camera.password}\n"\
                              f"Модель: {camera.model}, адрес потока: {camera.stream}, кодек: {camera.videocodec}\n\n"
        big_backup += f"===========================================================================\n\n"

    os.makedirs('backup', exist_ok=True)
    json_filename = f'backup_{date}.json'
    json_file_path = os.path.join('backup', json_filename)
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)

    os.makedirs('backup', exist_ok=True)
    log_filename = f'backup_{date}.txt'
    file_path = os.path.join('backup', log_filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(big_backup)

    await fpost.close()
    await write_log(f'backup_all_forpost: закончили бекапить. записано {len(accounts)} аккаунтов')
    end_time = datetime.datetime.now()
    print(f"Время работы функции: {end_time - now}")


def load_accounts_from_json(file_path):
     #Читаем все аккаунты из json файла
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [Account.from_dict(item) for item in data]



async def main():

    await backup_all_forpost()

    '''
    accounts = load_accounts_from_json('backup/backup_2025_08_28.json')
    for account in accounts:
        print(f"Договор: {account.contract}, Камер: {len(account.cameras)}")

    '''



if __name__ == "__main__":
# Запуск основного цикла
    asyncio.run(main())
