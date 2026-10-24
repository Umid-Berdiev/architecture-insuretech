"""Generate the InsureTech to-be technology architecture diagram as draw.io XML.

Icons are taken from the Yandex Cloud draw.io libraries (services) so the
notation matches the as-is diagram.
"""
import base64
import os
import sys
import xml.etree.ElementTree as ET

ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
OUT = sys.argv[1]


def icon(name):
    svg = open(f"{ICON_DIR}/{name}.svg", "rb").read()
    return "data:image/svg+xml," + base64.b64encode(svg).decode()


# Hand-drawn "users" icon (blue hexagon with people), matching the as-is diagram.
USERS_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">'
    '<path d="M16 1 L29 8.5 L29 23.5 L16 31 L3 23.5 L3 8.5 Z" fill="#5282ff"/>'
    '<circle cx="12" cy="12.5" r="3" fill="#fff"/><circle cx="20" cy="12.5" r="3" fill="#fff"/>'
    '<path d="M6 22 c0-4 3-6 6-6 s6 2 6 6 z" fill="#fff"/>'
    '<path d="M14 22 c0-4 3-6 6-6 s6 2 6 6 z" fill="#fff"/></svg>'
)
USERS_ICON = "data:image/svg+xml," + base64.b64encode(USERS_SVG.encode()).decode()

ICONS = {
    "k8s": icon("Managed_Kubernetes"),
    "pg": icon("Managed_PostgreSQL"),
    "alb": None,  # filled below from library xml item
    "cdn": None,
    "dns": icon("Cloud_DNS"),
    "s3": icon("Object_Storage"),
    "mon": icon("Monitoring"),
    "vm": icon("Compute_Cloud"),
    "users": USERS_ICON,
    "backup": icon("Cloud_Backup"),
}
# ALB and CDN are stored as full mxGraph xml in the library; their image data
# was extracted separately into icons/ as well.
ICONS["alb"] = icon("Application_Load_Balancer")
ICONS["cdn"] = icon("CDN")

FONT = "fontFamily=Arial;"
S_COMP = ("rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ff5958;"
          "verticalAlign=bottom;spacingBottom=6;spacingLeft=6;spacingRight=6;fontSize=12;" + FONT)
S_BOX = ("rounded=1;arcSize=6;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#5282ff;"
         "verticalAlign=top;align=left;spacingLeft=48;spacingTop=4;fontSize=13;" + FONT)
S_BOX_BOTTOM = S_BOX.replace("verticalAlign=top", "verticalAlign=bottom").replace("spacingTop=4", "spacingBottom=4")
S_AZ = ("rounded=1;arcSize=6;whiteSpace=wrap;html=1;fillColor=#dbe5fb;strokeColor=none;"
        "verticalAlign=bottom;align=center;spacingBottom=6;fontSize=16;" + FONT)
S_REGION = ("rounded=1;arcSize=3;whiteSpace=wrap;html=1;fillColor=#f3f6fd;strokeColor=#5282ff;dashed=1;"
            "verticalAlign=top;align=left;spacingLeft=12;spacingTop=4;fontSize=16;" + FONT)
S_NOTE = ("shape=note;size=14;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
          "align=left;verticalAlign=top;spacing=8;fontSize=11;" + FONT)
S_ICON = "shape=image;imageAspect=0;aspect=fixed;image={};"
S_TEXT = "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=11;" + FONT
S_EDGE = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;strokeColor=#333333;"
          "fontSize=10;labelBackgroundColor=#ffffff;" + FONT)
S_HC = S_EDGE + "dashed=1;strokeColor=#ff5958;fontColor=#ff5958;"
S_REPL = S_EDGE + "strokeColor=#5282ff;fontColor=#1f3f99;"
S_MON = S_EDGE + "dashed=1;dashPattern=1 3;strokeColor=#999999;fontColor=#777777;endArrow=open;endFill=0;"

mxfile = ET.Element("mxfile", host="app.diagrams.net", type="device")
diagram = ET.SubElement(mxfile, "diagram", id="to-be", name="InsureTech to-be")
model = ET.SubElement(diagram, "mxGraphModel", dx="2000", dy="1200", grid="1", gridSize="10", guides="1",
                      tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1",
                      pageWidth="2339", pageHeight="1654", math="0", shadow="0")
root = ET.SubElement(model, "root")
ET.SubElement(root, "mxCell", id="0")
ET.SubElement(root, "mxCell", id="1", parent="0")

