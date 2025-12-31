from picamera2 import Picamera2
import time
from datetime import datetime
from pathlib import Path

def capture(output_dir: str = "captures") -> str:
    Path(output_dir).mkdir(parents = True, exist_ok = True)

    picam2 = Picamera2()
    config = picam2.create_still_configuration(main = {"size": (640, 480)})
    picam2.configure(config)
    picam2.start()
    time.sleep(1)

    filename = f"{output_dir}/binbin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    picam2.capture_file(filename)
    picam2.stop()
    return filename

if __name__ == "__main__":
    path = capture()
    print(f"Captured: {path}")
