"""
Interactive Knowledge Graph Visualizer using PyVis
Renders NetworkX DiGraphs into styled, color-coded interactive HTML components for Streamlit.
"""

import os
import networkx as nx
from pyvis.network import Network
from typing import Optional, Set, Dict, Any

# Primary palette: Light neutral background, Teal (#00A896), Terracotta Red (#C94A4A)
NODE_STYLE_MAP = {
    "Paper": {
        "color": {"background": "#1D3557", "border": "#112233", "highlight": {"background": "#457B9D", "border": "#1D3557"}},
        "shape": "box",
        "size": 30,
        "font": {"color": "#FFFFFF", "size": 14, "bold": True}
    },
    "Model/Method": {
        "color": {"background": "#00A896", "border": "#028073", "highlight": {"background": "#02C39A", "border": "#00A896"}},
        "shape": "dot",
        "size": 24,
        "font": {"color": "#111827", "size": 13, "bold": True}
    },
    "Dataset": {
        "color": {"background": "#F4A261", "border": "#E76F51", "highlight": {"background": "#E9C46A", "border": "#F4A261"}},
        "shape": "database",
        "size": 22,
        "font": {"color": "#111827", "size": 12, "bold": True}
    },
    "Metric": {
        "color": {"background": "#2A9D8F", "border": "#21867A", "highlight": {"background": "#52B788", "border": "#2A9D8F"}},
        "shape": "diamond",
        "size": 20,
        "font": {"color": "#111827", "size": 12}
    },
    "Limitation": {
        "color": {"background": "#C94A4A", "border": "#A83232", "highlight": {"background": "#E63946", "border": "#C94A4A"}},
        "shape": "triangle",
        "size": 22,
        "font": {"color": "#FFFFFF", "size": 12, "bold": True}
    }
}

EDGE_STYLE_MAP = {
    "PROPOSES_METHOD": {"color": "#457B9D", "width": 2.2, "dashes": False},
    "USES_DATASET": {"color": "#00A896", "width": 2.0, "dashes": False},
    "ACHIEVES_METRIC": {"color": "#2A9D8F", "width": 2.2, "dashes": False},
    "HAS_LIMITATION": {"color": "#C94A4A", "width": 2.5, "dashes": False},
    "OUTPERFORMS": {"color": "#7209B7", "width": 3.0, "dashes": False},
    "CONTRADICTS": {"color": "#E63946", "width": 3.2, "dashes": [6, 6]}
}


