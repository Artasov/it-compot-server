import Client from "../../../../static/Core/js/classes/Client.js";

const errorModal = new bootstrap.Modal(document.getElementById('errorModal'), {
    keyboard: true
});
const successModal = new bootstrap.Modal(document.getElementById('successModal'), {
    keyboard: true
});
const confirmationModal = new bootstrap.Modal(document.getElementById('confirmationModal'), {
    keyboard: false
});
const nothingFitModal = new bootstrap.Modal(document.getElementById('nothingFitModal'), {
    keyboard: false
});
const chooseTZModal = new bootstrap.Modal(document.getElementById('chooseTZModal'), {
    backdrop: 'static',
    keyboard: false
});

function hideAllModals() {
    successModal.hide();
    confirmationModal.hide();
    nothingFitModal.hide();
}

async function getAvailableFormingGroups() {
    try {
        return await Client.sendGet(
            Client.getProtocolAndDomain() +
            '/api/v1/tools/get_forming_groups_for_join/',
            Client.getParamsFromCurrentURL()
        );
    } catch (error) {
        raiseErrorModal(`Ошибка получения групп, свяжитесь с менеджером.`);
        return null;
    }
}

function raiseErrorModal(error) {
    hideAllModals();
    document.querySelector('.error-modal-body').textContent = error;
    document.querySelector('#group_join_content').classList.add('d-none');
    errorModal.show();
}

function raiseSuccessModal(title, subtitle, contentElement) {
    hideAllModals();

    const successTitleEl = document.querySelector('#successModal .modal-title');
    successTitleEl.innerHTML = title;

    if (subtitle !== null) {
        const successSubTitleEl = document.querySelector('#successModal .modal-subtitle');
        successSubTitleEl.innerHTML = subtitle;
    }
    const successModalBodyEl = document.querySelector('.success-modal-body');
    if (contentElement !== null) {
        successModalBodyEl.innerHTML = '';
        successModalBodyEl.appendChild(contentElement);

        document.querySelector('.success-modal-body').appendChild(contentElement)
    } else {
        successTitleEl.parentElement.classList.add('border-0');
        successModalBodyEl.classList.add('pt-0');
    }

    document.querySelector('#group_join_content').classList.add('d-none');
    successModal.show();
}

async function postJoinStudentToGroup(student_id, group_id, TZ) {
    try {
        return await Client.sendPost(
            Client.getProtocolAndDomain() +
            '/api/v1/tools/student_to_forming_group/',
            {
                'student_id': student_id,
                'group_id': group_id,
                'client_tz': TZ
            }
        );
    } catch (error) {
        raiseErrorModal(`Ошибка добавления ученика в группу, свяжитесь с менеджером.`);
        return null;
    }
}

async function getIsStudentOnDiscipline() {
    try {
        return await Client.sendGet(
            Client.getProtocolAndDomain() +
            '/api/v1/tools/get_is_student_in_group_on_discipline/',
            {
                'discipline': Client.getParamsFromCurrentURL()['discipline'],
                'student_id': Client.getParamsFromCurrentURL()['student_id'],
            }
        );
    } catch (error) {
        raiseErrorModal(`Ошибка на нашей стороне, попробуйте перезагрузить страницу или свяжитесь с менеджером.`);
        return null;
    }
}

function joinStudentToGroup(student_id, group, TZ) {
    postJoinStudentToGroup(student_id, group['Id'], TZ).then(response => {

        confirmationModal.hide();
        document.getElementById('confirmationModal').classList.remove('show');

        if (response.success) {
            const groupPreview = createGroupEl(group, TZ);
            groupPreview.classList.remove('bg-primary');
            groupPreview.classList.add('bg-success', 'pointer-events-none', 'fs-5');
            raiseSuccessModal(
                'Вы успешно записаны на занятие',
                'Сделайте скриншот, чтобы не забыть 😉',
                groupPreview
            )
        } else {
            raiseErrorModal('Похоже произошла ошибка, менеджер свяжется с вами в рабочее время.')
        }
    })
}


