import subprocess


class qx:  # lower case because it mostly behaves like a function.
    """ A call-only static class (glorified function) shortcut to run shell commands with subprocess.run
    
    Closest we can get to perl/shell bakcticks, but better.
    
    Parameters:
    cmd:  a string command or a list with command and args separated..

    Returns (via call to qx() ):
    CompletedProcess,  with attributes of: stdout, stderr, returncode, args, and check_returncode()

    Class (static) attributes:
    qx.verbose: bool=False  :  Print all commands to the screen
    qx.pretend: bool=False  :  Only print commands, don't run them. 

    Example usage:
    qx(["echo", "Hello"])        :   prints "Hello" to screen using echo command
    x = qx("echo Hello").stdout  :   prints "Hello" to screen and stores "Hello" in x. 
    qx(f"echo say {x}")          :   prints "say Hello" to screen
    qx.pretend=True; qx(f"echo say {x}")  :   prints  "echo say Hello" to screen.
    """

    verbose: bool = False
    pretend: bool = False
    def __new__(cls, cmd):  #
        """ This does the work, no instance is made """
        if type (cmd) is list:
            shell = False
            if qx.verbose or qx.pretend:
                print (*cmd, "\n")
        else:
            shell = True
            if qx.verbose or qx.pretend:
                print (cmd, "\n")
        if not qx.pretend:
            output = subprocess.run(cmd, capture_output = True, shell = shell, text = True)
            return output
        else:
            return subprocess.CompletedProcess(cmd, 0)


# Note A stack exchange answer on this: https://stackoverflow.com/questions/279561/what-is-the-python-equivalent-of-static-variables-inside-a-function
# suggests a callable class object using __call__  and gets good reviews, so why not a callable class itself and skip instantiation.  
# This is just better. And less fuss than validating **kwargs in a function.
# Could just use global module variables, but setup and use is slightly messier.
