import codecs
import pygments.lexers
import re
import types

from pygments.lexer import inherit

def dq(x):
    if isinstance(x, str) or isinstance(x, unicode):
        return '"%s"' % "".join([esc(y) for y in x])
    elif isinstance(x, list) or isinstance(x, tuple):
        return "[" + ", ".join([dq(y) for y in x]) + "]"
    else:
        raise Exception("Cannot dq: %s" % repr(x))

def rr(x):
    # in a range?
    in_range = False

    # just after an opening [? (implies in_range)
    opened = False

    # next character escaped?
    escaped = False

    sane = ""

    # fix up []foo[] as [\]foo\[]
    for c in x:
        if c == '[' and not escaped:
            if in_range:
                sane += '\\'
            else:
                in_range = True
                opened = True
        elif c == ']' and not escaped:
            if opened:
                sane += '\\'
            elif in_range:
                in_range = False
        elif c == '\\':
            escaped = not escaped
            opened = False
        else:
            escaped = False
            opened = False

        sane += c

    # replace (?s) with (?m)
    sane = re.sub(r"\(\?([a-z]*)s([a-z]*)\)", r"(?\1m\2)", sane)

    return rq(sane)

def rq(x):
    if isinstance(x, str) or isinstance(x, unicode):
        return '"%s"' % "".join([reg_esc(y) for y in x])
    elif isinstance(x, list) or isinstance(x, tuple):
        return "[" + ", ".join([rq(y) for y in x]) + "]"
    else:
        raise Exception("Cannot rq: %s" % repr(x))

def esc(c):
    if c == '"':
        return '\\"'
    elif c == '\\':
        return '\\\\'
    elif ord(c) in range(32, 126):
        return c
    else:
        return "\\%s" % ord(c)

def reg_esc(c):
    if c == '"':
        return '\\"'
    elif c == '#': # interpolation
        return '\\#'
    elif ord(c) in range(32, 126):
        return c
    else:
        return "\\%s" % ord(c)

def convertible(states):
    if "root" not in states:
        print("no root state")
        return False

    for name, toks in states.items():
        if isinstance(toks, dict):
            if convertible(toks) == False:
                print("toks was unconvertible dict")
                return False

            continue

        for tok in toks:
            if isinstance(tok, str):
                continue

            if tok == inherit:
                print("cannot handle inherit")
                return False

            if not token_convertible(tok[1]):
                print("token not convertible: %s" % tok[1])
                return False

    return True

def token_convertible(tok):
    if isinstance(tok, tuple):
        return True

    if not (type(tok) is types.FunctionType \
            and tok.__name__ == "callback" \
            and tok.__closure__):
        return False

    closures = [x.cell_contents for x in tok.__closure__]

    # bygroups()
    if isinstance(closures[0], tuple) \
        and all([token_convertible(x) for x in tok.__closure__[0].cell_contents]):
        return True

    # using(this)
    if len(closures) == 2 \
        and isinstance(closures[0], dict) \
        and isinstance(closures[1], dict):
        return True

    # using()
    if len(closures) == 3 \
        and isinstance(closures[0], dict) \
        and hasattr(closures[2], "__name__") \
        and closures[2].__name__ in pygments.lexers.LEXERS:
        return True

    return False

def convert_state(all, name, toks):
    if isinstance(toks, str):
        return convert_state(all, toks, all.get(toks))

    ctoks = [
        convert_token(*x)
            if not isinstance(x, str)
            else "any-of(%s)" % convert_name(x)
        for x in toks
    ]

    if isinstance(toks, dict):
        conv = [convert_state(toks, x, toks.get(x)) for x in toks]
        more = "".join(["\n  " + x for x in conv])
    else:
        more = ""

    return """lex(%s):%s
  %s
""" % (convert_name(name), more, "\n  ".join(ctoks))

