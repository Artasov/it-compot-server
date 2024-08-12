from typing import TypedDict, Literal, Optional

import httplib2
from django.conf import settings
from google.oauth2 import service_account
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class ListAlreadyExists(Exception):
    pass


VerticalAlignmentOptions = Literal["TOP", "MIDDLE", "BOTTOM"]
HorizontalAlignmentOptions = Literal["LEFT", "CENTER", "RIGHT"]
WrapStrategyOptions = Literal["OVERFLOW_CELL", "WRAP", "CLIP"]


class GSColor(TypedDict):
    red: float
    green: float
    blue: float


class ColumnWidth(TypedDict):
    column_index: int
    width: int


class GSFormatOptions(TypedDict, total=False):
    text_color: GSColor | None
    background_color: GSColor | None
    font_size: int | None
    bold: bool | None
    vertical_alignment: VerticalAlignmentOptions | None
    horizontal_alignment: HorizontalAlignmentOptions | None
    wrap_strategy: WrapStrategyOptions | None


class GSSheet:
    def __init__(self, name: str, id: str):
        self.name = name
        self.id = id


class GSFormatOptionVariant:
    BASE_HEADER = GSFormatOptions(
        background_color={'red': 0.3, 'green': 0.5, 'blue': 1},
        text_color={'red': 1.0, 'green': 1.0, 'blue': 1.0},
        font_size=16,
        bold=True,
        vertical_alignment='MIDDLE',
        horizontal_alignment='CENTER',
        wrap_strategy='WRAP'
    )
    BASE_ROW = GSFormatOptions(
        background_color=None,
        text_color=None,
        font_size=None,
        bold=None,
        vertical_alignment="MIDDLE",
        horizontal_alignment="CENTER",
        wrap_strategy="WRAP"
    )


