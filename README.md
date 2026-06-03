
# pycli.py

This is a little piece of python boilerplate to get a command line program off to a good start.

* option parsing with `optparse`
* testing with `doctest`
* automatic manual generation with `pydoc`
* responds appropriately to CLI options:
    - --man
    - --doctest
    - --version
    - --verbose
    - --help

## Self-install (optional sidecar)

`selfinstall.py` ships alongside `pycli.py` and gives any tool built from it a small lifecycle —
`install` / `uninstall` / `update` / `status` — by **symlinking the checkout onto `PATH`**
(`~/.local/bin`). Because it's a symlink, `<tool> update` (a `git pull`) makes the new version
instantly live — ideal for tools that evolve under their developer's hands.

It's wired via a graceful optional import, so a fork that deletes `selfinstall.py` (and the few
marked lines) is still pure, self-contained `pycli`. To enable it in a new tool: copy
`selfinstall.py` next to your script, keep the import shim + the `maybe()` guard at the top of
`main()`, and `.gitignore __pycache__/`.

## Versioning

SemVer **plus a build-date metadata tag**: `MAJOR.MINOR.PATCH+YYYYMMDD` (the `+…` is ignored for
precedence — a human "when"). Bump both together on every change.
