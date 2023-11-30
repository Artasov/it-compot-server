from google.oauth2 import service_account
from googleapiclient.discovery import build


class GSheetsClient:
    def __init__(self, creds_json_path, spreadsheet_id):
        self.creds_json_path = creds_json_path
        self.spreadsheet_id = spreadsheet_id
        self.service = self.authenticate()

    def authenticate(self):
        # Загружаем учетные данные и создаем сервис
        credentials = service_account.Credentials.from_service_account_file(
            self.creds_json_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        service = build('sheets', 'v4', credentials=credentials)
        return service

    def get_sheets_titles(self):
        # Получаем метаданные о листах
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', '')
        titles = [sheet.get('properties', {}).get('title', '') for sheet in sheets]
        return titles

    def update_sheet(self, range_name, values):
        # Вставляем данные в таблицу
        body = {'values': values}
        request = self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        )
        response = request.execute()
        return response

    def update_sheet_with_df(self, range_name, df):
        # Передаем DataFrame в Google Sheets без изменений
        values = df.fillna('').values.tolist()
        body = {'values': values}

        request = self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        )
        response = request.execute()
        return response

    def clear_sheet(self, range_name):
        # Очищаем данные в таблице
        request = self.service.spreadsheets().values().clear(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
            body={}
        )
        response = request.execute()
        return response
