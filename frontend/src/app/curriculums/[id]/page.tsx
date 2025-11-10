"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
} from "reactflow";
import "reactflow/dist/style.css";

import * as api from "@/lib/api";
console.log("API module in page.tsx:", api);

// Conditionally import Link for testing purposes
const Link = process.env.NODE_ENV === 'test' ? (props: any) => <a {...props} /> : require('next/link').default;

// Define types for curriculum and node data
interface CurriculumData {
  curriculum_id: string;
  title: string;
  description: string;
}

interface NodeData {
  node_id: string;
  title: string;
  description?: string; // Assuming description might be part of node content
  parent_node_id?: string | null;
  order_index: number;
}

// Custom Node Component (simple for now)
const CustomNode = ({ data }: { data: NodeData }) => {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white border-2 border-stone-400">
      <div className="flex">
        <div className="text-lg font-bold">{data.title}</div>
      </div>
      <div className="text-sm text-stone-500">{data.description}</div>
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

export default function CurriculumDetailPage() {
  const params = useParams();
  const curriculumId = params.id as string;

  const [curriculum, setCurriculum] = useState<CurriculumData | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const handleAddNode = useCallback(async () => {
    console.log("handleAddNode called!");
    try {
      const newNodePayload = {
        title: "New Node",
        description: "",
        parent_node_id: null,
        order_index: nodes.length, // Simple order for now
      };
      const createdNode = await api.createNode(curriculumId, newNodePayload); // Use api.createNode
      console.log("api.createNode call completed!");
      const reactFlowNode: Node = {
        id: createdNode.node_id,
        position: { x: Math.random() * 250, y: Math.random() * 250 }, // Random position for new node
        data: { ...createdNode },
        type: "custom",
      };
      setNodes((nds) => nds.concat(reactFlowNode));
    } catch (err: any) {
      console.error("Error in handleAddNode:", err); // Log the error
      setError(err.message);
    }
  }, [curriculumId, nodes, setNodes]);

  useEffect(() => {
    async function fetchCurriculumData() {
      try {
        setLoading(true);
        const data = await getCurriculumWithNodes(curriculumId);
        setCurriculum(data.curriculum);

        const reactFlowNodes: Node[] = data.nodes.map((node: NodeData, index: number) => ({
          id: node.node_id,
          position: { x: index * 200, y: node.parent_node_id ? 150 : 50 }, // Simple positioning for now
          data: { ...node },
          type: "custom",
        }));

        const reactFlowEdges: Edge[] = data.nodes
          .filter((node: NodeData) => node.parent_node_id)
          .map((node: NodeData) => ({
            id: `e-${node.parent_node_id}-${node.node_id}`,
            source: node.parent_node_id!,
            target: node.node_id,
            animated: true,
          }));

        setNodes(reactFlowNodes);
        setEdges(reactFlowEdges);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    if (curriculumId) {
      fetchCurriculumData();
    }
  }, [curriculumId, setNodes, setEdges]);

  const onNodeDragStop = useCallback(
    async (event: React.MouseEvent, node: Node) => {
      // This is a simplified reordering logic.
      // A real implementation would need to calculate new parent and order_index
      // based on drop target or relative positions.
      // For now, we'll just log and potentially update its own position.
      console.log("Node dragged:", node.id, node.position);

      // Example: If we wanted to update position in DB, we'd call an API here.
      // For reordering, we need more context (where it was dropped relative to other nodes).
      // This part will be implemented more fully later.
      // await reorderNode(curriculumId, node.id, node.data.parent_node_id, new_order_index);
    },
    [curriculumId]
  );

  if (loading) {
    return <div className="p-8">Loading curriculum map...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-500">Error: {error}</div>;
  }

  if (!curriculum) {
    return <div className="p-8">Curriculum not found.</div>;
  }

  return (
    <div className="flex h-screen w-full">
      {/* Left Sidebar */}
      <aside className="flex h-full w-72 flex-col border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-[#181f2b] p-4">
        <div className="flex items-center gap-3 mb-6">
          <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10" data-alt="EduGraph logo" style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBD0Q1A_sDoRR6eKt4oWWYO23iRM4tVMi_t6lyVOk4TCgogIBVgRsJOpgxlGAV1MFkxQqBXfcm7IPPWMkCff5EWt7bZEJ84YgvJkMvH-W3ATgmXjdPM4VuE35dcx1EPwFQatJxyKIj_hvf7HfmV8kv4t3XaOW4X84LLVbqO72g34ThFtc2UO_2pnfLvGVdhigCN9sF7cEy0tXoHJ9U9_Lf5UjNPfkmnVguHUGQhjgR0BEc5Vu-zCQQ0X79JMY39f9hW0L36gYfiPTg0")' }}></div>
          <div className="flex flex-col">
            <h1 className="text-[#0d121b] dark:text-white text-base font-medium leading-normal">EduGraph</h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm font-normal leading-normal">Curriculum Builder</p>
          </div>
        </div>
        <nav className="flex flex-col gap-2 mb-6">
          <Link className="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700" href="/">
            <span className="material-symbols-outlined text-2xl">dashboard</span>
            <p className="text-sm font-medium">Dashboard</p>
          </Link>
          <Link className="flex items-center gap-3 px-3 py-2 rounded-lg bg-primary/10 dark:bg-primary/20 text-primary dark:text-primary-300" href="/curriculums">
            <span className="material-symbols-outlined text-2xl">schema</span>
            <p className="text-sm font-medium">Curriculums</p>
          </Link>
        </nav>
        <div className="flex flex-col flex-grow">
          <p className="px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Graph Tools</p>
          <div className="flex flex-col gap-2 mt-2">
            <button className="flex w-full cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em] gap-2"
              onClick={handleAddNode}
            >
              <span className="material-symbols-outlined text-xl">add_circle</span>
              <span className="truncate">Add Node</span>
            </button>
            <button className="flex w-full cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-sm font-bold leading-normal tracking-[0.015em] gap-2">
              <span className="material-symbols-outlined text-xl">ios_share</span>
              <span className="truncate">Export Graph</span>
            </button>
          </div>
          <div className="mt-4 flex flex-col flex-grow">
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-xl">search</span>
              <input className="w-full h-10 pl-10 pr-4 rounded-lg border border-gray-300 dark:border-gray-600 bg-background-light dark:bg-background-dark focus:ring-primary focus:border-primary" placeholder="Find a node..." type="text"/>
            </div>
            <ul className="mt-2 space-y-1 overflow-y-auto flex-grow">
              {/* Node list for quick navigation/selection */}
              {nodes.map((node) => (
                <li key={node.id}>
                  <a className="block px-3 py-2 text-sm rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" href={`#${node.id}`}>
                    {node.data.title}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-200 dark:border-gray-800 pt-4 mt-4 flex flex-col gap-1">
          <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700" href="#">
            <span className="material-symbols-outlined text-2xl">settings</span>
            <p className="text-sm font-medium">Settings</p>
          </a>
          <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700" href="#">
            <span className="material-symbols-outlined text-2xl">help</span>
            <p className="text-sm font-medium">Help</p>
          </a>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Page Header */}
        <header className="flex flex-wrap justify-between items-center gap-3 p-6 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-[#181f2b]">
          <div className="flex min-w-72 flex-col gap-1">
            <p className="text-[#0d121b] dark:text-white text-2xl font-bold tracking-tight">{curriculum.title}</p>
            <p className="text-gray-500 dark:text-gray-400 text-sm font-normal leading-normal">{curriculum.description}</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex -space-x-2">
              {/* Placeholder for user avatars */}
              <img className="inline-block h-10 w-10 rounded-full ring-2 ring-white dark:ring-gray-800" data-alt="User avatar" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAmo1qbmJwQJFkAcZs2QKG6zfx1FWuzl-7JiG5mZO30th2cZYEtIXBNkqQknqOUyPWrY6wOp2WwXAOTlOStYp6Wif1hXsaoub6v8IFoM_LERxIme9WHANPXFxYs7V3oVNiZt4aTHoystSSV1ommDOKBbqAuFl0mzU1R4-jt3rmj2eNB5vIGhOci0wXtJ1RDoEc_ZujiOofPRvNG1EOhHZtom4jFj6J_8ggrozXQ8CgeKaxatcrKm6C84g5235flqKEtJbA9gyuizvur"/>
              <img className="inline-block h-10 w-10 rounded-full ring-2 ring-white dark:ring-gray-800" data-alt="User avatar" src="https://lh3.googleusercontent.com/aida-public/AB6AXuB9IyGS4o_wqmP7NTYCws4nRUNvPREgqxqleyDdUT3MLn7o73pwGH24yrbNUo3NrM3lduAn1-x4QNEEpYJ3Dsaz-2GKQKM8GL7u8zqJQ6wm2CMuAtp6CXnGRTCi9UWBCj5f_Ww7rYuo-dgnhfCujOKS5YKSoq7GI4No_kOgUtQlx2-_0cFed_tXGkMN2Z6bt40hbrbTnbeGImizCAvT25ibk8gfyyMz7Cro86P3xwe1NeFmUaabA5uO4Gj0eTbe10B3g5x8lv-F1yuX"/>
              <img className="inline-block h-10 w-10 rounded-full ring-2 ring-white dark:ring-gray-800" data-alt="User avatar" src="https://lh3.googleusercontent.com/aida-public/AB6AXuC1J4a7fiD_kA2CHlD1EM5NXhl9Fyrpv84l4UMy0AA1SfOosxTWg3mgtU2pzLTT4BYobwEqr2GdmMhnlPMWWg9tC8a2vOmtbxGoXBf2LDlJNNcw09hh_5VxnYTu6cpYVXoHxSmqBl8V4u6a0GOHnFCUEAnZszPGvsFPPRubrz2z4xn8V7SvdzPLrE3EEJ5Xp1Og6xN8_d5Q9u3mZOeXiOHzMPWyGvocvbsp5bhHpxnWTkj9VJMPwa_7rqDYM3JTn2fBXH-UV_sXym2t"/>
            </div>
            <button className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em] gap-2">
              <span className="material-symbols-outlined text-xl">share</span>
              <span className="truncate">Share</span>
            </button>
          </div>
        </header>

        {/* Canvas */}
        <div className="flex-1 relative">
          {/* Toolbar */}
          <div className="absolute top-4 left-4 flex gap-2 bg-white dark:bg-[#181f2b] p-2 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 z-10">
            <button className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
              <span className="material-symbols-outlined">zoom_in</span>
            </button>
            <button className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
              <span className="material-symbols-outlined">zoom_out</span>
            </button>
            <button className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
              <span className="material-symbols-outlined">zoom_out_map</span>
            </button>
          </div>
          {/* Graph Area */}
          <div className="w-full h-full">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeDragStop={onNodeDragStop}
              nodeTypes={nodeTypes}
              fitView
            >
              <MiniMap />
              <Controls />
              <Background variant="dots" gap={12} size={1} />
            </ReactFlow>
          </div>
        </div>
      </main>

      {/* Right Sidebar (Properties Panel) */}
      <aside className="flex h-full w-80 flex-col border-l border-gray-200 dark:border-gray-800 bg-white dark:bg-[#181f2b] p-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-base font-bold text-gray-800 dark:text-white">Node Properties</h2>
          <button className="p-1 rounded-full text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700">
            <span className="material-symbols-outlined text-xl">close</span>
          </button>
        </div>
        <div className="flex flex-col gap-4 flex-grow">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" htmlFor="node-title">Title</label>
            <input className="w-full h-10 px-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-background-light dark:bg-background-dark focus:ring-primary focus:border-primary" id="node-title" type="text" value="Linear Equations"/>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" htmlFor="node-description">Description</label>
            <textarea className="w-full p-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-background-light dark:bg-background-dark focus:ring-primary focus:border-primary" id="node-description" rows={6}>An equation between two variables that gives a straight line when plotted on a graph.</textarea>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="flex-1 flex min-w-0 max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-sm font-bold leading-normal tracking-[0.015em] gap-2">
            <span className="material-symbols-outlined text-xl text-red-500">delete</span>
            <span className="truncate">Delete</span>
          </button>
          <button className="flex-1 flex min-w-0 max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em] gap-2">
            <span className="material-symbols-outlined text-xl">save</span>
            <span className="truncate">Save Changes</span>
          </button>
        </div>
      </aside>
    </div>
  );
}
