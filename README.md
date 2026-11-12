# CSV → CAMT.053 Umwandler

Wandelt Kontoumsätze aus einer CSV-Datei in einen Kontoauszug im Format **CAMT.053.001.08** (ISO 20022) um. Nützlich für Konten ohne CAMT- oder MT940-Export, zum Beispiel Kreditkarten, PayPal oder alte und geschlossene Konten, deren Umsätze trotzdem in die Buchhaltung sollen.

- Erprobt mit dem Bankimport von **weclapp**: Soll und Haben, Partner, Partner-IBAN und Verwendungszweck werden übernommen.
- Die Ausgabe ist gegen das offizielle Schema `camt.053.001.08.xsd` von iso20022.org geprüft.
- Eine Datei, nur Python 3, keine Zusatzpakete.

[English version](README.en.md)

## Benutzung

```bash
python3 csv_zu_camt.py umsaetze.csv --iban DE89370400440532013000 --anfangssaldo "1.000,00"
```

| Option | Bedeutung |
|---|---|
| `--iban` | IBAN des eigenen Kontos (Pflicht). Sie muss der IBAN des Bankkontos in der Buchhaltung entsprechen |
| `--bic` | BIC des eigenen Kontos (optional) |
| `--anfangssaldo` | Kontostand vor der ersten Buchung, Standard 0 |
| `--endsaldo` | Kontrollwert: Abbruch, wenn die Summe der Buchungen nicht passt |
| `--waehrung` | Standard EUR |
| `-o` | Ausgabedatei, Standard: gleicher Name wie die CSV mit `.xml` |

**Mac:** In `camt-umwandeln.command` die IBAN eintragen. Danach doppelklicken oder CSV-Dateien darauf ziehen. Beim ersten Start eventuell mit Rechtsklick → Öffnen bestätigen.

## CSV-Aufbau

Trennzeichen `,` oder `;`, Kodierung UTF-8 oder Windows-1252. Erste Zeile mit Spaltennamen:

| Spalte | Pflicht | Inhalt |
|---|---|---|
| `date` | ja | Buchungstag: `10.11.2026`, `10.11.26` oder `2026-11-10` |
| `value_date` | | Valuta, leer = Buchungstag |
| `amount` | ja | `119,00`, `1.234,56`, `1234.56` oder `-49,90` |
| `debit_credit` | | `c` = Haben (Eingang), `d` = Soll (Ausgang). Leer = das Vorzeichen des Betrags entscheidet |
| `partner_name` | | Zahler bzw. Empfänger |
| `partner_iban` | | Wird nur übernommen, wenn die IBAN gültig ist |
| `remittance_info` | | Verwendungszweck |
| `reference` | | End-to-End-Referenz |
| `fee` | | Gebühr, die vom Betrag abgezogen wurde (z. B. SumUp, PayPal). Die Buchung steht netto im Auszug, Bruttobetrag (`AmtDtls`) und Gebühr (`Chrgs`) werden mitgeliefert, im Zweck steht „\| Gebühr 3,20 EUR“ |

Siehe `beispiel.csv` (eine Haben- und eine Soll-Buchung) und das Ergebnis `beispiel-camt.xml`.

## Hinweise

- Jede Buchung bekommt eine feste Referenz (`AcctSvcrRef`), die sich aus Datum, Betrag, Partner und Zweck ergibt. Bei erneutem Umwandeln derselben CSV bleibt sie gleich, so kann die Buchhaltung Dubletten erkennen.
- Beim Import in weclapp wird das Konto in den Banktransaktionen ausgewählt. Die IBAN im Auszug ist dabei offenbar zweitrangig.

## Lizenz

MIT, siehe [LICENSE](LICENSE). Nutzung auf eigene Verantwortung, Ergebnisse bitte vor dem Buchen prüfen.
