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