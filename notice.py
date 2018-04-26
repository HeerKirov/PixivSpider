

class OutputToScreen:
    def output(self, msg):
        print(msg)

    def close(self):
        pass


class OutputToFile:
    __f__ = None

    def __init__(self, filepath):
        self.__f__ = open(filepath, 'a')

    def output(self, msg):
        self.__f__.write(msg)

    def close(self):
        self.__f__.close()


class Notice:

    __log_to__ = None
    __error_to__ = None
    __print_to__ = OutputToScreen()

    def __init__(self, log_to=OutputToScreen(), error_to=OutputToScreen()):
        self.__log_to__ = log_to
        self.__error_to__ = error_to

    def output(self, tp, msg):
        pass

    # 输出一条记录类消息。
    def log(self, msg):
        if self.__log_to__ is not None:
            self.__log_to__.output(msg)

    # 输出一条错误提示型消息。
    def error(self, msg):
        if self.__log_to__ is not None:
            self.__log_to__.output(msg)

    # 输出一条任何情况都打印到屏幕的消息。
    def print(self, msg):
        self.__print_to__.output(msg)

    def close(self):
        if self.__log_to__ is not None:
            self.__log_to__.close()
        if self.__error_to__ is not None:
            self.__error_to__.close()
