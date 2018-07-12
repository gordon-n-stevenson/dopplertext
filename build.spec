import sys
sys.setrecursionlimit(5000)

import gooey
gooey_root = os.path.dirname(gooey.__file__)
gooey_languages = Tree(os.path.join(gooey_root, 'languages'), prefix = 'gooey/languages')
gooey_images = Tree(os.path.join(gooey_root, 'images'), prefix = 'gooey/images')
a = Analysis(['DopplerText.py'],
             pathex=['C:\\Python27','C:\\Python27\\Lib\\site-packages\\scipy\\extra-dll'],
             hiddenimports=['scipy._lib.messagestream','pywt._extensions._cwt','pandas._libs.tslibs','pandas._libs.tslibs.timedeltas', 'pandas._libs.tslibs.np_datetime', 'pandas._libs.tslibs.nattype', 'pandas._libs.skiplist'],
             hookspath=None,
             runtime_hooks=None,
             )
pyz = PYZ(a.pure)

"""# Add the following
def get_pandas_path():
    import pandas
    pandas_path = pandas.__path__[0]
    return pandas_path

dict_tree = Tree(get_pandas_path(), prefix='pandas', excludes=["*.pyc"])
a.datas += dict_tree
a.binaries = filter(lambda x: 'pandas' not in x[0], a.binaries)
"""

options = [('u', None, 'OPTION'), ('u', None, 'OPTION'), ('u', None, 'OPTION')]

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          options,
          gooey_languages, # Add them in to collected files
          gooey_images, # Same here.
          name='DopplerText',
          debug=True,
          strip=None,
          upx=True,
          console=True,
          windowed=True,
          icon=os.path.join(gooey_root, 'images', 'program_icon.ico'))