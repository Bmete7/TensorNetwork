# Copyright 2019 The TensorNetwork Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Helper methods for `path_contractors`."""

from tensornetwork import network
from tensornetwork import network_components
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# `opt_einsum` algorithm method typing
Algorithm = Callable[[List[Set[int]], Set[int], Dict[int, int]],
                     List[Tuple[int, int]]]


def multi_remove(elems: List[Any], indices: List[int]) -> List[Any]:
  """Remove multiple indicies in a list at once."""
  return [i for j, i in enumerate(elems) if j not in indices]


def get_first_nondangling(node: network_components.CopyNode) -> Optional[network_components.Edge]:
  """Returns the first non-dangling edge of a copy node."""
  for edge in node.edges:
    if not edge.is_dangling():
      return edge
  return None


def get_path(net: network.TensorNetwork, algorithm: Algorithm
             ) -> Tuple[List[Tuple[int, int]],
                        List[network_components.BaseNode]]:
  """Calculates the contraction paths using `opt_einsum` methods.

  Args:
    net: TensorNetwork object to contract.
    algorithm: `opt_einsum` method to use for calculating the contraction path.

  Returns:
    The optimal contraction path as returned by `opt_einsum`.
  """
  copy_nodes = {node: get_first_nondangling(node) for node in net.nodes_set
                if isinstance(node, network_components.CopyNode)}

  sorted_nodes = sorted(net.nodes_set - set(copy_nodes.keys()),
                        key = lambda n: n.signature)

  edge_map = {} # Maps all non-dangling edges of a copy node to a specific
                # non-dangling edge of this copy node
  node_to_copies = {} # Maps nodes to their copy node neighbors
  copy_to_nodes = {} # Maps copy nodes to their node neighbors
  for copy, edge in copy_nodes.items():
    copy_to_nodes[copy] = {}
    for e in copy.edges:
      if not e.is_dangling():
        edge_map[e] = edge
        node = ({e.node1, e.node2} - {copy}).pop()
        copy_to_nodes[copy].add(node)
        if node in node_to_copies:
          node_to_copies[node].add(copy)
        else:
          node_to_copies[node] = {copy}


  input_sets = [set(node.edges) for node in sorted_nodes]
  output_set = net.get_all_edges() - net.get_all_nondangling()
  size_dict = {edge: edge.dimension for edge in net.get_all_edges()}

  return algorithm(input_sets, output_set, size_dict), sorted_nodes



#def get_path(net: network.TensorNetwork, algorithm: Algorithm
#             ) -> Tuple[Union[List[Tuple[int]],
#                        List[network_components.BaseNode]]]:
#  """Calculates the contraction paths using `opt_einsum` methods.
#
#  Args:
#    net: TensorNetwork object to contract.
#    algorithm: `opt_einsum` method to use for calculating the contraction path.
#
#  Returns:
#    The optimal contraction path as returned by `opt_einsum`.
#    A list of nodes sorted compatibly with their indices in the path.
#  """
#  copy_nodes = {node: get_first_nondangling(node) for node in net.node_set
#                if isinstance(node, network_components.CopyNode)}
#
#  sorted_nodes = sorted(net.node_set - set(copy_nodes.keys()),
#                        key = lambda n: n.signature)
#
#  if copy_nodes:
#    # TODO: Work in progress!
#
#    # Map all non-dangling edges of a copy node to one specific edge.
#    # In `einsum` notation this is equivalent to using a character more
#    # than twice.
#    edge_map = {}
#    for node, edge in copy_nodes.items():
#      edge_map.update({e: edge for e in node.edges})
#    input_sets = [set((edge_map[edge] if edge in edge_map else edge
#                       for edge in node.edges)) for node in sorted_nodes]
#  else:
#    input_sets = [set(node.edges) for node in sorted_nodes]
#
#  output_set = net.get_all_edges() - net.get_all_nondangling()
#  size_dict = {edge: edge.dimension for edge in net.get_all_edges()}
#
#  return algorithm(input_sets, output_set, size_dict), sorted_nodes