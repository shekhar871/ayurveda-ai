// Ayurvedic knowledge graph seed constraints
CREATE CONSTRAINT lakshana_name IF NOT EXISTS FOR (n:Lakshana) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT roga_name IF NOT EXISTS FOR (n:Roga) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT dravya_name IF NOT EXISTS FOR (n:Dravya) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT formulation_name IF NOT EXISTS FOR (n:Formulation) REQUIRE n.name IS UNIQUE;
