from zipfile import ZipFile
from pathlib import Path
from dex import DEXFile, map_list, class_def_item

apk_path = Path(__file__).parent / "base.apk"
class_name = "classes4.dex"
base_model = b"Lhu/ekreta/ellenorzo/data/remote/Dto;"
model_pattern_start = b"Lhu/ekreta/ellenorzo/data/remote/"
model_pattern_end = b"Dto;"

with ZipFile(apk_path, "r") as apk:
    classes = apk.open(class_name)
    dex = DEXFile.parser.parse(classes)
    dex.header
    with open("data", "w") as f:
        print(
            class_def_item[dex.header.class_defs_size].parse(
                classes, off=dex.header.class_defs_off
            ),
            file=f,
        )
