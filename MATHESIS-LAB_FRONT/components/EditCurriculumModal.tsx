
import React, { useState, useEffect } from 'react';
import { updateCurriculum } from '../services/curriculumService';
import { Curriculum, CurriculumUpdate } from '../types';

interface EditCurriculumModalProps {
    curriculum: Curriculum;
    onClose: () => void;
    onCurriculumUpdated: (updatedCurriculum: Curriculum) => void;
}

const EditCurriculumModal: React.FC<EditCurriculumModalProps> = ({ curriculum, onClose, onCurriculumUpdated }) => {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (curriculum) {
            setTitle(curriculum.title);
            setDescription(curriculum.description);
        }
    }, [curriculum]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!title) {
            setError('Title is required.');
            return;
        }

        try {
            const updatedData: CurriculumUpdate = { title, description };
            const updatedCurriculum = await updateCurriculum(curriculum.curriculum_id!, updatedData);
            onCurriculumUpdated(updatedCurriculum);
            onClose();
        } catch (err) {
            setError('Failed to update curriculum. Please try again.');
            console.error(err);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-xl bg-surface p-6 shadow-2xl" role="dialog" aria-labelledby="dialog-title" aria-modal="true">
                <form onSubmit={handleSubmit}>
                    <h2 id="dialog-title" className="text-2xl font-bold mb-4">Edit Curriculum</h2>
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
                                placeholder="e.g., Introduction to Calculus"
                            />
                        </div>
                        <div>
                            <label htmlFor="description" className="block text-sm font-medium text-text-secondary mb-1">Description</label>
                            <textarea
                                id="description"
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                className="w-full rounded-lg border-border-light"
                                placeholder="A brief description of the curriculum"
                                rows={4}
                            />
                        </div>
                    </div>
                    <div className="mt-6 flex justify-end gap-4">
                        <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium rounded-lg hover:bg-black/10">Cancel</button>
                        <button type="submit" className="px-4 py-2 text-sm font-bold text-white bg-primary rounded-lg hover:bg-primary/90">Save Changes</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default EditCurriculumModal;
