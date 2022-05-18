from typing import List, Optional, Set


def next_location(cur_location: str) -> Optional[str]:
    if cur_location == "init":
        return "A1"
    letter = cur_location[0]
    number = cur_location[1:]
    if number == "12":
        number = "1"
        letter = chr(ord(letter) + 1)
    else:
        number = str(int(number) + 1)
    if letter == "I" and number == "12":
        return None
    return letter + number


class WellPlate:
    def __init__(self, reserved: Set[str] = set()) -> None:
        self.reserved = reserved
        # The current well
        self._well: Optional[str] = "init"

    def get_open_well(self) -> Optional[str]:
        while True:
            assert self._well is not None
            self._well = next_location(self._well)
            if self._well is None:
                return None
            if self._well not in self.reserved:
                return self._well


class TipRack:
    def __init__(self) -> None:
        self._tip: Optional[str] = "init"

    def get_tips(self, n: int = 1) -> Optional[List[str]]:
        """Get a list of unused tip positions.

        Parameters
        ----------
        n : int
            Number of tips to return.

        Returns
        -------
        List[str]
            The next :code:`n` available tip locations.
        """
        tips: List[str] = []
        for _ in range(n):
            assert self._tip is not None
            self._tip = next_location(self._tip)
            if self._tip is None:
                return None
            tips.append(self._tip)

        return tips