class GSDocument:
    """В одном документе может быть несколько таблиц"""

    def __init__(self, doc_id, creds_json_path=settings.GOOGLE_API_JSON_CREDS_PATH):
        self.creds_json_path = creds_json_path
        self.doc_id = doc_id
        self.sheets: dict[str, GSSheet] = {}
        self.service = self._authenticate()
        self.sheets_init()

    def _authenticate(self):
        credentials = service_account.Credentials.from_service_account_file(
            self.creds_json_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )

        http = httplib2.Http(timeout=600)
        authed_http = AuthorizedHttp(credentials, http=http)

        service = build('sheets', 'v4', http=authed_http)
        return service

    @staticmethod
    def col_num_to_letter(n: int) -> str:
        """
        Преобразует номер столбца в буквенное обозначение (например, 1 -> 'A', 27 -> 'AA').

        @param n: Номер столбца (начиная с 1).
        @return: Буквенное обозначение столбца.
        """
        string = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            string = chr(65 + remainder) + string
        return string

    def get_cell(self, row: int, col: int, sheet_name: str) -> str | None:
        """
        Получает значение ячейки из указанного листа Google Sheets.

        @param row: Номер строки (начиная с 1).
        @param col: Номер столбца (начиная с 1).
        @param sheet_name: Название листа, из которого нужно извлечь данные.
        @return: Значение ячейки.
        """
        col_letter = self.col_num_to_letter(col)
        cell_range = f"{col_letter}{row}:{col_letter}{row}"
        data = self.get_sheet_as_list(sheet_name, cell_range)

        if data and len(data) > 0 and len(data[0]) > 0:
            return data[0][0]

    def get_sheet_as_list(self, sheet_name: str, range: str = None) -> list[list[str]]:
        """
        Получает данные из указанного листа Google Sheets и возвращает их как массив строк.

        @param sheet_name: Название листа, из которого нужно извлечь данные.
        @param range: Диапазон ячеек для извлечения (например, 'A1:D500'). Если None, извлекаются все данные листа.
        @return: Массив строк, представляющий данные листа.
        """
        # Если диапазон не задан, берем все данные листа
        if range is None:
            range = f"{sheet_name}"
        else:
            range = f"{sheet_name}!{range}"

        # Получаем данные
        result = self.service.spreadsheets().values().get(spreadsheetId=self.doc_id, range=range).execute()
        values = result.get('values', [])

        return values

    def sheets_init(self):
        sheets_meta = self.get_sheets_meta()
        for sheet in sheets_meta:
            self.sheets[sheet['properties']['title']] = GSSheet(
                name=sheet['properties']['title'],
                id=sheet['properties']['sheetId'],
            )

    def resize_columns_width(self, sheet_name: str, columns_widths: list[ColumnWidth, ...]):
        """
        Изменяет ширину указанных столбцов в Google Sheets.

        @param sheet_name: Название листа, в котором находятся столбцы.
        @param columns_widths: Список словарей, содержащих индекс столбца и новую ширину.
        """
        sheet_id = self.sheets[sheet_name].id
        if sheet_id is None:
            print(f"Лист с именем '{sheet_name}' не найден.")
            return

        requests = []
        for column_width in columns_widths:
            column_index = column_width["column_index"]
            width = column_width["width"]

            requests.append({
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": column_index,
                        "endIndex": column_index + 1,
                    },
                    "properties": {
                        "pixelSize": width
                    },
                    "fields": "pixelSize"
                }
            })

        body = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(spreadsheetId=self.doc_id, body=body).execute()
        return response

    def auto_resize_columns(self, sheet_name: str, start_col: int, end_col: Optional[int] = None):
        """
        Автоматически изменяет ширину столбцов в указанном диапазоне, чтобы содержимое помещалось.

        @param sheet_name: Название листа.
        @param start_col: Начальный индекс столбца для изменения размера (начинается с 0).
        @param end_col: Конечный индекс столбца для изменения размера (не включается). Если None, изменяется только start_row.
        """
        sheet_id = self.sheets[sheet_name].id
        if sheet_id is None:
            print(f"Лист с именем '{sheet_name}' не найден.")
            return

        if end_col is None:
            end_col = start_col + 1  # Автоизменение размера будет применено только к start_row

        requests = [{
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": start_col,
                    "endIndex": end_col
                }
            }
        }]

        body = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(spreadsheetId=self.doc_id, body=body).execute()
        return response

    def auto_resize_rows(self, sheet_name: str, start_row: int, end_row: Optional[int] = None):
        """
        Автоматически изменяет ширину строк в указанном диапазоне, чтобы содержимое помещалось.

        @param sheet_name: Название листа.
        @param start_row: Начальный индекс столбца для изменения размера (начинается с 0).
        @param end_row: Конечный индекс столбца для изменения размера (не включается). Если None, изменяется только start_col.
        """
        sheet_id = self.sheets[sheet_name].id
        if sheet_id is None:
            print(f"Лист с именем '{sheet_name}' не найден.")
            return

        if end_row is None:
            end_row = start_row + 1  # Автоизменение размера будет применено только к start_row

        requests = [{
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": start_row,
                    "endIndex": end_row
                }
            }
        }]

        body = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(spreadsheetId=self.doc_id, body=body).execute()
        return response

    def auto_resize_last_row(self, sheet_name: str):
        """
        Автоматически изменяет ширину последней строки на указанном листе, чтобы содержимое помещалось.

        @param sheet_name: Название листа.
        """
        sheet_id = self.sheets[sheet_name].id
        if sheet_id is None:
            print(f"Лист с именем '{sheet_name}' не найден.")
            return

        # Получить текущий индекс последней строки
        response = self.service.spreadsheets().values().get(spreadsheetId=self.doc_id, range=sheet_name).execute()
        num_rows = len(response.get('values', []))

        # Если нет данных, нет смысла изменять размер строки
        if num_rows == 0:
            print(f"Лист '{sheet_name}' пустой.")
            return

        start_row = num_rows - 1
        end_row = num_rows  # end_row не включается в диапазон, поэтому он равен индексу последней строки

        requests = [{
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": start_row,
                    "endIndex": end_row
                }
            }
        }]

        body = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(spreadsheetId=self.doc_id, body=body).execute()
        return response

    def append_row(self, row: list | tuple, sheet_name: str):
        # Проверяем, существует ли лист
        if sheet_name not in self.sheets:
            print(f"Лист '{sheet_name}' не найден. Создаем новый лист.")
            self.create_sheet(sheet_name)

        # Добавляем строку в конец листа
        range_name = f"{sheet_name}!A1"  # A1 указывает Google Sheets начать поиск конца таблицы с первой колонки
        body = {'values': [row]}
        request = self.service.spreadsheets().values().append(
            spreadsheetId=self.doc_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        )
        response = request.execute()
        return response

    def create_sheet(self, sheet_name):
        # Создаем запрос на добавление нового листа
        try:
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }
            request = self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.doc_id, body=body)
            response = request.execute()
        except HttpError as e:
            if 'already exists' in str(e):
                raise ListAlreadyExists()
            else:
                raise e
        self.sheets[sheet_name] = GSSheet(
            sheet_name, response.get('replies')[0].get('addSheet').get('properties').get('sheetId')
        )
        return self.sheets[sheet_name]

    def get_sheets_meta(self):
        # Получаем метаданные о листах/таблицах
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.doc_id).execute()
        sheets = sheet_metadata.get('sheets', '')
        return sheets

    def get_sheets_titles(self):
        sheets = self.get_sheets_meta()
        titles = [sheet.get('properties', {}).get('title', '') for sheet in sheets]
        return titles

    def aupdate_sheet(self, sheet_name: str, values: list[list | tuple] | tuple[list | tuple]):
        body = {'values': values}
        request = self.service.spreadsheets().values().update(
            spreadsheetId=self.doc_id,
            range=sheet_name,
            valueInputOption='USER_ENTERED',
            body=body
        )
        response = request.execute()
        return response

    def update_sheet_with_format_header(
            self,
            sheet_name: str,
            header: list | tuple,
            values: list[list | tuple],
            format_header: GSFormatOptions):
        values.insert(0, header)
        self.clear_sheet(sheet_name=sheet_name)
        self.update_sheet(sheet_name=sheet_name, values=values)
        self.format_range(
            start_row=0, start_col=0,
            sheet_name=sheet_name,
            format_options=format_header,
            end_row=1
        )

    def update_sheet_with_df(self, sheet_name, df):
        # Передаем DataFrame в Google Sheets без изменений
        values = df.fillna('').values.tolist()
        body = {'values': values}

        request = self.service.spreadsheets().values().update(
            spreadsheetId=self.doc_id,
            range=sheet_name,
            valueInputOption='USER_ENTERED',
            body=body
        )
        response = request.execute()
        return response

    def clear_sheet(self, sheet_name):
        # Очищаем данные в таблице
        request = self.service.spreadsheets().values().clear(
            spreadsheetId=self.doc_id,
            range=sheet_name,
            body={}
        )
        response = request.execute()
        return response

    def format_range(self,
                     start_row: int, start_col: int,
                     sheet_name: str, format_options: GSFormatOptions,
                     end_row: Optional[int] = None, end_col: Optional[int] = None) -> dict:
        """
        Форматирует диапазон ячеек в Google Sheets с заданными параметрами форматирования.

        @param start_row: Начальный индекс строки для форматирования (начинается с 0).
        @param end_row: Конечный индекс строки для форматирования (не включается). Если None, форматирование применяется до конца листа.
        @param start_col: Начальный индекс столбца для форматирования (начинается с 0).
        @param end_col: Конечный индекс столбца для форматирования (не включается). Если None, форматирование применяется до конца листа.
        @param sheet_name: Название листа, в котором будет произведено форматирование.
        @param format_options: Параметры форматирования ячеек.
        @return: Ответ API на запрос форматирования.
        """
        sheet_id = self.sheets[sheet_name].id
        if sheet_id is None:
            print(f"Лист с именем '{sheet_name}' не найден.")
            return {}

        requests = [{
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': start_row,
                    'endRowIndex': end_row,
                    'startColumnIndex': start_col,
                    'endColumnIndex': end_col,
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': format_options['background_color'],
                        'horizontalAlignment': format_options['horizontal_alignment'],
                        'verticalAlignment': format_options['vertical_alignment'],
                        'wrapStrategy': format_options['wrap_strategy'],
                        'textFormat': {
                            'bold': format_options['bold'],
                            'fontSize': format_options['font_size'],
                            'foregroundColor': format_options['text_color'],
                        }
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)'
            }
        }]
        body = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(spreadsheetId=self.doc_id, body=body).execute()
        return response

    def format_cell(self, row: int, col: int, sheet_name: str, format_options) -> dict:
        return self.format_range(
            start_row=row, end_row=row + 1,
            start_col=col, end_col=col + 1,
            sheet_name=sheet_name, format_options=format_options)
