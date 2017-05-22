"""
setup.py
"""

from setuptools import setup, find_packages
from setuptools.extension import Extension

if __name__ == '__main__':
    with \
            open('requirements.in') as requirements, \
            open('README.rst') as readme:

        ext_modules = [
            Extension('pkcs11._loader',
                    sources=[
                        'pkcs11/_loader.pyx',
                    ],
            ),
            Extension('pkcs11._pkcs11',
                    sources=[
                        'pkcs11/_pkcs11.pyx',
                    ],
                    define_macros=[
                        # These are required to build the PKCS11 headers
                        #
                        # They vary based on OS. See extern/pkcs11.h
                        ('CK_PTR', '*'),
                        ('CK_DEFINE_FUNCTION(returnType, name)', 'returnType name'),
                        ('CK_DECLARE_FUNCTION(returnType, name)', 'returnType name'),
                        ('CK_DECLARE_FUNCTION_POINTER(returnType, name)', 'returnType (* name)'),
                        ('CK_CALLBACK_FUNCTION(returnType, name)', 'returnType (* name)'),
                    ],
            ),
        ]

        setup(
            name='python-pkcs11',
            description='PKCS#11 (Cryptoki) support for Python',
            use_scm_version=True,
            author='Danielle Madeley',
            author_email='danielle@madeley.id.au',
            url='https://github.com/danni/python-pkcs11',
            long_description=readme.read(),
            classifiers=[
                'License :: OSI Approved :: MIT License',
                'Programming Language :: Python',
                'Programming Language :: Python :: 3',
                'Programming Language :: Python :: 3.5',
                'Programming Language :: Python :: 3.6',
                'Topic :: Security :: Cryptography',
            ],

            packages=find_packages(exclude=['tests']),
            include_package_data=True,
            ext_modules=ext_modules,

            install_requires=requirements.readlines(),
            setup_requires=[
                'cython',
                'setuptools >= 18.0',
                'setuptools_scm',
            ],

            test_suite='tests',
        )
