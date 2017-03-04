import uuid

from py2neo import Graph, authenticate
from py2neo.ogm import GraphObject, RelatedFrom, RelatedTo, Property


class Uti(GraphObject):
    __primarykey__ = 'name'
    __primarylabel__ = 'Uti'

    name = Property()
    inherits = RelatedTo('Uti', 'inherits')

    def __init__(self):
        self.__primarykey__ = 'name'
        self.__primarylabel__ = 'Uti'
        self.name = 'com.base'

    def base(self):
        return self.__class__.__base__

    def base_instance(self):
        return self.base()()


class TaskUti(Uti):
    def __init__(self):
        super(TaskUti, self).__init__()
        self.name = 'com.task'
        self.inherits.add(self.base_instance())


class TextureTaskUti(TaskUti):
    def __init__(self):
        super(TaskUti, self).__init__()
        self.name = 'com.task-texture'
        self.inherits.add(self.base_instance())


class ProductUti(Uti):
    __primarylabel__ = 'Uti'

    def __init__(self):
        super(Uti, self).__init__()
        self.name = 'com.product'
        self.inherits.add(self.base_instance())


class Version(GraphObject):
    __primarykey__ = 'id'

    id = Property()

    previous = RelatedFrom('Version')
    next = RelatedTo('Version')

    def __init__(self, id, previous=None):
        self.id = id
        if previous:
            if isinstance(previous, Version):
                self.previous.add(previous)
            else:
                self._error(type(previous))

    @staticmethod
    def _error(*args, **kwargs):
        raise TypeError(
            "Expected previous to be Version, got type {}".format(
                *args)
        )


class Entity(GraphObject):
    name = Property()

    is_type = RelatedTo(Uti, 'is_type')

    def __init__(self, name, uti):
        self.__primarykey__ = 'name'
        self.name = name
        self.is_type.add(uti)


class Product(Entity):
    uses = RelatedTo(Version, 'uses')

    def __init__(self, name, uti):
        self.__primarylabel__ = 'Product'
        super(Product, self).__init__(name, uti)


class Task(Entity):
    delivers = RelatedTo(Product, 'delivers')

    def __init__(self, name, uti):
        self.__primarylabel__ = 'Task'
        super(Task, self).__init__(name, uti)


def connect(host_port, user, pwd):
    authenticate(host_port, user, pwd)
    return Graph('http://' + host_port + '/db/data')


def init():
    host = 'localhost:7474'
    graph = connect(host, 'neo4j', 'w1tness1')
    graph.delete_all()
    return graph


def seed_types(graph):
    uti = Uti()
    task_uti = TaskUti()
    texture_task_uti = Uti()
    texture_task_uti.name = 'com.task-texture'
    texture_task_uti.inherits.add(task_uti)
    product_uti = Uti()
    product_uti.name = 'com.product'
    image_product_uti = Uti()
    image_product_uti.name = 'com.product-image'
    image_product_uti.inherits.add(product_uti)
    graph.push(uti)
    graph.push(task_uti)
    # for entity in (task_uti, product_uti, texture_task_uti, image_product_uti):
    #     graph.push(entity)


def generate_surfacing_task(graph):
    texture_boots = Task('texture-boots', TextureTaskUti())
    images_product = Product('textures', ProductUti())
    texture_version = Version(str(uuid.uuid4()))
    texture_boots.delivers.add(images_product)
    images_product.uses.add(texture_version)
    graph.push(texture_boots)


def main():
    graph = init()
    seed_types(graph)
    generate_surfacing_task(graph)


main()