_ids = {}
ABS = {}  # id -> (x, y) absolute origin, for relative child placement


def vertex(cid, value, style, x, y, w, h, parent="1"):
    px, py = ABS.get(parent, (0, 0))
    c = ET.SubElement(root, "mxCell", id=cid, value=value, style=style, vertex="1", parent=parent)
    ET.SubElement(c, "mxGeometry", x=str(x - px), y=str(y - py), width=str(w), height=str(h)).set("as", "geometry")
    ABS[cid] = (x, y)
    return cid


def comp(cid, title, subtitle, ico, x, y, w, h, parent="1"):
    """Component box in the as-is notation: red border, icon on top, label below."""
    value = f"<b>{title}</b>" + (f"<br><font style='font-size:10px'>{subtitle}</font>" if subtitle else "")
    vertex(cid, value, S_COMP, x, y, w, h, parent)
    vertex(cid + "_i", "", S_ICON.format(ICONS[ico]), x + (w - 32) / 2, y + 8, 32, 32, cid)
    return cid


def box(cid, title, ico, x, y, w, h, parent="1", style=S_BOX):
    vertex(cid, title, style, x, y, w, h, parent)
    if ico:
        vertex(cid + "_i", "", S_ICON.format(ICONS[ico]), x + 8, y + 6, 32, 32, cid)
    return cid


_e = 0


def edge(src, dst, label="", style=S_EDGE, points=None, exit=None, entry=None, lx=None, off=None):
    global _e
    _e += 1
    st = style
    if exit:
        st += f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
    if entry:
        st += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
    c = ET.SubElement(root, "mxCell", id=f"e{_e}", value=label, style=st, edge="1", parent="1", source=src, target=dst)
    g = ET.SubElement(c, "mxGeometry", relative="1")
    if lx is not None:
        g.set("x", str(lx))
    g.set("as", "geometry")
    if off is not None:
        o = ET.SubElement(g, "mxPoint", x=str(off[0]), y=str(off[1]))
        o.set("as", "offset")
    if points:
        arr = ET.SubElement(g, "Array")
        arr.set("as", "points")
        for (px, py) in points:
            ET.SubElement(arr, "mxPoint", x=str(px), y=str(py))
    return f"e{_e}"


# ---------------------------------------------------------------- layout
# Title
vertex("title", "<b style='font-size:20px'>InsureTech — технологическая архитектура (to-be)</b>"
       "<br><font style='font-size:12px'>Целевые показатели: доступность 99,9 %, RTO 45 мин, RPO 15 мин, 24/7, "
       "одинаковое время загрузки страниц из всех регионов РФ</font>",
       S_TEXT, 40, 10, 900, 60)

# Clients
comp("browser", "Браузер пользователя", "регионы РФ, все часовые пояса", "users", 640, 90, 200, 100)
comp("partner", "Системы партнёров", "B2B API, квота 20 RPS на партнёра", "users", 900, 90, 200, 100)

# Global services (outside the region: DNS, CDN)
comp("dns", "Cloud DNS", "insuretech.ru → anycast-IP ALB<br>TTL 60 с (быстрое переключение)", "dns", 300, 230, 240, 100)
comp("cdn", "Yandex Cloud CDN", "edge-узлы в регионах РФ: статика SPA (JS/CSS/img),<br>HTTP/2, gzip/brotli, TLS termination на edge",
     "cdn", 1180, 230, 300, 100)

# Region container
vertex("region", "<b>Yandex Cloud — регион ru-central1</b>&nbsp;&nbsp;<font style='font-size:12px'>"
       "(один регион РФ; все сервисы ниже — региональные, разнесены по трём зонам доступности)</font>",
       S_REGION, 40, 370, 1740, 1200)

# ALB (regional, above AZs)
comp("alb", "Application Load Balancer (L7)", "региональный, anycast-IP, HTTPS-listener :443, "
     "active-active на 3 зоны; backend group = ingress-узлы всех зон, веса 1:1:1; "
     "rate-limit per partner (20 RPS)", "alb", 560, 400, 520, 100, "region")

# Availability zones
AZ = [("ru-central1-a", 70), ("ru-central1-b", 650), ("ru-central1-d", 1230)]
for name, x in AZ:
    vertex(f"az_{name[-1]}", f"<b>Зона доступности {name}</b>", S_AZ, x, 560, 530, 970, "region")

