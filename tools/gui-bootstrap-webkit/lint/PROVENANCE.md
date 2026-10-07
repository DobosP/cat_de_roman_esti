# Fleet documentation checker provenance

check_docs.py is unchanged from agent-ops commit
4a29c2f69e026171164d5a665b60df8fddd84d99, path scripts/check_docs.py.
SHA-256: 33dc3903c5919c3ae523d8cd994295a8e0c56ea9f166a9545f5ceefc8ff10583.
docs_gate.py enumerates Markdown without Git then invokes its scan and
find_orphans functions, preserving its historical-file pattern.
