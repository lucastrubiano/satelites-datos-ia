# Flujo de trabajo

## Antes de tocar nada
1. Leer `PLAN.md` (recorte validado y decisiones abiertas), `docs/DECISIONS.md` y `docs/TROUBLESHOOTING.md`.
2. Validar el enfoque con Lucas antes de detallar: primero esqueleto, después detalle.

## Para hacer un cambio
1. Si suma una fuente: confirmar que es gratis y sin tarjeta (`AGENTS.md`) y anotarla con su licencia en `docs/fuentes.md`.
2. Implementar la demo como script autónomo en `demos/`.
3. Correrla de punta a punta y guardar la imagen de salida.
4. Actualizar `PLAN.md` (estado de la demo) y, si hubo una decisión, `docs/DECISIONS.md`.

## Antes de dar algo por terminado
- [ ] El script corre de punta a punta sin intervención
- [ ] La imagen de salida existe, como captura de respaldo para la charla
- [ ] Toda cifra nueva tiene fuente y fecha
- [ ] No se usó nada que cobre

## Deploy
No hay deploy. El repo es local, sin remoto ni commits todavía. Publicarlo como repo público es decisión de Lucas: [PENDIENTE].
