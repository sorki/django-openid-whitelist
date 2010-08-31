from distutils.core import setup
import os

NAME = 'django-openid-whitelist'
VERSION = '0.3'


# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('whitelist'):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)
    elif filenames:
        prefix = dirpath[10:] # Strip "whitelist/" or "whitelist\"
        for f in filenames:
            data_files.append(os.path.join(prefix, f))


f = open(os.path.join(os.path.dirname(__file__), 'README.rst'))
long_description = f.read().strip()
f.close()




setup(name=NAME,
        version=VERSION,
        description='OpenID Whitelist application for Django',
        long_description=long_description,
        author='Richard Marko',
        author_email='rissko@gmail.com',
        url='http://github.com/sorki/django-openid-whitelist',
        license='BSD',
        package_dir={'whitelist': 'whitelist'},
        packages=packages,
        package_data={'whitelist': data_files},

        classifiers=['Development Status :: 5 - Production/Stable',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Utilities'],


    )       

