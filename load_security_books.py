"""Batch-load mission-relevant security books into Nia's memory.

Downloads a curated subset of github.com/mizazhaider-ceh/Security-Books —
focused on cybersecurity policy, AI security, NIST frameworks, small business
protection, and career resources that align with Nia's mission.

Usage:
    python3 load_security_books.py              # load all curated books
    python3 load_security_books.py --list       # show what's already loaded
    python3 load_security_books.py --no-skip    # re-ingest everything

Each book is downloaded to a temp file, embedded, then deleted.
Embeddings live in nia_memory.db — permanent, searchable, always available.
"""

import argparse
import os
import tempfile
import urllib.request
import urllib.parse

BASE_URL = "https://raw.githubusercontent.com/mizazhaider-ceh/Security-Books/main/"

# Curated subset — mission-relevant for Nia's communities
BOOKS = [
    # Foundational cybersecurity awareness
    "CYBER SEC BASICS.pdf",
    "Small Business Guide Cyber Security.pdf",
    "Common Sense Guide to Mitigating Insider Threats, v7.pdf",
    "Network Safety Certification.pdf",
    "Types Of Sensitive Information.pdf.pdf",
    "Learn how to prevent phishing attacks.pdf",
    "Common Malware Types.pdf",

    # NIST & policy frameworks
    "NIST Cyber Security Framework.pdf",
    "NIST Cyber Security Framework - Overview.pdf",
    "NIST Cybersecurity Framework in a nutshell !.pdf",
    "NIST.CSWP.04162018.pdf",
    "zero Trust Archi.pdf",

    # AI & emerging threats
    "AI Tools in Cybersecurity – 2025 Edition.pdf",
    "AI in Cybersecurity.pdf",
    "Cyber Security in the Age of Artificial Intelligence.pdf",
    "Utilizing Generative AI for Cyber Defense Strategies.pdf",
    "What_Can_Generative_AI_Red_Teaming_Learn_from_Cyber_Red_Teaming.pdf",
    "Creatively Malicious Prompt Engineering.pdf",
    "OWASP Top 10 for  LLM Applications 2025.pdf",
    "Major Cybersecurity Focus Areas for 2026 .pdf",

    # Careers & opportunity (wealth-building angle)
    "5 Steps to Get a Job in Cyber Security.pdf",
    "cybersecurity career 2026.pdf",
    "Cyber Security For CISO-CIO-CTO.pdf",
    "Cybersecurity_Strategies_and_Best_Practices_A_Comprehensive_Guide.pdf",
    "Building an Application Security Program.pdf",

    # Network fundamentals (understanding infrastructure)
    "Network Defense_ Security Policy & Threats.pdf",
    "Network Performance and Security.pdf",
    "Network Security Through Data.pdf",
    "Subnetting.pdf",
    "Common Ports.pdf",

    # Privacy & data protection
    "RANSOMWARE DEFENSE REPORT.pdf",
    "windows event log analysis.pdf",
    "API Security threats.pdf",
    "OWASP Top 10 Vulnerabilities -1.pdf",
    "OWASP Top 10 vulnerabilities .pdf",
]


def _already_ingested(label):
    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), "nia_memory.db")
    if not os.path.exists(db_path):
        return False
    db = sqlite3.connect(db_path)
    cols = [r[1] for r in db.execute("PRAGMA table_info(mem)").fetchall()]
    if "source" not in cols:
        db.close()
        return False
    n = db.execute("SELECT COUNT(*) FROM mem WHERE source=?", (label,)).fetchone()[0]
    db.close()
    return n > 0


def download_and_ingest(filename, skip_existing=True):
    import learn_pdf as lp

    label = os.path.splitext(filename)[0]
    # Handle double extension (e.g. "Types Of Sensitive Information.pdf.pdf")
    if label.endswith(".pdf"):
        label = os.path.splitext(label)[0]

    if skip_existing and _already_ingested(label):
        print(f"  [skip] already loaded: {label}")
        return 0

    encoded = urllib.parse.quote(filename)
    url = BASE_URL + encoded
    tmp_path = None

    print(f"\n[↓] Downloading: {filename}")
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        urllib.request.urlretrieve(url, tmp_path)
        size_kb = os.path.getsize(tmp_path) // 1024
        print(f"    Downloaded {size_kb}KB")

        if size_kb < 5:
            print(f"    [skip] file too small — likely not a readable PDF")
            os.unlink(tmp_path)
            return 0

        chunks = lp.ingest(tmp_path, label=label)
        os.unlink(tmp_path)
        return chunks

    except Exception as e:
        print(f"    [error] {e}")
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return 0


def main():
    ap = argparse.ArgumentParser(description="Load security library into Nia's memory")
    ap.add_argument("--list", action="store_true", help="Show already-loaded books")
    ap.add_argument("--no-skip", action="store_true", help="Re-ingest everything")
    args = ap.parse_args()

    if args.list:
        import learn_pdf as lp
        lp.list_sources()
        return

    skip = not args.no_skip

    print(f"Security Books Library → Nia's memory")
    print(f"Curated books to process: {len(BOOKS)}")
    print(f"Skip existing: {skip}\n")

    total_chunks = 0
    loaded = 0
    failed = []

    for i, book in enumerate(BOOKS, 1):
        print(f"[{i}/{len(BOOKS)}]", end=" ")
        try:
            chunks = download_and_ingest(book, skip_existing=skip)
            if chunks:
                total_chunks += chunks
                loaded += 1
        except KeyboardInterrupt:
            print("\n\nInterrupted. Progress saved — run again to continue.")
            break
        except Exception as e:
            print(f"  [error] {book}: {e}")
            failed.append(book)

    print(f"\n{'='*60}")
    print(f"Done. {loaded} books loaded, {total_chunks:,} chunks embedded.")
    if failed:
        print(f"Failed ({len(failed)}): {', '.join(failed[:5])}")
    print("Nia knows the library. Ask her anything.")


if __name__ == "__main__":
    main()
