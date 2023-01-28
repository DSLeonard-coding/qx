A call-only static class (glorified function) shortcut to run shell commands with subprocess.run

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

### Installation

Directly from git:
```
pip install https://gitlab.com/douglas.s.leonard/qx/-/archive/master/qx-master.tar
```
or from your clone's root directory:
```
pip install .
```
from a python script requiring it you can garuantee installation this way at the top:

```python
import subprocess  
def install(package,source=None):
    if source is None:
        source=package
    try:
        __import__(package)
    except:
        subprocess.check_call([sys.executable, "-m", "pip", "install", source])

if __name__ == "__main__":
    install("qx","https://gitlab.com/douglas.s.leonard/qx/-/archive/v1/qx-v1.tar")
