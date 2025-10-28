Great — below is a comprehensive, hackathon-ready **System Design Document** for the enhanced **PublicBridge AI**. It's engineered to be actionable: developer-friendly, judge-friendly, and honest about risks. It prescribes what to change, why, and exactly how to implement and integrate the AI features with your existing Django codebase.

I’ve organized it so you can give it to engineers and start executing immediately (migrations, microservices, endpoints, CI, deployment steps, and a 30-day workplan). I call out “must-do” security items and conservative design choices (the devil’s-advocate part) so judges see you built responsibly — not just prettified AI.

# PublicBridge AI — System Design Document (Hackathon Edition)

---

## 1. Document Purpose & Scope

**Purpose:** Provide a full system design for integrating AI capabilities into the existing PublicBridge platform—covering architecture, data model changes, microservices, APIs, deployment, security, testing, monitoring, and a practical implementation plan for the hackathon.

**Scope:**

* Integrate AI modules: classification, sentiment & urgency scoring, summarization, translation.
* Ensure auditable, explainable AI decisions.
* Add admin workflow (review queue, overrides), area summaries, and hotspots.
* Keep existing features intact; migrate DB where needed.
* Deliver a reproducible demo and production-ready design decisions.

**Out-of-scope:** Full production hardened scaling (beyond recommended steps), long-term model retraining pipelines at enterprise scale (we provide a baseline).

---

## 2. High-Level Architecture

### 2.1 Architecture Summary

* Keep Django as the core application (monolith) for UIs and APIs.
* Add an `AI Gateway` microservice (FastAPI) to host and orchestrate AI model endpoints.
* Use Celery workers + Redis for asynchronous processing (report processing, batch summaries).
* Use persistent object storage (S3 / MinIO) for attachments and model artifacts.
* Add Prometheus/Grafana and centralized logging (ELK/Loki) for observability.
* Use Docker Compose for hackathon demo, Kubernetes recommended for production.

### 2.2 ASCII Diagram

```
+-----------------+        +-----------------+        +------------------+
|   User Browser  | <----> |  Django WebApp  | <----> |   Admin Dashboard|
+-----------------+        +-----------------+        +------------------+
        |                         |  ^  \
        | WebSocket/HTTP/REST     |  |   \---> [Audit Logs / DB]
        v                         |  |
+-----------------+               |  |                  +----------------+
|  Mobile / Chat  |               v  |                  |  Postgres/MySQL|
+-----------------+           +-----------+             +----------------+
                             |  Redis     | <--- Celery ---|
                             | (Channels/ |                 |
                             |   Broker)  |                 v
                             +-----------+             +----------------+
                                 ^  |                   |   S3 / MinIO   |
                                 |  |                   +----------------+
                                 |  |                           ^
                                 v  v                           |
                          +-----------------+        +---------------------+
                          |  Celery Worker  | <----> |   AI Gateway (API)  |
                          +-----------------+        |  (FastAPI / Torch)  |
                                                     +---------------------+
```

---

## 3. Key Design Principles & Constraints (Devil’s-Advocate)

1. **Conservative automation:** AI only *suggests* — humans make final legal/urgent decisions. All AI decisions must be auditable and overridable.
2. **Explainability:** Provide token-level attributions or top-phrases plus model version metadata for each AI decision.
3. **Privacy-by-default:** PII redaction in public exports; role-based access for full data.
4. **Incremental rollout:** Feature flags for AI modules to enable gradual tests and fallback.
5. **Reproducibility:** Use Dockerized model serving and store model artifacts with hashes for provenance.

---

## 4. Component Design & Responsibilities

### 4.1 Django (Core App)

* Responsibilities:

  * Serve web UI and REST API endpoints for reports, users, and admin.
  * Enqueue `process_report` tasks to Celery.
  * Store report records and AI outputs.
  * Provide review/override endpoints for admins.
* Changes:

  * Add AI fields to `Report` model.
  * Add `ReportAudit` model for audit logs.
  * Add Celery config and tasks.

### 4.2 AI Gateway (Microservice)

