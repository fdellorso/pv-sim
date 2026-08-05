"""PDF report generation from simulation results.

Implemented in the web layer (it needs DB data, persisted curves and the
Jinja templates): see ``src.web.report.build_report_pdf``. This engine
module is intentionally kept as a stub so the engine stays importable in
isolation; the web layer imports WeasyPrint + matplotlib directly.
"""
