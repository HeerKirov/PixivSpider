from pixiv import Pixiv
from core import Core
from notice import Notice, OutputToFile
import json
import re
import os

help_text = """为了使用自动化下载，你应当配置一个conf.json文件。
调用$ python app.py conf.json来启用这个配置。
配置应当包括以下内容：
{
    account: {
        username: <string> 你用来模拟登录的Pixiv 用户名。
        password: <string> 此账户的密码。
    }
    proxy: <bool> 是否启用随机代理。默认是启用的。
    log: <filepath> 日志的输出文件位置。默认值为null，这会将日志打印到屏幕。
    content: [
        {...} 需要下载的配置块。可以列出多个配置块。
    ]
}
配置块应当包裹在一个JSON Object内。目前的配置块有2种可用的写法：
1. 基于Pixiv ID进行批量下载。
{
    pid: <array|string|int> 要批量下载的Pixiv ID或其列表。
                            语法比较宽松。可以写 
                                pid: 12345678
                                pid: "12345678"
                                pid: [12345678, 23456789]
                            这样的语法。
                            此外，还可以写"12345678-12345690"这样的语法，指定一连串的Pixiv ID。
}
2. 基于画师的Member ID进行批量下载。
{
    uid: <array|string|int> 要批量下载的画师的ID或其列表。
                            语法比较宽松。可以写
                                uid: 12345678
                                uid: "12345678"
                                uid: [12345678, 23456789]
                            这样的语法。
                            此外，还可以写"12345678[10]"或"12345678[2-20]"这样的语法，指定下载该画师的哪些作品。
}
除了上面的特有配置之外，还有所有的配置块都可以写的通用配置。
{
    enabled: <bool> 可用。默认是可用的，可以临时设为不可用，起到注释的作用。
    replace: <bool> 覆盖。重复下载同名文件时，覆盖之前的文件。默认是不覆盖的。
    save: <file_expression> 单文件存储路径。Pixiv ID下只有一张画时使用这个路径。必须指定。
    multi_save: <file_expression> 多文件存储路径。有多张画时使用此路径。
                                  可以不指定，但是会使下载器只下载第1张，并采用save路径。
}
有关save路径的写法，规则如下：
    * 可以使用绝对路径或相对路径。
    * 路径分隔符使用‘/’。
    * 使用{prop}的语法，在路径中插入关键值。可以插入的关键值包括：
            1. {title} 作品标题
            2. {pid} Pixiv ID
            3. {user} 作者用户名
            4. {uid} 作者的Member ID。
            5. {index} 仅multi_save中可用，表示画的索引值。
    * 文件路径不应当带扩展名，扩展名会由下载器自动补全。
"""


