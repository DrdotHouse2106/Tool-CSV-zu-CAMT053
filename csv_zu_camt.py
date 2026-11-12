#!/usr/bin/env python3
"""CSV -> CAMT.053.001.08 (ISO-20022-Kontoauszug, z. B. für weclapp). Siehe README.md."""
import argparse, csv, hashlib, re, sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from xml.sax.saxutils import escape

def betrag(s):
    s = re.sub(r"[^\d,.\-]", "", s or "") or "0"
    if "," in s and "." in s:  # letztes Trennzeichen ist das Dezimalzeichen
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    return Decimal(s.replace(",", "."))

def datum(s):
    for f in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"):
        try: return datetime.strptime(s.strip(), f).date()
        except ValueError: pass
    sys.exit(f"Unbekanntes Datum: {s!r}")

def iban_ok(i):
    i = re.sub(r"\s", "", i or "").upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", i): return False
    return int("".join(str(int(c, 36)) for c in i[4:] + i[:4])) % 97 == 1

def lesen(pfad):
    roh = Path(pfad).read_bytes()
    try: text = roh.decode("utf-8-sig")
    except UnicodeDecodeError: text = roh.decode("cp1252")
    trenner = ";" if text.count(";") > text.count(",") else ","
    zeilen = []
    for r in csv.DictReader(text.splitlines(), delimiter=trenner):
        r = {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
        if not r.get("date"): continue
        b = betrag(r.get("amount"))
        dc = r.get("debit_credit", "").upper()
        haben = dc == "C" if dc in ("C", "D") else b >= 0
        zeilen.append(dict(r, betrag=abs(b), haben=haben, buch=datum(r["date"]),
                           valuta=datum(r.get("value_date") or r["date"])))
    if not zeilen: sys.exit("Keine Buchungen in der CSV.")
    return sorted(zeilen, key=lambda z: z["buch"])

def x(tag, inhalt="", **attr):
    a = "".join(f' {k}="{v}"' for k, v in attr.items())
    return f"<{tag}{a}>{inhalt}</{tag}>"

def saldo(cd, wert, waehrung, tag):
    return x("Bal", x("Tp", x("CdOrPrtry", x("Cd", cd))) + x("Amt", f"{abs(wert):.2f}", Ccy=waehrung)
             + x("CdtDbtInd", "CRDT" if wert >= 0 else "DBIT") + x("Dt", x("Dt", tag.isoformat())))

def buchung(z, waehrung):
    e = lambda s: escape(s[:140])
    ref = hashlib.sha1(f"{z['buch']}|{z['betrag']}|{z['haben']}|{z.get('partner_name')}|{z.get('remittance_info')}".encode()).hexdigest()[:16].upper()
    rolle = "Dbtr" if z["haben"] else "Cdtr"
    partei = ""
    if z.get("partner_name"):
        partei += x(rolle, x("Pty", x("Nm", e(z["partner_name"]))))
    if iban_ok(z.get("partner_iban")):
        partei += x(rolle + "Acct", x("Id", x("IBAN", z["partner_iban"].replace(" ", "").upper())))
    details = (x("Refs", x("AcctSvcrRef", ref) + (x("EndToEndId", e(z["reference"])) if z.get("reference") else ""))
               + (x("RltdPties", partei) if partei else "")
               + (x("RmtInf", x("Ustrd", e(z["remittance_info"]))) if z.get("remittance_info") else ""))
    return x("Ntry", x("Amt", f"{z['betrag']:.2f}", Ccy=waehrung) + x("CdtDbtInd", "CRDT" if z["haben"] else "DBIT")
             + x("Sts", x("Cd", "BOOK")) + x("BookgDt", x("Dt", z["buch"].isoformat()))
             + x("ValDt", x("Dt", z["valuta"].isoformat())) + x("AcctSvcrRef", ref)
             + x("BkTxCd", x("Domn", x("Cd", "PMNT") + x("Fmly", x("Cd", "RCDT" if z["haben"] else "ICDT") + x("SubFmlyCd", "ESCT"))))
             + x("NtryDtls", x("TxDtls", details)))

def main():
    p = argparse.ArgumentParser(description="CSV -> CAMT.053 für weclapp")
    p.add_argument("csv")
    p.add_argument("--iban", required=True)
    p.add_argument("--bic", default="")
    p.add_argument("--waehrung", default="EUR")
    p.add_argument("--anfangssaldo", default="0")
    p.add_argument("--endsaldo", default="", help="Kontrollwert, Abbruch bei Abweichung")
    p.add_argument("-o", "--ausgabe")
    a = p.parse_args()
    iban = a.iban.replace(" ", "").upper()
    if not iban_ok(iban): sys.exit(f"IBAN ungültig: {iban}")
    zeilen = lesen(a.csv)
    anfang = betrag(a.anfangssaldo)
    ende = anfang + sum(z["betrag"] if z["haben"] else -z["betrag"] for z in zeilen)
    if a.endsaldo and betrag(a.endsaldo) != ende:
        sys.exit(f"Endsaldo passt nicht: berechnet {ende:.2f}, erwartet {betrag(a.endsaldo):.2f}")
    jetzt = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sid = "STMT" + datetime.now().strftime("%Y%m%d%H%M%S")
    w = a.waehrung.upper()
    konto = x("Id", x("IBAN", iban)) + x("Ccy", w) + (x("Svcr", x("FinInstnId", x("BICFI", a.bic))) if a.bic else "")
    stmt = (x("Id", sid) + x("ElctrncSeqNb", "1") + x("CreDtTm", jetzt)
            + x("FrToDt", x("FrDtTm", f"{zeilen[0]['buch']}T00:00:00") + x("ToDtTm", f"{zeilen[-1]['buch']}T23:59:59"))
            + x("Acct", konto) + saldo("OPBD", anfang, w, zeilen[0]["buch"]) + saldo("CLBD", ende, w, zeilen[-1]["buch"])
            + "".join(buchung(z, w) for z in zeilen))
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.08">'
           + x("BkToCstmrStmt", x("GrpHdr", x("MsgId", sid) + x("CreDtTm", jetzt)) + x("Stmt", stmt)) + "</Document>\n")
    ziel = Path(a.ausgabe or Path(a.csv).with_suffix(".xml"))
    ziel.write_text(xml, encoding="utf-8")
    print(f"{len(zeilen)} Buchungen, Anfangssaldo {anfang:.2f}, Endsaldo {ende:.2f} -> {ziel}")

if __name__ == "__main__":
    main()