def convert_token(regexp, type, next = None):
    if next:
        return "r%s is(%s) -> %s" % (rr(regexp), convert_type(type), convert_next(next))
    else:
        return "r%s is(%s)" % (rr(regexp), convert_type(type))

def convert_type(t):
    if isinstance(t, tuple):
        return ".".join([x.lower() for x in list(t)])
    elif isinstance(t, str):
        return t.lower()
    elif type(t) is types.FunctionType and t.__closure__:
        if isinstance(t.__closure__[0].cell_contents, tuple):
            return "by-groups(" + ", ".join([convert_type(x) for x in t.__closure__[0].cell_contents if x]) + ")"
        elif len(t.__closure__) == 2:
            return "using(self class)"
        elif len(t.__closure__) == 3:
            # TODO
            return "using(" + convert_modname(t.__closure__[2].cell_contents.__name__) + ")"
    else:
        #return "TODO"
        raise Exception("Could not convert: %s" % repr(t))

def convert_next(n):
    if not n:
        return "continue"
    elif isinstance(n, pygments.lexer.combined):
        states = list(n)
        #states.reverse()
        return "combined(" + ", ".join([convert_name(x) for x in states]) + ")"
    elif isinstance(n, tuple):
        # silly reversed stacks, pah.
        states = list(n)
        #states.reverse()
        return "do-all(" + ", ".join([convert_next(x) for x in states]) + ")"
    elif n == "#pop":
        return "pop"
    elif n[0:4] == "#pop":
        return "pop(" + n[5:] + ")"
    elif n == "#push":
        return "push"
    else:
        return "go-to(" + convert_name(n) + ")"

def convert_lexer(mod, name, aliases, filenames, mimetypes, flags):
  return """use("atomy")
use("hl/define")

Lexer = lexer:
name: %s
aliases: %s
extensions: %s
mimetypes: %s
start: .root
flags: %s

""" % (dq(name), dq(aliases), dq([convert_filename(x) for x in filenames]),
       dq(mimetypes), convert_flags(flags))

def convert_filename(fn):
    return fn.replace("*", "")

def convert_modname(mod):
    return mod.replace("Lexer", "")

def convert_name(s):
    return s[0] + s[1:].replace("_", "-").replace(" ", "-") # TODO: mangle?

def convert_flags(f):
    options = []

    while True:
        if f == 0:
            break

        if f & re.IGNORECASE:
            options.append("Regexp IGNORECASE")
            f = f ^ re.IGNORECASE
        elif f & re.LOCALE:
            f = f ^ re.LOCALE
        elif f & re.MULTILINE:
            f = f ^ re.MULTILINE
        elif f & re.DOTALL:
            options.append("Regexp MULTILINE") # yes, really
            f = f ^ re.DOTALL
        elif f & re.UNICODE:
            f = f ^ re.UNICODE
        elif f & re.VERBOSE:
            f = f ^ re.VERBOSE

    if len(options) == 0:
      return "0"
    else:
      return " | ".join(options)

def try_converting(k, l, to = "lib/hl/lexers/imported"):
    cls = pygments.lexers.__getattr__(k)
    if not issubclass(cls, pygments.lexer.RegexLexer) \
            or not hasattr(cls, 'tokens'):
        return False

    if not convertible(cls.tokens):
        return False

    print("converting %s" % k)

    mod = codecs.open("%s/%s.ay" % (to, convert_modname(k).lower()), encoding="utf-8", mode="w")

    name, aliases, filenames, mimetypes = l[1:]

    mod.write(convert_lexer(k, name, aliases, filenames, mimetypes, cls.flags))

    for name, state in cls.tokens.items():
        mod.write(convert_state(cls.tokens, name, state) + "\n")

    return True

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        print(try_converting(sys.argv[1], pygments.lexers.LEXERS.get(sys.argv[1])))
        exit()

    for k, l in pygments.lexers.LEXERS.items():
        if try_converting(k, l):
            print("converted %s" % k)
        else:
            print("could not convert %s" % k)
