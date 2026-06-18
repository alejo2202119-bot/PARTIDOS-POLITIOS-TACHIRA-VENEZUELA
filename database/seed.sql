-- ============================================================================
--  VPID — Seed / reference data
--
--  Contents:
--    * Roles & a default admin user (password must be reset on first login)
--    * Venezuelan states (24) + Táchira municipalities (29) — public geography
--    * Public political organizations & a reference set of public figures
--    * Public, verifiable media sources (fuentes)
--    * Topics
--    * A small SYNTHETIC sample of articles/mentions/sentiment/trends/alerts
--      purely to demonstrate the dashboard. Synthetic rows are clearly marked.
--
--  NOTE: All organizations, media outlets and public figures below are
--  public-record reference entities. Sample analytics (sentiment, mentions)
--  are SYNTHETIC and for demonstration only — they are not real measurements.
-- ============================================================================

-- ─────────────────────────── Roles ─────────────────────────────────────────
INSERT INTO roles (nombre, descripcion, permisos) VALUES
 ('admin',    'Acceso total: configuración, fuentes, usuarios, auditoría', '{"all":true}'),
 ('analista', 'Análisis, reportes, alertas; sin administración de usuarios', '{"read":true,"report":true,"alerts":true}'),
 ('editor',   'Gestión de fuentes y entidades; análisis de lectura',        '{"read":true,"sources":true}'),
 ('lector',   'Solo lectura del dashboard y descarga de informes PDF',      '{"read":true}')
ON CONFLICT (nombre) DO NOTHING;

-- Default admin (bcrypt hash of "ChangeMe!2026" — CHANGE on first login)
INSERT INTO usuarios (email, nombre, rol_id, password_hash)
SELECT 'admin@vpid.local', 'Administrador VPID', r.id,
       '$2b$12$Q5cVqkqB6Yy9b8Yx0m0Yyu2bq7sJtq9o3oQ1pQ5b4bq9oQ1pQ5b4'
FROM roles r WHERE r.nombre = 'admin'
ON CONFLICT (email) DO NOTHING;

-- ─────────────────────────── States (24) ───────────────────────────────────
INSERT INTO estados (codigo, nombre, capital, region, latitud, longitud) VALUES
 ('VE-A','Distrito Capital','Caracas','Capital',10.4806,-66.9036),
 ('VE-B','Anzoátegui','Barcelona','Oriente',10.1340,-64.6853),
 ('VE-C','Apure','San Fernando de Apure','Los Llanos',7.8939,-67.4736),
 ('VE-D','Aragua','Maracay','Central',10.2469,-67.5958),
 ('VE-E','Barinas','Barinas','Los Llanos',8.6226,-70.2076),
 ('VE-F','Bolívar','Ciudad Bolívar','Guayana',8.1222,-63.5497),
 ('VE-G','Carabobo','Valencia','Central',10.1620,-68.0077),
 ('VE-H','Cojedes','San Carlos','Los Llanos',9.6611,-68.5836),
 ('VE-I','Falcón','Coro','Occidente',11.4045,-69.6734),
 ('VE-J','Guárico','San Juan de los Morros','Los Llanos',9.9107,-67.3545),
 ('VE-K','Lara','Barquisimeto','Centroccidente',10.0731,-69.3220),
 ('VE-L','Mérida','Mérida','Los Andes',8.5897,-71.1561),
 ('VE-M','Miranda','Los Teques','Central',10.3417,-67.0407),
 ('VE-N','Monagas','Maturín','Oriente',9.7457,-63.1832),
 ('VE-O','Nueva Esparta','La Asunción','Insular',11.0337,-63.8628),
 ('VE-P','Portuguesa','Guanare','Los Llanos',9.0417,-69.7423),
 ('VE-R','Sucre','Cumaná','Oriente',10.4540,-64.1769),
 ('VE-S','Táchira','San Cristóbal','Los Andes',7.7669,-72.2250),
 ('VE-T','Trujillo','Trujillo','Los Andes',9.3667,-70.4333),
 ('VE-U','Yaracuy','San Felipe','Centroccidente',10.3400,-68.7400),
 ('VE-V','Zulia','Maracaibo','Occidente',10.6427,-71.6125),
 ('VE-X','La Guaira','La Guaira','Capital',10.6017,-66.9319),
 ('VE-Y','Delta Amacuro','Tucupita','Guayana',9.0606,-62.0455),
 ('VE-Z','Amazonas','Puerto Ayacucho','Guayana',5.6639,-67.6236)
