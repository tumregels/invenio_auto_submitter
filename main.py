import argparse
import collections
import csv
import os
import textwrap
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

Preprint = collections.namedtuple('Preprint', [
    'ReportNumbers',  # 'FileName','RN','TRN',
    'Title',
    'Authors',
    'Abstract',
    'Pages',
    'Language',
    'PublDate',  # 'Publ Year'
    'KeyPhrases',  # 'Descriptors',
    'Notes',  # 'Corporate Author', 'Issue', 'Volume', 'Original Title', 'Physical Description'
    'FilePath'
])


def prepare_field(row, list_of_fild_names):
    lines_of_text = []
    for name in list_of_fild_names:
        if row[name] != 'NULL':
            s = '{}: {}. '.format(name, row[name].strip().strip('.'))
            lines_of_text.append(s)
    return ''.join(lines_of_text).strip()


def splitter(val):
    return '\r\n'.join([item.strip().strip('.') for item in val.split(';')])


def get_data():
    preprints = []
    with open('metadata.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row['FilePath'] = os.path.join(os.getcwd(), 'preprints', row['FileName'] + '.pdf')
            if os.path.exists(row['FilePath']):
                preprints.append(row)
            else:
                print('File {} does not exist'.format(row['FilePath']))

    return preprints


def prepare_final_preprints(data):
    preprints = []

    for row in data:
        preprint = Preprint(
            ReportNumbers=prepare_field(row, ['FileName', 'RN', 'TRN']),
            Title=row['Title'].strip().strip('.') if row['Title'] != 'NULL' else row['Title'],
            Authors=splitter(row['Authors']) if row['Authors'] != 'NULL' else row['Authors'],
            Abstract=row['Abstract'],
            Pages=row['Pages'].split()[0].strip() if row['Pages'] != 'NULL' else row['Pages'],
            Language='eng' if row['Language'] == 'English' else 'rus',
            PublDate='01/01/{}'.format(
                row['Publ Year'].split('.')[0] if row['Publ Year'] != 'NULL' else row['Publ Year']),
            KeyPhrases=splitter(row['Descriptors']) if row['Descriptors'] != 'NULL' else row['Descriptors'],
            Notes=prepare_field(row,
                                ['Corporate Author', 'Original Title', 'Physical Description', 'Issue', 'Volume', ]),
            FilePath=row['FilePath']
        )
        preprints.append(preprint)

    return preprints


def preview(preprint, line_number):
    print('\r\n{:#^80}\r\n'.format(' Preprint N {} '.format(line_number)))
    for name in preprint._fields:
        print('{:-^80}'.format(name))
        print(textwrap.fill(getattr(preprint, name), 80))


def find_by_xpath(locator):
    element = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, locator))
    )
    return element


def login(username, password):
    browser.get("http://inveniodomain.com/youraccount/login")
    browser.find_element_by_xpath("//input[@id='p_un']").send_keys(username)
    browser.find_element_by_xpath("//input[@id='p_pw']").send_keys(password)
    browser.find_element_by_xpath("//input[@value='login']").click()


def choose_preprint():
    browser.get('http://inveniodomain.com/submit?ln=en&doctype=DEMOART')
    find_by_xpath(".//input[@id='comboPREPRINT' and @value='PREPRINT']").click()
    find_by_xpath(".//input[@class='adminbutton' and @value='Submit New Record']").click()


def fill_preprint(p):
    find_by_xpath('//tr/td/textarea[@name="DEMOART_REP"]').send_keys(p.ReportNumbers)
    find_by_xpath('//tr/td/textarea[@name="DEMOART_TITLE"]').send_keys(p.Title) if p.Title != 'NULL' else 'Skip'
    find_by_xpath('//tr/td/textarea[@name="DEMOART_AU"]').send_keys(p.Authors) if p.Authors != 'NULL' else 'Skip'
    find_by_xpath('//tr/td/textarea[@name="DEMOART_ABS"]').send_keys(p.Abstract) if p.Abstract != 'NULL' else 'Skip'
    find_by_xpath("//input[@name='DEMOART_NUMP']").send_keys(p.Pages) if p.Pages != 'NULL' else 'Skip'
    find_by_xpath("//select[@name='DEMOART_LANG']/option[@value='{}']".format(p.Language)).click()
    find_by_xpath("//input[@name='DEMOART_DATE']").send_keys(p.PublDate) if p.PublDate != 'NULL' else 'Skip'
    find_by_xpath('//tr/td/textarea[@name="DEMOART_KW"]').send_keys(p.KeyPhrases) if p.KeyPhrases != 'NULL' else 'Skip'
    find_by_xpath('//tr/td/textarea[@name="DEMOART_NOTE"]').send_keys(p.Notes)

    # upload file
    find_by_xpath("//input[@value='Add new file']").click()
    find_by_xpath("//input[@id='balloonReviseFileInput']").send_keys(p.FilePath)
    find_by_xpath("//input[@id='bibdocfilemanagedocfileuploadbutton']").click()

    time.sleep(2.0)


def submit_preprint():
    find_by_xpath("//input[@value='Finish Submission' and @class='adminbutton']").click()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', help='invenio username')
    parser.add_argument('--password', help='invenio password')
    args = parser.parse_args()

    data = get_data()
    preprints = prepare_final_preprints(data)

    browser = webdriver.Firefox()
    browser.set_window_size(1000, 1000)  # Resize the window to the screen width/height

    preprints = preprints
    login(args.username, args.password)
    for i, preprint in enumerate(preprints, start=1):
        choose_preprint()
        preview(preprint, i)
        fill_preprint(preprint)
        submit_preprint()
        time.sleep(1.0)
    browser.quit()
