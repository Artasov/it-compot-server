from datetime import datetime


def sort_groups_by_datetime(groups):
    for group in groups:
        group['sort_key'] = datetime.strptime(group['ScheduleItems'][0]['BeginDate'] + ' ' + group['ScheduleItems'][0]['BeginTime'], "%Y-%m-%d %H:%M")
    sorted_groups = sorted(groups, key=lambda x: x['sort_key'])

    for group in sorted_groups:
        del group['sort_key']
    return sorted_groups

