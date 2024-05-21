import gspread
from django.conf import settings
from google.oauth2.service_account import Credentials


class GSDocumentGSpread:
    def __init__(self, doc_id, creds_json_path=settings.GOOGLE_API_JSON_CREDS_PATH):
        self.doc_id = doc_id
        self.creds_json_path = creds_json_path
        self.gc = self._authenticate()  # Создаем объект клиента при инициализации

    def _authenticate(self):
        """
        Авторизует клиента с использованием учетных данных из файла JSON.
        """
        credentials = Credentials.from_service_account_file(
            self.creds_json_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        gc = gspread.authorize(credentials)
        gc.set_timeout(600)
        return gc

    def get_sheet_as_list(self, sheet_name: str) -> list[list[str]]:
        """
        Получает данные из указанного листа Google Sheets и возвращает их как массив строк.

        @param sheet_name: Название листа, из которого нужно извлечь данные.
        @return: Массив строк, представляющий данные листа.
        """
        # Открываем документ и лист
        sheet = self.gc.open_by_key(self.doc_id).worksheet(sheet_name)

        # Получаем все данные листа
        values = sheet.get_all_values()

        return values
