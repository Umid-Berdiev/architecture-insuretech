"""Build the Task 4 C4 container diagram (OSAGO sale) from the Task 3 to-be diagram.

Adds osago-aggregator with its database, Managed Redis, the WebSocket stream to the web app,
the Kafka topics for OSAGO requests/offers and the resilience-pattern markers drawn with the
course's notation (Kubernetes-style icons: TimeOut, Retry, Rate Limiter, Circuit Breaker).

Usage: gen_task4.py <Task3 to-be .drawio> <output .drawio>
"""
import sys
import xml.etree.ElementTree as ET

SRC, OUT = sys.argv[1], sys.argv[2]
P = "uZ0quFO-MIEIE11IO5jD-"

tree = ET.parse(SRC)
root_model = tree.getroot().find("diagram/mxGraphModel/root")
by_id = {el.get("id"): el for el in root_model}
by_name = {el.get("c4Name"): el for el in root_model if el.get("c4Name")}
by_name.update({el.get("c4Type"): el for el in root_model if el.get("c4Container")})  # databases


def cell_of(obj):
    """Return the mxCell of a C4 object, or the cell itself for a plain mxCell (notes)."""
    return obj if obj.tag == "mxCell" else obj.find("mxCell")


def geom_of(obj):
    return cell_of(obj).find("mxGeometry")


def move(obj, x=None, y=None, w=None, h=None):
    g = geom_of(obj)
    for k, v in (("x", x), ("y", y), ("width", w), ("height", h)):
        if v is not None:
            g.set(k, str(v))


def restyle(obj, extra):
    c = cell_of(obj)
    c.set("style", c.get("style") + extra)


def set_points(obj, points, lx=None, offset=None):
    g = geom_of(obj)
    for arr in g.findall("Array"):
        g.remove(arr)
    for pt in g.findall("mxPoint"):
        if pt.get("as") == "offset":
            g.remove(pt)
    if points:
        arr = ET.SubElement(g, "Array")
        arr.set("as", "points")
        for px, py in points:
            ET.SubElement(arr, "mxPoint", x=str(px), y=str(py))
    if lx is not None:
        g.set("x", str(lx))
    if offset:
        o = ET.SubElement(g, "mxPoint", x=str(offset[0]), y=str(offset[1]))
        o.set("as", "offset")


boundary = by_id[P + "1"]
web, core_app, core_db = by_id[P + "4"], by_id[P + "3"], by_id[P + "2"]
client_info, client_db = by_id["ckVUTfoMV_SZnMC_Z-Nl-1"], by_id["ckVUTfoMV_SZnMC_Z-Nl-2"]
person = by_id[P + "23"]
aggregator, settlement = by_id[P + "16"], by_id[P + "19"]
kafka, relay = by_name["Kafka"], by_name["outbox-relay"]
edge_web_core, edge_aggr_ins, edge_settl_ins = by_id[P + "5"], by_id[P + "17"], by_id[P + "32"]
edge_kafka_core = next(o for o in root_model if o.get("c4Description", "").startswith("Подписка: обновление"))
edge_relay_kafka = next(o for o in root_model if o.get("c4Description", "").startswith("Публикация policy.issued"))
notes = [el for el in root_model if el.tag == "mxCell" and "shape=note" in (el.get("style") or "")]
legend_note, decisions_note = notes[0], notes[1]

container_style = cell_of(core_app).get("style")
db_style = cell_of(core_db).get("style")
container_label = core_app.get("label")
db_label = core_db.get("label")
edge_style = cell_of(edge_web_core).get("style")
edge_label = edge_web_core.get("label")
ASYNC_STYLE = cell_of(edge_kafka_core).get("style").split("exitX=")[0]
ICON_STYLE = ("aspect=fixed;sketch=0;html=1;dashed=0;whitespace=wrap;verticalLabelPosition=bottom;"
              "verticalAlign=top;fillColor=#2875E2;strokeColor=#ffffff;fontSize=9;fontColor=#333333;"
              "points=[[0.005,0.63,0],[0.1,0.2,0],[0.9,0.2,0],[0.5,0,0],[0.995,0.63,0],[0.72,0.99,0],"
              "[0.5,1,0],[0.28,0.99,0]];shape=mxgraph.kubernetes.icon2;prIcon={};")
