from uuid import uuid4
from py2neo import Graph, Node, authenticate
from py2neo.ogm import GraphObject, RelatedFrom, RelatedTo, Property


_connections = {}


def init():
    host = 'localhost:7474'
    authenticate(host, 'neo4j', 'w1tness1')
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
    _label_id = 0

    previous = RelatedFrom('Version', 'previous')
    next = RelatedTo('Version', 'next')

    def __init__(self, previous_version=None):
        """
        Args:
            previous_version (V): Previous version node to link
        """
        self.name = 'v{}'.format(self._incr())
        self.id = str(uuid4())

        if previous_version is not None:
            if isinstance(previous_version, (Version, Node)):
                self.previous.add(previous_version)
                previous_version.next.add(self)
            else:
                self._error(type(previous_version))

    def _incr(self):
        type(self)._label_id += 1
        return self._label_id

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

    def __init__(self, name):
        if self._label:
            self.__primarylabel__ = self._label

        self.name = name
        if self._uti:
            self.is_type.add(self._uti)

    def __hash__(self):
        return hash(str(self))


class Product(Entity):
    _uti = ProductUti()
    _label = 'Product'

    uses = RelatedTo(Version, 'uses')
    depends_on = RelatedTo("Product", 'depends_on')

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
        version = iter(product.uses).next()
        self.depends_on.add(product, version=version.id)

    def get_used_version(self):
        return iter(self.uses).next()

    def get_dependent_version(self, product):
        version_id = self.depends_on.get(product, 'version')
        version = connect().find_one(Version.__name__, 'id', version_id)
        if version:
            return version

        raise ValueError('No version found with id {}.'.format(version_id))

    def update_dependent_version(self, product):
        for p in self.depends_on:
            if p == product:
                version = product.get_used_version()
                self.depends_on.update(product, version=version.id)


class ImageProduct(Product):
    _uti = ImageProductUti()


class GeometryProduct(Product):
    _uti = GeometryProductUti()


class Task(Entity):
    _uti = TaskUti()
    _label = 'Task'
    delivers = RelatedTo(Product, 'delivers')

    def add_product(self, product):
        self.delivers.add(product)


class ModelingTask(Task):
    _uti = ModelingTaskUti()


class TextureTask(Task):
    _uti = TextureTaskUti()


def get_types():
    classes = [Uti] + Uti.__subclasses__()
    types = []
    while classes:
        t = classes.pop()
        types.append(t())
        classes.extend(t.__subclasses__())

    return Subgraph(types)


def generate_modeling_task():
    model_boots = ModelingTask('model-boots')
    geometry_product = GeometryProduct(model_boots.name + ':geometry')
    model_boots.add_product(geometry_product)
    return Subgraph([model_boots, geometry_product])


def generate_surfacing_task(model_product):
    texture_boots = TextureTask('texture-boots')
    images_product = ImageProduct(texture_boots.name + ':textures')
    images_product.add_dependency(model_product)
    texture_boots.add_product(images_product)
    return Subgraph([texture_boots, images_product])


def main():
    graph = connect()
    graph.delete_all()
    graph.push(get_types())
    subgraph = generate_modeling_task()
    subgraph |= generate_surfacing_task(subgraph.nodes[-1])
    graph.push(subgraph)
    return graph


def more_versions():
    model_product.add_version()
    texture_product.add_version()
    texture_product.add_version()
    texture_product.add_version()
    for product in texture_product.depends_on:
            texture_product.get_dependent_version(product)


graph = main()
# graph = connect()
model_product = Product.select(graph, 'model-boots:geometry').first()
model_product.add_version()
texture_product = Product.select(graph, 'texture-boots:textures').first()
texture_product.update_dependent_version('foo')
