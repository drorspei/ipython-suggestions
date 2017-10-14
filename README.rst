ipython-suggestions
==================

(i) Get suggestions on misspelled names:

   In [1]: my_awesome_variable = 10

   In [2]: 10 * my_awsome_variable ** 3
   ---------------------------------------------------------------------------
   NameError                                 Traceback (most recent call last)
   <ipython-input-86-a128c9dcb1fc> in <module>()
   ----> 1 10 * my_awsome_variable ** 3

   NameError: name 'my_awsome_variable' is not defined
   Did you mean:
   my_awesome_variable

   In [3]: 10 * my_awesome_variable ** 3
   Out[3]: 10000

(ii) Do system wide symbol searching:

   In [1]: %findsymbol DecisionTreeClassifier
   Out[1]: (C) sklearn.tree.DecisionTreeClassifier

(iii) Combine the two:

  In [1]: len(list(wallk('/')))
   NameError                                 Traceback (most recent call last)
   <ipython-input-6-666d043cbf71> in <module>()
   ----> 1 len(list(wallk('/')))

   NameError: name 'wallk' is not defined
   Did you mean to import:
   os.walk

Installation
------------

Run:

   ```pip install git+https://github.com/drorspei/ipython-suggestions  # from Github```

then append the output of ``python -m ipython_suggestions``
to the output of ``ipython profile locate`` (typically
``~/.ipython/profile_default/ipython_config.py``).
