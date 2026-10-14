from pathlib import Path
import PySide6
# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    [str(Path(SPECPATH) / 'main.py')],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
from pathlib import Path
qt_runtime = Path(PySide6.__file__).parent
for dll_name in ('vcruntime140.dll', 'vcruntime140_1.dll', 'msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll', 'msvcp140_codecvt_ids.dll', 'concrt140.dll'):
    a.binaries = [entry for entry in a.binaries if entry[0].lower() != dll_name]
    a.binaries.append((dll_name, str(qt_runtime / dll_name), 'BINARY'))
a.binaries = [entry for entry in a.binaries if Path(entry[0]).name.lower() != 'ucrtbase.dll' and not Path(entry[0]).name.lower().startswith('api-ms-win-crt-')]
a.binaries = [entry for entry in a.binaries if Path(entry[0]).name.lower() not in ('icuuc.dll', 'icuin.dll', 'icudt.dll')]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MediaPlayer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)



