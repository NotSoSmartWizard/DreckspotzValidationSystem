# DreckspotzValidierungsSystem

## DreckspotzValidierungsSystem
Willkommen zur Benutzeroberfläche für die Datenanalyse der Dreckspotz-App mithilfe des RT-DTR-Algorithmus.

## Beschreibung
Dieses Programm ermöglicht sowohl das Herunterladen als auch die Analyse der Daten aus dem Dreckspotz-Datensatz.

## Installation
Die Installation gestaltet sich ganz einfach. Die einzige Vorraussetzung ist das Vorhandensein von Python auf ihren Computer. Klont dieses Repository und öffnet das Terminal im Verzeichnis, in dem ihr das Repository gespeichert habt. Installiert dann die benötigten Bibliotheken mit: pip install -r requirements.txt
## Verwendung

Navigiert im Terminal zum Verzeichnis des Repositories. Navigiert anschließend in den `app/code` folder. Startet das Programm auf Linux mit: `python3 main.py` oder auf Windows mit: `python main.py`. Gebt anschließend eine CSV-Datei im folgenden Format ein: `LATITUDE;LONGITUDE;CREATED_AT;MODIFIED_AT;CATEGORY;LITTER_CATEGORY_PRESELECT;LITTER_CATEGORY;LITTER_CATEGORY_OTHER;LITTER_BRAND;LITTER_COUNT;DISPOSAL_CATEGORY;DISPOSAL_TYPES;DISPOSAL_OVERFILLED;DISPOSAL_BROKEN;IMAGE;LITTER_CLEARED;DESCRIPTION;SPOTTED_AT` oder `ID,ROOT_ID,STATE,FEATURED,CHECKED,VALIDATION_SCORE,LATITUDE,LONGITUDE,CREATED_AT,MODIFIED_AT,USER_ID,USER_ROLE,CATEGORY,LITTER_CATEGORY_PRESELECT,LITTER_CATEGORY,LITTER_CATEGORY_OTHER,LITTER_BRAND,LITTER_COUNT,DISPOSAL_CATEGORY,DISPOSAL_TYPES,DISPOSAL_OVERFILLED,DISPOSAL_BROKEN,IMAGE,LITTER_CLEARED,DESCRIPTION,SPOTTED_AT,,,`. Wichtig: Beachtet, dass diese Spalten immer vorhanden sind und gleich heißen: `LATITUDE`, `LONGITUDE`, `SPOTTED_AT`, `LITTER_CATEGORY_PRESELECT`, `LITTER_CATEGORY`.

Es gibt zwei Möglichkeiten: Entweder startet ihr direkt mit dem Download oder ihr entfernt mögliche Duplikate. Diese Funktion durchsucht den Datensatz nach Bildern, die am gleichen Ort (innerhalb eines 10 m Radius) und zur gleichen Zeit (innerhalb einer 30-Minuten-Periode) aufgenommen wurden. Wenn diese Bilder zusätzlich der gleichen Müllkategorie angehören, werden sie als Duplikate erkannt und nur eines wird beibehalten. Diese Funktion ist optional, da Duplikate auch falsch erkannt werden können.

Beim Download werden nun alle Daten auf euren Rechner heruntergeladen und im `Data`-Ordner gespeichert. Diese werden dort nach den markierten Kategorien organisiert. 

Anschließend könnt ihr sofort mit der Analyse beginnen. Das Programm durchläuft jeden Ordner und überprüft, ob jedes erkannte Objekt seiner Kategorie entspricht und ob es auch zur übergeordneten Kategorie passt. Nach Abschluss der Analyse erstellt das Programm mehrere CSV-Listen mit den Ergebnissen im `Output`-Ordner.

