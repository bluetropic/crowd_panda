DROP TABLE material CASCADE;

CREATE TABLE material(
  id SERIAL PRIMARY KEY,
  category VARCHAR(32) NOT NULL,
  bucket_key VARCHAR(128) NOT NULL
);

CREATE TABLE issue_material(
  issue_id INT NOT NULL REFERENCES issue,
  material_id INT NOT NULL REFERENCES material,

  PRIMARY KEY (issue_id, material_id)
);