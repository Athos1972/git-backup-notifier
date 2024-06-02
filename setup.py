from setuptools import setup, find_packages

setup(
    name='git-backup-notifier',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'toml',
        'requests',
        'plyer',
    ],
    entry_points={
        'console_scripts': [
            'git-backup-notifier=git_backup_notifier.backup:main',
        ],
    },
    author='Bernhard Buhl',
    author_email='buhl@buhl-consulting.com.cy',
    description='A tool for backing up uncommitted and unpushed Git files with notifications.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Athos1972/git-backup-notifier',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
