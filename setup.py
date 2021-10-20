import re
from distutils.core import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

with open('README.md') as f:
    readme = f.read()

with open('useless_bot/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

setup(
    name='useless_bot',
    version=version,
    packages=['useless_bot'],
    url='https://github.com/MRvillager/useless_bot',
    license='MIT License',
    author='MRvillager',
    author_email='mrvillager.dev@gmail.com',
    description='A discord bot',
    long_description=readme,
    long_description_content_type="text/markdown",
    install_requires=requirements,
    python_requires='>=3.9.0,<3.10',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet',
        'Topic :: Utilities',
    ]
)
