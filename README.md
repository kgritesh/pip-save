### pip-save

pip-save is a simple wrapper around **pip** so as to add ```npm --save``` style functionality to pip.

Currently its a big pain while installing new dependencies using pip. After installing the dependency,
you need to figure out the version number and then manually add it to your requirements file.
``pip-save`` allows you to install/uninstall any dependecy and automatically add/remove
it to/from your requirements file using one command only.

Since its only a wrapper around pip install and uninstall commands,
it accepts all options/config as these commands.

#### Installation

	$ pip install pip-save

####Use

To Install a package and add it to your requirements.tx

	$ pip-save install [<list of packages>]

To upgrade a package

    $ pip-save install --upgrade [<list of packages>]

To uninstall a package and remove it from your requirements.txt

	$ pip-save uninstall [<list of packages>]

To install a package from VCS and add it to your requirements file

    $ pip-save install -e <url of the repo>


#### Configuration

For most users the default configuration of pip-save should be fine. If you do
want to change pip-save's defaults you do so by adding configuration options to
a configuration file. If a `.pipconfig` file exists in the current working
directory, its automatically loaded.

Here is an example of available options along with their default values.

    [pip-save]
    requirements = requirements.txt
    use_compatible = False


##### Configuration Options

* requirements:- path to the requirements file to be used. Default value is `requirements.txt`
Can be overwritten by using command line option `-r` or `--requirement`

* use_compatible:- whether to use compatible version specifier instead of exact versions.
Default value is `False`. Can be overwritten by using command line flag `--use-compatible`
