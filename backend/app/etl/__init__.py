"""Automated ETL pipeline: ingest → clean → classify → analyze → aggregate.

Processes only PUBLIC sources (RSS/HTML/official feeds). Every stage logs to
``etl_ejecuciones`` when the DB is reachable and degrades gracefully otherwise.
"""