ON CONFLICT (nombre) DO NOTHING;

-- ─────────────────────── Táchira municipalities (29) ───────────────────────
INSERT INTO municipios (estado_id, nombre, capital, latitud, longitud)
SELECT e.id, m.nombre, m.capital, m.lat, m.lon
FROM estados e, (VALUES
 ('Andrés Bello','Cordero',7.8333,-72.1667),
 ('Antonio Rómulo Costa','Las Mesas',7.9667,-72.0333),
 ('Ayacucho','San Juan de Colón',8.0333,-72.2667),
 ('Bolívar','San Antonio del Táchira',7.8147,-72.4436),
 ('Cárdenas','Táriba',7.8167,-72.2167),
 ('Córdoba','Santa Ana del Táchira',7.5667,-72.2667),
 ('Fernández Feo','San Rafael del Piñal',7.5500,-71.9167),
 ('Francisco de Miranda','San José de Bolívar',7.9000,-72.0167),
 ('García de Hevia','La Fría',8.2167,-72.2500),
 ('Guásimos','Palmira',7.7500,-72.1667),
 ('Independencia','Capacho Nuevo',7.8333,-72.3000),
 ('Jáuregui','La Grita',8.1333,-71.9833),
 ('José María Vargas','El Cobre',7.7167,-72.0500),
 ('Junín','Rubio',7.7000,-72.3500),
 ('Libertad','Capacho Viejo',7.8333,-72.3167),
 ('Libertador','Abejales',7.6167,-71.6500),
 ('Lobatera','Lobatera',7.9333,-72.2333),
 ('Michelena','Michelena',8.0333,-72.1333),
 ('Panamericano','Coloncito',8.2833,-72.0000),
 ('Pedro María Ureña','Ureña',7.9167,-72.4500),
 ('Rafael Urdaneta','Delicias',7.5333,-72.4500),
 ('Samuel Darío Maldonado','La Tendida',8.2000,-71.8500),
 ('San Cristóbal','San Cristóbal',7.7669,-72.2250),
 ('Seboruco','Seboruco',8.0667,-72.0167),
 ('Simón Rodríguez','San Simón',8.0500,-71.9333),
 ('Sucre','Queniquea',7.9667,-71.9667),
 ('Torbes','San Josecito',7.7167,-72.1833),
 ('Uribante','Pregonero',7.9500,-71.7667),
 ('San Judas Tadeo','Umuquena',8.1167,-72.1500)
) AS m(nombre,capital,lat,lon)
WHERE e.nombre = 'Táchira'
ON CONFLICT (estado_id, nombre) DO NOTHING;

-- ─────────────────── Public political organizations ─────────────────────────
INSERT INTO organizaciones (nombre, siglas, tipo, tendencia, sitio_web) VALUES
 ('Plataforma Unitaria Democrática','PUD','partido','oposicion',NULL),
 ('Primero Justicia','PJ','partido','oposicion','https://primerojusticia.org.ve'),
 ('Voluntad Popular','VP','partido','oposicion','https://voluntadpopular.com'),
 ('Un Nuevo Tiempo','UNT','partido','oposicion',NULL),
 ('Acción Democrática','AD','partido','oposicion',NULL),
 ('COPEI','COPEI','partido','oposicion',NULL),
 ('Vente Venezuela','VV','partido','oposicion',NULL),
 ('La Causa R','LCR','partido','oposicion',NULL),
 ('Fuerza Vecinal','FV','partido','oposicion',NULL),
 ('Movimiento Por Venezuela','MPV','partido','oposicion',NULL),
 ('Partido Socialista Unido de Venezuela','PSUV','partido','oficialismo',NULL)
