let inventory_json_url = $('#inventory_json_url').attr('href');
let customers_json_url = $('#customers_json_url').attr('href');

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
    a.setAttribute('href', '#');
    let avail = sg['qty_received'] - sg['qty_sold'] - sg['qty_committed'];
    let text = sg.item_name + ' (' + avail + ' available to sell)';
    a.appendChild(document.createTextNode(text));
    return a;
}

$('#input_item_name').typeahead({
    classNames: {
        dataset: 'list-group',
        suggestion: 'list-group-item'
    },
    highlight: true
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

let customer_source = new Bloodhound({
    datumTokenizer: Bloodhound.tokenizers.whitespace,
    prefetch: {
        cache: false,
        url: customers_json_url
    },
    queryTokenizer: Bloodhound.tokenizers.whitespace
});

function sg_template_customer(sg) {
    let a = document.createElement('a');
    a.setAttribute('href', '#');
    a.appendChild(document.createTextNode(sg));
    return a;
}

$('#sale_customer').typeahead({
    classNames: {
        dataset: 'list-group',
        suggestion: 'list-group-item'
    },
    highlight: true
}, {
    limit: 10,
    name: 'customer_source',
    source: customer_source,
    templates: {
        suggestion: sg_template_customer
    }
});
