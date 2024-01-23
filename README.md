# IPython Extension: ipython-suggestions

(i) Number one feature: system wide symbol searching!
  When ipython is loaded, suggestions module will scan your python paths for
  symbols and will create a cache. On the author's old 2008 computer (this
  readme is from 2017), 50000 symbols load in 10 seconds.
  But then you get a very easy way to import any symbol, without typing or
  remembering the entrine import path.
  First example:

   In [1]: %findsymbol DecisionTreeClasifir  # two typos here on purpose
   Out[1]: 0 (C) from sklearn.tree import DecisionTreeClassifier

   In [2]: %suggestion 0
   from sklearn.tree import DecisionTreeClassifier  # it's now imported!

  %findsymbol searches string up to two character edits (deletion, substitution, transpose
  and insertion).

  Second example:

    In [1]: %findsymbol pypl  # now hit tab!
    [this completes to:]
    In [1]: %findsymbol pyplot...matplotlib  # press enter now.
    from matplotlib import pyplot
    [pyplot is now imported]

  Even better example:

    In [1]: %findsymbol pypl  # now hit tab!
    [this completes to:]
    In [1]: %findsymbol pyplot...matplotlib
    [now add -as parameter]
    In [1]: %findsymbol pyplot...matplotlib -as plt
    from matplotlib import pyplot as plt
    [pyplot is now imported as plt]

  The completions offered by pressing tab in a %findsymbol line are all the
  symbols that begin with what you wrote. Note that this is case-sensitive.

  This also works in jupyter :)

(ii) Get suggestions on misspelled names:

   In [1]: my_awesome_variable = 10

   In [2]: 10 * my_awsome_variable ** 3
   ---------------------------------------------------------------------------
   NameError                                 Traceback (most recent call last)
   <ipython-input-86-a128c9dcb1fc> in <module>()
   ----> 1 10 * my_awsome_variable ** 3

   NameError: name 'my_awsome_variable' is not defined
   Did you mean:
   0 my_awesome_variable

   In [3]: %suggestion 0
   [ipython automatically fills the next line]
   In [4]: 10 * my_awesome_variable ** 3

   Auto-filling of corrected code currently only works inside the shell and not
   in jupyter.

# Installation

From pypi:

```shell
pip install ipython-suggestions
```

Or directly from source:

```shell
pip install git+https://github.com/drorspei/ipython-suggestions
```

then append the output of ``ipython -m ipython_suggestions``
to the output of ``ipython profile locate`` (typically
``~/.ipython/profile_default/ipython_config.py``).
