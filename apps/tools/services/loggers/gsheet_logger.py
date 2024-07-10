from datetime import datetime

from modules.gsheet.classes.gsheetsclient import GSDocument, ColumnWidth, GSFormatOptionVariant


class GSLoggerDayBase:
    def __init__(self,
                 header: list | tuple,
                 doc_id: str,
                 column_widths: list[ColumnWidth, ...] | tuple[ColumnWidth, ...] = None
                 ):
        self.column_widths = column_widths
        self.doc = GSDocument(doc_id)
        self.sheet_name = datetime.now().strftime('%Y-%m-%d')
        if self.sheet_name not in self.doc.sheets:
            self.doc.create_sheet(self.sheet_name)
            self.doc.append_row(row=header, sheet_name=self.sheet_name)
            self.doc.resize_columns_width(sheet_name=self.sheet_name, columns_widths=column_widths, )
            self.doc.format_range(0, 0, self.sheet_name, GSFormatOptionVariant.BASE_HEADER, 1, )


class GSheetLoggerJoinFormingGroup(GSLoggerDayBase):
    def log(self, status: str, student_amo_id: int, student_hh_id: int, groups_ids: list | tuple = None,
            comment: str = ''):
        if groups_ids is None:
            groups_ids = []
        base_url = 'https://it-school.t8s.ru'
        groups_links = '\n'.join(
            [f'{group_id.split(": ")[0]} {base_url}/Learner/Group/{group_id.split(": ")[1]}/' for group_id in
             groups_ids])
        now = datetime.now().strftime('%Y-%m-%d')
        self.doc.append_row(
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
        self.doc.format_range(1, 0, now, GSFormatOptionVariant.BASE_ROW)

    def error(self, student_amo_id: int, student_hh_id: int, groups_ids: list | tuple = None, comment: str = ''):
        self.log('ERROR', student_amo_id, student_hh_id, groups_ids, comment)

    def success(self, student_amo_id: int, student_hh_id: int, groups_ids: list | tuple = None, comment: str = ''):
        self.log('SUCCESS', student_amo_id, student_hh_id, groups_ids, comment)
