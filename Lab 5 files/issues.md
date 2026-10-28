# Lab 5 – Issue Table

**Name:** Chhavi S  **SRN:** PES1UG24CS132
**Assigned file:** `helpdesk_system.py` (repo `L5_06_it_helpdesk`)

## Score summary

| Tool | Before | After |
|------|--------|-------|
| Pylint | 5.53 / 10 (21 messages) | **10.00 / 10** |
| Bandit | 1 High, 3 Low | **No issues** |
| Flake8 | 15 findings | **0 findings** |

Reports: `reports/before/` and `reports/after/`.

## Issues found and fixed

Ordered by severity: security (Bandit) first, then bugs, then quality and style.

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Shell injection via `shell=True` (Bandit B602, **High**) | Security | 38 | `subprocess.call("ping -c 1 " + hostname, shell=True)` builds a shell command from a string, so a hostname like `x; rm -rf ~` runs arbitrary commands. | Validate the hostname with a strict regex, resolve `ping` with `shutil.which`, and call `subprocess.call([ping_path, "-c", "1", hostname])` with no shell. The regex also blocks option injection such as `-f`. |
| Hardcoded admin password (Bandit B105; CWE-259) | Security | 8, 54 | `ADMIN_PASSWORD = "helpdesk@123"` is committed to source, and `main()` repeats the literal. Anyone with repo access has the admin password. | Read it from the `HELPDESK_ADMIN_PASSWORD` environment variable at call time, deny closing if it is unset, and compare with `hmac.compare_digest` (constant time). |
| `try / except / pass` (Bandit B110) and bare `except:` (Pylint W0702, Flake8 E722) | Security / Bug | 21-24 | `add_note` swallows every exception, including typos and `KeyboardInterrupt`. Adding a note to missing ticket 999 fails silently. | Catch only `KeyError`, return `False`, and let `main()` report that the note was not added. |
| `subprocess` import (Bandit B404, Low) | Security | 2 | Informational flag for importing `subprocess`. | The module is genuinely needed for `ping`. Kept it with `# nosec B404` and a comment, since the risky usage is removed. This is an accepted, documented risk. |
| Mutable default argument `audit_trail=[]` (Pylint W0102) | Bug | 10 | The same list is shared by every call, so audit entries leak between unrelated callers. | Default to `None`; fall back to a module-level `audit_log` list inside the function. |
| No input validation on urgency (not flagged by any tool) | Bug | 13, 46-53 | `int(urgency)` accepts `-7` or `99`, and crashes with `ValueError` on `"abc"`. Ticket 103 was created with priority -7. | New `parse_urgency()` enforces a whole number from 1 to 5 and raises a clear `ValueError` *before* a ticket id is used. `main()` catches it and prints a message. |
| Hidden crashes and silent failures (not flagged) | Bug | 17-18, 26-28 | `assign_ticket` and `close_ticket` raise `KeyError` for unknown ids. `close_ticket` with a wrong password silently does nothing, and callers cannot tell. | Both now return `True` or `False`. `close_ticket` uses `dict.pop` and reports whether a ticket was really closed. |
| Global statement and invalid constant name (Pylint W0603, C0103) | Code smell | 7, 11 | A mutable module-level counter modified with `global`. | Replaced with `itertools.count(101)` and `next()`, which needs no `global` and is safe to call repeatedly. |
| File not closed safely, no encoding (Pylint R1732, W1514) | Bug / Quality | 41-43 | `open()` followed by manual `close()` leaks the handle if `write` raises, and uses the platform default encoding. | `with open(filename, "w", encoding="utf-8")` and `json.dump`. |
| Unrunnable on import: `main()` called at module level | Design | 58 | Importing the module (for tests) runs the whole demo and waits for input. | Added `if __name__ == "__main__":` guard. |
| `== None` comparison (Pylint C0121, Flake8 E711) | Style / Bug | 33 | Equality can be overridden; `None` should be compared by identity. | Use `is None`. |
| Non-snake_case function `unresolvedHighPriority` (Pylint C0103) | Style | 30 | Violates PEP 8 naming. | Renamed to `unresolved_high_priority`. |
| Index-based dict loop (Pylint C0206) | Quality | 32-35 | Looks up `tickets[t]` repeatedly. | Replaced with a list comprehension over `.items()`. |
| Old `%` string formatting (Pylint C0209) | Style | 14 | Hard to read, error-prone. | f-strings. |
| Magic numbers | Quality | 33, 52 | Bare `4`, `"3"`, `1-5`. | Named constants `HIGH_PRIORITY`, `MIN_URGENCY`, `MAX_URGENCY`, `DEFAULT_URGENCY`. |
| Unused variables `t2`, `t3` (Pylint W0612, Flake8 F841) | Quality | 47-48 | Assigned but never used. | `t2` is now used by the close-ticket demo; the invalid `t3` ticket is rejected instead of created. |
| Missing docstrings (Pylint C0114, C0116) | Documentation | 1, 10-45 | No module or function docstrings. | Added docstrings describing behaviour, return values and errors. |
| Long lines (Pylint C0301, Flake8 E501) | Style | 13, 14, 52 | Lines over 79 characters. | Wrapped. |
| Missing blank lines (Flake8 E302, E305) | Style | 10-58 | PEP 8 requires two blank lines around top-level definitions. | Added. |

## Fix order (one commit per tool)

1. **Bandit commit:** B602, B105, B110, B404.
2. **Pylint commit:** docstrings, naming, mutable default, global, `with open`, f-strings, plus validation and error-handling bugs.
3. **Flake8 commit:** E302/E305 blank lines and E501 line lengths.

## Behaviour change to be aware of

- `close_ticket` now needs `HELPDESK_ADMIN_PASSWORD` set in the environment. Run with
  `HELPDESK_ADMIN_PASSWORD=yourpassword python helpdesk_system.py` to see a ticket closed; without it the program reports the ticket was not closed.
- Invalid urgency is rejected rather than stored.
