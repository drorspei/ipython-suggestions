"""Get suggestions on misspelled names, and do system wide symbol searching.

To activate, pip-install and append the output of `ipython -m ipython_suggestions`
to `~/.ipython/profile_default/ipython_config.py`.
"""

from __future__ import print_function
import builtins
import os
import sys
import re
import traceback
import string
import itertools
import bisect
import time
from collections import defaultdict
from threading import Thread
from inspect import isclass
import token

from IPython.utils import PyColorize
from IPython import get_ipython
from IPython.display import display
from IPython.core.magic import register_line_magic
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring

from super_greedy_complete import super_greedy_complete

_var_name_chars = string.ascii_letters + string.digits + "_."
_builtins = set(dir(builtins))

_symbols_cache = defaultdict(lambda: defaultdict(dict))
_symbols_sorted = None
_symbols_running = False
_symbols_error = False
_symbols_last = None


def on_exception(ipython, etype, value, tb, tb_offset=None):
    ipython.showtraceback()
    source = traceback.extract_tb(tb)[-1][-1]

    if etype == NameError:
        suggest_name(ipython.user_ns, source, str(value))
    elif etype == AttributeError:
        suggest_attr(ipython.user_ns, source, str(value))


def suggest_prefix(self, event):
    global _symbols_cache, _symbols_sorted
    ret = []
    key = event.symbol.split("...")[0]
    if _symbols_sorted is not None and key:
        i = bisect.bisect_left(_symbols_sorted, key)
        j = bisect.bisect_right(_symbols_sorted, key[:-1] + chr(ord(key[-1]) + 1))
        for word in _symbols_sorted[i:j]:
            for _, modulepath in _symbols_cache[len(word)][word]:
                ret.append("%s...%s" % (word, modulepath))
    return sorted(ret)


def suggest_name(user_ns, source, value):
    global _symbols_error, _symbols_running, _symbols_last

    m = re.match("^(?:global )?name '(.*)' is not defined$", value)
    if not m:
        return
    attr = m.group(1)
    insert_word = lambda word: word
    index = source.find(attr)
    if index == -1 or source.find(attr, index + 1) != -1:
        return

    suggestions = list(
        unique(
            itertools.chain(close_words(attr, user_ns), close_words(attr, _builtins))
        )
    )

    symbols_last = []

    if suggestions:
        print("Did you mean:")
        for i, word in enumerate(suggestions):
            symbols_last.append(
                ("fill", source[:index] + word + source[index + len(attr) :])
            )
            print(i, word)

    if not _symbols_error and not _symbols_running:
        suggestions = close_cached_symbol(attr, False)
        if suggestions:
            print("Found the following symbols:")
            for i, (suggestion, code) in enumerate(suggestions, len(symbols_last)):
                print(i, suggestion)
                symbols_last.append(("exec", code))

    if symbols_last:
        _symbols_last = symbols_last


def suggest_attr(user_ns, source, value):
    global _symbols_last
    m = re.search("(object|module '.*') has no attribute '(.*)'$", value)
    if not m:
        return
    attr = m.group(2)
    index = source.find("." + attr)
    if index == -1 or source.find("." + attr, index + 1) != -1:
        return
    line = source[:index]
    varname = get_last_name(line)
    try:
        lst = dir(eval(varname, user_ns))
    except:
        return

    suggestions = list(
        unique(itertools.chain(close_words(attr, lst), close_words(attr, _builtins)))
    )
    if suggestions:
        _symbols_last = []
        print("Did you mean:")
        for i, word in enumerate(suggestions):
            newword = source[: index + 1] + word + source[index + len(attr) + 1 :]
            _symbols_last.append(("fill", newword))
            print(i, word)


