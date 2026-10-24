# Diagram generator

`gen_task1.py` builds the draw.io file for Task 1 from Python so the layout can be
regenerated and tweaked without hand-editing XML. Icons in `icons/` are extracted from
the Yandex Cloud draw.io libraries (services, Oct 2023) so the notation matches the
as-is diagram supplied by the course.

```bash
python3 tools/diagram/gen_task1.py "Task1/InureTech_технологическая архитектура_to-be.drawio"
```

Open the result in draw.io (desktop or app.diagrams.net) to view or export it.

`gen_task3.py` takes the course's as-is C4 container diagram
(`InsureTech_C4_container-diagram_as-is.drawio.xml`, downloaded unchanged) and produces the
Task 3 to-be version: it removes the synchronous polling relationships, adds Kafka, the
aggregator database and the outbox relay, and draws event-streaming relationships dashed.

```bash
python3 tools/diagram/gen_task3.py "Task3/InsureTech_C4_container-diagram_to-be.drawio"
```

`gen_task4.py` builds on the Task 3 result: it adds `osago-aggregator` with its database, Managed
Redis, the WebSocket stream to the web app, the OSAGO Kafka topics and the resilience-pattern
markers (TimeOut, Retry, Rate Limiter, Circuit Breaker) drawn with the course notation from
`resilience-patterns-notation.drawio.xml` (downloaded unchanged).

```bash
python3 tools/diagram/gen_task4.py "Task3/InsureTech_C4_container-diagram_to-be.drawio" "Task4/InsureTech_C4_container-diagram_to-be.drawio"
```

## Rendering to PNG

There is no draw.io CLI on this machine, so the PNGs are produced by opening the diagram in
`https://viewer.diagrams.net/?lightbox=1` (payload injected as a compressed `#R…` hash), exporting
the rendered SVG, inlining it into an HTML page and taking a screenshot with headless Google Chrome
(`--headless=new --window-size=W,H --force-device-scale-factor=1.5 --screenshot=`).
