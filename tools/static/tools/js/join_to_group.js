import Client from "../../../../static/Core/js/classes/Client.js";

async function getAvailableFormingGroups() {
    try {
        return await Client.sendGet(
            Client.getProtocolAndDomain() +
            '/api/v1/tools/get_forming_groups/',
            Client.getParamsFromCurrentURL()
        );
    } catch (error) {
        raiseErrorModal(`Ошибка получения групп, свяжитесь с менеджером и поругайтесь на него.`);
        return null;
    }
}

function raiseErrorModal(error) {
    // Установка текста ошибки в тело модального окна
    document.querySelector('.error-modal-body').textContent = error;

    // Инициализация и показ модального окна с помощью Bootstrap
    const errorModal = new bootstrap.Modal(document.getElementById('errorModal'), {
        keyboard: true
    });
    errorModal.show();
}

async function postJoinStudentToGroup(student_id, group_id) {
    try {
        return await Client.sendPost(
            Client.getProtocolAndDomain() +
            '/api/v1/tools/student_to_group/',
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
    const timeP = document.createElement('p');
    // Используем последний элемент расписания для даты и времени
    const schedule = group.ScheduleItems[group.ScheduleItems.length - 1];
    dateP.textContent = schedule.BeginDate;
    timeP.textContent = `${schedule.BeginTime} - ${schedule.EndTime}`;
    li.appendChild(dateP);
    li.appendChild(timeP);

    // Добавляем информацию о количестве учеников и вакансиях
    const frbDiv = document.createElement('div');
    frbDiv.className = "d-flex gap-2";
    const studentsSpan = document.createElement('span');
    studentsSpan.textContent = 'Учеников';
    const vacanciesSpan = document.createElement('span');
    vacanciesSpan.textContent = `${group.StudentsCount} / ${group.Vacancies}`;
    frbDiv.appendChild(studentsSpan);
    frbDiv.appendChild(vacanciesSpan);
    li.appendChild(frbDiv);

    // Добавляем информацию о преподавателе
    const teacherP = document.createElement('p');
    teacherP.textContent = `Педагог: ${schedule.Teacher}`;
    li.appendChild(teacherP);

    return li;
}

function joinStudentToGroup(student_id, group_id) {
    console.log('SENT')
    console.log(student_id)
    console.log(group_id)
    postJoinStudentToGroup(student_id, group_id).then(response => {
        console.log(response)
    })
}

const resultContainerEl = document.querySelector('.result_container');
const groupLoadingStatusContainerEl = document.querySelector('.group_loading_status_container');


getAvailableFormingGroups().then(groups => {
    console.log(groups);
    for (const group of groups) {
        const groupEl = createGroupEl(group)

        // Измените обработчик событий для groupEl
        groupEl.addEventListener('click', () => {
            const studentId = Client.getParamsFromCurrentURL()['student_id'];
            const groupId = group.Id;
            const confirmationModal = new bootstrap.Modal(document.getElementById('confirmationModal'), {
                keyboard: false
            });
            confirmationModal.show();

            const modalBodyEl = document.querySelector('.confirmation-modal-body');
            modalBodyEl.innerHTML = '';
            const groupPreview = createGroupEl(group);
            groupPreview.classList.remove('bg-primary');
            groupPreview.classList.add('bg-success');
            const submitQuestionText = document.createElement('p');
            submitQuestionText.className = 'text-center mb-0 mt-2 fs-5';
            submitQuestionText.innerHTML = 'Вы действительно хотите записаться в выбранную группу?';
            modalBodyEl.appendChild(groupPreview);
            modalBodyEl.appendChild(submitQuestionText);


            document.getElementById('confirmJoin').onclick = () => {
                joinStudentToGroup(studentId, groupId);
                confirmationModal.hide();
            };
        });


        resultContainerEl.appendChild(groupEl);
    }

    resultContainerEl.parentElement.classList.remove('d-none');
    groupLoadingStatusContainerEl.innerHTML = '';
    groupLoadingStatusContainerEl.className = '';
    const successEl = document.createElement('p');
    successEl.className = 'text-center fw-bold text-success fs-5 m-0';
    successEl.innerHTML = 'Ура! Найденные группы ниже :)';
    groupLoadingStatusContainerEl.appendChild(successEl);
});