PATTERN_ICON = {"TimeOut": "quota", "Retry": "deploy", "Rate Limiter": "job", "Circuit Breaker": "c_role"}

_n = 0


def new_id():
    global _n
    _n += 1
    return f"task4-{_n}"


def add_container(name, tech, desc, x, y, w=240, h=120, db=False):
    obj = ET.SubElement(root_model, "object", placeholders="1", id=new_id())
    if db:
        obj.set("c4Type", name)
        obj.set("c4Container", "Container")
        obj.set("label", db_label)
    else:
        obj.set("c4Name", name)
        obj.set("c4Type", "Container")
        obj.set("label", container_label)
    obj.set("c4Technology", tech)
    obj.set("c4Description", desc)
    c = ET.SubElement(obj, "mxCell", style=db_style if db else container_style, vertex="1", parent="1")
    g = ET.SubElement(c, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h))
    g.set("as", "geometry")
    return obj


def add_edge(src, dst, desc, tech, async_=False, exit=None, entry=None, points=None, lx=None, offset=None):
    obj = ET.SubElement(root_model, "object", placeholders="1", id=new_id())
    obj.set("c4Type", "Relationship")
    obj.set("c4Technology", tech)
    obj.set("c4Description", desc)
    obj.set("label", edge_label)
    st = ASYNC_STYLE if async_ else edge_style
    if exit:
        st += f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
    if entry:
        st += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
    c = ET.SubElement(obj, "mxCell", style=st, edge="1", parent="1", source=src.get("id"), target=dst.get("id"))
    g = ET.SubElement(c, "mxGeometry", width="160", relative="1")
    g.set("as", "geometry")
    set_points(obj, points, lx, offset)
    return obj


def add_pattern(name, x, y, size=24, label=None):
    """Resilience-pattern marker in the course notation: icon with the pattern name underneath."""
    c = ET.SubElement(root_model, "mxCell", id=new_id(), value=label or name,
                      style=ICON_STYLE.format(PATTERN_ICON[name]), vertex="1", parent="1")
    g = ET.SubElement(c, "mxGeometry", x=str(x), y=str(y), width=str(size), height=str(round(size * 0.96)))
    g.set("as", "geometry")


def add_note(text, x, y, w, h):
    c = ET.SubElement(root_model, "mxCell", id=new_id(), value=text, vertex="1", parent="1",
                      style=cell_of(legend_note).get("style"))
    g = ET.SubElement(c, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h))
    g.set("as", "geometry")


# ---------------------------------------------------------------- make room
# Top row 80px higher: a wider corridor between the web app and core-app for REST + WebSocket.
for obj in (web, client_info, client_db):
    move(obj, y=int(geom_of(obj).get("y")) - 80)
move(person, y=int(geom_of(person).get("y")) - 80)
move(boundary, y=50, w=1400, h=1280)          # x 450..1850, y 50..1330
for suffix in ("11", "12", "13"):             # insurers stack: further right and lower
    g = geom_of(by_id[P + suffix])
    g.set("x", str(int(g.get("x")) + 170))
    g.set("y", str(int(g.get("y")) + 180))
# Existing relationships to the insurers get new corridors.
set_points(edge_aggr_ins, [(1660, 508), (1660, 756)], lx=-0.55)
restyle(edge_aggr_ins, "exitX=1;exitY=0.6;exitDx=0;exitDy=0;entryX=0;entryY=0.3;entryDx=0;entryDy=0;")
set_points(edge_settl_ins, [(1700, 900), (1700, 786)], lx=-0.55)
restyle(edge_settl_ins, "exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.55;entryDx=0;entryDy=0;")

