import uuid

from py2neo import Graph, authenticate
from py2neo.ogm import GraphObject, RelatedFrom, RelatedTo, Property


class Uti(GraphObject):
    __primarykey__ = 'name'

    name = Property()
    inherits = RelatedTo('Uti', 'inherits')

    def __init__(self):
        self.name = 'com.base'


class TaskUti(Uti):
    def __init__(self):
        self.name = 'com.task'
        self.inherits.add(Uti())


class TextureTaskUti(TaskUti):
    def __init__(self):
        self.name = 'com.task-texture'
        self.inherits.add(TaskUti())


class ProductUti(Uti):
    def __init__(self):
        super(Uti, self).__init__()
        self.name = 'com.product'
        self.inherits.add(Uti())


class Version(GraphObject):
    __primarykey__ = 'id'

    id = Property()

    previous = RelatedFrom('Version')
    next = RelatedTo('Version')


class Entity(GraphObject):
    is_kind = RelatedTo(Uti, 'type')
    name = Property()
    __primarykey__ = 'name'


class Product(Entity):
    uses = RelatedTo(Version)


class Task(Entity):
    delivers = RelatedTo(Product)


def connect(host_port, user, pwd):
    authenticate(host_port, user, pwd)
    return Graph('http://' + host_port + '/db/data')


def init():
    host = 'localhost:7474'
    graph = connect(host, 'neo4j', 'w1tness1')
    graph.delete_all()
    return graph


def seed_types(graph):
    task_uti = Uti()
    task_uti.name = 'com.task'
    texture_task_uti = Uti()
    texture_task_uti.name = 'com.task-texture'
    texture_task_uti.inherits.add(task_uti)
    product_uti = Uti()
    product_uti.name = 'com.product'
    image_product_uti = Uti()
    image_product_uti.name = 'com.product-image'
    image_product_uti.inherits.add(product_uti)
    for entity in (task_uti, product_uti, texture_task_uti, image_product_uti):
        graph.push(entity)


def generate_surfacing_task(graph):
    texture_boots = Task()
    texture_boots.name = 'texture-boots'
    texture_boots.is_kind.add(Uti.select(graph, 'com.task-texture').first())
    images_product = Product()
    images_product.name = 'textures'
    images_product.is_kind.add(Uti.select(graph, 'com.product-image').first())
    texture_version = Version()
    texture_version.id = str(uuid.uuid4())
    texture_boots.delivers.add(images_product)
    images_product.uses.add(texture_version)
    graph.push(texture_boots)


def main():
    graph = init()
    seed_types(graph)
    generate_surfacing_task(graph)


main()
