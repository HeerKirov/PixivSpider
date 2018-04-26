import requests
import re
import core


class ProxyPool:
    pool = []

    def __init__(self):
        pass

    def request(self):
        try:
            res = requests.get('http://www.xicidaili.com/wt/', headers=core.Core.get_headers())
        except requests.ConnectionError:
            return self.pool
        if res.status_code == 200:
            reg = '<td>([0-9.]*)</td>\\s*<td>([0-9]*)</td>'
            matched = re.findall(reg, res.text)
            pool = []
            for item in matched:
                pool.append("%s:%s" % item)
            self.pool = pool
        return self.pool
