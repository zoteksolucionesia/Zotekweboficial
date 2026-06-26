# Sesión 2026-06-02 — SSO con el CRM LiliBauza: causa raíz y gotcha de tráfico

Registro del lado Zotek. El documento completo (incluye el CRM) está en:
`LiliBauza-admin/docs/SESION_2026-06-02_SSO_y_DarkMode.md`.

## Qué pasó

El SSO de entrada desde el CRM (`POST /api/auth/sso`) devolvía **401** de forma persistente
aunque `functions/.env` tenía el `PORTAL_SSO_SECRET` correcto y se redeployaba la función.

## Causa raíz (NO era el secreto)

El servicio Cloud Run `api-handler` (que respalda la Cloud Function Gen2 `api_handler`)
tenía el **100% del tráfico clavado en una revisión vieja** (`api-handler-00190-pal`) que
llevaba baked un secreto antiguo. Los redeploys creaban revisiones nuevas con el secreto
correcto, pero **el tráfico no migraba a ellas**.

### ⚠️ GOTCHA recurrente

`firebase deploy --only functions` a `zotek-ia` **no mueve el tráfico** a la nueva revisión
de `api-handler`. Tras CADA deploy de functions hay que verificar/forzar el tráfico:

```bash
# Ver qué revisión sirve realmente
gcloud run services describe api-handler --project zotek-ia --region us-central1 \
  --format="value(status.traffic)"

# Forzar 100% a la más nueva
NEW=$(gcloud run revisions list --service api-handler --project zotek-ia --region us-central1 \
  --sort-by="~metadata.creationTimestamp" --limit=1 --format="value(metadata.name)")
gcloud run services update-traffic api-handler --project zotek-ia --region us-central1 \
  --to-revisions ${NEW}=100
```

Si un cambio de env o de código "no toma efecto" tras desplegar, revisar PRIMERO el tráfico.

## Cambios de esta sesión en este repo

- `functions/.env` y `.env` (raíz): `PORTAL_SSO_SECRET` rotado a valor fuerte aleatorio.
- `www/portal/portal.js`: listener `message` para heredar **tema claro/oscuro y acento**
  del CRM en vivo cuando el portal va embebido.

  ⚠️ El check de `event.origin` debe aceptar **ambos** dominios de Firebase del CRM
  (`https://lilibauza-admin.web.app` **y** `https://lilibauza-admin.firebaseapp.com`).
  Con solo uno, el toggle de modo oscuro cambiaba el CRM pero NO el portal (el mensaje
  se descartaba en silencio al llegar desde el otro dominio).

## Pendiente

Investigar por qué el tráfico de `api-handler` no se promueve solo (posible pin manual).
