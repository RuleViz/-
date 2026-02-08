import React, { useState, useEffect } from 'react';
import * as api from '../api';

interface JobListProps {
    refreshTrigger?: number;
}

const JobList: React.FC<JobListProps> = ({ refreshTrigger }) => {
    const [jobs, setJobs] = useState<api.Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState({
        status: '',
        industry_id: null as number | null,
    });

    useEffect(() => {
        loadJobs();
    }, [refreshTrigger, filter]);

    const loadJobs = async () => {
        setLoading(true);
        try {
            const data = await api.getJobs(filter.status ? { status: filter.status } : {});
            setJobs(data);
        } catch (error) {
            console.error('Failed to load jobs:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('确定要删除此职位吗？')) return;

        try {
            await api.deleteJob(id);
            setJobs(jobs.filter(job => job.id !== id));
        } catch (error) {
            alert('删除职位失败');
        }
    };

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString('zh-CN');
    };

    if (loading) {
        return (
            <div className="flex-center" style={{ padding: '60px' }}>
                <div className="spinner" style={{ width: '40px', height: '40px', borderWidth: '3px' }}></div>
            </div>
        );
    }

    return (
        <div>
            <div className="flex-between" style={{ marginBottom: '24px' }}>
                <h2>职位列表 ({jobs.length})</h2>
                <div style={{ display: 'flex', gap: '12px' }}>
                    <select
                        className="select"
                        value={filter.status}
                        onChange={(e) => setFilter({ ...filter, status: e.target.value })}
                        style={{ width: 'auto' }}
                    >
                        <option value="">所有状态</option>
                        <option value="active">启用</option>
                        <option value="draft">草稿</option>
                        <option value="expired">过期</option>
                    </select>
                </div>
            </div>

            {jobs.length === 0 ? (
                <div className="card text-center" style={{ padding: '60px' }}>
                    <p style={{ fontSize: '48px', marginBottom: '16px' }}>📭</p>
                    <p style={{ color: '#7F8C8D' }}>未找到职位，请添加您的第一个职位！</p>
                </div>
            ) : (
                <div className="grid grid-2">
                    {jobs.map(job => (
                        <div key={job.id} className="card">
                            <div className="flex-between" style={{ marginBottom: '12px' }}>
                                <h3 style={{ fontSize: '1.2rem', margin: 0 }}>{job.title}</h3>
                                <span
                                    className="tag"
                                    style={{
                                        background: job.status === 'active' ? 'rgba(82, 196, 26, 0.1)' : 'rgba(191, 191, 191, 0.1)',
                                        color: job.status === 'active' ? '#52c41a' : '#999',
                                    }}
                                >
                                    {job.status}
                                </span>
                            </div>

                            <p style={{ color: '#7F8C8D', marginBottom: '12px' }}>
                                {job.company_name}
                            </p>

                            {job.industry_name && (
                                <div style={{ marginBottom: '12px' }}>
                                    <span className="tag" style={{ background: 'rgba(114, 46, 209, 0.1)', color: '#722ed1' }}>
                                        {job.industry_name}
                                    </span>
                                </div>
                            )}

                            {job.tags.length > 0 && (
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '12px' }}>
                                    {job.tags.map(tag => (
                                        <span
                                            key={tag.id}
                                            className="tag"
                                            style={{ background: `${tag.color}20`, color: tag.color }}
                                        >
                                            {tag.name}
                                        </span>
                                    ))}
                                </div>
                            )}

                            {job.requirements && (
                                <div style={{ fontSize: '13px', color: '#95A5A6', marginBottom: '12px' }}>
                                    {job.requirements.location && <div>地点: {job.requirements.location}</div>}
                                    {job.requirements.salary && <div>薪资: {job.requirements.salary}</div>}
                                </div>
                            )}

                            <div style={{ fontSize: '12px', color: '#BDC3C7', marginBottom: '12px' }}>
                                添加于 {formatDate(job.created_at)}
                            </div>

                            <div style={{ display: 'flex', gap: '8px', paddingTop: '12px', borderTop: '1px solid #E8ECEF' }}>
                                <button
                                    className="btn btn-secondary"
                                    style={{ flex: 1, padding: '8px 12px', fontSize: '13px' }}
                                >
                                    编辑
                                </button>
                                <button
                                    className="btn btn-ghost"
                                    style={{ padding: '8px 12px', fontSize: '13px', color: '#E74C3C' }}
                                    onClick={() => handleDelete(job.id)}
                                >
                                    删除
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default JobList;
