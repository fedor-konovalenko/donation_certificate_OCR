# donation_certificate_OCR
## Структура репозитория
- app/ - приложение с веб-интерфейсом. После запускка app.py работает по адресу localhost:8000. выдает результат в JSON-формате
- celery_app - приложение с веб-интерфейсом и потоковой обработкой запросов. Запускается через run.sh из папки /Docker
- command2_6.ipynb - ноутбук с экспериментами
- final_1807.pdf - презентация с заключительной встречи по проекту
- thanks_letter - благодарственное письмо от заказчика
- **classifier405.ipynb - ноутбук с экспериментами по построению нейросети для определению корректности типа справки при загрузке** 

## Цель проекта
Разработка инструмента для идентификации на фотографии таблиц с машинописным текстом и распознавания текста в таблице. Область применения - автоматическое заполнение базы данных доноров на [сайте](https://donorsearch.org/)
## Исходные данные
Набор изображений справок формы №405 о сдаче крови и ее компонентов и набор соответствующих им файлов в формате .csv, которые будут использоваться для валидации модели распознавания
## Рассмотренные инструменты


1.Tesseract в чистом виде. Хорошо распознает отдельные строки или абзацы, но с таблицам не справляется.

2. [CascadeTabNet](https://github.com/DevashishPrasad/CascadeTabNet). Оказался не применим. В статье у авторов все работает прекрасно, но требует уже неактуальной библиотеки pytorch 1.4.0 и версии python не позднее 3.7.

3. Опыт, описанный на [хабре](https://habr.com/ru/articles/546824/) по распознаванию таблиц в накладных торг-12. При ближайшем рассмотрении - оказался слишком узкоспециальным инструментом: у автора статьи задача стояла распознавать  сканы хорошего качества и искать на них маленькие ячейки определенного заранее известного размера.

4. Нейросети и готовые тяжелые модели в данной задаче не рассматривались

5. [img2table](https://github.com/xavctn/img2table/tree/main) Готовая библиотека для распознавания таблиц. При хорошем качестве изображения справляется с поиском таблицы, но текст распознает плохо.
   
**В качестве рабочего варианта выбрана комбинация img2table и tesseract**
Раз img2table плохо справляется с распознаванием текста, зато хорошо ищет ячейки таблиц, то пусть ячейками и занимается. А tesseract хорошо распознает строки, тогда пуская ограничивается одной ячейкой

_____________
## Алгоритм распознавания
1. Подготовка изображения: перевод к оттенкам серого, максимизация контрастности, минимизация шумов. Предобработка выполняется средствами opencv. [Пример](https://digitology.tech/posts/primenenie-ocr-tesseract-sovmestno-s-python/)

2. Определение ориентации изображения и поворот в этой задаче не выполнялись. Для изображений с искажениями перспективы инструменты opencv дают некорректный результат

3. Поиск на изображении координат ячеек таблиц при помощи img2table

4. В цикле из изображения вырезается кусок, содержащий данную ячейку, в ней при помощи tesseract распознаются сначала цифры, а потом буквы, посе чего списки объединяются

5. Распознанный список строк очищается при помощи регулярных выражений от мусорных символов, остаются даты, пометка о типе донации и классе крови и объем сданной крови

6. Из очищенного списка собирается таблица по следующей логике. Главная информация - дата, поскольку это уникальное значение (мало кто сдает кровь чаще 1 раза в день). Соответственно, если дата не распознана ни разу, то изображение считается некорректным. Для распознанных дат остальные ячейки присоединяются по принципу структуры справки формы 405: слева направо в строке идут "дата->объем->тип донации". Помимо корректности даты также проверяется корректность распознанного объема крови (от 50 до 700 мл).

7. Таблица сохраняется в csv и JSON формат

_____________
## Проблемы и слабые места

1. Весь алгоритм, реализованный в command2_6.ipynb, построен на том, как устроена именно справка формы 405. На справке другой формы, так же содержащей табличные данные, он скорее всего сломается.
2. В имевшихся данных тип донации - только безвозмездный. То есть, платные донации созданная модель пока в принципе не идентифицирует.
3. Идентифицировать центр крови в соответсвии с требованиями ТЗ на основании имеющихся изображений невозможно. Только город.
4. Форма таблицы приводит к тому, что в несколько символов 'кр/д (бв)' содержат в себе много информации: и о типе донации, и о классе крови. и от точности их распознавания зависит очень многое.
5. Выбранная библиотека для поиска таблиц (img2table) дает разные результаты при работе в разных операционных системах. Последняя версия корректно работает в Docker- контейнере, корректность работы приложения вне контейнера в ОС windows не проверялась. 
_____________
## Методика расчета accuracy

Расчет "по определению": количество правильных ответов / количество ячеек в валидационной таблице
_____________
## Полученные результаты
Распознано 10 изображений из 16 предложенных. 
Среднее значение accuracy - 0,44
Лучшее - 0,95
_____________
## Выводы
- разработанный инструмент позволяет распознавать табличный текст на изображениях хорошего качества с неискаженной перспективой
- пути повышения точности распознавания:
    - оптимизация регулярных выражений при обработке текста
    - применение разных масок препроцессинга для изображений с разным разрешением
    - распознавание за несколько проходов с разными настройками и сборка таблицы по уникальным датам
    - отказ от img2table в пользу opencv или другого способа поиска контуров ячеек: img2table ищет "просто ячейки", а точность можно повысить если искать опреденной формы ячейки с заранее известным соотношением сторон
____________
## Update 04.09.2023
Дополнительно возникла задача определения, правильного ли типа справка загружена пользователем: справки бывают нескольких форм: 402, 405, 448. На данном этапе требуется отличать справки 405 формы от всех остальных. Для этого была построена и обучена (на ~200 справках, предварительно размеченных по классам) сверточная нейросеть [LeNet](https://www.kaggle.com/code/blurredmachine/lenet-architecture-a-complete-guide) - подобной архитектуры. Отличие от классической LeNet состояло в том, что в качестве функции активации использовалась ReLU вместо гиперболического тангенса, поскольку ReLU показала более хорошие результаты на валидации.
Перед обучением изображения предобрабатывались средствами opencv: поскольку на справке 405 в отличие от остальных справок есть характерная сетка таблицы, то гипотеза состояла в том, что выделение контуров на изображении и удаление всего, кроме контуров, позволит обучить нейросеть даже на небольшой выборке. 

**Результаты на тестовой выборке**


<img src="https://github.com/fedor-konovalenko/donation_certificate_OCR/blob/master/img/pic1.png" width="500" height="500">

*Матрица ошибок*

