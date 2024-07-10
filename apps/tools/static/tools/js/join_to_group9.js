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
const summerInfoModal = new bootstrap.Modal(document.getElementById('summerInfo'), {
    keyboard: false
});

const queryParams = Client.getParamsFromCurrentURL();

function hideAllModals() {
    successModal.hide();
    confirmationModal.hide();
    nothingFitModal.hide();
}

async function getAvailableFormingGroups(params) {
    try {
        return await Client.sendGet(
            Client.getProtocolAndDomain() +
            '/api/v1/tools/get_forming_groups_for_join/',
            params
        );
    } catch (error) {
        raiseErrorModal(`Ошибка получения групп, свяжитесь с менеджером.`);
        return null;
    }
}

function raiseErrorModal(error) {
    hideAllModals();
    document.querySelector('.error-modal-text-content').textContent = error;
    if (Object.keys(queryParams).length > 1) {
        document.querySelector('#group_join_content').classList.add('d-none');
    }
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
    } else {
        successTitleEl.parentElement.classList.add('border-0');
        successModalBodyEl.classList.add('pt-0');
    }

    document.querySelector('#group_join_content').classList.add('d-none');
    successModal.show();
}

async function postJoinStudentToGroup(student_id, group_id, TZ, join_type) {
    try {
        const res = await Client.sendPost(
            Client.getProtocolAndDomain() +
            '/api/v1/tools/student_to_forming_group/',
            {
                student_id: student_id,
                group_id: group_id,
                client_tz: TZ,
                join_type: join_type
            }
        );
        return res;
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
                'discipline': queryParams['discipline'],
                'student_id': queryParams['student_id']
            }
        );
    } catch (error) {
        raiseErrorModal(`Ошибка на нашей стороне, попробуйте перезагрузить страницу или свяжитесь с менеджером.`);
        return null;
    }
}

function joinStudentToGroup(student_id, group, TZ) {
    console.log(group)
    postJoinStudentToGroup(student_id, group['Id'], TZ, join_type).then(response => {
        confirmationModal.hide();
        document.getElementById('confirmationModal').classList.remove('show');

        if (response.data.success) {
            const groupPreview = createUnitEl(group, TZ);
            groupPreview.classList.remove('bg-primary');
            groupPreview.classList.add('frcc');
            raiseSuccessModal(
                'Вы успешно записаны на занятие',
                'Сделайте скриншот, чтобы не забыть 😉',
                groupPreview
            );
        } else {
            raiseErrorModal('Похоже произошла ошибка, менеджер свяжется с вами в рабочее время.');
        }
    });
}

function createDateFromString(dateTimeString) {
    const [date, time] = dateTimeString.split(' ');
    const [year, month, day] = date.split('-');
    const [hour, minute] = time.split(':');
    return new Date(year, month - 1, day, hour, minute);
}

function adjustDateHours(date, hoursChange) {
    const newDate = new Date(date);
    newDate.setHours(newDate.getHours() + hoursChange);
    return newDate;
}

