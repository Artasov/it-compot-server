hh_disciplines = (
    'Информатика Junior (Scratch компьютерная грамотность)',  # 0
    'Scratch математика',  # 1
    'Город программистов Джуниор',  # 2
    'Город программистов',  # 3
    'Python GameDev (Разработка 2D-игр 1 ступень)',  # 4
    'Python GameDev (Разработка 2D и 3D-игр 2 ступень)',  # 5
    'Программирование Python (начальный уровень)',  # 6
    'Программирование Python не игры',  # 7
    'Web-программирование (1 ступень frontend)',  # 8
    'Web-программирование (2 ступень backend)',  # 9
    'Web-дизайн',  # 10
    'Графический дизайн Junior',  # 11
    'Графический дизайн',  # 12
    'Медиа вне программы',  # 13
    'Школа блогеров',  # 14
    '3D-моделирование (Blender)',  # 15
    '3D-моделирование 2 год',  # 16
    'Программирование вне программы',  # 17
    'Внутренние мероприятия',  # 18
    'Хакатон',  # 19
    'Марафон IT-профессий',  #
    '(ОУ) Scratch программирование',  #
    '(ОУ) Python программирование',  #
    '(ОУ) Школа блогеров / дизайн',  #
    '(ОУ) Веб-программирование',  #
    '(ОУ) 3D-моделирование',  #
    '(ОУ) Дизайн',  #
    '(ОУ) Школа блогера',  #
    '(ОУ) Информатика Junior',  #
    '(ОУ) Программирование (разработка сайтов или игр)',  #
    '(ОУ) Web-дизайн',  #
    '(ОУ) вне программы',  #
    'Клуб',  #
    'Программирование Roblox',  #
    'Архив не могу удалить (',  #
    '(архив, не могу удалить)',  #
    '(ОУ) Марафон профессий (удалить)',  #
    'Разработка чат-ботов',  #
    '(0)Разработка приложений на Пайтон',  #
    'Разработка мобильных приложений на Python для Android',  #
    'Мастер анимации - создаем мультфильмы',  #
    'Разработка мобильных приложений для Android в App Inventor',  #
    'Первые шаги в программировании и английском.  джуниор',  #
    'Первые шаги в 3д-моделировании.  Создай свой мир майнкрафта',  #
    'Видеомонтаж на компьютере - прокачка навыков',  #
    'Академия Заработка',  #
    'Урок диагностика',  #
    'Нейросети'  #
)

transfers = (
    (hh_disciplines[1], hh_disciplines[2]),
    (hh_disciplines[2], hh_disciplines[3]),
    (hh_disciplines[4], hh_disciplines[5]),
    (hh_disciplines[5], hh_disciplines[7]),
    (hh_disciplines[8], hh_disciplines[9]),
    (hh_disciplines[15], hh_disciplines[16]),
    (hh_disciplines[12], hh_disciplines[10]),
)


def get_next_discipline(age: int, discipline: str, level: str = None) -> str | None:
    if (level == hh_levels[2] or level == hh_levels[3] or level == hh_levels[4]) and \
            age >= 10 and discipline == hh_disciplines[1]:
        return hh_disciplines[3]
    for transfer in transfers:
        if transfer[0] == discipline:
            return transfer[1]


