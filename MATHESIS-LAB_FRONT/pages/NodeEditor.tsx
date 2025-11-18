
import React, { useState, useEffect } from 'react';

import { Link, useParams, useNavigate } from 'react-router-dom';

import AIAssistant from '../components/AIAssistant';
import LinkManager from '../components/LinkManager';
import CreatePDFLinkModal from '../components/CreatePDFLinkModal';
import CreateNodeLinkModal from '../components/CreateNodeLinkModal';
import NodeGraph from '../components/NodeGraph';

import { Node, NodeLinkResponse, Curriculum } from '../types';

import { getCurriculum } from '../services/curriculumService';

import { fetchNodeDetails, deleteNodeLink, fetchNodeLinks } from '../services/nodeService'; // Import new nodeService functions



const LinkedResourceItem: React.FC<{

    link: NodeLinkResponse;

    onRemoveRequest: (link: NodeLinkResponse) => void;

}> = ({ link, onRemoveRequest }) => {

    const getResourceTitle = (link: NodeLinkResponse): string => {

        if (link.link_type === 'YOUTUBE' && link.youtube_video_id) {

            // In a real app, you'd fetch YouTube video details to get the title

            return `YouTube Video (ID: ${link.youtube_video_id})`;

        }

        if (link.link_type === 'ZOTERO' && link.zotero_key) {

            // In a real app, you'd fetch Zotero item details to get the title

            return `Zotero Item (ID: ${link.zotero_key})`;

        }

        return `Unknown Resource (${link.link_type})`;

    };



    const getResourceIcon = (link: NodeLinkResponse): string => {

        if (link.link_type === 'YOUTUBE') return 'smart_display';

        if (link.link_type === 'ZOTERO') return 'menu_book';

        return 'article';

    };



    return (

        <div className="flex items-center gap-3 p-3 bg-slate-100 rounded-lg">

            <span className="material-symbols-outlined text-slate-500">{getResourceIcon(link)}</span>

            <p className="text-sm font-medium text-slate-800 flex-1 truncate">{getResourceTitle(link)}</p>

            <button onClick={() => onRemoveRequest(link)} className="text-slate-500 hover:text-red-500">

                <span className="material-symbols-outlined text-xl">delete</span>

            </button>

        </div>

    );

};

