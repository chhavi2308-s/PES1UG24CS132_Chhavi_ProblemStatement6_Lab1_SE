# Lab 5 – Reflection

**Name:** Chhavi S  **SRN:** PES1UG24CS132

## 1. Which issues were the easiest to fix, and which were the hardest? Why?

The easiest were the mechanical ones: Flake8's blank-line and line-length warnings, `== None` to `is None`, f-strings, and adding docstrings. Each has one obvious fix with no effect on behaviour.

The hardest was the Bandit High finding, `shell=True` in `ping_user_machine`. Deleting `shell=True` alone would break the command because it was passed as one string. I had to restructure the call as an argument list, validate the hostname so it cannot be mistaken for a ping option, and locate `ping` with `shutil.which` so the full path is used. The hardcoded password was also harder than it looks, because the fix is a design change (read it from an environment variable) and it changes how the program is run. The urgency bug took thought too, because no tool flagged it: I had to notice `-7` was being accepted and decide where validation belongs.

## 2. Did the tools report any false positives? Give an example.

Bandit B404 (`import subprocess`) is the closest to one. It only says "consider the security implications" of importing the module. Once the unsafe `shell=True` call was gone, the import was legitimate, so I kept it with `# nosec B404` and a comment explaining why. After the rewrite, Bandit also flagged `subprocess.call` with a list (B603) as a low-severity item, even though that is the safe form once the input is validated, so I suppressed it with a justification as well. Pylint's `line-too-long` (limit 100) and Flake8's `E501` (limit 79) disagree about line length, so a line could pass one tool and fail the other. I satisfied both by using the stricter 79.

## 3. How would you integrate static analysis into your actual workflow?

- **In the editor:** enable Pylint and Flake8 in VS Code so problems show as I type.
- **Before each commit:** a `pre-commit` hook running `flake8`, `pylint` and `bandit -r`, so bad code never reaches the repo.
- **In CI:** a GitHub Actions workflow that runs the same three tools on every pull request and fails the build on Bandit High/Medium findings or a Pylint score below a threshold (for example 9.0).
- **Tuning:** keep one shared config (`.pylintrc`, `setup.cfg`) so the team agrees on rules, and allow `# nosec` or `# pylint: disable` only with a written reason.

## 4. What tangible improvements did you observe after applying the fixes?

- **Scores:** Pylint went from 5.53 to 10.00, Flake8 from 15 findings to 0, and Bandit from 1 High + 3 Low to no issues.
- **Security:** the command-injection hole is closed (inputs like `x; echo PWNED` and `-f` are rejected), and the admin password is no longer in the source.
- **Reliability:** invalid urgency (`-7`, `9`, `abc`) is rejected with a clear message instead of corrupting data or crashing, a missing ticket no longer raises `KeyError`, and a failed note no longer disappears silently.
- **Maintainability:** consistent naming, docstrings, named constants, no global state, and the module can now be imported for testing without running the demo.
- **Takeaway:** the tools found most problems, but not all. The urgency validation and the silent wrong-password failure were found by running the program and reading its output, so static analysis complements testing rather than replacing it.
