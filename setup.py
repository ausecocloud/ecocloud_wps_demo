from setuptools import setup, find_packages

version = '0.1'

setup(
    name='ecocloud_wps_demo',
    version=version,
    description="Ecocloud WPS demo services",
    long_description=(open("README.rst").read() + "\n\n" +
                      open("HISTORY.rst").read()),
    classifiers=[
        "Development Status :: 1 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Pyramid",
        "Intended Audience :: Developers",
        'Intended Audience :: Science/Research',
        "License :: OSI Approved :: Apache Software License"
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        'Topic :: Scientific/Engineering :: GIS'
    ],
    keywords='ogc wps pyramid',
    author='',
    author_email='',
    maintainer='',
    maintainer_email='',
    url='https://github.com/ausecocloud/ecocloud_wps_demo',
    license='Apache License 2.0',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'pyramid',
        'pywps',
        'python-swiftclient',
        'python-keystoneclient'
    ],
    entry_points={
        'paste.app_factory': [
            'main = ecocloud_wps_demo:main',
        ],
        'pywps_processing': [
            'threads = ecocloud_wps_demo.pywps.processing:ThreadProcessing',
        ],
        'pywps_storage': [
            'SwiftStorage = ecocloud_wps_demo.pywps.swiftstorage:SwiftStorage',
        ]
    },

)
