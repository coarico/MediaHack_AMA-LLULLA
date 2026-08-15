# Firebase - AMA-LLU-IA

Esta carpeta contiene el contrato de base de datos para Firestore.

## Archivos

- `firebase.json`: configuracion para Firebase CLI.
- `firestore.rules`: reglas de seguridad.
- `firestore.indexes.json`: indices recomendados.
- `FIRESTORE_SCHEMA.md`: estructura de colecciones y documentos.

## Desplegar

Desde esta carpeta:

```bash
firebase use <project-id>
firebase deploy --only firestore:rules,firestore:indexes
```

El backend usa Firebase Admin SDK, por lo que las reglas aplican principalmente al frontend y usuarios autenticados. El servidor debe validar igualmente permisos y datos antes de escribir.

