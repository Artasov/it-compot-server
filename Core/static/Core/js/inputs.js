let form_inputs = document.querySelectorAll('.form__group > input');
for (let i = 0; i < form_inputs.length; i++) {
    if (form_inputs[i].value.length !== 0) {
        form_inputs[i].classList.add('form__field-filled');
    } else {
        form_inputs[i].classList.remove('form__field-filled');
    }
}
for (let i = 0; i < form_inputs.length; i++) {
    form_inputs[i].addEventListener('blur', function (e) {
        if (form_inputs[i].value.length !== 0) {
            form_inputs[i].classList.add('form__field-filled');
        } else {
            form_inputs[i].classList.remove('form__field-filled');
        }
    });
}