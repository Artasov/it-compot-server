hh_disciplines = (
    'Информатика Junior (Scratch компьютерная грамотность)',
    'Scratch математика',
    'Город программистов Джуниор',
    'Город программистов',
    'Python GameDev (Разработка 2D-игр 1 ступень)',
    'Python GameDev (Разработка 2D и 3D-игр 2 ступень)',
    'Программирование Python (начальный уровень)',
    'Программирование Python не игры',
    'Web-программирование (1 ступень frontend)',
    'Web-программирование (2 ступень backend)',
    'Web-дизайн',
    'Графический дизайн Junior',
    'Графический дизайн',
    'Медиа вне программы',
    'Школа блогеров',
    '3D-моделирование (Blender)',
    '3D-моделирование 2 год',
    'Программирование вне программы',
    'Внутренние мероприятия',
    'Хакатон',
    'Марафон IT-профессий',
    '(ОУ) Scratch программирование',
    '(ОУ) Python программирование',
    '(ОУ) Школа блогеров / дизайн',
    '(ОУ) Веб-программирование',
    '(ОУ) 3D-моделирование',
    '(ОУ) Дизайн',
    '(ОУ) Школа блогера',
    '(ОУ) Информатика Junior',
    '(ОУ) Программирование (разработка сайтов или игр)',
    '(ОУ) Web-дизайн',
    '(ОУ) вне программы',
    'Клуб',
    'Программирование Roblox',
    'Архив не могу удалить (',
    '(архив, не могу удалить)',
    '(ОУ) Марафон профессий (удалить)',
    'Разработка чат-ботов',
    '(0)Разработка приложений на Пайтон',
    'Разработка мобильных приложений на Python для Android',
    'Мастер анимации - создаем мультфильмы',
    'Разработка мобильных приложений для Android в App Inventor',
    'Первые шаги в программировании и английском.  джуниор',
    'Первые шаги в 3д-моделировании.  Создай свой мир майнкрафта',
    'Видеомонтаж на компьютере - прокачка навыков',
    'Академия Заработка',
    'Урок диагностика',
    'Нейросети'
)
hh_levels = (
    'Easy',
    'Easy-medium',
    'Medium',
    'Medium-hard',
    'Hard',
)
amo_disciplines = (
    'Python (игры) 1 ступень',
    'Python (игры) 2 ступень',
    'Python (не игры, углубленный)',
    'Scratch + математика',
    'Город программистов',
    'Школа блогеров',
    'Дизайн',
    '3Д-моделирование',
    'Веб-программирование 1 ступень',
    'Веб-программирование 2 ступень',
    'Веб-дизайн',
    'Информатика Junior (6-7 лет)',
    'Комп.грамотность в записи',
)
amo_levels = (
    'easy (слабый уровень комп грамотности)',
    'easy-medium',
    'medium (средний)',
    'medium-hard',
    'hard (прошаренный в компах, легко ему)',
)
amo_hh_disciplines_map = (
    (amo_disciplines[0], hh_disciplines[4]),
    (amo_disciplines[1], hh_disciplines[5]),
    (amo_disciplines[2], hh_disciplines[7]),
    (amo_disciplines[3], hh_disciplines[1]),
    (amo_disciplines[4], hh_disciplines[2]),
    (amo_disciplines[5], hh_disciplines[14]),
    (amo_disciplines[6], hh_disciplines[12]),
    (amo_disciplines[7], hh_disciplines[15]),
    (amo_disciplines[8], hh_disciplines[8]),
    (amo_disciplines[9], hh_disciplines[9]),
    (amo_disciplines[10], hh_disciplines[10]),
    (amo_disciplines[11], hh_disciplines[0]),
)
amo_hh_levels_map = (
    (amo_levels[0], hh_levels[0]),
    (amo_levels[1], hh_levels[1]),
    (amo_levels[2], hh_levels[2]),
    (amo_levels[3], hh_levels[3]),
    (amo_levels[4], hh_levels[4]),
)
amo_hh_currencies = {
    'Евро': '€',
    'Доллар': '$',
    'Рубль': 'руб.',
    'Английский фунт': '£',
    'Дубай дирхам': 'дрх.',
    'Тенге': 'тг.'
}

amo_hh_pay_methods = {
    'Stripe': 1005,
    'по счету юкасса': 1,
    'по QR-коду (Тинькоф)': 5,
    'Рассрочка (РР)': 6,
    'Долями': 4,
    'PayPal': 1006,
    'Code Like (перевод)': 1007,
    'на р.счет по реквиз (от юр лица)': 2,
    'на р.счет по реквиз. (от физ. лица)': 2,
    'Альфабанк по ссылке': 1009,
    'Альфа по QR коду': 1010,
}
# Пример использования
# forming_unit = {'Discipline': 'Python GameDev (Разработка 2D-игр 1 ступень)'}
# amo_discipline = next((amo for amo, hh in amo_hh_disciplines_map if hh == forming_unit['Discipline']), "Дисциплина не найдена")
# print(amo_discipline)  # Вывод: Python (игры) 1 ступень