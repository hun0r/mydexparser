from zipfile import ZipFile
from pathlib import Path
from dex import DEXFile, map_list

apk_path = Path(__file__).parent / 'base.apk'
class_name = 'classes4.dex'
base_model = b'Lhu/ekreta/ellenorzo/data/remote/Dto;'
model_pattern_start = b'Lhu/ekreta/ellenorzo/data/remote/'
model_pattern_end = b'Dto;'

with ZipFile(apk_path, 'r') as apk:
    classes = apk.open(class_name)
    dex = DEXFile.parse(classes)
    print(map_list.parse(classes, None, off=dex.header.map_off))