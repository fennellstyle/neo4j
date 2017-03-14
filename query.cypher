// show the graph
match (a)
return * limit 100

// given the texture task, get the dependent product and version
match (:Task {name:"texture-boots"})-[:produces]->(:Product)-[:depends_on]->(d:Dependency)
match (d)-[:to_version]->(v:Version),(d)-[:to_product]->(p:Product)
return v,p

// what if I care about the edges?
match (:Task {name:"texture-boots"})-[:produces]->(p:Product)-[:depends_on]->(d:Dependency)
match (d)-[:to_version]->(v:Version),(d)-[:to_product]->(dest:Product)
return *
