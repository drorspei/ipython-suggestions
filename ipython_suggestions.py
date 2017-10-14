"""Get suggestions on misspelled names, and do system wide symbol searching.

To activate, pip-install and append the output of `python -m i python_suggestions`
to `~/.ipython/profile_default/ipython_config.py`.
"""

import builtins
import os
import sys
import re
from collections import defaultdict
import traceback
import string
import itertools

from IPython.core.display import display

try:
    import _ipython_suggestions_version
except ImportError:
    from pip._vendor import pkg_resources
    __version__ = pkg_resources.get_distribution("ipython-suggestions").version
else:
    __version__ = _ipython_suggestions_version.get_versions()["version"]


_var_name_chars = string.ascii_letters + string.digits + '_.'
_builtins = set(dir(builtins))
_symbols_cache = defaultdict(lambda: defaultdict(dict))


def on_exception(ipython, etype, value, tb, tb_offset=None):
    ipython.showtraceback()
    source = traceback.extract_tb(tb)[-1].line

    if etype == NameError:
        suggest_name(ipython.user_ns, source, str(value))
    elif etype == AttributeError:
        suggest_attr(ipython.user_ns, source, str(value))


def suggest_name(user_ns, source, value):
    m = re.match("^(?:global )?name '(.*)' is not defined$", value)
    if not m:
        return
    attr = m.group(1)
    insert_word = lambda word: word
    index = source.find(attr)
    if index == -1 or source.find(attr, index + 1) != -1:
        return

    suggestions = list(unique(itertools.chain(close_words(attr, user_ns),
                                              close_words(attr, _builtins))))
    if suggestions:
        print("Did you mean:")
        for word in suggestions:
            new_source = source[:index + 1] + word + source[index + len(attr) + 1:]
            display(SuggestionWord(word, new_source))


def suggest_attr(user_ns, source, value):
    import pdb; pdb.set_trace()
    m = re.search("(object|module '.*') has no attribute '(.*)'$", value)
    if not m:
        return
    attr = m.group(2)
    index = source.find('.' + attr)
    if index == -1 or source.find('.' + attr, index + 1) != -1:
        return
    line = source[:index]
    varname = get_last_name(line)
    try:
        lst = dir(eval(varname, user_ns))
    except:
        return

    suggestions = list(unique(itertools.chain(close_words(attr, lst),
                                              close_words(attr, _builtins))))
    if suggestions:
        print("Did you mean:")
        for word in suggestions:
            new_source = source[:index + 1] + word + source[index + len(attr) + 1:]
            display(SuggestionWord(word, new_source))


class SuggestionWord(object):
    def __init__(self, word, source):
        self.word = word
        self.source = source

    def __repr__(self):
        return self.word

    def _repr_html_(self):
        return '<a href="#">%s</a>' % self.word


def load_ipython_extension(ipython):
    ipython.set_custom_exc((NameError, AttributeError), on_exception)


def unload_ipython_extension(ipython):
    ipython.set_custom_exc((), None)


###############################################################################


def close_deletions(word, all_words):
    for i in range(len(word)):
        w = word[:i] + word[i+1:]
        if w in all_words:
            yield w


def close_transposes(word, all_words):
    for i in range(len(word) - 1):
        w = word[:i] + word[i+1] + word[i] + word[i+2:]
        if w in all_words:
            yield w


def close_insertions(word, all_words):
    for w in all_words:
        for i in range(len(w)):
            if w[:i] + w[i+1:] == word:
                yield w


def close_substitutions(word, all_words):
    for w in all_words:
        for i in range(len(w)):
            if w[:i] + w[i+1:] == word[:i] + word[i+1:]:
                yield w


def close_words(word, all_words):
    return itertools.chain(close_deletions(word, all_words),
                           close_transposes(word, all_words),
                           close_insertions(word, all_words),
                           close_substitutions(word, all_words))


def close_cached_symbol(word):
    return itertools.chain(close_deletions(word, _symbols_cache[len(word) - 1]),
                           close_transposes(word, _symbols_cache[len(word)]),
                           close_insertions(word, _symbols_cache[len(word) + 1]),
                           close_substitutions(word, _symbols_cache[len(word)]))


def unique(it):
    seen = set()
    for w in it:
        if w not in seen:
            seen.add(w)
            yield w

###############################################################################

def get_last_name(line):
    index = len(line) - 1
    stack = []
    while index >= 0:
        ch = line[index]
        ls = stack[-1] if stack else ''
        if ls == '"' or ls == "'":
            if ch == ls:
                stack[-1:] = []
        else:
            if ch in '"\'':
                stack.append(ch)
            elif ch == ']':
                stack.append('[')
            elif ch == '[':
                if ls == '[':
                    stack[-1:] = []
                else:
                    break
            elif ch == '}':
                stack.append('{')
            elif ch == '{':
                if ls == '}':
                    stack[-1:] = []
                else:
                    break
            elif ch == '(':
                break
            elif ch == ')':
                return
            elif line[index-2:index+1] == 'for' and ls in '[{':
                return
            elif ch not in _var_name_chars and not stack:
                break
        index -= 1
    return line[index + 1:]


###############################################################################


if __name__ == "__main__":
    if os.isatty(sys.stdout.fileno()):
        print("""\
# Please append the output of this command to the
# output of `ipython profile locate` (typically
# `~/.ipython/profile_default/ipython_config.py`)
""")
    print("""\
c.InteractiveShellApp.exec_lines.append(
    "try:\\n    %load_ext ipython_suggestions\\nexcept ImportError: pass")""")
