
import React, { useState } from 'react';
import { createNode } from '../services/curriculumService';
import { Node, NodeCreate, NodeType } from '../types';

interface CreateNodeModalProps {
    curriculumId: string;
    onClose: () => void;
    onNodeCreated: (newNode: Node) => void;
}

const NODE_TYPE_OPTIONS: NodeType[] = [
    'CHAPTER',
    'SECTION',
    'TOPIC',
    'CONTENT',
    'ASSESSMENT',
    'QUESTION',
    'PROJECT'
];

const CreateNodeModal: React.FC<CreateNodeModalProps> = ({ curriculumId, onClose, onNodeCreated }) => {
    const [title, setTitle] = useState('');
    const [nodeType, setNodeType] = useState<NodeType>('CONTENT');
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!title) {
            setError('Title is required.');
            return;
        }

        const newNodeData: NodeCreate = {
            title,
            node_type: nodeType  // [NEW] Include node type
        };
        const newNode = await createNode(curriculumId, newNodeData);
        onNodeCreated(newNode);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-xl bg-surface p-6 shadow-2xl">
                <form onSubmit={handleSubmit}>
                    <h2 className="text-2xl font-bold mb-4">Create New Node</h2>
                    {error && <p className="text-red-500 mb-4">{error}</p>}
                    <div className="flex flex-col gap-4">
                        <div>
                            <label htmlFor="title" className="block text-sm font-medium text-text-secondary mb-1">Title</label>
                            <input
                                id="title"
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                className="w-full rounded-lg border-border-light"
                                placeholder="e.g., Introduction to Derivatives"
                            />
                        </div>
                        {/* [NEW] Node Type Selector */}
                        <div>
                            <label htmlFor="nodeType" className="block text-sm font-medium text-text-secondary mb-1">Node Type</label>
                            <select
                                id="nodeType"
                                value={nodeType}
                                onChange={(e) => setNodeType(e.target.value as NodeType)}
                                className="w-full rounded-lg border-border-light"
                            >
                                {NODE_TYPE_OPTIONS.map((type) => (
                                    <option key={type} value={type}>
                                        {type.charAt(0) + type.slice(1).toLowerCase().replace(/_/g, ' ')}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <div className="mt-6 flex justify-end gap-4">
                        <button type="button" onClick={onClose} id="cancel-create-node" className="px-4 py-2 text-sm font-medium rounded-lg hover:bg-black/10">Cancel</button>
                        <button type="submit" id="submit-create-node" className="px-4 py-2 text-sm font-bold text-white bg-primary rounded-lg hover:bg-primary/90">Create</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CreateNodeModal;
