// The following cypher will create and wire up an independent view
// node for each set of tasks that have matching context and asset properties
// NOTE: this does not account for tasks that do not have one or the other property
match(t:Task)
with distinct([t.asset, t.context]) as view_candidates, collect(t) as group
foreach(gt in group |
	merge (v:View {name:(gt.context + "/" + gt.asset)})
    merge (v)-[:sees]->(gt))