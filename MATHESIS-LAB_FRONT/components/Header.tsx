
import React from 'react';
import { Link, NavLink } from 'react-router-dom';

interface NavItem {
    path: string;
    label: string;
}

interface HeaderProps {
    navItems: NavItem[];
}

const Header: React.FC<HeaderProps> = ({ navItems }) => {
    return (
        <header className="sticky top-0 z-10 w-full border-b border-border-light bg-surface/80 backdrop-blur-sm">
            <div className="container mx-auto px-4">
                <div className="flex h-16 items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="size-6 text-primary">
                            <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                                <path d="M44 11.2727C44 14.0109 39.8386 16.3957 33.69 17.6364C39.8386 18.877 44 21.2618 44 24C44 26.7382 39.8386 29.123 33.69 30.3636C39.8386 31.6043 44 33.9891 44 36.7273C44 40.7439 35.0457 44 24 44C12.9543 44 4 40.7439 4 36.7273C4 33.9891 8.16144 31.6043 14.31 30.3636C8.16144 29.123 4 26.7382 4 24C4 21.2618 8.16144 18.877 14.31 17.6364C8.16144 16.3957 4 14.0109 4 11.2727C4 7.25611 12.9543 4 24 4C35.0457 4 44 7.25611 44 11.2727Z" fill="currentColor"></path>
                            </svg>
                        </div>
                        <h1 className="text-lg font-bold">MATHESIS LAB</h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <nav className="hidden md:flex items-center gap-6">
                            {navItems.map(item => (
                                <NavLink
                                    key={item.path}
                                    to={item.path}
                                    className={({ isActive }) =>
                                        `text-sm font-medium transition-colors hover:text-primary ${isActive ? 'text-text-primary' : 'text-text-secondary'}`
                                    }
                                >
                                    {item.label}
                                </NavLink>
                            ))}
                        </nav>
                        <div className="h-6 w-px bg-border-light hidden md:block"></div>
                        <button className="flex h-10 w-10 cursor-pointer items-center justify-center overflow-hidden rounded-full hover:bg-black/5">
                            <span className="material-symbols-outlined text-2xl text-text-secondary">notifications</span>
                        </button>
                        <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10" style={{ backgroundImage: `url("https://picsum.photos/seed/user/40/40")` }}></div>
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
