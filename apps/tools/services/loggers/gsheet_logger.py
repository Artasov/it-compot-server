from datetime import datetime

from django.conf import settings

from service.tools.gsheet.classes.gsheetsclient import GSDocument, GSFormatOptions, ColumnWidth


class GSheetsSignUpFormingGroupLogger:
    def __init__(self, doc_id=settings.GSDOCID_LOG_JOIN_FORMING_GROUPS):
        self.client = GSDocument(doc_id)

        # Добавим заголовочную часть.
        all_sheets_names = self.client.get_sheets_titles()
        sheet_name = datetime.now().strftime('%Y-%m-%d')
        if sheet_name not in all_sheets_names:
            self.client.append_row(
                row=('Status', 'StudentAmoId', 'StudentHH', 'Groups', 'DateTime +0', 'Comment'),
                sheet_name=sheet_name
            )
            format_options_header = GSFormatOptions(
                background_color={'red': 0.3, 'green': 0.5, 'blue': 1},  # Красный фон
                text_color={'red': 1.0, 'green': 1.0, 'blue': 1.0},  # Белый текст
                font_size=16,  # Размер шрифта
                bold=True,
                vertical_alignment='MIDDLE',  # Вертикальное выравнивание по центру
                horizontal_alignment='CENTER',  # Горизонтальное выравнивание по центру
                wrap_strategy='WRAP'  # Включить перенос текста
            )
            self.client.format_range(0, 0, sheet_name, format_options_header, 1, )
            self.client.resize_columns_width(sheet_name=sheet_name, columns_widths=[
                ColumnWidth(column_index=1, width=170),
                ColumnWidth(column_index=2, width=250),
                ColumnWidth(column_index=3, width=280),
                ColumnWidth(column_index=4, width=155),
                ColumnWidth(column_index=5, width=150),
            ]

                                             )

    def log(self, status: str, student_amo_id: int, student_hh_id: int, groups_ids: list | tuple = None,
            comment: str = ''):
        if groups_ids is None:
            groups_ids = []
        base_url = 'https://it-school.t8s.ru'
        groups_links = '\n'.join([f'{base_url}/Learner/Group/{group_id.split(": ")[1]}/' for group_id in groups_ids])
        now = datetime.now().strftime('%Y-%m-%d')
        self.client.append_row(
            row=[
                status,
                str(student_amo_id),
                f'{base_url}/Profile/{student_hh_id}/',
                groups_links,
                datetime.now().strftime('%Y-%m-%d %H:%M'),
                comment
            ],
            sheet_name=now,
        )
        format_options = GSFormatOptions(
            background_color=None,
            text_color=None,
            font_size=None,
            bold=None,
            vertical_alignment="MIDDLE",
            horizontal_alignment="CENTER",
            wrap_strategy="WRAP"
        )
        self.client.format_range(1, 0, now, format_options)

    def error(self, student_amo_id: int, student_hh_id: int, groups_ids: list | tuple = None, comment: str = ''):
        self.log('ERROR', student_amo_id, student_hh_id, groups_ids, comment)

    def success(self, student_amo_id: int, student_hh_id: int, groups_ids: list | tuple = None, comment: str = ''):
        self.log('SUCCESS', student_amo_id, student_hh_id, groups_ids, comment)
