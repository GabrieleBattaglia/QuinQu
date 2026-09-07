# -*- mode: python ; coding: utf-8 -*-
# Quinqu, ricetta di compilazione.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5, modalita' auto).
# Il percorso di GBUtils si ricava dalla posizione di questo file, cosi' la
# compilazione riesce anche su una macchina dove i repository stanno altrove.
# La collezione dei suoni condivisa va portata dentro il pacchetto, altrimenti
# Acusticator non la trova e l'eseguibile resta muto: tutti i suoni di Quinqu
# vengono da li'.
import os

GBUTILS_DIR = os.path.abspath(os.path.join(SPECPATH, '..', 'GBUtils'))
COLLEZIONE = os.path.join(GBUTILS_DIR, 'Acu_Collection.json')

a = Analysis(
    ['quinqu.py'],
    pathex=[GBUTILS_DIR],
    binaries=[],
    datas=[(COLLEZIONE, '.')],
    # Servono al controllo aggiornamenti di GBUtils: senza, l'eseguibile parte
    # ma non riesce a contattare GitHub. Non toglierli.
    hiddenimports=[
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'chardet',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Quinqu usa numpy, sounddevice e la libreria standard. Le interfacce
    # grafiche e i pacchetti scientifici pesanti arriverebbero seguendo le
    # catene di import di GBUtils, che qui non si usano.
    excludes=[
        'wx',
        'PyQt5',
        'PySide2',
        'PySide6',
        'matplotlib',
        'scipy',
        'IPython',
        'notebook',
        'nbconvert',
        'qtpy',
        'pytest',
        'tkinter',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='quinqu',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
