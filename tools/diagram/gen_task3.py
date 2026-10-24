"""Build the Task 3 to-be C4 container diagram from the course's as-is diagram.

The source XML is kept untouched; this script removes the synchronous polling relationships,
adds Kafka, the aggregator database and the Transactional Outbox relay, and draws the new
event-streaming relationships dashed. Existing C4 shapes, styles and label templates are reused.
"""
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "InsureTech_C4_container-diagram_as-is.drawio.xml")
OUT = sys.argv[1]

P = "uZ0quFO-MIEIE11IO5jD-"  # id prefix used by the source diagram
ID = {
    "boundary": P + "1", "core_db": P + "2", "core_app": P + "3", "web": P + "4",
    "edge_core_db": P + "6", "insurers": P + "11", "aggregator": P + "16",
    "edge_aggr_insurers": P + "17", "edge_core_aggr": P + "18", "settlement": P + "19",
    "settlement_db": P + "28", "edge_settl_aggr": P + "33", "edge_settl_core": P + "34",
}

tree = ET.parse(SRC)
root_model = tree.getroot().find("diagram/mxGraphModel/root")
by_id = {el.get("id"): el for el in root_model}


def cell_of(obj):
    return obj.find("mxCell")


def geom_of(obj):
    return cell_of(obj).find("mxGeometry")


# ---------------------------------------------------------------- templates
container_style = cell_of(by_id[ID["core_app"]]).get("style")
db_style = cell_of(by_id[ID["core_db"]]).get("style")
edge_style = cell_of(by_id[ID["edge_core_aggr"]]).get("style")
container_label = by_id[ID["core_app"]].get("label")
db_label = by_id[ID["core_db"]].get("label")
edge_label = by_id[ID["edge_core_aggr"]].get("label")
ASYNC_STYLE = edge_style + "dashed=1;dashPattern=6 4;strokeColor=#0E7DAD;fontColor=#0E7DAD;"

_n = 0


def new_id():
    global _n
    _n += 1
    return f"task3-{_n}"


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
    return obj.get("id")


def add_edge(src, dst, desc, tech, async_=True, exit=None, entry=None, points=None, lx=None):
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
    c = ET.SubElement(obj, "mxCell", style=st, edge="1", parent="1", source=src, target=dst)
    g = ET.SubElement(c, "mxGeometry", width="160", relative="1")
    if lx is not None:
        g.set("x", str(lx))
    g.set("as", "geometry")
    if points:
        arr = ET.SubElement(g, "Array")
        arr.set("as", "points")
        for px, py in points:
            ET.SubElement(arr, "mxPoint", x=str(px), y=str(py))
    return obj.get("id")


def add_note(text, x, y, w, h):
    c = ET.SubElement(root_model, "mxCell", id=new_id(), value=text, vertex="1", parent="1",
                      style="shape=note;size=14;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
                            "align=left;verticalAlign=top;spacing=8;fontSize=11;fontColor=#333333;")
    g = ET.SubElement(c, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h))
    g.set("as", "geometry")


# ---------------------------------------------------------------- remove synchronous polling
for key in ("edge_core_aggr", "edge_settl_aggr", "edge_settl_core"):
    root_model.remove(by_id[ID[key]])

# ---------------------------------------------------------------- helpers for geometry
def move(obj_id, x=None, y=None, w=None, h=None):
    g = geom_of(by_id[obj_id])
    for k, v in (("x", x), ("y", y), ("width", w), ("height", h)):
        if v is not None:
            g.set(k, str(v))


def restyle(obj_id, extra):
    c = cell_of(by_id[obj_id])
    c.set("style", c.get("style") + extra)


# ---------------------------------------------------------------- make room: taller rows, wider boundary
move(ID["boundary"], w=1230, h=1080)
move(ID["core_app"], h=130)
move(ID["aggregator"], h=130)
move(ID["core_db"], y=830, h=140)
move(ID["settlement"], y=830, h=140)
move(ID["settlement_db"], y=1070)
for suffix in ("11", "12", "13"):           # the stacked "insurance companies" shapes
    g = geom_of(by_id[P + suffix])
    g.set("x", str(int(g.get("x")) + 120))

# ---------------------------------------------------------------- update existing elements
by_id[ID["core_app"]].set("c4Description",
    "Монолитное приложение:\n• показывает доступные страховые продукты\n• оформляет новые страховки\n"
    "• показывает купленные страховки\n• публикует policy.issued через outbox")
by_id[ID["core_db"]].set("c4Description",
    "Тарифы СК (локальная реплика), заявки клиентов на страховые продукты и таблица outbox "
    "с событиями policy.issued")
by_id[ID["aggregator"]].set("c4Description",
    "По расписанию опрашивает каждую СК независимо, хранит снимок каталога продуктов и тарифов "
    "и публикует изменения в Kafka. Синхронный API остаётся для запросов «здесь и сейчас» "
    "(например, предложения по ОСАГО)")
