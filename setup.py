"""
Author(s): Matthew Loper

See LICENCE.txt for licensing and contact information.
"""

from setuptools import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import numpy
import platform
import os

# setuptools DWIM monkey-patch madness
# http://mail.python.org/pipermail/distutils-sig/2007-September/thread.html#8204
import sys
if 'setuptools.extension' in sys.modules:
    m = sys.modules['setuptools.extension']
    m.Extension.__dict__ = m._Extension.__dict__

context_dir = os.path.join(os.path.dirname(__file__), 'contexts')

def download_osmesa():
    import os, re, zipfile
    from utils import wget
    mesa_dir = os.path.join(context_dir,'OSMesa')
    if not os.path.exists(mesa_dir):
        sysinfo = platform.uname()
        osmesa_fname = 'OSMesa.%s.%s.zip' % (sysinfo[0], sysinfo[-2])
        zip_fname = os.path.join(context_dir, osmesa_fname)
        if not os.path.exists(zip_fname):
            print "Downloading %s" % osmesa_fname
            # MPI url was: http://files.is.tue.mpg.de/mloper/opendr/osmesa/%s
            wget('https://s3.amazonaws.com/bodylabs-assets/public/osmesa/%s' % (osmesa_fname,), dest_fname=zip_fname)
        assert(os.path.exists(zip_fname))
        with zipfile.ZipFile(zip_fname, 'r') as z:
            for f in filter(lambda x: re.search('[ah]$', x), z.namelist()):
                z.extract(f, path=context_dir)
        assert(os.path.exists(mesa_dir))


def autogen_opengl_sources():
    import os
    sources = [ os.path.join(context_dir, x) for x in ['_constants.py', '_functions.pyx'] ]
    if not all([ os.path.exists(x) for x in sources ]):
        print "Autogenerating opengl sources"
        from contexts import autogen
        autogen.main()
        for x in sources:
            assert(os.path.exists(x))


def setup_opendr(ext_modules):
    ext_modules=cythonize(ext_modules)
    setup(name='opendr',
            version='0.5',
            packages = ['opendr', 'opendr.contexts', 'opendr.test_dr'],
            package_dir = {'opendr': '.'},
            author = 'Matthew Loper',
            author_email = 'matt.loper@gmail.com',
            url = 'http://files.is.tue.mpg/mloper/opendr/',
            ext_package='opendr',
            package_data={'opendr': ['test_dr/nasa*']},
            install_requires=['cython'],
            ext_modules=ext_modules,
          )


def mesa_ext():
    libraries = ['OSMesa', 'GL', 'GLU']
    extra_args = []
    if platform.system()=='Darwin':
        libraries.append('talloc')
        extra_args.append('-Qunused-arguments')
    return Extension("contexts.ctx_mesa", ['contexts/ctx_mesa.pyx'],
                        language="c",
                        library_dirs=['contexts/OSMesa/lib'],
                        depends=['contexts/_constants.py'],
                        define_macros = [('__OSMESA__', 1)],
                        include_dirs=['.', numpy.get_include(), 'contexts/OSMesa/include'],
                        libraries=libraries,
                        extra_compile_args=extra_args,
                        extra_link_args=extra_args)

def mac_ext():
    return Extension("contexts.ctx_mac", ['contexts/ctx_mac.pyx', 'contexts/ctx_mac_internal.c'],
        language="c",
        depends=['contexts/_constants.py', 'contexts/ctx_mac_internal.h'],
        include_dirs=['.', numpy.get_include()],
        extra_compile_args=['-Qunused-arguments'],
        extra_link_args=['-Qunused-arguments'])


def main():
    from contexts.fix_warnings import fix_warnings
    fix_warnings()

    # Get osmesa and some processed files ready
    download_osmesa()
    autogen_opengl_sources()

    # Get context extensions ready & build
    if platform.system() == 'Darwin':
        setup_opendr([mesa_ext(), mac_ext()])
    else:
        setup_opendr([mesa_ext()])


if __name__ == '__main__':
    main()