# Kubernetes regional cluster band (spans all three zones)
box("k8s", "<b>Managed Service for Kubernetes — кластер 1 (региональный)</b>&nbsp;&nbsp;"
    "<font style='font-size:11px'>мастер ×3 (по одному в каждой зоне), node group в каждой зоне, "
    "Cluster Autoscaler; один кластер вместо трёх независимых — см. комментарий ②</font>",
    "k8s", 90, 600, 1650, 360, "region")

for name, x in AZ:
    z = name[-1]
    box(f"ng_{z}", f"<b>Node group {name}</b><br><font style='font-size:11px'>2–6 узлов, autoscaling</font>",
        "vm", x + 30, 650, 470, 300, "k8s")
    comp(f"ns_{z}", "InsureTech namespace",
         "ingress-nginx ×1 (NodePort) · core-app ×2 · client-info ×2<br>"
         "ins-product-aggregator ×2 · ins-comp-settlement ×1<br>"
         "HPA (CPU / RPS), podAntiAffinity по зонам, PDB,<br>"
         "<font color='#ff5958'>readiness / liveness probes: GET /actuator/health, 10 с</font>",
         "k8s", x + 60, 700, 410, 210, f"ng_{z}")

# PostgreSQL regional cluster band
box("pgc", "<b>Managed Service for PostgreSQL — кластер из 3 хостов</b>&nbsp;&nbsp;"
    "<font style='font-size:11px'>HA на базе Patroni + DCS: автоматический failover ≈ 30 с; "
    "rw-FQDN / ro-FQDN для приложений; connection pooler (Odyssey) на каждом хосте; "
    "без шардирования — см. комментарий ⑥</font>",
    "pg", 90, 1000, 1650, 300, "region")

comp("pg_a", "PostgreSQL — master (RW)", "ru-central1-a · запись и чтение<br>архивация WAL непрерывно (archive_timeout 5 мин)",
     "pg", 120, 1050, 420, 130, "pgc")
comp("pg_b", "PostgreSQL — синхронная реплика", "ru-central1-b · кандидат на failover<br>RPO ≈ 0 (synchronous_commit = on)",
     "pg", 700, 1050, 420, 130, "pgc")
comp("pg_d", "PostgreSQL — асинхронная реплика", "ru-central1-d · чтение (ro-FQDN): каталог продуктов, тарифы, отчёты",
     "pg", 1280, 1050, 420, 130, "pgc")

vertex("pg_note", "<font style='font-size:11px'>Вертикальное масштабирование хоста БД (vCPU/RAM/SSD) — достаточно для 50 GB; "
       "горизонтально — только чтение через реплики</font>", S_TEXT, 120, 1210, 1600, 30, "pgc")

# Backups (Object Storage) and static bucket
comp("s3_backup", "Object Storage — бэкапы БД", "ежедневный полный бэкап + непрерывный WAL-архив → PITR на любую точку;<br>"
     "хранение 7 дней; бакет реплицируется по 3 зонам региона", "s3", 120, 1340, 520, 110, "region")
comp("s3_static", "Object Storage — статика InsureTech Web", "origin для CDN: React SPA (index.html, JS, CSS, img);<br>"
     "деплой через CI/CD, версии по hash", "s3", 1180, 1340, 480, 110, "region")

# Monitoring
comp("mon", "Yandex Monitoring + Alerting", "метрики ALB / k8s / PostgreSQL, SLO 99,9 %, "
     "алерты on-call (Telegram / телефон) при ошибках HC", "mon", 1180, 400, 400, 100, "region")

# ---------------------------------------------------------------- edges
edge("browser", "dns", "1. DNS-запрос: insuretech.ru", exit=(0.25, 1), entry=(0.5, 0))
edge("browser", "cdn", "2. Статика SPA (HTTPS)<br>ближайший edge-узел", exit=(0.75, 1), entry=(0.25, 0))
edge("browser", "alb", "3. REST API / HTML (HTTPS, HTTP/2)", exit=(0.5, 1), entry=(0.3, 0))
edge("partner", "alb", "REST API (HTTPS) · API-ключ", exit=(0.5, 1), entry=(0.7, 0))
edge("cdn", "s3_static", "origin при cache-miss (HTTPS)", points=[(1768, 280), (1768, 1395)], exit=(1, 0.5), entry=(1, 0.5), lx=-0.9)

