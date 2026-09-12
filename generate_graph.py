# generate_graph.py
import math
import random
import networkx as nx

def scale_positions(pos, width, height, margin_x, margin_y, top_offset):
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    scaled_pos = {}
    for node, (x, y) in pos.items():
        nx_norm = (x - min_x) / (max_x - min_x) if max_x > min_x else 0.5
        ny_norm = (y - min_y) / (max_y - min_y) if max_y > min_y else 0.5
        sx = margin_x + nx_norm * (width - 2 * margin_x)
        sy = top_offset + margin_y + ny_norm * (height - top_offset - 2 * margin_y)
        scaled_pos[node] = (sx, sy)
    return scaled_pos

def generate_graph(draw_width, draw_height, margin_x, margin_y, top_offset):
    G = nx.DiGraph()
    pos = {}
    
    G.add_node("C")
    pos["C"] = (0, 0)
    
    inner_ring = []
    for i in range(5):
        angle = i * (2 * math.pi / 5)
        node = f"I_{i}"
        inner_ring.append(node)
        G.add_node(node)
        pos[node] = (math.cos(angle), math.sin(angle))
        if random.random() > 0.1: G.add_edge("C", node, weight=random.randint(1, 7))
        if random.random() > 0.1: G.add_edge(node, "C", weight=random.randint(1, 7))
        
    for i in range(5):
        u, v = inner_ring[i], inner_ring[(i+1)%5]
        G.add_edge(u, v, weight=random.randint(1, 7))
        G.add_edge(v, u, weight=random.randint(1, 7))

    boundary_nodes = []
    for i in range(10):
        angle = i * (2 * math.pi / 10)
        node = f"b_{i}"
        boundary_nodes.append(node)
        G.add_node(node)
        pos[node] = (2.5 * math.cos(angle), 2.5 * math.sin(angle))
        
    for i in range(10):
        u, v = boundary_nodes[i], boundary_nodes[(i+1)%10]
        G.add_edge(u, v, weight=random.randint(1, 7))
        G.add_edge(v, u, weight=random.randint(1, 7))
        
        inner_node = inner_ring[i // 2]
        if random.random() > 0.1: G.add_edge(inner_node, boundary_nodes[i], weight=random.randint(1, 7))
        if random.random() > 0.1: G.add_edge(boundary_nodes[i], inner_node, weight=random.randint(1, 7))

    V_infinity = []
    radius_multiplier = 1.35
    for i in range(10):
        b_i = boundary_nodes[i]
        r_i = f"r_{i}"
        V_infinity.append(r_i)
        bx, by = pos[b_i]
        pos[r_i] = (bx * radius_multiplier, by * radius_multiplier)

    final_pos = scale_positions(pos, draw_width, draw_height, margin_x, margin_y, top_offset)
    return G, final_pos, boundary_nodes, V_infinity