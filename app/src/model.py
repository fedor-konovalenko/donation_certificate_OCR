import pandas as pd
import cv2
import os
import re
import numpy as np
import datetime as dt
import Levenshtein as lev
import logging

#import hashlib

m_logger = logging.getLogger(__name__)
m_logger.setLevel(logging.DEBUG)
handler_m = logging.StreamHandler()#FileHandler(f"{__name__}.log", mode='w')
formatter_m = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
handler_m.setFormatter(formatter_m)
m_logger.addHandler(handler_m)


from PIL import Image as PILImage
from img2table.document import Image
import pytesseract

def pre(img: np.array) -> np.array:
    """Предобработка изображений: обрезка, монохром, контраст"""
    try:
        height = int(img.shape[0])
    except:
        m_logger.error(f'incorrect file')
        return('IT IS NOT AN IMAGE, DUDE')
    half = int(img.shape[0] / 2)
    cut = img[half:height, :]
    gray = cv2.cvtColor(cut, cv2.COLOR_BGR2GRAY)
    noise = cv2.medianBlur(gray,1)
    thresh = cv2.adaptiveThreshold(noise,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, \
                                   cv2.THRESH_BINARY,11,11)
    out = thresh
    return out


def search(pre_image_st: str, pre_image: np.array) -> list:
    """Поиск координат ячеек таблицы (построчно)"""
    img = Image(pre_image_st, detect_rotation=False) 
    extracted_tables = img.extract_tables()
    table_img = pre_image
    find_cell = []
    for table in extracted_tables:
        for row in table.content.values():
            for cell in row:
                rect = [cell.bbox.x1, cell.bbox.y1, cell.bbox.x2, cell.bbox.y2]
                if (rect[3] - rect[1] > 10) and (rect[2] - rect[0] > 5) and (rect[3] < pre_image.shape[0]) and (rect[2] < pre_image.shape[1]):
                    find_cell.append(rect)
    m_logger.debug(f'найдено ячеек {len(find_cell)}')
    if len(find_cell) < 5:
        m_logger.error(f'no table found')
        return 'PREPROCESSING ERROR TRY ANOTHER IMAGE'
    else:
        return find_cell


def numbers(cells: list, pre_image: np.array) -> list:
    """распознавание чисел и дат"""
    cfg = r'--oem 3 --psm 7 outputbase digits'
    nums = []
    img = pre_image
    for place in cells:   
        img_part = img[place[1]:place[3],place[0]:place[2]]
        nums.append(pytesseract.image_to_string(img_part, lang='rus', config=cfg))
    return nums

def words(cells: list, pre_image: np.array) -> list:
    """Распознавание всего остального"""
    cfg = r'--oem 3 --psm 7'
    wds = []
    img = pre_image
    for place in cells:
        img_part = img[place[1]:place[3],place[0]:place[2]]
        wds.append(pytesseract.image_to_string(img_part, lang='rus', config=cfg))
    return wds


def join_data(numbers: list, words: list) -> list:
    """Объединение распознанных данных"""
    for i in range(len(numbers)):
        if numbers[i] == '':
            numbers[i] = words[i]
    return numbers


def clean(tess_result: list) -> list:
    """Очистка выходных значений: 
    
    оставляем только данные в формате "дата - тип донации - объем", 
    удаляем пробельные символы и точки из конца строки
    """
    stop_head = 0
    for i in range(len(tess_result)):
        if re.search(r'\d{2}.\d{2}.\d{4}', tess_result[i]):
            stop_head = i
            break
    cut_head = tess_result[stop_head:]
    for j in range(len(cut_head)-1, 0, -1):
        if re.search(r'\d{2,}', cut_head[j]):
            stop_tail = j
            break
    cut_tail = cut_head[:j+1]
    clean_list = cut_tail
    clean_counter = 0
    for k in range(len(clean_list)):
        if (not (re.search(r'\d{2}.\d{2}.\d{4}', clean_list[k]) or \
        re.search(r'\d{2,}', clean_list[k]) or \
        re.fullmatch(r'\w{,2}\s', clean_list[k]))):
            clean_list[k] = 'unknown'
            clean_counter += 1
        clean_list[k] = re.sub(r'\s', '', clean_list[k])
        clean_list[k] = re.sub(r'[-, =]', '', clean_list[k])
        if clean_list[k] == '':
            clean_list[k] = 'unknown'
        if clean_list[k][-1] == '.':
            clean_list[k] = clean_list[k][:-1]
        if clean_list[k][0] == '.':
            clean_list[k] = clean_list[k][1:]
    return clean_list


