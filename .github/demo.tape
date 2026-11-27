# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT

# The README demo: the installed version, the amounts, codes and
# remittance lines of the repository's camt.054 fixture, then the
# loader reading it. Render with `make demo`.

Output .github/demo.gif

Set Shell "bash"
Set FontSize 14
Set Width 1280
Set Height 640
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 20ms

Hide
Type "export PS1='$ ' && clear"
Enter
Show

Type "poetry run python -c 'import bankstatementparser_loader_camt054 as c; print(c.__version__)'"
Enter
Wait /\$$/
Sleep 1s

Type "grep -E '<Amt|CdtDbtInd|<Cd>|Ustrd' tests/fixtures/notification.xml"
Enter
Wait /\$$/
Sleep 3s

Type `poetry run python -c 'from bankstatementparser_loader_camt054 import load_camt054_file as load; [print(t.booking_date, t.amount, t.category, t.reference, t.description) for t in load("tests/fixtures/notification.xml")]'`
Enter
Wait /\$$/
Sleep 5s
