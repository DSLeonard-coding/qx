import warnings
from dsleonard_qx import *
warnings.warn(
"\n[REBRAND] The 'qx' package has been renamed to 'dsleonard_qx'.\n"
"Please update your code to: 'import dsleonard_qx'\n"
"This shim will be removed in a future version.",
category=FutureWarning,
stacklevel=2
)
