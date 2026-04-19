# Deployment Guide

## 1. Build and publish image

GitHub Actions builds and pushes a GHCR image via:

- `.github/workflows/release-image.yml`
- Optional server deploy workflow: `.github/workflows/deploy-self-hosted.yml`

Image naming:

- `ghcr.io/<owner>/autonomous-news-broadcaster:latest` on default branch
- `ghcr.io/<owner>/autonomous-news-broadcaster:sha-<shortsha>` on each build
- `ghcr.io/<owner>/autonomous-news-broadcaster:<tag>` on tag pushes

## 2. Prepare host

1. Install Docker Engine + Docker Compose plugin.
2. Create deployment directory and copy files:
   - `docker-compose.prod.yml`
   - `.env.production.example` as `.env`
3. Edit `.env` with real secrets and channel credentials.
4. Set `USE_MOCK_INGESTORS=false` for production data only.

## 3. Run

```bash
export NEWSBOT_IMAGE=ghcr.io/<owner>/autonomous-news-broadcaster:latest
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

## 3b. One-click deploy from GitHub Actions

Configure repository secrets:

- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`
- `DEPLOY_PORT` (optional, default `22`)
- `DEPLOY_APP_DIR` (directory containing `docker-compose.prod.yml`)
- `GHCR_USER`
- `GHCR_PAT` (read:packages)

Then run workflow:

- `.github/workflows/deploy-self-hosted.yml`
- Input `image_tag` as `latest`, `sha-...`, or a release tag.

## 4. Verify

```bash
curl -sSf http://<host>:8000/health/live
curl -sSf http://<host>:8000/health/ready
curl -sSf http://<host>:8000/system/readiness
```

Expected:

- `/health/live` always returns status `live` when process is up.
- `/health/ready` returns HTTP 200 only when runtime readiness checks pass.
- `/system/readiness` includes detailed issues and component status.

## 5. Rollback

```bash
export NEWSBOT_IMAGE=ghcr.io/<owner>/autonomous-news-broadcaster:<previous-tag>
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

## 6. Data durability

- Runtime snapshots persist under `./state` on the host.
- Backends:
  - `STATE_BACKEND=json`
  - `STATE_BACKEND=sqlite`
- If switching to SQLite, legacy JSON snapshot is imported automatically at startup when present.
