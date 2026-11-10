# dsleonard-qx  
Provides qx callable to run shell commands with subprocess.run; Includes logging.  
---

Closest we can get to perl/shell backticks (command-line execution), but better.

Includes optional log-level control for stdout,stderr and echoing the cmd
as well as a simple messaging interface piggybacking on that.

Levels are fixed traits that describe the importance of the output of a line of code, a command (or message), for all three of stdout, stderr, and echoing the command.  Thresholds decide the level of importance that the app wants to show.  Defaults exist for both but default levels should usually be set and known when the code is written, not changed later.  You change the thresholds. 

### Installation

If you're depending on source builds, in my opinion, you need to be using the uv package manager.  It has about 30% more usage at PyPI than pip now, is faster, has many advantages, and it makes source dependency conflicts reasonable to solve in reproducible ways, particularly as the lock file automates reproducible builds of each commit.  Source overrides are also nice.  I will not try to write instructions for pip. 

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



## Quick Usage 
```code
qx(<cmd>,<optional args>,<passthrough args>)

    Required arguments:
    <cmd>   The shell command to execute and arguments, all as a single string or list of strings.
```

### Example usage (interpreted as if entered in sequence):
```code
    from dsleonard_qx import *  #uses global qx with immutable defaults.
    
    # The master level to set what output levels print.
    # Only the top-level app should call this. 
    # Uncommenting this would allow DEBUG output to print: 
    # Qx.verbosity_thresholds(verbose_thrsh=Qx.DEBUG)    
    
    qxv(["echo", "Hello"])        :   runs "echo" command with "Hello" argument.  By default, displays output.
        (  an alias for qx(["echo", "Hello"],out_lvl=qx.CRITICAL  )
 
    x = qx("echo Hello").stdout  :   same, and stores output ("Hello") in x.
    qx(f"echo say {x}")          :   runs "echo" command with arguments "say Hello".
    Qx.verbosity_thresholds(pretend=True); qx(f"echo say {x}")  
                            : prints full command "echo say Hello" to screen
                              without running it.  This is meant to temporarily
                              disable running commands,  and print them instead
                              msg() is better for just printing a message.
    
    x = qx("ls -1").lines        :   collects file names as a list in x.
    msg("Hello")                 :  Prints hello to screen, if verbose_thrsh <= INFO.
    dbg("You are here.")         :  Prints "DEBUG: You are here." if verbose_thrsh <= DEBUG. (see others below)
```

### USE CASES from simplest to advanced:
    from dsleonard_qx import *  # Note: imports qx.qx to qx

1) Default:  
Just use qx(<cmd>).  Commands will be run, with output available in the return value.
2) Dead-Simple:  
Same as 1 but at start of main() call qx.verbosity_thresholds(qx.DEBUG) to print all commands and outputs.
3) Easy:  
Same as 2 but set verbose=<LEVEL> on each call to differentiate which calls will have
    output at each threshold. See level aliases below.
4) Advanced:  
For more control set out_lvl, echo_lvl, and err_lvl independently on each call, This controls the command stdout level, stderr level, and echo (the command itself) level.
Both err_lvl and echo_lvl will track out_lvl if they are not explicitly set on each call 
to qx, if a default was not set for them, and if verbose is not passed.  verbose also.  Nothing overrides explicit sets.
    
### Return value (via call to qx() ):
   a qx_out object, an extended CompletedProcess,  with attributes of: stdout, stderr, 
   returncode, args, and check_returncode(). Also includes lines and errlines list attributes with output lines split and
   newlines removed. These always contain at least an empty list, not None.  
   It also contains rstripped, the stdout with right side stripped of white space.  
   Finally the return object is truthy, True like for exit 0 (success), False for failure. 
 
### Args:    

Aside from those shown, qx accepts **kwargs and passes them through to subprocess.run, except for text and capture.  Those will error.
 
qx uses a typical log-level system for output verbosity for printing the command itself and its
stdout and stderr, with independent controls for all three or simplified combined controls. (See USE CASES below)
Each call optionally sets the "importance" level for all three outputs, with defaults defined on the qx instance.  The resolved levels are compared to the corresponding
global threshold settings that are then increased and decreased to adjust which things will be output.

```
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
    prefix      : Optional[str] = None      # Prefix text for logging all output text except 
                                            # for INFO level.  
                                            # Usually better to set it in instance defaults
    
    Passthrough args:
        All unprocessed args now passed through to subprocess


    For each call...
    err_lvl will be set to the first non-None value in the list:
                err_lvl, verbose, out_lvl, qx._err_lvl (instance default) 
    echo_lvl will be set to the first non-None value in:
                echo_lvl, verbose, qx._echo_lvl (instance default)
    out_lvl will be set to the first non-None value in:
                out_lvl, verbose, qx._out_lvl (if modified), DEBUG (initial default)
    If nothing is set, everything defaults to DEBUG via fallback through out_lvl,
    and no output will be emitted unless the thresholds are also raised to at least DEBUG.
    pretend will be set to pretend if not None, or else False.
```

