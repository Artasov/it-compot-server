from datetime import datetime

from django.conf import settings

from service.tools.gsheet.classes.gsheetsclient import GSheetsClient


class GSheetsSignUpFormingGroupLogger:
    def __init__(self, doc_id=settings.GSDOCID_LOG_JOIN_FORMING_GROUPS):
        self.client = GSheetsClient(doc_id)

    def log(self, status: str, student_amo_id: int, student_hh_id: int, groups_ids: list | tuple = None,
            comment: str = ''):
        if groups_ids is None:
            groups_ids = []
        base_url = 'https://it-school.t8s.ru'
        groups_links = '\n'.join([f'{base_url}/Learner/Group/{group_id.split(": ")[1]}/' for group_id in groups_ids])
        row = [
            status,
            str(student_amo_id),
            f'{base_url}/Profile/{student_hh_id}/',
            groups_links,
            datetime.now().strftime('%Y-%m-%d %H:%M'),
            comment
        ]
        self.client.append_row(
            row=row,
            sheet_name=datetime.now().strftime("%Y-%m-%d"),
            header_if_new_list=('Status', 'StudentAMO', 'StudentHH', 'Groups', 'DateTime', 'Comment')
        )

    def error(self, student_amo_id: int, student_hh_id: int, groups_ids: list | tuple = None, comment: str = ''):
        self.log('ERROR', student_amo_id, student_hh_id, groups_ids, comment)

    def success(self, student_amo_id: int, student_hh_id: int, groups_ids: list | tuple = None, comment: str = ''):
        self.log('SUCCESS', student_amo_id, student_hh_id, groups_ids, comment)
