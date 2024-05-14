import Client from "../../../../static/Core/js/classes/Client.js";

function isDateInRange(dateStr, startDate, endDate) {
    const date = new Date(dateStr);
    return date >= startDate && date <= endDate;
}

async function getEdUnitsForReport() {
    try {
        return await Client.sendGet(
            Client.getProtocolAndDomain() +
            '/api/v1/tools/get_teacher_lesson_for_report/',
            []
        );
    } catch (error) {
        // raiseErrorModal(`Ошибка получения групп, свяжитесь с менеджером.`);
        console.log(error)
        return null;
    }
}

async function getThemesByDiscipline(discipline) {
    try {
        console.log(discipline)
        return await Client.sendGet(
            Client.getProtocolAndDomain() +
            '/api/v1/tools/get_course_themes_view/',
            {discipline: discipline}
        );
    } catch (error) {
        // raiseErrorModal(`Ошибка получения тем по дисциплине.`);
        console.log(error)
        return null;
    }
}


async function postSendReport(ed_unit_id, day_date, theme_number, theme_name, additionalInfo, lessonCompletionPercentage) {
    try {
        return await Client.sendPost(
            Client.getProtocolAndDomain() +
            '/api/v1/tools/send_lesson_report/',
            {
                ed_unit_id: ed_unit_id,
                day_date: day_date,
                theme_number: theme_number,
                theme_name: theme_name,
                lesson_completion_percentage: lessonCompletionPercentage,
                additional_info: additionalInfo,
            }
        );
    } catch (error) {
        setError('Ошибка отправки отчета')
        console.log(error)
        return null;
    }
}

function setError(error_text) {
    errorTextEl.innerHTML = error_text;
}

const chooseUnitContainer = document.querySelector('.choose_unit_container');
const errorTextEl = document.querySelector('.error-text');

const lessonSetInfoContainer = document.querySelector('.lesson_set_info_container');
const lessonPreviewEl = document.getElementById('lesson-preview');

const btnReportSubmit = document.getElementById('btn-report-submit');
const themeSelectEl = document.querySelector('.lesson_theme_select');
const additionalInfoEl = document.querySelector('textarea[name="additional_info"]');
btnReportSubmit.addEventListener('click', sendReport);
const edUnitIdInput = document.getElementById('ed_unit_id');
const lessonCompletionPercentage = document.getElementById('lesson_completion_percentage');
const lessonCompletionPercentageCount = document.getElementById('lesson_completion_percentage-count');
lessonCompletionPercentageCount.textContent = lessonCompletionPercentage.value;
lessonCompletionPercentage.oninput = function () {
    lessonCompletionPercentageCount.textContent = this.value;
}

async function sendReport(e) {
    e.preventDefault();
    if (themeSelectEl.value === '0') {
        setError('Вы не выбрали тему для занятия.')
        return;
    }
    if (lessonCompletionPercentage.value < 1) {
        setError('Урок пройден менее чем на 1%.')
        return;
    }
    const result = await postSendReport(
        edUnitIdInput.value.split(' ')[0],
        edUnitIdInput.value.split(' ')[1],
        themeSelectEl.value,
        themeSelectEl.querySelector(`option[value="${themeSelectEl.value}"]`).textContent.slice(3, themeSelectEl.textContent.length),
        additionalInfoEl.value,
        lessonCompletionPercentage.value
    )
    console.log(result)
    if (result.error) {
        setError(result.error)
    }
}

async function chooseEdUnitDay(unit, day_index) {
    chooseUnitContainer.classList.add('d-none');
    edUnitIdInput.value = `${unit.Id} ${unit.Days[day_index].Date}`
    lessonPreviewEl.appendChild(createEdUnitEl(unit, day_index));
    const response = await getThemesByDiscipline(unit.Discipline);
    // add select title
    themeSelectEl.innerHTML = '';
    const themeBaseOptionEl = document.createElement('option');
    themeBaseOptionEl.textContent = 'Выберите тему урока';
    themeBaseOptionEl.value = 0;
    themeSelectEl.appendChild(themeBaseOptionEl);
    // add themes options
    for (let i = 0; i < response.themes.length; i++) {
        const themeOptionEl = document.createElement('option');
        themeOptionEl.textContent = `${i + 1}. ` + response.themes[i][0];
        themeOptionEl.value = i + 1;
        themeSelectEl.appendChild(themeOptionEl);
    }
    lessonSetInfoContainer.classList.remove('d-none');
}


function createEdUnitEl(unit, day_index) {
    console.log(unit)
    const unitEl = document.createElement('div');
    unitEl.className = 'fcss bg-opacity-25 bg-secondary p-2 rounded-2';

    const nameEl = document.createElement('span');
    nameEl.textContent = unit.Name;
    unitEl.appendChild(nameEl);

    const timeEl = document.createElement('p');
    if (unit.ScheduleItems && unit.ScheduleItems.length !== 0) {
        timeEl.textContent = `${unit.Days[day_index].Date} ${unit.ScheduleItems[0].BeginTime}`;
    } else {
        timeEl.textContent = 'Время не указано';
    }
    unitEl.appendChild(timeEl);

    return unitEl;
}


const response = await getEdUnitsForReport()
const units = response.units
const today = new Date();
const thirtyDaysAgo = new Date(today);
thirtyDaysAgo.setDate(today.getDate() - 30);

for (const unit of units) {
    const unitDays = unit.Days;
    for (let i = 0; i < unitDays.length; i++) {
        if (isDateInRange(unitDays[i].Date, thirtyDaysAgo, today) && !unitDays[i].Pass) {
            const unitEl = createEdUnitEl(unit, i)
            unitEl.addEventListener('click', () => {
                chooseEdUnitDay(unit, i);
            })
            document.getElementById('units-container').appendChild(unitEl)
        }
    }
}