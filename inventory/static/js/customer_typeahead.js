let customers_json_url = $('#customers_json_url').attr('href');

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
