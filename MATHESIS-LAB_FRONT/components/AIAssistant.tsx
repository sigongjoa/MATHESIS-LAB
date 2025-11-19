
import React, { useState, useRef } from 'react';
import gcpService from '../services/gcpService';
import Spinner from './Spinner';
import '../styles/AIAssistant.css';

interface AIAssistantProps {
    content: string;
    nodeId: string;
    onUpdateContent: (newContent: string) => void;
}

type AITask = 'summarize' | 'expand' | 'manim';

interface AIResult {
    task: AITask;
    result: string;
    tokensUsed?: number;
    processingTime?: number;
}

const AIAssistant: React.FC<AIAssistantProps> = ({ content, nodeId, onUpdateContent }) => {
    const [loadingTask, setLoadingTask] = useState<AITask | null>(null);
    const [aiResults, setAIResults] = useState<AIResult[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [showResults, setShowResults] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleAIAssist = async (task: AITask) => {
        setLoadingTask(task);
        setError(null);

        let response;

        switch (task) {
            case 'summarize':
                response = await gcpService.summarizeContent(nodeId, content);
                break;
            case 'expand':
                response = await gcpService.extendContent(nodeId, content);
                break;
            case 'manim':
                // This shouldn't be called directly, use handleManimUpload instead
                setLoadingTask(null);
                return;
        }

        // Add result to history
        const newResult: AIResult = {
            task,
            result: response.result,
            tokensUsed: response.tokens_used,
            processingTime: response.processing_time_ms,
        };

        setAIResults([newResult, ...aiResults]);
        setShowResults(true);
        onUpdateContent(response.result);
        setLoadingTask(null);
    };

    const handleManimUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setLoadingTask('manim');
        setError(null);

        const response = await gcpService.generateManimGuidelines(nodeId, file);

        const newResult: AIResult = {
            task: 'manim',
            result: response.result,
            tokensUsed: response.tokens_used,
            processingTime: response.processing_time_ms,
        };

        setAIResults([newResult, ...aiResults]);
        setShowResults(true);
        onUpdateContent(response.result);
        setLoadingTask(null);
        // Reset file input
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const AIButton: React.FC<{ task: AITask; icon: string; label: string }> = ({ task, icon, label }) => (
        <button
            onClick={() => handleAIAssist(task)}
            disabled={loadingTask !== null || !content.trim()}
            className="ai-button"
            title={!content.trim() ? 'Add content first' : undefined}
        >
            {loadingTask === task ? <Spinner /> : <span className="icon">{icon}</span>}
            <span className="label">{label}</span>
        </button>
    );

    const formatTaskName = (task: AITask): string => {
        switch (task) {
            case 'summarize':
                return 'Summarized Content';
            case 'expand':
                return 'Expanded Content';
            case 'manim':
                return 'Manim Guidelines';
        }
    };

    const getTaskIcon = (task: AITask): string => {
        switch (task) {
            case 'summarize':
                return '📝';
            case 'expand':
                return '📚';
            case 'manim':
                return '🎥';
        }
    };

    return (
        <div className="ai-assistant">
            <div className="ai-header">
                <h3>✨ AI Assistant (Powered by Vertex AI)</h3>
                <p>Enhance your content using Google's advanced AI capabilities</p>
            </div>

            {error && <div className="ai-error">{error}</div>}

            <div className="ai-buttons-grid">
                <AIButton task="summarize" icon="📝" label="Summarize" />
                <AIButton task="expand" icon="📚" label="Expand" />
                <label className="ai-button ai-file-button">
                    {loadingTask === 'manim' ? (
                        <>
                            <Spinner />
                            <span className="label">Processing...</span>
                        </>
                    ) : (
                        <>
                            <span className="icon">🎥</span>
                            <span className="label">Manim Guide</span>
                        </>
                    )}
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleManimUpload}
                        disabled={loadingTask !== null}
                        style={{ display: 'none' }}
                    />
                </label>
            </div>

            {aiResults.length > 0 && (
                <div className="ai-results-section">
                    <div className="results-header">
                        <h4>📊 AI Results History ({aiResults.length})</h4>
                        <button
                            className="toggle-button"
                            onClick={() => setShowResults(!showResults)}
                        >
                            {showResults ? '▼ Hide' : '▶ Show'}
                        </button>
                    </div>

                    {showResults && (
                        <div className="results-list">
                            {aiResults.map((result, index) => (
                                <div key={index} className="result-item">
                                    <div className="result-header">
                                        <span className="result-task">
                                            {getTaskIcon(result.task)} {formatTaskName(result.task)}
                                        </span>
                                        {result.processingTime && (
                                            <span className="result-time">
                                                ⏱️ {(result.processingTime / 1000).toFixed(2)}s
                                            </span>
                                        )}
                                        {result.tokensUsed && (
                                            <span className="result-tokens">
                                                🔤 {result.tokensUsed} tokens
                                            </span>
                                        )}
                                    </div>
                                    <div className="result-content">
                                        {result.result.substring(0, 300)}
                                        {result.result.length > 300 ? '...' : ''}
                                    </div>
                                    <button
                                        className="use-result-btn"
                                        onClick={() => onUpdateContent(result.result)}
                                    >
                                        ✓ Use This Result
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            <div className="ai-info">
                <p>
                    💡 <strong>Tip:</strong> Add content to the editor above, then click any AI button to enhance it. Upload images for Manim guideline generation.
                </p>
            </div>
        </div>
    );
};

export default AIAssistant;
