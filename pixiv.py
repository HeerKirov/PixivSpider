from core import Core
from notice import Notice
import re
from bs4 import BeautifulSoup


class Pixiv:
    urls = {
        "home": "https://www.pixiv.net/",
        "login": "https://accounts.pixiv.net/login?lang=zh",
        "illust": "https://www.pixiv.net/member_illust.php?mode=medium&illust_id=%s",
        "pximg": "https://i.pximg.net/img-original/img/%s/%s/%s/%s/%s/%s/%s_p%s.%s",
        "member": "https://www.pixiv.net/member_illust.php?id=%s&type=all&p=%s"
    }
    core = None
    info = None

    def __init__(self, core=None, notice=None):
        self.core = core if core is not None else Core()
        self.info = notice if notice is not None else Notice()

    def get_login_post_key(self):
        headers = {
            "referer": "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index",
            "origin": "https://accounts.pixiv.net",
        }
        login_page_response = self.core.get(url=self.urls["login"], headers=headers, rand_user_agent=False)
        if login_page_response is None:
            return None
        elif login_page_response.status_code == 200:
            text = login_page_response.text
            matched = re.search('"pixivAccount.postKey":"([\\w]*)"', text).groups()[0]
            return matched
        else:
            return None

    def login(self, username, password):
        post_key = self.get_login_post_key()
        if post_key is not None:
            data = {
                'pixiv_id': username,
                'password': password,
                'captcha': '',
                'g_recaptcha_response': '',
                'post_key': post_key,
                'source': 'pc',
                'ref': 'wwwtop_accounts_index',
                'return_to': self.urls['home']
            }
            headers = {
                "referer": "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index",
                "origin": "https://accounts.pixiv.net",
            }
            res = self.core.post(url=self.urls["login"], data=data, headers=headers, rand_user_agent=False)
            if res is None:
                self.info.error('登录失败。多次请求未得到结果。')
            elif res.status_code != 200:
                self.info.error('登录失败。登录请求失败。')
            else:
                self.info.log('[%s]登录成功。' % (username,))
        else:
            self.info.error('登录失败。postKey未找到。')

    def get_image_source(self, pid, count=None):
        res = self.core.get(url=self.urls['illust'] % (pid,), use_proxy=True)
        if res is None:
            self.info.error('[%s]图片下载出错。多次请求始终无法请求到图片信息。' % (pid,))
        elif res.status_code == 200:
            bs = BeautifulSoup(res.text, "html.parser")
            if bs is not None:
                try:
                    title = Pixiv.get_bs_by_re(bs, 'script', r'"illustTitle":"([^"]*)"')[0].encode('utf-8').decode('unicode-escape')
                    user_id = Pixiv.get_bs_by_re(bs, 'script', r'"authorId":"([0-9]*)"')[0]
                    user = Pixiv.get_bs_by_re(bs, 'script', r'"userId":"%s","name":"([^"]*)"' % (user_id,))[0].encode('utf-8').decode('unicode-escape')

                    original_src = Pixiv.get_bs_by_re(bs, 'script', r'"original":"([^"]*)"')[0]
                except Exception:
                    self.info.error('[%s]图片下载出错。无法解析图片相关信息。' % (pid,))
                    return None
                self.info.log('[%s]图片开始下载。' % (pid,))
                res_img_content = []
                index = 0
                page_looping = True
                while page_looping and (count is None or index < count):
                    use_count = 3
                    img_url, pg_index, extension, ugoira = self.format_original(original_src, index)
                    if img_url is None:
                        self.info.error('[%s]图片URL解析失败。' % (pid,))
                        break
                    if ugoira is True:
                        self.info.error('[%s]该图片为动图。目前不支持处理动图。' % (pid,))
                        break
                    res_img = self.core.get(url=img_url, headers={'Referer': self.urls["illust"] % (pid,)})
                    while use_count > 0:
                        if res_img is None:
                            use_count -= 1
                        elif res_img.status_code == 404:
                            page_looping = False
                            break
                        elif res_img.status_code == 200:
                            res_img_content.append((res_img.content, pg_index, extension))
                            break
                        else:
                            use_count -= 1
                    if use_count == 0:
                        self.info.error('[%s]图片下载出错。第%s张图片始终无法正确请求。' % (pid, index))
                    elif page_looping:
                        self.info.log('[%s]第%s张下载完成。' % (pid, index))
                    index += 1
                return {
                    'content': res_img_content,
                    'title': title,
                    'pid': pid,
                    'user_id': user_id,
                    'user': user
                }
            else:
                self.info.error('[%s]图片下载出错。无法解析内容。' % (pid,))
                return None
        else:
            self.info.error('[%s]图片下载出错。无法正确请求内容。' % (pid,))
            return None

    def format_original(self, src, index=None):
        matched = re.search(r'img\\/([0-9]*)\\/([0-9]*)\\/([0-9]*)\\/([0-9]*)\\/([0-9]*)\\/([0-9]*)\\/([0-9]*)_p([0-9]*).(\w*)', src)
        if matched is not None:
            res = matched.groups()
            return (
                self.urls['pximg'] % (res[0], res[1], res[2], res[3], res[4], res[5], res[6], index if index is not None else res[7], res[8]),
                index if index is not None else res[7],
                res[8],
                False
            )
        else:
            matched = re.search(r'img\\/([0-9]*)\\/([0-9]*)\\/([0-9]*)\\/([0-9]*)\\/([0-9]*)\\/([0-9]*)\\/([0-9]*)_ugoira([0-9]*).(\w*)', src)
            if matched is not None:
                res = matched.groups()
                return (
                    # TODO 修改此URL
                    self.urls['pximg'] % (res[0], res[1], res[2], res[3], res[4], res[5], res[6], index if index is not None else res[7], res[8]),
                    index if index is not None else res[7],
                    res[8],
                    True
                )
            else:
                self.info.error('无法解析该图片的URL。')
                return None, None, None, False

    @staticmethod
    def get_bs_by_re(bs, content, reg):
        regex = re.compile(reg)
        txt = bs.find(content, text=regex)
        if txt is not None:
            return regex.search(txt.text).groups()
        else:
            return None

    def get_member_image_list(self, uid, page=None, max_count=None):
        if page is not None:
            res = self.core.get(url=self.urls['member'] % (uid, page), use_proxy=True)
            if res is None:
                self.info.error('用户获取出错。多次请求始终无法获取页面信息。')
                return None
            elif res.status_code == 200:
                bs = BeautifulSoup(res.text, 'html.parser')
                if bs is not None:
                    pids = []
                    try:
                        no_item = bs.find('li', attrs={'class', '_no-item'})
                        if no_item is not None:
                            return []
                        items = bs.find('ul', attrs={'class', '_image-items'}).find_all('li')
                        for i in items:
                            pid = i.find('img')['data-id']
                            title = i.find('h1', attrs={'class', 'title'})['title']
                            pids.append((pid, title))
                    except Exception:
                        self.info.error('用户获取出错。无法正确解析作品列表。页码为%s。' % (page,))
                        return None
                    return pids
                else:
                    self.info.error('用户获取出错。无法解析内容列表。页码为%s。' % (page,))
                    return None
            elif res.status_code == 404:
                return []
            else:
                self.info.error('用户获取出错。无法正确请求内容。页码为%s。' % (page,))
                return None
        else:
            ret = []
            p = 1
            while True:
                current = self.get_member_image_list(uid, p)
                if current is not None:
                    if len(current) > 0:
                        ret += current
                        p += 1
                        if max_count is not None and len(ret) >= max_count:
                            break
                    else:
                        break
                else:
                    return None
            return ret

    @staticmethod
    def download_to(content, uri):
        with open(uri, 'wb') as f:
            f.write(content)

