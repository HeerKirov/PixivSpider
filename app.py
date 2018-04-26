from configure import Configure
import sys
import os


def get_configure():
    if len(sys.argv) <= 1:
        print(Configure.help())
        return None
    conf_path = sys.argv[1]
    if not os.path.exists(conf_path):
        raise Exception("未找到配置文件。")
    f = open(conf_path, 'r')
    text = ""
    for line in f.readlines():
        text += line + '\n'
    return text


def main():
    text = get_configure()
    if text is not None:
        c = Configure(text)
        c.run()


if __name__ == '__main__':
    main()