# Magic registration only works in ipython, and we don't
# need it if we're in "__main__".
if __name__ != "__main__":

    @register_line_magic
    @magic_arguments()
    @argument("-as", dest="as_", type=str, default=None)
    @argument(
        "-e",
        dest="exact",
        action="store_const",
        const=True,
        default=False,
        help="If given the symbol search is exact. "
        "Otherwise, the search allows two character edits.",
    )
    @argument("symbol", type=str, help="Symbol to search for.")
    def findsymbol(arg):
        global _symbols_running, _symbols_error, _symbols_last

        if _symbols_error:
            print("ipython-suggestions had an error while scanning.")
            return

        if _symbols_running:
            print("ipython-suggestions is still scanning symbols...")
            return

        args = parse_argstring(findsymbol, arg)

        if args.as_ is not None:
            as_ = " as %s" % args.as_
        else:
            as_ = ""

        if "..." in args.symbol:
            try:
                name, modulepath = args.symbol.split("...")
                if modulepath == "":
                    line = "import %s%s" % (name, as_)
                else:
                    line = "from %s import %s%s" % (modulepath, name, as_)
            except:
                print("An error occured when trying to import symbol.")
            else:
                shell = get_ipython()

                try:
                    sys.stdout._raw = True
                except AttributeError:
                    pass
                cs = PyColorize.Parser().color_table[shell.colors].colors
                print(
                    "{}Suggestions:{} {}".format(cs[token.NUMBER], cs["normal"], line)
                )

                shell.execution_count += 1
                shell.run_cell(line, store_history=True)
            return

        suggestions = close_cached_symbol(args.symbol, args.exact)
        if suggestions:
            _symbols_last = []
            print("Found the following symbols:")
            for i, (suggestion, code) in enumerate(suggestions):
                print(i, suggestion + as_)
                _symbols_last.append(("exec", code + as_))
        else:
            print("Didn't find symbol.")

    @register_line_magic
    @magic_arguments()
    @argument("suggestion_index", type=int, help="Index of suggestion to execute.")
    def suggestion(arg):
        global _symbols_last
        args = parse_argstring(suggestion, arg)
        if -len(_symbols_last) < args.suggestion_index < len(_symbols_last):
            method, line = _symbols_last[args.suggestion_index]
            if method == "exec":
                shell = get_ipython()

                try:
                    sys.stdout._raw = True
                except AttributeError:
                    pass
                cs = PyColorize.Parser().color_table[shell.colors].colors
                print(
                    "{}Suggestions:{} {}".format(cs[token.NUMBER], cs["normal"], line)
                )

                shell.execution_count += 1
                shell.run_cell(line, store_history=True)
            elif method == "fill":
                get_ipython().set_next_input(line)
        else:
            print("Invalid suggestion index.")


def load_ipython_extension(ipython):
    ipython.set_custom_exc((NameError, AttributeError), on_exception)
    ipython.set_hook("complete_command", suggest_prefix, str_key="%findsymbol")
    ipython.set_hook("complete_command", super_greedy_complete, re_key=".*")
    thread = Thread(target=inspect_all_objs)
    thread.daemon = True
    thread.start()


def unload_ipython_extension(ipython):
    global _symbols_cache, _symbols_running, _symbols_error, _symbols_last
    _symbols_cache = defaultdict(lambda: defaultdict(dict))
    _symbols_sorted = None
    _symbols_running = False
    _symbols_error = False
    _symbols_last = None
    ipython.set_custom_exc((), None)


def inspect_all_objs():
    global _symbols_cache, _symbols_sorted, _symbols_running, _symbols_error

    _symbols_running = True

    try:
        visited = set()
        defclass = re.compile(r"(class|def) ([_A-z][_A-z0-9]*)[\(:]")
        variable = re.compile(r"([A-z][_A-z0-9]+)\s=")
        objs = defaultdict(dict)

        rootmodules = list(sys.builtin_module_names)
        for name in rootmodules:
            objs[name][("module", name)] = ("builtin", 0)
            m = __import__(name)
            for attr in dir(m):
                a = getattr(m, attr)
                if isclass(a):
                    objs[attr][("class", name)] = ("builtin", 0)
                elif callable(a):
                    objs[attr][("def", name)] = ("builtin", 0)

        for path in sys.path:
            if path == "":
                path = "."

            if os.path.isdir(path):
                for root, dirs, nondirs in os.walk(path):
                    if "-" in root[len(path) + 1 :] or root in visited:
                        dirs[:] = []
                        continue

                    visited.add(root)

                    for name in nondirs:
                        if name.endswith(".py"):
                            filepath = os.path.join(root, name)

                            if name == "__init__.py":
                                name = root[len(path) + 1 :].split("/")[-1]
                                modulepath = ".".join(
                                    root[len(path) + 1 :].split("/")[:-1]
                                )
                            else:
                                name = name[:-3]
                                modulepath = root[len(path) + 1 :].replace("/", ".")

                            if modulepath.endswith("."):
                                modulepath = modulepath[:-1]

                            if ("module", modulepath) not in objs[name]:
                                objs[name][("module", modulepath)] = (filepath, 0)

                                try:
                                    with open(filepath, "r") as f:
                                        for i, line in enumerate(f):
                                            if modulepath:
                                                fullpath = "%s.%s" % (modulepath, name)
                                            else:
                                                fullpath = name

                                            m = defclass.match(line)
                                            if m:
                                                t, sym = m.groups()
                                                objs[sym][(t, fullpath)] = (filepath, i)
                                            else:
                                                m = variable.match(line)
                                                if m:
                                                    objs[m.group(1)][
                                                        ("var", fullpath)
                                                    ] = (filepath, i)
                                except:
                                    pass

        for word, value in objs.items():
            _symbols_cache[len(word)][word] = value

        _symbols_sorted = sorted(sum(map(list, _symbols_cache.values()), []))
    except:
        _symbols_error = True
    finally:
        _symbols_running = False


