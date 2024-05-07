import Client from "../../../../static/Core/js/classes/Client.js";

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


async function postSendReport(theme_number, theme_name, additionalInfo, lessonCompletionPercentage) {
    try {
        return await Client.sendPost(
            Client.getProtocolAndDomain() +
            '/api/v1/tools/send_lesson_report/',
            {
                theme_number: theme_number,
                theme_name: theme_name,
                lesson_completion_percentage: lessonCompletionPercentage,
                additional_info: additionalInfo,
            }
        );
    } catch (error) {
        console.log('Ошибка отправки отчета')
        console.log(error)
        return null;
    }
}

const chooseUnitContainer = document.querySelector('.choose_unit_container');

const lessonSetInfoContainer = document.querySelector('.lesson_set_info_container');
const lessonPreviewEl = document.getElementById('lesson-preview');

const btnReportSubmit = document.getElementById('btn-report-submit');
const themeSelectEl = document.querySelector('.lesson_theme_select');
const additionalInfoEl = document.querySelector('textarea[name="additional_info"]');
btnReportSubmit.addEventListener('click', sendReport);
const lessonCompletionPercentage = document.getElementById('lesson_completion_percentage');
const lessonCompletionPercentageCount = document.getElementById('lesson_completion_percentage-count');
lessonCompletionPercentageCount.textContent = lessonCompletionPercentage.value;
lessonCompletionPercentage.oninput = function () {
    lessonCompletionPercentageCount.textContent = this.value;
}

async function sendReport(e) {
    e.preventDefault();
    if (themeSelectEl.value === '0') {
        console.log('Вы не выбрали тему для занятия.')
        return;
    }
    if (lessonCompletionPercentage.value < 1) {
        console.log('Урок пройден менее чем на 1%.')
        return;
    }
    const result = await postSendReport(
        themeSelectEl.value,
        themeSelectEl.querySelector(`option[value="${themeSelectEl.value}"]`).textContent.slice(3, themeSelectEl.textContent.length),
        additionalInfoEl.value,
        lessonCompletionPercentage.value
    )

    console.log(result)
}

async function chooseEdUnit(unit) {
    chooseUnitContainer.classList.add('d-none');
    lessonPreviewEl.appendChild(createEdUnitEl(unit));
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


function createEdUnitEl(unit) {
    console.log(unit)
    const unitEl = document.createElement('div');
    unitEl.className = 'fcss bg-opacity-25 bg-secondary p-2 rounded-2';

    const nameEl = document.createElement('span');
    nameEl.textContent = unit.Name;
    unitEl.appendChild(nameEl);

    const timeEl = document.createElement('p');
    if (unit.ScheduleItems && unit.ScheduleItems.length !== 0) {
        timeEl.textContent = `Время: ${unit.ScheduleItems[0].BeginTime}`;
    } else {
        timeEl.textContent = 'Время не указано';
    }
    unitEl.appendChild(timeEl);

    return unitEl;
}


const response = await getEdUnitsForReport()
for (const unit of response.units) {
    const unitEl = createEdUnitEl(unit)
    unitEl.addEventListener('click', () => {
        chooseEdUnit(unit);
    })
    document.getElementById('units-container').appendChild(unitEl)
}