for name, x in AZ:
    z = name[-1]
    ex_t = {"a": 0.15, "b": 0.5, "d": 0.85}[z]
    ex_h = {"a": 0.05, "b": 0.6, "d": 0.95}[z]
    tx_t = x + 60 + 0.6 * 410
    tx_h = x + 60 + 0.85 * 410
    edge("alb", f"ns_{z}", "HTTPS → ingress (NodePort)", exit=(ex_t, 1), entry=(0.6, 0),
         points=[(560 + ex_t * 520, 540), (tx_t, 540)], lx=-1, off=(0, 22))
    edge("alb", f"ns_{z}", "health check: GET /healthz<br>каждые 2 с, таймаут 1 с,<br>3 неудачи → зона исключается",
         S_HC, exit=(ex_h, 1), entry=(0.85, 0), points=[(560 + ex_h * 520, 585), (tx_h, 585)], lx=-1, off=(0, 60))

edge("ns_a", "pg_a", "RW: rw-FQDN кластера<br>TCP 6432 (Odyssey)", exit=(0.5, 1), entry=(0.5, 0))
edge("ns_b", "pg_a", "RW: rw-FQDN", exit=(0.3, 1), entry=(0.8, 0), points=[(805, 980), (456, 980)])
edge("ns_d", "pg_a", "RW: rw-FQDN", exit=(0.3, 1), entry=(0.9, 0), points=[(1385, 985), (498, 985)])
edge("ns_d", "pg_d", "RO: ro-FQDN (тарифы, продукты)", exit=(0.7, 1), entry=(0.5, 0))

edge("pg_a", "pg_b", "синхронная репликация (streaming)", S_REPL, exit=(1, 0.4), entry=(0, 0.4))
edge("pg_b", "pg_d", "асинхронная репликация", S_REPL, exit=(1, 0.4), entry=(0, 0.4))
edge("pg_b", "pg_a", "Patroni: проверка лидера через DCS каждые 10 с;<br>нет ответа 30 с → promote синхронной реплики",
     S_HC, exit=(0, 0.75), entry=(1, 0.75))
edge("pg_a", "s3_backup", "WAL-архив + ежедневный full backup", exit=(0.5, 1), entry=(0.5, 0))

edge("alb", "mon", "метрики, статус HC", S_MON, exit=(1, 0.5), entry=(0, 0.5), lx=-0.2)
edge("k8s", "mon", "метрики подов и узлов, probes", S_MON, exit=(0.9, 0), entry=(0.5, 1), points=[(1575, 585), (1380, 585)])
edge("pgc", "mon", "метрики БД, состояние Patroni", S_MON, exit=(1, 0.3), entry=(0.7, 1), points=[(1752, 1090), (1752, 560), (1460, 560)], lx=0.3)