const NodeEditor: React.FC = () => {
    const { curriculumId, nodeId } = useParams<{ curriculumId: string; nodeId: string }>();
    const navigate = useNavigate();
    const [node, setNode] = useState<Node | null>(null);
    const [parentCurriculum, setParentCurriculum] = useState<Curriculum | null>(null);
    const [content, setContent] = useState('');
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [resourceToRemove, setResourceToRemove] = useState<NodeLinkResponse | null>(null); // Use NodeLinkResponse
    const [showPDFModal, setShowPDFModal] = useState(false);
    const [showNodeLinkModal, setShowNodeLinkModal] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            if (!curriculumId || !nodeId) {
                setError("Curriculum ID or Node ID is missing.");
                setLoading(false);
                return;
            }
            try {
                // Fetch node details using the new nodeService
                const nodeData = await fetchNodeDetails(nodeId);
                // Fetch curriculum details using curriculumService
                const curriculumData = await getCurriculum(curriculumId);
                
                setNode(nodeData);
                setParentCurriculum(curriculumData);
                setContent(nodeData.content?.markdown_content || '');
            } catch (err) {
                setError("Failed to load data.");
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [curriculumId, nodeId]);

    const handleConfirmRemove = async () => {
        if (node && resourceToRemove) {
            try {
                await deleteNodeLink(node.node_id, resourceToRemove.link_id);
                // Update the node state to remove the deleted link
                setNode(prevNode => {
                    if (!prevNode) return null;
                    return {
                        ...prevNode,
                        links: prevNode.links?.filter(link => link.link_id !== resourceToRemove.link_id) || [],
                    };
                });
                setResourceToRemove(null); // Close the modal
            } catch (err) {
                setError("Failed to delete node link.");
                console.error(err);
            }
        }
    };

    const handleLinkCreated = (newLink: NodeLinkResponse) => {
        setNode(prevNode => {
            if (!prevNode) return null;
            return {
                ...prevNode,
                links: [...(prevNode.links || []), newLink],
            };
        });
    };

    if (loading) {
        return <div>Loading data...</div>;
    }

    if (error) {
        return <div>Error: {error}</div>;
    }

    if (!node || !parentCurriculum) {
        return <div>Data not found</div>;
    }

    // Use node.links directly from the fetched node data
    const linkedResources = node.links || [];
    
    // The "Add a New Resource" section will be commented out for now
    // as it requires implementing resource search and creation, which is
    // beyond the current scope of implementing link deletion.
    // const availableResources = MOCK_RESOURCES.filter(mockRes => 
    //     !linkedResources.some(linkedRes => linkedRes.id === mockRes.id)
    // );

    return (
        <div className="relative flex h-auto min-h-screen w-full flex-col bg-slate-50">
             <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-slate-200 px-6 lg:px-10 py-3 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
                <div className="flex items-center gap-4">
                    <div className="size-6 text-primary">
                        <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                            <path d="M44 11.2727C44 14.0109 39.8386 16.3957 33.69 17.6364C39.8386 18.877 44 21.2618 44 24C44 26.7382 39.8386 29.123 33.69 30.3636C39.8386 31.6043 44 33.9891 44 36.7273C44 40.7439 35.0457 44 24 44C12.9543 44 4 40.7439 4 36.7273C4 33.9891 8.16144 31.6043 14.31 30.3636C8.16144 29.123 4 26.7382 4 24C4 21.2618 8.16144 18.877 14.31 17.6364C8.16144 16.3957 4 14.0109 4 11.2727C4 7.25611 12.9543 4 24 4C35.0457 4 44 7.25611 44 11.2727Z" fill="currentColor"></path>
                        </svg>
                    </div>
                    <h2 className="text-slate-900 text-lg font-bold leading-tight tracking-[-0.015em]">MATHESIS LAB</h2>
                </div>
                 <div className="flex items-center gap-2">
                    <button className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em]">
                    <span className="truncate">Publish</span>
                    </button>
                    <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10" style={{ backgroundImage: `url("https://picsum.photos/seed/user1/40/40")`}}></div>
                </div>
            </header>
            <main className="px-4 lg:px-10 py-8 flex-1">
                <div className="layout-content-container flex flex-col max-w-7xl mx-auto flex-1 gap-6">
                    <div className="flex flex-col gap-2">
                        <div className="flex flex-wrap gap-2 text-sm font-medium leading-normal">
                            <Link to={`/curriculum/${parentCurriculum.curriculum_id}`} className="text-slate-500 hover:underline">{parentCurriculum.title}</Link>
                            <span className="text-slate-500">/</span>
                            <span className="text-slate-800">{node.title}</span>
                        </div>
                        <h1 className="text-slate-900 text-4xl font-black leading-tight tracking-[-0.033em]">{node.title}</h1>
                    </div>
                    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 items-start">
                        <div className="lg:col-span-2 flex flex-col gap-6">
                            <div className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col gap-4">
                                <label className="flex flex-col min-w-40 flex-1">
                                    <p className="text-slate-800 text-base font-medium leading-normal pb-2">Node Content (Markdown)</p>
                                    <textarea
                                        value={content}
                                        onChange={(e) => setContent(e.target.value)}
                                        className="form-input flex w-full min-w-0 flex-1 resize-y overflow-hidden rounded-lg text-slate-900 focus:outline-0 focus:ring-2 focus:ring-primary/50 border border-slate-300 bg-slate-50 focus:border-primary min-h-96 placeholder:text-slate-400 p-[15px] text-base font-normal leading-normal"
                                        placeholder="Start writing your content using Markdown..."
                                    ></textarea>
                                </label>
                                <div className="flex justify-start">
                                    <button className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em]">
                                        <span className="truncate">Save Changes</span>
                                    </button>
                                </div>
                            </div>
                            <AIAssistant content={content} onUpdateContent={setContent} nodeId={node.node_id} />
                        </div>
                        <div className="lg:col-span-2 flex flex-col gap-6 sticky top-28">
                            <div className="bg-white rounded-xl border border-slate-200 p-6">
                                <LinkManager
                                    links={linkedResources}
                                    onDeleteRequest={setResourceToRemove}
                                    onAddPDFClick={() => setShowPDFModal(true)}
                                    onAddNodeLinkClick={() => setShowNodeLinkModal(true)}
                                />
                            </div>
                            {/* Always render NodeGraph - debug why it's not showing */}
                            {node && parentCurriculum && (
                                <NodeGraph
                                    currentNode={node}
                                    allNodes={parentCurriculum.nodes}
                                    onNodeClick={(nodeId) => {
                                        navigate(`/curriculum/${curriculumId}/node/${nodeId}`);
                                    }}
                                />
                            )}
                        </div>
                    </div>
                </div>
            </main>

            {/* Delete Confirmation Modal */}
            {resourceToRemove && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl">
                        <h2 className="text-xl font-bold mb-4 text-gray-900">Delete Link</h2>
                        <p className="mb-6 text-gray-700">Are you sure you want to delete this link? This action cannot be undone.</p>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setResourceToRemove(null)}
                                className="flex-1 px-4 py-2 rounded-lg bg-gray-200 text-gray-900 hover:bg-gray-300 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleConfirmRemove}
                                className="flex-1 px-4 py-2 rounded-lg bg-red-500 text-white hover:bg-red-600 transition-colors"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* PDF Link Modal */}
            {showPDFModal && node && (
                <CreatePDFLinkModal
                    nodeId={node.node_id}
                    onClose={() => setShowPDFModal(false)}
                    onLinkCreated={handleLinkCreated}
                />
            )}

            {/* Node-to-Node Link Modal */}
            {showNodeLinkModal && node && parentCurriculum && (
                <CreateNodeLinkModal
                    nodeId={node.node_id}
                    curriculumId={parentCurriculum.curriculum_id}
                    availableNodes={parentCurriculum.nodes}
                    onClose={() => setShowNodeLinkModal(false)}
                    onLinkCreated={handleLinkCreated}
                />
            )}
        </div>
    );
};

export default NodeEditor;
