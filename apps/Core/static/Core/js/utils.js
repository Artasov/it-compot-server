export async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


export function copyInnerHtml(selector) {
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