function createDateFromString(dateTimeString) {
    // Пример входной строки '2024-03-23 19:40'
    const parts = dateTimeString.split(' ');
    const dateParts = parts[0].split('-');
    const timeParts = parts[1].split(':');
    return new Date(dateParts[0], dateParts[1] - 1, dateParts[2], timeParts[0], timeParts[1]);
}

function adjustDateHours(date, hoursChange) {
    const newDate = new Date(date); // Создаем копию, чтобы не изменять исходный объект
    newDate.setHours(newDate.getHours() + hoursChange);
    return newDate;
}

function createGroupEl(group, TZ) {
    const li = document.createElement('li');
    li.className = "unit-item rounded-3 text-light bg-primary";

    const dateP = document.createElement('p');
    dateP.classList.add('fw-bold', 'fs-5', 'frsc', 'gap-2');
    const schedule = group.ScheduleItems[0];

    // Вычисляем даты относительно TZ
    const moscowTZ = 3; // Московское время +3
    const diff = TZ - moscowTZ;
    const datetimeStart = adjustDateHours(
        createDateFromString(`${schedule.BeginDate} ${schedule.BeginTime}`),
        diff
    );
    const datetimeEnd = adjustDateHours(
        createDateFromString(`${schedule.BeginDate} ${schedule.EndTime}`),
        diff
    );
    const day = datetimeStart.getDate().toString().padStart(2, '0');
    const month = (datetimeStart.getMonth() + 1).toString().padStart(2, '0'); // месяцы начинаются с 0
    const startHours = datetimeStart.getHours().toString().padStart(2, '0');
    const startMinutes = datetimeStart.getMinutes().toString().padStart(2, '0');
    const endHours = datetimeEnd.getHours().toString().padStart(2, '0');
    const endMinutes = datetimeEnd.getMinutes().toString().padStart(2, '0');

    dateP.innerHTML = `
        <div class="frcc gap-2">
            <span class="bg-primary-05 rounded-2 px-2" style="padding-top: 0.1em;">
                ${day}.${month}
            </span>
            <span class="bg-primary-05 rounded-2 px-2 fw-normal fs-6" style="padding-top: 0.1em;">
                ${startHours}:${startMinutes} - ${endHours}:${endMinutes}
            </span>
        </div>
    `;
    li.appendChild(dateP);

    // Добавляем информацию о количестве учеников и вакансиях
    const frbDiv = document.createElement('div');
    frbDiv.className = "d-flex gap-2";
    const studentsSpan = document.createElement('span');
    studentsSpan.classList.add('fw-bold');
    studentsSpan.textContent = 'Осталось мест: ';
    const vacanciesSpan = document.createElement('span');
    const vacancies_count = parseInt(group.Vacancies);
    vacanciesSpan.textContent = `${vacancies_count}`;
    frbDiv.appendChild(studentsSpan);
    frbDiv.appendChild(vacanciesSpan);
    li.appendChild(frbDiv);

    // Добавляем информацию о преподавателе
    const teacherP = document.createElement('p');
    teacherP.classList.add('fw-bold');
    teacherP.innerHTML = `Педагог: <br><span class="fw-normal">${schedule.Teacher}</span>`;
    li.appendChild(teacherP);

    return li;
}

async function send_nothing_fit(student_id, msg) {
    try {
        return await Client.sendPost(
            Client.getProtocolAndDomain() +
            '/api/v1/tools/send_nothing_fit/',
            {
                'student_id': student_id,
                'msg': msg
            }
        );
    } catch (error) {
        raiseErrorModal(`Ошибка добавления ученика в группу, свяжитесь с менеджером.`);
        return null;
    }
}


let loadedGroups = undefined;
const resultContainerEl = document.querySelector('.result_container');
const groupLoadingStatusContainerEl = document.querySelector('.group_loading_status_container');

