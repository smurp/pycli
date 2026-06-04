#!/usr/bin/env python3
# Version scheme: SemVer + build-date  ->  MAJOR.MINOR.PATCH+YYYYMMDD  (KEEP BOTH CURRENT)
__version__ = "0.2.0+20260604"
"""selfinstall — drop-in install/update lifecycle for pycli-style single-file tools.

Ships with pycli; COPY it next to any single-file tool (it stays self-contained / auditable) and
the tool gains four commands, all operating on the tool's OWN checkout:

  <tool> install [--bindir DIR]   symlink the checkout into a bindir (default ~/.local/bin),
                                  then warn (with the fix) if that dir isn't on PATH
  <tool> uninstall                remove that symlink (only if it points at this tool)
  <tool> update                   `git pull` the tool's own checkout; the symlink makes the
                                  pulled version instantly live. Refuses on a dirty tree.
  <tool> status                   where it's linked from, version, and ahead/behind origin

The symlink points at the REPO file, so editing/pulling the checkout updates the live command with
no reinstall — the point of an ecosystem of tools evolving under their developer's hands.

WIRE-UP  (a few lines; the tool still works if selfinstall.py is absent)
  At the top of the tool, after its stdlib imports:
      import os, sys
      sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))  # find a sibling selfinstall
      try: import selfinstall
      except ImportError: selfinstall = None
  As the first thing in main():
      if selfinstall:
          rc = selfinstall.maybe(sys.argv, __file__, __version__)
          if rc is not None: return rc
  (The subcommand must come first: `tool install`, not `tool -v install`.)
"""
import os, shutil, subprocess, sys

COMMANDS = ("install", "uninstall", "update", "status")
DEFAULT_BINDIR = "~/.local/bin"
DISPATCH_PREFIX = "boydstrap"   # tools also install as `<prefix>-<name>` so the `boydstrap` dispatcher finds them (git-plugin style)

# ---------- pure helpers (doctested: `python3 -m doctest selfinstall.py -v`) ----------
def parse_opts(rest, default_bindir):
    """(bindir, dry_run, verbose) from a selfinstall arg list.

    >>> parse_opts([], "~/.local/bin")
    ('~/.local/bin', False, False)
    >>> parse_opts(["--dry-run", "-v"], "~/.local/bin")
    ('~/.local/bin', True, True)
    >>> parse_opts(["--bindir", "~/bin"], "~/.local/bin")
    ('~/bin', False, False)
    """
    bindir, dry, verbose = default_bindir, False, False
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == "--bindir" and i + 1 < len(rest):
            bindir = rest[i + 1]; i += 2; continue
        if a == "--dry-run": dry = True
        elif a in ("-v", "--verbose"): verbose = True
        i += 1
    return bindir, dry, verbose

def dir_on_path(d, pathenv):
    """Is directory `d` present in a PATH-style string?

    >>> dir_on_path("/home/u/.local/bin", "/usr/bin:/home/u/.local/bin")
    True
    >>> dir_on_path("/home/u/bin", "/usr/bin:/bin")
    False
    """
    d = os.path.normpath(os.path.expanduser(d))
    return any(os.path.normpath(p) == d for p in pathenv.split(os.pathsep) if p)

def linknames(name, prefix=DISPATCH_PREFIX):
    """Command names a tool installs as: its own name, plus `<prefix>-<name>` so the
    dispatcher can find it. The dispatcher itself (name == prefix, or already prefixed)
    installs under just its own name.

    >>> linknames("secretkeeper", "boydstrap")
    ['secretkeeper', 'boydstrap-secretkeeper']
    >>> linknames("boydstrap", "boydstrap")
    ['boydstrap']
    >>> linknames("boydstrap-backinator", "boydstrap")
    ['boydstrap-backinator']
    """
    if name == prefix or name.startswith(prefix + "-"):
        return [name]
    return [name, prefix + "-" + name]

# ---------- side-effecting ----------
def _real(p): return os.path.realpath(os.path.expanduser(p))
def _repo(prog_file): return os.path.dirname(_real(prog_file))
def _git(repo, *args): return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)

