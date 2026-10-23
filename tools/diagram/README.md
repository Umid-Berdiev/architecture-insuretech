# Diagram generator

`gen_task1.py` builds the draw.io file for Task 1 from Python so the layout can be
regenerated and tweaked without hand-editing XML. Icons in `icons/` are extracted from
the Yandex Cloud draw.io libraries (services, Oct 2023) so the notation matches the
as-is diagram supplied by the course.

```bash
python3 tools/diagram/gen_task1.py "Task1/InureTech_технологическая архитектура_to-be.drawio"
```

Open the result in draw.io (desktop or app.diagrams.net) to view or export it.