# ---------------------------------------------------------------- comments
NOTES = [
    ("① Стратегия масштабирования и отказоустойчивости",
     "Горизонтальное масштабирование: сервисы stateless, реплики подов (HPA по CPU и RPS) и узлы (Cluster Autoscaler) "
     "добавляются под нагрузку рекламной кампании; пиковые 50 RPS поиска / 10 RPS оформления / 250 RPS партнёров "
     "закрываются 2–3 репликами на зону. Вертикальное — только для хоста PostgreSQL (vCPU/RAM/SSD): объём 50 GB "
     "не требует распределённой БД.<br>"
     "Три зоны доступности обязательны: один зал/ВМ даёт SPOF, а 99,9 % (≤ 8,8 ч простоя в год) при RTO 45 мин "
     "недостижимы при отказе зоны. Все сервисы — региональные, деплой в ru-central1-a/b/d."),
    ("② Конфигурация Kubernetes: один региональный кластер",
     "Выбран один растянутый (региональный) кластер Managed Kubernetes с мастерами в трёх зонах и node group в каждой зоне, "
     "а не три независимых. Причины: один набор манифестов и один pipeline деплоя; один Service/Ingress — ALB видит "
     "все зоны как один backend group; podAntiAffinity + topologySpreadConstraints гарантируют реплики в каждой зоне; "
     "отказ зоны обрабатывает сам планировщик (пересоздание подов в живых зонах) без внешней оркестрации. "
     "Задержка между зонами одного региона < 2 мс, поэтому stretched-кластер не вносит накладных расходов. "
     "Независимые кластеры оправданы только при геораспределении между регионами — для РФ в Yandex Cloud доступен один регион."),
    ("③ Балансировка нагрузки и health checks",
     "Клиент → Cloud DNS (TTL 60 с) → anycast-IP ALB. ALB (L7) терминирует TLS, маршрутизирует по хостам/путям "
     "(/api/partner/* — отдельный backend с rate-limit 20 RPS на API-ключ) и распределяет запросы между ingress-узлами "
     "трёх зон (round robin, веса 1:1:1, locality-aware). Статика SPA — через CDN с edge-узлами в регионах РФ, "
     "поэтому время загрузки страницы не зависит от географии пользователя; API-запросы идут в один регион с одинаковой "
     "задержкой для всех.<br>Health checks (красный пунктир): ALB → ingress GET /healthz каждые 2 с, таймаут 1 с, "
     "3 неудачи = unhealthy, 2 успеха = healthy; kubelet → поды: readiness/liveness GET /actuator/health 10 с; "
     "Patroni → лидер PostgreSQL через DCS 10 с; CDN → origin (Object Storage) при cache-miss. Результаты HC — в Monitoring."),
    ("④ Failover-стратегия: active-active по трём зонам",
     "Все три зоны обслуживают трафик одновременно; «тёплого резерва» нет — это проще и дешевле, а переключение "
     "не требует ручных действий. Отказ зоны: ALB исключает её ingress через ≈ 6 с (3 × 2 с); клиент видит только "
     "ретрай запроса (SPA повторяет идемпотентные GET; POST оформления — через idempotency-key). Отказ ALB-узла — "
     "anycast-IP, прозрачно. Отказ мастера БД — Patroni за ≈ 30 с переводит синхронную реплику в master, rw-FQDN "
     "переключается автоматически, пулы соединений переподключаются. Итог: фактический RTO < 5 мин (требование 45 мин), "
     "RPO ≈ 0 для отказа зоны (требование 15 мин). CDN продолжает отдавать оболочку сайта даже во время failover бэкенда."),
    ("⑤ Конфигурация базы данных (RTO/RPO)",
     "Managed Service for PostgreSQL, 3 хоста по одному в зоне: master (a), синхронная реплика (b), асинхронная "
     "реплика для чтения (d). Кластер управляется Patroni (DCS — etcd/ZooKeeper управляемого сервиса): автоматический "
     "выбор лидера, fencing старого мастера, переключение FQDN. Синхронная репликация даёт RPO ≈ 0 при потере зоны; "
     "асинхронная реплика разгружает чтение тарифов и отчёты.<br>Резервное копирование: ежедневный полный бэкап + "
     "непрерывная архивация WAL (archive_timeout 5 мин) в Object Storage (реплицируется по трём зонам) → PITR на любую "
     "точку, RPO ≤ 5 мин даже при логической порче данных; восстановление 50 GB из бэкапа ≈ 15–20 мин, что укладывается "
     "в RTO 45 мин. Хранение бэкапов — 7 дней, еженедельная проверка восстановления."),
    ("⑥ Шардирование БД: не применяется",
     "Объём данных 50 GB и умеренная нагрузка (десятки RPS на запись) помещаются на один хост PostgreSQL с запасом "
     "на порядок; вертикальное масштабирование хоста и read-реплики закрывают рост на ближайшие годы. "
     "Шардирование добавило бы сложность (роутер, кросс-шардовые транзакции для «заявка + клиент», отсутствие "
     "внешних ключей, усложнение бэкапов) без выигрыша. Пересмотреть при > 1 TB или > 5 000 RPS на запись; "
     "естественный ключ шардирования на будущее — client_id (данные клиента и его заявки на одном шарде). "
     "Схемы сервисов уже разделены — при необходимости их можно вынести в отдельные кластеры по сервисам."),
]
nx, ny = 1810, 370
for i, (t, body) in enumerate(NOTES):
    h = 190 if i in (0, 5) else 215
    vertex(f"note{i}", f"<b>{t}</b><br>{body}", S_NOTE, nx, ny, 470, h)
    ny += h + 10

# Legend
vertex("legend", "<b>Обозначения</b><br>"
       "<font color='#ff5958'>▬ ▬</font> health check &nbsp;&nbsp; <font color='#5282ff'>▬▬</font> репликация БД &nbsp;&nbsp; "
       "<font color='#999999'>· · ·</font> метрики/алерты &nbsp;&nbsp; ▬▬ пользовательский трафик<br>"
       "Нотация: библиотеки Yandex Cloud (services / containers, окт. 2023)",
       S_TEXT, 40, 1580, 900, 50)

ET.ElementTree(mxfile).write(OUT, encoding="utf-8", xml_declaration=True)
print("written", OUT)