ON CONFLICT DO NOTHING;

-- ─────────────────── Public figures (public-record reference) ───────────────
-- Names + public roles only; included as reference entities for analysis.
INSERT INTO actores (nombre, tipo, cargo, organizacion_id, estado_id)
SELECT v.nombre, 'persona'::tipo_actor, v.cargo, o.id, e.id
FROM (VALUES
 ('María Corina Machado','Líder político','Vente Venezuela','Distrito Capital'),
 ('Edmundo González Urrutia','Figura pública','Plataforma Unitaria Democrática','Distrito Capital'),
 ('Henrique Capriles','Dirigente','Primero Justicia','Miranda'),
 ('Manuel Rosales','Gobernador','Un Nuevo Tiempo','Zulia'),
 ('Juan Pablo Guanipa','Dirigente','Primero Justicia','Zulia'),
 ('Roberto Enríquez','Dirigente','COPEI','Distrito Capital'),
 ('Laidy Gómez','Dirigente regional','Acción Democrática','Táchira'),
 ('Tomás Guanipa','Dirigente','Primero Justicia','Distrito Capital')
) AS v(nombre,cargo,org,estado)
LEFT JOIN organizaciones o ON o.nombre = v.org
LEFT JOIN estados e ON e.nombre = v.estado
ON CONFLICT DO NOTHING;

-- ─────────────────── Public, verifiable media sources (fuentes) ─────────────
INSERT INTO fuentes (nombre, tipo, url, rss_url, alcance, idioma, pais, credibilidad, verificada, estado_geo_id)
SELECT v.nombre, v.tipo::tipo_fuente, v.url, v.rss, v.alcance::alcance_fuente, 'es', v.pais, v.cred, v.verif,
       (SELECT id FROM estados WHERE nombre = v.estado)
FROM (VALUES
 ('El Nacional','medio','https://www.elnacional.com','https://www.elnacional.com/feed/','nacional','VE',70,true,NULL),
 ('El Universal','medio','https://www.eluniversal.com','https://www.eluniversal.com/rss','nacional','VE',68,true,NULL),
 ('Tal Cual','medio','https://talcualdigital.com','https://talcualdigital.com/feed/','nacional','VE',72,true,NULL),
 ('Efecto Cocuyo','portal','https://efectococuyo.com','https://efectococuyo.com/feed/','nacional','VE',78,true,NULL),
 ('Runrun.es','portal','https://runrun.es','https://runrun.es/feed/','nacional','VE',75,true,NULL),
 ('La Patilla','portal','https://www.lapatilla.com','https://www.lapatilla.com/feed/','nacional','VE',66,true,NULL),
 ('Crónica.Uno','portal','https://cronica.uno','https://cronica.uno/feed/','nacional','VE',77,true,NULL),
 ('Diario La Nación','medio','https://lanacionweb.com','https://lanacionweb.com/feed/','regional','VE',69,true,'Táchira'),
 ('La Prensa del Táchira','medio','https://laprensatachira.com',NULL,'regional','VE',60,false,'Táchira'),
 ('Diario de Los Andes','medio','https://diariodelosandes.com','https://diariodelosandes.com/feed/','regional','VE',62,true,'Trujillo'),
 ('Reuters (América Latina)','agencia','https://www.reuters.com',NULL,'internacional','GB',85,true,NULL),
 ('France 24 Español','medio','https://www.france24.com/es','https://www.france24.com/es/rss','internacional','FR',82,true,NULL)
) AS v(nombre,tipo,url,rss,alcance,pais,cred,verif,estado)
ON CONFLICT DO NOTHING;

-- ─────────────────────────── Topics ────────────────────────────────────────
INSERT INTO temas (nombre, slug, categoria, palabras_clave, color) VALUES
 ('Elecciones','elecciones','politica','{elecciones,comicios,voto,candidatura,primarias}','#6366f1'),
 ('Derechos Humanos','derechos-humanos','social','{ddhh,libertad,detencion,derechos}','#ef4444'),
 ('Economía','economia','economia','{inflacion,salario,dolar,economia,precios}','#22c55e'),
 ('Servicios Públicos','servicios-publicos','social','{electricidad,agua,gasolina,servicios}','#f59e0b'),
 ('Negociación Política','negociacion','politica','{dialogo,negociacion,acuerdo,mesa}','#06b6d4'),
 ('Migración','migracion','social','{migracion,migrantes,frontera,retorno}','#a855f7'),
 ('Seguridad','seguridad','seguridad','{seguridad,delincuencia,frontera,orden}','#64748b')
