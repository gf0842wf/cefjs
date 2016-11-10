# please see cefjs.__all__
from cefjs import Session, loop


class MySession(Session):
    def start(self):
        self.open('https://www.baidu.com/')

        js = """
        var btn_text = document.getElementById('su').value;
        py_func(btn_text)
        """
        print '###js callback data:%s' % repr(self.evaluate_args(js))

        self.evaluate("document.getElementsByTagName('a')[0].click()")

        # print '###content:%s' % self.content


if __name__ == '__main__':
    session_cls = MySession
    loop(session_cls)
