from gpiozero import DistanceSensor
from time import sleep

class BinDistanceSensor:
    def __init__(
        self,
        trigger_pin: int = 23,
        echo_pin: int = 24,
        max_distance_m: float = 3.0
    ):
        self.sensor = DistanceSensor(
            trigger=trigger_pin,
            echo=echo_pin,
            max_distance=max_distance_m
        )

    def get_distance_cm(self) -> float:
        return self.sensor.distance * 100.0

    def is_full(self, threshold_cm: float = 15.0) -> bool:
        return self.get_distance_cm() < threshold_cm


if __name__ == "__main__":
    s = BinDistanceSensor(trigger_pin=23, echo_pin=24)
    while True:
        print(f"Distance: {s.get_distance_cm():.2f} cm")
        sleep(1)
