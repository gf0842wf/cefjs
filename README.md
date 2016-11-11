# cefjs
cefpython3 based scriptable web browser for python.

**it support for JS is better than ghost.py.**

# requirements

- python2.7
- wxpython
- cefpython3

# install

- install wxpython
```
osx:
  brew install wxpython
other:
  see wxpython official website
```    

- install cefpython3
```
see https://github.com/cztomczak/cefpython
```
`pip install cefpython3`

- use cefjs

  copy the cefjs.py file to your project

# usage

see [test.py](https://github.com/gf0842wf/cefjs/blob/master/test.py)

# settings

```
http proxy, socks5 proxy, user-agent see cefjs.py -> switch_settings
cache path, log, resources, subprocess see cefjs.py -> application_settings
you must change your resources_dir_path, if not in osx.
eg. in ubuntu resources_dir_path is cefpython.GetModuleDirectory()
```


# if you want run in no x window server

`xvfb-run --auto-servernum --server-args="-screen 0 1280x760x24"  python test.py`
