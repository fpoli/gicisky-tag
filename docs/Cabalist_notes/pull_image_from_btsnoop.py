import re
import subprocess
import time
import uuid
import zipfile
from pathlib import Path

# Install Gicisky app (http://a.picksmart.cn:8088/picksmart/app/ble-tag-english-app-release-v3.1.32.apk)
# Register/Login
# Design templates here: http://a.picksmart.cn:8081

# Put Android device in Developer mode and Enable HCI Snoop
# The most reliable way I've found on my device is to restart before every capture


start = time.time()
print("Pulling bugreport...")
bugreport_filename = Path(f'staging/bugreport-{time.strftime("%Y%m%d-%H%M%S")}.zip')
subprocess.run(["adb", "bugreport", bugreport_filename])

# First range is Connection handle
# Second range is Total data size
# Third range is Application data size (i.e. total data size - 0x4
bt_image_write_header_pattern = b"\x02[\x01-\x04]\x00[\x00-\xFF]\x00[\x00-\xFF]\x00\x04\x00\x52\x12\x00"

print("Extracting images...")
with zipfile.ZipFile(bugreport_filename) as zf:
    output_filename = Path(f"staging/sample_image_{uuid.uuid4().hex}.txt")
    print(f"Saving to {output_filename}")
    with zf.open('FS/data/misc/bluetooth/logs/btsnoop_hci.log') as f, open(output_filename, 'w') as output:
        log_data = f.read()
        log_data.replace(b" ", b"").replace(b"\n", b"")
        packet_counter = 0
        for m in re.finditer(bt_image_write_header_pattern, log_data):
            # Get the Total Data size and then add the offset from the header
            packet_length = log_data[m.start() + 3] + 5
            output.write((log_data[m.start() + 12:m.start() + packet_length]).hex() + "\n")
            packet_counter += 1

        print(f"Total packets received: {packet_counter}")

successful_img_captures = Path("successful_img_captures")

with open(output_filename) as f:
    data = f.read()
    _file_header = "00000000983a"
    imgs = [_file_header + e for e in data.split(_file_header) if e]
    for i, each_img in enumerate(imgs):
        print(f"Saving image {i} ({len(each_img.split())} packets)...")
        with open(output_filename.parent / f"{output_filename.stem}_{i}{output_filename.suffix}", 'w') as img_output:
            img_output.write(each_img)
        for each_good_img in successful_img_captures.iterdir():
            if each_good_img.name.startswith("."):
                continue
            if not each_good_img.is_file():
                continue
            with open(each_good_img) as good_img:
                if each_img == good_img.read():
                    print(f"Image {i} is the same as {each_good_img}")

print("Done!")
end = time.time()
print(f"This took: {end - start}")
