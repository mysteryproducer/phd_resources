import subprocess, threading, traceback, time
STATUS_STOPPED=0
STATUS_RUNNING=2
STATUS_STARTING=1
STATUS_STOPPING=3
STATUS_ERROR=4
status_txt={STATUS_STOPPED:"Stopped",
            STATUS_STARTING:"Starting",
            STATUS_RUNNING:"Running",
            STATUS_STOPPING:"Stopping",
            STATUS_ERROR:"Error"}

class WirelessToolkit(threading.Thread):
    def __init__(self,ap_name:str="Free Wifi"):
        super().__init__(name="Wifiphisher")
        self._evil:bool=False
        self._running:bool=True
        self._process:subprocess.Popen=None
        self._ap_name:str=ap_name
        self._status:int=STATUS_STOPPED
        self._status_handlers:list=list()
        #This thread is in a comms loop with the process, and there'd be a conflict
        #if we tried to communicate() and issue a request to close.
        #Instead, queue commands for the external process and feed them on the comms loop.
        self._msgs_for_wp:list=list()
        self.set_status(STATUS_STOPPED)
        self._process=self._run_engine()

    def set_status(self,status:int) -> None:
        self._status=status
        status_msg:str=status_txt[status]
        for handler in self._status_handlers:
            handler((status,status_msg))
    def add_status_handler(self,handler):
        self._status_handlers.append(handler)
        handler((self._status,status_txt[self._status]))
    def shutdown(self):
        self._running=False
        self._stop_engine()
    def cycle_ap(self,enable_evil=None):
        if (self._status & 1) != 0:
            print('Request for restart while ' + status_txt[self._status])
            return
        t=threading.Thread(name="wireless restart",target=lambda:self._cycle(enable_evil))
        t.start()
    def _cycle(self,enable_evil=None):
        self.set_status(STATUS_STOPPING)
        if type(enable_evil)==bool:
            self._evil=enable_evil
        else:
            self._evil=not self._evil
        thread=self._stop_engine()
        thread.join()
        self._process=self._run_engine()
    def _stop_engine(self) -> threading.Thread:
        self.set_status(STATUS_STOPPING)
        t=threading.Thread(name="wireless shutdown",target=lambda:self._stop_process())
        t.start()
        return t
    def _stop_process(self) -> None:
        sp=self._process
        if sp is not None:
            try:
                sp.stdin.write('\x1b')
                sp.stdin.flush()
                try:
                    sp.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    sp.kill()
                self._process=None
                self.set_status(STATUS_STOPPED)
            except Exception:
                sp.kill()
                print('Error stopping wireless: ')
                traceback.print_exc()
                self._process=None
                self.set_status(STATUS_ERROR)
    def _run_engine(self) -> subprocess.Popen:
        self.set_status(STATUS_STARTING)
        try:
            #args: -nE ; no extensions (switch off all attacks, just run AP)
            #      -nD=no deauth. Deauthing is nasty (non-destructive, but annoying); no need for it.
            #      -essid='AP Name'
            #      -iNM ; no MAC randomisation (I use this mode for dev because I run a MAC filter at home)
            #      -kB ; emit known beacons (this is an extension, so it's evil mode only)
            #      -pI l0 ; protect interface. In this case, prevents filtering traffic on the loopback (127.0.0.1, or ::1).
            #               This is necessary because the AP communicates with apache over the loopback
            #      -p httprelay ; enables the phishing scenario, 'httprelay' overrides with the apache forwarder
            #      -aI wlan0 ; selects wlan0 as the If for for the AP.  
            #      --dnsmasq-conf ; sets the configuration file location for the DNS server. This file has an entry to spoof all domains.
            dnsmasq_cfg='/home/pi/dnsmasq/dnsmasq.conf'
            wp_exe='/usr/local/bin/wifiphisher'
            args=[wp_exe,'-e',self._ap_name,'-nD','-iNM','-pI','l0','-p','httprelay']#,'--skip-dnsmasq','--dnsmasq-conf',dnsmasq_cfg,
            if not self._evil:
                args.append('-nE')
            engine=subprocess.Popen(args,stdin=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,bufsize=1)
            return engine
        except KeyboardInterrupt:
            print(R + '\n (^C)' + O + ' interrupted\n' + W)
            engine.stop()
        except EOFError:
            print(R + '\n (^D)' + O + ' interrupted\n' + W)
        except Exception as e:
            print('Error starting wireless: ')
            traceback.print_exc()
            self.set_status(STATUS_ERROR)
        return None

    def run(self):
        while (self._running):
            if self._status==STATUS_ERROR:
                time.sleep(0.5)
                continue
            proc=self._process
            if proc is None:
                print('No process')
                time.sleep(0.5)
                continue
            try:
                err_message=proc.stderr.readline()
#                print('Got: ' + err_message)
                if err_message.startswith('Running'):
                    self.set_status(STATUS_RUNNING)
            except Exception as e:
                traceback.print_exc()


