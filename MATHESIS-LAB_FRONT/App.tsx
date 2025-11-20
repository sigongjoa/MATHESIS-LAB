
import React from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import MyCurriculum from './pages/MyCurriculum';
import BrowseCurriculums from './pages/BrowseCurriculums';
import CurriculumEditor from './pages/CurriculumEditor';
import NodeEditor from './pages/NodeEditor';
import GCPSettings from './pages/GCPSettings';
import GDriveCallback from './pages/GDriveCallback';

function App() {
    return (
        <HashRouter>
            <Routes>
                <Route path="/" element={<MyCurriculum />} />
                <Route path="/browse" element={<BrowseCurriculums />} />
                <Route path="/curriculum/:curriculumId" element={<CurriculumEditor />} />
                <Route path="/curriculum/:curriculumId/node/:nodeId" element={<NodeEditor />} />
                <Route path="/gcp-settings" element={<GCPSettings />} />
                <Route path="/gdrive/callback" element={<GDriveCallback />} />
            </Routes>
        </HashRouter>
    );
}

export default App;
