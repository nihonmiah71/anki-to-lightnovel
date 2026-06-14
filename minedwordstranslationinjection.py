import csv
import os
import random
import re
import tkinter as tk
from tkinter import filedialog


def clean_text(text):
    """Bereinigt japanischen Text von ASS-Tags, Zeilenumbrüchen und Interpunktion,

    um ein robustes Kontext-Matching zu ermöglichen.
    """
    if not text:
        return ""
    # ASS-Formatierungstags wie {\pos(X,Y)} entfernen
    text = re.sub(r"\{[^}]+\}", "", text)
    # ASS-Zeilenumbrüche (\N oder \n) entfernen
    text = text.replace(r"\N", "").replace(r"\n", "")
    # Leerzeichen sowie typische japanische/deutsche Satzzeichen & Marker entfernen
    text = re.sub(
        r"[\s●③②①④⑤⑥⑦⑧⑨⓪①-⑨\.。,、 („)“、「」『』？?！!！？]", "", text
    )
    return text


def generate_bright_ass_color():
    """Generiert eine zufällige, helle Farbe im ASS-Hex-Format (BBGGRR)."""
    b = random.randint(120, 255)
    g = random.randint(120, 255)
    r = random.randint(120, 255)
    return f"{b:02X}{g:02X}{r:02X}"


def main():
    # Tkinter-Hauptfenster initialisieren und verstecken
    root = tk.Tk()
    root.withdraw()

    # 1. Datei-Auswahl via Explorer
    print("Bitte wähle die Tabellendatei (TSV/CSV) aus...")
    table_path = filedialog.askopenfilename(
        title="Wähle die Tabellendatei (TSV/CSV) aus",
        filetypes=[("Tabellendateien", "*.tsv *.csv"), ("Alle Dateien", "*.*")],
    )

    if not table_path:
        print("Keine Tabellendatei ausgewählt. Programm wird beendet.")
        return

    print("Bitte wähle die zu bearbeitende ASS-Untertiteldatei aus...")
    ass_path = filedialog.askopenfilename(
        title="Wähle die ASS-Untertiteldatei aus",
        filetypes=[("ASS Untertitel", "*.ass"), ("Alle Dateien", "*.*")],
    )

    if not ass_path:
        print("Keine ASS-Datei ausgewählt. Programm wird beendet.")
        return

    # 2. Tabellendatei flexibel einlesen
    with open(table_path, mode="r", encoding="utf-8-sig") as f:
        sample = f.read(2048)
        delimiter = "\t"
        if ";" in sample and sample.count(";") > sample.count("\t"):
            delimiter = ";"
        elif "," in sample and sample.count(",") > sample.count("\t"):
            delimiter = ","

    table_rows = []
    with open(table_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            cleaned_row = {
                k.strip(): v.strip() if v else ""
                for k, v in row.items()
                if k
            }
            table_rows.append(cleaned_row)

    if not table_rows:
        print("Fehler: Die ausgewählte Tabelle ist leer.")
        return

    # Spaltenvalidierung
    required_cols = ["Word", "SentencePlain", "Kontextuelle_Definition"]
    missing_cols = [col for col in required_cols if col not in table_rows[0]]

    if missing_cols:
        print(
            f"Fehler: Erforderliche Spalten fehlen in der Tabelle: {missing_cols}"
        )
        return

    # Farben fest an die Tabelleneinträge koppeln
    row_colors = {}
    for idx, row in enumerate(table_rows):
        word = row["Word"]
        sentence = row["SentencePlain"]
        entry_key = (word, sentence)
        if entry_key not in row_colors:
            row_colors[entry_key] = generate_bright_ass_color()

    print(
        f"-> {len(table_rows)} Vokabel-Einträge geladen und mit konstanten Farben verknüpft."
    )
    print("Starte ASS-Verarbeitung...")

    # 3. ASS-Datei einlesen
    with open(ass_path, mode="r", encoding="utf-8") as f:
        ass_lines = f.readlines()

    new_ass_lines = []

    for line in ass_lines:
        if not line.startswith("Dialogue:"):
            new_ass_lines.append(line)
            continue

        parts = line.split(",", 9)
        if len(parts) < 10:
            new_ass_lines.append(line)
            continue

        prefix = parts[:9]
        text_part = parts[9].rstrip("\r\n")

        style = prefix[3].strip()
        if style != "Text":
            new_ass_lines.append(line)
            continue

        cleaned_ass_text = clean_text(text_part)

        # Finde passende Tabelleneinträge im aktuellen Kontext
        matched_items = []
        for row in table_rows:
            word = row["Word"]
            sentence_plain = row["SentencePlain"]

            if not word or not sentence_plain:
                continue

            cleaned_sentence = clean_text(sentence_plain)

            if cleaned_sentence in cleaned_ass_text and word in text_part:
                if row not in matched_items:
                    matched_items.append(row)

        if not matched_items:
            new_ass_lines.append(line)
            continue

        # --- ÄNDERUNG HIER: ZWEI SEPARATE SORTIERUNGEN ---

        # 1. Für die Ersetzung im Haupttext: Nach Länge sortieren wegen Substring-Problemen
        matched_items_sorted_by_len = sorted(
            matched_items, key=lambda r: len(r["Word"]), reverse=True
        )

        updated_text_part = text_part

        for item in matched_items_sorted_by_len:
            word = item["Word"]
            sentence_plain = item["SentencePlain"]
            color = row_colors[(word, sentence_plain)]

            # Haupttext formatieren
            updated_text_part = updated_text_part.replace(
                word, f"{{\\b1\\c&H{color}&}}{word}{{\\b0\\c&HFFFFFF&}}"
            )

        # 2. Für die Definitionen im Zwischenblock: Nach Auftreten im Text sortieren
        matched_items_sorted_by_appearance = sorted(
            matched_items, key=lambda r: text_part.find(r["Word"])
        )

        defs_to_render = []
        for item in matched_items_sorted_by_appearance:
            word = item["Word"]
            definition = item["Kontextuelle_Definition"]
            sentence_plain = item["SentencePlain"]
            color = row_colors[(word, sentence_plain)]

            # Definition mit identischer Farbe sammeln (jetzt in korrekter Reihenfolge)
            defs_to_render.append(f"{{\\c&H{color}&}}{definition}")

        # Positionierung auslesen (X und Y Koordinate der fließenden Blöcke)
        pos_match = re.search(
            r"\{\\pos\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\}", text_part
        )

        if pos_match and defs_to_render:
            x_coord = int(pos_match.group(1))
            y_coord = int(pos_match.group(2))

            # Zwischenraum berechnen (Y - 100)
            y_new = y_coord - 100

            # Mehrere Definitionen nebeneinander setzen
            def_combined_text = "    ".join(defs_to_render)
            def_text_part = f"{{\\pos({x_coord},{y_new})}}{def_combined_text}"

            # Definitionszeile erstellen
            def_line = ",".join(prefix) + "," + def_text_part + "\n"
            new_ass_lines.append(def_line)

        # Hauptzeile hinzufügen
        modified_main_line = ",".join(prefix) + "," + updated_text_part + "\n"
        new_ass_lines.append(modified_main_line)

    # 4. ASS-Datei überschreiben
    with open(ass_path, mode="w", encoding="utf-8") as f:
        f.writelines(new_ass_lines)

    print(
        f"\nErfolgreich abgeschlossen! Die Datei '{os.path.basename(ass_path)}' wurde aktualisiert."
    )


if __name__ == "__main__":
    main()