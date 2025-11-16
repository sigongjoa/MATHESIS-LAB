
import React, { useState, useEffect } from 'react';

import { Link, useParams } from 'react-router-dom';

import AIAssistant from '../components/AIAssistant';

import { Node, NodeLinkResponse, Curriculum } from '../types';

import { getCurriculum } from '../services/curriculumService';

import { fetchNodeDetails, deleteNodeLink } from '../services/nodeService'; // Import new nodeService functions



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
    const [node, setNode] = useState<Node | null>(null);
    const [parentCurriculum, setParentCurriculum] = useState<Curriculum | null>(null);
    const [content, setContent] = useState('');
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [resourceToRemove, setResourceToRemove] = useState<NodeLinkResponse | null>(null); // Use NodeLinkResponse

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
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
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
                        <div className="lg:col-span-1 flex flex-col gap-6 sticky top-28">
                             <div className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col gap-4">
                                <h3 className="text-slate-900 text-lg font-bold">Linked Resources</h3>
                                <div className="flex flex-col gap-1 max-h-64 overflow-y-auto pr-2">
                                    {linkedResources.length > 0 ? linkedResources.map(link => (
                                        <LinkedResourceItem key={link.link_id} link={link} onRemoveRequest={setResourceToRemove} />
                                    )) : <p className="text-sm text-slate-500 text-center py-4">No linked resources.</p>}
                                </div>
                            </div>
                            {/* The "Add a New Resource" section is commented out for now */}
                            {/*
                            <div className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col gap-4">
                                <h3 className="text-slate-900 text-lg font-bold">Add a New Resource</h3>
                                <div className="relative">
                                    <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">search</span>
                                    <input className="form-input w-full rounded-lg text-slate-900 focus:outline-0 focus:ring-2 focus:ring-primary/50 border border-slate-300 bg-slate-50 focus:border-primary placeholder:text-slate-400 pl-10 pr-4 py-2 text-sm" placeholder="Search available resources..." type="text"/>
                                </div>
                                <div className="flex flex-col gap-2 max-h-60 overflow-y-auto pr-2">
                                    {availableResources.map(res => (
                                        <div key={res.id} className="flex items-center gap-3 p-3 hover:bg-slate-100 rounded-lg">
                                            <span className="material-symbols-outlined text-slate-500">{res.type === 'book' ? 'menu_book' : res.type === 'video' ? 'smart_display' : 'article'}</span>
                                            <p className="text-sm font-medium text-slate-800 flex-1 truncate">{res.title}</p>
                                            <button className="flex-shrink-0 flex items-center justify-center h-8 px-3 bg-primary/10 text-primary text-xs font-bold rounded-md hover:bg-primary/20">Add</button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            */}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default NodeEditor;
