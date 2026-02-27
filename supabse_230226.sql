-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.analysis_results (
  id integer NOT NULL DEFAULT nextval('analysis_results_id_seq'::regclass),
  url character varying NOT NULL,
  credibility_score double precision NOT NULL,
  summary text,
  created_at timestamp without time zone DEFAULT now(),
  source_reputation character varying,
  fact_check_count integer DEFAULT 0,
  CONSTRAINT analysis_results_pkey PRIMARY KEY (id)
);
CREATE TABLE public.rdf_triples (
  id integer NOT NULL DEFAULT nextval('rdf_triples_id_seq'::regclass),
  subject character varying NOT NULL,
  predicate character varying NOT NULL,
  object text NOT NULL,
  object_type character varying DEFAULT 'uri'::character varying,
  graph_name character varying DEFAULT 'data'::character varying,
  created_at timestamp without time zone DEFAULT now(),
  CONSTRAINT rdf_triples_pkey PRIMARY KEY (id)
);
CREATE TABLE public.sources (
  id integer NOT NULL DEFAULT nextval('sources_id_seq'::regclass),
  domain character varying NOT NULL UNIQUE,
  reputation_score double precision,
  analysis_count integer DEFAULT 0,
  created_at timestamp without time zone DEFAULT now(),
  CONSTRAINT sources_pkey PRIMARY KEY (id)
);