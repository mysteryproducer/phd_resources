from wifiphisher.pywifiphisher import WifiphisherEngine
import argparse, threading, time

#This approach to running wifiphisher in a thread was abandoned.
#The problem turned out to be wp needing console i/o to function
#(because curses?) so this might be workable.

class WirelessToolkit(threading.Thread):
    def __init__(self,ap_name:str="Free Wifi"):
        super().__init__(name="Wifiphisher")
        self._evil:bool=False
        self._engine:WifiphisherEngine=None
        self._msg_handlers=list()
        self._ap_name:str=ap_name
        self._running:bool=True
        self._thread:threading.Thread;
    def run(self):
        #print('run!')
        self._thread=threading.current_thread()
        self._engine=self._run_engine()
        while (self._running):
            time.sleep(1)
    def stop(self):
        self._running=False
        self._thread.join()
        self._stop_engine()
    def cycle_ap(self,enable_evil=None):
        if type(enable_evil)==bool:
            self._evil=enable_evil
        else:
            self._evil=not self._evil
        self._stop_engine()
        self._engine=self._run_engine()
    def add_message_handler(self,handler):
        self._msg_handlers.append(handler)
    def _stop_engine(self) -> None:
        while self._engine is not None:
            try:
                self._engine.stop()
                self._engine=None
            except Exception as e:
                print('Error stopping wireless: ' + str(e))
    def _run_engine(self) -> WifiphisherEngine:
        try:
            #args: -nE ; no extensions
            #      -essid='AP Name'
            #      -iNM ; no MAC randomisation (optional)
            #      -kB ; emit known beacons
            #      -pI l0 ; protect interface. In this case, prevents filtering traffic on the loopback (127.0.0.1, or ::1).
            #               This is necessary because the process communicates with apache over the loopback
            #      -p oauth-login ; enables the phishing scenario, but this is overridden with the apache forwarder
            #      -aI wlan0 ; selects wlan0 as the If for for the AP. Not sure if this is needed? 
            args=['-e',self._ap_name,'-iNM','-kB','-pI','l0','-p','oauth-login','--logging','-lP=./zdw.log']#,'-aI','wlan0']
            if not self._evil:
                args.append('-nE')
            engine:WifiphisherEngine = WifiphisherEngine()
            #print(args)
            engine.start(args)
            return engine
        except KeyboardInterrupt:
            print(R + '\n (^C)' + O + ' interrupted\n' + W)
            engine.stop()
        except EOFError:
            print(R + '\n (^D)' + O + ' interrupted\n' + W)
        except Exception as e:
            print('Error starting wireless: ' + str(e))
        return None
