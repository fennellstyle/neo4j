// builds a graph to model a portion of a pipeline task graph

// create uti hierarchy
create uti_graph = (base_uti:Uti {name: "com.base"}),
(task_uti:Uti {name: "com.task"}),
(model_task_uti:Uti {name: "com.task-model"}),
(texture_task_uti:Uti {name: "com.task-texture"}),
(product_uti:Uti {name: "com.product"}),
(image_product_uti:Uti {name: "com.product-image"}),
(geo_product_uti:Uti {name: "com.product-geometry"}),
(base_uti)<-[:inherits]-(task_uti),
(base_uti)<-[:inherits]-(product_uti),
(task_uti)<-[:inherits]-(model_task_uti),
(task_uti)<-[:inherits]-(texture_task_uti),
(product_uti)<-[:inherits]-(image_product_uti),
(product_uti)<-[:inherits]-(geo_product_uti)
return uti_graph


// create modeling task with a product and an initial version
match (model_task_uti:Uti {name: "com.task-model"}),
      (image_product_uti:Uti {name: "com.product-image"})
create (model_task:Task {name: "model-hiccup-boots", asset: "hiccup"}),
(geo_product:Product {name: "model-hiccup-boots:geometry"}),
(geo_v1:Version {name:"v1"}),
(model_task)-[:is_type]->(model_task_uti),
(geo_product)-[:is_type]->(image_product_uti),
(model_task)-[:produces]->(geo_product),
(geo_product)-[:uses]->(geo_v1)

// create a texture task and make it dependent on the model task
match (texture_task_uti:Uti {name: "com.task-texture"}),
      (:Task {name: "model-hiccup-boots"})-[:produces]->(mdl_prod:Product)-[:uses]->(vers:Version)
create (texture_task:Task {name: "texture-hiccup-boots", asset: "hiccup"}),
(img_product:Product {name: "texture-hiccup-boots:image"}),
(tex_v1:Version {name:"v1"}),
(texture_task)-[:is_type]->(texture_task_uti),
(texture_task)-[:produces]->(img_product),
(img_product)-[:uses]->(tex_v1),
(d:Dependency)-[:to_product]->(mdl_prod),
(d)-[:to_version]->(vers),
(img_product)-[:depends_on]->(d)


// create more versions of the model task
match (t:Task {name: "model-hiccup-boots"})-[:produces]->(p)-[:uses]->(v)



// update the texture task to use the current model version


// add another model version


// create a view that watches the hiccup asset


// create an astrid asset model and texture sub-graph
