$(function () {
    $("#button").click(function () {
        $("#button").addClass("onclick");
        setTimeout(validate, 250)
    });
    function validate() {
        setTimeout(function () {
            $("#button").removeClass("onclick");
            $("#button").addClass("validate");
            setTimeout(callback, 450)
        }, 2250);
    }

    function callback() {
        setTimeout(function () {
            $("#button").removeClass("validate");
        }, 1250);
    }
});