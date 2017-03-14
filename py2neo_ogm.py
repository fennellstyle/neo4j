from hashlib import sha224
from uuid import uuid4
from py2neo import Graph, Node, authenticate
from py2neo.ogm import GraphObject, RelatedTo, Property

_connections = {}


def init():
    host = 'localhost:7474'
    authenticate(host, 'neo4j', 'neo')
    graph = Graph('http://' + host + '/db/data')
    return graph


def get_connection(alias):
    return _connections[alias]


def register_connection(alias, graph):
    if not graph:
        graph = init()
    _connections[alias] = graph
    return get_connection(alias)


def connect(graph=None, alias='DEFAULT_GRAPH'):
    if alias not in _connections:
        register_connection(alias, graph)
    return get_connection(alias)


class Subgraph(set):
    def __init__(self, nodes, relationships=list()):
        def none_filter(n):
            return n is not None

        self.nodes = filter(none_filter, nodes)
        self.relationships = filter(none_filter, relationships)
        super(Subgraph, self).__init__(self.nodes + self.relationships)

    def __repr__(self):
        return 'Subgraph(nodes={}, relationships={})'.format(self.nodes, self.relationships)

    def __db_push__(self, graph):
        for node in self:
            graph.push(node)


class Uti(GraphObject):
    _primarykey = 'name'
    _name = 'com.base'

    name = Property()
    inherits = RelatedTo('Uti', 'inherits')

    def __init__(self):
        self.__primarykey__ = self._primarykey
        self.__primarylabel__ = 'Uti'
        self.name = self._name
        if self.__class__.__base__ != GraphObject:
            self.inherits.add(self._base_instance())

    def _base_instance(self):
        return self.__class__.__base__()


class TaskUti(Uti):
    _name = 'com.task'


class ModelingTaskUti(TaskUti):
    _name = 'com.task-model'


class TextureTaskUti(TaskUti):
    _name = 'com.task-texture'


class ProductUti(Uti):
    _name = 'com.product'


class ImageProductUti(ProductUti):
    _name = 'com.product-image'


class GeometryProductUti(ProductUti):
    _name = 'com.product-geometry'


class Version(GraphObject):
    __primarykey__ = 'id'
    id = Property()
    name = Property()
    name_int = Property()

    previous = RelatedTo('Version', 'previous')
    next = RelatedTo('Version', 'next')

    def __init__(self, previous_version=None):
        """
        Args:
            previous_version (V): Previous version node to link
        """
        if not previous_version:
            self.name_int = 1
        else:
            self.name_int = self._incr(previous_version)

        self.name = self.get_name()
        self.id = str(uuid4())

        if previous_version is not None:
            if isinstance(previous_version, (Version, Node)):
                self.previous.add(previous_version)
                previous_version.next.add(self)
            else:
                self._error(type(previous_version))

    def get_name(self):
        return 'v{}'.format(self.name_int)

    def _incr(self, previous_version):
        if not previous_version:
            return self.name_int

        # follow next links to get next version int
        version_number = previous_version.name_int
        for version in previous_version.next:
            print 'walked to:', version.name, version.name_int
            version_number = int(version.name_int)
            print 'version_number set to', str(version_number)

        version_number += 1
        print 'version_number set to', str(version_number)
        return version_number

    @staticmethod
    def _error(*args, **kwargs):
        raise TypeError(
            "Expected previous to be Version, got type {}".format(
                *args)
        )


class Entity(GraphObject):
    __primarykey__ = 'name'
    _label = None
    _uti = None

    name = Property()
    is_type = RelatedTo(Uti, 'is_type')

    def __init__(self, name, *args, **kwargs):
        if self._label:
            self.__primarylabel__ = self._label

        self.name = name

        if self._uti:
            self.is_type.add(self._uti)

    def __hash__(self):
        return hash(str(self))


class Dependency(GraphObject):
    __primarykey__ = 'id'

    id = Property()
    to_product = RelatedTo('Product', 'to_product')
    to_version = RelatedTo('Version', 'to_version')

    def __init__(self, product):
        self.id = str(uuid4())
        self.to_product.add(product)
        self.to_version.add(product.get_current_version())

    def get_product(self):
        return iter(self.to_product).next()

    def get_version(self):
        return iter(self.to_version).next()

    def get_product_and_version(self):
        return self.get_product(), self.get_version()

    def update_version(self):
        version = self.get_product().get_current_version()
        self.to_version.clear()
        self.to_version.add(version)
        connect().push(self)