* Tech: FastAPI + PyTorch/Hugging Face models (or ONNX for speed).
* Endpoints:

  * `POST /v1/classify` → classification + probabilities + explanation
  * `POST /v1/sentiment` → sentiment score
  * `POST /v1/urgency` → urgency score
  * `POST /v1/translate` → translated text
  * `POST /v1/summarize` → area summary
* Responsibilities:

  * Load model artifacts, handle inference requests, return explanations and model metadata.
  * Provide health and metrics endpoints.
* Notes:

  * Return `model_version`, `inference_time_ms`, and `explanation`.

### 4.3 Celery Workers

* Responsibilities:

  * Orchestrate AI calls asynchronously.
  * Retry on transient failures.
  * Update DB with AI outputs and write audit logs.
  * Trigger notifications (via Channels) when urgency threshold exceeded.

### 4.4 Redis

* Use for channel layers (Django Channels) and as Celery broker.
* Configure persistence and secure access in production.

### 4.5 Postgres / MySQL

* Use Postgres with PostGIS recommended (spatial index) — but MySQL is supported; add spatial index.
* Add migrations for new AI fields and indices.

### 4.6 Object Storage (S3 / MinIO)

* Store attachments and model artifacts.
* Configure signed URLs for secure access.

### 4.7 Observability & Logging

* Prometheus/Grafana for metrics (latency, error rates).
* Loki/ELK for logs. Include model inference logs and DB write logs.
* Create dashboards for AI latency and classification distribution.

---

## 5. Data Model Changes (Detailed)

### 5.1 New/Updated Models

**Reports** — additions (Django fields):

* `classification = JSONField(null=True, default=dict)`
* `primary_label = CharField(max_length=64, null=True)`
* `classification_confidence = FloatField(null=True)`
* `sentiment_score = FloatField(null=True)`  # -1..1 or 0..1 consistent
* `urgency_score = FloatField(null=True)`   # 0..10
* `ai_model_version = CharField(max_length=64, null=True)`
* `ai_explanation = JSONField(null=True)`   # tokens and weights
* `ai_processed_at = DateTimeField(null=True)`
* `language = CharField(max_length=16, default='auto')`

**ReportAudit**

```python
class ReportAudit(models.Model):
    id = UUIDField(primary_key=True, default=uuid4)
    report = ForeignKey(Report, on_delete=models.CASCADE)
    action = CharField(max_length=64)  # "AI_CLASSIFY", "OVERRIDE", "SUMMARY_GENERATED"
    data = JSONField()  # payload snapshot
    user = ForeignKey(User, null=True)  # null if automated
    timestamp = DateTimeField(auto_now_add=True)
    model_version = CharField(max_length=64, null=True)
    payload_hash = CharField(max_length=128)  # hash of text input for provenance
```

**AreaSummary**

* `area_id`, `period_start`, `period_end`, `summary_text`, `generated_by`, `generated_at`

### 5.2 Migration SQL (example)

```sql
ALTER TABLE reports_report ADD COLUMN classification JSON DEFAULT '{}';
ALTER TABLE reports_report ADD COLUMN primary_label VARCHAR(64);
ALTER TABLE reports_report ADD COLUMN classification_confidence FLOAT;
ALTER TABLE reports_report ADD COLUMN sentiment_score FLOAT;
ALTER TABLE reports_report ADD COLUMN urgency_score FLOAT;
ALTER TABLE reports_report ADD COLUMN ai_model_version VARCHAR(64);
ALTER TABLE reports_report ADD COLUMN ai_explanation JSON;
ALTER TABLE reports_report ADD COLUMN ai_processed_at DATETIME;
ALTER TABLE reports_report ADD COLUMN language VARCHAR(16) DEFAULT 'auto';

CREATE TABLE reports_reportaudit (
  id UUID PRIMARY KEY,
  report_id UUID REFERENCES reports_report(id),
  action VARCHAR(64),
  data JSON,
  user_id UUID NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  model_version VARCHAR(64),
  payload_hash VARCHAR(128)
);
```

---

## 6. API Contracts

### 6.1 Django APIs (existing + new)

