#!/bin/zsh
# Doppelklick: CSV auswählen, oder CSV-Dateien auf dieses Skript ziehen.
# Erzeugt neben jeder CSV eine CAMT.053-XML für den Import in weclapp.
IBAN="DE89370400440532013000"   # Eigene IBAN eintragen (wie in der Buchhaltung hinterlegt)
BIC=""                          # optional
cd "$(dirname "$0")"
[[ $# -eq 0 ]] && set -- "$(osascript -e 'POSIX path of (choose file with prompt "CSV auswählen")')"
SALDO=$(osascript -e 'text returned of (display dialog "Kontostand vor der ersten Buchung:" default answer "0,00")')
for f in "$@"; do
  python3 csv_zu_camt.py "$f" --iban "$IBAN" --bic "$BIC" --anfangssaldo "$SALDO"
done
read -k1 "?Fertig – Taste drücken zum Schließen."
