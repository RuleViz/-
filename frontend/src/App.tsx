import { useState } from 'react';
import './index.css';
import LLMConfigModal from './components/LLMConfigModal';
import JobAddForm from './components/JobAddForm';
import JobList from './components/JobList';

function App() {
  const [showConfig, setShowConfig] = useState(false);
  const [currentView, setCurrentView] = useState<'add' | 'list'>('add');
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleJobCreated = () => {
    setRefreshTrigger(prev => prev + 1);
    setCurrentView('list');
  };

  return (
    <div style={{ minHeight: '100vh', paddingBottom: '40px' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #E74C3C 0%, #C0392B 100%)',
        color: 'white',
        padding: '32px 0',
        marginBottom: '40px',
        boxShadow: '0 4px 12px rgba(231, 76, 60, 0.2)',
      }}>
        <div className="container">
          <div className="flex-between">
            <div>
              <h1 style={{ color: 'white', marginBottom: '8px' }}>职位投递系统</h1>
              <p style={{ color: 'rgba(255,255,255,0.9)', margin: 0 }}>
                AI驱动的职位管理，自动分类
              </p>
            </div>
            <button
              className="btn"
              style={{
                background: 'rgba(255,255,255,0.2)',
                color: 'white',
                backdropFilter: 'blur(10px)',
              }}
              onClick={() => setShowConfig(true)}
            >
              LLM 状态
            </button>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="container">
        <div style={{
          display: 'flex',
          gap: '12px',
          marginBottom: '32px',
          borderBottom: '2px solid #E8ECEF',
          paddingBottom: '12px',
        }}>
          <button
            className={`btn ${currentView === 'add' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setCurrentView('add')}
            style={{ borderRadius: '8px 8px 0 0' }}
          >
            添加职位
          </button>
          <button
            className={`btn ${currentView === 'list' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setCurrentView('list')}
            style={{ borderRadius: '8px 8px 0 0' }}
          >
            职位列表
          </button>
        </div>

        {/* Content */}
        <div style={{ display: currentView === 'add' ? 'block' : 'none' }}>
          <JobAddForm onSuccess={handleJobCreated} />
        </div>
        <div style={{ display: currentView === 'list' ? 'block' : 'none' }}>
          <JobList refreshTrigger={refreshTrigger} />
        </div>
      </div>

      {/* LLM Config Modal */}
      <LLMConfigModal
        isOpen={showConfig}
        onClose={() => setShowConfig(false)}
      />

      {/* Footer */}
      <div style={{
        textAlign: 'center',
        padding: '24px',
        marginTop: '60px',
        color: '#95A5A6',
        fontSize: '14px',
      }}>
        <p>基于 FastAPI + React + OpenAI 构建</p>
      </div>
    </div>
  );
}

export default App;
