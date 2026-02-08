import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface LLMConfigModalProps {
    isOpen: boolean;
    onClose: () => void;
}

interface LLMConfig {
    is_configured: boolean;
    model: string;
    base_url: string;
    api_key_preview: string;
}

const LLMConfigModal: React.FC<LLMConfigModalProps> = ({ isOpen, onClose }) => {
    const [config, setConfig] = useState<LLMConfig | null>(null);
    const [loading, setLoading] = useState(true);

    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

    useEffect(() => {
        if (isOpen) {
            loadConfig();
            setTestResult(null);
        }
    }, [isOpen]);

    const loadConfig = async () => {
        setLoading(true);
        try {
            const response = await axios.get('/api/config/llm');
            setConfig({
                is_configured: response.data.is_configured,
                model: response.data.model,
                base_url: response.data.base_url,
                api_key_preview: response.data.api_key_preview
            });
        } catch (error) {
            console.error('Failed to load config:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleTest = async () => {
        setTesting(true);
        setTestResult(null);
        try {
            const response = await axios.post('/api/config/llm/test');
            setTestResult({
                success: response.data.success,
                message: response.data.message + (response.data.model_info ? ` (Model: ${response.data.model_info.model})` : '')
            });
        } catch (error: any) {
            setTestResult({
                success: false,
                message: error.response?.data?.message || 'Connection failed'
            });
        } finally {
            setTesting(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
                <h2 style={{ marginBottom: '24px' }}>LLM 配置</h2>

                {loading ? (
                    <div className="flex-center" style={{ padding: '40px' }}>
                        <div className="spinner" style={{ width: '30px', height: '30px' }}></div>
                    </div>
                ) : config ? (
                    <>
                        {testResult && (
                            <div className={`alert ${testResult.success ? 'alert-success' : 'alert-error'}`} style={{ marginBottom: '16px' }}>
                                {testResult.success ? '✅ ' : '❌ '}{testResult.message}
                            </div>
                        )}

                        <div className={`alert ${config.is_configured ? 'alert-success' : 'alert-error'}`}>
                            {config.is_configured
                                ? '✅ LLM 已配置 (API Key已设置)'
                                : '❌ LLM 未配置 (未检测到 API Key)'
                            }
                        </div>

                        <div style={{
                            background: '#f8f9fa',
                            borderRadius: '12px',
                            padding: '20px',
                            marginTop: '16px'
                        }}>
                            <h3 style={{ fontSize: '1.1rem', marginBottom: '16px' }}>当前配置 (.env)</h3>

                            <div className="form-group">
                                <label className="form-label">模型</label>
                                <div style={{
                                    padding: '12px',
                                    background: 'white',
                                    borderRadius: '8px',
                                    fontFamily: 'monospace',
                                    fontSize: '14px'
                                }}>
                                    {config.model}
                                </div>
                            </div>

                            <div className="form-group">
                                <label className="form-label">基础 URL</label>
                                <div style={{
                                    padding: '12px',
                                    background: 'white',
                                    borderRadius: '8px',
                                    fontFamily: 'monospace',
                                    fontSize: '14px',
                                    wordBreak: 'break-all'
                                }}>
                                    {config.base_url}
                                </div>
                            </div>

                            <div className="form-group">
                                <label className="form-label">API 密钥状态</label>
                                <div style={{
                                    padding: '12px',
                                    background: 'white',
                                    borderRadius: '8px',
                                    fontSize: '14px',
                                    fontFamily: 'monospace',
                                    color: config.is_configured ? '#52c41a' : '#ff4d4f'
                                }}>
                                    {config.api_key_preview}
                                </div>
                            </div>
                        </div>

                        <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                            <button
                                className="btn btn-secondary"
                                onClick={handleTest}
                                disabled={testing || !config.is_configured}
                                style={{ flex: 1.5 }}
                            >
                                {testing ? <span className="spinner"></span> : ''}
                                {testing ? '测试中...' : '测试连接'}
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={loadConfig}
                                disabled={testing}
                                style={{ flex: 1 }}
                            >
                                刷新状态
                            </button>
                            <button
                                className="btn btn-ghost"
                                onClick={onClose}
                                disabled={testing}
                                style={{ flex: 0.5 }}
                            >
                                关闭
                            </button>
                        </div>

                        {!config.is_configured && (
                            <div style={{
                                background: '#fff3cd',
                                border: '1px solid #ffc107',
                                borderRadius: '8px',
                                padding: '16px',
                                marginTop: '16px',
                                fontSize: '14px',
                                lineHeight: '1.6'
                            }}>
                                <strong>配置方法：</strong>
                                <br />
                                1. 打开 <code style={{ background: '#f8f9fa', padding: '2px 6px', borderRadius: '4px' }}>backend/.env</code> 文件
                                <br />
                                2. 设置 <code style={{ background: '#f8f9fa', padding: '2px 6px', borderRadius: '4px' }}>OPENAI_API_KEY</code>
                                <br />
                                3. 重启后端服务
                            </div>
                        )}
                    </>
                ) : (
                    <div className="alert alert-error">
                        加载配置失败
                    </div>
                )}
            </div>
        </div>
    );
};

export default LLMConfigModal;
