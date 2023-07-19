import pandas as pd
import cv2
import os
import re
import numpy as np
import datetime as dt
import Levenshtein as lev
import hashlib

from PIL import Image as PILImage
from img2table.document import Image
from pytesseract import Output
import pytesseract

# Предобработка изображений
def pre(img):
    try:
        height = int(img.shape[0])
    except:
        return('IT IS NOT AN IMAGE, DUDE')
    half = int(img.shape[0] / 2)
    cut = img[half:height, :]
    gray = cv2.cvtColor(cut, cv2.COLOR_BGR2GRAY)
    noise = cv2.medianBlur(gray,1)
    thresh = cv2.adaptiveThreshold(noise,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, \
                                   cv2.THRESH_BINARY,11,11)
    out = thresh
    return out


# Поиск координат ячеек таблицы
def search(pre_image_st, pre_image):
    #print('ищу ячейки в -', path, '\n')
    img = Image(pre_image_st, detect_rotation=False)
    #print('контрольная сумма файла для поиска ячеек, \n')
    #print(hashlib.sha1(open(path,'rb').read()).hexdigest())    
    extracted_tables = img.extract_tables()
    table_img = pre_image#(cv2.imread(path))
    print('размер-', table_img.shape, '\n')
    find_cell = []
    for table in extracted_tables:
        for row in table.content.values():
            for cell in row:
                cv2.rectangle(table_img, (cell.bbox.x1, cell.bbox.y1), \
                              (cell.bbox.x2, cell.bbox.y2), (255, 0, 0), 2)
                rect = [cell.bbox.y1, cell.bbox.y2, cell.bbox.x1, cell.bbox.x2]
                find_cell.append(rect)
    print('найдено ячеек', len(find_cell))
    if len(find_cell) < 5:
        return 'PREPROCESSING ERROR TRY ANOTHER IMAGE'
    else:
        return find_cell


# Распознавание числовых значений и дат
def numbers(cells, pre_image):
    cfg = r'--oem 3 --psm 7 outputbase digits'
    nums = []
    img = pre_image#(cv2.imread(path))
    #print('ищу цифры в -', path, '\n')
    print('размер-', img.shape, '\n')
    for place in cells:
        print(place)
        img_part = img[place[0]:place[1],place[2]:place[3]]
        print(pytesseract.image_to_string(img_part, lang='rus', config=cfg))
        nums.append(pytesseract.image_to_string(img_part, lang='rus', config=cfg))
    return nums


# Распознавание всего остального
def words(cells, pre_image):
    cfg = r'--oem 3 --psm 7'
    wds = []
    img = pre_image#(cv2.imread(path))
    for place in cells:
        img_part = img[place[0]:place[1],place[2]:place[3]]
        wds.append(pytesseract.image_to_string(img_part, lang='rus', config=cfg))
    return wds


# Объединение распознанных данных
def join_data(n, w):
    for i in range(len(n)):
        if n[i] == '':
            n[i] = w[i]
    return n


#Очистка выходных значений: оставляем только данные в формате "дата - 
#тип донации - объем", удаляем пробельные символы и точки из конца строки

def clean(list):
    stop_head = 0
    for i in range(len(list)):
        if re.search(r'\d{2}.\d{2}.\d{4}', list[i]):
            stop_head = i
            break
    cut_head = list[stop_head:]
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
        if clean_list[k][-1] == '.':
            clean_list[k] = clean_list[k][:-1]
        if clean_list[k][0] == '.':
            clean_list[k] = clean_list[k][1:]
    return clean_list


# Удаление записей с датой, больше текущей
def date_corr(d):
    td = dt.datetime.date(dt.datetime.today())
    if d > td:
        d = None
    return d

def date_output(dt):
    return dt.strftime("%Y-%m-%d")

# Формирование таблицы из распознанных значений и сортировка их по дате
def table(list):
    date = []
    volume = []
    don = []
    category = []
    error = []
    rec_counter = 0
    for i in range(len(list)):
        if re.fullmatch(r'\d{2}.\d{2}.\d{4}', list[i]):
            try:
                d = dt.datetime.strptime(list[i], '%d.%m.%Y')
                d = dt.datetime.date(d)
                rec_counter += 1
            except:
                d = None
            date.append(d)
        elif re.fullmatch(r'\d{3,4}', list[i]) and (50 <= int(list[i]) <= 750):
            volume.append(int(list[i]))
        elif re.search(r'[8, б, в, 6]', list[i].lower()) \
             or re.search(r'[п, л, д, т, ф]', list[i].lower()):
            don.append('Безвозмездно')
            if lev.distance(list[i], 'кр/д') < 5 or \
               lev.distance(list[i], 'ц/д') < 5 or \
               re.search(r'[ц, к, р]', list[i].lower()):
                category.append('Цельная кровь')
            elif lev.distance(list[i], 'пл/д') < 5 or \
                 lev.distance(list[i], 'п/ф') < 5 or \
                 re.search(r'[п, л]', list[i].lower()): 
                category.append('Плазма')
            elif lev.distance(list[i], 'т/ф') < 5 or \
                 re.search(r'[т, ф]', list[i].lower()):
                category.append('Тромбоциты')
        else:
            error.append(list[i])
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
        result['Дата донации'] = result['Дата донации'].apply(date_output)
        result = result.drop(['Объем, мл'], axis=1) #эххххх
        return result


def recognize_image(file: str):
    IMAGE_PATH = file
    print('предобработка для-', IMAGE_PATH, '\n')
    input_image = cv2.imread(IMAGE_PATH)
    preprocessed_image = pre(input_image)
    if type(preprocessed_image) == str:
        status = 'Файл не может быть распознан. Пожалуйста, загрузите изображение'
        out_json = ''
        out_file = ''
        return out_json, status, out_file
    #pre_path = 'tmp/' + re.sub(r'\D', '', IMAGE_PATH) + '.png'
    #cv2.imwrite(pre_path, preprocessed_image)
    pre_img = cv2.imencode('.png', preprocessed_image)[1].tostring()
    #print('контрольная сумма файла после предобработки, \n')
    #print(hashlib.sha1(open(pre_path,'rb').read()).hexdigest())    
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
    
