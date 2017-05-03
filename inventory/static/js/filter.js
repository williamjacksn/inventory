$('#filter-input').keyup($.debounce(250, function (event) {
    if (event.keyCode === 27) {
        // [Esc] was pressed
        $(this).val('');
    }
    let query = $(this).val().toLowerCase();
    let items = $('.filter-candidate');
    if (query === '') {
        items.show();
    } else {
        items.each(function () {
            if (this.getAttribute('data-filter-value').includes(query)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        })
    }
}));