by_id[ID["settlement"]].set("c4Description",
    "Сервис взаиморасчётов со страховыми компаниями. Тарифы и реестр оформленных страховок "
    "получает из Kafka, а не по REST")
by_id[ID["edge_core_db"]].set("c4Description",
    "Работа с данными: страховка и событие\nв outbox пишутся в одной транзакции")
by_id[ID["edge_aggr_insurers"]].set("c4Description",
    "Плановый опрос каждой СК отдельным адаптером:\nтаймаут, retry, circuit breaker")


def reroute(edge_id, exit, entry, points, lx=None):
    """Replace the waypoints of an existing relationship so it avoids the new containers."""
    restyle(edge_id, f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
                     f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;")
    g = geom_of(by_id[edge_id])
    for arr in g.findall("Array"):
        g.remove(arr)
    arr = ET.SubElement(g, "Array")
    arr.set("as", "points")
    for px, py in points:
        ET.SubElement(arr, "mxPoint", x=str(px), y=str(py))
    if lx is not None:
        g.set("x", str(lx))


reroute(ID["edge_aggr_insurers"], (1, 0.25), (0, 0.5), [(1640, 462), (1640, 600)], lx=-0.55)
reroute(P + "32", (1, 0.5), (0, 0.85), [(1665, 900), (1665, 642)], lx=-0.55)

# ---------------------------------------------------------------- new containers
kafka = add_container(
    "Kafka", "Managed Service for Apache Kafka",
    "Топики: products (compacted, ключ — СК + продукт), policies (ключ — id страховки), DLQ; "
    "схемы событий — в Schema Registry",
    830, 605, 470, 80)
relay = add_container(
    "outbox-relay", "Kafka Connect, Debezium",
    "Читает outbox из core-db по WAL и публикует в Kafka (Transactional Outbox)",
    830, 725, 240, 90)
aggr_db = add_container(
    "ins-product-aggregator-db", "PostgreSQL",
    "Снимок каталога продуктов и тарифов по каждой СК, время и результат последнего опроса",
    1400, 560, 220, 110, db=True)

# ---------------------------------------------------------------- new relationships
add_edge(ID["aggregator"], kafka, "Публикация изменений\nкаталога", "Kafka: topic products",
         exit=(0.75, 1), entry=(0.9, 0))
add_edge(kafka, ID["core_app"], "Подписка: обновление\nлокальной реплики тарифов", "Kafka: topic products",
         exit=(0, 0.5), entry=(1, 0.75), points=[(780, 645), (780, 527)])
add_edge(kafka, ID["settlement"], "Подписка: тарифы и реестр\nоформленных страховок",
         "Kafka: topics products, policies", exit=(0.85, 1), entry=(0.65, 0))
add_edge(relay, kafka, "Публикация policy.issued", "Kafka: topic policies",
         exit=(0.5, 0), entry=(0.25, 1))
add_edge(ID["core_db"], relay, "Чтение outbox (CDC)", "Debezium PostgreSQL connector",
         exit=(0.75, 0), entry=(0, 0.5), points=[(670, 770), (805, 770)])
add_edge(ID["aggregator"], aggr_db, "Работа с данными", "TCP", async_=False,
         exit=(1, 0.75), entry=(0, 0.3))

# ---------------------------------------------------------------- legend and decisions
add_note(
    "<b>Обозначения</b><br>"
    "<font color='#0E7DAD'>- - -&gt;</font> асинхронное взаимодействие через Kafka (event streaming)<br>"
    "——&gt; синхронный вызов (REST / HTTP / TCP)",
    40, 690, 300, 70)
add_note(
    "<b>Решения</b><br>"
    "1. ins-product-aggregator больше не опрашивает 5–10 СК внутри синхронного запроса: опрос каждой СК "
    "идёт по расписанию, независимо, с таймаутом и circuit breaker; результат хранится в своей БД и "
    "публикуется в топик products.<br>"
    "2. core-app и ins-comp-settlement читают products из Kafka вместо REST-опроса раз в 15 мин / раз в сутки; "
    "compacted-топик даёт полный актуальный каталог новому потребителю.<br>"
    "3. Реестр оформленных страховок уходит в ins-comp-settlement событиями policy.issued, а не ночным REST-запросом.<br>"
    "4. Transactional Outbox применяется для policy.issued (страховка и событие пишутся в одной транзакции core-db, "
    "Debezium доставляет в Kafka). Для событий каталога outbox не нужен: это снимок, который переиздаётся при "
    "следующем опросе.<br>"
    "5. Синхронными остаются вызовы, где нужен ответ сразу: веб и партнёрский API → core-app, client-info, платежи, "
    "передача данных для взаиморасчётов в СК.",
    40, 780, 300, 330)

tree.write(OUT, encoding="utf-8", xml_declaration=False)
print("written", OUT)
