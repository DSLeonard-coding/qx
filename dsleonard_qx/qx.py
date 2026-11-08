# Douglas S. Leonard 2023
# MIT expat license
""" Provides qx callable to run shell commands with subprocess.run

Closest we can get to perl/shell bakcticks (command-line execution), but better.
Includes optional log-level control for stdout,stderr and echoing the cmd
as well as a simple messaging interface piggy-backing on that.

See included README.md for full details
"""

import subprocess
import sys
from typing import List, Optional, Union

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
        self.errlines : List [str] = (self.stderr or '').splitlines()  # can't splitlines with None


    @property
    def rstripped(self) -> str:
        """stdout without trailing whitespace; '' if there was no output.
        It's good for string assignment that needs empty to be \"\" """
        return (self.stdout or '').rstrip()

#Can't do inheritance easily as subclasses.  Define inheritted helpers here, instantiate in Qx:

class Warn:
    prefix = "WARNING: "

    def __init__(self, qx_instance):
        self.qx = qx_instance
        self.level = self.qx.PRIORITY

    @classmethod
    def end(cls):  # stub for inheritted functionality
        pass

    def __call__(self, cmd: Union[str, List[str]]):
        if isinstance(cmd, list):
            cmd = [f"{self.prefix}"]+cmd
        elif isinstance(cmd, str):
            cmd = self.prefix+cmd
        output: qx_out = self.qx(
            cmd,
            out_lvl=self.qx.NEVER,
            err_lvl=self.qx.NEVER,
            echo_lvl=self.level,
            pretend=True
        )
        self.end()
        return output


class Error(Warn):
    prefix = "FATAL ERROR: "
    def __init__(self, qx_instance):
        super().__init__(qx_instance)
        self.level = self.qx.CRITICAL

    @classmethod
    def end(cls):
        raise Qx.Fatal("     Fatal Error....")

class Dbg(Warn):
    prefix = "DEBUG: "
    def __init__(self, qx_instance):
        super().__init__(qx_instance)
        self.level = self.qx.DEBUG


class Trace(Warn):  # For very detailed output
    prefix = "Trace: "
    def __init__(self, qx_instance):
        super().__init__(qx_instance)
        self.level = self.qx.TRACE

