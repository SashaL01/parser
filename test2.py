import os
import csv
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import random
# Функция для сохранения изображения
def save_image(url, folder, filename):
    if not os.path.exists(folder):
        os.makedirs(folder)
    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(os.path.join(folder, filename), 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Изображение сохранено: {filename}")
        else:
            print(f"Не удалось загрузить изображение: {url} (статус {response.status_code})")
    except Exception as e:
        print(f"Ошибка при загрузке изображения {url}: {e}")

# Функция для инициализации браузера с настройками игнорирования SSL ошибок
def init_driver():
    options = Options()
    # Удалите или закомментируйте следующую строку для запуска браузера в обычном режиме
    # options.add_argument('--headless')  
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

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

# Функция для извлечения carid из URL
def extract_carid(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    carid = query_params.get('carid', [None])[0]
    return carid

# Функция для извлечения ссылок на страницы деталей автомобилей из каталога
def get_car_links(driver, catalog_url, pages=1):
    car_links = []
    driver.get(catalog_url)

    try:
        # Явное ожидание загрузки элементов списка автомобилей
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="dc_cardetailview.do"]')))
    except Exception as e:
        print("Ошибка при загрузке каталога:", e)
        return car_links

    for page_num in range(1, pages + 1):
        print(f'Парсинг страницы каталога {page_num}...')

        # Получение HTML-кода страницы
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Поиск всех ссылок на страницы деталей автомобилей
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            if 'dc_cardetailview.do' in href:
                full_link = 'https://www.encar.com' + href if href.startswith('/') else href
                carid = extract_carid(full_link)
                if carid and full_link not in car_links:
                    car_links.append(full_link)
                    print(f"Добавлена ссылка: {full_link}")

        # Переход на следующую страницу каталога, если необходимо
        if page_num < pages:
            try:
                next_button = driver.find_element(By.LINK_TEXT, '다음')  # "다음" означает "Следующая" на корейском
                next_button.click()
                # Ожидание загрузки новой страницы
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="dc_cardetailview.do"]')))
                time.sleep(2)  # Дополнительная задержка для полной загрузки
            except Exception as e:
                print("Больше страниц нет или произошла ошибка при переходе:", e)
                break

    return car_links








# Функция для извлечения данных с страницы детали автомобиля
def parse_car_detail(driver, car_url, retries=3):
    attempt = 0
    while attempt < retries:
        try:
            driver.get(car_url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.prod_name'))
            )
            # Добавление случайной задержки для полной загрузки страницы
            time.sleep(random.uniform(2, 4))  

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Извлечение названия
            name_tag = soup.find('strong', class_='prod_name')
            if name_tag:
                brand = name_tag.find('span', class_='brand').get_text(strip=True) if name_tag.find('span', class_='brand') else ''
                detail = name_tag.find('span', class_='detail').get_text(strip=True) if name_tag.find('span', class_='detail') else ''
                name = f"{brand} {detail}".strip()
            else:
                name = 'Неизвестно'

            # Извлечение цены
            price_tag = soup.find('em', class_='emph_price')
            if price_tag:
                # Очистка цены от лишних символов
                price = price_tag.get_text(strip=True).replace('won', '').replace(',', '').strip()
            else:
                price = 'Неизвестно'

            # Инициализация словаря для хранения информации
            car_info = {
                'Пробег': 'Неизвестно',
                'Дата сборки': 'Неизвестно',
                'Топливо': 'Неизвестно',
                'Двигатель': 'Неизвестно',
                'Коробка передач': 'Неизвестно',
                'Цвет': 'Неизвестно',
                'Номер автомобиля': 'Неизвестно'
            }

            # Извлечение информации из списка
            info_ul = soup.find('ul', class_='list_carinfo')
            if info_ul:
                li_items = info_ul.find_all('li')
                for li in li_items:
                    span_blind = li.find('span', class_='blind')
                    if span_blind:
                        label = span_blind.get_text(strip=True).rstrip(':').lower()
                        # Получение текста непосредственно после span.blind
                        # Используем метод next_sibling, чтобы избежать вложенных тегов
                        value = span_blind.next_sibling
                        if value:
                            value = value.strip()
                            # Очистка значения от лишних символов, например, вопросительных знаков
                            value = value.replace('?', '').strip()
                        else:
                            # Если прямой текст не найден, пытаемся найти текст внутри дочерних тегов
                            value = li.get_text(separator=' ', strip=True).replace(span_blind.get_text(strip=True), '').strip()
                            if not value:
                                value = 'Неизвестно'

                        # Соответствие меток полям
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

            return {
                'Название': name,
                'Пробег': car_info['Пробег'],
                'Дата сборки': car_info['Дата сборки'],
                'Топливо': car_info['Топливо'],
                'Двигатель': car_info['Двигатель'],
                'Коробка передач': car_info['Коробка передач'],
                'Цвет': car_info['Цвет'],
                'Номер автомобиля': car_info['Номер автомобиля'],
                'Цена': price,
                'Фотографии': ', '.join(image_paths)
            }

        except Exception as e:
            attempt += 1
            print(f"Попытка {attempt} не удалась при парсинге {car_url}: {e}")
            # Добавление случайной задержки перед повторной попыткой
            time.sleep(random.uniform(3, 6))  

    # Если все попытки не удались, возвращаем None
    print(f"Не удалось спарсить страницу после {retries} попыток: {car_url}")
    # Сохранение HTML-кода для отладки
    with open('error_page.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    return None




# Основная функция парсинга
def parse_encar(catalog_url, catalog_pages=1):
    driver = init_driver()
    try:
        all_cars = []
        car_links = get_car_links(driver, catalog_url, pages=catalog_pages)

        print(f'Всего найдено {len(car_links)} автомобилей.')

        for idx, car_link in enumerate(car_links, start=1):
            print(f'Парсинг автомобиля {idx}/{len(car_links)}: {car_link}')
            car_data = parse_car_detail(driver, car_link)
            if car_data:
                all_cars.append(car_data)
                print(f"Данные собраны для: {car_link}")
            else:
                print(f'Не удалось спарсить данные для {car_link}')
            time.sleep(1)  # Задержка между запросами

        return all_cars
    finally:
        driver.quit()

if __name__ == "__main__":
    # URL каталога автомобилей
    catalog_url = "https://www.encar.com/dc/dc_carsearchlist.do?carType=kor&searchType=model&TG.R=A#!%7B%22action%22%3A%22(And.Hidden.N._.CarType.Y.)%22%2C%22toggle%22%3A%7B%7D%2C%22layer%22%3A%22%22%2C%22sort%22%3A%22ModifiedDate%22%2C%22page%22%3A1%2C%22limit%22%3A20%2C%22searchKey%22%3A%22%22%2C%22loginCheck%22%3Afalse%7D"
    number_of_pages = 1  # Укажите количество страниц каталога для парсинга

    data = parse_encar(catalog_url, catalog_pages=number_of_pages)
    
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