defaults can be set with q.defaults but not on the default instance.  See [More about instances](#instantiation-libraries-prefixes-and-defaults) below, but this should not be considered as a way to modify global output anyway. It doesn't modify call sites with explicit settings. Defaults just exist to help define the call sites more easily.  They are defaults, not modifiers.   

What you can modify is the global output thresholds. In the future we might get thresholds per each "prefix"(generally a package)

```
qx.verbosity_thresholds(verbose_thrsh, out_thrsh=None,err_thrsh=None,echo_thrsh=None,):
    Sets the following verbosity levels (with initial values):

    out_thrsh:     int = INFO    # Threshold for output of stdout
    err_thrsh:     int = INFO    # Threshold for output of stderr
    echo_thrsh:    int = INFO    # Threshold for printing command to stdout
    verbose_thrsh:  default: None    # Just an alias to set all three above thresholds

    NOTE: Unset options are set to out_thrsh after out_thrsh is set or defaulted.


    Threshold aliases, names are intentionally a little different than usual,
    since the use is for importance of command output, not necessarily warnings and errors.
    Qx.NEVER = 0       # Stuff that should never be output, makes sense in context of 3 channels of output.
    Qx.TRACE = 10      # Things to print at high verbosity
    Qx.DEBUG = 20      # Debugging information
    Qx.INFO = 30       # Standard
    Qx.PRIORITY = 40   # Only High Priority messages, ex: warnings.
    Qx.CRITICAL = 50   # For fatal errors for example
    Qx.HIGHEST = 100   # Probably no messages should have this level.
                        # So setting the threshold to HIGHEST can produce silence.
                        # But that is not enforced.
```
### Helper functions, including messging/logging:
```
The following methods are all essentially aliases for qx with different settings.
They all

qx.qxv(...)
    Just a shortcut to qx but with verbose = Qx.CRITICAL by default.

Messaging Functions:  (built on command echoing and level system above)
qx.msg(msg,**kwargs)

takes an optional verbose or echo_lvl arg and prints msg.
verbosity default = INFO.

qx.dbg(msg)

Prints DEBUG: {msg} at threshold <= Qx.DEBUG and exits

qx.warn(msg)

Prints WARNING: {msg} at threshold <= Qx.PRIORITY

qx.error(msg)

Prints FATAL ERROR: {msg} at threshold <= Qx.CRITICAL, and (always) raises an exception.

qx.trace(msg)

Prints Trace: {msg} at threshold <= Qx.TRACE and exits
```

## Instantiation, libraries, prefixes, and defaults

By default, qx creates a single qx instance and provides helper names in your scope to access its methods.  The instance holds the output levels The global class holds the thresholds.  Thresholds should generally only be set by an app.  

The instances also hold the default prefix name used to prefix output at all levels except for INFO. For apps, the default empty prefix is probably fine.  Libraries can create an instance and set the prefix to the package name. 

Helper methods actually exist on an instance and must be to use the prefix value in their output.

You cannot edit the prefix or default output levels on the default instance, but you can if you make a new instance.

You can instantiate instances in your libraries to avoid passing around qx objects and/or to set different default output level policies.

```python
from dsleonard_qx  import Qx

qx=Qx(out_lvl=Qx.INFO,prefix="ourlib: ") # if most of your output is for standard use.
```
This creates a new Qx instance, sets the level defaults, and assigns the instance to qx.

### Accessing instance helpers
Note that we did not import *.  We don't want the default helper methods.  They won't know the prefix of our instance. We have a couple of ways to get our instance helpers. **In a quick script you can do:**
```python
qx=Qx().export_helpers() # for quick scripts only
```
This dumps all the helper names in your module namespace, but it's a quick hack.  Editors like pycharm won't understand it.  It's better to do:
```python
from dsleonard_qx  import Qx
qx=Qx() 
msg, dbg, warn, error = qx.msg, qx.dbg, qx.warn, qx.error  # trace, and qxv also available
```
**Be careful not to import * when creating an instance or** you can get a mix of explicit and default helpers from different instances, with different prefixes. export_helpers() is slightly safer in that sense, but the rule stands, import Qx for intances. Apps can freely * important if they are using the default empty prefix, and need no instance if they are not modifying output defaults. 

If you are in an app, you can also do this just as before, but you shouldn't do it in a library.  The runner controls the output, libraries just offer levels and should not interfere with output controls. 
```
Qx.verbosity_thresholds(verbose_thrsh=Qx.DEBUG) 
```
You can call through though qx instance or the Qx class.  Qx makes it more clear.
If you want to share one instance through a project you could do it in a _qx.py 

```python
import os
from dsleonard_qx import Qx  # type: ignore
qx = Qx(prefix="mylib: ")
msg, dbg, warn, error, trace, qxv = qx.msg, qx.dbg, qx.warn, qx.error, trace, qxv

__all__ = ['qx', 'msg', 'dbg', 'warn', 'error']
```
and then use ``` from ._qx import *``` in your modules, but note that overriding defaults in a hidden location can cause confusion. There's a strong case for making an instance with the same prefix in every module if you are adjusting default levels. 

## QX_DEBUG QX_PRETEND and Environment variables

You can set verbose_thrsh and enable global PRETEND mode from environment variables.
```QX_DEBUG_ALL``` and `QX_PRETEND_ALL` set `=1` (or anything non falsey) will enable debug mode (all thresholds set to DEBUG unless already lower) and PRETEND mode (all calls will run in pretend unless explicitly set to false at call site)  for all qx instances/prefixes.  PRETEND implies DEBUG.

Likewise `QX_PREFIX_DEBUG` enables DEBUG for one prefix, converted to uppercase, with starting and trailing _ and specia characters removed. and `QX_DEBUG` is the same for the default empty prefix (often top level app) but NOT all other prefixes. The same pattern works for PRETEND.  This avoids a lot of env parsing 

Aside from DEBUG, PRETEND and ALL, the keywords OUT, ERR, ECHO, and VERBOSE now follow the same pattern  QX_\<OPTIONAL:PREFIX_>KEYWORD  but take values or level names for thresholds.  These will be applied only if they lower the threshold, ie you cannot reduce output from the environment variables.  The same precedence rules apply as in QX(), defaults(), or verbosity_thrsh()