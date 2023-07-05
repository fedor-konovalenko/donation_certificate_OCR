# donation_certificate_OCR
## Цель проекта
Разработка инструмента для идентификации на фотографии таблиц с машинописным текстом и распознавания текста в таблице. Область применения - автоматическое заполнение базы данных доноров на сайте [социальной сети доноров](https://donorsearch.org/)
## Исходные данные
Набор изображений справок формы №405 о сдаче крови и ее компонентов и набор соответствующих им файлов в формате .csv, которые будут использоваться для валидации
## План исследования
Задача декомпозируется на несколько подзадач:

1. Подготовка изображения: перевод к оттенкам серого, максимизация контрастности, минимизация шумов. Предполагается использовать средства opencv. [Пример](https://digitology.tech/posts/primenenie-ocr-tesseract-sovmestno-s-python/)

2. Определение ориентации изображения и при необходимости, поворот [Пример](https://nanonets.com/blog/ocr-with-tesseract/#detectorientationandscript)

3. Поиск на изображении таблиц. Пока что видится, что это наиболее сложный этап. Предполагается использовать [инструменты opencv](https://habr.com/ru/articles/546824/), [CascadeTabNet](https://github.com/DevashishPrasad/CascadeTabNet) и еще смотрел в сторону [microsoft table transformer](https://github.com/microsoft/table-transformer), но кажется, он окажется слишком тяжелым

4. В найденных ячейках таблиц распознавание текста с помощью tesseract

5. Корректировка распознанного текста там, где это возможно. Пример: "8в" = "бв" -> безвозмездно. "23.87.2018" = "23.07.2018" и так далее

6. Расчет accuracy, возврат к шагу 1:)
## Исследованные инструменты

1. CascadeTabNet. Похоже, не применим. В статье у авторов все рабоает прекрасно, но требует уже неактуальной библиотеки pytorch 1.4.0 и версии python не позднее 3.7.
2. Метод чувака с хабра для распознавания таблиц накладных торг-12. При ближайшем рассмотрении - слишком узкоспециальная история. Пока решил отложить.
3. Инструменты open cv. ... in progress... все сильно зависит от качества и разрешения изображения
4. [img2table](https://github.com/xavctn/img2table/tree/main). Плохо работает "из коробки", зато хорошо ищет ячейки таблиц. Идея в том, что img2table хорошо находит ячейки. а tesseract сносно распознает отдельные строки. Поэтому в цикле по ячейкам буду распознавать отдельные записи. Отдельно числовые значения, отдельно - слова. После этого можно собирать series из распознанных данных. Будет использоваться тот факт, что структура таблиц при движении слева направо сверху вниз одинаковая: дата-тип донации-объем. Даты распознаются хорошо, а следующий после даты объем можно считать относящимся к этой дате. 

_____________
## Полученные результаты
_____________
## Выводы

