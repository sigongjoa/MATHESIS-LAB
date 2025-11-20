import React, { useState } from 'react';
import { createPDFLink } from '../services/nodeService';
import { NodeLinkResponse, NodeLinkPDFCreate } from '../types';

interface CreatePDFLinkModalProps {
    nodeId: string;
    onClose: () => void;
    onLinkCreated: (newLink: NodeLinkResponse) => void;
}

const CreatePDFLinkModal: React.FC<CreatePDFLinkModalProps> = ({ nodeId, onClose, onLinkCreated }) => {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setSelectedFile(e.target.files[0]);
            setError(null);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!selectedFile) {
            setError('Please select a PDF file.');
            return;
        }

        setIsLoading(true);
        try {
            const newLink = await createPDFLink(nodeId, selectedFile);
            onLinkCreated(newLink);
            onClose();
        } catch (err) {
            console.error(err);
            setError('Failed to upload PDF file.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-xl bg-surface p-6 shadow-2xl">
                <form onSubmit={handleSubmit}>
                    <h2 className="text-2xl font-bold mb-4">Upload PDF File</h2>
                    {error && <p className="text-red-500 mb-4">{error}</p>}
                    <div className="flex flex-col gap-4">
                        <div>
                            <label htmlFor="pdfFile" className="block text-sm font-medium text-text-secondary mb-1">
                                Select PDF
                            </label>
                            <input
                                id="pdfFile"
                                type="file"
                                accept=".pdf"
                                onChange={handleFileChange}
                                className="w-full rounded-lg border border-border-light px-3 py-2 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                            />
                        </div>
                        {selectedFile && (
                            <div className="text-sm text-gray-600">
                                <p>Selected: {selectedFile.name}</p>
                                <p>Size: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                            </div>
                        )}
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
                            disabled={!selectedFile || isLoading}
                            className="flex-1 px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary-dark transition-colors disabled:opacity-50"
                        >
                            {isLoading ? 'Uploading...' : 'Upload'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CreatePDFLinkModal;