* `POST /api/reports/` — create new report (existing)
* `GET /api/reports/` — list reports with filter params (status, label, urgency)
* `GET /api/reports/{id}/` — detail, includes AI fields
* `POST /api/reports/{id}/override` — body: `{ "primary_label": "...", "urgency_score": x, "note": "..." }`
* `GET /api/area-summary/?area_id=...&period=...` — get summary

### 6.2 AI Gateway API (example request/response)

**Request**

```
POST /v1/classify
{
  "report_id": "uuid",
  "text": "There is a collapsed bridge on ABC rd.",
  "attachments_meta":{"images":2},
  "location":{"lat":-1.286389,"lon":36.817223},
  "language":"sw"
}
```

**Response**

```
{
  "report_id":"uuid",
  "primary_label":"infrastructure",
  "labels":[{"label":"infrastructure","score":0.92},{"label":"road","score":0.65}],
  "classification_confidence":0.92,
  "sentiment": -0.12,
  "urgency": 8.4,
  "explanation": {"top_tokens":[["collapsed", 0.40],["bridge",0.32]]},
  "model_version":"distilbert_v1_2025-10-20",
  "inference_ms": 204
}
```

---

## 7. AI Model Design & Training Plan

### 7.1 Label Taxonomy (recommended)

* `infrastructure`, `water_supply`, `health`, `education`, `sanitation`, `electricity`, `security`, `corruption`, `traffic`, `welfare`

Limit labels to 6–10 to maintain accuracy for hackathon.

### 7.2 Datasets

* Seed data: export 1k-3k historical reports. Anonymize PII.
* Augmentation: paraphrase, translate back-and-forth, generate synthetic samples for low-frequency labels.
* Labeling: internal labeling + quick crowdsource (team + volunteers). Use label tool (Label Studio or CSV).

### 7.3 Models (baseline & production)

* **Baseline (Hackathon)**:

  * Classification: `distilbert-base-multilingual-cased` fine-tuned for multi-class (or multi-label).
  * Sentiment: TF-IDF + LightGBM or small transformer head.
  * Urgency: regression via LightGBM on features (text embedding + attachments_count + time_of_day + label).
  * Summarization: `t5-small` or `facebook/bart-large-cnn` (fine-tune if time permits), else use Hugging Face hosted API.
* **Production**:

  * Convert to ONNX for faster CPU inference or use TorchServe with GPU.

### 7.4 Explainability

* Use `Captum` for token attributions or `LIME` to show top contributing tokens. Return top-5 tokens and their contributions.

### 7.5 Metrics & Targets (MVP)

* Classification macro-F1 ≥ 0.70 (target ≥ 0.75 if possible).
* Urgency RMSE vs human label ≤ 2 (scale 0–10).
* Summarization human rating ≥ 3/5 on clarity/usefulness by domain reviewer.

---

## 8. Integration & Implementation Steps (Concrete Tasks)

### Phase A — Prep & Safety (Days 0–2)

* Remove hardcoded credentials, set DEBUG=False. Add `.env.template`.
* Add Redis & Celery configurations to settings.
* Create `feature/ai-integration` branch.

### Phase B — DB & Backend Changes (Days 2–5)

* Add fields to `Report` model and create migrations.
* Introduce `ReportAudit` and `AreaSummary` models.
* Add API endpoint for override and area summary.

### Phase C — AI Gateway & Celery (Days 3–10)

* Scaffold FastAPI `ai_gateway` with required endpoints and Dockerfile.
* Add Celery tasks to Django to call AI Gateway.
* Wire Redis and test end-to-end with stub responses.

### Phase D — Models (Days 5–15)

* Prepare seed dataset; fine-tune DistilBERT.
* Containerize model and serve behind FastAPI.
* Implement explainability and return token attributions.

### Phase E — Admin UI & Workflow (Days 10–20)

* Update admin dashboard: show `primary_label`, `urgency_score`, `explain` modal, and override controls.
* Add review queue for items flagged as high urgency or low confidence.

### Phase F — Summaries & Hotspots (Days 15–24)

