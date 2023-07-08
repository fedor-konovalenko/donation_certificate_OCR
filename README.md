# donation_certificate_OCR
## Цель проекта
Разработка инструмента для идентификации на фотографии таблиц с машинописным текстом и распознавания текста в таблице. Область применения - автоматическое заполнение базы данных доноров на [сайте](https://donorsearch.org/)
## Исходные данные
Набор изображений справок формы №405 о сдаче крови и ее компонентов и набор соответствующих им файлов в формате .csv, которые будут использоваться для валидации
## Рассмотренные инструменты

1.Tesseract в чистом виде. Хорошо распознает отдельные строки или абзацы, но с таблицам не справляется.

2. [CascadeTabNet](https://github.com/DevashishPrasad/CascadeTabNet). Оказался не применим. В статье у авторов все рабоает прекрасно, но требует уже неактуальной библиотеки pytorch 1.4.0 и версии python не позднее 3.7.

3. Опыт, описанный на [хабре](https://habr.com/ru/articles/546824/) по распознаванию таблиц в накладных торг-12. При ближайшем рассмотрении - оказался слишком узкоспециальным инструментом: задача стояла распознавать  сканы хорошего качества и искать на них маленькие ячейки определенного заранее известного размера.

5. [img2table](https://github.com/xavctn/img2table/tree/main) Неидеальные таблицы распознает плохо.
   
6. Раз img2table плохо справляется с распознаванием текста, зато хорошо ищет ячейки таблиц, то пусть ячейками и занимается. Идея в том, что img2table хорошо находит ячейки, а tesseract хорошо распознает отдельные строки. Пусть работают вместе.
**Данный вариант выбран в качестве рабочего**
_____________
## Алгоритм распознавания
1. Подготовка изображения: перевод к оттенкам серого, максимизация контрастности, минимизация шумов. Предобработка выполняется средствами opencv. [Пример](https://digitology.tech/posts/primenenie-ocr-tesseract-sovmestno-s-python/)

2. Определение ориентации изображения и поворот на данном этапе не выполняется. Для изображений с искажениями перспективами инструменты opencv дают некорректный результат

3. Поиск на изображении координат ячеек таблиц при помощи img2table

4. В цикле из изображения вырезается кусок, содержащий данную ячейку, в ней при помощи tesseract распознается текст

5. Распознанный список строк очищается при помощи регулярных выражений от мусорных символов, остаются даты, пометка о типе донации и объем сданной крови

6. Из очищенного списка собирается таблица по следующей логике. Главная информация - дата, поскольку это уникальное значение (мало кто сдает кровь чаще 1 раза в день). Соответственно, если дата не распознана ни разу, то изображение считается некорректным. Для распознанных дат остальные ячейки присоединяются по принципу структуры справки формы 405: слева направо в строке идут "дата->объем->тип донации"
_____________
## Методика расчета accuracy
_____________
## Полученные результаты
_____________
## Выводы

