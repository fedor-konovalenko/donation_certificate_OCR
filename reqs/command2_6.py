#!/usr/bin/env python
# coding: utf-8

# # Предобработка данных

# ## Импорт библиотек

# In[47]:


import pandas as pd
import os

import pytesseract
from PIL import Image

import cv2

pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'


# ## Загрузка и осмотр данных

# In[41]:


shape_counter = 0
nan_counter = 0
columns = 10
df_list = []

for filename in os.listdir('405/'):
    if 'csv' in filename:
        path = '405/' + filename
        df = pd.read_csv(path)
        print('\n', filename)
        print(df.head())
        df_list.append(df)
        if df.shape[1] != columns:
            shape_counter += 1
        if df.isna().sum().sum() != 0:
            nan_counter += 1
print('\n', 'Число файлов где количество столбцов отличается от 10---', shape_counter)
print('\n', 'Число файлов с пропусками---', nan_counter)


# **Чтож, неплохо. все таблицы имеют одинаковое число столбцов, пропусков нет. Жить можно**

# ## Добавляем город и убираем лишние столбцы

# In[42]:


def region_to_city(st):
    return st.split(', ')[-1]


# In[43]:


trash_columns = ['ID', 'ID пользователя', 'Дата добавления донации', 'Место стадчи', 'Статус донации', 'Есть справка', 'Регион']

for i in range(len(df_list)):
    df_list[i]['Город'] = df_list[i]['Регион'].apply(region_to_city)
    df_list[i] = df_list[i].drop(trash_columns, axis=1)


# In[44]:


df_list[5].head()


# # Первые попытки что-то распознать

# In[50]:


image = cv2.imread('405/141899 .jpg')

preprocess = "thresh"
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

if preprocess == "thresh":
    gray = cv2.threshold(gray, 0, 255,
        cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
elif preprocess == "blur":
    gray = cv2.medianBlur(gray, 3)
    
filename = "{}.png".format(os.getpid())
cv2.imwrite(filename, gray)



string = pytesseract.image_to_string(gray, lang='rus')

print(string)


# In[ ]:





# In[ ]:




