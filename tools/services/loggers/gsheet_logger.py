from datetime import datetime

from django.conf import settings

from service.tools.gsheet.classes.gsheetsclient import GSheetsClient


class GSheetsSignUpFormingGroupLogger:
    def __init__(self, doc_id=settings.GSDOCID_LOG_JOIN_FORMING_GROUPS):
        self.client = GSheetsClient(doc_id)

    def error(self, row: list | tuple):
        self.client.append_row(row=['ERROR'] + row, sheet_name=datetime.now().strftime("%Y-%m-%d"))

    def success(self, row: list | tuple):
        self.client.append_row(row=['SUCCESS'] + row, sheet_name=datetime.now().strftime("%Y-%m-%d"))
