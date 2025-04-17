-- Get HGNC ID and its disease connections
SELECT g.hgnc_id, d.disease_name
FROM hgnc_gene g
         JOIN gene_disease gd ON g.hgnc_id = gd.hgnc_id
         JOIN disease d ON gd.disease_id = d.disease_id;

-- Get HGNC Gene Name and all aliases
SELECT g.gene_name, GROUP_CONCAT(a.alias, ', ') AS aliases
FROM hgnc_gene g
         LEFT JOIN gene_alias a ON g.hgnc_id = a.hgnc_id
GROUP BY g.gene_name;