import re
import math
import json
import time
import os.path
import requests
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool

threads = 10

def saveCookies(cookies, xf_id, xf_session, xf_tfa_trust, xf_token):
    with open('cookies', 'w') as f:
        data = {'cookies': cookies,
                'xf_id': xf_id,
                'xf_session':xf_session,
                'xf_tfa_trust':xf_tfa_trust,
                'xf_token':xf_token}
        json.dump(data, f)

def loadCookies():
    if os.path.exists('cookies'):
        f = open('cookies', 'r')
        return json.load(f)
    else:
        return False


class Client:
    def __init__(self, email='', password=''):
        self.email = email
        self.password = password
        self.cookies = {}
        self.xf_id = ''
        self.xf_session = ''
        self.xf_tfa_trust = ''
        self.xf_token = ''
        self.converts = 0


    def sendCode(self):
        resp = requests.get('https://lolzteam.net/').text
        self.xf_id = re.search(
            r'href\|max\|([\w]{32})\|navigator',
            resp).group(1)
        self.xf_session = requests.get(
            'https://lolzteam.net/',
            cookies={
                'xf_id': self.xf_id}).cookies.get_dict()['xf_session']
        r = requests.post(
            'https://lolzteam.net/login/login',
            cookies={
                'xf_id': self.xf_id,
                'xf_session': self.xf_session},
            data={
                'login': self.email,
                'password': self.password,
                'remember': '1',
                'stopfuckingbrute1337': '1',
                'cookie_check': '1',
                '_xfToken': '',
                'redirect': 'https%3A%2F%2Flolzteam.net%2F'},
            headers={
                'Referer': 'https://lolzteam.net/login/login',
                'Origin': 'https://lolzteam.net/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/437.36 (KHTML, like Gecko)'})
        if 'ctrl_telegram_code' in r.text:
            return 'telegram'
        elif 'ctrl_email_code' in r.text:
            return 'email'
        else:
            return False


    def auth(self, code, provider):
        r = requests.post(
            'https://lolzteam.net/login/two-step',
            cookies={
                'xf_id': self.xf_id,
                'xf_session': self.xf_session},
            data={
                "code": code,
                "trust": "1",
                "provider": provider,
                "_xfConfirm": "1",
                "_xfToken": "",
                "remember": [
                    "1",
                    "1"],
                "redirect": "https://lolzteam.net/",
                "save": "Подтвердить",
                "_xfRequestUri": "/login/two-step?redirect",
                "_xfNoRedirect": "1",
                "_xfResponseType": "json"},
            headers={
                'Referer': 'https://lolzteam.net/login/two-step?redirect',
                'Origin': 'https://lolzteam.net/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/437.36 (KHTML, like Gecko)'})
        if '_redirectStatus' in r.json().keys():
            self.converts = int(r.json()['_visitor_conversationsUnread'])
            self.cookies = r.cookies.get_dict()
            self.cookies['xf_id'] = self.xf_id
            self.xf_session = self.cookies['xf_session']
            r = requests.get('https://lolzteam.net/', cookies=self.cookies)
            self.xf_token = re.search(
                r'name="_xfToken" value="([\w,\d]+)"',
                r.text).group(1)
            self.xf_tfa_trust = self.cookies['xf_tfa_trust']
            return True
        else:
            return False


    def getConversations(self):
        cycles = math.ceil(self.converts / 30)
        all_ids = []
        for i in range(1, cycles + 1):
            r = requests.post(
                'https://lolzteam.net/conversations/unread-conversations',
                data={
                    'page': str(i),
                    '_xfRequestUri': '/conversations/',
                    '_xfNoRedirect': '1',
                    '_xfToken': self.xf_token,
                    '_xfResponseType': 'json'},
                headers={
                    'Referer': 'https://lolzteam.net/',
                    'Origin': 'https://lolzteam.net/',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/437.36 (KHTML, like Gecko)'},
                cookies=self.cookies).json()
            soup = BeautifulSoup(r['templateHtml'], 'html.parser')
            for d in soup.find_all('li'):
                all_ids.append(d.get('id').replace('conversation-', ''))
        return all_ids


    def read(self, id):
        r = requests.post(
            f'https://lolzteam.net/conversations/{id}/',
            headers={
                'Referer': 'https://lolzteam.net/',
                'Origin': 'https://lolzteam.net/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/437.36 (KHTML, like Gecko)'},
            data={
                'fromList': 'true',
                '_xfRequestUri': f'/conversations/{id}/',
                '_xfNoRedirect': '1',
                '_xfToken': self.xf_token,
                '_xfResponseType': 'json'},
            cookies=self.cookies,
            stream=True)
        if 'conversationRecipientUsername' in r.text:
            return True
        else:
            return False


    def threads(self, func, ids):
        pool = Pool(threads)
        for _ in pool.imap_unordered(func, ids):
            pass
    

    def getContests(self):
        ids = []
        for i in range(1,4):
            html = requests.get(f'https://lolzteam.net/forums/contests/page-{str(i)}',  headers={
                'Referer': 'https://lolzteam.net/',
                'Origin': 'https://lolzteam.net/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/437.36 (KHTML, like Gecko)'},
                cookies=self.cookies).text
            lst = re.findall(r'href="threads/(\d{7,10})/"', html)
            ids += lst
        return ids
    

    def joinContest(self, id):
        r = requests.post(
            f'https://lolzteam.net/threads/{id}/participate', 
            params={'_xfToken': self.xf_token},
            data={
                "_xfRequestUri": f"/threads/{id}/",
                "_xfNoRedirect": "1",
                "_xfToken": self.xf_token,
                "_xfResponseType": "json"}, cookies=self.cookies)
        if '"_redirectStatus":"ok"' in r.text:
            return True
        elif '\\u0412\\u044b \\u0443\\u0436\\u0435' in r.text:
            return 'alredy'
        else:
            return False
            


def main():
    if os.path.exists('cookies'):
        print('Найден авторизационный файл')
        auth_data = loadCookies()
        cl = Client()
        cl.cookies = auth_data['cookies']
        cl.xf_id = auth_data['xf_id']
        cl.xf_session = auth_data['xf_session']
        cl.xf_tfa_trust = auth_data['xf_tfa_trust']
        cl.xf_token = auth_data['xf_token']
    else:
        email = input('Почта: ')
        password = input('Пароль: ')
        cl = Client(email, password)
        while True:
            r = cl.sendCode()
            if r is False:
                print('Ошибка. Попробуй снова')
            else:
                while True:
                    code = input('Код: ')
                    if cl.auth(code, r) is False:
                        print('Неверный код')
                    else:
                        print('Успешный вход')
                        saveCookies(cl.cookies, cl.xf_id, cl.xf_session, cl.xf_tfa_trust, cl.xf_token)
                        print('Данные авторизации сохранены в файл cookies')
                        break
                break
    while True:
        what = str(input('''1 - Очистка непрочитанных сообщений
2 - Автовход во все розыгрыши
3 - Выход
-> '''))
        if what == '1':
            print('------------------\nЗагрузка диалогов...')
            conv = cl.getConversations()
            print(f'Загружено {cl.converts} диалогов')
            print('Начинаю читать...')
            cl.threads(cl.read, conv)
            print('Чтение завершено\n------------------')
        elif what == '2':
            print('------------------\nЗагрузка розыгрышей...')
            conv = cl.getContests()
            print(f'Загружено {len(conv)} розыгрышей')
            print('Вступаю...')
            cl.threads(cl.joinContest, conv)
            print('Успешно завершено\n------------------')
        elif what == '3':
            break
        else:
            print('Ошибка')



if __name__ == '__main__':
    main()