* Implement scheduled `generate_area_summary` Celery job (daily/weekly).
* Implement simple hotspot detection: KDE + Gi* (PySAL) over recent period; display on map.

### Phase G — Testing, Observability, Demo (Days 20–30)

* End-to-end tests and demo dataset.
* Add monitoring dashboards, configure logging.
* Prepare pitch + recorded backup demo.

---

## 9. Security & Privacy Checklist (Non-Negotiable)

1. **Config & Secrets**

   * Remove hardcoded DB creds. Use environment variables and secret manager.
   * `DEBUG=False` in production/demo server.
2. **Authentication & RBAC**

   * Enforce role-based access: public users vs authenticated citizens vs ministry admins vs super-admin.
   * Secure override endpoints (audit every override).
3. **Data Protection**

   * PII redaction in public and exported summaries.
   * Encrypt sensitive data at rest (DB-level encryption) and in transit (TLS).
4. **Audit & Provenance**

   * Record `ReportAudit` entries for each AI decision, override, summary generation, and file access.
5. **Rate limiting & Abuse Protection**

   * Add rate-limiting to prevent spam or adversarial inputs.
6. **Model Safety**

   * Add content filters to block harmful or illegal content before model processing.
7. **CORS & CSRF**

   * Proper CORS config for APIs; enable CSRF for form submissions.
8. **Third-party keys**

   * Manage Nominatim / HF API keys securely; avoid embedding in client.

---

## 10. CI/CD & Deployment

### 10.1 CI Pipeline (GitHub Actions example)

* `pull_request` triggers:

  * Lint (flake8), unit tests, Django migrations check.
  * Build Docker images for `django-app` and `ai_gateway`.
  * Push images to registry on `main` merge.
* `main` branch deployment:

  * Deploy to demo server via SSH or to a Kubernetes cluster using `kubectl` / Helm.

### 10.2 Docker Compose (Hackathon)

Provide `docker-compose.yml` with services:

* `django-app`, `db` (MySQL/Postgres), `redis`, `celery-worker`, `ai_gateway`, `minio`, `nginx`.

### 10.3 Production

* K8s with HPA, use managed DB, AWS S3, and load balancer.
* Use cert-manager for TLS on ingress.

---

## 11. Observability & Monitoring

### 11.1 Metrics to monitor

* Number of reports processed / hr.
* AI inference latency (per model endpoint).
* AI classification distribution (per label).
* Celery queue length and task failure rates.
* Error rates (500s), DB slow queries.

### 11.2 Alerts

* Celery retry > threshold.
* Inference latency > 2s per request.
* High error rate for AI Gateway.

### 11.3 Logging

* Structured logs with `request_id`, `report_id`, `model_version`.
* Retain audit logs for regulatory compliance.

---

## 12. Testing & Validation Plan

### 12.1 Unit Tests

* Celery tasks mock AI responses.
* API endpoints: create report, override, get summary.

### 12.2 Integration Tests

* End-to-end flow: submit report → Celery processes → DB updated → notification sent.

### 12.3 Model Tests

* Holdout test set with metrics: confusion matrix, precision/recall, F1.
* Test explainability output for consistency.

### 12.4 User Acceptance Testing

* Simulate admin triage sessions and measure triage time improvements.

---

## 13. Demo & Pitch Plan (Concrete)

**Goal:** 2–3 minute live demo + 1 recorded 2-minute backup.

**Demo Steps**

1. Preload demo DB with 50 synthesized reports (mix of languages and urgency levels).
2. Live: Submit a Swahili report (mobile form).

   * Show real-time WebSocket notification in admin UI.
   * Show AI fields populate (translation, label, urgency, explain).
3. Admin review: override low-confidence label. Show audit log entry.
4. Generate and download area summary PDF.
5. Show hotspot map (KDE overlay) with flagged areas.

**Slides:** Problem → Approach → Demo → Metrics → Roadmap → Ask (pilot support / data access).

---

## 14. Acceptance Criteria (For Hackathon Judges)

