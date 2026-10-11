# main.py
import sys
import pygame
import networkx as nx

from config import *
from generate_graph import generate_graph
from planar_mssp import PlanarMSSPDataStructure

def main():
    G, pos, boundary_nodes, V_infinity = generate_graph(GRAPH_AREA_WIDTH, HEIGHT, 60, 40, 80)

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MSSP Algorithm Visualizer")
    
    font = pygame.font.SysFont("Courier", 14)
    node_font = pygame.font.SysFont("Arial", 12, bold=True)
    title_font = pygame.font.SysFont("Arial", 20, bold=True)
    weight_font = pygame.font.SysFont("Arial", 11, bold=True)
    
    state = "ANIMATE_PREPARE" 
    prep_idx, anim_idx = 0, 0
    last_anim_time = pygame.time.get_ticks()
    
    mssp, start_node, target_node = None, None, None
    query_log, shortest_path, final_distance = [], [], 0
    panel_text = ["--- PREPARING INFINITE FACE ---", "Press SPACE to advance steps..."]
    
    active_interval, active_u, active_step_type = None, None, None
    current_H_nodes = list(G.nodes())
    current_H_edges = list(G.edges(data=True))
    advance_build_step, advance_query_step = False, False

    running = True
    while running:
        screen.fill(WHITE)
        pygame.draw.rect(screen, PANEL_BG, (GRAPH_AREA_WIDTH, 0, WIDTH - GRAPH_AREA_WIDTH, HEIGHT))
        pygame.draw.line(screen, BLACK, (GRAPH_AREA_WIDTH, 0), (GRAPH_AREA_WIDTH, HEIGHT), 3)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if state == "ANIMATE_PREPARE": 
                    n = len(V_infinity)
                    while prep_idx < 2 * n:
                        if prep_idx < n:
                            G.add_node(V_infinity[prep_idx])
                            G.add_edge(V_infinity[prep_idx], boundary_nodes[prep_idx], weight=0)
                        else:
                            G.add_edge(V_infinity[prep_idx - n], V_infinity[(prep_idx - n + 1) % n], weight=float('inf'))
                        prep_idx += 1
                    current_H_nodes = list(G.nodes())
                    current_H_edges = list(G.edges(data=True))
                elif state == "ANIMATE_BUILD": 
                    advance_build_step = True 
                elif state == "ANIMATE_QUERY": 
                    advance_query_step = True
                elif state == "SHOW_PATH":
                    # Flawless reset via SPACE for unlimited subsequent queries
                    state = "WAIT_START"
                    start_node, target_node = None, None
                    active_interval, active_u = None, None
                    shortest_path, query_log = [], []
                    panel_text = ["--- AWAITING INPUT ---", "Select a green boundary node."]
                    current_H_nodes = list(G.nodes())
                    current_H_edges = list(G.edges(data=True))
                    advance_query_step = False 
                    
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = event.pos
                
                # Ignore clicks unless we are explicitly waiting for node selection
                if state in ["ANIMATE_PREPARE", "BUILD_BACKEND", "ANIMATE_BUILD", "ANIMATE_QUERY", "SHOW_PATH"]: 
                    continue
                    
                clicked_node = None
                for node, (nx_x, nx_y) in pos.items():
                    if node not in G.nodes(): continue
                    if (mouse_x - nx_x)**2 + (mouse_y - nx_y)**2 <= NODE_RADIUS**2:
                        clicked_node = node
                        break
                        
                if clicked_node:
                    if state == "WAIT_START" and clicked_node in V_infinity:
                        start_node = clicked_node
                        state = "WAIT_TARGET"
                        panel_text = ["--- AWAITING INPUT ---", "Target node: Please click anywhere."]
                    elif state == "WAIT_TARGET":
                        target_node = clicked_node
                        query_log = []
                        final_distance = mssp.query(target_node, V_infinity.index(start_node), log=query_log)
                        try: 
                            shortest_path = nx.shortest_path(G, source=start_node, target=target_node, weight='weight')
                        except nx.NetworkXNoPath: 
                            shortest_path = []
                        
                        anim_idx = -1
                        panel_text = ["--- EXECUTING QUERY ---", f"Start: {start_node}", f"Target: {target_node}", "Press SPACE to trace."]
                        state = "ANIMATE_QUERY"
                        current_H_nodes = list(G.nodes())
                        current_H_edges = list(G.edges(data=True))

        active_edges, active_eshared, active_nodes = [], [], []
        active_root = None
        current_interval_nodes = []
        
        if state == "ANIMATE_PREPARE":
            if current_time - last_anim_time > 100:
                n = len(V_infinity)
                if prep_idx < n:
                    G.add_node(V_infinity[prep_idx])
                    G.add_edge(V_infinity[prep_idx], boundary_nodes[prep_idx], weight=0)
                elif prep_idx < 2 * n:
                    G.add_edge(V_infinity[prep_idx - n], V_infinity[(prep_idx - n + 1) % n], weight=float('inf'))
                else:
                    state = "BUILD_BACKEND"
                    current_H_nodes = list(G.nodes())
                    current_H_edges = list(G.edges(data=True))
                prep_idx += 1
                last_anim_time = current_time

        elif state == "BUILD_BACKEND":
            screen.blit(title_font.render("PREPARING BACKEND... (Please wait)", True, BLACK), (20, 10))
            pygame.display.flip()
            mssp = PlanarMSSPDataStructure(G, V_infinity)
            state = "ANIMATE_BUILD"
            panel_text = ["--- PREPROCESSING ---", "Press SPACE to advance steps."]

        elif state == "ANIMATE_BUILD":
            if advance_build_step:
                advance_build_step = False
                if anim_idx < len(mssp.build_log) - 1:
                    anim_idx += 1
                    step = mssp.build_log[anim_idx]
                    
                    if "H_nodes" in step:
                        current_H_nodes, current_H_edges = step["H_nodes"], step["H_edges"]
                    if step.get("interval"): 
                        active_interval = step["interval"]
                    
                    active_step_type = step.get("type")
                    if active_step_type == "info": panel_text.append(step["msg"])
                    elif active_step_type == "sssp": panel_text.append(f"Int {active_interval}: SSSP from {step['root']}")
                    elif active_step_type == "eshared": panel_text.append(f"Int {active_interval}: Highlighting E_shared (Magenta)")
                    elif active_step_type in ["contract_target", "contract"]: panel_text.append(f"Int {active_interval}: Target T({step['s']}) (Purple)")
                    elif active_step_type == "contract_done": panel_text.append(f"Int {active_interval}: Absorbed into {step['s']}")
                else:
                    state = "WAIT_START"
                    active_interval, active_step_type = None, None
                    panel_text = ["--- PREPROCESSING COMPLETE ---", "Click a green boundary node."]
                    current_H_nodes = list(G.nodes())
                    current_H_edges = list(G.edges(data=True))

            if anim_idx < len(mssp.build_log):
                step = mssp.build_log[anim_idx]
                if "interval" in step: 
                    current_interval_nodes = [V_infinity[k] for k in range(step["interval"][0], step["interval"][1] + 1)]
                
                if step.get("type") == "sssp": active_edges, active_root = step["edges"], step["root"]
                elif step.get("type") == "eshared": active_eshared = step["edges"]
                elif step.get("type") in ["contract_target", "contract"]: active_nodes, active_root = step["nodes"], step["s"]
                elif step.get("type") == "contract_done": active_nodes, active_root = [], step["s"]

        elif state == "ANIMATE_QUERY":
            if advance_query_step:
                advance_query_step = False
                if anim_idx < len(query_log) - 1:
                    anim_idx += 1
                    step = query_log[anim_idx]
                    if step["type"] == "start":
                        active_interval = step["interval"]
                        panel_text.append(f"Start Int: {active_interval}")
                    elif step["type"] == "lookup":
                        active_interval, active_u = step["interval"], step["original_u"]
                        chain_str = " -> ".join(map(str, step.get("chain", [step["original_u"], step["mapped_s"]])))
                        panel_text.append(f"Drop to {active_interval} | Total delta={step.get('delta', 0)}")
                        panel_text.append(f"  Target: {chain_str}")
                    elif step["type"] == "base_case":
                        active_interval, active_u = step["interval"], None
                        
                        # Prevent the double-print bug by verifying we haven't already appended it
                        new_text = f"Base case {active_interval}! Dist to {step['node']}: {step['found_dist']}"
                        if panel_text[-1] != new_text:
                            panel_text.append(new_text)
                else:
                    if not panel_text[-1].startswith("TOTAL"):
                        panel_text.append(f"TOTAL DISTANCE: {final_distance}")
                    state = "SHOW_PATH"
                    
                    # Restore the un-contracted graph so the orange path renders correctly
                    current_H_nodes = list(G.nodes())
                    current_H_edges = list(G.edges(data=True))
                
            if state == "ANIMATE_QUERY" and 0 <= anim_idx < len(query_log):
                step = query_log[anim_idx]
                if step["type"] == "lookup":
                    active_nodes = [step["original_u"], step["mapped_s"]]
                if step.get("interval"):
                    active_interval = step["interval"]
                    
                    # Apply graph shrinking during trace
                    if active_interval in mssp.interval_graphs:
                        current_H_nodes = mssp.interval_graphs[active_interval][0]
                        current_H_edges = mssp.interval_graphs[active_interval][1]

        # --- DRAWING ---
        for u, v, data in current_H_edges:
            weight = data.get('weight', 1)
            is_inf = (weight == float('inf'))
            edge_color = GRAY if is_inf else BLACK
            
            pygame.draw.line(screen, edge_color, pos[u], pos[v], 1)
            
            mid_x = (pos[u][0] + pos[v][0]) / 2
            mid_y = (pos[u][1] + pos[v][1]) / 2
            
            weight_str = "∞" if is_inf else str(weight)
            text_color = GRAY if is_inf else (0, 0, 150)
            
            weight_surface = weight_font.render(weight_str, True, text_color)
            screen.blit(weight_surface, (mid_x - weight_surface.get_width() // 2, mid_y - weight_surface.get_height() // 2))
                
        if active_edges:
            for u, v in active_edges:
                if u in V_infinity and v in V_infinity: continue 
                if u in current_H_nodes and v in current_H_nodes:
                    pygame.draw.line(screen, CYAN, pos[u], pos[v], 4)
                    
        if active_eshared:
            for u, v in active_eshared:
                if u in V_infinity and v in V_infinity: continue 
                if u in current_H_nodes and v in current_H_nodes:
                    pygame.draw.line(screen, MAGENTA, pos[u], pos[v], 5)
                
        if state == "SHOW_PATH" and shortest_path:
            for i in range(len(shortest_path) - 1):
                pygame.draw.line(screen, ORANGE, pos[shortest_path[i]], pos[shortest_path[i+1]], 5)

        for node in current_H_nodes:
            n_pos = pos[node]
            color = GREEN if node in V_infinity else LIGHT_BLUE
            border_color, border_width = (DARK_GREEN, 4) if node in current_interval_nodes else (BLACK, 1)
            
            if node == start_node: color = YELLOW
            elif node == target_node and state != "ANIMATE_QUERY": color = RED
            if node == active_root: color = YELLOW
            elif node in active_nodes: color = PURPLE
            if state == "SHOW_PATH" and node in shortest_path and node not in (start_node, target_node): color = ORANGE
                
            pygame.draw.circle(screen, color, n_pos, NODE_RADIUS)
            pygame.draw.circle(screen, border_color, n_pos, NODE_RADIUS, border_width)
            screen.blit(node_font.render(str(node), True, BLACK), (n_pos[0] + 12, n_pos[1] - 20))

        screen.blit(title_font.render(f"State: {state} (Press SPACE to step)", True, BLACK), (20, 10))
        if state == "ANIMATE_BUILD": screen.blit(font.render("Yellow: Root | Cyan: SSSP | Magenta: E_shared | Purple: Contract target", True, BLACK), (20, 40))
        if active_interval and state in ["ANIMATE_BUILD", "ANIMATE_QUERY"]:
            interval_title = title_font.render(f"Current Graph for Interval: {active_interval}", True, DARK_GREEN)
            screen.blit(interval_title, (GRAPH_AREA_WIDTH // 2 - interval_title.get_width() // 2, 50))

        for i, line in enumerate(panel_text[-25:]):
            screen.blit(font.render(line, True, BLACK), (GRAPH_AREA_WIDTH + 20, 20 + i * 20))

        pygame.display.flip()

if __name__ == "__main__":
    main()