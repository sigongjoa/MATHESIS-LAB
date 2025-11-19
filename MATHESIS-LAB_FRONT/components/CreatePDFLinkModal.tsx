import React, { useState } from 'react';
import { createPDFLink } from '../services/nodeService';
import { NodeLinkResponse, NodeLinkPDFCreate } from '../types';

interface CreatePDFLinkModalProps {
    nodeId: string;
    onClose: () => void;
    onLinkCreated: (newLink: NodeLinkResponse) => void;
}

const CreatePDFLinkModal: React.FC<CreatePDFLinkModalProps> = ({ nodeId, onClose, onLinkCreated }) => {
    const [driveFileId, setDriveFileId] = useState('');
    const [fileName, setFileName] = useState('');
    const [fileSizeBytes, setFileSizeBytes] = useState<number | undefined>(undefined);
    const [fileMimeType, setFileMimeType] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!driveFileId || !fileName) {
            setError('Drive File ID and File Name are required.');
            return;
        }

        setIsLoading(true);
        const linkData: NodeLinkPDFCreate = {
            drive_file_id: driveFileId,
            file_name: fileName,
            file_size_bytes: fileSizeBytes,
            file_mime_type: fileMimeType || undefined,
        };
        const newLink = await createPDFLink(nodeId, linkData);
        onLinkCreated(newLink);
        onClose();
        setIsLoading(false);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-xl bg-surface p-6 shadow-2xl">
                <form onSubmit={handleSubmit}>
                    <h2 className="text-2xl font-bold mb-4">Link PDF File</h2>
                    {error && <p className="text-red-500 mb-4">{error}</p>}
                    <div className="flex flex-col gap-4">
                        <div>
                            <label htmlFor="driveFileId" className="block text-sm font-medium text-text-secondary mb-1">
                                Google Drive File ID
                            </label>
                            <input
                                id="driveFileId"
                                type="text"
                                value={driveFileId}
                                onChange={(e) => setDriveFileId(e.target.value)}
                                className="w-full rounded-lg border border-border-light px-3 py-2"
                                placeholder="e.g., 1BwxN3u7KxxXX-XXXXXXXXXXXX"
                            />
                        </div>
                        <div>
                            <label htmlFor="fileName" className="block text-sm font-medium text-text-secondary mb-1">
                                File Name
                            </label>
                            <input
                                id="fileName"
                                type="text"
                                value={fileName}
                                onChange={(e) => setFileName(e.target.value)}
                                className="w-full rounded-lg border border-border-light px-3 py-2"
                                placeholder="e.g., lecture-notes.pdf"
                            />
                        </div>
                        <div>
                            <label htmlFor="fileSizeBytes" className="block text-sm font-medium text-text-secondary mb-1">
                                File Size (bytes) - Optional
                            </label>
                            <input
                                id="fileSizeBytes"
                                type="number"
                                value={fileSizeBytes || ''}
                                onChange={(e) => setFileSizeBytes(e.target.value ? Number(e.target.value) : undefined)}
                                className="w-full rounded-lg border border-border-light px-3 py-2"
                                placeholder="e.g., 2048576"
                            />
                        </div>
                        <div>
                            <label htmlFor="fileMimeType" className="block text-sm font-medium text-text-secondary mb-1">
                                MIME Type - Optional
                            </label>
                            <input
                                id="fileMimeType"
                                type="text"
                                value={fileMimeType}
                                onChange={(e) => setFileMimeType(e.target.value)}
                                className="w-full rounded-lg border border-border-light px-3 py-2"
                                placeholder="e.g., application/pdf"
                            />
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
                            disabled={isLoading}
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

export default CreatePDFLinkModal;
