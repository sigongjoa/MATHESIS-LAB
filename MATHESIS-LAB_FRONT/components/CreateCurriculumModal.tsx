
import React, { useState } from 'react';
import { createCurriculum } from '../services/curriculumService';
import { Curriculum, CurriculumCreate } from '../types';

interface CreateCurriculumModalProps {
    onClose: () => void;
    onCurriculumCreated: (newCurriculum: Curriculum) => void;
}

const CreateCurriculumModal: React.FC<CreateCurriculumModalProps> = ({ onClose, onCurriculumCreated }) => {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!title) {
            setError('Title is required.');
            return;
        }

        const newCurriculumData: CurriculumCreate = { title, description };
        const newCurriculum = await createCurriculum(newCurriculumData);
        onCurriculumCreated(newCurriculum);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-xl bg-surface p-6 shadow-2xl" role="dialog" aria-labelledby="dialog-title" aria-modal="true">
                <form onSubmit={handleSubmit}>
                    <h2 id="dialog-title" className="text-2xl font-bold mb-4">Create New Curriculum</h2>
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
                        <button type="button" onClick={onClose} id="cancel-create-curriculum" className="px-4 py-2 text-sm font-medium rounded-lg hover:bg-black/10">Cancel</button>
                        <button type="submit" id="submit-create-curriculum" className="px-4 py-2 text-sm font-bold text-white bg-primary rounded-lg hover:bg-primary/90">Create</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CreateCurriculumModal;