###############################################################################


def close_deletions(word, all_words):
    if len(word) > 1:
        for i in range(len(word)):
            w = word[:i] + word[i + 1 :]
            if w in all_words:
                yield w


def close_transposes(word, all_words):
    for i in range(len(word) - 1):
        w = word[:i] + word[i + 1] + word[i] + word[i + 2 :]
        if w in all_words:
            yield w


def close_insertions(word, all_words):
    for w in all_words:
        for i in range(len(w)):
            if w[:i] + w[i + 1 :] == word:
                yield w


def close_substitutions(word, all_words):
    for w in all_words:
        for i in range(len(w)):
            if w[:i] + w[i + 1 :] == word[:i] + word[i + 1 :]:
                yield w


def close_words(word, all_words):
    return itertools.chain(
        close_deletions(word, all_words),
        close_transposes(word, all_words),
        close_insertions(word, all_words),
        close_substitutions(word, all_words),
    )


def unique(it):
    seen = set()
    for w in it:
        if w not in seen:
            seen.add(w)
            yield w


def close_cached_symbol(word, exact):
    suggestions = []

    if not exact and len(word) >= 3:
        words = unique(
            itertools.chain(
                close_deletions(word, _symbols_cache[len(word) - 1]),
                close_transposes(word, _symbols_cache[len(word)]),
                close_insertions(word, _symbols_cache[len(word) + 1]),
                close_substitutions(word, _symbols_cache[len(word)]),
            )
        )
    elif word in _symbols_cache[len(word)]:
        words = [word]
    else:
        words = []

    for word in words:
        for (t, modulepath), (filepath, linenum) in _symbols_cache[len(word)][
            word
        ].items():
            if t == "module":
                if filepath not in ["builtin", ""]:
                    tag = "M"
                else:
                    tag = "BM"

                if modulepath == "" or filepath == "builtin":
                    suggestions.append(
                        ("(%s) import %s" % (tag, word), "import %s" % word)
                    )
                else:
                    suggestions.append(
                        (
                            "(%s) from %s import %s" % (tag, modulepath, word),
                            "from %s import %s" % (modulepath, word),
                        )
                    )
            else:
                if t == "class":
                    tag = "C"
                elif t == "def":
                    tag = "F"
                else:  # t == 'var'
                    tag = "V"

                suggestions.append(
                    (
                        "(%s) from %s import %s" % (tag, modulepath, word),
                        "from %s import %s" % (modulepath, word),
                    )
                )

    return sorted(suggestions, key=lambda key: key[1])


###############################################################################


def get_last_name(line):
    index = len(line) - 1
    stack = []
    while index >= 0:
        ch = line[index]
        ls = stack[-1] if stack else ""
        if ls == '"' or ls == "'":
            if ch == ls:
                stack[-1:] = []
        else:
            if ch in "\"'":
                stack.append(ch)
            elif ch == "]":
                stack.append("[")
            elif ch == "[":
                if ls == "[":
                    stack[-1:] = []
                else:
                    break
            elif ch == "}":
                stack.append("{")
            elif ch == "{":
                if ls == "}":
                    stack[-1:] = []
                else:
                    break
            elif ch == "(":
                break
            elif ch == ")":
                return
            elif line[index - 2 : index + 1] == "for" and ls in "[{":
                return
            elif ch not in _var_name_chars and not stack:
                break
        index -= 1
    return line[index + 1 :]


###############################################################################


if __name__ == "__main__":
    if os.isatty(sys.stdout.fileno()):
        print(
            """\
# Please append the output of this command to the
# output of `ipython profile locate` (typically
# `~/.ipython/profile_default/ipython_config.py`)
"""
        )
    print(
        """\
c.InteractiveShellApp.exec_lines.append(
    "try:\\n    %load_ext ipython_suggestions\\nexcept ImportError: pass")"""
    )
