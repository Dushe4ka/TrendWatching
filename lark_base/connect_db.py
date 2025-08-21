import requests
from datetime import datetime
import pandas as pd
import clickhouse_connect
from collections import Counter


APP_ID = "cli_a7764cea6af99029"
APP_SECRET = "sr8FEkHkNRWfI0OirUCQbg6EeeHv60fg"

TABLE_APP_ID = "VpuPbqXvsaVKewsMZe9l7auBgUg"
TABLE_ID_BASE_PARTICIPANTS = "tbliFeTLOkCUpCps"

def get_access_token():
    print("Получение токена доступа...")
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal/"
    payload = {"app_id": APP_ID, "app_secret": APP_SECRET}
    
    print(f"Отправка запроса на {url}")
    response = requests.post(url, json=payload)
    print(f"Статус ответа: {response.status_code}")
    
    response_data = response.json()
    print(f"Ответ сервера: {response_data}")
    
    token = response_data["tenant_access_token"]
    print(f"Успешно получен токен: {token[:10]}...")
    return token

def get_record_from_base(access_token):
    print("\nНачало получения записей из базы...")
    flag = True
    page_token = ""
    base_url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{TABLE_APP_ID}/tables/{TABLE_ID_BASE_PARTICIPANTS}/records"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    all_participants = []
    page_count = 0
    total_records = 0

    while flag:
        page_count += 1
        print(f"\nОбработка страницы {page_count}...")
        
        if page_token == "":
            print("Первая страница")
            response = requests.get(base_url, headers=headers)
        else:
            print(f"Следующая страница (токен: {page_token[:10]}...)")
            new_url = base_url + f"?page_token={page_token}"
            response = requests.get(new_url, headers=headers)
        
        print(f"Статус ответа: {response.status_code}")
        data = response.json()
        
        if len(data["data"]["items"]) > 0:
            records_on_page = len(data["data"]["items"])
            total_records += records_on_page
            print(f"Найдено записей на странице: {records_on_page}")
            
            if data["data"]["has_more"]:
                page_token = data["data"]["page_token"]
                print("Есть дополнительные страницы")
            else:
                flag = False
                print("Это последняя страница")
            
            for record in data["data"]["items"]:
                participant = {
                    'tg': record['fields'].get('Telegram'),
                    'role': record['fields'].get('Роль')
                }
                all_participants.append(participant)
                print(f"Добавлен участник: {participant}")
        else:
            print("Нет данных на странице")
            flag = False
    
    print(f"\nВсего обработано страниц: {page_count}")
    print(f"Всего получено записей: {total_records}")
    return all_participants

def print_role_statistics(participants):
    print("\nСтатистика по ролям:")
    print("-" * 30)
    
    # Собираем статистику по ролям
    roles = [p['role'] for p in participants if p['role']]
    role_counter = Counter(roles)
    
    if not role_counter:
        print("Нет данных о ролях")
        return
    
    # Выводим статистику
    for role, count in role_counter.most_common():
        print(f"{role}: {count} участников")
    
    print("-" * 30)
    print(f"Всего уникальных ролей: {len(role_counter)}")

if __name__ == "__main__":
    print("="*50)
    print("Начало выполнения скрипта")
    print(f"Время запуска: {datetime.now()}")
    print("="*50)

    try:
        # Получение токена
        token = get_access_token()
        
        # Получение данных
        print("\nЗапуск получения данных из базы...")
        participants = get_record_from_base(token)
        
        print("\nРезультаты:")
        print(f"Всего участников получено: {len(participants)}")
        print("Первые 5 записей:")
        for i, participant in enumerate(participants[:5]):
            print(f"{i+1}. TG: {participant['tg']}, Роль: {participant['role']}")
        
        # Вывод статистики по ролям
        print_role_statistics(participants)
        
        # Здесь можно добавить вывод в ClickHouse
        # print("\nЗапись данных в ClickHouse...")
        # ваш код для записи в БД
        
    except Exception as e:
        print(f"\nОШИБКА: {str(e)}")
    
    print("\n" + "="*50)
    print(f"Завершение работы скрипта в {datetime.now()}")
    print("="*50)