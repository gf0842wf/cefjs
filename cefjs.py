# -*- coding: UTF-8 -*-
from cefpython3 import cefpython
from threading import Thread, Lock
import Queue
import wx

application_settings = {
    "cache_path": "/tmp/cef/cache/",
    "debug": True,
    "log_severity": cefpython.LOGSEVERITY_INFO,
    "log_file": "/tmp/cef/debug.log",
    "resources_dir_path": cefpython.GetModuleDirectory() + "/Resources",
    "browser_subprocess_path": "%s/%s" % (cefpython.GetModuleDirectory(), "subprocess"),
    "unique_request_context_per_browser": True,
    "downloads_enabled": True,
    "remote_debugging_port": 0,
    "context_menu": {
        "enabled": True,
        "navigation": True,
        "print": True,
        "view_source": True,
        "external_browser": True,
        "devtools": True,
    },

    "ignore_certificate_errors": True,
}

browser_settings = {
    "plugins_disabled": True,
    "file_access_from_file_urls_allowed": True,
    "universal_access_from_file_urls_allowed": True,
}

switch_settings = {
    "locale_pak": cefpython.GetModuleDirectory() + "/Resources/en.lproj/locale.pak",

    # "proxy-server": "socks5://127.0.0.1:8888",
    # "no-proxy-server": "",
    # "enable-media-stream": "",
    # "remote-debugging-port": "12345",
    # "disable-gpu": "",
    # "--invalid-switch": "" -> Invalid switch name
}


def set_app_settings(settings={}):
    global application_settings
    application_settings.update(settings)


def set_browser_settings(settings={}):
    global browser_settings

    browser_settings.update(settings)


def set_switch_settings(settings={}):
    global switch_settings
    switch_settings.update(settings)


status = 0
lock = Lock()


class Session(object):
    def initialize(self, task_q, page_q, js_q, sentinel_q):
        self.task_q = task_q
        self.page_q = page_q
        self.js_q = js_q
        self.sentinel_q = sentinel_q
        self.start()

    def start(self):
        self.open('http://120.76.121.103/fengshen/game.php?sid=f41a93a9ee56ff7d318d1079f93c65fa&cmd=1913')
        self.evaluate("document.getElementsByTagName('a')[0].click()")

    def open(self, url):
        global lock
        lock.acquire()
        global status
        status = 1
        lock.release()
        self.task_q.put(('page', (url,)))
        self.page_q.get()

    def evaluate(self, js):
        js += '\n__py_cb();'
        global lock
        lock.acquire()
        global status
        status = 2
        lock.release()
        self.task_q.put(('js', js))
        self.sentinel_q.get()

    def evaluate_args(self, js):
        if 'py_func' not in js:
            raise Exception('not use py_func, please use evaluate')
        global lock
        lock.acquire()
        global status
        status = 2
        lock.release()
        self.task_q.put(('js', js))
        args = self.js_q.get()
        return args

    @property
    def content(self):
        js = """
            var html = document.documentElement.outerHTML;
            py_func(html);
            """
        return self.evaluate_args(js)


class CEF(object):
    js_bindings = None
    main_browser = None

    task_q = Queue.Queue(maxsize=1)
    page_q = Queue.Queue(maxsize=1)
    js_q = Queue.Queue(maxsize=1)
    sentinel_q = Queue.Queue(maxsize=1)

    task_thread = None
    logic_thread = None

    session = None

    def task(self, task_q):
        while True:
            try:
                k, msg = task_q.get(True, 1)
            except Queue.Empty:
                continue
            if k == 'page':
                url = msg[0]
                self.main_browser.LoadUrl(url)
            if k == 'js':
                self.main_browser.GetMainFrame().ExecuteJavascript(msg)

    def __init__(self, session_cls):
        self.session_cls = session_cls

    def initialize(self):
        self.task_thread = Thread(target=self.task, args=(self.task_q,))
        self.task_thread.start()

        self.js_bindings = cefpython.JavascriptBindings(bindToFrames=False, bindToPopups=True)
        # in `html js` can call the function of js_func_name
        self.js_bindings.SetFunction('py_func', self.on_py_func)
        self.js_bindings.SetFunction('__py_cb', self.__py_sentinel)
        self.main_browser.SetJavascriptBindings(self.js_bindings)

    def __py_sentinel(self):
        self.sentinel_q.put(None)

    def on_py_func(self, *args):
        self.js_q.put(args)

    def on_init(self, url, status_code):
        if not self.session:
            self.session = self.session_cls()
        self.logic_thread = Thread(target=self.session.initialize,
                                   args=(self.task_q, self.page_q, self.js_q, self.sentinel_q))
        self.logic_thread.start()

    def on_load_end(self, url, status_code):

        global lock
        lock.acquire()
        global status

        if status == 1:
            self.page_q.put(None)
        lock.release()