def maybe(argv, prog_file, version=""):
    """Handle a selfinstall subcommand if argv[1] is one; else return None (let the tool run).
    Returns an int exit code when handled."""
    if len(argv) < 2 or argv[1] not in COMMANDS:
        return None
    bindir, dry, verbose = parse_opts(argv[2:], DEFAULT_BINDIR)
    return {"install": _install, "uninstall": _uninstall,
            "update": _update, "status": _status}[argv[1]](prog_file, version, bindir, dry, verbose)

def _install(prog_file, version, bindir, dry, verbose):
    target = _real(prog_file); name = os.path.basename(target)
    bd = os.path.expanduser(bindir); names = linknames(name); rc = 0
    if not dry: os.makedirs(bd, exist_ok=True)
    for ln in names:
        link = os.path.join(bd, ln)
        if os.path.exists(link) and not os.path.islink(link):
            print(f"  refuse: {link} exists and is not a symlink"); rc = 1; continue
        print(f"  install: {link} -> {target}")
        if not dry:
            if os.path.islink(link) or os.path.exists(link): os.remove(link)
            os.symlink(target, link)
    if dir_on_path(bd, os.environ.get("PATH", "")):
        print(f"  ✓ {bd} is on PATH — run: {name}")
        if names != [name]:
            print(f"    (also reachable as `{DISPATCH_PREFIX} {name}` via the dispatcher)")
    else:
        print(f"  ⚠ {bd} is NOT on your PATH. Add it, e.g.:")
        print(f"      echo 'export PATH=\"{bindir}:$PATH\"' >> ~/.profile   # then re-login")
        print(f"    (Ubuntu's ~/.profile auto-adds ~/.local/bin and ~/bin at login if they exist.)")
    return rc

def _uninstall(prog_file, version, bindir, dry, verbose):
    target = _real(prog_file); name = os.path.basename(target); bd = os.path.expanduser(bindir)
    removed = 0
    for ln in linknames(name):
        link = os.path.join(bd, ln)
        if os.path.islink(link) and _real(link) == target:
            print(f"  uninstall: rm {link}")
            if not dry: os.remove(link)
            removed += 1
    if not removed:
        print(f"  not installed in {bd} (or not this tool's symlinks)"); return 1
    return 0

def _update(prog_file, version, bindir, dry, verbose):
    repo = _repo(prog_file)
    if not os.path.isdir(os.path.join(repo, ".git")):
        print(f"  update: {repo} is not a git checkout"); return 1
    dirty = _git(repo, "status", "--porcelain").stdout.strip()
    if dirty:
        print(f"  refuse: {repo} has uncommitted changes (commit or stash first):")
        print("\n".join("    " + l for l in dirty.splitlines())); return 1
    print(f"  update: git -C {repo} pull --ff-only")
    if dry: return 0
    r = _git(repo, "pull", "--ff-only")
    out = (r.stdout + r.stderr).strip()
    print("\n".join("    " + l for l in out.splitlines()) if out else "    (done)")
    return r.returncode

def _status(prog_file, version, bindir, dry, verbose):
    target = _real(prog_file); name = os.path.basename(target); repo = _repo(prog_file)
    print(f"  {name} {version}".rstrip())
    print(f"    script: {target}")
    found = shutil.which(name)
    if found:
        same = _real(found) == target
        print(f"    on PATH: {found}" + ("  (this checkout)" if same else f"  (-> {_real(found)})"))
    else:
        print(f"    on PATH: no  (run `{name} install`)")
    extra = [n for n in linknames(name) if n != name]
    if extra:
        print(f"    dispatch: `{DISPATCH_PREFIX} {name}`" + ("" if shutil.which(extra[0]) else "  (alias not linked — run `install`)"))
    if os.path.isdir(os.path.join(repo, ".git")):
        _git(repo, "fetch", "--quiet")  # best-effort; ignore failure (offline)
        br = _git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        ahead = _git(repo, "rev-list", "--count", "@{u}..HEAD").stdout.strip()
        behind = _git(repo, "rev-list", "--count", "HEAD..@{u}").stdout.strip()
        if ahead == "" and behind == "":
            print(f"    git: {br} (no upstream tracking)")
        else:
            state = "up to date" if (ahead, behind) == ("0", "0") else f"{behind} behind / {ahead} ahead"
            tip = f"  (run `{name} update`)" if behind not in ("0", "") else ""
            print(f"    git: {br}, {state}{tip}")
    return 0
