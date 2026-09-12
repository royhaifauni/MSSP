# planar_mssp.py
import networkx as nx

class PlanarMSSPDataStructure:
    def __init__(self, G, V_infinity):
        self.G = G.copy()
        self.V_infinity = V_infinity
        self.V_inf_set = set(V_infinity)
        self.s_maps = {}      
        self.delta_maps = {}  
        self.tree_distances = {}
        self.build_log = []
        
        full_interval = (0, len(V_infinity) - 1)
        self.build_log.append({"type": "info", "msg": "Starting Preprocessing", "H_nodes": list(self.G.nodes()), "H_edges": list(self.G.edges(data=True))})
        self._mssp(full_interval, self.G)

    def _compute_sssp_tree(self, H, root):
        try:
            lengths, paths = nx.single_source_dijkstra(H, root, weight='weight')
        except nx.NetworkXNoPath:
            return set(), {}, {}
            
        tree_edges = set()
        parent_map = {}
        for target, path in paths.items():
            if len(path) > 1:
                u, v = path[-2], path[-1]
                tree_edges.add((u, v))
                parent_map[v] = u
        return tree_edges, parent_map, lengths

    def _mssp(self, interval, H_I):
        i1, i2 = interval
        i = (i1 + i2) // 2
        roots = list(set([self.V_infinity[i1], self.V_infinity[i2], self.V_infinity[i]]))
        sssp_trees = {}
        
        for r_idx in roots:
            if r_idx in H_I:
                edges, parents, lengths = self._compute_sssp_tree(H_I, r_idx)
                sssp_trees[r_idx] = (edges, parents, lengths)
                self.tree_distances[(interval, r_idx)] = lengths
                self.build_log.append({
                    "type": "sssp", "interval": interval, "root": r_idx, "edges": list(edges),
                    "H_nodes": list(H_I.nodes()), "H_edges": list(H_I.edges(data=True))
                })

        if i2 - i1 <= 1: return 

        subintervals = [(i1, i), (i, i2)]
        for J in subintervals:
            j1, j2 = J
            r_j1, r_j2 = self.V_infinity[j1], self.V_infinity[j2]
            
            if r_j1 not in sssp_trees or r_j2 not in sssp_trees: continue
                
            self.build_log.append({
                "type": "info", "interval": J, "msg": f"Switching to sub-interval {J}",
                "H_nodes": list(H_I.nodes()), "H_edges": list(H_I.edges(data=True))
            })
                
            edges_j1, parents_j1, _ = sssp_trees[r_j1]
            edges_j2, parents_j2, _ = sssp_trees[r_j2]
            e_shared = edges_j1.intersection(edges_j2)
            
            self.build_log.append({
                "type": "eshared", "interval": J, "edges": list(e_shared),
                "H_nodes": list(H_I.nodes()), "H_edges": list(H_I.edges(data=True))
            })
            
            H_J = H_I.copy()
            s_map_J = {}
            delta_map_J = {}
            
            targets_in_shared = set(v for u, v in e_shared)
            roots_of_shared = set(u for u, v in e_shared if u not in targets_in_shared)
            
            for s in roots_of_shared:
                sub_tree_nodes = self._get_subtree_nodes(s, e_shared)
                if len(sub_tree_nodes) > 1:
                    self.build_log.append({
                        "type": "contract_target", "interval": J, "s": s, "nodes": list(sub_tree_nodes), 
                        "H_nodes": list(H_J.nodes()), "H_edges": list(H_J.edges(data=True))
                    })
                    
                    H_J = self._contract_tree(H_J, s, sub_tree_nodes, s_map_J, delta_map_J)
                    
                    self.build_log.append({
                        "type": "contract_done", "interval": J, "s": s,
                        "s_map": dict(s_map_J), "delta_map": dict(delta_map_J),
                        "H_nodes": list(H_J.nodes()), "H_edges": list(H_J.edges(data=True))
                    })

            self.s_maps[J] = s_map_J
            self.delta_maps[J] = delta_map_J
            self._mssp(J, H_J)

    def _get_subtree_nodes(self, root, edge_set):
        nodes = {root}
        queue = [root]
        children = {}
        for u, v in edge_set: children.setdefault(u, []).append(v)
        while queue:
            curr = queue.pop(0)
            for child in children.get(curr, []):
                if child not in nodes and child not in self.V_inf_set:
                    nodes.add(child)
                    queue.append(child)
        return nodes

    def _contract_tree(self, H_J, s, t_nodes, s_map_J, delta_map_J):
        subgraph = H_J.subgraph(t_nodes)
        internal_lengths = nx.single_source_dijkstra_path_length(subgraph, s, weight='weight') if s in subgraph else {s: 0}
        
        for u in t_nodes:
            s_map_J[u] = s
            delta_map_J[u] = internal_lengths.get(u, 0)
            
        edges_to_add, edges_to_remove = [], []
        for u in t_nodes:
            if u not in H_J: continue
            for _, v, data in H_J.out_edges(u, data=True):
                if v not in t_nodes:
                    edges_to_add.append((s, v, data.get('weight', 1) + delta_map_J.get(u, 0)))
                    edges_to_remove.append((u, v))
            for v, _, data in H_J.in_edges(u, data=True):
                if v not in t_nodes and u != s:
                    edges_to_remove.append((v, u))

        H_J.remove_edges_from(edges_to_remove)
        for u, v, w in edges_to_add:
            if H_J.has_edge(u, v): H_J[u][v]['weight'] = min(H_J[u][v]['weight'], w)
            else: H_J.add_edge(u, v, weight=w)
                
        for u in t_nodes:
            if u != s and u in H_J: H_J.remove_node(u) 
        return H_J

    def query(self, u, j_index, interval=(0, None), log=None, current_delta=0, chain=None):
        if interval[1] is None: 
            interval = (0, len(self.V_infinity) - 1)
        if chain is None:
            chain = [u]
            if log is not None:
                log.append({"type": "start", "interval": interval, "chain": list(chain), "delta": current_delta})
            
        i1, i2 = interval
        if j_index == i1 or j_index == i2:
            r_node = self.V_infinity[j_index]
            dist = self.tree_distances.get((interval, r_node), {}).get(u, float('inf'))
            if log is not None: 
                log.append({"type": "base_case", "interval": interval, "node": u, "found_dist": dist, "total": current_delta + dist})
            return dist

        i = (i1 + i2) // 2
        active_J = (i1, i) if j_index <= i else (i, i2)
        mapped_s = self.s_maps.get(active_J, {}).get(u, u)
        delta_val = self.delta_maps.get(active_J, {}).get(u, 0)
        
        # Track the nested hierarchy of targets
        new_chain = list(chain)
        if mapped_s != u:
            new_chain.append(mapped_s)
            
        new_delta = current_delta + delta_val
        
        if log is not None: 
            log.append({
                "type": "lookup", 
                "interval": active_J, 
                "original_u": u, 
                "mapped_s": mapped_s, 
                "delta": new_delta,
                "chain": new_chain
            })
            
        return self.query(mapped_s, j_index, active_J, log, new_delta, new_chain)