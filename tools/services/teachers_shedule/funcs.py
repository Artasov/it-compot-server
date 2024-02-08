from pandas import DataFrame

from service.tools.gsheet.classes.gsheetsclient import GSDocument
from tools.forms.other import LoadHHTeachersScheduleXLSXForm
from tools.services.teachers_shedule.funcs_parse import parse_teachers_schedule_from_dj_mem, create_schedule


async def handle_teachers_schedule_upload(request) -> dict:
    """
    Обрабатывает загрузку расписания учителей через POST-запрос.

    @param request: Объект запроса Django.
    @return: Контекст для рендеринга шаблона.
    """
    context = {}
    form = LoadHHTeachersScheduleXLSXForm(request.POST, request.FILES)
    if form.is_valid():
        # try:
        schedule_dataframe = await process_teachers_schedule_xlsx(form.cleaned_data['file'])
        client = GSDocument(form.cleaned_data['gdoc_id'])
        new_glist_name = form.cleaned_data['new_glist_name'].replace('.', '_').replace(':', '_')
        create_and_update_gsheet(client, new_glist_name, schedule_dataframe)
        context['success'] = 'Готово, проверьте таблицу'
    # except ListAlreadyExists as e:
    #     form.add_error(None, f"List with this name '{new_glist_name}' already exists, delete or rename.")
    # except Exception as e:
    #     traceback_str = ''.join(traceback.format_tb(e.__traceback__))
    #     form.add_error(None, f"Произошла ошибка при загрузке данных: {e}\n\nTraceback: {traceback_str}")
    context['form'] = form
    return context


def create_and_update_gsheet(client, sheet_name, dataframe):
    """
    Создает новый лист в Google Sheets и обновляет его данными из DataFrame.

    @param client: Клиент для взаимодействия с Google Sheets.
    @param sheet_name: Название нового листа.
    @param dataframe: DataFrame с данными для обновления.
    """
    client.create_sheet(sheet_name)
    range_name = f'{sheet_name}!A1'
    client.update_sheet_with_df(range_name, dataframe)


async def process_teachers_schedule_xlsx(xlsx_file) -> DataFrame:
    """
    Обрабатывает загруженный XLSX файл с расписанием преподавателей и возвращает DataFrame.

    @param xlsx_file: Файл XLSX с расписанием преподавателей.
    @return: DataFrame с обработанным расписанием.
    """
    teachers_parsed_schedule = await parse_teachers_schedule_from_dj_mem(xlsx_file)
    schedule_dataframe = await create_schedule(teachers_parsed_schedule)
    return schedule_dataframe
