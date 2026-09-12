# Planar Multiple-Source Shortest Paths (MSSP) Visualizer

A Pygame-based educational visualizer for the divide-and-conquer contraction algorithm for Multiple-Source Shortest Paths in planar digraphs. 

This project explicitly models the theoretical $O(n \log |f_\infty|)$ algorithm detailed in *A Simple Algorithm for Multiple-Source Shortest Paths in Planar Digraphs* by Das, Kipouridis, Probst Gutenberg, and Wulff-Nilsen.

## Features
* **Graph Generation:** Dynamically generates a sparse, circular planar graph with randomized edge weights.
* **Topological Preparation:** Visually animates the creation of an artificial, infinite-weight outer boundary face ($f_\infty$) to enforce topological restrictions.
* **Preprocessing Animation:** Steps through the divide-and-conquer binary tree of intervals, visualizing:
  * Single-Source Shortest Path (SSSP) calculations from interval boundaries.
  * The identification of $E_{\text{shared}}$ branches.
  * Graph minor contraction, where bounded trees are absorbed into super-vertices.
* **Query Tracing:** Demonstrates the $O(\log |f_\infty|)$ query lookup utilizing $s$-maps (nesting-doll super-vertex targeting) and $\delta$-maps (internal distance accumulation) to evaluate true topological distances.

## Project Structure
The codebase has been refactored into four functional files to strictly separate the algorithm's backend math from the frontend visual rendering:
* `config.py` - Stores dimension and color constants.
* `generate_graph.py` - Handles NetworkX planar graph generation and geometric coordinate scaling.
* `planar_mssp.py` - Contains the `PlanarMSSPDataStructure` class, the raw algorithm, and data logging.
* `main.py` - The Pygame entry point that runs the visualizer loop.

## Requirements
* Python 3.x
* `pygame`
* `networkx`

Installation via `uv` or `pip`:
```bash
pip install pygame networkx