# Bucks-R-Us ETL & Retail Analytics System

Bucks-R-Us is a fictional multi-location fixed-price discount retailer created as the basis for a data analytics and ETL portfolio project.

The goal of the project is to build a reproducible data pipeline that extracts operational retail data from multiple sources, validates and transforms that data, loads trustworthy records into an analytical database, and ultimately supports analysis of product demand and inventory needs across store locations.

## Business Problem

Bucks-R-Us operates multiple retail locations selling most merchandise at a standardized company-wide price. Each store generates sales and inventory data, while product and store information are maintained separately.

The business needs a reliable way to combine these sources so analysts can answer questions such as:

- Which products sell differently across store locations?
- Which products or categories are increasing or declining in demand?
- Where are inventory shortages occurring?
- Are stores receiving inventory appropriate for their local demand?
- Are incoming operational records complete and trustworthy?

The initial development work is focused on building the ingestion and data-quality foundation required before those analyses can be trusted.
