This is just a utils library I have to share code with my discord bots. You are free to use it with an MIT license.


# Using the utils library in your project
To include it in your own project, you should use Github's submodule feature. Below is an example of how to do this.

```bash
# In an already existing git repository
git submodule add https://github.com/Ken-Miles/utils utils --recurse-submodules
# and then
git submodule update --init --remote --recursive
```


To update the submodule to the latest commit if you already have it added as a submodule
```bash
git submodule update --remote --merge --recursive
```

If you are attempting to clone a project that uses this as a submodule, you may need to add a flag when you attempt to clone it.
```bash
git clone --recurse-submodules <your-repository-url>
```

If you have already cloned the repository without the `--recurse-submodules` flag, you should be able to initialize and fetch the submodules like so:
```bash
git submodule update --init --remote --recursive
```

# Install dependencies
To install the dependencies for this utils library, the project includes both a requirements file and a pyproject.toml file. You can use either method to install the dependencies.

### For standard use
```bash
# from your project root
cd utils # cd into the utils directory
pip install -r requirements.txt
```

Below are just extras/misc installation options.

### Install extras (speedup, documentation, tests)

you may include any combination of the extras, below they are listed for your convenience
`docs`: documentation dependencies and files
`tests`: testing dependencies and files
`speed`: optional speedup dependencies (orjson, etc)

```bash
# from your project root
cd utils # cd into the utils directory

pip install .[docs,tests,speed]
```

## Running tests
To run the tests for this utils library, you can use pytest. Make sure you have installed the testing dependencies first (see above).

```bash
# from your project root
cd utils # cd into the utils directory
pytest -vs tests
```