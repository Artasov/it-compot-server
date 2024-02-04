import Client from "../../../../static/Core/js/classes/Client.js";


async function getAvailableFormingGroups() {
    try {
        return await Client.sendGet(
            Client.getProtocolAndDomain() +
            '/api/v1/tools/get_forming_groups_for_join/',
            Client.getParamsFromCurrentURL()
        );
    } catch (error) {
        raiseErrorModal(`Ошибка получения групп, свяжитесь с менеджером и поругайтесь на него.`);
        return null;
    }
}

function raiseErrorModal(error) {
    document.querySelector('.error-modal-body').textContent = error;
    const errorModal = new bootstrap.Modal(document.getElementById('errorModal'), {
        keyboard: true
    });
    document.querySelector('#group_join_content').classList.add('d-none');
    errorModal.show();
}

function raiseSuccessModal(contentElement) {
    const successModalBodyEl = document.querySelector('.success-modal-body');
    successModalBodyEl.innerHTML = '';
    successModalBodyEl.appendChild(contentElement);
    document.querySelector('.success-modal-body').appendChild(contentElement)
    const successModal = new bootstrap.Modal(document.getElementById('successModal'), {
        keyboard: true
    });
    document.querySelector('#group_join_content').classList.add('d-none');
    successModal.show();
}

async function postJoinStudentToGroup(student_id, group_id) {
    try {
        return await Client.sendPost(
            Client.getProtocolAndDomain() +
            '/api/v1/tools/student_to_forming_group/',
            {
                'student_id': student_id,
                'group_id': group_id

            }
        );
    } catch (error) {
        raiseErrorModal(`Ошибка добавления ученика в группу, свяжитесь с менеджером и поругайтесь на него.`);
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
        raiseErrorModal(`Ошибка на нашей стороне, попробуйте перезагрузить страницу или свяжитесь с менеджером и поругайтесь на него.`);
        return null;
    }
}

const confirmationModal = new bootstrap.Modal(document.getElementById('confirmationModal'), {
    keyboard: false
});

function joinStudentToGroup(student_id, group) {
    postJoinStudentToGroup(student_id, group['Id']).then(response => {

        confirmationModal.hide();
        document.getElementById('confirmationModal').classList.remove('show');

        if (response.success) {
            const groupPreview = createGroupEl(group);
            groupPreview.classList.remove('bg-primary');
            groupPreview.classList.add('bg-success', 'pointer-events-none', 'fs-5');
            raiseSuccessModal(groupPreview)
        } else {
            raiseErrorModal('Похоже произошла ошибка, менеджер свяжется с вами в рабочее время.')
        }
    })
}

function createGroupEl(group) {
    // Создаем элемент списка
    const li = document.createElement('li');
    li.className = "group-item bg-primary rounded-3 text-light";

    // Добавляем информацию о типе группы
    // const typeP = document.createElement('p');
    // typeP.textContent = group.Type;
    // li.appendChild(typeP);

    // Добавляем информацию о дате и времени
    const dateP = document.createElement('p');
    dateP.classList.add('fw-bold', 'fs-5', 'frsc', 'gap-2');
    const schedule = group.ScheduleItems[0];
    dateP.innerHTML = `${schedule.BeginDate}
        <span class="fw-normal fs-6" style="padding-bottom: 2px;">${schedule.BeginTime} - ${schedule.EndTime}</span>`;
    li.appendChild(dateP);

    // Добавляем информацию о количестве учеников и вакансиях
    const frbDiv = document.createElement('div');
    frbDiv.className = "d-flex gap-2";
    const studentsSpan = document.createElement('span');
    studentsSpan.classList.add('fw-bold');
    studentsSpan.textContent = 'Учеников';
    const vacanciesSpan = document.createElement('span');
    const students_count = parseInt(group.StudentsCount);
    const vacancies_count = parseInt(group.Vacancies);
    vacanciesSpan.textContent = `${students_count} / ${students_count + vacancies_count}`;
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

async function main() {
    // Если параметров в запросе достаточно
    if (Object.keys(Client.getParamsFromCurrentURL()).length !== 4) {
        raiseErrorModal(`Неверное количество параметров.`);
        return;
    }
    // Проверяем, может быть ученик уже учится по этой дисциплине
    const alreadyStudying = await getIsStudentOnDiscipline()
    if (alreadyStudying) {
        raiseErrorModal(`Ученик уже есть в группе по данной дисциплине, свяжитесь с менеджером и поругайтесь на него.`);
        return;
    } else if (alreadyStudying === null) return;

    // Подгружаем группы
    const resultContainerEl = document.querySelector('.result_container');
    const groupLoadingStatusContainerEl = document.querySelector('.group_loading_status_container');

    getAvailableFormingGroups().then(groups => {
        for (const group of groups) {
            const groupEl = createGroupEl(group)

            // Измените обработчик событий для groupEl
            groupEl.addEventListener('click', () => {
                const studentId = Client.getParamsFromCurrentURL()['student_id'];
                confirmationModal.show();

                const modalBodyEl = document.querySelector('.confirmation-modal-body');
                modalBodyEl.innerHTML = '';
                const groupPreview = createGroupEl(group);
                groupPreview.classList.add('pointer-events-none', 'fs-5');
                const submitQuestionText = document.createElement('p');
                submitQuestionText.className = 'text-center mb-0 mt-2 fs-5';
                submitQuestionText.innerHTML = 'Вы действительно хотите записаться в выбранную группу?';
                modalBodyEl.appendChild(groupPreview);
                modalBodyEl.appendChild(submitQuestionText);


                document.getElementById('confirmJoin').onclick = () => {
                    document.getElementById('confirmSpinner').classList.remove('d-none')
                    joinStudentToGroup(studentId, group);
                    document.getElementById('confirmJoin').setAttribute('disabled', 'true');
                };
            });


            resultContainerEl.appendChild(groupEl);
        }

        resultContainerEl.parentElement.classList.remove('d-none');
        groupLoadingStatusContainerEl.innerHTML = '';
        groupLoadingStatusContainerEl.className = '';
        const successEl = document.createElement('p');
        successEl.className = 'text-center fw-bold text-success fs-5 m-0';
        successEl.innerHTML = 'Готово! Найденные группы ниже.';
        groupLoadingStatusContainerEl.appendChild(successEl);
    });
}

await main();