def render_knowledge_graph_html(
    graph: nx.DiGraph,
    filter_node_types: Optional[Set[str]] = None,
    highlight_nodes: Optional[Set[str]] = None,
    height: str = "580px",
    width: str = "100%",
    physics_enabled: bool = True
) -> str:
    """
    Renders the NetworkX graph as an interactive PyVis HTML document.
    Includes rich tooltips, color-coded node/edge schemas, and interactive controls.
    """
    if graph.number_of_nodes() == 0:
        return """
        <div style="display:flex; justify-content:center; align-items:center; height:300px; 
                    background:#F8F9FA; border-radius:12px; border:2px dashed #E5E7EB; color:#6B7280; font-family:sans-serif;">
            <div style="text-align:center;">
                <p style="font-size:18px; font-weight:600; margin-bottom:4px;">No Graph Entities Extracted Yet</p>
                <p style="font-size:13px;">Upload 1–5 research PDFs or load sample benchmark papers to generate the Knowledge Graph.</p>
            </div>
        </div>
        """

    net = Network(
        height=height,
        width=width,
        directed=True,
        notebook=False,
        bgcolor="#FAFAFB",
        font_color="#1E293B"
    )

    # Filter nodes if requested
    nodes_to_render = set()
    for n, data in graph.nodes(data=True):
        n_type = data.get("type", "Model/Method")
        if filter_node_types is None or n_type in filter_node_types:
            nodes_to_render.add(n)

    # Add filtered nodes to PyVis
    for n in nodes_to_render:
        data = graph.nodes[n]
        n_type = data.get("type", "Model/Method")
        style = NODE_STYLE_MAP.get(n_type, NODE_STYLE_MAP["Model/Method"])
        desc = data.get("description", "")
        papers = ", ".join(data.get("papers", [])) or "None cited"
        
        # Calculate degree for subtle sizing scaling
        deg = graph.degree(n)
        node_size = style["size"] + min(deg * 2, 16)
        
        is_highlighted = highlight_nodes and n in highlight_nodes
        border_width = 4 if is_highlighted else 1.5
        
        tooltip_html = f"""
        <div style="font-family:sans-serif; min-width:180px; max-width:280px; padding:6px; line-height:1.4;">
            <div style="font-size:14px; font-weight:bold; color:#0F172A; border-bottom:1px solid #E2E8F0; padding-bottom:3px; margin-bottom:4px;">
                {n}
            </div>
            <div style="font-size:12px; color:#475569; margin-bottom:4px;">
                <b style="color:#00A896;">Category:</b> {n_type}
            </div>
            {f'<div style="font-size:11px; color:#334155; margin-bottom:4px;"><b>Context:</b> {desc}</div>' if desc else ''}
            <div style="font-size:11px; color:#64748B;">
                <b>Source Papers:</b> {papers}
            </div>
        </div>
        """
        
        net.add_node(
            n,
            label=str(n),
            title=tooltip_html,
            color=style["color"],
            shape=style["shape"],
            size=node_size,
            borderWidth=border_width,
            font=style["font"]
        )

    # Add edges where both endpoints are rendered
    for u, v, data in graph.edges(data=True):
        if u in nodes_to_render and v in nodes_to_render:
            relation = data.get("relation", "RELATES_TO")
            edge_style = EDGE_STYLE_MAP.get(relation, {"color": "#94A3B8", "width": 1.5, "dashes": False})
            details = data.get("details", "")
            source_paper = data.get("source_paper", "Unknown")
            page_num = data.get("page_num", 1)
            citation = data.get("citation", f"[{source_paper}, p. {page_num}]")
            
            edge_tooltip = f"""
            <div style="font-family:sans-serif; padding:4px; font-size:12px;">
                <b>{u}</b> &rarr; <b>{v}</b><br/>
                <span style="color:#00A896; font-weight:bold;">{relation}</span><br/>
                {f'<i>Details:</i> {details}<br/>' if details else ''}
                <b>Citation:</b> <span style="color:#1D3557; font-weight:600;">{citation}</span>
            </div>
            """
            
            net.add_edge(
                u,
                v,
                title=edge_tooltip,
                label=relation.replace("_", " ").lower(),
                color=edge_style["color"],
                width=edge_style["width"],
                dashes=edge_style["dashes"],
                arrows={"to": {"enabled": True, "scaleFactor": 0.8}},
                font={"size": 10, "color": "#64748B", "align": "horizontal", "background": "rgba(255,255,255,0.7)"}
            )

    # Physics and layout options
    import json
    options = {
        "nodes": {
            "borderWidthSelected": 3,
            "shadow": {"enabled": True, "color": "rgba(0,0,0,0.06)", "size": 6, "x": 2, "y": 2}
        },
        "edges": {
            "smooth": {"type": "cubicBezier", "forceDirection": "none", "roundness": 0.25},
            "shadow": {"enabled": False}
        },
        "physics": {
            "enabled": physics_enabled,
            "barnesHut": {
                "gravitationalConstant": -3500,
                "centralGravity": 0.25,
                "springLength": 130,
                "springConstant": 0.04,
                "damping": 0.09,
                "avoidOverlap": 0.35
            },
            "stabilization": {"iterations": 150}
        },
        "interaction": {
            "hover": True,
            "navigationButtons": True,
            "keyboard": True,
            "zoomView": True
        }
    }
    net.set_options(json.dumps(options))

    # Generate raw HTML string
    html = net.generate_html()
    return html
