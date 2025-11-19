
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import { Curriculum } from '../types';
import { getCurriculums, deleteCurriculum } from '../services/curriculumService';
import CreateCurriculumModal from '../components/CreateCurriculumModal';
import EditCurriculumModal from '../components/EditCurriculumModal';

const CurriculumListItem: React.FC<{ 
    curriculum: Curriculum, 
    onDelete: (id: string) => void,
    onEdit: (curriculum: Curriculum) => void 
}> = ({ curriculum, onDelete, onEdit }) => (
    <div className="flex items-center gap-4 rounded-lg border border-border-light bg-surface p-4 shadow-sm transition-shadow hover:shadow-md">
        <div className="flex shrink-0 items-center justify-center rounded-lg bg-primary/10 size-12">
            <span className="material-symbols-outlined text-2xl text-primary">{curriculum.icon || 'school'}</span>
        </div>
        <div className="flex-1">
            <Link to={`/curriculum/${curriculum.curriculum_id}`} className="block">
                <p className="text-base font-bold leading-normal line-clamp-1 hover:underline">{curriculum.title}</p>
            </Link>
            <p className="text-sm font-normal text-text-secondary line-clamp-2">{curriculum.description}</p>
        </div>
        <div className="flex items-center gap-2">
            <button 
                onClick={() => onEdit(curriculum)}
                className="flex h-9 min-w-9 cursor-pointer items-center justify-center overflow-hidden rounded-lg bg-black/5 px-3 text-sm font-medium hover:bg-black/10">
                <span className="material-symbols-outlined text-xl">edit</span>
                <span className="hidden sm:inline ml-1.5">수정</span>
            </button>
            <button 
                onClick={() => onDelete(curriculum.curriculum_id!)}
                className="flex h-9 min-w-9 cursor-pointer items-center justify-center overflow-hidden rounded-lg px-3 text-sm font-medium hover:bg-red-500/10 hover:text-red-500">
                <span className="material-symbols-outlined text-xl">delete</span>
                <span className="hidden sm:inline ml-1.5">삭제</span>
            </button>
        </div>
    </div>
);

const MyCurriculum: React.FC = () => {
    const [curriculums, setCurriculums] = useState<Curriculum[]>([]);
    const [isCreateModalOpen, setCreateModalOpen] = useState(false);
    const [isEditModalOpen, setEditModalOpen] = useState(false);
    const [editingCurriculum, setEditingCurriculum] = useState<Curriculum | null>(null);

    useEffect(() => {
        const fetchCurriculums = async () => {
            const data = await getCurriculums();
            setCurriculums(data);
        };
        fetchCurriculums();
    }, []);

    const handleCurriculumCreated = (newCurriculum: Curriculum) => {
        setCurriculums([newCurriculum, ...curriculums]);
    };

    const handleDelete = async (id: string) => {
        await deleteCurriculum(id);
        setCurriculums(curriculums.filter(c => c.curriculum_id !== id));
    };

    const handleEditClick = (curriculum: Curriculum) => {
        setEditingCurriculum(curriculum);
        setEditModalOpen(true);
    };

    const handleCurriculumUpdated = (updatedCurriculum: Curriculum) => {
        setCurriculums(curriculums.map(c => c.curriculum_id === updatedCurriculum.curriculum_id ? updatedCurriculum : c));
    };

    const navItems = [
        { path: "/browse", label: "Browse All" },
        { path: "/", label: "My Curriculum" },
    ];

    return (
        <div className="relative flex h-auto min-h-screen w-full flex-col">
            <Header navItems={navItems} />
            <main className="flex-1">
                <div className="container mx-auto max-w-4xl px-4 py-8 md:py-12">
                    <div className="flex flex-col gap-8">
                        <div className="flex flex-wrap items-center justify-between gap-4">
                            <h2 className="text-3xl md:text-4xl font-black tracking-tighter">내 커리큘럼 관리</h2>
                            <button 
                                onClick={() => setCreateModalOpen(true)}
                                className="flex h-10 items-center justify-center gap-2 whitespace-nowrap rounded-lg bg-primary px-4 text-sm font-bold text-white shadow-sm transition-transform hover:scale-[1.02] active:scale-[0.98]">
                                <span className="material-symbols-outlined text-xl">add_circle</span>
                                <span className="truncate">새 커리큘럼 만들기</span>
                            </button>
                        </div>
                        <div className="flex flex-col gap-4">
                            {curriculums.map(curriculum => (
                                <CurriculumListItem 
                                    key={curriculum.curriculum_id} 
                                    curriculum={curriculum} 
                                    onDelete={handleDelete}
                                    onEdit={handleEditClick}
                                />
                            ))}
                        </div>
                    </div>
                </div>
            </main>
            {isCreateModalOpen && (
                <CreateCurriculumModal 
                    onClose={() => setCreateModalOpen(false)} 
                    onCurriculumCreated={handleCurriculumCreated} 
                />
            )}
            {isEditModalOpen && editingCurriculum && (
                <EditCurriculumModal
                    curriculum={editingCurriculum}
                    onClose={() => setEditModalOpen(false)}
                    onCurriculumUpdated={handleCurriculumUpdated}
                />
            )}
        </div>
    );
};

export default MyCurriculum;
