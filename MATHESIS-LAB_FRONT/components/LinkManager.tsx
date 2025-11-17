import React, { useState } from 'react';
import { NodeLinkResponse } from '../types';

interface LinkManagerProps {
    links: NodeLinkResponse[];
    onDeleteRequest: (link: NodeLinkResponse) => void;
    onAddPDFClick: () => void;
    onAddNodeLinkClick: () => void;
}

const LinkManager: React.FC<LinkManagerProps> = ({
    links,
    onDeleteRequest,
    onAddPDFClick,
    onAddNodeLinkClick,
}) => {
    const getLinkDisplayInfo = (link: NodeLinkResponse) => {
        switch (link.link_type) {
            case 'YOUTUBE':
                return {
                    icon: 'smart_display',
                    title: `YouTube: ${link.youtube_video_id || 'Unknown'}`,
                    description: 'Video Resource',
                };
            case 'ZOTERO':
                return {
                    icon: 'menu_book',
                    title: `Zotero: ${link.zotero_key || 'Unknown'}`,
                    description: 'Literature Reference',
                };
            case 'DRIVE_PDF':
                return {
                    icon: 'picture_as_pdf',
                    title: link.file_name || `PDF: ${link.drive_file_id}`,
                    description: `${link.file_size_bytes ? `${(link.file_size_bytes / 1024 / 1024).toFixed(2)} MB` : 'PDF File'}`,
                };
            case 'NODE':
                return {
                    icon: 'link',
                    title: `Linked Node (${link.link_relationship || 'REFERENCE'})`,
                    description: `ID: ${link.linked_node_id || 'Unknown'}`,
                };
            default:
                return {
                    icon: 'article',
                    title: `Unknown: ${link.link_type}`,
                    description: 'Resource',
                };
        }
    };

    const pdfLinks = links.filter((link) => link.link_type === 'DRIVE_PDF');
    const nodeLinks = links.filter((link) => link.link_type === 'NODE');
    const otherLinks = links.filter((link) => link.link_type !== 'DRIVE_PDF' && link.link_type !== 'NODE');

    return (
        <div className="space-y-4">
            {/* PDF Links Section */}
            <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-gray-700">PDF Files</h3>
                    <button
                        onClick={onAddPDFClick}
                        className="px-3 py-1 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors"
                    >
                        + Add PDF
                    </button>
                </div>
                {pdfLinks.length > 0 ? (
                    <div className="space-y-2">
                        {pdfLinks.map((link) => {
                            const info = getLinkDisplayInfo(link);
                            return (
                                <div key={link.link_id} className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200">
                                    <span className="material-symbols-outlined text-blue-500">{info.icon}</span>
                                    <div className="flex-1">
                                        <p className="font-medium text-gray-800">{info.title}</p>
                                        <p className="text-sm text-gray-500">{info.description}</p>
                                    </div>
                                    <button
                                        onClick={() => onDeleteRequest(link)}
                                        className="text-gray-400 hover:text-red-500 transition-colors"
                                        title="Delete link"
                                    >
                                        <span className="material-symbols-outlined">delete</span>
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <p className="text-sm text-gray-500 italic">No PDF files linked yet.</p>
                )}
            </div>

            {/* Node-to-Node Links Section */}
            <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-gray-700">Node Links</h3>
                    <button
                        onClick={onAddNodeLinkClick}
                        className="px-3 py-1 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600 transition-colors"
                    >
                        + Add Link
                    </button>
                </div>
                {nodeLinks.length > 0 ? (
                    <div className="space-y-2">
                        {nodeLinks.map((link) => {
                            const info = getLinkDisplayInfo(link);
                            return (
                                <div key={link.link_id} className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200">
                                    <span className="material-symbols-outlined text-green-500">{info.icon}</span>
                                    <div className="flex-1">
                                        <p className="font-medium text-gray-800">{info.title}</p>
                                        <p className="text-sm text-gray-500">{info.description}</p>
                                    </div>
                                    <button
                                        onClick={() => onDeleteRequest(link)}
                                        className="text-gray-400 hover:text-red-500 transition-colors"
                                        title="Delete link"
                                    >
                                        <span className="material-symbols-outlined">delete</span>
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <p className="text-sm text-gray-500 italic">No node links yet.</p>
                )}
            </div>

            {/* Other Links Section */}
            {otherLinks.length > 0 && (
                <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Other Resources</h3>
                    <div className="space-y-2">
                        {otherLinks.map((link) => {
                            const info = getLinkDisplayInfo(link);
                            return (
                                <div key={link.link_id} className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200">
                                    <span className="material-symbols-outlined text-gray-500">{info.icon}</span>
                                    <div className="flex-1">
                                        <p className="font-medium text-gray-800">{info.title}</p>
                                        <p className="text-sm text-gray-500">{info.description}</p>
                                    </div>
                                    <button
                                        onClick={() => onDeleteRequest(link)}
                                        className="text-gray-400 hover:text-red-500 transition-colors"
                                        title="Delete link"
                                    >
                                        <span className="material-symbols-outlined">delete</span>
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

export default LinkManager;
