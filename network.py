# %%
import networkx as nx
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from csv import DictReader
from itertools import groupby

# %%
DATA_ROOT = './data/'
TRIPS_FILE = f'{DATA_ROOT}trips.txt'
ROUTES_FILE = f'{DATA_ROOT}routes.txt'
STOPS_FILE = f'{DATA_ROOT}stops.txt'
STOPS_TIMES_FILE = f'{DATA_ROOT}stop_times.txt'

INCLUDE_AGENCIES = []

# %%


def load_routes(filename):
    """ include only routes from agencies we are interested in
    """
    routes_csv = DictReader(open(filename, 'r', encoding='utf-8'))
    routes_dict = dict()

    for route in routes_csv:
        if route['agency_id'] in INCLUDE_AGENCIES or len(INCLUDE_AGENCIES) == 0:
            routes_dict[route[routes_csv.fieldnames[0]]] = route
    print('routes', len(routes_dict))
    return routes_dict


def load_trips(filename, routes_dict):
    """ load trips from file
        only include trips on routes we are interested in
    """
    trips_csv = DictReader(open(filename, 'r', encoding='utf-8'))
    trips_dict = dict()
    for trip in trips_csv:
        if trip[trips_csv.fieldnames[0]] in routes_dict:
            trip['color'] = routes_dict[trip[trips_csv.fieldnames[0]]]['route_color']
            trip['route_short_name'] = routes_dict[trip[trips_csv.fieldnames[0]]
                                                   ]['route_short_name']
            trips_dict[trip['trip_id']] = trip
    print('trips', len(trips_dict))
    return trips_dict


def load_stops(filename):
    stops_csv = DictReader(open(filename, 'r', encoding='utf-8'))
    stops_dict = dict()
    for stop in stops_csv:
        stops_dict[stop[stops_csv.fieldnames[0]]] = stop
    print('stops', len(stops_dict))
    return stops_dict


# %%
ROUTES = load_routes(filename=ROUTES_FILE)
TRIPS = load_trips(filename=TRIPS_FILE, routes_dict=ROUTES)
STOPS = load_stops(filename=STOPS_FILE)

# %%
stop_times_csv = DictReader(
    open(f'{DATA_ROOT}stop_times.txt', 'r', encoding='utf-8'))

# %%
stops = set()
edges = dict()
G = nx.MultiDiGraph()

times_group = groupby(
    stop_times_csv, lambda stop_time: stop_time[stop_times_csv.fieldnames[0]])

for trip_id, stop_time_iter in times_group:
    if trip_id in TRIPS:
        trip = TRIPS[trip_id]
        prev_stop = next(stop_time_iter)['stop_id']
        stops.add(prev_stop)
        for stop_time in stop_time_iter:
            stop = stop_time['stop_id']
            edge = (prev_stop, stop)
            edges[edge] = trip['route_short_name']
            stops.add(stop)
            prev_stop = stop

print('stops', len(stops))
print('edges', len(edges))

# %%


def get_stop_id(stop_id):
    """ translate stop_id to parent_stop_id 
        if available
    """
    if STOPS[stop_id]['parent_station'] == '':
        return stop_id
    else:
        return STOPS[stop_id]['parent_station']


def add_stop_to_graph(G, stop_id):
    """ add stop as new node to graph
    """
    node = STOPS[get_stop_id(stop_id)]

    if node['\ufeffstop_id'] not in G.nodes:
        G.add_node(node['\ufeffstop_id'],
                   stop_code=node['stop_code'],
                   stop_name=node['stop_name'],
                   stop_lon=node['stop_lon'],
                   stop_lat=node['stop_lat'])
    return G


def add_edge_to_graph(G, from_id, to_id, route_short_name):
    """ add edge to graph 
        adding the route short name as a key
        if the edge and key exist, increment the count
    """

    G.add_edge(get_stop_id(from_id), get_stop_id(
        to_id), route=route_short_name,)


def get_stop_id_by_code(stop_code):
    """ get stop_id by stop_code
    """
    for stop_id in STOPS:
        if STOPS[stop_id]['stop_code'] == stop_code:
            return stop_id
    return None


# %%
for stop_id in STOPS:
    if stop_id in stops:
        add_stop_to_graph(G, stop_id)
print('Nodes:', G.number_of_nodes())

for (start_stop_id, end_stop_id), route_short_name in edges.items():
    add_edge_to_graph(G,
                      from_id=start_stop_id,
                      to_id=end_stop_id,
                      route_short_name=route_short_name)
print('Edges:', G.number_of_edges())

# %%
deg = nx.degree(G)

pos = {
    stop_id: (
        float(G.nodes[stop_id]['stop_lon']),
        float(G.nodes[stop_id]['stop_lat'])
    )
    for stop_id in G.nodes
    if 'stop_lon' in G.nodes[stop_id] and 'stop_lat' in G.nodes[stop_id]
}

subgraph_nodes = [stop_id for stop_id in G.nodes if stop_id in pos]

data_crs = ccrs.PlateCarree()

fig = plt.figure(figsize=(250, 250))
ax = plt.axes(projection=ccrs.PlateCarree())

nx.draw_networkx(G.subgraph(subgraph_nodes), ax=ax, labels={}, pos=pos, node_size=1,
                 )

ax.set_axis_off()

plt.show()
