# build/build.spec — Especificação PyInstaller para Email Builder
# Uso: pyinstaller build/build.spec
# Resultado: dist/email_builder.exe

import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent  # email_builder/

block_cipher = None

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "templates"), "templates"),
    ],
    hiddenimports=[
        "openpyxl",
        "pandas",
        "matplotlib",
        "matplotlib.backends.backend_agg",
        "PIL",
        "win32com",
        "win32com.client",
        "pywintypes",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "unittest",
        "distutils",
        "setuptools",
        "test",
        "xmlrpc",
        "http.server",
        "ftplib",
        "imaplib",
        "smtplib",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="email_builder",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # sem janela de terminal
    icon=None,       # substituir por caminho para .ico quando disponível
)