function createUnitEl(unit, TZ, wrapperFilterStyle = '') {
    const div = document.createElement('div');
    div.className = 'schedule_item';

    const dateP = document.createElement('div');
    dateP.className = 'frcc gap-2 fs-5 w-100';

    const schedule = unit.ScheduleItems[0];
    const first_day = unit.Days[0];

    const moscowTZ = 3;
    const diff = TZ - moscowTZ;
    const datetimeStart = adjustDateHours(
        createDateFromString(`${first_day.Date} ${schedule.BeginTime}`),
        diff
    );
    const datetimeEnd = adjustDateHours(
        createDateFromString(`${first_day.Date} ${schedule.EndTime}`),
        diff
    );

    const formatDate = (date) => date.toString().padStart(2, '0');
    const day = formatDate(datetimeStart.getDate());
    const month = formatDate(datetimeStart.getMonth() + 1);
    const startHours = formatDate(datetimeStart.getHours());
    const startMinutes = formatDate(datetimeStart.getMinutes());
    const endHours = formatDate(datetimeEnd.getHours());
    const endMinutes = formatDate(datetimeEnd.getMinutes());

    if (join_type === 'summer') {
        const second_day = unit.Days[1];
        const datetimeStart2 = adjustDateHours(
            createDateFromString(`${second_day.Date} ${schedule.BeginTime}`),
            diff
        );
        const datetimeEnd2 = adjustDateHours(
            createDateFromString(`${second_day.Date} ${schedule.EndTime}`),
            diff
        );
        const day2 = formatDate(datetimeStart2.getDate());
        const month2 = formatDate(datetimeStart2.getMonth() + 1);
        const startHours2 = formatDate(datetimeStart2.getHours());
        const startMinutes2 = formatDate(datetimeStart2.getMinutes());
        const endHours2 = formatDate(datetimeEnd2.getHours());
        const endMinutes2 = formatDate(datetimeEnd2.getMinutes());

        dateP.innerHTML = `
            <div class="fc w-100">
                <div class="frc gap-2">
                    <img src="/static/tools/img/join_to_group/time.svg" width="24" alt="">
                    <p class="schedule_item-date">${day}.${month}</p>
                    <p class="schedule_item-time">
                        ${startHours}:${startMinutes} - ${endHours}:${endMinutes}
                    </p>
                </div>
                <div class="frc gap-2">
                    <img src="/static/tools/img/join_to_group/time.svg" width="24" alt="" class="opacity-0">
                    <p class="schedule_item-date">${day2}.${month2}</p>
                    <p class="schedule_item-time">
                        ${startHours2}:${startMinutes2} - ${endHours2}:${endMinutes2}
                    </p>
                </div>
            </div>
        `;
    } else {
        dateP.innerHTML = `
            <div class="fc w-100">
                <div class="frc gap-2">
                    <img src="/static/tools/img/join_to_group/time.svg" width="24" alt="">
                    <p class="schedule_item-date">${day}.${month}</p>
                    <p class="schedule_item-time">
                        ${startHours}:${startMinutes} - ${endHours}:${endMinutes}
                    </p>
                </div>
            </div>
        `;
    }

    div.appendChild(dateP);

    const divider = document.createElement('div');
    divider.className = 'schedule_item-divider';
    div.appendChild(divider);

    const teacherP = document.createElement('p');
    teacherP.className = 'schedule_item-teacher';
    teacherP.innerHTML = `Педагог<br><span>${schedule.Teacher}</span>`;
    div.appendChild(teacherP);

    const btnJoin = document.createElement('button');
    btnJoin.className = 'schedule_item-button';
    btnJoin.innerHTML = `Записаться`;
    div.appendChild(btnJoin);

    const studentsSpan = document.createElement('span');
    studentsSpan.className = 'schedule_item-place_leave';
    studentsSpan.textContent = `Осталось мест: ${parseInt(unit.Vacancies)}`;
    div.appendChild(studentsSpan);

    const li = document.createElement('li');
    li.style.filter = wrapperFilterStyle;
    li.appendChild(div);

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

let join_type = undefined;
let loadedGroups = undefined;
const resultContainerEl = document.querySelector('.result_container');
const groupLoadingStatusContainerEl = document.querySelector('.group_loading_status_container');
const findGroupsForUText = document.querySelector('.find-groups-for-u-text');
const inputStudentInfoContainer = document.querySelector('.input-student-info-container');
let studentId = queryParams['student_id'];

function showGroupsWithTZ(TZ) {
    const hueRotateValues = [0, 55, 280, 343];
    for (let i = 0; i < loadedGroups.length; i++) {
        const hueRotate = hueRotateValues[i % hueRotateValues.length];
        if (join_type === 'summer' && loadedGroups[i].Days.length < 2) {
            continue;
        }
        const groupEl = createUnitEl(loadedGroups[i], TZ, `hue-rotate(${hueRotate}deg)`);
        groupEl.addEventListener('click', () => {
            confirmationModal.show();

            const modalBodyEl = document.querySelector('.confirmation-modal-body');
            modalBodyEl.innerHTML = '';
            const groupPreview = createUnitEl(loadedGroups[i], TZ);
            groupPreview.classList.add('pointer-events-none', 'fs-5');
            modalBodyEl.appendChild(groupPreview);

            const confirmJoinBtn = document.getElementById('confirmJoin');
            confirmJoinBtn.onclick = () => {
                document.getElementById('confirmSpinner').classList.remove('d-none');
                joinStudentToGroup(studentId, loadedGroups[i], TZ);
                confirmJoinBtn.setAttribute('disabled', 'true');
            };
        });
        resultContainerEl.appendChild(groupEl);
    }
    document.getElementById('btn-nothing-fit').classList.remove('d-none');
    resultContainerEl.parentElement.classList.remove('d-none');
    groupLoadingStatusContainerEl.innerHTML = '';
    groupLoadingStatusContainerEl.className = '';
    const successEl = document.createElement('p');
    successEl.className = 'fs-1 mb-0 mt-3 text-center welcome-text';
    successEl.innerHTML = 'Добро пожаловать<br>в компьютерную школу будущего!<br>' +
        '<p id="help-text" class="text-center fs-5 fw-bold my-2 opacity-this85">Выберите удобную для вас группу</p>';
    groupLoadingStatusContainerEl.appendChild(successEl);
    inputStudentInfoContainer.classList.add('d-none');
}

function attachTZEventHandlers() {
    const btnsChooseTz = document.getElementsByClassName('btn-choose-tz');
    for (const btnTz of btnsChooseTz) {
        btnTz.addEventListener('click', function handleClick() {
            chooseTZModal.hide();
            if (join_type === 'summer' || join_type === 'autumn') {
                summerInfoModal.show();
            }
            document.getElementById('tz-info').classList.remove('d-none');
            const tzByMoscow = parseInt(btnTz.value) - 3;
            document.getElementById('tz-span').innerHTML = tzByMoscow < 0 ? `${tzByMoscow}` : `+${tzByMoscow}`;
            showGroupsWithTZ(parseInt(btnTz.value));
            btnTz.removeEventListener('click', handleClick); // Remove the event listener after it is used
        });
    }
    const btnChangeTz = document.getElementById('btn-change-tz');
    btnChangeTz.addEventListener('click', () => {
        resultContainerEl.innerHTML = '';
        chooseTZModal.show();
    });
}

async function main() {
    if (Object.keys(queryParams).length === 4) {
        const formNothingFit = document.getElementById('form-nothing_fit');
        formNothingFit.addEventListener('submit', (e) => {
            e.preventDefault();
            const submitButton = document.getElementById('btn-nothing-fit-submit');
            const msg = document.getElementById('nothing_fit_user_textarea').value;

            submitButton.disabled = true;
            send_nothing_fit(studentId, msg)
                .then(response => {
                    if (response.ok) {
                        raiseSuccessModal(
                            'Отлично, мы получили ваше сообщение, с вами свяжется менеджер 😉',
                            null, null
                        );
                    }
                });
        });

        const response = await getIsStudentOnDiscipline();
        const alreadyStudying = response.data;
        if (alreadyStudying) {
            raiseErrorModal(`Ученик уже есть в группе по данной дисциплине, свяжитесь с менеджером.`);
            return;
        } else if (alreadyStudying === null) return;

        getAvailableFormingGroups(Client.getParamsFromCurrentURL()).then(response => {
            const data = response.data;
            join_type = data.join_type;
            const groups = data.groups;
            if (groups.length === 0) {
                document.getElementById('nothing_fit_user_textarea').setAttribute(
                    'placeholder',
                    'К сожалению система не смогла подобрать группу. ' +
                    'Напишите подходящие вам дни и время для занятия, мы с вами свяжемся 🙂');
                nothingFitModal.show();
                groupLoadingStatusContainerEl.innerHTML = '';
                return;
            }
            loadedGroups = groups;
            attachTZEventHandlers();
            chooseTZModal.show();
        });
    } else if (Object.keys(queryParams).length === 1 && queryParams['discipline']) {
        join_type = 'autumn';
        findGroupsForUText.classList.add('d-none');
        inputStudentInfoContainer.classList.remove('d-none');
        const studentFullNameInput = document.querySelector('input[name="student_full_name"]');
        const emailInput = document.querySelector('input[name="email"]');
        const telInput = document.querySelector('input[name="tel"]');
        telInput.addEventListener('input', () => {
            let value = telInput.value;
            value = value.replace(/[^0-9+]/g, '');
            if (value.startsWith('+')) value = '+' + value.slice(1).replace(/\+/g, '');
            else value = value.replace(/\+/g, '');
            telInput.value = value;
        });
        const btnSubmitFindStudent = document.querySelector('#btnSubmitFindStudent');
        btnSubmitFindStudent.addEventListener('click', () => {
            const params = {};

            if (studentFullNameInput.value) {
                params.student_full_name = studentFullNameInput.value;
            }
            if (emailInput.value) {
                params.email = emailInput.value;
            }
            if (telInput.value) {
                params.tel = telInput.value;
            }
            params.discipline = queryParams['discipline'];
            getAvailableFormingGroups(params).then(response => {
                if (response.status === 200) {
                    const units = response.data.groups;
                    loadedGroups = units;
                    studentId = response.data.student_id;
                    if (!units.length) {
                        document.getElementById('nothing_fit_user_textarea').setAttribute(
                            'placeholder',
                            'К сожалению система не смогла подобрать группу. ' +
                            'Напишите подходящие вам дни и время для занятия, мы с вами свяжемся 🙂');
                        nothingFitModal.show();
                        return;
                    }
                    attachTZEventHandlers();
                    chooseTZModal.show();
                } else {
                    raiseErrorModal(response.data.error);
                }
            });
        });
    } else {
        raiseErrorModal(`Неверное количество параметров.`);
    }
}

await main();
