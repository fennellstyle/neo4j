// add another version to model
match (task:Task {name:"model-hiccup-boots"})-[old_edge:current]->(previous_version),
      // match the product the previous version points to
      (previous_version)-[:products]->(product:Product)-[:uti]->(uti:Uti)
// create the new version based on the previous version
merge (new_version:Version {name: "v"+(previous_version.num+1), num:(previous_version.num+1), id:"v"+(previous_version.num+1)+"-"+task.name})
// link the new version to the previous version
merge (new_version)-[:previous]->(previous_version)
// set task current to point at the new version
merge (task)-[:current]->(new_version)
// link the previous version to the new version
merge (previous_version)-[:next]->(new_version)
// create a new product for the new version
merge (new_product:Product {name: product.name, id: 3})-[:uti]->(uti)
// connect the new version to the new product
merge (new_version)-[:products]->(new_product) // this doesn't make the products edge
delete old_edge
