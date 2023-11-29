async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function initCopyBtns() {
    const copyBtns = document.querySelectorAll('.btn-copy');
    for (const copyBtn of copyBtns) {
        copyBtn.addEventListener('click', () => {
            const selectorForCopyInner = copyBtn.getAttribute('data-selector-for-copy-inner');
            copyInnerHtml(selectorForCopyInner)
        })
    }
}
initCopyBtns();
function copyInnerHtml(selector) {
    const element = document.querySelector(selector);
    const content = element.innerHTML;

    navigator.clipboard.writeText(content)
        .then(() => {
            console.log("Содержимое скопировано!");
        })
        .catch(err => {
            console.error("Ошибка при копировании: ", err);
        });
}

function getCookie(name) {
    const value = "; " + document.cookie;
    const parts = value.split("; " + name + "=");
    if (parts.length === 2) return parts.pop().split(";").shift();
}

function set_input_value_by_id(input_id, value) {
    document.getElementById(input_id).value = value;
}

const themeChangeBtns = document.getElementsByClassName('theme-change-btn');
for (let i = 0; i < themeChangeBtns.length; i++) {
    themeChangeBtns[i].addEventListener('click', function () {
        next_theme();
    })
}

window.onload = function (e) {
    document.getElementById('loading_spinner_block').remove();
    document.getElementById('content').classList.remove('d-none');
    let telegram_auth = document.getElementById('telegram-login-xlartas_web_bot')
    if (telegram_auth) {
        telegram_auth.classList.add('telegram-auth');
    }
}

function sendGetRequest(url, callback) {
    let xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            let response = xhr.responseText;
            callback(null, response);
        } else if (xhr.readyState === 4) {
            callback(new Error('Request failed'));
        }
    };
    xhr.open('GET', url, true);
    xhr.send();
}