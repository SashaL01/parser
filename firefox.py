import os
import csv
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Функция для сохранения изображения
def save_image(url, folder, filename):
    if not os.path.exists(folder):
        os.makedirs(folder)
    try:
        response = requests.get(url, stream=True, timeout=20)
        if response.status_code == 200:
            with open(os.path.join(folder, filename), 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Изображение сохранено: {filename}")
        else:
            print(f"Не удалось загрузить изображение: {url} (статус {response.status_code})")
    except Exception as e:
        print(f"Ошибка при загрузке изображения {url}: {e}")

# Функция для инициализации браузера
def init_driver():
    options = Options()
    # Запуск браузера в обычном режиме для отладки
    # options.add_argument('--headless')  # Раскомментируйте для headless режима
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')  
    options.add_argument('--ignore-ssl-errors')          
    options.add_argument('--allow-insecure-localhost')   
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-web-security')
    options.add_argument('--window-size=1920,1080')
    # Опционально: измените User-Agent для имитации реального пользователя
    # options.add_argument("user-agent=Mozilla/5.0 ...")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

# Функция для проверки, существует ли страница
def page_exists(driver, url):
    driver.get(url)
    time.sleep(2)  # Ждём пару секунд
    # Проверяем, загрузилась ли страница с деталями автомобиля
    if "페이지를 찾을 수 없습니다" in driver.page_source:
        return False
    return True

# Функция для извлечения данных с страницы детали автомобиля
def parse_car_detail(driver, car_url):
    driver.get(car_url)
    time.sleep(2)  # Добавляем задержку для загрузки страницы
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Проверка наличия страницы
    if soup.find('div', class_='error_page'):
        print(f"Страница {car_url} не найдена.")
        return None
    
    # Извлечение названия
    name_tag = soup.find('strong', class_='prod_name')
    if name_tag:
        brand = name_tag.find('span', class_='brand').get_text(strip=True) if name_tag.find('span', class_='brand') else ''
        detail = name_tag.find('span', class_='detail').get_text(strip=True) if name_tag.find('span', class_='detail') else ''
        name = f"{brand} {detail}".strip()
    else:
        name = 'Неизвестно'

    # Извлечение других данных из <ul class="list_carinfo">
    car_info = {
        'Пробег': 'Неизвестно',
        'Дата сборки': 'Неизвестно',
        'Топливо': 'Неизвестно',
        'Двигатель': 'Неизвестно',
        'Коробка передач': 'Неизвестно',
        'Цвет': 'Неизвестно',
        'Номер автомобиля': 'Неизвестно'
    }

    info_ul = soup.find('ul', class_='list_carinfo')
    if info_ul:
        li_items = info_ul.find_all('li')
        for li in li_items:
            span_blind = li.find('span', class_='blind')
            if span_blind:
                label = span_blind.get_text(strip=True).rstrip(':').lower()
                # Получение текста после спана
                value = li.get_text(separator=' ', strip=True).replace(span_blind.get_text(strip=True), '').strip()
                if label == 'mileage':
                    car_info['Пробег'] = value
                elif label == 'year':
                    car_info['Дата сборки'] = value
                elif label == 'fuel':
                    car_info['Топливо'] = value
                elif label == 'displacement':
                    car_info['Двигатель'] = value
                elif label == 'transmission':
                    car_info['Коробка передач'] = value
                elif label == 'color':
                    car_info['Цвет'] = value
                elif label == 'vehicle number':
                    car_info['Номер автомобиля'] = value

    # Извлечение цены
    price_tag = soup.find('strong', class_='pay')
    if price_tag:
        price = price_tag.get_text(strip=True)
    else:
        price = 'Неизвестно'

    # Извлечение ссылок на фотографии из <div class="gallery_thumbnail">
    images_div = soup.find('div', class_='gallery_thumbnail')
    image_urls = []
    if images_div:
        img_tags = images_div.find_all('img', class_='photo_s')
        for img in img_tags:
            img_url = img.get('src')
            if img_url:
                # Обработка URL изображения
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = 'https://www.encar.com' + img_url
                # Удаление параметров запроса
                img_url = img_url.split('?')[0]
                image_urls.append(img_url)

    # Сохранение фотографий
    image_paths = []
    for idx, img_url in enumerate(image_urls, start=1):
        img_filename = os.path.basename(img_url)
        save_image(img_url, 'images', img_filename)
        image_path = os.path.join('images', img_filename)
        image_paths.append(image_path)

    # Возвращаем собранные данные
    return {
        'Название': name,
        'Пробег': car_info['Пробег'],
        'Дата сборки': car_info['Дата сборки'],
        'Топливо': car_info['Топливо'],
        'Цена': price,
        'Фотографии': ', '.join(image_paths)
    }

# Основная функция парсинга
def parse_encar():
    driver = init_driver()
    try:
        all_cars = []

        base_url = "http://www.encar.com/dc/dc_cardetailview.do?pageid=dc_carsearch&listAdvType=word&carid={carid}&view_type=hs_ad&wtClick_korList=007&advClickPosition=kor_word_p{p}_g{g}"

        # Задайте диапазоны для p и g
        p_range = range(1, 11)  # от 1 до 10
        g_range = range(1, 22)  # от 1 до 21

        # Задайте диапазон для carid
        carid_start = 38000000
        carid_end = 38001000

        for p in p_range:
            for g in g_range:
                for carid in range(carid_start, carid_end):
                    car_url = base_url.format(carid=carid, p=p, g=g)
                    print(f"Проверка URL: {car_url}")
                    # Проверяем, существует ли страница
                    if page_exists(driver, car_url):
                        print(f'Парсинг автомобиля: {car_url}')
                        car_data = parse_car_detail(driver, car_url)
                        if car_data:
                            all_cars.append(car_data)
                    else:
                        print(f"Страница {car_url} не найдена.")
                    time.sleep(1)  # Задержка между запросами

        return all_cars
    finally:
        driver.quit()

if __name__ == "__main__":
    data = parse_encar()

    # Сохранение результатов в файл CSV
    if data:
        keys = data[0].keys()
        with open('encar_cars.csv', 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
        print(f"Парсинг завершён. Данные сохранены в 'encar_cars.csv'.")
    else:
        print("Нет данных для сохранения.")

    # Вывод данных в консоль
    for car in data:
        print(car)
