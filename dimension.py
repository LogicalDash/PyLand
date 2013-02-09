import igraph

class Dimension:
    def __init__(self, name, places=[], portals=[]):
        self.name = name
        self.places = places
        self.portals = portals
    def add_place(self, place):
        self.places.append(place)
    def add_portal(self, portal):
        self.portals.append(portal)
    def get_edge(self, portal):
        origi = self.places.index(portal.orig)
        desti = self.places.index(portal.dest)
        return (origi, desti)
    def get_edges(self):
        return [ self.get_edge(port) for port in self.portals ]
    def get_edge_atts(self):
        r = {}
        for port in self.portals:
            key = self.get_edge(port)
            val = port.att.iteritems()
            r[key] = val
        return r
    def get_vertex_atts(self):
        r = {}
        i = 0
        while i < len(self.places):
            r[i] = self.places[i].att.iteritems()
            i += 1
        return r
    def get_graph(self):
        return igraph.Graph(edges=self.get_edges(), directed=True,
                            vertex_attrs=self.get_vertex_atts(),
                            edge_attrs=self.get_edge_atts())