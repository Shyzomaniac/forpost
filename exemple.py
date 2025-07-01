import forpost
import asyncio
import json
import account
from conf import login, password, target





async def test_1():
    # Ищем аккаунт по номеру договора или названию
    fpost = forpost.Forpost(target, login, password)
    await fpost.initialize()
    acc = await forpost.search_account('Сайт')
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
    id_account = await fpost.create_account(name="Власов Виктор Сергеевич", contract="556677", max_cameras="6")
    #await forpost.edit_account(id_account="919", name="Vlasov Viktor Sergeevich", contract="889900", max_cameras="1", max_users="1")
    print(id_account)
    await fpost.close()


async def test_3():
    #выгребаем все аккаунты и записываем в файл
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
        cam = await fpost.get_camera(camera_data.get("id_account"), camera_id)
        speed = int(cam.get("speed"))
        if speed > 2048:
            print(f'ID камеры: {camera_id}, ID аккаунта: {camera_data.get("id_account")}\n{cam.get("speed")}')
            cam_big_bitrate[camera_id] = {"id_account": camera_data.get("id_account"), "speed":cam.get("speed")}
    if cam_big_bitrate:
        print(f"Количество камер с битрейтом более 2048: {len(cam_big_bitrate)}")
        with open("big_bitrate.json", "w", encoding="utf-8") as f:
            json.dump(cam_big_bitrate, f, ensure_ascii=False, indent=4)

    await fpost.close()



async def main():

    await test_5()



if __name__ == "__main__":
# Запуск основного цикла
    asyncio.run(main())