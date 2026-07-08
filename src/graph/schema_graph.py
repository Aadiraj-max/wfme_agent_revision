import os
import sys
import networkx as nx
from typing import List, Dict, Any, Optional

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.engine.schema_reflector import SchemaReflector

class SchemaGraph:
    def __init__(self, joins: Optional[List[Dict[str, Any]]] = None, cubes: Optional[List[Dict[str, Any]]] = None):
        """
        Builds the NetworkX MultiGraph from Cube join metadata.
        If joins list is not provided, it fetches them using SchemaReflector on startup.
        """
        self.graph = nx.MultiGraph()
        if joins is None:
            reflector = SchemaReflector()
            meta = reflector.fetch_and_filter()
            joins = meta.get("joins", [])
            if cubes is None:
                cubes = meta.get("cubes", [])
        
        if cubes is None:
            cubes = []
            
        self._build(joins, cubes)

    def _build(self, joins: List[Dict[str, Any]], cubes: List[Dict[str, Any]]):
        """
        Populates the MultiGraph with cubes as nodes and joins as edges.
        """
        # Add all defined cubes as nodes first (so even isolated ones exist)
        for cube in cubes:
            cube_name = cube["name"]
            if not self.graph.has_node(cube_name):
                self.graph.add_node(cube_name)

        for edge in joins:
            from_cube = edge["from_cube"]
            to_cube = edge["to_cube"]

            # Add nodes (Cube names) if they don't exist (safety fallback)
            if not self.graph.has_node(from_cube):
                self.graph.add_node(from_cube)
            if not self.graph.has_node(to_cube):
                self.graph.add_node(to_cube)

            # Add undirected edge with attributes
            self.graph.add_edge(
                from_cube,
                to_cube,
                from_column=edge["from_column"],
                to_column=edge["to_column"],
                relationship_type=edge["relationship_type"]
            )

    def get_join_path(self, from_cube: str, to_cube: str) -> Optional[List[str]]:
        """
        Finds the shortest path of cube names connecting from_cube to to_cube.
        Returns None if no path exists.
        """
        try:
            path = nx.shortest_path(self.graph, from_cube, to_cube)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def get_join_details(self, path: List[str]) -> List[Dict[str, Any]]:
        """
        Takes a path list and returns details of the join at each step.
        """
        if not path or len(path) < 2:
            return []

        details = []
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i + 1]
            
            # Get edge data (MultiGraph returns a dictionary of edges)
            try:
                edge_data = self.graph[u][v][0]
                details.append({
                    "from_table": u,
                    "from_column": edge_data["from_column"],
                    "to_table": v,
                    "to_column": edge_data["to_column"],
                    "relationship_type": edge_data["relationship_type"]
                })
            except Exception:
                # Fallback if edge data is missing
                details.append({
                    "from_table": u,
                    "from_column": "id",
                    "to_table": v,
                    "to_column": "id",
                    "relationship_type": "belongsTo"
                })
        
        return details

    def validate_path(self, target_nodes: List[str]) -> List[str]:
        """
        Validates if an unbroken path exists between requested cubes.
        Drops target nodes that are completely isolated or unreachable from the first/core node.
        If there are multiple target nodes, we start with the first node (our core/anchor)
        and keep only the nodes that have a valid path to it.
        """
        if not target_nodes:
            return []
        
        # Verify which target nodes actually exist in our graph
        valid_targets = [node for node in target_nodes if self.graph.has_node(node)]
        if not valid_targets:
            # If none are in graph, but they are valid single tables, return them
            return target_nodes[:1]
        
        anchor = valid_targets[0]
        verified_targets = [anchor]
        
        for node in valid_targets[1:]:
            if self.get_join_path(anchor, node) is not None:
                verified_targets.append(node)
                
        return verified_targets

    def get_all_tables(self) -> List[str]:
        """Return a sorted list of all node (cube) names in the graph."""
        return sorted(list(self.graph.nodes()))

    def get_neighbors(self, cube_name: str) -> List[str]:
        """Return a list of all cubes directly joined to the given cube."""
        if not self.graph.has_node(cube_name):
            return []
        return list(self.graph.neighbors(cube_name))
