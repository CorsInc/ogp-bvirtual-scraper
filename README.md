# OGP Biblioteca Virtual Scraper

Scraper para la **Biblioteca Virtual de OGP "Miguel J. Rodríguez Fernández"** — la biblioteca digital de la Oficina de Gerencia y Presupuesto de Puerto Rico.

## ¿Qué extrae?

- **Leyes Orgánicas** — Leyes que crean agencias y entidades gubernamentales
- **Leyes de Referencia** — Leyes por temas (Contabilidad, Empleos, Ética, Justicia, etc.)
- **Reorganización Gubernamental** — Documentos de reorganización
- **Resoluciones Conjuntas del Presupuesto** — Presupuestos por año fiscal
- **Memoriales Explicativos del Presupuesto** — Documentos presupuestarios

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

### Scrapear todo:
```bash
python -m scraper.main
```

### Scrapear una sección específica:
```bash
python -m scraper.main leyes_organicas
python -m scraper.main memoriales
```

### Secciones disponibles:
- `inicio` — Página principal
- `leyes_organicas` — Leyes Orgánicas
- `leyes_referencia` — Leyes de Referencia
- `reorganizacion` — Reorganización Gubernamental
- `resoluciones_presupuesto` — Resoluciones Conjuntas
- `memoriales` — Memoriales Explicativos

## Output

Los resultados se guardan en `scraper/output/` como archivos JSON.

## Notas

El sitio está construido sobre SharePoint. Algunas secciones pueden requerir JavaScript para cargar completamente. Si una sección no devuelve documentos, prueba abriendo la URL directamente en un navegador para verificar que existe.
