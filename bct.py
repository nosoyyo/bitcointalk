from time import time
import requests
from requests_toolbelt import MultipartEncoder
from bs4 import BeautifulSoup

from config import headers, headers4post, cookies


class Thread():

    def __init__(self, _id):
        print('{} [init] initializing...'.format(time()))
        self.__url = 'https://bitcointalk.org/index.php'
        print('{} [init] started grabbing main thread...'.format(time()))
        self.__resp = requests.get(
            self.__url+'?topic='+str(_id), headers=headers, cookies=cookies)
        if self.__resp.status_code is 200:
            print('{} [init] <Response [200]> main thread grabbed, now cooking soup.'.format(time()))
        else:
            return '[init] initialization failed.'
        self._id = str(_id)
        self.soup = BeautifulSoup(self.__resp.text, 'html5lib')
        self.title, self.n_replies = self.cook()
        self.post_url = self.__url+'?action=post2;start=0;topic=' + self._id
        return print('{} [init] successfully initialized.'.format(time()))

    def cook(self):

        print('{} [init] grabbing title...'.format(time()))
        title = self.soup.select('td#top_subject')[0].text.split(':')[
            1].split('\xa0')[0].strip()

        print('{} [init] grabbing n_replies...'.format(time()))
        for item in self.soup.select("a[href*='num_replies']")[0]['href'].split(';'):
            if 'num_replies' in item:
                n = item.split('=')[-1]
        return title, n

    def buildPayload(self, message, selfBuild=False):

        print('{} [post] building formdata payload...'.format(time()))

        def formDataEncode(_dict):
            bdry = '------WebKitFormBoundaryHVhSKUsjkv7MUqA9\n'
            item = ''
            for key in _dict:
                k, v = key, _dict[key]
                k, v = str(k), str(v) + '\n'
                item_0 = 'Content-Disposition: form-data; name="{}"\n\n'.format(
                    k)
                item = item + bdry + item_0 + v
            return item + bdry + '--'

        formdata = {}
        formdata['topic'] = self._id
        formdata['subject'] = 'RE:' + self.title
        formdata['icon'] = 'xx'
        formdata['message'] = message
        formdata['notify'] = '0'
        formdata['do_watch'] = '0'
        formdata['goback'] = '1'
        formdata['post'] = 'Post'
        formdata['num_replies'] = str(self.n_replies)
        formdata['seqnum'] = str(self.seqnum)
        formdata['sc'] = str(self.sc)
        if selfBuild:
            payload = formDataEncode(formdata)
        else:
            payload = MultipartEncoder(fields=formdata)
            print('{} [post] formdata payload encoded.'.format(time()))
        return payload

    def post(self, message):

        pre_post_url = self.__url+'?action=post;topic={};num_replies={}'.format(
            self._id, self.n_replies)
        print('{} [post] pre_post_url ready.'.format(time()))

        def getPrePost():
            print('{} [post] preparing for post...'.format(time()))
            resp = requests.get(pre_post_url,
                                headers=headers, cookies=cookies)
            if resp.status_code is 200:
                print(
                    '{} [bct] <Response [200]> preparation good.'.format(time()))
            else:
                return '{} [bct] {} preparation not good.'.format(time(), resp.status_code)
            soup = BeautifulSoup(resp.text, 'html5lib')
            self.seqnum = soup.select('input[name="seqnum"]')[0]['value']
            self.sc = soup.select('input[name="sc"]')[0]['value']
            print('{} [bct] seqnum:{}, sc: {}.'.format(
                time(), self.seqnum, self.sc))
        return

        payload = self.buildPayload(message)
        headers4post['referer'] = self.pre_post_url
        headers4post['Content-Type'] = payload.content_type
        print('{} [bct] posting...'.format(time()))
        resp = requests.post(self.post_url, data=payload,
                             headers=headers4post, cookies=cookies)
        if resp.status_code is 200:
            print('{} [bct] successfully post.'.format(time()))
        else:
            return '{} [bct] {} post failed.'.format(time(), resp.status_code)
        soup = BeautifulSoup(resp.text, 'html5lib')
        if soup.select('div#error_list'):
            error = soup.select('div#error_list')[0].text
            if 'while you were typing a new reply has been posted' in error:
                self.__init__(self._id)
        else:
            return soup
