#! /usr/bin/env python
# Copyright by Yutaka Matsubara (See http://d.hatena.ne.jp/mopemope/20070529/p2)
# Used under MIT License with permission by the author.

from twisted.internet import reactor
import sys, os, string, time

if string.find(os.path.abspath(sys.argv[0]), os.sep+'Twisted') != -1: 
    sys.path.insert(0, os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir)))
if hasattr(os, "getuid") and os.getuid() != 0:
    sys.path.insert(0, os.path.abspath(os.getcwd()))

def reloader_thread():
    mtimes = {}
    win = (sys.platform == "win32")
    while reactor.running:
        for filename in filter(lambda v: v, map(lambda m: getattr(m, "__file__", None), sys.modules.values())):
            if filename.endswith(".pyc") or filename.endswith("*.pyo"):
                filename = filename[:-1]
            if not os.path.exists(filename):
                continue # File might be in an egg, so it can't be reloaded.
            stat = os.stat(filename)
            mtime = stat.st_mtime
            if win:
                mtime -= stat.st_ctime
            if filename not in mtimes:
                mtimes[filename] = mtime
                continue
            if mtime != mtimes[filename]:
                def _stop():
                    reactor.stop()
                    global reload
                    reload = True
                reactor.callFromThread(_stop)
        time.sleep(1)

def restart_with_reloader():
    while True:
        args = [sys.executable] + sys.argv
        if sys.platform == "win32":
            args = ['"%s"' % arg for arg in args]
        new_environ = os.environ.copy()
        new_environ["RUN_MAIN"] = 'true'
        exit_code = os.spawnve(os.P_WAIT, sys.executable, args, new_environ)
        if exit_code != 3:
            return exit_code

def reload_support(main_func, args=None, kwargs=None):
    if os.environ.get("RUN_MAIN") == "true":
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        try:
            def _delay():
                reactor.callInThread(reloader_thread)
            reactor.callLater(5, _delay)
            main_func(*args, **kwargs)
        except KeyboardInterrupt:
            pass
    else:
        try:
            sys.exit(restart_with_reloader())
        except KeyboardInterrupt:
            pass
            
from twisted.scripts.twistd import run 
reload_support(run)
if reload:
    sys.exit(3)
else:
    sys.exit(0)

# vim: set ft=python:
