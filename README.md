# Gicisky Bluetooth ESL e-paper tag

This repository provides a `gicisky-tag-writer ` script and a `gicisky_tag` Python library to write custom images to a Gicisky / PICKSMART electronic price tag (also called electronic shelf label, or ESL), provided that it's programmable via Bluetooth ESL. So far the project has been tested only on the model "2.1 inch EPA LCD 250x122 BWR". If you have a different device, feel free to open a PR to generalize the code.

This Python project uses Poetry to manage all dependencies. To run the script from the repository folder:
```bash
git clone https://github.com/fpoli/gicisky-tag.git
cd gicisky-tag
poetry install
poetry run gicisky-tag-writer --help
```

Alternatively, to install the script without cloning the repository use [pipx](https://pypa.github.io/pipx/):
```bash
pipx install git+https://github.com/fpoli/gicisky-tag.git
gicisky-tag-writer --help
```

## Usage

```text
$ gicisky-tag-writer --help
usage: gicisky-tag-writer [-h] --image IMAGE [--address ADDRESS] [--dithering {none,floydsteinberg,combined}] [--debug-folder DEBUG_FOLDER]

Write an image to a Gicisky tag.

options:
  -h, --help            show this help message and exit
  --image IMAGE         Image to send.
  --address ADDRESS     Bluetooth address of the Gicisky tag to be updated. If not provided, the script will scan and use the first Gicisky tag that it can find.
  --dithering {none,floydsteinberg,combined}
                        Dithering method (default: none).
  --debug-folder DEBUG_FOLDER
                        Folder in which to save debug data.
```
## Documentation

Officially, to write to the tags you need to [register an account](http://a.picksmart.cn:8082/index) and [download an app](http://www.picksmart.cn/index.php/page-22-11.html) on the Picksmart website. In my case, I used the APK [`ble-tag-english-app-release-v3.1.37.apk`](http://a.picksmart.cn:8088/picksmart/app/ble-tag-english-app-release-v3.1.32.apk). I don't know why their app is not on the official app store, so install and use it at your own risk. This project makes it possible to write custom images to the tags without using any proprietary service or app.

The Bluetooth ESL protocol to update the screen is described [here](https://zhuanlan.zhihu.com/p/633113543). Independently, [`atc1441`](https://github.com/atc1441) reverse-engineered the protocol and published a Javascript image uploader ([video](https://www.youtube.com/watch?v=Cp4gNXtlbGk), [repo](https://github.com/atc1441/ATC_GICISKY_ESL), [uploader](https://atc1441.github.io/ATC_GICISKY_Paper_Image_Upload.html)) that in my case managed to write something on the screen, altough the result was gibberish because the base-64 encoded image data provided as default in the uploader is for a different screen model. Modifying the image data is not trivial, because it uses an undocumented compression format. Disassembling the APK doesn't help much to shed light on this format, because the compression function is implemented natively. One way to work around the unknown format is to flash a new custom firmware on the tags, like `atc1441` and [`rbaron`](https://github.com/rbaron) did for the TLSR tags ([firmware repo](https://github.com/atc1441/ATC_TLSR_Paper), [uploader repo](https://github.com/rbaron/pricetag-printer)). However, that's not necessary for the Gicisky tags since [`Cabalist`](https://github.com/Cabalist) managed to reverse-engineer the image format ([his notes](https://github.com/Cabalist/gicisky_image_notes)), which turns out to be a form of run-length encoding. Producing uncompressed images is not that difficult, so that's what this project does. The disadvantage is that sending the image data to the screen is slower than the official app: about 10 seconds instead of just 3 on some examples that I tried. Feel free to contribute implementing some real compression.

A copy of some of the material linked above is stored in the `docs` folder.

## Details of tag model 2.1" EPA LCD 250x122 BWR

* Bluetooth name: "PICKSMART" while it's powering up, then "NEMRxxyyzzkk"
* Bluetooth address: `FF:FF:xx:yy:zz:kk`
* Brand: Gicisky / PICKSMART
* Batteries: 2 replaceable CR2450 3V

The `xxyyzzkk` above correspond to the number encoded by the barcode on the right of the screen.

## License

License of the project, except for the content of the `docs/` folder:

Copyright (C) 2023  Federico Poli

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