* End-to-end flow works (report → AI → dashboard) for at least 90% demo inputs.
* Admin override logged and visible with model version and explanation.
* At least one area summary generated and downloadable.
* Multilingual input (Swahili or Sheng) is translated & classified correctly in demo cases.
* Demonstrate how AI suggestions reduce triage steps in a small simulated benchmark.

---

## 15. Risk Assessment & Mitigations (Honest view)

| Risk                                | Likelihood                | Impact             | Mitigation                                                                                |
| ----------------------------------- | ------------------------- | ------------------ | ----------------------------------------------------------------------------------------- |
| Misclassification of urgent reports | Medium                    | High               | Conservative thresholds, human-in-loop, immediate notifications for high-urgency phrases. |
| Data bias                           | High (if dataset limited) | Medium             | Seed diverse dataset and disclose limitations. Use active learning.                       |
| Model downtime in demo              | Medium                    | High               | Provide recorded demo backup; implement fallback TF-IDF baseline.                         |
| Privacy leakage in summaries        | Low/Medium                | High               | Redact PII; RBAC; export only aggregated fields publicly.                                 |
| Overpromising AI certainty          | High                      | High (legal/trust) | Be explicit in UI & pitch: AI aids triage only; humans make decisions.                    |

---

## 16. Roadmap & Sprint Plan (30 days — exact task list)

### Week 0 (Prep)

* Branch creation, fix security issues, initial env setup, create demo dataset.

### Week 1

* DB migrations, Celery and Redis integration, scaffold `ai_gateway` with stubs.
* Implement process_report Celery task to call stubs.

### Week 2

* Train baseline classification model and integrate real inference in AI gateway.
* Update admin UI to show AI fields.

### Week 3

* Summarization & translation integration.
* Explainability output and audit logging.
* Hotspot detection and map overlay.

### Week 4

* Testing (unit/integration), performance tuning, demo recording, finalize slides.

(Include per-day subtasks for the team—ask me to output a Gantt if you want.)

---



* VM (DigitalOcean/Hetzner) for demo: $10–$40/month (small)
* Redis & DB: t2.small equivalents
* Storage (MinIO): negligible for demo
* Model hosting: CPU-only sufficient; HF Inference API costs if used.
* Estimated hackathon budget: $0–$200 (use free tiers + team machines); production pilot likely $200–$1000+ / month depending on load and hosting choices.

---

## 18. Deliverables You Should Produce Before Hackathon Submission

1. Hosted demo endpoint (render) + fallback recorded demo link.
2. GitHub repo with `feature/ai-integration` branch &
3. Script to seed demo DB with 50+ synthetic reports.
4. README with how to run demo locally.
5. Model evaluation report (confusion matrix + metrics).

---

## 19. Checklist (Pre-demo: must pass)

* [ ] `DEBUG=False`
* [ ] No hardcoded credentials in repo
* [ ] Redis & Celery processing works locally
* [ ] AI Gateway responds with predictions for demo inputs
* [ ] Audit logs recorded on AI decisions & overrides
* [ ] Admin UI shows explanation modal
* [ ] Area summary PDF generation test passed
* [ ] Backup recorded demo exists

---

## 20. Appendix: Useful Code Snippets & Commands



```yaml
version: "3.8"
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: publicbridge
      POSTGRES_USER: pb
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data

  redis:
    image: redis:7

  django:
    build: .
    command: gunicorn publicbridge.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    env_file: .env
    volumes:
      - ./:/app
    depends_on:
      - db
      - redis

  celery:
    build: .
    command: celery -A publicbridge worker --loglevel=info
    env_file: .env
    depends_on:
      - redis
      - db

  ai_gateway:
    build: ./ai_gateway
    ports: ["8001:8000"]
    env_file: .env
    depends_on:
      - db

  minio:
    image: minio/minio
    command: server /data
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio123
    ports: ["9000:9000"]

volumes:
  db-data:
```

### Celery Task Example (already shown earlier) — use with retries and logging.

---

## Final Notes (Straight talk)

* This design gives you a **winning combination**: social impact, technical depth, and cautious operational controls. Judges like polished demos *and* teams who demonstrate domain understanding and safety awareness.
