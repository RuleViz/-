/* ==========================================
   职递AI - 前端交互逻辑 (API对接版本)
   ========================================== */

'use strict';

// ==========================================
// API 配置
// ==========================================

const API_BASE_URL = 'http://localhost:8000/api';

// API 请求封装
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  console.log('API Request:', url, options.method || 'GET');
  
  const config = {
    headers: {
      ...options.headers,
    },
    ...options,
  };

  if (!(config.body instanceof FormData)) {
    config.headers = {
      'Content-Type': 'application/json',
      ...config.headers,
    };
  }

  if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
    config.body = JSON.stringify(config.body);
  }

  try {
    const response = await fetch(url, config);
    console.log('API Response:', response.status, response.statusText);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('API Error:', errorText);
      throw new Error(errorText || `HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API请求失败:', error);
    throw error;
  }
}

// API 方法
const api = {
  // 职位相关
  getJobs: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/jobs?${query}`);
  },
  parseJob: (rawContent, sourceType = '手动') => 
    apiRequest('/jobs/parse', {
      method: 'POST',
      body: { raw_content: rawContent, source_type: sourceType },
    }),
  createJob: (jobData) => 
    apiRequest('/jobs', {
      method: 'POST',
      body: jobData,
    }),

  // 购物车相关
  getCartItems: () => apiRequest('/cart/items'),
  addToCart: (jobId) => 
    apiRequest(`/cart/items/${jobId}`, { method: 'POST' }),
  removeFromCart: (jobId) => 
    apiRequest(`/cart/items/${jobId}`, { method: 'DELETE' }),
  getCartCount: () => apiRequest('/cart/count'),
  clearCart: () => apiRequest('/cart/clear', { method: 'DELETE' }),

  // 投递相关
  getDeliveries: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/deliveries?${query}`);
  },
  prepareDelivery: (payload) =>
    apiRequest('/delivery/prepare', {
      method: 'POST',
      body: payload,
    }),
  getDeliveryJob: (jobId) => apiRequest(`/delivery/jobs/${jobId}`),
  batchDeliver: (jobIds, coverLetterStyle = 'concise') => 
    apiRequest('/deliveries/batch', {
      method: 'POST',
      body: { job_ids: jobIds, cover_letter_style: coverLetterStyle },
    }),
  getDeliveryStats: () => apiRequest('/deliveries/stats/summary'),
  getDeliveryTrends: (days = 30) => apiRequest(`/deliveries/trends/daily?days=${days}`),

  // 行业标签
  getIndustries: () => apiRequest('/industries'),
  getTags: () => apiRequest('/tags'),

  // 简历与匹配
  uploadResume: (formData, userId = 'default_user') =>
    apiRequest(`/resumes/upload?user_id=${encodeURIComponent(userId)}`, {
      method: 'POST',
      headers: {},
      body: formData,
    }),
  getResumeDetail: (resumeId) => apiRequest(`/resumes/${resumeId}`),
  searchResumes: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/resumes/search?${query}`);
  },
  aiMatch: (resumeId, topN = 3, filters = {}) =>
    apiRequest('/ai/match', {
      method: 'POST',
      body: { resume_id: resumeId, top_n: topN, filters },
    }),
  getDeliveryAnalytics: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/analytics/deliveries?${query}`);
  },
};

// ==========================================
// Mock 数据 (备用)
// ==========================================

const MOCK_JOBS = [
  {
    id: 1,
    company_name: '腾讯',
    logoColor: '#1677FF',
    logoChar: 'T',
    title: '前端开发工程师（校招）',
    city: '深圳',
    salary: '18k-28k',
    type: '校招',
    deadline: '2026-03-31',
    tags: [{name: 'React', color: '#61DAFB'}, {name: 'TypeScript', color: '#3178C6'}],
    inCart: false,
  },
  {
    id: 2,
    company_name: '字节跳动',
    logoColor: '#FF4444',
    logoChar: '字',
    title: '产品经理（校招）',
    city: '北京',
    salary: '20k-30k',
    type: '校招',
    deadline: '2026-04-10',
    tags: [{name: '产品', color: '#FF6B6B'}, {name: '数据分析', color: '#4ECDC4'}],
    inCart: false,
  },
];

const MOCK_LIBRARIES = [
  {
    id: 1,
    name: '清华大学2026春招专场',
    author: '清华就业指导中心',
    authorType: '高校认证',
    jobCount: 128,
    coverGradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    coverEmoji: '🎓',
    price: '免费',
    priceType: 'free',
    joined: true,
    isPublic: true,
  },
];

const MY_LIBRARIES = [
  {
    id: 101,
    name: '我的秋招目标公司',
    author: '张同学（我）',
    authorType: '个人',
    jobCount: 18,
    coverGradient: 'linear-gradient(135deg, #4A90E2 0%, #6BA3E8 100%)',
    coverEmoji: '⭐',
    price: '私有',
    priceType: 'private',
    joined: true,
    isPublic: false,
  },
];

const MOCK_FAQS = [
  { q: '如何将职位加入购物车？', a: '在职位广场浏览职位时，点击卡片右下角的「加入购物车」按钮即可。' },
  { q: 'AI 自荐信是如何生成的？', a: 'AI 会根据你的个人简介、技能、教育经历，结合目标职位要求，自动生成个性化自荐信。' },
  { q: '投递后如何追踪邮件状态？', a: '在「投递洞察」页面可以查看每封邮件的发送状态、对方查看时间等信息。' },
];

// ==========================================
// 全局状态
// ==========================================

const state = {
  currentPage: 'job-square',
  cart: [],
  jobs: [],
  librarySubmenuOpen: false,
  userDropdownOpen: false,
  useRealAPI: true,  // 是否使用真实API
  parsedJobData: null,  // AI解析结果
  latestResumeId: null,
  aiMatches: [],
};

// ==========================================
// 工具函数
// ==========================================

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icons = {
    success: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    error: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    info: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
    warning: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  };

  toast.innerHTML = `${icons[type] || icons.info}<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('hide');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

