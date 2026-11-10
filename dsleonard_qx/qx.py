# Douglas S. Leonard 2023
# MIT expat license
""" Provides qx callable to run shell commands with subprocess.run

Closest we can get to perl/shell bakcticks (command-line execution), but better.
Includes optional log-level control for stdout,stderr and echoing the cmd
as well as a simple messaging interface piggy-backing on that.

See included README.md for full details
"""
import warnings
import subprocess
import sys
from typing import List, Optional, Union, NamedTuple
import functools
import os, re

__all__ = [
    # Core execution
    "qx",
    "Qx",
    "qx_out",
    "qxv",
    "msg",
    "warn",
    "error",
    "dbg",
    "trace",
]


class qx_out(subprocess.CompletedProcess):
    """
    Like a CompletedProcess, holds results of process, but sanitized a little
    stdout and std err are in Lists with lines broken and newlines stripped.
    Now is also bool, truthy on success!
    """

    def __init__(self, args: List[str], returncode: int, stdout=None, stderr=None):
        super().__init__(args, returncode, stdout, stderr)
        self.extend()

    def __bool__(self) -> bool:
        return self.returncode == 0

    @classmethod
    def from_CompletedProcess(cls, proc: subprocess.CompletedProcess) -> 'qx_out':
        """Build directly from a CompletedProcess, the primary use"""
        output = cls(args=proc.args, stdout=proc.stdout,
                     stderr=proc.stderr, returncode=proc.returncode)
        return (output)

    def extend(self) -> None:
        """ extends the CompletedProcess with sanitized output """
        self.lines: List[str] = (self.stdout or '').splitlines()  # can't splitlines with None
        self.errlines: List[str] = (self.stderr or '').splitlines()  # can't splitlines with None

    @property
    def rstripped(self) -> str:
        """stdout without trailing whitespace; '' if there was no output.
        It's good for string assignment that needs empty to be \"\" """
        return (self.stdout or '').rstrip()

def _beats(*items):
    for x in items[:-1]:
        if x is not None:
            return x
    return items[-1]

class Inputs(NamedTuple):
    verbose: Optional[int]
    out: Optional[int]
    echo: Optional[int]
    err: Optional[int]
    pretend: Optional[bool]

class Values(NamedTuple):
    out: int = 0
    echo: int = 0
    err: int = 0
    pretend: bool = 0


def _merge(baseline: Values, verbose=None, out=None, echo=None, err=None, pretend=None) -> Values:
    """Specific beats general; out cascades to err, fallback to baseline."""
    return Values(
        err=_beats(err, verbose, out, baseline.err),
        echo=_beats(echo, verbose, baseline.echo),
        out=_beats(out, verbose, baseline.out),
        pretend=_beats(pretend, baseline.pretend)
    )


