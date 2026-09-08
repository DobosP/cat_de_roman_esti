# First full V89 backend run

Valid until: V89 is superseded — then treat as history.

The original Python3.12 run completed with **1,530 passed /one failed** in913.36seconds.
The exact failed receipt/log and407-input freeze are preserved here. The failure is
`test_every_proxy_anchor_reaches_every_selectable_unique_target`: its historical
pre-V88 sink assertions incorrectly included the newly selected Mop target, already
reachable within the old cleaning component. All26 proxy anchors reached all236 current
targets before this assertion failed. No application, fixture or frontend change is
required. Final backend runs follow the independently reviewed historical test correction.
