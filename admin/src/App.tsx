import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileText, MessageSquare, BarChart3, LogOut, Lock, CheckCircle, XCircle, RefreshCw, Edit2, Trash2, Eye } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const API_BASE = 'http://localhost:8000';

interface Software {
  id: number;
  name: string;
  display_name: string;
  description: string;
  category: string;
  source_type: string;
}

interface InstallPlan {
  id: number;
  software_id: number;
  version_id: number;
  platform: string;
  plan_content: string;
  script_powershell: string;
  script_bash: string;
  software_name: string;
  display_name: string;
  version: string;
  created_at: string;
  updated_at: string;
}

interface Feedback {
  id: number;
  software_id: number;
  plan_id: number;
  is_valid: boolean;
  comment: string;
  platform: string;
  software_name: string;
  display_name: string;
  created_at: string;
}

interface Stats {
  software_stats: { name: string; count: number }[];
  platform_stats: { platform: string; count: number }[];
  feedback_stats: { valid: number; invalid: number };
}

// 登录页面
function LoginPage({ onLogin }: { onLogin: (token: string) => void }) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const resp = await fetch(`${API_BASE}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });
      
      if (resp.ok) {
        const data = await resp.json();
        localStorage.setItem('admin_token', data.token);
        onLogin(data.token);
      } else {
        setError('密码错误');
      }
    } catch (err) {
      setError('连接失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-20 h-20 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center text-4xl font-bold mx-auto mb-4">
            装
          </div>
          <h1 className="text-3xl font-bold text-white">装了吗</h1>
          <p className="text-gray-400 mt-2">管理后台</p>
        </div>
        
        <form onSubmit={handleLogin} className="bg-white/5 border border-white/10 rounded-2xl p-8">
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-400 mb-2">
              管理密码
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="请输入管理密码"
                className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
          
          {error && (
            <p className="text-red-400 text-sm mb-4">{error}</p>
          )}
          
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl font-medium text-white hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {loading ? '登录中...' : '登录'}
          </button>
        </form>
      </div>
    </div>
  );
}

// 侧边栏
function Sidebar() {
  const location = useLocation();
  
  const menuItems = [
    { path: '/', icon: LayoutDashboard, label: '仪表盘' },
    { path: '/plans', icon: FileText, label: '方案管理' },
    { path: '/feedback', icon: MessageSquare, label: '反馈管理' },
    { path: '/stats', icon: BarChart3, label: '统计分析' },
  ];
  
  return (
    <div className="w-64 bg-slate-900 border-r border-white/10 min-h-screen">
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center text-lg font-bold">
            装
          </div>
          <div>
            <h2 className="font-bold text-white">装了吗</h2>
            <p className="text-xs text-gray-400">管理后台</p>
          </div>
        </div>
      </div>
      
      <nav className="p-4 space-y-2">
        {menuItems.map(item => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                isActive
                  ? 'bg-purple-500/20 text-purple-400'
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

// 仪表盘
function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  
  useEffect(() => {
    loadStats();
  }, []);
  
  const loadStats = async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/stats`);
      const data = await resp.json();
      setStats(data);
    } catch (err) {
      console.error('加载统计失败:', err);
    }
  };
  
  if (!stats) {
    return <div className="p-8 text-gray-400">加载中...</div>;
  }
  
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-white mb-8">仪表盘</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">有效反馈</p>
              <p className="text-3xl font-bold text-green-400">{stats.feedback_stats.valid}</p>
            </div>
            <CheckCircle className="w-10 h-10 text-green-400/20" />
          </div>
        </div>
        
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">无效反馈</p>
              <p className="text-3xl font-bold text-red-400">{stats.feedback_stats.invalid}</p>
            </div>
            <XCircle className="w-10 h-10 text-red-400/20" />
          </div>
        </div>
        
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">总生成次数</p>
              <p className="text-3xl font-bold text-purple-400">
                {stats.software_stats.reduce((sum, s) => sum + s.count, 0)}
              </p>
            </div>
            <BarChart3 className="w-10 h-10 text-purple-400/20" />
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">热门软件</h3>
          <div className="space-y-3">
            {stats.software_stats.slice(0, 5).map((s, i) => (
              <div key={i} className="flex items-center justify-between">
                <span className="text-gray-300">{s.name}</span>
                <span className="text-purple-400 font-medium">{s.count}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">平台分布</h3>
          <div className="space-y-3">
            {stats.platform_stats.map((p, i) => (
              <div key={i} className="flex items-center justify-between">
                <span className="text-gray-300">{p.platform}</span>
                <span className="text-pink-400 font-medium">{p.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// 方案管理
function PlansManager() {
  const [plans, setPlans] = useState<InstallPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingPlan, setEditingPlan] = useState<InstallPlan | null>(null);
  const [editContent, setEditContent] = useState('');
  
  useEffect(() => {
    loadPlans();
  }, []);
  
  const loadPlans = async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/admin/plans`);
      const data = await resp.json();
      setPlans(data.results);
    } catch (err) {
      console.error('加载方案失败:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这个方案吗？')) return;
    
    try {
      await fetch(`${API_BASE}/api/admin/plans/${id}`, { method: 'DELETE' });
      loadPlans();
    } catch (err) {
      console.error('删除失败:', err);
    }
  };
  
  const handleEdit = (plan: InstallPlan) => {
    setEditingPlan(plan);
    setEditContent(plan.plan_content);
  };
  
  const handleSaveEdit = async () => {
    if (!editingPlan) return;
    
    try {
      await fetch(`${API_BASE}/api/admin/plans/${editingPlan.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan_content: editContent })
      });
      setEditingPlan(null);
      loadPlans();
    } catch (err) {
      console.error('保存失败:', err);
    }
  };
  
  if (loading) {
    return <div className="p-8 text-gray-400">加载中...</div>;
  }
  
  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-white">方案管理</h1>
        <button
          onClick={loadPlans}
          className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-xl hover:bg-white/20 transition-colors text-gray-300"
        >
          <RefreshCw className="w-4 h-4" />
          刷新
        </button>
      </div>
      
      <div className="space-y-4">
        {plans.map(plan => (
          <div key={plan.id} className="bg-white/5 border border-white/10 rounded-2xl p-6">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-bold text-white">{plan.display_name || plan.software_name}</h3>
                <p className="text-sm text-gray-400 mt-1">
                  版本: {plan.version || 'latest'} · 平台: {plan.platform}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  更新时间: {new Date(plan.updated_at).toLocaleString()}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleEdit(plan)}
                  className="p-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors text-gray-400"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDelete(plan.id)}
                  className="p-2 bg-red-500/10 rounded-lg hover:bg-red-500/20 transition-colors text-red-400"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
            
            <div className="mt-4 p-4 bg-slate-900/50 rounded-xl max-h-48 overflow-auto">
              <ReactMarkdown className="prose prose-invert prose-sm max-w-none">
                {plan.plan_content.substring(0, 500) + '...'}
              </ReactMarkdown>
            </div>
          </div>
        ))}
      </div>
      
      {/* 编辑弹窗 */}
      {editingPlan && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 border border-white/10 rounded-2xl w-full max-w-4xl max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b border-white/10">
              <h3 className="text-lg font-bold text-white">编辑方案 - {editingPlan.display_name || editingPlan.software_name}</h3>
            </div>
            <div className="p-6 overflow-auto max-h-[60vh]">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full h-96 bg-slate-900 border border-white/10 rounded-xl p-4 text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div className="p-6 border-t border-white/10 flex justify-end gap-3">
              <button
                onClick={() => setEditingPlan(null)}
                className="px-4 py-2 bg-white/10 rounded-xl text-gray-300 hover:bg-white/20"
              >
                取消
              </button>
              <button
                onClick={handleSaveEdit}
                className="px-4 py-2 bg-purple-500 rounded-xl text-white hover:bg-purple-600"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// 反馈管理
function FeedbackManager() {
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadFeedbacks();
  }, []);
  
  const loadFeedbacks = async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/admin/feedback`);
      const data = await resp.json();
      setFeedbacks(data.results);
    } catch (err) {
      console.error('加载反馈失败:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleMarkProcessed = async (id: number) => {
    try {
      await fetch(`${API_BASE}/api/admin/feedback/${id}/process`, { method: 'PUT' });
      loadFeedbacks();
    } catch (err) {
      console.error('标记失败:', err);
    }
  };
  
  if (loading) {
    return <div className="p-8 text-gray-400">加载中...</div>;
  }
  
  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-white">反馈管理</h1>
        <button
          onClick={loadFeedbacks}
          className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-xl hover:bg-white/20 transition-colors text-gray-300"
        >
          <RefreshCw className="w-4 h-4" />
          刷新
        </button>
      </div>
      
      <div className="space-y-4">
        {feedbacks.map(fb => (
          <div key={fb.id} className="bg-white/5 border border-white/10 rounded-2xl p-6">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-white">{fb.display_name || fb.software_name}</h3>
                  {fb.is_valid ? (
                    <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" />
                      有效
                    </span>
                  ) : (
                    <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs flex items-center gap-1">
                      <XCircle className="w-3 h-3" />
                      无效
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-400 mt-1">
                  平台: {fb.platform} · 时间: {new Date(fb.created_at).toLocaleString()}
                </p>
                {fb.comment && (
                  <p className="text-sm text-gray-300 mt-2 p-3 bg-slate-900/50 rounded-lg">
                    {fb.comment}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {feedbacks.length === 0 && (
          <div className="text-center text-gray-400 py-12">
            暂无反馈数据
          </div>
        )}
      </div>
    </div>
  );
}

// 统计分析
function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  
  useEffect(() => {
    loadStats();
  }, []);
  
  const loadStats = async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/stats`);
      const data = await resp.json();
      setStats(data);
    } catch (err) {
      console.error('加载统计失败:', err);
    }
  };
  
  if (!stats) {
    return <div className="p-8 text-gray-400">加载中...</div>;
  }
  
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-white mb-8">统计分析</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">软件使用统计</h3>
          <div className="space-y-3">
            {stats.software_stats.map((s, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-32 text-gray-300 truncate">{s.name}</div>
                <div className="flex-1 h-6 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                    style={{ width: `${(s.count / Math.max(...stats.software_stats.map(x => x.count))) * 100}%` }}
                  />
                </div>
                <div className="w-12 text-right text-purple-400 font-medium">{s.count}</div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="space-y-6">
          <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4">平台分布</h3>
            <div className="space-y-4">
              {stats.platform_stats.map((p, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-gray-300 capitalize">{p.platform}</span>
                  <div className="flex items-center gap-3">
                    <div className="w-32 h-4 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"
                        style={{ width: `${(p.count / Math.max(...stats.platform_stats.map(x => x.count))) * 100}%` }}
                      />
                    </div>
                    <span className="text-green-400 font-medium w-12 text-right">{p.count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4">反馈质量</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 bg-green-500/10 rounded-xl">
                <p className="text-3xl font-bold text-green-400">{stats.feedback_stats.valid}</p>
                <p className="text-sm text-gray-400 mt-1">有效反馈</p>
              </div>
              <div className="text-center p-4 bg-red-500/10 rounded-xl">
                <p className="text-3xl font-bold text-red-400">{stats.feedback_stats.invalid}</p>
                <p className="text-sm text-gray-400 mt-1">无效反馈</p>
              </div>
            </div>
            <div className="mt-4 text-center text-sm text-gray-400">
              有效率: {stats.feedback_stats.valid + stats.feedback_stats.invalid > 0
                ? Math.round((stats.feedback_stats.valid / (stats.feedback_stats.valid + stats.feedback_stats.invalid)) * 100)
                : 0}%
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// 主布局
function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}

// 主应用
function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('admin_token'));
  
  if (!token) {
    return <LoginPage onLogin={setToken} />;
  }
  
  return (
    <Router>
      <AdminLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/plans" element={<PlansManager />} />
          <Route path="/feedback" element={<FeedbackManager />} />
          <Route path="/stats" element={<StatsPage />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </AdminLayout>
    </Router>
  );
}

export default App;
