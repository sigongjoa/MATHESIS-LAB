"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getCurriculums, createCurriculum, updateCurriculum, deleteCurriculum } from "@/lib/api";

interface Curriculum {
  curriculum_id: string;
  title: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export default function CurriculumsPage() {
  const [curriculums, setCurriculums] = useState<Curriculum[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // State for the create form
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");

  // State for inline editing
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [editingDescription, setEditingDescription] = useState("");

  const fetchAndSetCurriculums = async () => {
    try {
      const data = await getCurriculums();
      setCurriculums(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAndSetCurriculums();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) {
      setError("Title is required.");
      return;
    }
    try {
      await createCurriculum({ title: newTitle, description: newDescription });
      setNewTitle("");
      setNewDescription("");
      setError(null);
      await fetchAndSetCurriculums(); // Refetch the list
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm("Are you sure you want to delete this curriculum?")) {
      try {
        await deleteCurriculum(id);
        await fetchAndSetCurriculums(); // Refetch the list
      } catch (err: any) {
        setError(err.message);
      }
    }
  };

  const handleEdit = (curriculum: Curriculum) => {
    setEditingId(curriculum.curriculum_id);
    setEditingTitle(curriculum.title);
    setEditingDescription(curriculum.description);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditingTitle("");
    setEditingDescription("");
  };

  const handleUpdate = async (id: string) => {
    if (!editingTitle.trim()) {
      setError("Title is required.");
      return;
    }
    try {
      await updateCurriculum(id, { title: editingTitle, description: editingDescription });
      handleCancelEdit();
      await fetchAndSetCurriculums(); // Refetch the list
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (loading) {
    return <div className="p-8">Loading curriculums...</div>;
  }

  return (
    <main className="px-4 sm:px-6 lg:px-8 flex flex-1 justify-center py-5">
      <div className="layout-content-container flex flex-col w-full max-w-4xl flex-1 gap-8">
        <div className="flex flex-wrap justify-between gap-3 items-center">
          <p className="text-gray-900 dark:text-white text-4xl font-black leading-tight tracking-[-0.033em] min-w-72">Curriculums</p>
        </div>

        {/* Create New Curriculum Section */}
        <section className="bg-white dark:bg-background-dark/50 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800">
          <h2 className="text-gray-900 dark:text-white text-[22px] font-bold leading-tight tracking-[-0.015em] pb-5">Create New Curriculum</h2>
          <form onSubmit={handleCreate} className="flex flex-col gap-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <label className="flex flex-col min-w-40 flex-1">
                <p className="text-gray-800 dark:text-gray-200 text-base font-medium leading-normal pb-2">Title</p>
                <input
                  className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-gray-900 dark:text-white focus:outline-0 focus:ring-2 focus:ring-primary/50 border border-gray-300 dark:border-gray-700 bg-background-light dark:bg-gray-900/50 h-12 placeholder:text-gray-400 dark:placeholder:text-gray-500 p-[15px] text-base font-normal leading-normal"
                  placeholder="e.g., Introduction to Web Development"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                />
              </label>
            </div>
            <div>
              <label className="flex flex-col min-w-40 flex-1">
                <p className="text-gray-800 dark:text-gray-200 text-base font-medium leading-normal pb-2">Description</p>
                <textarea
                  className="form-input flex w-full min-w-0 flex-1 resize-y overflow-hidden rounded-lg text-gray-900 dark:text-white focus:outline-0 focus:ring-2 focus:ring-primary/50 border border-gray-300 dark:border-gray-700 bg-background-light dark:bg-gray-900/50 min-h-28 placeholder:text-gray-400 dark:placeholder:text-gray-500 p-[15px] text-base font-normal leading-normal"
                  placeholder="A beginner's course covering HTML, CSS, and JavaScript."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                ></textarea>
              </label>
            </div>
            <div className="mt-2 flex justify-end">
              <button className="flex items-center justify-center gap-2 cursor-pointer rounded-lg h-10 px-5 bg-primary text-white text-sm font-bold leading-normal tracking-[0.015em] hover:bg-blue-700" type="submit">
                <span className="material-symbols-outlined text-xl">add_circle</span>
                <span>Create</span>
              </button>
            </div>
          </form>
          {error && (
            <div className="mt-4 p-4 bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-300 rounded-lg">
              <p>{error}</p>
            </div>
          )}
        </section>

        {/* Curriculum List Section */}
        <section>
          <h2 className="text-gray-900 dark:text-white text-[22px] font-bold leading-tight tracking-[-0.015em] px-4 pb-3 pt-5">Curriculum List</h2>
          <div className="flex flex-col gap-4">
            {loading ? (
              <div className="text-center py-16 text-gray-500 dark:text-gray-400">Loading curriculums...</div>
            ) : curriculums.length === 0 ? (
              <div className="text-center py-16 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-xl">
                <span className="material-symbols-outlined text-5xl text-gray-400 dark:text-gray-600">school</span>
                <p className="text-gray-500 dark:text-gray-400 mt-4">No curriculums found. Create one!</p>
              </div>
            ) : (
              curriculums.map((curriculum) => (
                <div key={curriculum.curriculum_id} className="bg-white dark:bg-background-dark/50 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6 flex flex-col gap-4">
                  {editingId === curriculum.curriculum_id ? (
                    // Editing View
                    <form className="flex flex-col gap-4" onSubmit={(e) => { e.preventDefault(); handleUpdate(curriculum.curriculum_id); }}>
                      <label className="flex flex-col min-w-40 flex-1">
                        <p className="text-gray-800 dark:text-gray-200 text-sm font-medium leading-normal pb-2">Title</p>
                        <input
                          className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-gray-900 dark:text-white focus:outline-0 focus:ring-2 focus:ring-primary/50 border border-gray-300 dark:border-gray-700 bg-background-light dark:bg-gray-900/50 h-11 placeholder:text-gray-400 dark:placeholder:text-gray-500 p-[15px] text-sm font-normal"
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                        />
                      </label>
                      <label className="flex flex-col min-w-40 flex-1">
                        <p className="text-gray-800 dark:text-gray-200 text-sm font-medium leading-normal pb-2">Description</p>
                        <textarea
                          className="form-input flex w-full min-w-0 flex-1 resize-y overflow-hidden rounded-lg text-gray-900 dark:text-white focus:outline-0 focus:ring-2 focus:ring-primary/50 border border-gray-300 dark:border-gray-700 bg-background-light dark:bg-gray-900/50 min-h-24 placeholder:text-gray-400 dark:placeholder:text-gray-500 p-[15px] text-sm font-normal"
                          value={editingDescription}
                          onChange={(e) => setEditingDescription(e.target.value)}
                        ></textarea>
                      </label>
                      <div className="flex justify-end gap-2 mt-2">
                        <button type="button" onClick={handleCancelEdit} className="flex items-center justify-center gap-1.5 cursor-pointer rounded-lg h-9 px-4 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-sm font-bold hover:bg-gray-300 dark:hover:bg-gray-600">
                          <span>Cancel</span>
                        </button>
                        <button type="submit" className="flex items-center justify-center gap-1.5 cursor-pointer rounded-lg h-9 px-4 bg-green-500 text-white text-sm font-bold hover:bg-green-600">
                          <span className="material-symbols-outlined text-base">save</span>
                          <span>Save</span>
                        </button>
                      </div>
                    </form>
                  ) : (
                    // Default View
                    <div>
                      <Link href={`/curriculums/${curriculum.curriculum_id}`} className="block">
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="text-lg font-bold text-gray-900 dark:text-white">{curriculum.title}</h3>
                            <p className="text-gray-600 dark:text-gray-400 mt-1 text-sm">{curriculum.description}</p>
                          </div>
                          <p className="text-xs text-gray-500 dark:text-gray-500 whitespace-nowrap pt-1">Last Updated: {new Date(curriculum.updated_at).toLocaleDateString()}</p>
                        </div>
                      </Link>
                      <div className="flex justify-end gap-2 mt-2">
                        <button onClick={() => handleEdit(curriculum)} className="flex items-center justify-center gap-1.5 cursor-pointer rounded-lg h-9 px-4 bg-amber-400/20 dark:bg-amber-400/10 text-amber-700 dark:text-amber-300 text-sm font-bold hover:bg-amber-400/30 dark:hover:bg-amber-400/20">
                          <span className="material-symbols-outlined text-base">edit</span>
                          <span>Edit</span>
                        </button>
                        <button onClick={() => handleDelete(curriculum.curriculum_id)} className="flex items-center justify-center gap-1.5 cursor-pointer rounded-lg h-9 px-4 bg-red-500/10 dark:bg-red-500/10 text-red-600 dark:text-red-400 text-sm font-bold hover:bg-red-500/20 dark:hover:bg-red-500/20">
                          <span className="material-symbols-outlined text-base">delete</span>
                          <span>Delete</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </main>
  );
}