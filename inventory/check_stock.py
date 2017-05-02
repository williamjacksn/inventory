import email.message
import json
import logging
import lxml.html
import os
import requests
import smtplib
import sys

log = logging.getLogger(__name__)


def notify(change_list):
    log.info('Sending notification email to {}'.format(os.environ.get('NOTIFICATION_TO')))
    msg = email.message.EmailMessage()
    msg['Subject'] = 'Stock alert'
    msg['From'] = os.environ.get('SMTP_USER')
    msg['To'] = os.environ.get('NOTIFICATION_TO')
    msg.set_content('''Hello,

The following items recently changed status:

{}

(This is an automated message.)
'''.format('\n'.join(change_list)))
    with smtplib.SMTP_SSL(host=os.environ.get('SMTP_HOST')) as s:
        s.login(user=os.environ.get('SMTP_USER'), password=os.environ.get('SMTP_PASSWORD'))
        s.send_message(msg)


def main():
    logging.basicConfig(level='DEBUG', stream=sys.stdout, format='%(levelname)s | %(message)s')

    log.info(f"Attempting to read data from {os.environ.get('STOCK_JSON')}")
    change_list = []

    try:
        with open(os.environ.get('STOCK_JSON')) as f:
            stock_current = json.load(f)
    except FileNotFoundError:
        stock_current = {}

    s = requests.session()

    login_data = f"{{Dist_ID:'{os.environ.get('USERNAME')}',Dist_Pass:'{os.environ.get('PASSWORD')}'}}"
    login_headers = {'Content-Type': 'application/json; charset=utf-8'}
    s.post(os.environ.get('LOGIN_URL'), data=login_data, headers=login_headers)

    stock = s.get(os.environ.get('STOCK_URL'))
    stock_html = lxml.html.document_fromstring(stock.text)
    for row in stock_html.xpath('//tr'):
        cells = row.xpath('td')
        if len(cells) < 5:
            continue
        item_num = cells[1].xpath('span/font')
        if not item_num:
            continue
        item_num_text = item_num[0].text
        desc = cells[2].xpath('a/font')
        if not desc:
            continue
        desc_text = desc[0].text
        price = cells[3].xpath('span/font')
        if not price:
            continue
        price_text = price[0].text
        comments = cells[4].xpath('span/b/font')
        if not comments:
            continue
        comments_text = comments[0].text
        other_comments_text = comments[1].text
        if other_comments_text is None:
            other_comments_text = ''
        other_comments_text = other_comments_text.strip()
        new = {'description': desc_text, 'price': price_text, 'comments': comments_text,
               'other_comments': other_comments_text}
        existing = stock_current.get(item_num_text)
        if existing is None:
            log.info(f'{item_num_text}: adding a new item')
            stock_current[item_num_text] = new
            continue
        if existing == new:
            log.info(f'{item_num_text}: no change')
            continue
        changed_fields = []
        for field in new:
            if existing[field] == new[field]:
                continue
            changed_fields.append(field)
        change_msg = '; '.join([f'{f} changed from {existing[f]} to {new[f]}' for f in changed_fields])
        log.info(f'{item_num_text}: {change_msg}')
        change_list.append(f"{existing['description']}: {change_msg}")
        stock_current[item_num_text] = new

    with open(os.environ.get('STOCK_JSON'), 'w') as f:
        json.dump(stock_current, f, sort_keys=True, indent=2)

    if change_list:
        notify(change_list)

if __name__ == '__main__':
    main()
