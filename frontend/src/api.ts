import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Types
export interface Industry {
    id: number;
    code: string;
    name: string;
    parent_id: number | null;
    sort_order: number;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface Tag {
    id: number;
    code: string;
    name: string;
    category: string;
    color: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface Job {
    id: number;
    title: string;
    company_name: string;
    industry_id: number | null;
    industry_name: string | null;
    apply_email: string | null;
    email_subject_template: string | null;
    email_body_template: string | null;
    requirements: any;
    source_url: string | null;
    source_type: string | null;
    raw_content: string | null;
    published_at: string | null;
    status: string;
    created_at: string;
    updated_at: string;
    tags: Tag[];
}

export interface LLMParseResponse {
    title: string;
    company_name: string;
    suggested_industry: string | null;
    suggested_industry_code: string | null;
    suggested_tags: Array<{
        name: string;
        category: string;
        color?: string;
    }>;
    apply_email: string | null;
    email_subject_template: string | null;
    email_body_template: string | null;
    requirements: any;
    published_at: string | null;
}

export interface LLMConfig {
    api_key: string;
    base_url: string;
    model: string;
}

// API Functions

// Jobs
export const parseJobPosting = async (rawContent: string, sourceType: string = '手动'): Promise<LLMParseResponse> => {
    const response = await api.post('/jobs/parse', { raw_content: rawContent, source_type: sourceType });
    return response.data;
};

export const createJob = async (jobData: any): Promise<Job> => {
    const response = await api.post('/jobs', jobData);
    return response.data;
};

export const getJobs = async (params?: any): Promise<Job[]> => {
    const response = await api.get('/jobs', { params });
    return response.data;
};

export const getJob = async (id: number): Promise<Job> => {
    const response = await api.get(`/jobs/${id}`);
    return response.data;
};

export const updateJob = async (id: number, jobData: any): Promise<Job> => {
    const response = await api.put(`/jobs/${id}`, jobData);
    return response.data;
};

export const deleteJob = async (id: number): Promise<void> => {
    await api.delete(`/jobs/${id}`);
};

// Industries
export const getIndustries = async (): Promise<Industry[]> => {
    const response = await api.get('/industries');
    return response.data;
};

export const createIndustry = async (industryData: any): Promise<Industry> => {
    const response = await api.post('/industries', industryData);
    return response.data;
};

// Tags
export const getTags = async (category?: string): Promise<Tag[]> => {
    const response = await api.get('/tags', { params: { category } });
    return response.data;
};

export const createTag = async (tagData: any): Promise<Tag> => {
    const response = await api.post('/tags', tagData);
    return response.data;
};

// LLM Config
export const saveLLMConfig = async (config: LLMConfig): Promise<any> => {
    const response = await api.post('/config/llm', config);
    return response.data;
};

export const getLLMConfig = async (): Promise<any> => {
    const response = await api.get('/config/llm');
    return response.data;
};

export const testLLMConnection = async (): Promise<any> => {
    const response = await api.post('/config/llm/test');
    return response.data;
};

export default api;
