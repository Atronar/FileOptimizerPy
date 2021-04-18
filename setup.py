from setuptools import setup
from setuptools import find_packages

setup(
  name = "FileOptimizerPy",
  description = "Python package and utility for files optimization",
  url = "https://github.com/Atronar/FileOptimizerPy",
  version = "1.1.1624",
  author = "ATroN",
  author_email = "master.atron@gmail.com",
  license = "AGPLv3",
  python_requires='>=3.6',
  platforms = ["any"],
  packages = find_packages(),
  install_requires = ["fleep","send2trash","jsmin"],
  include_package_data = True,
  classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Operating System :: OS Independent",
    "License :: OSI Approved :: GNU Affero General Public License v3",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Utilities",
    "Programming Language :: Python :: 3"
  ]
)
