from hashlib import sha224
from uuid import uuid4
from py2neo import Graph, Node, authenticate
from py2neo.ogm import GraphObject, RelatedTo, Property

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


class Dependency(GraphObject):
    __primarykey__ = 'id'

    id = Property()
    product = RelatedTo('Product', 'product')
    version = RelatedTo('Version', 'version')

    def __init__(self, product):
        self.id = str(uuid4())
        self.product.add(product)
        self.version.add(product.get_current_version())

    def get_product(self):
        return iter(self.product).next()

    def get_version(self):
        return iter(self.version).next()

    def get_product_and_version(self):
        return self.get_product(), self.get_version()

    def update_version(self):
        version = self.get_product().get_current_version()
        self.version.clear()
        self.version.add(version)
        connect().push(self)


class Version(GraphObject):
    __primarykey__ = 'id'
    id = Property()
    name = Property()
    _label_id = 0

    dependency = RelatedTo(Dependency, 'dependency')
    previous = RelatedTo('Version', 'previous')
    products = RelatedTo('Product', 'products')
    next = RelatedTo('Version', 'next')

    def __init__(self, products, previous_version=None):
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

        self.products.add(products)

    def _incr(self):
        type(self)._label_id += 1
        return self._label_id

    @staticmethod
    def _error(*args, **kwargs):
        raise TypeError(
            "Expected previous to be Version, got type {}".format(
                *args)
        )

    def get_dependent_version(self, product):
        for dependency in self.dependency:
            if dependency.get_product() == product:
                return dependency.get_version()

    def update_dependent_version(self, product):
        for d in self.dependency:
            if d.get_product() == product:
                d.update_version()

    def get_product(self, graph):
        return graph.evaluate('match (a:Version {id: "<<id>>"}) return a//-[:prev|:next]->(p:Product) '
                              'return p', id=self.id)

        product = list(set(list(self.next) + list(self.previous)))
        if len(product) > 1:
            raise ValueError("Ambiguous state found.  Found more than one product.")
        return product[0] if product else None

    def add_dependency(self, to_task):
        to_current_version = to_task.get_current_version()
        self.dependency.add(to_current_version)


class Entity(GraphObject):
    __primarykey__ = 'name'
    _label = None
    _uti = None

    name = Property()
    uti = RelatedTo(Uti, 'uti')

    def __init__(self, name, *args, **kwargs):
        if self._label:
            self.__primarylabel__ = self._label

        self.name = name

        if self._uti:
            self.uti.add(self._uti)

    def __hash__(self):
        return hash(str(self))


class Product(Entity):
    _uti = ProductUti()
    _label = 'Product'

    # latest = RelatedTo(Version, 'latest')
    current = RelatedTo(Version, 'current')
    published = RelatedTo(Version, 'published')
    official = RelatedTo(Version, 'official')
    dependency = RelatedTo(Dependency, 'dependency')

    def set_latest_version(self, new_version):
        self.latest.clear()
        self.latest.add(new_version)

    def set_current_version(self, new_version):
        self.current.clear()
        self.current.add(new_version)

    def add_dependency(self, to_product):
        # version = self.get_current_version()
        # version.dependency.add(Dependency(product))
        self.dependency.add(Dependency(to_product))

    # def get_latest_version(self):
    #     return iter(self.latest).next()

    def get_current_version(self):
        return iter(self.current).next()

    def get_dependent_version(self, product):
        for dependency in self.dependency:
            if dependency.get_product() == product:
                return dependency.get_version()

    def update_dependent_version(self, product):
        for d in self.dependency:
            if d.get_product() == product:
                d.update_version()

    def update_version(self):
        # do nothing if already at latest version
        if self.get_latest_version() == self.get_current_version():
            return

        self.set_current_version(self.get_latest_version())


class ImageProduct(Product):
    _uti = ImageProductUti()


class GeometryProduct(Product):
    _uti = GeometryProductUti()


class Task(Entity):
    _uti = TaskUti()
    _label = 'Task'
    current = RelatedTo(Version, 'current')
    published = RelatedTo(Version, 'published')
    official = RelatedTo(Version, 'official')

    def __init__(self, name, version):
        super(Task, self).__init__(name)
        self.current.add(version)

    def add_version(self):
        current_version = None
        try:
            # current_version = iter(self.latest).next()
            current_version = iter(self.current).next()
        except StopIteration:
            pass
        new_version = Version(self, current_version)
        subgraph = Subgraph([new_version, current_version, self])
        # self.set_latest_version(new_version)
        self.set_current_version(new_version)
        connect().push(subgraph)
        return new_version

    def add_dependency(self, to_version):
        version = self.get_current_version()
        version.dependency.add(to_version)

    def get_current_version(self):
        return iter(self.current).next()

    def set_current_version(self, to_version):
        self.current.clear()
        self.current.add(to_version)


class AssetTask(Task):
    asset = Property()
    context = Property()

    def __init__(self, name, version, asset, context):
        super(AssetTask, self).__init__(name, version)
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


def generate_modeling_task():
    geometry_product = GeometryProduct('geometry')
    first_version = Version([geometry_product])
    model_boots = ModelingTask('model-boots', first_version, 'hiccup', 'test:context')
    return Subgraph([model_boots, first_version, geometry_product])


def generate_surfacing_task(model_task):
    images_product = ImageProduct('textures')
    first_version = Version([images_product])
    first_version.add_dependency(model_task)
    texture_boots = TextureTask('texture-boots', first_version, 'hiccup', 'test:context')
    return Subgraph([texture_boots, images_product])


def main():
    graph = connect()
    graph.delete_all()
    graph.push(get_types())
    subgraph = generate_modeling_task()
    subgraph |= generate_surfacing_task(subgraph.nodes[0])
    graph.push(subgraph)
    return graph


graph = main()
# graph = connect()
model_product = Product.select(graph, 'model-boots:geometry').first()
texture_product = Product.select(graph, 'texture-boots:textures').first()
og_version = texture_product.get_current_version()
model_product.add_version()
texture_product.update_dependent_version(model_product)
# model_product.add_version()
# model_product.add_version()
# other = ModelingTask('test-model', 'another_asset', 'some:context')
# graph.push(other)
# texture_product.update_version()
version = texture_product.add_version()
product = og_version.get_product(graph)
print product

