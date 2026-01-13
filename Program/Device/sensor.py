from gpiozero import DistanceSensor
from time import sleep

class BinDistanceSensor:
    def __init__(self, pin: int = 23, max_distance_m: float = 3.0):
        self.sensor = DistanceSensor(
            echo = pin,
            trigger = pin,
            max_distance = max_distance_m
        )

    def get_distance_cm(self) -> float:
        return self.sensor.distance * 100.0

    def is_full(self, threshold_cm: float = 15.0) -> bool:
        return self.get_distance_cm() < threshold_cm


if __name__ == "__main__":
    s = BinDistanceSensor(pin = 23)
    while True:
        d = s.get_distance_cm()
        print(f"Distance: {d:.2f} cm")
        sleep(1)
