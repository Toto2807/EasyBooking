"""Génère docs/FICHE_DE_TESTS.md à partir des docstrings des tests et du dernier rapport JUnit.

Chaque test est documenté dans son code : la 1re partie de la docstring décrit le cas,
la partie après « Attendu : » donne le résultat attendu. Les résultats viennent de
docs/reports/junit.xml (produit par scripts/run_all_tests.py).

Usage : python scripts/generate_test_sheet.py
"""
import ast
import re
import xml.etree.ElementTree as ET
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
JUNIT = ROOT / "docs" / "reports" / "junit.xml"
OUTPUT = ROOT / "docs" / "FICHE_DE_TESTS.md"

TYPES = {
    "UT": "Tests unitaires",
    "IT": "Tests d'intégration",
    "ST": "Tests de sécurité",
    "PT": "Tests de performance",
}
NAME_RE = re.compile(r"^test_(ut|it|pt|st)(\d+)_", re.IGNORECASE)


def collect_cases() -> list[dict]:
    cases = []
    for path in sorted((BACKEND / "tests").rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            match = NAME_RE.match(node.name)
            if not match:
                continue
            doc = ast.get_docstring(node) or ""
            parts = re.split(r"Attendu\s*:", doc, maxsplit=1)
            description = parts[0]
            expected = parts[1] if len(parts) > 1 else ""
            cases.append(
                {
                    "id": f"{match.group(1).upper()}-{int(match.group(2)):02d}",
                    "kind": match.group(1).upper(),
                    "num": int(match.group(2)),
                    "func": node.name,
                    "file": path.relative_to(BACKEND).as_posix(),
                    "description": " ".join(description.split()),
                    "expected": " ".join(expected.split()),
                }
            )
    return sorted(cases, key=lambda c: (list(TYPES).index(c["kind"]), c["num"]))


def read_results() -> tuple[dict, str]:
    if not JUNIT.exists():
        return {}, "non exécuté"
    root = ET.parse(JUNIT).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    results: dict[str, dict] = {}
    for case in root.iter("testcase"):
        base = case.get("name", "").split("[")[0]
        entry = results.setdefault(base, {"runs": 0, "failed": 0, "skipped": 0, "time": 0.0, "mesures": []})
        entry["runs"] += 1
        entry["time"] += float(case.get("time", 0))
        for prop in case.iterfind("properties/property"):
            if prop.get("name") == "mesure":  # valeur relevée par les tests de performance
                entry["mesures"].append(prop.get("value", ""))
        if case.find("failure") is not None or case.find("error") is not None:
            entry["failed"] += 1
        elif case.find("skipped") is not None:
            entry["skipped"] += 1
    return results, (suite.get("timestamp", "") if suite is not None else "")[:19].replace("T", " ")


def verdict(result: dict | None) -> str:
    if result is None:
        return "Non exécuté"
    if result["failed"]:
        return "ÉCHEC"
    if result["skipped"] == result["runs"]:
        return "Ignoré"
    return "RÉUSSI"


def escape(text: str) -> str:
    return text.replace("|", "\\|")


def main() -> None:
    cases = collect_cases()
    results, executed_at = read_results()

    lines = [
        "# Fiche de tests EasyBooking",
        "",
        "> Fichier **généré** par `backend/scripts/generate_test_sheet.py` à partir des docstrings des tests "
        "et du rapport `docs/reports/junit.xml`. Ne pas modifier à la main : relancer `python backend/scripts/run_all_tests.py`.",
        "",
        f"- Date d'exécution : **{executed_at or 'n/a'}**",
        f"- Nombre de cas de test : **{len(cases)}** (« jeux de données » = nombre d'exécutions pytest du cas, "
        "quand il est paramétré)",
        "",
        "## Synthèse",
        "",
        "| Type de test | Cas de test | Exécutions pytest | Réussis | Échecs | Durée cumulée |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    totals = [0, 0, 0, 0, 0.0]
    for kind, label in TYPES.items():
        group = [c for c in cases if c["kind"] == kind]
        runs = sum(results.get(c["func"], {}).get("runs", 0) for c in group)
        failed = sum(results.get(c["func"], {}).get("failed", 0) for c in group)
        duration = sum(results.get(c["func"], {}).get("time", 0.0) for c in group)
        ok = sum(1 for c in group if verdict(results.get(c["func"])) == "RÉUSSI")
        lines.append(f"| {label} ({kind}) | {len(group)} | {runs} | {ok} cas | {failed} | {duration:.2f} s |")
        totals = [totals[0] + len(group), totals[1] + runs, totals[2] + ok, totals[3] + failed, totals[4] + duration]
    lines.append(f"| **Total** | **{totals[0]}** | **{totals[1]}** | **{totals[2]} cas** | **{totals[3]}** | **{totals[4]:.2f} s** |")

    for kind, label in TYPES.items():
        with_measures = kind == "PT"  # colonne supplémentaire pour les tests de performance
        header = "| ID | Cas de test | Résultat attendu | Jeux de données | Résultat | Durée |"
        separator = "|---|---|---|---:|---|---:|"
        if with_measures:
            header += " Mesure relevée |"
            separator += "---|"
        lines += ["", f"## {label} ({kind})", "", header, separator]
        for case in (c for c in cases if c["kind"] == kind):
            result = results.get(case["func"])
            runs = result["runs"] if result else 0
            duration = f"{result['time']:.2f} s" if result else "-"
            line = f"| {case['id']} | {escape(case['description'])} | {escape(case['expected'])} | {runs} | {verdict(result)} | {duration} |"
            if with_measures:
                line += f" {escape(' ; '.join(result['mesures'])) if result else '-'} |"
            lines.append(line)
        files = sorted({c["file"] for c in cases if c["kind"] == kind})
        lines += ["", "Code : " + ", ".join(f"`backend/{f}`" for f in files)]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Fiche de tests écrite : {OUTPUT.relative_to(ROOT)} ({len(cases)} cas)")


if __name__ == "__main__":
    main()
