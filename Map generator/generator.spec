# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_data_files

sys.setrecursionlimit(5000)
block_cipher = None

a = Analysis(['generator.py'],
             pathex=['C:\\Users\\Arturo\\Desktop\\test'],
             binaries=collect_dynamic_libs("rtree"),
             datas=collect_data_files('geopandas', subdir='datasets'),
             hiddenimports=[
    		'ctypes',
    		'ctypes.util',
    		'fiona',
		'fiona.schema',
		'fiona._shim',
    		'gdal',
    		'geos',
    		'shapely',
    		'shapely.geometry',
    		'pyproj',
    		'rtree',
    		'geopandas.datasets',
    		'pandas._libs.tslibs.timedeltas',
		'rasterio._shim',
		'sklearn.utils._weight_vector',
		'rasterio.control',
		'rasterio.sample',
		],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='test',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='test')