class Product(Entity):
    _uti = ProductUti()
    _label = 'Product'

    uses = RelatedTo(Version, 'uses')
    depends_on = RelatedTo(Dependency, 'depends_on')

    def __init__(self, name):
        super(Product, self).__init__(name)
        self.add_version()

    def add_version(self):
        current_version = None
        try:
            current_version = iter(self.uses).next()
        except StopIteration:
            pass
        new_version = Version(current_version)
        subgraph = Subgraph([new_version, current_version, self])
        self.uses.clear()
        self.uses.add(new_version)
        connect().push(subgraph)
        return new_version

    def add_dependency(self, product):
        self.depends_on.add(Dependency(product))

    def get_current_version(self):
        return iter(self.uses).next()

    def get_dependent_version(self, product):
        for dependency in self.depends_on:
            if dependency.get_product() == product:
                return dependency.get_version()

    def update_dependent_version(self, product):
        for d in self.depends_on:
            if d.get_product() == product:
                d.update_version()


class ImageProduct(Product):
    _uti = ImageProductUti()


class GeometryProduct(Product):
    _uti = GeometryProductUti()


class Task(Entity):
    _uti = TaskUti()
    _label = 'Task'
    produces = RelatedTo(Product, 'produces')

    def add_product(self, product):
        self.produces.add(product)


class AssetTask(Task):
    asset = Property()
    context = Property()

    def __init__(self, name, asset, context):
        super(AssetTask, self).__init__(name)
        self.asset = asset
        self.context = context


class ModelingTask(AssetTask):
    _uti = ModelingTaskUti()


class TextureTask(AssetTask):
    _uti = TextureTaskUti()


class View(GraphObject):
    __primarykey__ = 'name'

    name = Property()
    id = Property()
    hash = Property()
    sees = RelatedTo(Task, 'sees')

    def __init__(self):
        self.id = sha224(self.name) + '@view'


def get_types():
    classes = [Uti] + Uti.__subclasses__()
    types = []
    while classes:
        t = classes.pop()
        types.append(t())
        classes.extend(t.__subclasses__())

    return Subgraph(types)


def generate_modeling_task(graph):
    model_boots = ModelingTask('model-hiccup-boots', 'hiccup', 'test:context')
    geometry_product = GeometryProduct(model_boots.name + ':geometry')
    model_boots.add_product(geometry_product)
    subgraph = Subgraph([model_boots, geometry_product])
    graph.push(subgraph)
    return model_boots


def generate_surfacing_task(graph, model_product):
    texture_boots = TextureTask('texture-boots', 'hiccup', 'test:context')
    images_product = ImageProduct(texture_boots.name + ':textures')
    images_product.add_dependency(model_product)
    texture_boots.add_product(images_product)
    subgraph = Subgraph([texture_boots, images_product])
    graph.push(subgraph)
    return texture_boots


def main():
    graph = connect()
    graph.delete_all()
    return graph


# def more_versions():
#     model_product.add_version()
#     texture_product.add_version()
#     texture_product.add_version()
#     texture_product.add_version()
#     for product in texture_product.depends_on:
#             texture_product.get_dependent_version(product)
#
#
# graph = main()
# # graph = connect()
#
# # create types
# types = get_types()
# graph.push(types)
#
# # create a modeling task
# model_task = generate_modeling_task(graph)
#
# # create a surfacing task
# model_product = iter(model_task.produces).next()
# texture_task = generate_surfacing_task(graph, model_product)
# texture_product = iter(texture_task.produces).next()
#
# # add version to model product
# model_product.add_version()
#
# # Update dependency of texture_product
# texture_product.update_dependent_version(model_product)
#
# # add more model versions
# model_product.add_version()
# model_product.add_version()
#
# # demonstrate users here
#
# # demonstrate views here
# # other = ModelingTask('test-model', 'another_asset', 'some:context')
# # graph.push(other)