class Qx:  # lower case because it mostly behaves like a function.


    # Stuff that should never be output, makes sense in context of 3 channels of output.
    NEVER = 0
    TRACE = 10      # Things to print at high versobisty
    DEBUG = 20      # Debugging iformation
    INFO = 30       # Stanardard
    PRIORITY = 40   # Only High Priority messages, ex: warnings.
    CRITICAL = 50   # For fatal errors for example
    HIGHEST = 100   # Probably no messages should have this level.
    # So setting the threshold to HIGHEST can produce silence.
    # But that is not enforced.
    _OUT_LVL_DEFAULT = DEBUG
    _out_thrsh: int = INFO  # Threshold for output of stdout/stderr
    _echo_thrsh: int = INFO  # Threshold for printing command to stdout
    _err_thrsh: int = INFO  #


    def __init__(self, out_lvl=None, echo_lvl=None, err_lvl=None, pretend=None):
        #  Thresholds are global, levels are instance
        # Document default output levels for commands, overrideable on each call:
        self._out_lvl: int
        self._echo_lvl: Optional[int]
        self._err_lvl: Optional[int]
        self._pretend: Optional[bool]

        # Real initialization is here:
        self.defaults(out_lvl, echo_lvl, err_lvl, pretend)

        # Instance-bound messaging helpers
        self.warn = Warn(self)
        self.error = Error(self)
        self.dbg = Dbg(self)
        self.trace = Trace(self)

    class Fatal(Exception):
        pass

    def expose(self):
        """Automatically injects msg, warn, error, dbg, and trace into the caller's module globals."""
        caller_globals = sys._getframe(1).f_globals
        g = sys._getframe(1).f_globals
        for name in ("msg", "qxv", "warn", "error", "dbg", "trace"):
            g[name] = getattr(self, name)
        return self

    @classmethod
    def verbosity_thresholds(cls, verbose_thrsh: Optional[int] = None, out_thrsh: Optional[int] = None,
                             echo_thrsh: Optional[int] = None, err_thrsh: Optional[int] = None) -> None:
        """Sets global verbosity thresholds for qx output"""
        cls._out_thrsh = (verbose_thrsh if verbose_thrsh is not None
                          else out_thrsh if out_thrsh is not None else cls._out_thrsh)
        cls._echo_thrsh = (verbose_thrsh if verbose_thrsh is not None
                           else echo_thrsh if echo_thrsh is not None else cls._out_thrsh)
        cls._err_thrsh = (verbose_thrsh if verbose_thrsh is not None
                          else err_thrsh if err_thrsh is not None else cls._out_thrsh)

    def defaults(self, out_lvl: Optional[int] = None, echo_lvl: Optional[int] = None,
                 err_lvl: Optional[int] = None, pretend: Optional[bool] = None) -> 'Qx':
        """ Sets defatuls for qx including output levels"""
        self._out_lvl = out_lvl if out_lvl is not None else self._OUT_LVL_DEFAULT
        self._err_lvl = err_lvl
        self._echo_lvl = echo_lvl
        self._pretend = pretend
        return self

    def __call__(self, cmd: Union[str, List[str]], verbose: Optional[int] = None, out_lvl: Optional[int] = None,
                 err_lvl: Optional[int] = None, echo_lvl: Optional[int] = None, pretend: Optional[bool] = None,
                 echo_end="\n\n",
                 **kwargs
                 ) -> qx_out:  #
        """ This does the work, no instance is made """
        run: bool = True  # run the command
        pretend = pretend if pretend is not None else self._pretend
        # Prioritize direct arg, then verbose arg, then default.
        # err_lvl will fall_back to out_lvl if nothing is set (including a default)
        out_lvl = (
            out_lvl if out_lvl is not None
            else verbose if verbose is not None
            else self._out_lvl
        )
        err_lvl = (
            err_lvl if err_lvl is not None
            else verbose if verbose is not None
            else self._err_lvl if self._err_lvl is not None
            else out_lvl  # already set above, not None now.
        )
        echo_lvl = (
            echo_lvl if echo_lvl is not None
            else verbose if verbose is not None
            else self._echo_lvl if self._echo_lvl is not None
            else out_lvl # already set above, not None now.
        )
        if pretend: # don't print empty output
            out_lvl = self.NEVER
            err_lvl = self.NEVER

        do_print = False
        print_cmd = False
        print_err = False
        is_shell = isinstance(cmd,str)
        if pretend:
            run = False
        if out_lvl >= self._out_thrsh:
            do_print = True
        if echo_lvl >= self._echo_thrsh:
            print_cmd = True
        if err_lvl >= self._err_thrsh:
            print_err = True
        if print_cmd:
            shown = cmd if isinstance(cmd, str) else " ".join(
                '"' + w.replace('"', r'\"') + '"' for w in cmd)
            print(shown, end=echo_end)
        if run:
            output: 'subprocess.CompletedProcess[str]' = subprocess.run(
                cmd, capture_output=True,text=True,shell=is_shell,
                **kwargs
            )
        else:
            output = subprocess.CompletedProcess(cmd, 0)
        # replace None outputs with empty strings
        output = qx_out.from_CompletedProcess(output)
        # FIXME:  We need popen above and two async reader threads here
        # This solution is kind of a quick hack
        if do_print and output.stdout:
            sys.stdout.write(output.stdout+"\n")
            sys.stdout.flush()
        if print_err and output.stderr:
            sys.stderr.write(output.stderr+"\n")
            sys.stderr.flush()
        return (output)

    def qxv(self, cmd: Union[str, List[str]], out_lvl=CRITICAL, err_lvl=CRITICAL) -> 'qx_out':  #
        """
           A shorthand wrapper for qx to pass through (print) stdout and stderr
        """
        output: qx_out = self(cmd, out_lvl=out_lvl, err_lvl=err_lvl)
        return output

    def msg(self, cmd: str, verbose: Optional[int] = None, echo_lvl: Optional[int] = None):
        echo_lvl = echo_lvl if echo_lvl is not None else verbose if verbose is not None else Qx.INFO
        output: 'subprocess.CompletedProcess[str]' = self(cmd, echo_lvl=echo_lvl, pretend=True, out_lvl=Qx.NEVER,
                                                        err_lvl=Qx.NEVER,echo_end="\n")
        return output

#Export a default singleton and helper aliases for backward compatibility:
qx = Qx()
qxv = qx.qxv
msg = qx.msg
warn = qx.warn
error = qx.error
dbg = qx.dbg
trace = qx.trace
