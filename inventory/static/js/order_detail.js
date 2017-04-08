let inventory_json_url = $('#inventory_json_url').attr('href');

let item_name_source = new Bloodhound({
    datumTokenizer: function (d) { return Bloodhound.tokenizers.whitespace(d.item_name); },
    identify: function (d) { return d.item_name; },
    prefetch: {
        cache: false,
        url: inventory_json_url
    },
    queryTokenizer: Bloodhound.tokenizers.whitespace
});

function sg_template_item_name(sg) {
    let a = document.createElement('a');
    a.setAttribute('role', 'button');
    let p = document.createElement('p');
    a.appendChild(p);
    p.appendChild(document.createTextNode(sg.item_name.toString()));
    return a;
}

$('#input_item_name').typeahead({
    classNames: {
        dataset: 'list-group',
        menu: 'panel panel-default',
        suggestion: 'list-group-item'
    }
}, {
    display: 'item_name',
    limit: 10,
    name: 'item_name_source',
    source: item_name_source,
    templates: {
        suggestion: sg_template_item_name
    }
}).on('typeahead:select', function (e, sg) {
    let f = e.target.form;
    f.item_category.value = sg.item_category;
});

let item_category_source = new Bloodhound({
    datumTokenizer: function (d) { return Bloodhound.tokenizers.whitespace(d.item_category); },
    identify: function (d) { return d.item_category; },
    prefetch: {
        cache: false,
        url: inventory_json_url
    },
    queryTokenizer: Bloodhound.tokenizers.whitespace
});

function sg_template_item_category(sg) {
    let a = document.createElement('a');
    a.setAttribute('role', 'button');
    let p = document.createElement('p');
    a.appendChild(p);
    p.appendChild(document.createTextNode(sg.item_category.toString()));
    return a;
}

$('#input_item_category').typeahead({
    classNames: {
        dataset: 'list-group',
        menu: 'panel panel-default',
        suggestion: 'list-group-item'
    }
}, {
    display: 'item_category',
    limit: 10,
    name: 'item_category_source',
    source: item_category_source,
    templates: {
        suggestion: sg_template_item_category
    }
});
