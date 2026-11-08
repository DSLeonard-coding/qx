# dsleonard-qx  
Provides qx callable to run shell commands with subprocess.run; Includes logging.  
---

Closest we can get to perl/shell backticks (command-line execution), but better.
Includes optional log-level control for stdout,stderr and echoing the cmd
as well as a simple messaging interface piggybacking on that.

### Installation

If you're depending on source builds, in my opinion, you need to be using the uv package manager.  It has about 30% more usage at PyPi than pip now, is faster, has many advantages, and it makes source dependency conflicts reasonable to solve in reproducible ways, particularly as the lock file automates reproducible builds of each commit.  Source overrides are also nice.  I will not try to write instructions for pip. 

### Install uv if you don't have it
```
curl -LsSf https://astral.sh/uv/install.sh | sh    # or with pip:  pip install pipx; pip install uv
```

### Use in your custom library or app
If you don't have a project structure configured for your app, use the [quick script](#use-in-a-quick-script) instructions below,
or launch a new uv-based project in a few seconds with [dsleonard-pylaunch](www.github.com/DSLeonard-coding/dsleonard-pylaunch)

To use dsleonard-qx in your Python program, cd to your working directory or project directory, if it's already a  project, and just do:
```bash
uv add "dsleonard-qx @ git+https://github.com/DSLeonard-coding/qx.git"
uv sync   # redundant here actually.
uv run myscript.py

```
for private repos replace ```git+https://```   with ```git+ssh://git@``` to use ssh authentication.

After using uv add for source deps you are locked in to using uv as your package manager for your app going forward.  



### Use in a quick script:
The --script option will embedd the dependencies to the top of your script, avoiding the need for a pyproject.toml
```bash
uv add --script myscript.py "dsleonard-qx @ git+https://github.com/DSLeonard-coding/qx.git"
```
Then add the following uv shebang as the first line in your script file:
```sh
#!/usr/bin/env -S uv run --script
```
and just after the ```uv add```:
```bash
./myscript.py
```

Or if you don't like the shebang, leave it out and run with uv manually with
```bash
uv run --python 3.13 myscript.py    # the --python <version> is optional
```

However, if you want today's version of your script to always run with today's tested dependencies, 
you need to commit it with an extra lock file anyway, made with:

```bash
uv lock --script myscript.py
```
Don't worry, future commits can be re-locked to updated dependencies.  It just makes sure
that every commit works the same as the day you committed it.