class CEFHandler:
    cef = None

    def __init__(self):
        pass

    def OnBeforePopup(self, browser, frame, targetUrl, unknown1, unknown2, unknown3, unknown4, unknown5, unknown6):
        # open only in one tab
        browser.LoadUrl(targetUrl)
        return True

    def OnLoadStart(self, browser, frame):
        pass

    def OnLoadEnd(self, browser, frame, httpStatusCode):
        url = frame.GetUrl()
        if url == 'about:blank':
            self.cef.on_init(url, httpStatusCode)
        else:
            self.cef.on_load_end(url, httpStatusCode)


class CEFJSFrame(wx.Frame):
    window_count = 0
    browser = None
    mainPanel = None

    def __init__(self, url, session_cls):
        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY, title='cef wx', size=(800, 600))
        self.window_count += 1

        self.mainPanel = wx.Panel(self, style=wx.WANTS_CHARS)

        window_info = cefpython.WindowInfo()
        width, height = self.mainPanel.GetClientSizeTuple()
        window_info.SetAsChild(self.mainPanel.GetHandle(), [0, 0, width, height])

        self.browser = cefpython.CreateBrowserSync(
            window_info,
            browserSettings=browser_settings,
            navigateUrl=url)

        self.clientHandler = CEFHandler()
        self.clientHandler.cef = CEF(session_cls)
        self.clientHandler.cef.main_browser = self.browser
        self.clientHandler.cef.initialize()
        self.browser.SetClientHandler(self.clientHandler)

        menu = wx.Menu()

        act_test = menu.Append(1, 'Test')
        act_exit = menu.Append(10, 'Exit')
        menu_bar = wx.MenuBar()
        menu_bar.Append(menu, 'Action')
        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_MENU, self.on_close, act_exit)
        self.Bind(wx.EVT_MENU, self.on_test, act_test)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_test(self, event):
        print 'on test'

    def on_close(self, event):
        del self.browser
        self.Destroy()

        self.window_count -= 1
        if self.window_count <= 0:
            cefpython.Shutdown()
            wx.GetApp().Exit()


class CEFWXApp(wx.App):
    timer = None
    timerID = 1
    timerCount = 0

    def __init__(self, redirect, session_cls):
        self.session_cls = session_cls
        wx.App.__init__(self, redirect)

    def OnInit(self):
        self._create_timer()
        frame = CEFJSFrame('about:blank', self.session_cls)
        self.SetTopWindow(frame)
        frame.Show()
        return True

    def _create_timer(self):
        self.timer = wx.Timer(self, self.timerID)
        self.timer.Start(10)  # 10ms
        wx.EVT_TIMER(self, self.timerID, self.on_timer)

    def on_timer(self, event):
        self.timerCount += 1
        cefpython.MessageLoopWork()

    def OnExit(self):
        self.timer.Stop()


def loop(session_cls):
    cefpython.Initialize(application_settings, switch_settings)

    app = CEFWXApp(False, session_cls)
    app.MainLoop()

    del app
    cefpython.Shutdown()


__all__ = ['loop', 'Session']

if __name__ == '__main__':
    s_cls = Session
    loop(s_cls)
