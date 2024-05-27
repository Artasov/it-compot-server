import Client from "../../../../static/Core/js/classes/Client.js";

const errorTextEl = document.querySelector('.error-text');
const loadingEl = document.getElementById('loading_spinner_block-lessons');

function setLoading(flag) {
    loadingEl.className = `${flag ? '' : 'd-none'}`
}

function setError(error_text) {
    errorTextEl.innerHTML = error_text;
    setLoading(false);
}

try {
    function isDateInRange(dateStr, startDateStr, endDateStr) {
        const date = new Date(dateStr);
        const startDate = new Date(startDateStr);
        const endDate = new Date(endDateStr);
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


    async function postSendReport(ed_unit_id, day_date, theme_number, theme_name, students_comments, lessonCompletionPercentage, type) {
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
                    students_comments: students_comments,
                    type: type,
                }
            );
        } catch (error) {
            setError('Ошибка отправки отчета')
            console.log(error)
            return null;
        }
    }


    const chooseUnitContainer = document.querySelector('.choose_unit_container');
    const successTextEl = document.querySelector('.success-text');

    const lessonSetInfoContainer = document.querySelector('.lesson_set_info_container');
    const lessonPreviewEl = document.getElementById('lesson-preview');

    const btnReportSubmit = document.getElementById('btn-report-submit');
    const btnBackToChooseUnit = document.getElementById('btn-back-to-choose-unit');
    btnBackToChooseUnit.addEventListener('click', backToChooseUnit);

    const themeSelectEl = document.querySelector('.lesson_theme_select');
    const additionalInfoTextEl = document.querySelector('textarea[name="additional_info_text"]');
    btnReportSubmit.addEventListener('click', sendReport);
    const lessonCompletionPercentage = document.getElementById('lesson_completion_percentage');
    const lessonCompletionPercentageCount = document.getElementById('lesson_completion_percentage-count');
    lessonCompletionPercentageCount.textContent = lessonCompletionPercentage.value;
    lessonCompletionPercentage.oninput = function () {
        lessonCompletionPercentageCount.textContent = this.value;
    }

    let choosedEdUnitDay = [];


    async function sendReport(e) {
        e.preventDefault();

        if (!themeSelectEl.classList.contains('d-none') && themeSelectEl.value === '0') {
            setError('Вы не выбрали тему для занятия.')
            return;
        }
        if (lessonCompletionPercentage.value < 1) {
            setError('Урок пройден менее чем на 1%.')
            return;
        }

        lessonSetInfoContainer.classList.add('d-none');
        setError('');
        setLoading(true);
        btnBackToChooseUnit.classList.add('d-none');

        let studentsComments = [];
        for (const student of choosedEdUnitDay[0]['Students']) {
            for (const sDay of student['Days']) {
                if (sDay['Date'] === choosedEdUnitDay[0]['Days'][choosedEdUnitDay[1]]['Date']) {
                    const description = sDay.Description ? sDay.Description : '';
                    studentsComments.push({
                        ClientId: student['StudentClientId'],
                        StudentName: student['StudentName'],
                        Pass: sDay.Pass,
                        Description: (description.toLowerCase().includes('перенос') ? false : description) || additionalInfoTextEl.value
                    });
                }
            }
        }
        let themeName;
        if (themeSelectEl.classList.contains('d-none')) {
            themeName = 'Занятия вне программы.';
            themeSelectEl.value = '';
        } else {
            themeName = themeSelectEl.querySelector(`option[value="${themeSelectEl.value}"]`).textContent.slice(
                3, themeSelectEl.textContent.length
            )
        }
        const result = await postSendReport(
            choosedEdUnitDay[0]['Id'],
            choosedEdUnitDay[0]['Days'][choosedEdUnitDay[1]]['Date'],
            themeSelectEl.value,
            themeName,
            studentsComments,
            lessonCompletionPercentage.value,
            choosedEdUnitDay[0]['Type'],
        )
        console.log(result)
        if (result.success) {
            successTextEl.innerHTML = 'Комментарий к уроку успешно отправлен!';
            document.getElementById(`${choosedEdUnitDay[0]['Id']}-${choosedEdUnitDay[1]}`).remove();
        } else {
            setError(result.error)
            lessonSetInfoContainer.classList.remove('d-none');
        }
        btnBackToChooseUnit.classList.remove('d-none');
        setLoading(false);
    }

    function backToChooseUnit() {
        lessonSetInfoContainer.classList.add('d-none');
        chooseUnitContainer.classList.remove('d-none');
        btnBackToChooseUnit.classList.add('d-none');
        lessonPreviewEl.innerHTML = '';
        successTextEl.innerHTML = '';
        setError('');
    }

    async function chooseEdUnitDay(unit, day_index) {
        setLoading(true);
        chooseUnitContainer.classList.add('d-none');
        choosedEdUnitDay = [unit, day_index];
        lessonPreviewEl.appendChild(createEdUnitEl(unit, day_index));
        if (unit.Type !== 'Individual') {
            const studentsSpanEl = document.createElement('p');
            studentsSpanEl.innerHTML = 'Ученики';
            studentsSpanEl.className = 'text-left';
            lessonPreviewEl.appendChild(studentsSpanEl);
            for (const student of unit.Students) {
                const studentEl = document.createElement('div');
                studentEl.className = 'frsc bg-opacity-25 bg-secondary p-2 rounded-2';
                studentEl.innerHTML = student.StudentName;
                lessonPreviewEl.appendChild(studentEl);
            }
        }
        if (day_index !== 0) {
            const day = unit.Days[day_index - 1];
            const student = unit.Students[0]; // Берем первого студента на похуй
            const sDays = student.Days;
            for (const sDay of sDays) {
                if (sDay.Date === day['Date']) {
                    if (sDay.Description) {
                        const previewsThemeSpanEl = document.createElement('p');
                        previewsThemeSpanEl.innerHTML = 'Предыдущая тема';
                        previewsThemeSpanEl.className = 'text-left';
                        lessonPreviewEl.appendChild(previewsThemeSpanEl)
                        const previewsThemeEl = document.createElement('div');
                        previewsThemeEl.innerHTML = sDay.Description.replace(/\*/g, '<br>*').replace('<br>', '');
                        previewsThemeEl.className = 'frsc bg-opacity-25 bg-secondary p-2 rounded-2 text-left';
                        lessonPreviewEl.appendChild(previewsThemeEl)
                    }
                }
            }
        }
        const response = await getThemesByDiscipline(unit.Discipline);
        if (response.themes) {
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
        } else {
            themeSelectEl.classList.add('d-none')
        }
        lessonSetInfoContainer.classList.remove('d-none');
        setLoading(false);
        btnBackToChooseUnit.classList.remove('d-none');
    }


    function createEdUnitEl(unit, day_index) {
        console.log(unit)
        const unitEl = document.createElement('div');
        unitEl.setAttribute('id', `${unit.Id}-${day_index}`);
        unitEl.className = 'fcss bg-opacity-25 bg-secondary p-2 rounded-2 position-relative';

        const nameEl = document.createElement('span');
        nameEl.textContent = unit.Name;
        unitEl.appendChild(nameEl);

        const timeEl = document.createElement('p');
        if (unit.Type === 'Individual') {
            timeEl.textContent = `${unit.Days[day_index].Date} ${unit.Students[0].BeginTime}`;
        } else {
            for (const scheduleItem of unit.ScheduleItems) {
                if(isDateInRange(unit.Days[day_index].Date), scheduleItem.BeginDate, scheduleItem.EndDate){
                    timeEl.textContent = `${unit.Days[day_index].Date} ${scheduleItem.BeginTime}`;
                    break;
                }
            }
        }

        unitEl.appendChild(timeEl);

        return unitEl;
    }


    setLoading(true);
    const response = await getEdUnitsForReport()
    const units = response.units

    setLoading(false);

    for (const unit of units) {
        const unitDays = unit.Days;
        // Проверяем дни учебной единицы на отсутствие комментария
        for (let i = 0; i < unitDays.length; i++) {
            if (!unitDays[i].Pass) {
                let commentExists = true;
                for (const student of unit['Students']) {
                    for (const sDay of student['Days']) {
                        if (sDay['Date'] === unit['Days'][i]['Date']) {
                            if (!sDay.Description ||
                                (
                                    sDay.Description.toLowerCase().includes('перенос') &&
                                    !sDay.Description.toLowerCase().includes('*')
                                )
                            ) {
                                commentExists = false;
                                break;
                            }
                        }
                    }
                }
                if (!commentExists) {
                    const unitEl = createEdUnitEl(unit, i)

                    // if (unit.Type !== 'Individual') {
                    //     console.log(unit)
                    // }

                    unitEl.addEventListener('click', () => {
                        chooseEdUnitDay(unit, i);
                    })
                    document.getElementById('units-container').appendChild(unitEl)
                }

            }
        }

    }
    chooseUnitContainer.classList.remove('d-none');
} catch (e) {
    console.error(e)
    setError(e)
}