"""Lance toute la suite de tests et produit les exports d'exécution.

Usage (depuis le dossier backend/, base PostgreSQL démarrée) :
    python scripts/run_all_tests.py

Produit dans docs/reports/ :
    execution.txt   sortie console complète de pytest (avec couverture)
    junit.xml       résultats au format JUnit (outils de CI)
    report.html     rapport HTML autonome (à ouvrir dans un navigateur)
    coverage.xml    couverture de code
puis régénère docs/FICHE_DE_TESTS.md.
"""
import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
REPORTS = ROOT / "docs" / "reports"


def scrub_paths() -> None:
    """Remplace les chemins absolus de la machine par <projet> / <home> dans les exports.

    Ces fichiers sont versionnés dans Git : on n'y laisse ni nom d'utilisateur ni chemin local.
    """
    replacements = [
        (sys.executable, "python"),
        (Path(sys.executable).as_posix(), "python"),
        (ROOT.as_uri(), "<projet>"),
        (str(ROOT), "<projet>"),
        (ROOT.as_posix(), "<projet>"),
        (Path.home().as_uri(), "<home>"),
        (str(Path.home()), "<home>"),
        (Path.home().as_posix(), "<home>"),
    ]
    for report in REPORTS.glob("*"):
        if report.suffix not in {".txt", ".xml", ".html"}:
            continue
        text = report.read_text(encoding="utf-8", errors="replace")
        for old, new in replacements:
            text = text.replace(old, new)
        report.write_text(text, encoding="utf-8")


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable, "-m", "pytest", "-v", "--durations=10",
        f"--junitxml={REPORTS / 'junit.xml'}",
        f"--html={REPORTS / 'report.html'}", "--self-contained-html",
        "--cov=app", "--cov-report=term-missing", f"--cov-report=xml:{REPORTS / 'coverage.xml'}",
        *sys.argv[1:],
    ]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    sys.stdout.reconfigure(errors="replace")

    with open(REPORTS / "execution.txt", "w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command, cwd=BACKEND, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )
        for line in process.stdout:
            sys.stdout.write(line)
            log.write(line)
        code = process.wait()

    scrub_paths()
    subprocess.run([sys.executable, str(BACKEND / "scripts" / "generate_test_sheet.py")], check=False)
    return code


if __name__ == "__main__":
    sys.exit(main())