async function updateCartBadge() {
  try {
    const data = await api.getCartCount();
    const badge = document.getElementById('cartBadge');
    badge.textContent = data.count;
    badge.style.display = data.count > 0 ? 'flex' : 'none';
    state.cart = Array(data.count).fill(0); // 简化处理
  } catch (error) {
    console.error('获取购物车数量失败:', error);
  }
}

// ==========================================
// 导航切换
// ==========================================

function switchPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const target = document.getElementById(`page-${pageId}`);
  if (target) target.classList.add('active');

  document.querySelectorAll('.sidebar-menu-item').forEach(item => {
    item.classList.remove('active');
  });
  document.querySelectorAll('.sidebar-submenu-item').forEach(item => {
    item.classList.remove('active');
  });

  const menuItem = document.querySelector(`.sidebar-menu-item[data-page="${pageId}"]`);
  if (menuItem) {
    menuItem.classList.add('active');
  }
  const subItem = document.querySelector(`.sidebar-submenu-item[data-page="${pageId}"]`);
  if (subItem) {
    subItem.classList.add('active');
    if (!state.librarySubmenuOpen) toggleLibrarySubmenu();
  }

  state.currentPage = pageId;
  document.getElementById('mainContainer').scrollTop = 0;

  // 按需初始化页面
  if (pageId === 'cart') renderCart();
  if (pageId === 'insights') initInsightsCharts();
  if (pageId === 'support') renderFAQ();
  if (pageId === 'job-square') loadJobs();
}

function toggleLibrarySubmenu() {
  state.librarySubmenuOpen = !state.librarySubmenuOpen;
  const submenu = document.getElementById('jobLibrarySubmenu');
  const chevron = document.getElementById('libraryChevron');

  submenu.classList.toggle('expanded', state.librarySubmenuOpen);
  chevron.classList.toggle('rotated', state.librarySubmenuOpen);
}

function toggleUserDropdown() {
  state.userDropdownOpen = !state.userDropdownOpen;
  const dropdown = document.getElementById('userDropdown');
  const chevron = document.getElementById('userChevron');
  dropdown.classList.toggle('hidden', !state.userDropdownOpen);
  chevron.classList.toggle('rotated', state.userDropdownOpen);
}

function closeUserDropdown() {
  state.userDropdownOpen = false;
  document.getElementById('userDropdown').classList.add('hidden');
  document.getElementById('userChevron').classList.remove('rotated');
}

// ==========================================
// 职位广场 - API对接
// ==========================================

async function loadJobs() {
  try {
    const jobs = await api.getJobs({ limit: 50 });
    state.jobs = jobs.map(job => ({
      ...job,
      logoColor: generateLogoColor(job.company_name),
      logoChar: job.company_name ? job.company_name.charAt(0) : '?',
      city: job.requirements?.location || '未知',
      salary: job.requirements?.salary || '薪资面议',
      type: job.source_type || '校招',
      deadline: '2026-04-30',
    }));
    renderJobsGrid(state.jobs);
  } catch (error) {
    console.error('加载职位失败:', error);
    showToast('加载职位失败，使用本地数据', 'warning');
    state.jobs = MOCK_JOBS;
    renderJobsGrid(MOCK_JOBS);
  }
}

