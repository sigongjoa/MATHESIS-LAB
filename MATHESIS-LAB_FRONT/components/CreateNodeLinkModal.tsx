import React, { useState, useEffect } from 'react';
import { createNodeLink } from '../services/nodeService';
import { fetchNodeDetails } from '../services/nodeService';
import { NodeLinkResponse, NodeLinkNodeCreate, Node } from '../types';

interface CreateNodeLinkModalProps {
    nodeId: string;
    curriculumId: string;
    availableNodes: Node[];
    onClose: () => void;
    onLinkCreated: (newLink: NodeLinkResponse) => void;
}

const LINK_RELATIONSHIP_OPTIONS = [
    'REFERENCE',
    'EXTENDS',
    'DEPENDS_ON',
    'PREREQUISITE',
    'SUPPLEMENT',
];

const CreateNodeLinkModal: React.FC<CreateNodeLinkModalProps> = ({
    nodeId,
    curriculumId,
    availableNodes,
    onClose,
    onLinkCreated,
}) => {
    const [linkedNodeId, setLinkedNodeId] = useState('');
    const [linkRelationship, setLinkRelationship] = useState('REFERENCE');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!linkedNodeId) {
            setError('Target Node is required.');
            return;
        }

        if (linkedNodeId === nodeId) {
            setError('Cannot link a node to itself.');
            return;
        }

        setIsLoading(true);
        try {
            const linkData: NodeLinkNodeCreate = {
                linked_node_id: linkedNodeId,
                link_relationship: linkRelationship,
            };
            const newLink = await createNodeLink(nodeId, linkData);
            onLinkCreated(newLink);
            onClose();
        } catch (err) {
            setError('Failed to create node link. Please try again.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    // Filter out the current node from available nodes
    const selectableNodes = availableNodes.filter((node) => node.node_id !== nodeId);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-xl bg-surface p-6 shadow-2xl">
                <form onSubmit={handleSubmit}>
                    <h2 className="text-2xl font-bold mb-4">Link to Another Node</h2>
                    {error && <p className="text-red-500 mb-4">{error}</p>}
                    <div className="flex flex-col gap-4">
                        <div>
                            <label htmlFor="linkedNodeId" className="block text-sm font-medium text-text-secondary mb-1">
                                Target Node
                            </label>
                            <select
                                id="linkedNodeId"
                                value={linkedNodeId}
                                onChange={(e) => setLinkedNodeId(e.target.value)}
                                className="w-full rounded-lg border border-border-light px-3 py-2"
                            >
                                <option value="">-- Select a Node --</option>
                                {selectableNodes.map((node) => (
                                    <option key={node.node_id} value={node.node_id}>
                                        {node.title}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label htmlFor="linkRelationship" className="block text-sm font-medium text-text-secondary mb-1">
                                Relationship Type
                            </label>
                            <select
                                id="linkRelationship"
                                value={linkRelationship}
                                onChange={(e) => setLinkRelationship(e.target.value)}
                                className="w-full rounded-lg border border-border-light px-3 py-2"
                            >
                                {LINK_RELATIONSHIP_OPTIONS.map((type) => (
                                    <option key={type} value={type}>
                                        {type}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <div className="flex gap-3 mt-6">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-4 py-2 rounded-lg bg-surface border border-border-light hover:bg-gray-100 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading || !linkedNodeId}
                            className="flex-1 px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary-dark transition-colors disabled:opacity-50"
                        >
                            {isLoading ? 'Creating...' : 'Create Link'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CreateNodeLinkModal;
