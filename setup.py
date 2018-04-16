from distutils.core import setup
import py2exe

setup(
    windows = [
        {
            "script": "report.py",
            "icon_resources": [(1, "report.ico")],
            "name": "report",
            "version": "0.3",
        },
        {
            "script": "consolle.py",
            "icon_resources": [(1, "consolle.ico")],
            "name": "consolle",
            "version": "0.3",
        },
    ],
    data_files = [('', ['report.gif', 'consolle.gif'])])

# to create the distribution, run `python setup.py py2exe`
