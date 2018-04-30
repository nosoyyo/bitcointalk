from time import time
import requests
from requests_toolbelt import MultipartEncoder
from bs4 import BeautifulSoup

from config import headers, headers4post, cookies


time_limit = 0


def now():
    now = round(time())
    return now


class Thread():

    def __init__(self, _id, protocol='https'):
        print('{} [init] initializing...'.format(time()))
        self.__url = protocol+'://bitcointalk.org/index.php'
        print('{} [init] started grabbing main thread...'.format(time()))
        self.__resp = requests.get(
            self.__url+'?topic='+str(_id), headers=headers, cookies=cookies)
        if self.__resp.status_code is 200:
            print(
                '{} [init] <Response [200]> main thread grabbed, now cooking soup.'.format(time()))
        else:
            return '[init] initialization failed.'
        self._id = str(_id)
        self.soup = BeautifulSoup(self.__resp.text, 'html5lib')
        if 'Reply' in self.soup.select('td[class="maintab_back"]')[-1].a:
            self.repliable = True
        else:
            self.repliable = False
        self.title, self.n_replies = self.cook()
        self.post_url = self.__url+'?action=post2;start=0;topic=' + self._id

        ##########################
        # ATTENTION! GLOBAL HERE #
        ##########################
        global time_limit
        if time_limit:
            last_post = 'Last post was {} secs ago.'.format(now() - time_limit)
        else:
            last_post = None
        if last_post:
            return print('{} [init] successfully initialized.'.format(time())) + last_post
        else:
            return print('{} [init] successfully initialized.'.format(time()))

    def cook(self):

        print('{} [init] grabbing title...'.format(time()))
        title = self.soup.select('meta[name="description"]')[0]['content']

        print('{} [init] grabbing n_replies...'.format(time()))
        for item in self.soup.select("a[href*='num_replies']")[0]['href'].split(';'):
            if 'num_replies' in item:
                n = item.split('=')[-1]
        return title, n

    def buildPayload(self, message):

        print('{} [post] building formdata payload...'.format(time()))

        formdata = {}
        formdata['topic'] = self._id
        formdata['subject'] = 'RE:' + \
            self.title.encode('unicode-escape').decode('latin-1')
        formdata['icon'] = 'xx'
        formdata['message'] = message.encode(
            'unicode-escape').decode('latin-1')
        formdata['notify'] = '0'
        formdata['do_watch'] = '0'
        formdata['goback'] = '1'
        formdata['post'] = 'Post'
        formdata['num_replies'] = str(self.n_replies)
        formdata['seqnum'] = str(self.seqnum)
        formdata['sc'] = str(self.sc)

        payload = MultipartEncoder(fields=formdata)
        print('{} [post] formdata payload encoded.'.format(time()))
        return payload

    def post(self, message):
        ##########################
        # ATTENTION! GLOBAL HERE #
        ##########################
        global time_limit

        if not self.repliable:
            return 'This thread is not repliable.'
        elif now() - time_limit < 360:
            return 'Wait another {} secs.'.format(360-(now()-time_limit))

        pre_post_url = self.__url+'?action=post;topic={};num_replies={}'.format(
            self._id, self.n_replies)
        print('{} [post] pre_post_url ready, moving to getPrePost()'.format(time()))

        def getPrePost():
            print('{} [post] preparing for post...'.format(time()))
            pre_resp = requests.get(pre_post_url,
                                    headers=headers, cookies=cookies)
            if pre_resp.status_code is 200:
                print(
                    '{} [post] <Response [200]> preparation good.'.format(time()))
            else:
                return '{} [post] {} preparation not good.'.format(time(), pre_resp.status_code)
            pre_soup = BeautifulSoup(pre_resp.text, 'html5lib')
            self.seqnum = pre_soup.select('input[name="seqnum"]')[0]['value']
            self.sc = pre_soup.select('input[name="sc"]')[0]['value']
            print('{} [post] seqnum:{}, sc: {}.'.format(
                time(), self.seqnum, self.sc))

        getPrePost()

        print('{} [post] getPrePost() ready, building payload...'.format(time()))
        payload = self.buildPayload(message)
        print('{} [post] buildPayload() ready.'.format(time()))
        headers4post['referer'] = pre_post_url
        headers4post['Content-Type'] = payload.content_type
        print('{} [post] posting...'.format(time()))
        after_resp = requests.post(self.post_url, data=payload,
                                   headers=headers4post, cookies=cookies)
        if after_resp.status_code is 200:
            print('{} [post] successfully post.'.format(time()))
        else:
            return '{} [post] {} post failed.'.format(time(), after_resp.status_code)
        after_soup = BeautifulSoup(after_resp.text, 'html5lib')
        if after_soup.select('div#error_list'):
            error = after_soup.select('div#error_list')[0].text
            if 'while you were typing a new reply has been posted' in error:
                self.__init__(self._id)
                return 'you can try again instantly.'
            elif 'Please try again later' in error:
                return 'you can try again after {} seconds'.format(now() - time_limit)
        else:
            time_limit = now()
            return after_resp
