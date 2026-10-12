from py2exe import freeze

freeze(
    windows = [
        {
            "script": "report.py",
            "icon_resources": [(1, "report.ico")],
            "version_info": {"version": "0.7.1"},
        },
        {
            "script": "consolle.py",
            "icon_resources": [(1, "consolle.ico")],
            "version_info": {"version": "0.7.4"},
        },
    ],
    data_files = [('', ['report.gif', 'consolle.gif'])])

# to create the distribution, run `python setup.py`