# ---------------------------------------------------------------- existing elements: text updates
edge_web_core.set("c4Description", "1. Получение тарифов\n2. Создание заявок на страховки\n3. Создание заявки на ОСАГО")
set_points(edge_web_core, None, offset=(-5, -35))
restyle(edge_web_core, "exitX=0.25;exitY=1;exitDx=0;exitDy=0;entryX=0.25;entryY=0;entryDx=0;entryDy=0;")
move(core_app, h=150)
core_app.set("c4Description",
    "Монолит: продукты и страховки; оформление ОСАГО (заявка, сбор предложений, выбор); "
    "публикует policy.issued и osago.request через outbox; отдаёт предложения в браузер по WebSocket")
core_db.set("c4Description",
    "Тарифы СК (реплика), заявки клиентов, заявки на ОСАГО и полученные предложения, таблица outbox")
edge_kafka_core.set("c4Description", "Подписка: products,\nosago.offers")
edge_kafka_core.set("c4Technology", "Kafka consumer")
edge_relay_kafka.set("c4Description", "Публикация policy.issued,\nosago.request")
edge_relay_kafka.set("c4Technology", "Kafka: topics policies, osago.requests")
set_points(by_id["ckVUTfoMV_SZnMC_Z-Nl-4"], None, lx=-0.4, offset=(30, 0))
kafka.set("c4Description",
    "Топики: products (compacted), policies, osago.requests (ключ — id заявки), osago.offers "
    "(ключ — id заявки), DLQ; схемы — в Schema Registry")

# ---------------------------------------------------------------- new containers
osago = add_container(
    "osago-aggregator", "Kotlin, SpringBoot (N экземпляров)",
    "Принимает заявки на ОСАГО из Kafka, создаёт их во всех СК, опрашивает решения до 60 с и "
    "публикует каждое предложение сразу по получении. Один адаптер на СК; опрос заявки держит "
    "один экземпляр по lease в БД",
    1520, 320, 240, 130)
osago_db = add_container(
    "osago-aggregator-db", "PostgreSQL",
    "Заявки, id заявки в каждой СК, дедлайн и lease опроса, полученные предложения",
    1560, 160, 220, 100, db=True)
redis = add_container(
    "Redis", "Managed Service for Redis",
    "Pub/Sub для рассылки предложений всем экземплярам core-app; распределённый token bucket "
    "на каждую СК",
    1020, 240, 190, 110)
redis.set("c4Description", "Pub/Sub для рассылки предложений экземплярам core-app; token bucket на каждую СК")

# ---------------------------------------------------------------- new relationships
# Web app <- core-app: WebSocket stream of offers (new arrow next to the REST one).
add_edge(core_app, web, "Поток предложений по заявке ОСАГО\n(сразу по мере ответа СК)", "WebSocket (WSS)",
         exit=(0.83, 0), entry=(0.83, 1), offset=(100, -50))
# core-app <-> Redis
add_edge(core_app, redis, "Pub/Sub: предложение → все экземпляры\n(у кого WebSocket-сессия клиента)",
         "Redis Pub/Sub", exit=(1, 0.1), entry=(0, 0.8), points=[(940, 443), (940, 322)], lx=0.1)
# Kafka <-> osago-aggregator
add_edge(kafka, osago, "Подписка: osago.requests", "Kafka consumer", async_=True,
         exit=(1, 0.25), entry=(0, 0.5), points=[(1360, 625), (1360, 385)], lx=0.6)
add_edge(osago, kafka, "Публикация osago.offers\n(по одному событию на ответ СК)", "Kafka: topic osago.offers",
         async_=True, exit=(0, 0.9), entry=(1, 0.75), points=[(1330, 437), (1330, 665)], lx=-0.6)