class Configure:
    conf = None
    pixiv = None
    notice = None
    core = None

    def __init__(self, conf):
        self.conf = conf
        if conf is None:
            raise Exception("Conf缺失。")
        if isinstance(conf, str):
            try:
                self.conf = json.loads(conf)
            except Exception:
                raise Exception("Conf不是合法的JSON结构。")
        self.initialize_notice()
        self.initialize_core()
        self.initialize_pixiv()

    def initialize_notice(self):
        log_file = self.conf.get("log", None)
        if log_file is not None:
            log_notice = OutputToFile(log_file)
            self.notice = Notice(log_notice, log_notice)
        else:
            self.notice = Notice()

    def initialize_core(self):
        proxy = self.conf.get("proxy", True) is True
        self.core = Core(use_proxy=proxy)

    def initialize_pixiv(self):
        self.pixiv = Pixiv(core=self.core, notice=self.notice)
        if "account" in self.conf:
            username = self.conf["account"].get("username", None)
            password = self.conf["account"].get("password", None)
            if username is None:
                raise Exception("Conf JSON缺失结构'account.username'。")
            if password is None:
                raise Exception("Conf JSON缺失结构'account.password'。")
            self.pixiv.login(username, password)
        else:
            raise Exception("Conf JSON缺失结构'account'。")

    def run(self):
        content = self.conf.get("content", [])
        for c in content:
            if c.get("enabled", True):
                if "save" not in c:
                    raise Exception("无法找到启动配置的存储路径配置(save)。")
                if "uid" in c:
                    self.run_uid(c)
                elif "pid" in c:
                    self.run_pid(c)
                else:
                    raise Exception("无法找到启动配置的特征码(pid/uid/etc.)。")

    def run_uid(self, content):
        uids = content["uid"]
        replace = content.get("replace", False)
        save = content.get("save")
        multi_save = content.get("multi_save", None)
        if isinstance(uids, str) or isinstance(uids, int):
            uids = [uids]
        elif not isinstance(uids, list):
            raise Exception("启动配置的uid不是合法的User ID或其表达式。")
        for uid in uids:
            if isinstance(uid, str):
                u, begin, end = Configure.get_uid_and_range(uid)
                if u is None:
                    raise Exception("启动配置的uid不是合法的User ID或其表达式。")
                self.run_uid_source(u, begin, end, save, multi_save, replace)
            elif isinstance(uid, int):
                self.run_uid_source(uid, None, None, save, multi_save, replace)
            else:
                raise Exception("启动配置的uid不是合法的User ID或其表达式。")

    def run_pid(self, content):
        pids = content["pid"]
        replace = content.get("replace", False)
        save = content.get("save")
        multi_save = content.get("multi_save", None)
        if isinstance(pids, str) or isinstance(pids, int):
            pids = [pids]
        elif not isinstance(pids, list):
            raise Exception("启动配置的pid不是合法的Pixiv ID或其表达式。")
        for pid in pids:
            if isinstance(pid, str):
                matched = re.match(r'([0-9]*)[-: ]([0-9]*)', pid)
                if matched is not None:
                    min_pid, max_pid = matched.groups()
                    for i in range(int(min_pid), int(max_pid) + 1):
                        self.run_pid_source(i, save, multi_save, replace)
                else:
                    try:
                        p = int(pid)
                    except ValueError:
                        raise Exception("启动配置的pid不是合法的Pixiv ID或其表达式。")
                    self.run_pid_source(p, save, multi_save, replace)
            elif isinstance(pid, int):
                self.run_pid_source(pid, save, multi_save, replace)
            else:
                raise Exception("启动配置的pid不是合法的Pixiv ID或其表达式。")

    def run_uid_source(self, uid, begin, end, save, multi_save, replace=False):
        ret = self.pixiv.get_member_image_list(uid=uid, max_count=end)
        if ret is None:
            return
        head = begin - 1 if begin is not None else 0
        tail = end if end is not None else len(ret)
        for i in range(head, tail):
            pid, title = ret[i]
            self.run_pid_source(pid, save, multi_save, replace, uid=uid)

    def run_pid_source(self, pid, save, multi_save, replace=False, uid=None):
        ret = self.pixiv.get_image_source(pid)
        if ret is None:
            return
        if len(ret["content"]) == 1 or (len(ret["content"]) > 1 and multi_save is None):
            content, pg_index, extension = ret["content"][0]
            file_path = save.format(title=ret["title"],
                                    pid=ret["pid"],
                                    user=ret["user"],
                                    uid=uid if uid is not None else ret["user_id"]) + "." + extension
            if not os.path.exists(file_path) or replace:
                Configure.make_dir(file_path)
                with open(file_path, 'wb') as f:
                    f.write(content)
            elif not replace:
                self.notice.log("[%s]已存在，跳过。" % (pid,))
        else:
            for content, pg_index, extension in ret["content"]:
                file_path = multi_save.format(title=ret["title"],
                                              pid=ret["pid"],
                                              user=ret["user"],
                                              uid=uid if uid is not None else ret["user_id"],
                                              index=pg_index) + "." + extension
                if not os.path.exists(file_path) or replace:
                    Configure.make_dir(file_path)
                    with open(file_path, 'wb') as f:
                        f.write(content)
                elif not replace:
                    self.notice.log("[%s]已存在，跳过。" % (pid,))

    @staticmethod
    def get_uid_and_range(uid_str):
        matched = re.match(r'([0-9]*)\[([0-9]*)[-: ]([0-9]*)\]', uid_str)
        if matched is not None:
            u, begin, end = matched.groups()
            return int(u), int(begin), int(end)
        else:
            matched = re.match(r'([0-9]*)\[([0-9]*)\]', uid_str)
            if matched is not None:
                u, num = matched.groups()
                return int(u), 1, int(num)
            else:
                try:
                    u = int(uid_str)
                except ValueError:
                    return None, None, None
                return int(u), None, None

    @staticmethod
    def make_dir(filepath):
        split_index = filepath.rfind('/')
        if split_index >= 0:
            dir_path = filepath[:split_index]
            os.makedirs(dir_path, exist_ok=True)

    @staticmethod
    def help():
        return help_text
