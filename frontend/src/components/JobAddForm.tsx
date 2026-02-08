import React, { useState, useEffect } from 'react';
import * as api from '../api';

interface JobAddFormProps {
    onSuccess?: () => void;
}

const JobAddForm: React.FC<JobAddFormProps> = ({ onSuccess }) => {
    const [rawContent, setRawContent] = useState('');
    const [parsing, setParsing] = useState(false);
    const [saving, setSaving] = useState(false);
    const [parsedData, setParsedData] = useState<api.LLMParseResponse | null>(null);
    const [industries, setIndustries] = useState<api.Industry[]>([]);
    const [allTags, setAllTags] = useState<api.Tag[]>([]);
    const [selectedTagIds, setSelectedTagIds] = useState<number[]>([]);
    const [error, setError] = useState<string>('');
    const [success, setSuccess] = useState<string>('');

    useEffect(() => {
        loadIndustries();
        loadTags();
    }, []);

    const loadIndustries = async () => {
        try {
            const data = await api.getIndustries();
            setIndustries(data);
        } catch (error) {
            console.error('Failed to load industries:', error);
        }
    };

    const loadTags = async () => {
        try {
            const data = await api.getTags();
            setAllTags(data);
        } catch (error) {
            console.error('Failed to load tags:', error);
        }
    };

    const handleParse = async () => {
        if (!rawContent.trim()) {
            setError('请输入职位发布内容');
            return;
        }

        setParsing(true);
        setError('');
        setParsedData(null);

        try {
            const data = await api.parseJobPosting(rawContent, '手动');
            setParsedData(data);

            // Auto-create suggested tags
            const createdTagIds: number[] = [];
            for (const suggestedTag of data.suggested_tags) {
                const existing = allTags.find(t => t.code === suggestedTag.name.toLowerCase().replace(/\s+/g, '-'));
                if (existing) {
                    createdTagIds.push(existing.id);
                } else {
                    try {
                        const newTag = await api.createTag({
                            code: suggestedTag.name.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
                            name: suggestedTag.name,
                            category: suggestedTag.category,
                            color: suggestedTag.color || '#1890ff',
                            is_active: true,
                        });
                        createdTagIds.push(newTag.id);
                        setAllTags(prev => [...prev, newTag]);
                    } catch (error) {
                        console.error('Failed to create tag:', error);
                    }
                }
            }
            setSelectedTagIds(createdTagIds);

            // Auto-create industry if needed
            if (data.suggested_industry && data.suggested_industry_code) {
                const existing = industries.find(i => i.code === data.suggested_industry_code);
                if (!existing) {
                    try {
                        const newIndustry = await api.createIndustry({
                            code: data.suggested_industry_code,
                            name: data.suggested_industry,
                            parent_id: null,
                            sort_order: 0,
                            is_active: true,
                        });
                        setIndustries(prev => [...prev, newIndustry]);
                    } catch (error) {
                        console.error('Failed to create industry:', error);
                    }
                }
            }

        } catch (error: any) {
            setError(error.response?.data?.detail || '解析职位发布失败，请检查您的 LLM 配置。');
        } finally {
            setParsing(false);
        }
    };

    const handleSave = async () => {
        if (!parsedData) {
            setError('请先解析职位发布内容');
            return;
        }

        if (!parsedData.title?.trim()) {
            setError('❌ 职位名称不能为空');
            return;
        }

        if (!parsedData.apply_email?.trim()) {
            setError('❌ 投递邮箱不能为空');
            return;
        }

        setSaving(true);
        setError('');

        try {
            await api.createJob({
                title: parsedData.title,
                company_name: parsedData.company_name,
                industry_name: parsedData.suggested_industry,
                apply_email: parsedData.apply_email,
                email_subject_template: parsedData.email_subject_template,
                email_body_template: parsedData.email_body_template,
                requirements: parsedData.requirements,
                source_type: '手动',
                raw_content: rawContent,
                published_at: parsedData.published_at,
                status: 'active',
                tag_ids: selectedTagIds,
            });

            setSuccess('职位创建成功！');
            setTimeout(() => {
                setRawContent('');
                setParsedData(null);
                setSelectedTagIds([]);
                setSuccess('');
                onSuccess?.();
            }, 1500);
        } catch (error: any) {
            setError(error.response?.data?.detail || '创建职位失败');
        } finally {
            setSaving(false);
        }
    };

    const toggleTag = (tagId: number) => {
        setSelectedTagIds(prev =>
            prev.includes(tagId) ? prev.filter(id => id !== tagId) : [...prev, tagId]
        );
    };

    return (
        <div className="card" style={{ maxWidth: '900px', margin: '0 auto' }}>
            <h2 style={{ marginBottom: '24px' }}>添加新职位</h2>

            {error && <div className="alert alert-error">{error}</div>}
            {success && <div className="alert alert-success">{success}</div>}

            <div className="form-group">
                <label className="form-label">原始职位发布内容</label>
                <textarea
                    className="textarea"
                    placeholder="在此粘贴职位发布内容（来自微信、网站等）..."
                    value={rawContent}
                    onChange={(e) => setRawContent(e.target.value)}
                    rows={8}
                    disabled={parsing || saving}
                />
                <div className="form-hint">{rawContent.length} 个字符</div>
            </div>

            <button
                className="btn btn-primary"
                onClick={handleParse}
                disabled={parsing || saving || !rawContent.trim()}
                style={{ width: '100%', marginBottom: '24px' }}
            >
                {parsing ? <span className="spinner"></span> : ''}
                {parsing ? 'AI 解析中...' : 'AI 解析'}
            </button>

            {parsedData && (
                <>
                    <div style={{ padding: '20px', background: '#f8f9fa', borderRadius: '12px', marginBottom: '24px' }}>
                        <h3 style={{ marginBottom: '16px', fontSize: '1.2rem' }}>解析结果</h3>

                        <div className="form-group">
                            <label className="form-label">职位名称 <span style={{ color: 'red' }}>*</span></label>
                            <input
                                type="text"
                                className="input"
                                value={parsedData.title}
                                onChange={(e) => setParsedData({ ...parsedData, title: e.target.value })}
                            />
                        </div>

                        <div className="form-group">
                            <label className="form-label">公司名称</label>
                            <input
                                type="text"
                                className="input"
                                value={parsedData.company_name}
                                onChange={(e) => setParsedData({ ...parsedData, company_name: e.target.value })}
                            />
                        </div>

                        <div className="form-group">
                            <label className="form-label">行业</label>
                            <div className="tag" style={{ background: 'rgba(24, 144, 255, 0.1)', color: '#1890ff' }}>
                                {parsedData.suggested_industry || '未指定'}
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="form-label">标签</label>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                {allTags.map(tag => (
                                    <button
                                        key={tag.id}
                                        className="tag"
                                        style={{
                                            background: selectedTagIds.includes(tag.id) ? tag.color : 'transparent',
                                            color: selectedTagIds.includes(tag.id) ? 'white' : tag.color,
                                            border: `1px solid ${tag.color}`,
                                            cursor: 'pointer',
                                        }}
                                        onClick={() => toggleTag(tag.id)}
                                    >
                                        {tag.name}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="form-label">投递邮箱 <span style={{ color: 'red' }}>*</span></label>
                            <input
                                type="email"
                                className="input"
                                value={parsedData.apply_email || ''}
                                onChange={(e) => setParsedData({ ...parsedData, apply_email: e.target.value })}
                                placeholder="必要信息，不能为空"
                            />
                        </div>

                        {parsedData.email_subject_template && (
                            <div className="form-group">
                                <label className="form-label">邮件主题模板</label>
                                <input
                                    type="text"
                                    className="input"
                                    value={parsedData.email_subject_template}
                                    onChange={(e) => setParsedData({ ...parsedData, email_subject_template: e.target.value })}
                                />
                            </div>
                        )}

                        {parsedData.requirements && (
                            <div className="form-group">
                                <label className="form-label">任职要求</label>
                                <div style={{ fontSize: '14px', color: '#666' }}>
                                    {parsedData.requirements.education && <div>学历: {parsedData.requirements.education}</div>}
                                    {parsedData.requirements.experience && <div>经验: {parsedData.requirements.experience}</div>}
                                    {parsedData.requirements.location && <div>地点: {parsedData.requirements.location}</div>}
                                    {parsedData.requirements.salary && <div>薪资: {parsedData.requirements.salary}</div>}
                                    {parsedData.requirements.skills && (
                                        <div>技能: {parsedData.requirements.skills.join(', ')}</div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    <div style={{ display: 'flex', gap: '12px' }}>
                        <button
                            className="btn btn-primary"
                            onClick={handleSave}
                            disabled={saving}
                            style={{ flex: 1 }}
                        >
                            {saving ? <span className="spinner"></span> : ''}
                            {saving ? '保存中...' : '保存职位'}
                        </button>
                        <button
                            className="btn btn-secondary"
                            onClick={() => {
                                setParsedData(null);
                                setRawContent('');
                                setSelectedTagIds([]);
                            }}
                            disabled={saving}
                        >
                            清空
                        </button>
                    </div>
                </>
            )}
        </div>
    );
};

export default JobAddForm;
