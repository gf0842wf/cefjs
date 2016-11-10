from cefjs import CEF, loop


class MyCEF(CEF):
    def py_func(self, *args):
        """this function is callback, can call in js code
        """
        content = args[0]
        num = args[1]
        print content, num

    def on_init(self, browser, frame, status_code):
        self.open('http://120.76.121.103/fengshen/game.php?sid=f41a93a9ee56ff7d318d1079f93c65fa&cmd=113')

    def on_load_end(self, browser, frame, status_code):
        num = 1
        js = """
            var html = document.documentElement.outerHTML;
            var num = %s;
            py_func(html, num);
            """ % num
        self.evaluate(js)


if __name__ == '__main__':
    cef_cls = MyCEF
    loop(cef_cls)