hh_levels = (
    'Easy',
    'Easy-medium',
    'Medium',
    'Medium-hard',
    'Hard',
)
base_ages = {
    f'{hh_disciplines[1]} {hh_levels[0]}': 8,
    f'{hh_disciplines[1]} {hh_levels[1]}': 9,
    f'{hh_disciplines[1]} {hh_levels[2]}': 10,
    f'{hh_disciplines[1]} {hh_levels[3]}': 11,
    f'{hh_disciplines[1]} {hh_levels[4]}': 12,

    f'{hh_disciplines[2]} {hh_levels[0]}': 8,
    f'{hh_disciplines[2]} {hh_levels[1]}': 9,
    f'{hh_disciplines[2]} {hh_levels[2]}': 10,
    f'{hh_disciplines[2]} {hh_levels[3]}': 11,
    f'{hh_disciplines[2]} {hh_levels[4]}': 12,

    f'{hh_disciplines[3]} {hh_levels[0]}': 9,
    f'{hh_disciplines[3]} {hh_levels[1]}': 9,
    f'{hh_disciplines[3]} {hh_levels[2]}': 10,
    f'{hh_disciplines[3]} {hh_levels[3]}': 11,
    f'{hh_disciplines[3]} {hh_levels[4]}': 12,

    f'{hh_disciplines[4]} {hh_levels[0]}': 10,
    f'{hh_disciplines[4]} {hh_levels[1]}': 11,
    f'{hh_disciplines[4]} {hh_levels[2]}': 12,
    f'{hh_disciplines[4]} {hh_levels[3]}': 13,
    f'{hh_disciplines[4]} {hh_levels[4]}': 14,

    f'{hh_disciplines[5]} {hh_levels[0]}': 11,
    f'{hh_disciplines[5]} {hh_levels[1]}': 12,
    f'{hh_disciplines[5]} {hh_levels[2]}': 13,
    f'{hh_disciplines[5]} {hh_levels[3]}': 14,
    f'{hh_disciplines[5]} {hh_levels[4]}': 15,

    f'{hh_disciplines[7]} {hh_levels[0]}': 12,
    f'{hh_disciplines[7]} {hh_levels[1]}': 13,
    f'{hh_disciplines[7]} {hh_levels[2]}': 14,
    f'{hh_disciplines[7]} {hh_levels[3]}': 15,
    f'{hh_disciplines[7]} {hh_levels[4]}': 16,

    f'{hh_disciplines[8]} {hh_levels[0]}': 12,
    f'{hh_disciplines[8]} {hh_levels[1]}': 13,
    f'{hh_disciplines[8]} {hh_levels[2]}': 14,
    f'{hh_disciplines[8]} {hh_levels[3]}': 15,
    f'{hh_disciplines[8]} {hh_levels[4]}': 16,

    f'{hh_disciplines[9]} {hh_levels[0]}': 13,
    f'{hh_disciplines[9]} {hh_levels[1]}': 14,
    f'{hh_disciplines[9]} {hh_levels[2]}': 15,
    f'{hh_disciplines[9]} {hh_levels[3]}': 16,
    f'{hh_disciplines[9]} {hh_levels[4]}': 17,

    f'{hh_disciplines[10]} {hh_levels[0]}': 9,
    f'{hh_disciplines[10]} {hh_levels[1]}': 10,
    f'{hh_disciplines[10]} {hh_levels[2]}': 11,
    f'{hh_disciplines[10]} {hh_levels[3]}': 12,
    f'{hh_disciplines[10]} {hh_levels[4]}': 13,

    f'{hh_disciplines[12]} {hh_levels[0]}': 9,
    f'{hh_disciplines[12]} {hh_levels[1]}': 10,
    f'{hh_disciplines[12]} {hh_levels[2]}': 11,
    f'{hh_disciplines[12]} {hh_levels[3]}': 12,
    f'{hh_disciplines[12]} {hh_levels[4]}': 13,

    f'{hh_disciplines[15]} {hh_levels[0]}': 9,
    f'{hh_disciplines[15]} {hh_levels[1]}': 10,
    f'{hh_disciplines[15]} {hh_levels[2]}': 11,
    f'{hh_disciplines[15]} {hh_levels[3]}': 12,
    f'{hh_disciplines[15]} {hh_levels[4]}': 13,

    f'{hh_disciplines[16]} {hh_levels[0]}': 10,
    f'{hh_disciplines[16]} {hh_levels[1]}': 11,
    f'{hh_disciplines[16]} {hh_levels[2]}': 12,
    f'{hh_disciplines[16]} {hh_levels[3]}': 13,
    f'{hh_disciplines[16]} {hh_levels[4]}': 14,
}
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
