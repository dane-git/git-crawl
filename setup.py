from setuptools import setup, find_packages

setup(
    name='github-crawler',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'requests',
        'pymupdf',
        'markdownify',
        'mwparserfromhell',
        'pypandoc',
        'PyYAML',
    ],
    entry_points={
        'console_scripts': [
            'github-crawler=src.main:main',
        ],
    },
)