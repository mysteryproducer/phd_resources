FADE_RATE=0.1

class InterfaceState:
    def __init__(self):
        self._alpha:float=1.0
        self._target:float=1.0
    def calc_frame_alpha(self) -> float:
        if self._alpha!=self._target:
            self._alpha+=(-1 if self._target<self._alpha else 1) * FADE_RATE
#        self._alpha=self._alpha*0.8+self._target_alpha*0.2
#        if math.abs(self._target_alpha-self._alpha)<0.05:
#            self._alpha=self._target_alpha
        if self._alpha>0:
            self._options=False
        return self._alpha
    def show_normal(self) -> None:
        self._target=1.0
    def show_closed(self) -> None:
        self._target=0.0

    @property
    def main_alpha(self) -> float:
        return self._alpha
    @property
    def secondary_alpha(self) -> float:
        return 1.0-self._alpha