def date_corr(d: dt.datetime) -> dt.datetime:
    """Удаление записей с датой больше текущей"""
    td = dt.datetime.date(dt.datetime.today())
    if d > td:
        d = None
    return d

def table(final_list: list) -> pd.DataFrame:
    """Формирование таблицы из распознанных значений и сортировка их по дате"""
    date = []
    volume = []
    don = []
    category = []
    error = []
    rec_counter = 0
    for i in range(len(final_list)):
        if re.fullmatch(r'\d{2}.\d{2}.\d{4}', final_list[i]):
            try:
                d = dt.datetime.strptime(final_list[i], '%d.%m.%Y')
                d = dt.datetime.date(d)
                rec_counter += 1
            except:
                d = None
            date.append(d)
        elif re.fullmatch(r'\d{3,4}', final_list[i]) and \
            (50 <= int(final_list[i]) <= 750):
            volume.append(int(final_list[i]))
        elif re.search(r'[8, б, в, 6]', final_list[i].lower()) \
             or re.search(r'[п, л, д, т, ф]', final_list[i].lower()):
            don.append('Безвозмездно')
            if any([lev.distance(final_list[i], 'кр/д') < 5, \
               lev.distance(final_list[i], 'ц/д') < 5, \
               re.search(r'[ц, к, р]', final_list[i].lower())]):
                category.append('Цельная кровь')
            elif any([lev.distance(final_list[i], 'пл/д') < 5, \
                 lev.distance(final_list[i], 'п/ф') < 5, \
                 re.search(r'[п, л]', final_list[i].lower())]): 
                category.append('Плазма')
            elif any([lev.distance(final_list[i], 'т/ф') < 5, \
                 re.search(r'[т, ф]', final_list[i].lower())]):
                category.append('Тромбоциты')
        else:
            error.append(final_list[i])
            volume.append('unknown')
            category.append('unknown')
            don.append('unknown')
    if rec_counter == 0:
        return 'RECOGNITION ERROR TRY ANOTHER IMAGE'
    else:
        result = pd.concat([pd.Series(date), pd.Series(volume), \
                            pd.Series(don), pd.Series(category)], axis=1)
        result = result.rename(columns={0: "Дата донации", 1: "Объем, мл", \
                                        2: "Тип донации", 3: "Класс крови"})
        result = result.dropna(subset=["Дата донации"]).reset_index(drop=True)
        result = result.fillna(0)
        result = result.drop_duplicates(subset=["Дата донации"]).reset_index(drop=True)
        result = result.sort_values(by='Дата донации')
        result['Дата донации'] = result['Дата донации'].apply(date_corr)
        result = result.dropna(subset=["Дата донации"]).reset_index(drop=True)
        result['Дата донации'] = result['Дата донации'].\
            apply(lambda x: x.strftime("%Y-%m-%d"))
        result = result.drop(['Объем, мл'], axis=1) #эххххх
        return result


def recognize_image(file: str):
    IMAGE_PATH = file
    input_image = cv2.imread(IMAGE_PATH)
    preprocessed_image = pre(input_image)
    if type(preprocessed_image) == str:
        status = 'Файл не может быть распознан. Пожалуйста, загрузите изображение'
        out_json = ''
        out_file = ''
        return out_json, status, out_file
    pre_img = cv2.imencode('.png', preprocessed_image)[1].tostring()
    cell = search(pre_img, preprocessed_image)
    if type(cell) == str:
        status = 'Ошибка распознавания. Попробуйте другое изображение'
        out_json = ''
        out_file = ''
        return out_json, status, out_file
    n = numbers(cell, preprocessed_image)
    w = words(cell, preprocessed_image)
    raw_out = (join_data(n, w))
    cleaned_out = clean(raw_out)
    out_data = table(cleaned_out)
    if type(out_data) == str:
        status = 'Ошибка распознавания. Попробуйте другое изображение'
        out_json = ''
        out_file = ''
        return out_json, status, out_file
    name = 'tmp/' + re.sub(r'\D', '', IMAGE_PATH) + '.csv'
    out_json = out_data.to_json(orient='table', force_ascii=False)
    out_file = out_data.to_csv(name)
    if out_data.shape[0] * out_data.shape[1] < len(cell):
        status = 'Изображение распознано. Есть нераспознанные ячейки'
    else:
        status = 'Изображение распознано'
    return out_json, status, name        
    
