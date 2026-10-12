# hDo – Supabase Todo Integration für Home Assistant

Zeigt eine Supabase-Tabelle `todos` als Home-Assistant-To-Do-Liste an.
Login erfolgt per E-Mail + Passwort über Supabase Auth (Row Level Security
wird dadurch automatisch respektiert – jeder Nutzer sieht nur seine eigenen Einträge).

## Erwartetes Tabellenschema (`todos`)

| Spalte       | Typ          |
|--------------|--------------|
| id           | int8 (PK)    |
| created_at   | timestamptz  |
| name         | text         |
| isCompleted  | bool         |
| user_id      | uuid         |
| content      | text         |

Falls deine Tabelle anders heißt, passe `TABLE_NAME` in `const.py` an.

## Installation über HACS (eigenes Repository)

1. HACS öffnen → oben rechts die drei Punkte → **Benutzerdefinierte Repositories**.
2. Repository-URL eintragen (dein GitHub-Repo mit diesem Code), Kategorie: **Integration**.
3. "hDo" in HACS suchen und installieren.
4. Home Assistant neu starten.

## Manuelle Installation (ohne HACS/GitHub)

1. Den Ordner `custom_components/hdo` in dein Home-Assistant-Konfigurationsverzeichnis
   kopieren, sodass der Pfad `config/custom_components/hdo/...` lautet.
2. Home Assistant neu starten.

## Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**.
2. "hDo" suchen.
3. E-Mail und Passwort des Supabase-Benutzers eingeben (derselbe Login wie
   in deiner App/Supabase Auth).
4. Fertig – es erscheint eine To-Do-Liste "hDo" mit allen Einträgen des
   eingeloggten Nutzers.

## Funktionen

- Aufgaben anzeigen (Name, erledigt/offen, Inhalt als Beschreibung)
- Aufgaben über die HA-To-Do-Karte abhaken/erledigen
- Neue Aufgaben über HA anlegen
- Aufgaben löschen
- Automatischer Token-Refresh (Supabase Access Token läuft nach 1h ab,
  wird automatisch erneuert)
- Polling-Intervall: 60 Sekunden (einstellbar in `const.py` über
  `UPDATE_INTERVAL_SECONDS`)

## Wichtiger Hinweis zu Supabase RLS

Damit der Login sinnvoll nur die eigenen Todos liefert, sollte in Supabase
eine Row-Level-Security-Policy auf der `todos`-Tabelle aktiv sein, z. B.:

```sql
create policy "Users can view their own todos"
on todos for select
using (auth.uid() = user_id);

create policy "Users can insert their own todos"
on todos for insert
with check (auth.uid() = user_id);

create policy "Users can update their own todos"
on todos for update
using (auth.uid() = user_id);

create policy "Users can delete their own todos"
on todos for delete
using (auth.uid() = user_id);
```

Ohne solche Policies (bzw. mit RLS deaktiviert) sieht der eingeloggte
Nutzer ggf. alle Zeilen der Tabelle, abhängig von deiner Konfiguration.