## Usage 
```code
qx(<cmd>,<optional args>,<passthrough args>)

    Required arguments:
    <cmd>   The shell command to execute and arguments, all as a single string or list of strings.

    Example usage, interpreted as if entered in sequence:
    from dsleonard_qx import *
    # The master level on the app to let DEBUG output through, etc:
    #qx.verbosity_thresholds(verbose_thrsh=Qx.DEBUG)    #commented for the example
    
    qxv(["echo", "Hello"])        :   runs "echo" command with "Hello" argument.  By default, displays output.
        (  same as qx(["echo", "Hello"],out_lvl=qx.HIGHEST  )
    x = qx("echo Hello").stdout  :   same, and stores output ("Hello") in x.
    qx(f"echo say {x}")          :   runs "echo" command with arguments "say Hello".
    qx.defaults(pretend=True); qx(f"echo say {x}")  : prints full command "echo say Hello" to screen
                                                      without running it.  This is meant to temporarily
                                                      disable running commands,  and print them instead
                                                     msg() is better for just printing a message.
    x = qx("ls -1").lines        :   collects file names as a list in x.
    msg("Hello")                 :  Prints hello to screen, if verbosity <= INFO.
    dbg("You are here.")         :  Prints "DEBUG: You are here." if verbosity <= DEBUG. (see others below)

    USE CASES from simplest to advanced:
    from qx import *  # Note: imports qx.qx to qx

    1) Default:
    Just use qx(<cmd>).  Commands will be run, with output available in the return value.

    2) Dead-Simple:
    Same as 1 but at start of main() call qx.verbosity_thresholds(qx.DEBUG) to print all commands and outputs.

    3) Easy:
    Same as 2 but set verbose=<LEVEL> on each call to differentiate which calls will have output at each threshold.
    See level aliases below.

    4) Advanced:
    For more control just call qx.defaults(out_lvl=qx.<X>,echo_lvl=qx.<Y>), not err_lvl,
    and  then err_lvl will track out_lvl for per-call adjustments (because it has no default).
    Actually this is true even without setting defaults at all, but then you get the default default of DEBUG
    and both err_lvl and echo_lvl will track out_lvl if they are not explicitly set on each call to qx

    Return value (via call to qx() ):
    a qx_out object, an extended CompletedProcess,  with attributes of: stdout, stderr, returncode, args,
    and check_returncode(). Also includes lines and errlines list attributes with output lines split and
    newlines removed. These always contain at least an empty list, not None.

    qx uses a typical log-level system for output verbosity for printing the command itself and its
    stdout and stderr, with independent controls for all three or simplified combined controls. (See USE CASES below)
    Each call optionally sets the "importance" level for all three outputs which are compared to the corresponding
    global threshold settings that are then increased and decreased to adjust which things will be output.

    Optional args with initial defaults:
    out_lvl : Optional[int] = qx.DEBUG      # if >=  qx.out_thrsh,
                                            #   cmd stdout is printed
    err_lvl     : Optional[int] =  None     # if >= qx.err_thrsh,
                                            #   stderr is printed.
    echo_lvl    : Optional[int] =  None     # if >= qx.echo_thrsh,
                                            #   the <cmd> is printed.
    verbose     : Optional[int]  = None     #  Sets all output levels
    pretend : bool None                     #  Can override class attribute to force command to
                                            #  run even if qx.pretend == True.

    Passthrough args:
        All unprocessed args now pass through to subprocess

    Default values are set with qx.defaults().
    For each call...
    err_lvl will be set to the first non-None value in the list:
                err_lvl, verbose, qx.err_lvl (class default), out_lvl
    echo_lvl will be set to the first non-None value in:
                echo_lvl, verbose, qx.echo_lvl (class default), out_lvl
    out_lvl will be set to the first non-None value in:
                out_lvl, verbose, qx.out_lvl (if modified), DEBUG (initial default),
    If nothing is set, everything defaults to DEBUG via fallback through out_lvl,
    and no output will be emitted unless the thresholds are also raised to at least DEBUG.


qx.verbosity_thresholds(verbose_thrsh, out_thrsh=None,err_thrsh=None,echo_thrsh=None,):
    Sets the following verbosity levels (with initial values):

    out_thrsh:     int = INFO    # Threshold for output of stdout
    err_thrsh:     int = INFO    # Threshold for output of stderr
    echo_thrsh:    int = INFO    # Threshold for printing command to stdout
    verbose_thrsh:  default: None    # Just an alias to set all three above thresholds

    NOTE: Unset options are set to out_thrsh after out_thrsh is set or defaulted.


    Threshold aliases, names are intentionally a little different than usual,
    since the use is for importance of command output, not necessarily warnings and errors.
    qx.NEVER = 0       # Stuff that should never be output, makes sense in context of 3 channels of output.
    qx.TRACE = 10      # Things to print at high verbosity
    qx.DEBUG = 20      # Debugging information
    qx.INFO = 30       # Standard
    qx.PRIORITY = 40   # Only High Priority messages, ex: warnings.
    qx.CRITICAL = 50   # For fatal errors for example
    qx.HIGHEST = 100   # Probably no messages should have this level.
                        # So setting the threshold to HIGHEST can produce silence.
                        # But that is not enforced.

qxv(...)
    Just a shortcut to qx but with verbose = Qx.CRITICAL by default.

Messaging Functions:  (built on command echoing and level system above)
msg(msg,**kwargs)

takes an optional verbose or echo_lvl arg and prints msg.
verbosity default = INFO.

dbg(msg)

Prints DEBUG: {msg} at threshold <= Qx.DEBUG and exits

warn(msg)

Prints WARNING: {msg} at threshold <= Qx.PRIORITY

error(msg)

Prints FATAL ERROR: {msg} at threshold <= Qx.CRITICAL and exits

trace(msg)

Prints Trace: {msg} at threshold <= Qx.TRACE and exits
```

## Instantiation and qx in libraries within apps

By default, qx creates a single qx instance and provides helper names in your scope to access its methods.  The instance holds the output levels, and the global class holds the thresholds.  Thresholds should generally only be set by an app.

You can instantiate instances in your libraries to avoid passing around qx objects and/or to set different default output level policies.

```python
from dsleonard_qx  import Qx

qx=Qx().defaults(out_lvl=Qx.INFO).expose()  # if most of your output is for standard use.
```
This creates a new Qx instance, sets the level defaults, exposes the helper methods to your namespace, and assigns the instance to qx.

You omit .expose() and you'd just use qx.msg("Hello") instead of msg("Hello")

Then, as before, within an app you set the verbosity of the app:
```
qx.verbosity_thresholds(verbose_thrsh=Qx.DEBUG) 
```