# osago-aggregator -> its db, Redis, insurers
add_edge(osago, osago_db, "Работа с данными", "TCP", exit=(0.85, 0), entry=(0.85, 1))
add_edge(osago, redis, "Распределённый rate limiter\nна каждую СК", "Redis", exit=(0, 0.1), entry=(1, 0.92))
add_edge(osago, by_id[P + "11"], "Создать заявку на ОСАГО,\nполучить предложение по заявке", "REST",
         exit=(0.9, 1), entry=(0, 0.8), points=[(1736, 560), (1880, 560), (1880, 816)], lx=0.3)

# ---------------------------------------------------------------- resilience-pattern markers
# Inbound web API of core-app (REST): rate limit per client + timeout.
add_pattern("Rate Limiter", 505, 352, label="Rate Limiter<br>5 заявок/мин")
add_pattern("TimeOut", 580, 352, label="TimeOut<br>2 с")
# WebSocket session: reconnect with backoff + idle timeout, then REST re-read of offers.
add_pattern("Retry", 765, 352, label="Retry<br>reconnect")
add_pattern("TimeOut", 840, 352, label="TimeOut<br>60 с")
# Kafka producers/consumers: retries, DLQ.
add_pattern("Retry", 1135, 692, label="Retry + DLQ")
# osago-aggregator -> insurer adapters (the main hot path).
add_pattern("TimeOut", 1795, 312, label="TimeOut<br>5 с / 3 с")
add_pattern("Retry", 1795, 364, label="Retry<br>3× backoff")
add_pattern("Circuit Breaker", 1795, 416, label="Circuit<br>Breaker")
add_pattern("Rate Limiter", 1795, 468, label="Rate Limiter<br>по договору")

# ---------------------------------------------------------------- notes
legend_note.set("value",
    "<b>Обозначения</b><br>"
    "<font color='#0E7DAD'>- - -&gt;</font> асинхронное взаимодействие через Kafka (event streaming)<br>"
    "——&gt; синхронный вызов (REST / WebSocket / TCP)<br>"
    "<br><b>Паттерны отказоустойчивости</b> (иконки у стрелок):")
move(legend_note, y=690, h=200)
for i, name in enumerate(("TimeOut", "Retry", "Rate Limiter", "Circuit Breaker")):
    add_pattern(name, 55 + i * 70, 785, size=26)
move(decisions_note, y=900)
decisions_note.set("value", decisions_note.get("value").replace("<b>Решения</b>", "<b>Решения (задание 3)</b>"))
add_note(
    "<b>Решения (задание 4, ОСАГО)</b><br>"
    "1. osago-aggregator — отдельный сервис с собственной БД: заявка, id в каждой СК, дедлайн 60 с, "
    "lease опроса и предложения должны переживать рестарт и быть видны всем экземплярам.<br>"
    "2. API для core-app — события Kafka: команда osago.request (через outbox core-app) и события "
    "osago.offers (одно на каждый ответ, отказ или таймаут СК); ключ — id заявки, порядок внутри "
    "заявки сохраняется партиционированием.<br>"
    "3. API для веб-приложения: REST POST создаёт заявку и возвращает id; WebSocket отдаёт "
    "предложения сразу по приходу; REST GET возвращает текущий список при переподключении.<br>"
    "4. Несколько экземпляров: предложение приходит в один экземпляр core-app, а WebSocket клиента "
    "открыт на другом — Redis Pub/Sub рассылает событие всем; лимит вызовов СК общий на все "
    "экземпляры osago-aggregator — token bucket в Redis; опрос одной заявки ведёт один экземпляр "
    "(lease в БД, перехват при падении).<br>"
    "5. Паттерны: Rate Limiter и TimeOut на входе в core-app; Retry (reconnect) и TimeOut 60 с на "
    "WebSocket; Retry + DLQ у продюсеров и консьюмеров Kafka; на адаптерах СК — TimeOut (5 с create, "
    "3 с poll), Retry 3× с backoff только для идемпотентного create, Circuit Breaker на каждую СК "
    "(50 % ошибок из 20 вызовов → открыт 30 с), Rate Limiter по договору с СК.",
    40, 1250, 300, 430)

tree.write(OUT, encoding="utf-8", xml_declaration=False)
print("written", OUT)
