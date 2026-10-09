--
-- PostgreSQL database dump
--

\restrict naB1fBQ8A9MQsHGReI1FCtwgPz6bvg5pT6505b7cSWuF1iODkvgznmvfsXuYv40

-- Dumped from database version 17.11 (Debian 17.11-1.pgdg13+2)
-- Dumped by pg_dump version 17.11 (Debian 17.11-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: inventory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory (
    store_id character varying(20) NOT NULL,
    sku character varying(20) NOT NULL,
    quantity_on_hand integer NOT NULL,
    inventory_timestamp timestamp without time zone NOT NULL,
    CONSTRAINT inventory_quantity_on_hand_check CHECK ((quantity_on_hand >= 0))
);


--
-- Name: products; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.products (
    sku character varying(20) NOT NULL,
    product_name character varying(255) NOT NULL,
    category character varying(100) NOT NULL,
    status character varying(20) NOT NULL
);


--
-- Name: stores; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.stores (
    store_id character varying(20) NOT NULL,
    address text NOT NULL,
    city character varying(100) NOT NULL,
    state character varying(100) NOT NULL,
    zip_code character varying(20),
    status character varying(20) NOT NULL,
    closed_at timestamp without time zone
);


--
-- Name: inventory inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_pkey PRIMARY KEY (store_id, sku, inventory_timestamp);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (sku);


--
-- Name: stores stores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stores
    ADD CONSTRAINT stores_pkey PRIMARY KEY (store_id);


--
-- Name: inventory inventory_sku_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_sku_fkey FOREIGN KEY (sku) REFERENCES public.products(sku);


--
-- Name: inventory inventory_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.stores(store_id);


--
-- PostgreSQL database dump complete
--

\unrestrict naB1fBQ8A9MQsHGReI1FCtwgPz6bvg5pT6505b7cSWuF1iODkvgznmvfsXuYv40

