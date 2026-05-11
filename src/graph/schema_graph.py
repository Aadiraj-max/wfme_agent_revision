import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import networkx as nx
import json
from src.graph.logical_edges import LOGICAL_EDGES

class SchemaGraph:
    def __init__(self):
        # Using MultiGraph to handle multiple edges between the same pair of tables
        self.graph = nx.MultiGraph()
        self._build()

    def _build(self):
        """
        Iterates over LOGICAL_EDGES and populates the MultiGraph.
        """
        for edge in LOGICAL_EDGES:
            from_table = edge["from_table"]
            to_table = edge["to_table"]

            # Add nodes if they don't exist
            if not self.graph.has_node(from_table):
                self.graph.add_node(from_table)
            if not self.graph.has_node(to_table):
                self.graph.add_node(to_table)

            # Add undirected edge with attributes
            self.graph.add_edge(
                from_table,
                to_table,
                from_column=edge["from_column"],
                to_column=edge["to_column"],
                relationship_type=edge["relationship_type"]
            )

    def get_join_path(self, from_table: str, to_table: str) -> list | None:
        """
        Uses nx.shortest_path to find the shortest node path.
        Returns None if no path exists.
        """
        try:
            path = nx.shortest_path(self.graph, from_table, to_table)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def get_join_details(self, path: list) -> list:
        """
        Takes a path list and returns a list of join details for each step.
        For MultiGraph, we take the first edge (index 0) between consecutive nodes.
        """
        if not path or len(path) < 2:
            return []

        details = []
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i + 1]
            
            # self.graph[u][v] for MultiGraph returns a dict of edges {0: attr_dict, 1: attr_dict, ...}
            # We take index 0 as per instruction
            edge_data = self.graph[u][v][0]
            
            # Find the original matching edge in LOGICAL_EDGES to determine which column belongs to which table
            matching_edge = None
            for e in LOGICAL_EDGES:
                if (e["from_table"] == u and e["to_table"] == v) or (e["from_table"] == v and e["to_table"] == u):
                    matching_edge = e
                    break
            
            if matching_edge:
                if matching_edge["from_table"] == u:
                    details.append({
                        "from_table": u,
                        "from_column": matching_edge["from_column"],
                        "to_table": v,
                        "to_column": matching_edge["to_column"],
                        "relationship_type": matching_edge["relationship_type"]
                    })
                else:
                    details.append({
                        "from_table": u,
                        "from_column": matching_edge["to_column"],
                        "to_table": v,
                        "to_column": matching_edge["from_column"],
                        "relationship_type": matching_edge["relationship_type"]
                    })
        
        return details

    def get_all_tables(self) -> list:
        """Return a sorted list of all node names in the graph."""
        return sorted(list(self.graph.nodes()))

    def get_neighbors(self, table_name: str) -> list:
        """Return a list of all tables directly connected to the given table."""
        if not self.graph.has_node(table_name):
            return []
        return list(self.graph.neighbors(table_name))

if __name__ == '__main__':
    g = SchemaGraph()
    print(f'Graph built with {g.graph.number_of_nodes()} nodes and {g.graph.number_of_edges()} edges.')
    print(f'All tables: {g.get_all_tables()}')
    
    path = g.get_join_path('EMP_WORKSLOT', 'LOCATIONS')
    print(f'Path from EMP_WORKSLOT to LOCATIONS: {path}')
    if path:
        details = g.get_join_details(path)
        for step in details:
            print(f"  JOIN {step['from_table']}.{step['from_column']} = {step['to_table']}.{step['to_column']}")
    
    path2 = g.get_join_path('VACATION_BALANCE', 'LOCATIONS')
    print(f'Path from VACATION_BALANCE to LOCATIONS: {path2}')
    if path2:
        details2 = g.get_join_details(path2)
        for step in details2:
            print(f"  JOIN {step['from_table']}.{step['from_column']} = {step['to_table']}.{step['to_column']}")