class Qx:
    # Stuff that should never be output, makes sense in context of 3 channels of output.
    NEVER = 0
    TRACE = 10  # Things to print at high versobisty
    DEBUG = 20  # Debugging iformation
    INFO = 30  # Stanardard
    PRIORITY = 40  # Only High Priority messages, ex: warnings.
    CRITICAL = 50  # For fatal errors for example
    HIGHEST = 100  # Probably no messages should have this level.
    # So setting the threshold to HIGHEST can produce silence.
    # But that is not enforced.
    _thrsh_defaults = Values(
        out=INFO, # Threshold for output of stdout/stderr
        echo=INFO, # Threshold for printing command to stdout
        err=INFO,
        pretend=False
    )
    _thrsh = _thrsh_defaults
    _OUT_LVL_DEFAULT = DEBUG

    def __init__(self,
                 out_lvl=None,
                 echo_lvl=None,
                 err_lvl=None,
                 prefix=None
                 ):
        #  Thresholds are global, levels are instance
        # Document default output levels for commands, overrideable on each call:
        self._out_lvl: int
        self._echo_lvl: Optional[int]
        self._err_lvl: Optional[int]
        self._prefix: str = ""

        # Real initialization is here:
        self.defaults(out_lvl, echo_lvl, err_lvl, prefix)

    def defaults(self,
                 out_lvl: Optional[int] = None,
                 echo_lvl: Optional[int] = None,
                 err_lvl: Optional[int] = None,
                 prefix: Optional[str] = None,
                 pretend: Optional[bool] = None,
                 ) -> 'Qx':
        """ Sets defatuls for qx including output levels"""
        self._out_lvl = _beats(out_lvl, self._OUT_LVL_DEFAULT)
        self._err_lvl = _beats( err_lvl, self._OUT_LVL_DEFAULT)
        self._echo_lvl = _beats(echo_lvl, self._OUT_LVL_DEFAULT)
        self._prefix = _beats( prefix, self._prefix, "")
        if pretend is not None:
            raise TypeError("The 'pretend' option has moved to Qx.verbosity_thresholds(pretend=<value>), \n"
                            "as it is a run-environment setting, not an instance setting.\n")
        return self

    class Fatal(Exception):
        pass

    def export_helpers(self, into=None):
        ns = _beats(into, sys._getframe(1).f_globals )
        ns.update(msg=self.msg, warn=self.warn, error=self.error,
                  dbg=self.dbg, trace=self.trace, qxv=self.qxv)
        return self


    @classmethod
    def verbosity_thresholds(cls,
                             #allow parameter pack or int in first slot:
                             #so we can accept a prior get_verbosity_thresholds output directly
                             verbose_thrsh: Optional[Union[Values, tuple, int]] = None,
                             out_thrsh: Optional[int] = None,
                             echo_thrsh: Optional[int] = None,
                             err_thrsh: Optional[int] = None,
                             pretend: Optional[bool] = None
                             ) -> None:
        #if pack provided, recurse on unpacked parameters:
        if isinstance(verbose_thrsh,(list,tuple)):
            return cls.verbosity_thresholds(*verbose_thrsh)
        else:
            inputs= (verbose_thrsh,out_thrsh,echo_thrsh,err_thrsh, pretend)
            Qx._thrsh = _merge(Qx._thrsh_defaults,*inputs)


    @staticmethod
    def _env_key(real_prefix: str) -> str:
        # "mytool: " -> "MYTOOL"; "" -> "" (default, so only QX_DEBUG applies)
        return re.sub(r'\W+', '_', real_prefix).strip('_').upper()

    _FALSE = {"", "0", "false", "no", "off"}

    @classmethod
    def _levels(cls) -> dict:
        # NEVER, TRACE, DEBUG, ... derived from the class so they can't drift
        # A little fragile if other public class constants get added.
        return {k: v for k, v in vars(Qx).items()
                if k.isupper() and not k.startswith('_') and isinstance(v, int)}

    @classmethod
    def _env_raw(cls, real_prefix: str, suffix: str):
        """(name, value) of the most specific var that's set, else (None, None)."""
        key = cls._env_key(real_prefix)
        specific = f"QX_{key}_{suffix}" if key else f"QX_{suffix}"
        for name in (specific, f"QX_{suffix}_ALL"):
            if name in os.environ:
                return name, os.environ[name]
        return None, None

    @classmethod
    def _env_flag(cls, real_prefix: str, suffix: str) -> Optional[bool]:
        name, val = cls._env_raw(real_prefix, suffix)
        if name is None:
            return None
        return val.strip().lower() not in cls._FALSE

    @classmethod
    def _env_level(cls, real_prefix: str, suffix: str) -> Optional[int]:
        """None = unset (or empty); otherwise an int level."""
        name, val = cls._env_raw(real_prefix, suffix)
        if name is None or not val.strip():
            return None
        v = val.strip()
        try:
            return int(v)
        except ValueError:
            pass
        try:
            return cls._levels()[v.upper()]
        except KeyError:
            raise ValueError(f"{name}={val!r}: expected an integer or one of "
                             f"{', '.join(cls._levels())}") from None


    @classmethod
    def _prefixed(cls, text: str, lvl: int, prefix: str) -> str:
        if lvl == cls.INFO or not prefix:
            return text
        return "".join(prefix + line for line in text.splitlines(keepends=True))

    @classmethod
    def _resolve(cls, real_prefix: str, call_pretend: Optional[bool] = None) -> Values:
        """Effective thresholds: globals, then env, then per-call pretend."""
        env = [cls._env_level(real_prefix, s)
               for s in ("VERBOSITY", "OUT", "ECHO", "ERR")]
        t = _merge(cls._thrsh, *env, pretend=call_pretend)
        # Env can only turn pretend on.
        if cls._env_flag(real_prefix, "PRETEND"):
            t = t._replace(pretend=True)

        # TRACE implies DEBUG, so the lower cap wins.
        cap = (cls.TRACE if cls._env_flag(real_prefix, "TRACE")
               else cls.DEBUG if cls._env_flag(real_prefix, "DEBUG")
        else None)
        if cap is not None:
            t = t._replace(out=min(t.out, cap),
                           echo=min(t.echo, cap),
                           err=min(t.err, cap))
        return t

    @property
    def pretend(self) -> bool:
        return self._resolve(self._prefix).pretend

    @property
    def debug(self):
        return self.DEBUG >= self._resolve(self._prefix).out

    @property
    def get_verbosity_thresholds(self):
        return self._thrsh

    @classmethod
    def _do_it(cls,
               cmd: Union[str, List[str]],
               out_lvl: int,
               err_lvl: int,
               echo_lvl: int,
               echo_end,
               prefix: str,
               real_prefix: str,
               pretend: bool = None,
               **kwargs
               ) -> qx_out:
        t = cls._resolve(real_prefix, pretend)
        run = not t.pretend
        do_print = out_lvl >= t.out
        print_cmd = echo_lvl >= t.echo
        print_err = err_lvl >= t.err

        is_shell = isinstance(cmd, str)
        if print_cmd:
            shown = cmd if isinstance(cmd, str) else " ".join(
                '"' + w.replace('"', r'\"') + '"' for w in cmd)
            print(cls._prefixed(shown, echo_lvl, prefix), end=echo_end)
        if run:
            output: 'subprocess.CompletedProcess[str]' = subprocess.run(
                cmd, capture_output=True, text=True, shell=is_shell,
                **kwargs
            )
        else:
            output = subprocess.CompletedProcess(cmd, 0)
        # replace None outputs with empty strings
        output = qx_out.from_CompletedProcess(output)
        # FIXME:  We need popen above and two async reader threads here
        # This solution is kind of a quick hack
        if do_print and output.stdout:
            sys.stdout.write(cls._prefixed(output.stdout, out_lvl, prefix) + "\n")
            sys.stdout.flush()
        if print_err and output.stderr:
            p = prefix + "! "
            sys.stderr.write(cls._prefixed(output.stderr, err_lvl, p) + "\n")
            sys.stderr.flush()
        return (output)

    def __call__(self,
                 cmd: Union[str, List[str]],
                 verbose: Optional[int] = None, out_lvl: Optional[int] = None,
                 err_lvl: Optional[int] = None, echo_lvl: Optional[int] = None,
                 pretend: Optional[bool] = None,
                 echo_end="\n\n", prefix: Optional[str] = None,
                 **kwargs
                 ) -> qx_out:  #
        prefix = prefix if prefix is not None else self._prefix
        # Prioritize direct arg, then verbose arg, then default.
        # err_lvl will fall_back to out_lvl if nothing is set (including a default)
        inputs = Inputs(verbose, out_lvl, echo_lvl, err_lvl, pretend)
        defaults = Values(self._out_lvl, self._echo_lvl, self._err_lvl)
        values = _merge(defaults,*inputs)

        return self._do_it(cmd, values.out, values.err, values.echo, pretend=values.pretend,
                           echo_end=echo_end, prefix=prefix, real_prefix=self._prefix, **kwargs)

    def _emit(self, text, lvl, prefix, tag):
        p = _beats(prefix, self._prefix) + tag
        t = self._resolve(self._prefix)
        if lvl >= t.out:
            print(self._prefixed(text, lvl, p))

    def qxv(self, cmd, prefix=None, **kwargs):
        """Run cmd, passing through (printing) stdout and stderr."""
        p = _beats(prefix, "")
        return self._do_it(cmd, out_lvl=self.CRITICAL, err_lvl=self.CRITICAL,
                           echo_lvl=self.CRITICAL, echo_end="\n\n", prefix=p, real_prefix=self._prefix, **kwargs)

    def msg(self, cmd, verbose=None, echo_lvl=None, prefix=None):
        lvl = _beats(echo_lvl, verbose, Qx.INFO)
        return self._emit(cmd, lvl, prefix, "")

    def warn(self, cmd, prefix=None):
        return self._emit(cmd, Qx.PRIORITY, prefix, "WARNING: ")

    def dbg(self, cmd, prefix=None):
        return self._emit(cmd, Qx.DEBUG, prefix, "DEBUG: ")

    def trace(self, cmd, prefix=None):
        return self._emit(cmd, Qx.TRACE, prefix, "TRACE: ")

    def error(self, cmd, prefix=None):
        self._emit(cmd, Qx.CRITICAL, prefix, "FATAL ERROR: ")
        raise Qx.Fatal("     Fatal Error....")


class _FrozenQx(Qx):
    """The shared Qx is now immutable"""
    _frozen = False

    def defaults(self, *a, **kw):
        if self._frozen:
            raise TypeError("The shared qx can't be reconfigured; \n"
                            "create your own: qx = Qx(...)\n")
        return super().defaults(*a, **kw)

    def __setattr__(self, name, value):
        if self._frozen:
            raise AttributeError("The shared qx is immutable")
        super().__setattr__(name, value)


qx = _FrozenQx()
qx._frozen = True
# default prefixless helpers:
msg, dbg, trace, warn, error, qxv = (qx.msg, qx.dbg, qx.trace, qx.warn, qx.error, qx.qxv)
