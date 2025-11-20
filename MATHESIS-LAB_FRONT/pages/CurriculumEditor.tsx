
import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getCurriculum } from '../services/curriculumService';
import { Curriculum, Node } from '../types';
import CreateNodeModal from '../components/CreateNodeModal';

const CurriculumEditor: React.FC = () => {
    const { curriculumId } = useParams<{ curriculumId: string }>();
    const [curriculum, setCurriculum] = useState<Curriculum | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [isCreateNodeModalOpen, setCreateNodeModalOpen] = useState<boolean>(false);

    useEffect(() => {
        const fetchCurriculum = async () => {
            if (!curriculumId) {
                setError("Curriculum ID is missing.");
                setLoading(false);
                return;
            }
            const data = await getCurriculum(curriculumId);
            setCurriculum(data);
            setLoading(false);
        };

        fetchCurriculum();
    }, [curriculumId]);

    const handleNodeCreated = (newNode: Node) => {
        if (curriculum) {
            setCurriculum({
                ...curriculum,
                nodes: [...curriculum.nodes, newNode],
            });
        }
    };

    if (loading) {
        return <div>Loading curriculum...</div>;
    }

    if (error) {
        return <div>Error: {error}</div>;
    }

    if (!curriculum) {
        return <div>Curriculum not found</div>;
    }

    return (
        <div className="flex h-screen w-full flex-col bg-white text-[#111827]">
            <header className="flex items-center justify-between whitespace-nowrap border-b border-gray-200 bg-white px-6 py-3 shrink-0">
                <div className="flex items-center gap-4 text-gray-800">
                    <div className="size-6 text-primary">
                        <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                            <path d="M44 11.2727C44 14.0109 39.8386 16.3957 33.69 17.6364C39.8386 18.877 44 21.2618 44 24C44 26.7382 39.8386 29.123 33.69 30.3636C39.8386 31.6043 44 33.9891 44 36.7273C44 40.7439 35.0457 44 24 44C12.9543 44 4 40.7439 4 36.7273C4 33.9891 8.16144 31.6043 14.31 30.3636C8.16144 29.123 4 26.7382 4 24C4 21.2618 8.16144 18.877 14.31 17.6364C8.16144 16.3957 4 14.0109 4 11.2727C4 7.25611 12.9543 4 24 4C35.0457 4 44 7.25611 44 11.2727Z" fill="currentColor"></path>
                        </svg>
                    </div>
                    <h2 className="text-lg font-bold leading-tight tracking-[-0.015em]">MATHESIS LAB</h2>
                </div>
                <div className="flex flex-1 justify-end items-center gap-8">
                    <div className="flex items-center gap-2">
                        <button className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-gray-100 text-gray-800 text-sm font-bold leading-normal tracking-[0.015em]">
                            <span className="truncate">Save</span>
                        </button>
                        <button className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em]">
                            <span className="truncate">Publish</span>
                        </button>
                    </div>
                    <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10" style={{ backgroundImage: `url("https://picsum.photos/seed/user/40/40")` }}></div>
                </div>
            </header>
            <div className="flex flex-1 overflow-hidden">
                <nav className="flex h-full flex-col justify-between bg-white border-r border-gray-200 p-4 w-64 shrink-0">
                    <div className="flex flex-col gap-2 pt-4">
                         <Link to="/" className="flex items-center gap-3 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">
                            <span className="material-symbols-outlined">arrow_back</span>
                            <p className="text-sm font-medium leading-normal">My Curriculums</p>
                        </Link>
                        <a className="flex items-center gap-3 px-3 py-2 rounded-lg bg-primary/10 text-primary" href="#">
                            <span className="material-symbols-outlined">account_tree</span>
                            <p className="text-sm font-medium leading-normal">Curriculum</p>
                        </a>
                    </div>
                </nav>
                <main className="flex flex-1 overflow-hidden">
                    <div className="flex flex-col flex-1">
                        <div className="flex items-center justify-between gap-4 p-4 border-b border-gray-200 bg-white shrink-0">
                            <div className="flex min-w-72 flex-col gap-1">
                                <p className="text-gray-900 text-2xl font-bold leading-tight tracking-[-0.033em]">{curriculum.title}</p>
                                <p className="text-gray-500 text-sm font-normal leading-normal">{curriculum.description}</p>
                            </div>
                        </div>
                        <div className="flex-1 p-6 bg-background-light overflow-auto relative">
                             <div className="flex flex-col gap-4">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-lg font-bold">Nodes</h3>
                                    <button 
                                        onClick={() => setCreateNodeModalOpen(true)}
                                        className="flex cursor-pointer items-center justify-center overflow-hidden rounded-lg h-8 px-3 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em] gap-2">
                                        <span className="material-symbols-outlined text-sm">add</span>
                                        <span className="truncate">Add Node</span>
                                    </button>
                                </div>
                                {curriculum.nodes && curriculum.nodes.length > 0 ? (
                                    curriculum.nodes.map(node => (
                                        <Link key={node.node_id} to={`/curriculum/${curriculum.curriculum_id}/node/${node.node_id}`} className="block p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
                                            <p className="font-semibold text-primary">{node.title}</p>
                                            <p className="text-sm text-gray-600 line-clamp-2 mt-1">{node.content?.markdown_content?.substring(0, 150)}...</p>
                                        </Link>
                                    ))
                                ) : (
                                    <div className="flex flex-col items-center gap-6 rounded-xl border-2 border-dashed border-gray-300 px-6 py-14">
                                        <div className="flex max-w-[480px] flex-col items-center gap-2">
                                            <p className="text-gray-900 text-lg font-bold leading-tight tracking-[-0.015em] text-center">Curriculum Map is Empty</p>
                                            <p className="text-gray-500 text-sm font-normal leading-normal text-center">Start by adding a node to build your curriculum.</p>
                                        </div>
                                        <button 
                                            onClick={() => setCreateNodeModalOpen(true)}
                                            className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 bg-gray-200 text-gray-800 text-sm font-bold leading-normal tracking-[0.015em] gap-2">
                                            <span className="material-symbols-outlined text-base">add</span>
                                            <span className="truncate">Add Node</span>
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                    <aside className="w-96 shrink-0 border-l border-gray-200 bg-white flex flex-col">
                        <div className="p-6 border-b border-gray-200">
                            <h3 className="text-lg font-bold text-gray-900">Properties</h3>
                        </div>
                        <div className="flex-1 p-6 space-y-6 overflow-y-auto">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="curriculum-title">Curriculum Title</label>
                                <input className="w-full rounded-md border-gray-300 bg-gray-100 text-gray-900 focus:ring-primary focus:border-primary" id="curriculum-title" type="text" defaultValue={curriculum.title} />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="curriculum-description">Description</label>
                                <textarea className="w-full rounded-md border-gray-300 bg-gray-100 text-gray-900 focus:ring-primary focus:border-primary" id="curriculum-description" rows={3} defaultValue={curriculum.description}></textarea>
                            </div>
                        </div>
                    </aside>
                </main>
            </div>
            {isCreateNodeModalOpen && (
                <CreateNodeModal
                    curriculumId={curriculum.curriculum_id!}
                    onClose={() => setCreateNodeModalOpen(false)}
                    onNodeCreated={handleNodeCreated}
                />
            )}
        </div>
    );
};

export default CurriculumEditor;
