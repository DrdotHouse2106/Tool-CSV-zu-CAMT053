# CSV → CAMT.053 converter

Converts bank transactions from a CSV file into a **CAMT.053.001.08** (ISO 20022) bank statement. Useful for accounts without a CAMT or MT940 export, such as credit cards, PayPal or closed accounts.

- Tested with the bank import of **weclapp**: debit/credit, counterparty, counterparty IBAN and remittance information are imported.
- Output is validated against the official `camt.053.001.08.xsd` schema from iso20022.org.
- Single file, Python 3 only, no dependencies.

## Usage

```bash
python3 csv_zu_camt.py transactions.csv --iban DE89370400440532013000 --anfangssaldo "1000.00"
```

Options: `--iban` (required, your own account IBAN), `--bic`, `--anfangssaldo` (opening balance), `--endsaldo` (expected closing balance, aborts on mismatch), `--waehrung` (currency, default EUR), `-o` (output file).

macOS: set your IBAN in `camt-umwandeln.command`, then double-click it or drop CSV files onto it.

## CSV columns

`date` (required: `10.11.2026`, `10.11.26` or `2026-11-10`), `value_date`, `amount` (required: `119,00`, `1.234,56`, `1234.56`, `-49,90`), `debit_credit` (`c` = credit, `d` = debit; empty = sign of amount), `partner_name`, `partner_iban`, `remittance_info`, `reference`. Delimiter `,` or `;`. See `beispiel.csv` and `beispiel-camt.xml`.

## License

MIT, see [LICENSE](LICENSE). Use at your own risk and check results before posting.