function generateLogoColor(name) {
  const colors = ['#1677FF', '#FF4444', '#FF6A00', '#FFAB00', '#CC0000', '#2932E1', '#FF2442', '#00AEEC', '#CF0A2C', '#00A4EF'];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

function renderJobsGrid(jobs) {
  const grid = document.getElementById('jobsGrid');
  const stats = document.getElementById('jobStats');

  stats.innerHTML = `共 <strong>${jobs.length}</strong> 个职位`;

  if (jobs.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#BDC3C7" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
        <p>没有找到符合条件的职位</p>
      </div>`;
    return;
  }

  grid.innerHTML = jobs.map(job => `
    <div class="job-card" data-job-id="${job.id}">
      <div class="job-card-header">
        <div class="company-logo" style="background:${job.logoColor}">${job.logoChar}</div>
        <div>
          <div class="company-name">${job.company_name}</div>
          <span class="tag-gray">${job.type}</span>
        </div>
      </div>
      <div class="job-title">${job.title}</div>
      <div class="job-meta">
        <span class="job-meta-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>
          </svg>
          ${job.city}
        </span>
        <span class="job-meta-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="1" x2="12" y2="23"/>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
          </svg>
          ${job.salary}
        </span>
      </div>
      <div class="job-tags">
        ${(job.tags || []).map(t => `<span class="tag-primary" style="background:${t.color}20;color:${t.color};border-color:${t.color}40">${t.name}</span>`).join('')}
      </div>
      <div class="job-card-footer">
        <span class="job-deadline">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
          </svg>
          截止 ${job.deadline}
        </span>
        <button class="btn-add-cart ${job.inCart ? 'in-cart' : ''}" data-job-id="${job.id}">
          ${job.inCart ? '✓ 已加入' : '+ 加入购物车'}
        </button>
      </div>
    </div>
  `).join('');
}

function filterJobs() {
  const search = document.getElementById('jobSearchInput').value.toLowerCase();
  const city = document.getElementById('cityFilter').value;
  const type = document.getElementById('typeFilter').value;

  const filtered = state.jobs.filter(job => {
    const matchSearch = !search ||
      job.title?.toLowerCase().includes(search) ||
      job.company_name?.toLowerCase().includes(search);
    const matchCity = !city || job.city === city;
    const matchType = !type || job.type === type;
    return matchSearch && matchCity && matchType;
  });

  renderJobsGrid(filtered);
}

async function addToCart(jobId) {
  try {
    await api.addToCart(jobId);
    showToast('已加入购物车', 'success');
    updateCartBadge();
    
    // 更新本地状态
    const job = state.jobs.find(j => j.id === jobId);
    if (job) job.inCart = true;
    renderJobsGrid(state.jobs);
  } catch (error) {
    showToast('加入购物车失败: ' + error.message, 'error');
  }
}

// ==========================================
// AI 解析职位弹窗
// ==========================================

function initAiParseModal() {
  const modal = document.getElementById('aiParseModal');
  const openBtn = document.getElementById('aiParseBtn');
  const closeBtn = document.getElementById('closeAiParseModal');
  const cancelBtn = document.getElementById('cancelAiParse');
  const confirmBtn = document.getElementById('confirmAiParse');
  const input = document.getElementById('aiParseInput');
  const resultDiv = document.getElementById('aiParseResult');
  const spinner = document.getElementById('aiParseSpinner');
  const btnText = document.getElementById('aiParseBtnText');

  // 打开弹窗
  openBtn.addEventListener('click', () => {
    modal.classList.remove('hidden');
    input.value = '';
    resultDiv.classList.add('hidden');
    confirmBtn.disabled = false;
    btnText.textContent = 'AI 解析';
    state.parsedJobData = null;
  });

  // 关闭弹窗
  function closeModal() {
    modal.classList.add('hidden');
  }

  closeBtn.addEventListener('click', closeModal);
  cancelBtn.addEventListener('click', closeModal);

  // 点击遮罩关闭
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });

  // AI 解析
  confirmBtn.addEventListener('click', async () => {
    const content = input.value.trim();
    if (!content) {
      showToast('请输入职位发布内容', 'warning');
      return;
    }

    // 显示加载状态
    spinner.classList.remove('hidden');
    btnText.textContent = '解析中...';
    confirmBtn.disabled = true;

    try {
      if (state.parsedJobData) {
        // 已解析，执行保存
        await saveParsedJob();
      } else {
        // 执行解析
        const result = await api.parseJob(content);
        state.parsedJobData = result;
        
        // 显示解析结果
        document.getElementById('parsedTitle').value = result.title || '';
        document.getElementById('parsedCompany').value = result.company_name || '';
        document.getElementById('parsedEmail').value = result.apply_email || '';
        document.getElementById('parsedIndustry').value = result.suggested_industry || '未识别';
        
        resultDiv.classList.remove('hidden');
        btnText.textContent = '保存职位';
        confirmBtn.disabled = false;
        
        showToast('AI 解析成功，请确认信息后保存', 'success');
      }
    } catch (error) {
      showToast('解析失败: ' + error.message, 'error');
      btnText.textContent = 'AI 解析';
      confirmBtn.disabled = false;
    } finally {
      spinner.classList.add('hidden');
    }
  });

  // 输入框变化时重置状态
  input.addEventListener('input', () => {
    if (state.parsedJobData) {
      state.parsedJobData = null;
      resultDiv.classList.add('hidden');
      btnText.textContent = 'AI 解析';
    }
  });
}

async function saveParsedJob() {
  const title = document.getElementById('parsedTitle').value.trim();
  const email = document.getElementById('parsedEmail').value.trim();
  
  if (!title) {
    showToast('职位名称不能为空', 'error');
    return;
  }
  if (!email) {
    showToast('投递邮箱不能为空', 'error');
    return;
  }

  const jobData = {
    title: title,
    company_name: document.getElementById('parsedCompany').value.trim(),
    apply_email: email,
    industry_name: state.parsedJobData.suggested_industry,
    email_subject_template: state.parsedJobData.email_subject_template,
    email_body_template: state.parsedJobData.email_body_template,
    requirements: state.parsedJobData.requirements,
    source_type: 'AI解析',
    raw_content: document.getElementById('aiParseInput').value.trim(),
    status: 'active',
    tag_ids: [],
  };

  try {
    await api.createJob(jobData);
    showToast('职位保存成功！', 'success');
    document.getElementById('aiParseModal').classList.add('hidden');
    loadJobs(); // 刷新职位列表
  } catch (error) {
    showToast('保存失败: ' + error.message, 'error');
  }
}

// ==========================================
// 职位库渲染
// ==========================================

function renderLibraryGrid(containerId, libraries) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (libraries.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#BDC3C7" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <ellipse cx="12" cy="5" rx="9" ry="3"/>
          <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
        </svg>
        <p>暂无职位库</p>
      </div>`;
    return;
  }

  container.innerHTML = libraries.map(lib => {
    const actionBtn = lib.joined
      ? `<button class="btn-secondary btn-sm" onclick="showToast('已进入「${lib.name}」', 'info')">查看职位</button>`
      : lib.priceType === 'free'
        ? `<button class="btn-primary btn-sm" onclick="joinLibrary(${lib.id})">免费加入</button>`
        : `<button class="btn-accent btn-sm" onclick="joinLibrary(${lib.id})">${lib.price} 解锁</button>`;

    return `
      <div class="library-card">
        <div class="library-cover" style="background:${lib.coverGradient}">
          <span class="library-cover-icon">${lib.coverEmoji}</span>
          <div class="library-cover-overlay"></div>
        </div>
        <div class="library-body">
          <div class="library-name">${lib.name}</div>
          <div class="library-author">
            ${lib.author}
            ${lib.authorType !== '个人' ? `<span class="tag-success" style="margin-left:4px">${lib.authorType}</span>` : ''}
          </div>
        </div>
        <div class="library-footer">
          <div class="library-stats">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;margin-right:3px">
              <rect width="20" height="14" x="2" y="7" rx="2" ry="2"/>
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
            </svg>
            ${lib.jobCount} 个职位
            ${lib.joined ? '<span class="tag-success" style="margin-left:6px">已加入</span>' : ''}
          </div>
          ${actionBtn}
        </div>
      </div>`;
  }).join('');
}

function joinLibrary(libId) {
  const lib = [...MOCK_LIBRARIES, ...MY_LIBRARIES].find(l => l.id === libId);
  if (lib) {
    lib.joined = true;
    showToast(`成功加入「${lib.name}」！`, 'success');
    renderLibraryGrid('discoverLibraryGrid', MOCK_LIBRARIES);
    renderLibraryGrid('joinedLibraryGrid', MOCK_LIBRARIES.filter(l => l.joined));
  }
}

// ==========================================
// 购物车渲染 - API对接
// ==========================================

async function renderCart() {
  const list = document.getElementById('cartJobsList');
  const empty = document.getElementById('cartEmpty');
  const countLabel = document.getElementById('cartCountLabel');

  try {
    const cartJobs = await api.getCartItems();
    countLabel.textContent = `共 ${cartJobs.length} 个`;

    if (cartJobs.length === 0) {
      list.innerHTML = '';
      empty.classList.remove('hidden');
      return;
    }

    empty.classList.add('hidden');
    list.innerHTML = cartJobs.map(job => `
      <div class="cart-job-item">
        <div class="company-logo" style="background:${generateLogoColor(job.company_name)};width:36px;height:36px;font-size:14px;border-radius:6px;flex-shrink:0">
          ${job.company_name ? job.company_name.charAt(0) : '?'}
        </div>
        <div class="cart-job-info">
          <div class="cart-job-title">${job.title}</div>
          <div class="cart-job-company">
            ${job.company_name} · ${job.requirements?.location || '未知'} · ${job.requirements?.salary || '薪资面议'}
          </div>
        </div>
        <span class="tag-gray">${job.source_type || '校招'}</span>
        <button class="btn-icon" onclick="removeFromCart(${job.id})" title="移除">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
          </svg>
        </button>
      </div>
    `).join('');
  } catch (error) {
    console.error('加载购物车失败:', error);
    showToast('加载购物车失败', 'error');
  }
}

async function removeFromCart(jobId) {
  try {
    await api.removeFromCart(jobId);
    showToast('已从购物车移除', 'info');
    updateCartBadge();
    renderCart();
  } catch (error) {
    showToast('移除失败: ' + error.message, 'error');
  }
}

// ==========================================
// 投递洞察 - API对接
// ==========================================

let trendChartInstance = null;
let statusChartInstance = null;

async function initInsightsCharts() {
  try {
    const [dayAnalytics, statusAnalytics, deliveries] = await Promise.all([
      api.getDeliveryAnalytics({ group_by: 'day' }),
      api.getDeliveryAnalytics({ group_by: 'status' }),
      api.getDeliveries({ limit: 10 })
    ]);

    const trends = (dayAnalytics.items || []).map(item => ({ date: item.key, count: item.count }));
    const statusMap = Object.fromEntries((statusAnalytics.items || []).map(item => [item.key, item.count]));
    const stats = {
      total_count: dayAnalytics.total || 0,
      viewed_count: statusMap.viewed || 0,
      interview_count: statusMap.interview || 0,
      hired_count: statusMap.hired || 0,
      rejected_count: statusMap.rejected || 0,
    };
    
    renderInsightsTable(deliveries);
    renderStatsCards(stats);
    renderCharts(trends, stats);
  } catch (error) {
    console.error('加载投递洞察失败:', error);
    // 使用Mock数据
    renderMockInsights();
  }
}

function renderStatsCards(stats) {
  // 更新统计卡片
  const cards = document.querySelectorAll('.stat-value');
  if (cards.length >= 4) {
    cards[0].textContent = stats.total_count;
    cards[1].textContent = stats.viewed_count;
    cards[2].textContent = stats.interview_count;
    cards[3].textContent = stats.hired_count;
  }
}

function renderCharts(trends, stats) {
  // 避免重复初始化
  if (trendChartInstance) trendChartInstance.destroy();
  if (statusChartInstance) statusChartInstance.destroy();

  if (typeof Chart === 'undefined') {
    document.getElementById('trendChart').parentElement.innerHTML =
      '<p style="color:#7F8C8D;text-align:center;padding:40px">图表加载中...</p>';
    return;
  }

  // 趋势折线图
  const trendCtx = document.getElementById('trendChart').getContext('2d');
  const labels = trends.map(t => {
    const date = new Date(t.date);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  });
  const data = trends.map(t => t.count);

  trendChartInstance = new Chart(trendCtx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: '每日投递数',
        data,
        borderColor: '#4A90E2',
        backgroundColor: 'rgba(74, 144, 226, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#4A90E2',
        pointRadius: 3,
        pointHoverRadius: 5,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          ticks: { maxTicksLimit: 8, font: { size: 12 }, color: '#7F8C8D' },
          grid: { color: '#ECF0F1' },
        },
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1, font: { size: 12 }, color: '#7F8C8D' },
          grid: { color: '#ECF0F1' },
        },
      },
    }
  });

  // 状态环形图
  const statusCtx = document.getElementById('statusChart').getContext('2d');
  const statusData = [
    { label: '已录用', value: stats.hired_count, color: '#2ECC71' },
    { label: '面试邀约', value: stats.interview_count, color: '#F39C12' },
    { label: '已查看', value: stats.viewed_count, color: '#4A90E2' },
    { label: '未查看', value: stats.total_count - stats.viewed_count, color: '#BDC3C7' },
    { label: '已拒绝', value: stats.rejected_count, color: '#E74C3C' },
  ];

  statusChartInstance = new Chart(statusCtx, {
    type: 'doughnut',
    data: {
      labels: statusData.map(d => d.label),
      datasets: [{
        data: statusData.map(d => d.value),
        backgroundColor: statusData.map(d => d.color),
        borderWidth: 2,
        borderColor: '#FFFFFF',
        hoverOffset: 4,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.raw} 封`
          }
        }
      },
      cutout: '65%',
    }
  });

  // 图例
  const legendContainer = document.getElementById('statusLegend');
  legendContainer.innerHTML = statusData.map(d => `
    <div class="legend-item">
      <span class="legend-dot" style="background:${d.color}"></span>
      <span>${d.label}</span>
      <span style="margin-left:auto;font-weight:600;color:#2C3E50">${d.value}</span>
    </div>
  `).join('');
}

function renderInsightsTable(deliveries) {
  const tbody = document.getElementById('insightsTableBody');
  const statusMap = {
    pending: '<span class="status-badge status-pending">待发送</span>',
    sent: '<span class="status-badge status-sent">已发送</span>',
    delivered: '<span class="status-badge status-sent">已送达</span>',
    viewed: '<span class="status-badge status-viewed">已查看</span>',
    replied: '<span class="status-badge status-interview">已回复</span>',
    interview: '<span class="status-badge status-interview">面试邀约</span>',
    rejected: '<span class="status-badge status-rejected">已拒绝</span>',
    hired: '<span class="status-badge" style="background:#2ECC20;color:#fff">已录用</span>',
  };

  tbody.innerHTML = deliveries.map(item => `
    <tr>
      <td><strong>${item.job?.company_name || '未知'}</strong></td>
      <td>${item.job?.title || '未知职位'}</td>
      <td style="color:#7F8C8D;font-size:13px">${item.created_at ? new Date(item.created_at).toLocaleString('zh-CN') : '-'}</td>
      <td>${statusMap[item.status] || item.status}</td>
      <td style="font-size:13px;color:#7F8C8D">${item.viewed_at ? new Date(item.viewed_at).toLocaleString('zh-CN') : '—'}</td>
    </tr>
  `).join('');
}

function renderMockInsights() {
  // Mock数据渲染
  const MOCK_INSIGHTS = [
    { company: '腾讯', position: '前端工程师', time: '2026-02-15 14:32', status: 'viewed', viewTime: '2月15日 15:41' },
    { company: '字节跳动', position: '产品经理', time: '2026-02-14 10:20', status: 'interview', viewTime: '2月14日 11:05' },
  ];
  
  const tbody = document.getElementById('insightsTableBody');
  const statusMap = {
    sent: '<span class="status-badge status-sent">已发送</span>',
    viewed: '<span class="status-badge status-viewed">已查看</span>',
    interview: '<span class="status-badge status-interview">面试邀约</span>',
    rejected: '<span class="status-badge status-rejected">已拒绝</span>',
    pending: '<span class="status-badge status-pending">待发送</span>',
  };

  tbody.innerHTML = MOCK_INSIGHTS.map(item => `
    <tr>
      <td><strong>${item.company}</strong></td>
      <td>${item.position}</td>
      <td style="color:#7F8C8D;font-size:13px">${item.time}</td>
      <td>${statusMap[item.status] || ''}</td>
      <td style="font-size:13px;color:#7F8C8D">${item.viewTime}</td>
    </tr>
  `).join('');
}

// ==========================================
// 客服 FAQ
// ==========================================

function renderFAQ() {
  const list = document.getElementById('faqList');
  list.innerHTML = MOCK_FAQS.map((faq, i) => `
    <div class="faq-item" id="faq-${i}">
      <div class="faq-question" onclick="toggleFAQ(${i})">
        <span>${faq.q}</span>
        <svg class="faq-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </div>
      <div class="faq-answer">${faq.a}</div>
    </div>
  `).join('');
}

function toggleFAQ(index) {
  const item = document.getElementById(`faq-${index}`);
  item.classList.toggle('open');
}

// ==========================================
// 材料页面 Tabs
// ==========================================

function initMaterialsTabs() {
  const tabs = document.getElementById('materialsTabs');
  tabs.addEventListener('click', (e) => {
    const tab = e.target.closest('.tab');
    if (!tab) return;
    const tabId = tab.dataset.tab;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    const panel = document.getElementById(`tab-${tabId}`);
    if (panel) panel.classList.add('active');
  });
}

async function loadResumeList() {
  const container = document.getElementById('resumeListContainer');
  if (!container) return;

  try {
    const data = await api.searchResumes({ page: 1, page_size: 10 });
    const items = data.items || [];

    if (items.length === 0) {
      container.innerHTML = '<div class="resume-item"><div class="resume-info"><span class="resume-name">暂无简历，请先上传</span></div></div>';
      return;
    }

    state.latestResumeId = items[0].id;
    container.innerHTML = items.map((item, idx) => `
      <div class="resume-item">
        <div class="resume-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#E74C3C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
        </div>
        <div class="resume-info">
          <span class="resume-name">${item.filename}</span>
          <span class="resume-meta">状态: ${item.status} · 上传于 ${new Date(item.uploaded_at).toLocaleString('zh-CN')}</span>
        </div>
        ${idx === 0 ? '<span class="tag-success">默认简历</span>' : ''}
      </div>
    `).join('');
  } catch (error) {
    console.error('加载简历列表失败:', error);
  }
}

async function handleResumeUpload(file) {
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);

  try {
    showToast('正在上传并解析简历...', 'info');
    const uploaded = await api.uploadResume(formData);
    state.latestResumeId = uploaded.resume_id;

    const detail = await api.getResumeDetail(uploaded.resume_id);
    const parsedFields = detail?.parsed?.extracted_fields || {};
    const parseText = document.getElementById('resumeParseText');
    const parsePanel = document.getElementById('resumeParseResult');

    parseText.textContent = `姓名: ${parsedFields.name || '-'}；邮箱: ${parsedFields.email || '-'}；技能: ${(parsedFields.skills || []).join(', ') || '-'}`;
    parsePanel.style.display = 'block';

    await loadResumeList();
    showToast('简历上传并解析成功', 'success');
  } catch (error) {
    showToast('简历上传失败: ' + error.message, 'error');
  }
}

async function triggerAiMatch() {
  if (!state.latestResumeId) {
    showToast('请先上传并解析简历', 'warning');
    return;
  }

  try {
    const matches = await api.aiMatch(state.latestResumeId, 3, {});
    state.aiMatches = matches;
    const el = document.getElementById('aiMatchResultText');
    if (matches.length === 0) {
      el.textContent = '暂无可匹配职位';
      return;
    }

    el.textContent = matches
      .map(item => `职位#${item.job_id} 匹配分 ${Math.round(item.score)}，${(item.highlights || []).join('；')}`)
      .join(' | ');
    showToast('AI 匹配完成，可直接发起准备投递', 'success');
  } catch (error) {
    showToast('AI 匹配失败: ' + error.message, 'error');
  }
}

// ==========================================
// 事件绑定
// ==========================================

function bindEvents() {
  // Logo 点击返回首页
  document.getElementById('logoBtn').addEventListener('click', () => switchPage('job-square'));

  // 主菜单项点击
  document.getElementById('sidebarNav').addEventListener('click', (e) => {
    const item = e.target.closest('.sidebar-menu-item[data-page]');
    if (item) {
      switchPage(item.dataset.page);
      return;
    }
    if (e.target.closest('#jobLibraryToggle')) {
      toggleLibrarySubmenu();
    }
    const subItem = e.target.closest('.sidebar-submenu-item[data-page]');
    if (subItem) {
      switchPage(subItem.dataset.page);
    }
  });

  // 底部菜单点击
  document.querySelector('.sidebar-bottom').addEventListener('click', (e) => {
    const menuItem = e.target.closest('.sidebar-menu-item[data-page]');
    if (menuItem) {
      switchPage(menuItem.dataset.page);
      closeUserDropdown();
      return;
    }
    if (e.target.closest('#userAvatarBtn')) {
      toggleUserDropdown();
      return;
    }
    if (e.target.closest('#logoutBtn')) {
      showToast('已退出登录', 'info');
      closeUserDropdown();
    }
    if (e.target.closest('#privilegeBtn')) {
      showToast('Pro 会员：有效期至 2026-12-31', 'success');
      closeUserDropdown();
    }
    if (e.target.closest('#settingsBtn')) {
      showToast('账号设置功能即将上线', 'info');
      closeUserDropdown();
    }
  });

  // 点击外部关闭下拉菜单
  document.addEventListener('click', (e) => {
    if (state.userDropdownOpen &&
      !e.target.closest('#userAvatarBtn') &&
      !e.target.closest('#userDropdown')) {
      closeUserDropdown();
    }
  });

  // 职位广场 - 搜索 & 筛选
  document.getElementById('jobSearchInput').addEventListener('input', filterJobs);
  document.getElementById('cityFilter').addEventListener('change', filterJobs);
  document.getElementById('typeFilter').addEventListener('change', filterJobs);
  document.getElementById('resetFilterBtn').addEventListener('click', () => {
    document.getElementById('jobSearchInput').value = '';
    document.getElementById('cityFilter').value = '';
    document.getElementById('typeFilter').value = '';
    filterJobs();
  });

  // 职位卡片：加入购物车
  document.getElementById('jobsGrid').addEventListener('click', (e) => {
    const btn = e.target.closest('.btn-add-cart');
    if (btn) {
      e.stopPropagation();
      addToCart(Number(btn.dataset.jobId));
    }
  });

  // 购物车：一键投递
  document.getElementById('submitCartBtn').addEventListener('click', async () => {
    try {
      const cartJobs = await api.getCartItems();
      if (cartJobs.length === 0) {
        showToast('购物车是空的，请先添加职位', 'warning');
        return;
      }
      
      const jobIds = cartJobs.map(j => j.id);
      const coverStyle = document.getElementById('coverLetterStyle').value;

      if (!state.latestResumeId) {
        showToast('请先在投递资料上传并解析简历', 'warning');
        return;
      }
      
      showToast(`正在准备 ${cartJobs.length} 份模拟投递...`, 'info');
      await api.prepareDelivery({
        user_id: 'default_user',
        resume_id: state.latestResumeId,
        job_ids: jobIds,
        config: {
          cover_letter_style: coverStyle,
          subject_template: document.getElementById('emailSubject').value,
          template_name: 'default_template',
          attachments: ['简历.pdf']
        }
      });
      showToast(`🎉 成功记录 ${cartJobs.length} 个模拟投递！`, 'success');
      
      updateCartBadge();
      renderCart();
    } catch (error) {
      showToast('投递失败: ' + error.message, 'error');
    }
  });

  const selectResumeBtn = document.getElementById('selectResumeFileBtn');
  const resumeInput = document.getElementById('resumeFileInput');
  if (selectResumeBtn && resumeInput) {
    selectResumeBtn.addEventListener('click', () => resumeInput.click());
    resumeInput.addEventListener('change', async (e) => {
      const file = e.target.files?.[0];
      await handleResumeUpload(file);
      e.target.value = '';
    });
  }

  const aiMatchBtn = document.getElementById('aiMatchCartBtn');
  if (aiMatchBtn) {
    aiMatchBtn.addEventListener('click', triggerAiMatch);
  }

  // 创建新库
  document.getElementById('createLibraryBtn').addEventListener('click', () => {
    showToast('创建职位库功能即将上线', 'info');
  });

  // 保存资料
  document.getElementById('saveMaterialsBtn').addEventListener('click', () => {
    showToast('资料保存成功！', 'success');
  });

  // 新增自荐信模板
  document.getElementById('addTemplateBtn').addEventListener('click', () => {
    showToast('模板编辑器即将上线', 'info');
  });
}

// ==========================================
// 初始化
// ==========================================

function init() {
  // 加载职位列表
  loadJobs();

  // 渲染职位库
  renderLibraryGrid('discoverLibraryGrid', MOCK_LIBRARIES);
  renderLibraryGrid('joinedLibraryGrid', MOCK_LIBRARIES.filter(l => l.joined));
  renderLibraryGrid('myLibraryGrid', MY_LIBRARIES);

  // 初始化材料页 Tabs
  initMaterialsTabs();
  loadResumeList();

  // 初始化AI解析弹窗
  initAiParseModal();

  // 绑定事件
  bindEvents();

  // 初始化购物车徽标
  updateCartBadge();

  console.log('职递AI 前端初始化完成 ✓');
}

// DOM 加载完成后执行
document.addEventListener('DOMContentLoaded', init);
