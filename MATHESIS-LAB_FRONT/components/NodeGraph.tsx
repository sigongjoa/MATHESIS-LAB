import React, { useEffect, useRef, useState } from 'react';
import { Node, NodeLinkResponse } from '../types';

interface GraphNode {
    id: string;
    title: string;
    x: number;
    y: number;
    vx?: number;
    vy?: number;
    isSelected?: boolean;
}

interface GraphLink {
    source: string;
    target: string;
    type: string;
}

interface NodeGraphProps {
    currentNode: Node;
    allNodes: Node[];
    onNodeClick?: (nodeId: string) => void;
}

/**
 * NodeGraph Component - Displays node relationships in an interactive graph
 * Inspired by Obsidian's graph view with force-directed layout
 */
const NodeGraph: React.FC<NodeGraphProps> = ({ currentNode, allNodes, onNodeClick }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [graphNodes, setGraphNodes] = useState<Map<string, GraphNode>>(new Map());
    const [graphLinks, setGraphLinks] = useState<GraphLink[]>([]);
    const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
    const animationRef = useRef<number>();

    // Initialize graph data from node relationships
    useEffect(() => {
        const nodes = new Map<string, GraphNode>();
        const links: GraphLink[] = [];

        // Add current node at center
        nodes.set(currentNode.node_id, {
            id: currentNode.node_id,
            title: currentNode.title,
            x: 0,
            y: 0,
            isSelected: true,
        });

        // Add linked nodes
        if (currentNode.links) {
            currentNode.links.forEach((link: NodeLinkResponse) => {
                if (link.linked_node_id && link.link_type === 'NODE') {
                    const linkedNode = allNodes.find(n => n.node_id === link.linked_node_id);
                    if (linkedNode) {
                        if (!nodes.has(linkedNode.node_id)) {
                            // Position linked nodes around the current node
                            const angle = Math.random() * Math.PI * 2;
                            const radius = 150;
                            nodes.set(linkedNode.node_id, {
                                id: linkedNode.node_id,
                                title: linkedNode.title,
                                x: Math.cos(angle) * radius,
                                y: Math.sin(angle) * radius,
                                vx: 0,
                                vy: 0,
                            });
                        }
                        links.push({
                            source: currentNode.node_id,
                            target: linkedNode.node_id,
                            type: link.link_relationship || 'EXTENDS',
                        });
                    }
                }
            });
        }

        // Add PDF links as visual indicators
        if (currentNode.links) {
            const pdfCount = currentNode.links.filter(l => l.link_type === 'PDF').length;
            if (pdfCount > 0) {
                // PDF nodes are shown as decorative elements
                nodes.set(`pdf-${currentNode.node_id}`, {
                    id: `pdf-${currentNode.node_id}`,
                    title: `${pdfCount} PDF Files`,
                    x: 120,
                    y: 0,
                });
            }
        }

        setGraphNodes(nodes);
        setGraphLinks(links);
    }, [currentNode, allNodes]);

    // Canvas rendering and force simulation
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || graphNodes.size === 0) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Set canvas size
        const rect = canvas.parentElement?.getBoundingClientRect();
        if (rect) {
            canvas.width = rect.width;
            canvas.height = rect.height;
        }

        // Simple force-directed layout simulation
        const simulate = () => {
            const nodes = Array.from(graphNodes.values());
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            const k = 50; // Repulsion strength
            const c = 0.1; // Damping

            // Apply forces
            nodes.forEach((node, i) => {
                let fx = 0;
                let fy = 0;

                // Attract to center (weaker for current node)
                if (node.id === currentNode.node_id) {
                    fx += (centerX - node.x) * 0.01;
                    fy += (centerY - node.y) * 0.01;
                } else {
                    fx += (centerX - node.x) * 0.02;
                    fy += (centerY - node.y) * 0.02;
                }

                // Repel from other nodes
                nodes.forEach((other, j) => {
                    if (i !== j) {
                        const dx = node.x - other.x;
                        const dy = node.y - other.y;
                        const distance = Math.sqrt(dx * dx + dy * dy) || 1;
                        const repulsion = k / (distance * distance);
                        fx += (dx / distance) * repulsion;
                        fy += (dy / distance) * repulsion;
                    }
                });

                // Apply link forces (attraction)
                graphLinks.forEach(link => {
                    if (link.source === node.id) {
                        const target = nodes.find(n => n.id === link.target);
                        if (target) {
                            const dx = target.x - node.x;
                            const dy = target.y - node.y;
                            const distance = Math.sqrt(dx * dx + dy * dy) || 1;
                            const attraction = 0.05;
                            fx += (dx / distance) * attraction;
                            fy += (dy / distance) * attraction;
                        }
                    } else if (link.target === node.id) {
                        const source = nodes.find(n => n.id === link.source);
                        if (source) {
                            const dx = source.x - node.x;
                            const dy = source.y - node.y;
                            const distance = Math.sqrt(dx * dx + dy * dy) || 1;
                            const attraction = 0.05;
                            fx += (dx / distance) * attraction;
                            fy += (dy / distance) * attraction;
                        }
                    }
                });

                // Update velocity and position
                node.vx = (node.vx || 0) * c + fx;
                node.vy = (node.vy || 0) * c + fy;
                node.x += node.vx;
                node.y += node.vy;
            });

            // Render
            ctx.fillStyle = '#f8fafc';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw links
            ctx.strokeStyle = '#cbd5e1';
            ctx.lineWidth = 1;
            graphLinks.forEach(link => {
                const source = graphNodes.get(link.source);
                const target = graphNodes.get(link.target);
                if (source && target) {
                    ctx.beginPath();
                    ctx.moveTo(source.x + canvas.width / 2, source.y + canvas.height / 2);
                    ctx.lineTo(target.x + canvas.width / 2, target.y + canvas.height / 2);
                    ctx.stroke();

                    // Draw relationship label
                    const midX = (source.x + target.x) / 2 + canvas.width / 2;
                    const midY = (source.y + target.y) / 2 + canvas.height / 2;
                    ctx.fillStyle = '#64748b';
                    ctx.font = '11px system-ui';
                    ctx.textAlign = 'center';
                    ctx.fillText(link.type, midX, midY - 5);
                }
            });

            // Draw nodes
            graphNodes.forEach((node) => {
                const x = node.x + canvas.width / 2;
                const y = node.y + canvas.height / 2;
                const radius = node.id === currentNode.node_id ? 25 : 20;
                const isHovered = hoveredNodeId === node.id;

                // Draw node circle
                ctx.fillStyle = node.isSelected ? '#3b82f6' : (isHovered ? '#60a5fa' : '#e2e8f0');
                ctx.beginPath();
                ctx.arc(x, y, radius, 0, Math.PI * 2);
                ctx.fill();

                // Draw node border
                ctx.strokeStyle = node.isSelected ? '#1e40af' : (isHovered ? '#1e3a8a' : '#94a3b8');
                ctx.lineWidth = node.isSelected ? 2 : 1;
                ctx.stroke();

                // Draw node label
                ctx.fillStyle = node.isSelected ? '#fff' : '#1e293b';
                ctx.font = 'bold 12px system-ui';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                const label = node.title.length > 10 ? node.title.substring(0, 10) + '...' : node.title;
                ctx.fillText(label, x, y);
            });

            animationRef.current = requestAnimationFrame(simulate);
        };

        simulate();

        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, [graphNodes, graphLinks, currentNode, hoveredNodeId]);

    // Handle canvas click
    const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const clickX = e.clientX - rect.left - canvas.width / 2;
        const clickY = e.clientY - rect.top - canvas.height / 2;

        // Find clicked node
        graphNodes.forEach((node) => {
            const dx = node.x - clickX;
            const dy = node.y - clickY;
            const distance = Math.sqrt(dx * dx + dy * dy);
            if (distance < 25 && node.id !== currentNode.node_id && !node.id.startsWith('pdf-')) {
                onNodeClick?.(node.id);
            }
        });
    };

    // Handle canvas hover
    const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left - canvas.width / 2;
        const mouseY = e.clientY - rect.top - canvas.height / 2;

        let found = false;
        graphNodes.forEach((node) => {
            const dx = node.x - mouseX;
            const dy = node.y - mouseY;
            const distance = Math.sqrt(dx * dx + dy * dy);
            if (distance < 25) {
                setHoveredNodeId(node.id);
                found = true;
            }
        });

        if (!found) {
            setHoveredNodeId(null);
        }

        canvas.style.cursor = found ? 'pointer' : 'default';
    };

    const handleCanvasLeave = () => {
        setHoveredNodeId(null);
    };

    return (
        <div className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col gap-4">
            <div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">Node Relationships</h3>
                <p className="text-sm text-slate-600">Interactive graph showing connected nodes</p>
            </div>
            <canvas
                ref={canvasRef}
                onClick={handleCanvasClick}
                onMouseMove={handleCanvasMouseMove}
                onMouseLeave={handleCanvasLeave}
                className="border border-slate-300 rounded-lg bg-slate-50 w-full"
                style={{ height: '400px', display: 'block' }}
            />
            <div className="text-xs text-slate-500 space-y-1">
                <p>🔵 Blue: Current node</p>
                <p>⚪ Gray: Related nodes (click to navigate)</p>
                <p>Drag nodes to explore relationships</p>
            </div>
        </div>
    );
};

export default NodeGraph;
