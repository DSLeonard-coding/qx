```text
Provides qx callable to run shell commands with subprocess.run

Closest we can get to perl/shell bakcticks (command-line execution), but better.
Includes optional log-level control for stdout,stderr and echoing the cmd
as well as a simple messaging interface piggy-backing on that.  

qx(<cmd>,<optional args>):  
    Requied arguments:  
    <cmd>   The shell command to execute and arguments, all as a single string or list of strings.  

    Example usage, interpretted as if entered in sequence:  
    qx(["echo", "Hello"])        :   runs "echo" command with "Hello" argument.  By defalt, displays output.  
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
    Same as 2 but set verbose=<LEVEL> on each call to differntiate which calls will have output at each threshold.
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
    out_lvl : Optional[int] = qx.DEBUG    # if >=  qx.out_thrsh,   
                                            #   cmd stdout is printed   
    err_lvl     : Optional[int] =  None   # if >= qx.err_thrsh,  
                                            #   stderr is printed.  
    echo_lvl    : Optional[int] =  None       # if >= qx.echo_thrsh,  
                                            #   the <cmd> is printed.  
    verbose     : Optional[int]  = None    #  Sets all output levels                                        
    pretend : bool None                   #  Can override class attribute to force command to  
                                            #  run even if qx.pretend == True.  

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
    verbose_thrsh  int = NONE    # Just an alias to set all three above thresholds  

    NOTE: Unset options are set to out_thrsh after out_thrsh is set or defaulted.  


    Threshold aliases, names are intentionally a little different  
    Since the use is for important command output, not necessarily warnings and errors.  
    qx.NEVER = 0       # Stuff that should never be output, makes sense in context of 3 channels of output.  
    qx.TRACE = 10      # Things to print at high versobisty  
    qx.DEBUG = 20      # Debugging iformation  
    qx.INFO = 30       # Stanardard  
    qx.PRIORITY = 40   # Only High Priority messages, ex: warnings.  
    qx.CRITICAL = 50   # For fatal errors for example  
    qx.HIGHEST = 100   # Probably no messages should have this level.  
                        # So setting the threshold to HIGHEST can produce silence.  
                        # But that is not enforced.  

qxv(...)  
    Just a shortcut to qx but with verbose = True by default.  

Messaging Functions:  (built on command echoing and level system above)  
msg(msg,**kwargs)  

takes an optional verbose or echo_lvl arg and prints msg.  
verbosity default = INFO.

dbg(msg)  

Prints DEBUG: {msg} at level <= qx.DEBUG and exits  

warn(msg)  

Prints WARNING: {msg} at level <= qx.PRIORITY  

error(msg)  

Prints FATAL ERROR: {msg} at level <= qx.CRITICAL and exits  

trace(msg)  

Prints Trace: {msg} at level <= qx.TRACE and exits  
```

### Installation

Directly from git:
```
pip install https://gitlab.com/douglas.s.leonard/qx/-/archive/master/qx-master.tar
```
or from your clone's root directory:
```
pip install .
```
from a python script requiring it you could garuantee installation this way at the top:

```python
def install(package, ver: Optional[str] = None, source=None):
    ''' version requires a comparator and value, ex: ">1.0"'''
    if source is None:
        source = package
    try:
        temp_pkg = __import__(package)
        if ver:
            if not eval(f'"{{{temp_pkg}.__version__}}" "{ver}"'):
                raise Exception()
    except:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", source])


if __name__ == "__main__":
    install("qx", source="https://gitlab.com/douglas.s.leonard/qx/-/archive/v1/qx-v1.tar", ver=">=1.1")
```