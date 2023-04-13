import os
import setuptools
import re

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

requirements = [
    "flatdict",
    "pyyaml",
    "dictdiffer"
]

requirements_tests = [
    "flake8",
    "coverage",
    'tox',
    'virtualenv',
    'ansible'
]

extras = {
    'tests': requirements_tests,
}

with open('{}/ansible_collections/lecontesteur/ganeti_cli/galaxy.yml'.format(os.path.dirname(__file__) or '.')) as f:
    search = re.search('version: (?P<version>\d+[.]\d+[.]\d+)', f.read())
    version = search.group('version')

setuptools.setup(
    name="ansible-module-ganeti-cli",
    version=version,
    author="LeConTesteur",
    description="Ansible Module for ganeti",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LeConTesteur/ansible-module-ganeti-cli",
    project_urls={
        "Bug Tracker": "https://github.com/LeConTesteur/ansible-module-ganeti-cli/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU GENERAL PUBLIC LICENSE v3.0",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "ansible_collections/"},
    packages=setuptools.find_packages(where="ansible_collections", include=["lecontesteur", "*.yml"]),
    python_requires=">=3.5",
    install_requires = requirements,
    tests_require = requirements_tests,
    extras_require = extras,
)