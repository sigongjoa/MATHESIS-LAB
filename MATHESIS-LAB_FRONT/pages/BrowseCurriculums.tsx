
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { MOCK_CURRICULUMS } from '../constants';
import { Curriculum } from '../types';
import GoogleSignInButton from '../components/GoogleSignInButton';


const CurriculumCard: React.FC<{ curriculum: Curriculum }> = ({ curriculum }) => (
    <div className="group @container">
        <Link to={`/curriculum/${curriculum.id}`}>
        <div className="flex flex-col items-stretch justify-start rounded-xl overflow-hidden shadow-sm hover:shadow-lg transition-shadow duration-300 bg-white cursor-pointer border border-gray-200 h-full">
            <div className="w-full bg-center bg-no-repeat aspect-video bg-cover" style={{ backgroundImage: `url("${curriculum.image}")` }}></div>
            <div className="flex w-full min-w-72 grow flex-col items-stretch justify-center gap-1 p-4">
                <p className="text-gray-900 text-lg font-bold leading-tight tracking-[-0.015em] group-hover:text-primary transition-colors">{curriculum.title}</p>
                <p className="text-gray-600 text-sm font-normal leading-normal mt-1">{curriculum.description}</p>
                <p className="text-gray-500 text-xs font-normal leading-normal mt-2">창작자: {curriculum.author}</p>
            </div>
        </div>
        </Link>
    </div>
);


const BrowseCurriculums: React.FC = () => {
    const [isSigningIn, setIsSigningIn] = useState(false);
    const [signInError, setSignInError] = useState<string | null>(null);

    const handleSignInStart = () => {
        setIsSigningIn(true);
        setSignInError(null);
    };

    const handleSignInError = (error: Error) => {
        setIsSigningIn(false);
        setSignInError(error.message);
        console.error('Sign-in error:', error);
    };

    return (
        <div className="relative flex h-auto min-h-screen w-full flex-col font-display group/design-root overflow-x-hidden bg-white">
            <div className="layout-container flex h-full grow flex-col">
                <div className="px-4 md:px-10 lg:px-20 xl:px-40 flex flex-1 justify-center py-5">
                    <div className="layout-content-container flex flex-col max-w-6xl flex-1">
                        <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-gray-200 px-4 sm:px-10 py-3">
                            <Link to="/" className="flex items-center gap-4 text-black">
                                <div className="size-6 text-primary">
                                    <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M44 11.2727C44 14.0109 39.8386 16.3957 33.69 17.6364C39.8386 18.877 44 21.2618 44 24C44 26.7382 39.8386 29.123 33.69 30.3636C39.8386 31.6043 44 33.9891 44 36.7273C44 40.7439 35.0457 44 24 44C12.9543 44 4 40.7439 4 36.7273C4 33.9891 8.16144 31.6043 14.31 30.3636C8.16144 29.123 4 26.7382 4 24C4 21.2618 8.16144 18.877 14.31 17.6364C8.16144 16.3957 4 14.0109 4 11.2727C4 7.25611 12.9543 4 24 4C35.0457 4 44 7.25611 44 11.2727Z" fill="currentColor"></path>
                                    </svg>
                                </div>
                                <h2 className="text-black text-lg font-bold leading-tight tracking-[-0.015em]">MATHESIS LAB</h2>
                            </Link>
                            <div className="flex flex-1 justify-end items-center gap-4 sm:gap-6">
                                <Link className="text-gray-700 text-sm font-medium leading-normal hover:text-primary transition-colors hidden sm:block" to="/">내 커리큘럼</Link>
                                <div className="min-w-[150px]">
                                    <GoogleSignInButton
                                        onSignInStart={handleSignInStart}
                                        onSignInError={handleSignInError}
                                        buttonText="로그인"
                                    />
                                </div>
                                {signInError && (
                                    <div className="text-red-500 text-sm mt-2">
                                        {signInError}
                                    </div>
                                )}
                            </div>
                        </header>
                        <main className="flex-1 px-4 py-8">
                            <div className="flex flex-wrap justify-between gap-4 items-center mb-6">
                                <p className="text-gray-900 text-3xl md:text-4xl font-black leading-tight tracking-[-0.033em] min-w-72">모든 커리큘럼 둘러보기</p>
                            </div>
                            <div className="mb-6">
                                <label className="flex flex-col min-w-40 h-12 w-full">
                                    <div className="flex w-full flex-1 items-stretch rounded-lg h-full">
                                        <div className="text-gray-400 flex border-y border-l border-gray-300 bg-white items-center justify-center pl-4 rounded-l-lg">
                                            <span className="material-symbols-outlined">search</span>
                                        </div>
                                        <input className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-r-lg text-gray-900 focus:outline-0 focus:ring-2 focus:ring-primary focus:ring-inset border-y border-r border-gray-300 bg-white h-full placeholder:text-gray-400 px-4 text-base font-normal leading-normal" placeholder="키워드로 커리큘럼 검색" />
                                    </div>
                                </label>
                            </div>
                            <div className="flex flex-wrap gap-3 mb-8">
                                <button className="flex h-8 shrink-0 items-center justify-center gap-x-2 rounded-lg bg-gray-200 pl-4 pr-2 hover:bg-gray-300 transition-colors">
                                    <p className="text-gray-800 text-sm font-medium leading-normal">정렬: 최신순</p>
                                    <div className="text-gray-800">
                                        <span className="material-symbols-outlined text-base">expand_more</span>
                                    </div>
                                </button>
                                <button className="flex h-8 shrink-0 items-center justify-center gap-x-2 rounded-lg bg-gray-200 pl-4 pr-2 hover:bg-gray-300 transition-colors">
                                    <p className="text-gray-800 text-sm font-medium leading-normal">카테고리</p>
                                    <div className="text-gray-800">
                                        <span className="material-symbols-outlined text-base">expand_more</span>
                                    </div>
                                </button>
                                <button className="flex h-8 shrink-0 items-center justify-center gap-x-2 rounded-lg bg-gray-200 pl-4 pr-2 hover:bg-gray-300 transition-colors">
                                    <p className="text-gray-800 text-sm font-medium leading-normal">레벨</p>
                                    <div className="text-gray-800">
                                        <span className="material-symbols-outlined text-base">expand_more</span>
                                    </div>
                                </button>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {MOCK_CURRICULUMS.map(curriculum => (
                                    <CurriculumCard key={curriculum.id} curriculum={curriculum} />
                                ))}
                            </div>
                        </main>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BrowseCurriculums;
