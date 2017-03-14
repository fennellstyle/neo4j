// The following cypher will create and wire up an independent view
// node for each set of tasks that have matching context and asset properties
// NOTE: this does not account for tasks that do not have one or the other property
match(t:Task)
with distinct([t.asset, t.context]) as view_candidates, collect(t) as group
foreach(task in group |
	merge (view:View {name:(task.context + "/" + task.asset)})
    merge (view)-[:sees]->(task))

// get task named texture-boots and all upstream Uti
match (a)-[:is_type]-(b)-[:inherits*]->(c)
where a.name = "texture-boots"
return *
// only return uti chain
// return b,c

// get upstream uti hierarchy of com.product-geometry
match (a:Uti {name:"com.product-geometry"})-[:inherits*]->(b:Uti) return *

// get all downstream uti hierarchy from com.task
match (a:Uti {name:"com.task"})<-[:inherits*]-(b:Uti) return *

// get the versions through dependencies
match (tp:Product)--(d:Dependency)-->(v:Version) return *


// make version dependency instead of product dependency
match (t:Task {name:"texture-boots"})-[:product]->(p:Product {name:t.name + ":textures"})-[r:dependency]->(d:Dependency),(v {name:"v2"}),(v4 {name:"v4"})
delete r
merge (v)-[:dependency]->(d)
merge (v4)-[:dependency]->(d)

// update version 4 dependencies
match (v4 {name:"v4"})-[de:dependency]->(d:Dependency)-[:product]->(p:Product)-[:current]->(dv:Version)
delete de
merge (v4)-[:dependency]->(nd:Dependency {name:"abdc-def52-314a"})
merge (nd)-[:product]->(p)
merge (nd)-[:version]->(dv)

// point v2 at an earlier version of the model
match (v2 {name:"v2"})-[:dependency]->(d:Dependency)-[e:version]->(cdv:Version)-[:previous]->(dv:Version)
delete e
merge (d)-[:version]->(dv)