function showGroupsWithTZ(TZ) {
    // TZ - цифра (данные в группах указаны по умолчанию в +3)
    // например -1 +1 +3 +2 и тому подобные цифры.
    // Могут быть как отрицательные, так и положительные.
    for (const group of loadedGroups) {
        const groupEl = createGroupEl(group, TZ)
        groupEl.addEventListener('click', () => {
            const studentId = Client.getParamsFromCurrentURL()['student_id'];
            confirmationModal.show();

            const modalBodyEl = document.querySelector('.confirmation-modal-body');
            modalBodyEl.innerHTML = '';
            const groupPreview = createGroupEl(group, TZ);
            groupPreview.classList.add('pointer-events-none', 'fs-5');
            const submitQuestionText = document.createElement('p');
            submitQuestionText.className = 'text-center mb-0 mt-2 fs-5';
            submitQuestionText.innerHTML = 'Вы действительно хотите записаться в выбранную группу?';
            modalBodyEl.appendChild(groupPreview);
            modalBodyEl.appendChild(submitQuestionText);


            document.getElementById('confirmJoin').onclick = () => {
                document.getElementById('confirmSpinner').classList.remove('d-none')
                joinStudentToGroup(studentId, group, TZ);
                document.getElementById('confirmJoin').setAttribute('disabled', 'true');
            };
        });
        resultContainerEl.appendChild(groupEl);
    }
    document.getElementById('btn-nothing-fit').classList.remove('d-none');
    resultContainerEl.parentElement.classList.remove('d-none');
    groupLoadingStatusContainerEl.innerHTML = '';
    groupLoadingStatusContainerEl.className = '';
    const successEl = document.createElement('p');
    successEl.className = 'text-center fw-bold fs-5 m-0 opacity-75';
    successEl.style.color = '#4058ff'
    successEl.innerHTML = 'Готово! Найденные группы ниже.';
    groupLoadingStatusContainerEl.appendChild(successEl);
}


async function main() {
    // Если параметров в запросе достаточно
    if (Object.keys(Client.getParamsFromCurrentURL()).length !== 4) {
        raiseErrorModal(`Неверное количество параметров.`);
        return;
    }
    // Связываем форму ничего не подошло и отправку запроса об этом
    const formNothingFit = document.getElementById('form-nothing_fit');
    formNothingFit.addEventListener('submit', (e) => {
        e.preventDefault();
        const submitButton = document.getElementById('btn-nothing-fit-submit');
        const msg = document.getElementById('nothing_fit_user_textarea').value;

        submitButton.disabled = true;

        send_nothing_fit(Client.getParamsFromCurrentURL()['student_id'], msg)
            .then(data => {
                console.log(data)
                if (data) {
                    raiseSuccessModal(
                        'Отлично, мы получили ваше сообщение, с вами свяжется менеджер 😉',
                        null, null
                    )
                }
            })
    })
    // Проверяем, может быть ученик уже учится по этой дисциплине
    const alreadyStudying = await getIsStudentOnDiscipline()
    if (alreadyStudying) {
        raiseErrorModal(`Ученик уже есть в группе по данной дисциплине, свяжитесь с менеджером.`);
        return;
    } else if (alreadyStudying === null) return;

    // Подгружаем группы
    getAvailableFormingGroups().then(groups => {
        if (groups.length === 0) {
            document.getElementById('nothing_fit_user_textarea').setAttribute(
                'placeholder',
                'К сожалению система не смогла подобрать группу. ' +
                'Напишите подходящие вам дни и время для занятия, мы с вами свяжемся 🙂')
            nothingFitModal.show();
            groupLoadingStatusContainerEl.innerHTML = '';
            return;

        }
        loadedGroups = groups
        const btnsChooseTz = document.getElementsByClassName('btn-choose-tz');
        for (const btnTz of btnsChooseTz) {
            btnTz.addEventListener('click', () => {
                chooseTZModal.hide();
                document.getElementById('tz-info').classList.remove('d-none');
                const tzByMoscow = parseInt(btnTz.value) - 3;
                document.getElementById('tz-span').innerHTML = tzByMoscow < 0 ? `${tzByMoscow}` : `+${tzByMoscow}`;
                showGroupsWithTZ(parseInt(btnTz.value));
            })
        }
        const btnChangeTz = document.getElementById('btn-change-tz');
        btnChangeTz.addEventListener('click', () => {
            resultContainerEl.innerHTML = '';
            chooseTZModal.show();
        })
        chooseTZModal.show();
    });

}

await main();