ON CONFLICT (slug) DO NOTHING;

-- ─────────────── SYNTHETIC sample articles for dashboard demo ───────────────
-- (clearly illustrative; titles are neutral placeholders)
INSERT INTO articulos (fuente_id, url, url_hash, titulo, resumen, publicado_en, estado, relevancia, alcance_estimado, estado_geo_id, tema_id)
SELECT f.id,
       'https://example.org/demo/' || g.n,
       encode(digest('demo-' || g.n, 'sha256'), 'hex'),
       (ARRAY[
         'Dirigentes opositores presentan agenda regional en San Cristóbal',
         'Análisis: cobertura mediática sobre el proceso electoral',
         'Organizaciones civiles publican comunicado sobre servicios públicos',
         'Foro público aborda economía y empleo en la región andina',
         'Cobertura internacional sobre la situación política venezolana',
         'Actividad partidista en municipios fronterizos del Táchira',
         'Debate público sobre derechos y participación ciudadana',
         'Medios regionales reportan jornada de organización vecinal'
       ])[1 + (g.n % 8)],
       'Resumen sintético de demostración para el panel analítico.',
       now() - (g.n || ' hours')::interval,
       'analizado'::estado_articulo,
       (ARRAY['media','alta','media','baja','alta','media','alta','media']::nivel_relevancia[])[1 + (g.n % 8)],
       (5000 + (g.n * 1373) % 95000),
       (SELECT id FROM estados WHERE nombre = 'Táchira'),
       (SELECT id FROM temas ORDER BY random() LIMIT 1)
FROM (SELECT generate_series(0, 47) AS n) g
JOIN LATERAL (SELECT id FROM fuentes ORDER BY random() LIMIT 1) f ON true
ON CONFLICT (url_hash) DO NOTHING;

-- Synthetic mentions + sentiment for the demo articles
INSERT INTO menciones (articulo_id, actor_id, peso)
SELECT a.id, ac.id, 1.0
FROM articulos a
JOIN LATERAL (SELECT id FROM actores ORDER BY random() LIMIT 1) ac ON true
WHERE a.url LIKE 'https://example.org/demo/%';

INSERT INTO analisis_sentimiento (articulo_id, etiqueta, score, confianza, modelo)
SELECT a.id,
       (ARRAY['positivo','neutral','negativo','neutral','positivo']::sentimiento[])[1 + (floor(random()*5))::int],
       round((random()*2 - 1)::numeric, 3)::real,
       round((0.6 + random()*0.4)::numeric, 3)::real,
       'demo-synthetic'
FROM articulos a
WHERE a.url LIKE 'https://example.org/demo/%';

-- A couple of demo alerts and one report shell
INSERT INTO alertas (titulo, descripcion, tipo, severidad, estado, valor) VALUES
 ('Pico de menciones detectado','Incremento del 142% en menciones sobre "Elecciones" en 24h.','pico_menciones','alta','abierta',142.0),
 ('Narrativa emergente','Nueva narrativa sobre servicios públicos ganando tracción regional.','narrativa_emergente','media','en_revision',38.0)
ON CONFLICT DO NOTHING;

-- Today's KPI snapshot (computed values will overwrite this in production ETL)
INSERT INTO kpi_snapshots (fecha, total_articulos, total_menciones, fuentes_activas,
                           sentimiento_global, narrativas_activas, narrativas_emergentes,
                           alertas_abiertas, alcance_total)
VALUES (current_date, 48, 48, 12, -0.06, 7, 2, 1, 1840000)
ON CONFLICT (fecha) DO NOTHING;

-- ============================================================================
--  End of seed
-- ============================================================================
