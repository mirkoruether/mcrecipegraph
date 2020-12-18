# -*- coding: utf-8 -*-
"""

@author: Mirko Ruether
"""

import io
import setuptools

def read_req_file(req_type):
    with open('requires-{}.txt'.format(req_type)) as fh:
        requires = (line.strip() for line in fh)
        return [req for req in requires if req and not req.startswith('#')]

setuptools.setup(
    name='mcrecipegraph',
    version='0.0.1',
    author='Mirko Ruether',
    author_email='mirkoruether@users.noreply.github.com',
    description='A small example package',
    long_description=io.open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/mirkoruether/mcrecipegraph',
    packages=setuptools.find_packages(exclude=['tests*']),
    include_package_data=True,
    license='MIT',
    python_requires='>=3.6',
    install_requires=read_req_file('install'),
    extras_require={
        'dev': read_req_file('dev'),
    },
    entry_points = {
        'console_scripts': ['parse_crafttweaker=mcrecipegraph.tools.parse_crafttweaker:main'],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
