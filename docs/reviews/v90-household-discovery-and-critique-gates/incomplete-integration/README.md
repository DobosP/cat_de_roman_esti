# Incomplete V90 Python3.14 attempt

Valid until: V90 is superseded — then treat as history.

The first full Python3.14 process ended with observed shell exit143 before a pytest
completion summary. No full passing receipt was produced; its progress dots are not
counted as a successful suite. The cause is not established. Original raw output,
runner and frozen inputs are preserved losslessly in [the receipt](receipt.json).

Run the unchanged test command again separately after the other backend completes.
The wrapper will print periodic progress so long runs remain observable. That changes
only monitoring, never tests, assertions, resource bounds or the application inputs.
