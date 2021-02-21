from threading import Timer

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False

    def _run(self):
        print("run")
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        print("start")
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True
    
    def pause(self):
        print("pause")
        self._timer.cancel()
        self.is_running = False

    def stop(self):
        print("stop")
        self._timer.cancel()
        self.is_running = False