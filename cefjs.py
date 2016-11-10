# -*- coding: UTF-8 -*-
from cefpython3 import cefpython
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


class CEF(object):
    js_bindings = None
    main_browser = None

    def initialize(self):
        self.js_bindings = cefpython.JavascriptBindings(bindToFrames=False, bindToPopups=True)
        self.js_bindings.SetFunction('py_func', self.py_func)  # in `html js` can call the function of js_func_name
        self.js_bindings.SetFunction('__py_cb',
                                     self.__py_sentinel)  # in `html js` can call the function of js_func_name
        self.main_browser.SetJavascriptBindings(self.js_bindings)

    def py_func(self, *args):
        pass

    def __py_sentinel(self):
        print '__py_sentinel'

    def evaluate(self, js):
        js += '\n__py_cb();'
        self.main_browser.GetMainFrame().ExecuteJavascript(js)

    def open(self, url):
        self.main_browser.LoadUrl(url)

    def on_init(self, browser, frame, status_code):
        print 'cef init ok'

    def on_load_end(self, browser, frame, status_code):
        print '%s load ok' % frame.GetUrl()


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
            self.cef.on_init(browser, frame, httpStatusCode)
        else:
            self.cef.on_load_end(browser, frame, httpStatusCode)


class CEFJSFrame(wx.Frame):
    window_count = 0
    browser = None
    mainPanel = None

    def __init__(self, url, cef_cls):
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
        self.clientHandler.cef = cef_cls()
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

    def __init__(self, redirect, cef_cls):
        self.cef_cls = cef_cls
        wx.App.__init__(self, redirect)

    def OnInit(self):
        self._create_timer()
        frame = CEFJSFrame('about:blank', self.cef_cls)
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


def loop(cef_cls):
    cefpython.Initialize(application_settings, switch_settings)

    app = CEFWXApp(False, cef_cls)
    app.MainLoop()

    del app
    cefpython.Shutdown()


if __name__ == '__main__':
    cef_cls = CEF
    loop(cef_cls)
