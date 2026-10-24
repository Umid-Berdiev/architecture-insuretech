# Задание 2. Динамическое масштабирование контейнеров

## Файлы

| Файл | Назначение |
|---|---|
| `namespace.yaml` | Namespace `insuretech`, в котором развёрнуты все ресурсы задания. |
| `deployment.yaml` | Deployment тестового приложения: 1 реплика, порт 8080, `requests.memory: 20Mi`, `limits.memory: 30Mi`, probes на `GET /`. |
| `service.yaml` | Service `scaletestapp` (NodePort, порт 8080) для доступа к приложению. |
| `hpa.yaml` | HorizontalPodAutoscaler (autoscaling/v2) по утилизации памяти: цель 80 %, min 1, max 10. |
| `locustfile.py` | Сценарий нагрузки из задания (`GET /`, пауза 1–5 с). |
| `locust-job.yaml` | ConfigMap с этим же locustfile и Job, запускающий Locust внутри кластера (см. «Нагрузка»). |
| `logs/` | Выгрузки `kubectl`: history HPA, события масштабирования, список подов, `kubectl top`, итог Locust. |
| `screenshots/` | Скриншоты Kubernetes Dashboard до и после масштабирования. |

## Как воспроизведено

```bash
minikube delete && minikube start --driver=docker
minikube addons enable metrics-server
minikube addons enable dashboard

kubectl apply -f namespace.yaml -f deployment.yaml -f service.yaml -f hpa.yaml
minikube service scaletestapp -n insuretech --url      # http://127.0.0.1:<port>
curl $URL/            # Идентификатор пода: scaletestapp-…
curl $URL/metrics     # http_requests_total …

kubectl apply -f locust-job.yaml                         # нагрузка
kubectl -n insuretech get hpa -w                         # наблюдение
minikube dashboard
```

## Почему `requests.memory: 20Mi`

HPA считает утилизацию памяти как отношение фактического потребления к **request** контейнера,
а не к limit. Задание фиксирует только limit (30Mi); без request метрика `Utilization`
не вычисляется вовсе. Request 20Mi даёт порог масштабирования 80 % × 20Mi = 16Mi, то есть
HPA добавляет реплики заметно раньше, чем под упирается в limit 30Mi и перезапускается по OOM.

В `hpa.yaml` дополнительно задано поведение: scale-up без окна стабилизации по 2 пода за 15 с
(быстрая реакция на пик), scale-down по 1 поду за 30 с с окном 120 с (без «дребезга» после спада).

## Особенности окружения и отклонения от инструкции

1. **Образ приложения.** `ghcr.io/yandex-practicum/scaletestapp:latest` собран только под
   `linux/amd64`; на Apple Silicon под эмуляцией qemu бинарник Go падает с SIGSEGV в `netpoll`
   (и в minikube, и в Docker на хосте). Поэтому тот же исходный код
   (github.com/Yandex-Practicum/scaletestapp, Dockerfile без изменений) собран под `linux/arm64`
   и загружен в кластер:
   ```bash
   docker build --platform linux/arm64 -t scaletestapp:local <путь к исходникам>
   minikube image load scaletestapp:local
   ```
   В `deployment.yaml` указан `image: scaletestapp:local` с `imagePullPolicy: IfNotPresent`.
   На amd64-хосте достаточно вернуть образ из ghcr.io.
2. **Образы из registry.k8s.io** не скачиваются изнутри узла minikube (корпоративный TLS-перехват),
   поэтому образ metrics-server загружен через `minikube image load`, а у Deployment аддона убран
   digest из ссылки на образ (`kubectl -n kube-system set image deployment/metrics-server …:v0.8.1`).
3. **Нагрузка.** Запуск `locust` на хосте через `minikube service --url` не подходит: на macOS
   с docker-драйвером этот URL — одиночный SSH-туннель, который при 1500 пользователях отбрасывал
   ~97 % запросов (`RemoteDisconnected`), и нагрузка до подов не доходила. Поэтому Locust запущен
   **внутри кластера** (`locust-job.yaml`) с тем же `locustfile.py` в headless-режиме:
   3000 пользователей, прирост 30 польз./с, 12 минут, цель — Service `scaletestapp` по DNS-имени.
   Так запросы распределяются kube-proxy по всем подам, как в реальной эксплуатации.
4. В задании сказано «количество реплик базы данных»; базы данных в тестовом стенде нет —
   масштабируется Deployment `scaletestapp`.

## Результат

Хронология из `logs/hpa-describe.log` и `logs/hpa-watch.log` (время UTC):

| Событие | Память (среднее к request) | Реплики |
|---|---|---|
| До нагрузки | 23 % | 1 |
| Старт нагрузки, через ~1 мин | 116 % | 1 → 2 |
| In-cluster Locust, 3000 пользователей | > 80 % | 2 → 3 → 5 → 7 → 9 |
| После окончания нагрузки (12:08 UTC) | 77 % → 51 % | 9 → 8 → 7 → 6 → 5 → 4 → 3 → 2 за ~10 мин, далее до 1 |

Пока HPA не успел добавить реплики, несколько подов под пиковой нагрузкой доходили до 28–29Mi и
перезапускались по OOM (см. `Restarts` в `logs/pods-final.log`) — это ровно та проблема из
условия задания, которую устраняет автоматическое масштабирование: после выхода на 9 реплик
потребление на под вернулось в норму, рестарты прекратились.

Скриншоты:

- `screenshots/01-deployment-2-replicas.png` — первое срабатывание HPA, 2 реплики.
- `screenshots/02-deployment-scaled-out.png` — Deployment на 9 репликах, раздел Events с цепочкой
  `SuccessfulRescale` от HPA и `ScalingReplicaSet` от deployment-controller.
- `screenshots/03-pods-scaled-out.png` — список подов и графики CPU/Memory по namespace.
- `screenshots/04-replicaset-scaled-out.png` — ReplicaSet 9/9.
- `screenshots/05-deployment-scaled-in.png` — уменьшение числа реплик после снятия нагрузки
  (`SuccessfulRescale … All metrics below target`). Спад плавный: по 1 поду за 30 с с окном 120 с,
  а Go-процесс отдаёт память ОС не сразу, поэтому утилизация снижается ступенями.
