import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

requirements = [
    "flatdict"
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

setuptools.setup(
    name="ansible-module-ganeti-cli",
    version="0.0.1",
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
    package_dir={"": "library"},
    packages=setuptools.find_packages(where="library") + setuptools.find_packages(where="module_utils"),
    python_requires=">=3.6",
    install_requires = requirements,
    tests_require = requirements_tests,
    extras_require = extras,
)