### pip-save

pip-save is a simple wrapper around **pip** so as to add ```npm --save``` style functionality to pip. Currently its a big pain while installing new dependencies using pip. After installing the dependency, you need to figure out the version number and then manually add it to your requirements file. ``pip-save`` allows you to install/uninstall any dependecy and automatically add/remove it to/from your requirements file using one command only. Since its only a wrapper around pip, it accepts all options/config as pip.

####Use
	
	python pip-save.py install [<list of packages>]

	python pip-save.py uninstall [<list of packages>]