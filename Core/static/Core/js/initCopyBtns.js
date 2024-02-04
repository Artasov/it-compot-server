import {copyInnerHtml} from "../../../static/Core/js/utils.js";

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