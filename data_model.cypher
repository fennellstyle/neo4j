//match (n) detach delete n
        // make utis
create (base_uti:Uti {name:"com.base"}),
       (task_uti:Uti {name:"com.task"})-[:inherits]->(base_uti),
       (tex_task_uti:Uti {name:"com.task-texture"})-[:inherits]->(task_uti),
       (mod_task_uti:Uti {name:"com.task-model"})-[:inherits]->(task_uti),
       (prod_uti:Uti {name:"com.product"})-[:inherits]->(base_uti),
       (img_prod_uti:Uti {name:"com.product-image"})-[:inherits]->(prod_uti),
       (geo_prod_uti:Uti {name:"com.product-geometry"})-[:inherits]->(prod_uti),
       // make model task with version and product
       (mod_task:Task {name: "model-hiccup-boots", asset: "hiccup"})-[:uti]->(mod_task_uti),
       (geo_prod:Product {name:"geometry", id:1})-[:uti]->(geo_prod_uti),
       (mod_v1:Version {name:"v1", num:1, id:"v1-"+mod_task.name})-[:products]->(geo_prod),
       (mod_task)-[:current]->(mod_v1),
       // make texture task dependent on model task version
       (tex_task:Task {name: "texture-hiccup-boots", asset: "hiccup"})-[:uti]->(tex_task_uti),
       (img_prod:Product {name:"texture", id:2})-[:uti]->(img_prod_uti),
       (tex_v1:Version {name:"v1", num:1, id:"v1-"+tex_task.name})-[:products]->(img_prod),
       (tex_task)-[:current]->(tex_v1),
       (tex_v1)-[:dependency]->(mod_v1)
       return *

