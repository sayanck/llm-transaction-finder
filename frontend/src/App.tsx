import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { BarChart3, Search, Brain, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import Dashboard from './components/Dashboard';
import PatternAnalysis from './components/PatternAnalysis';
import AIAnalysis from './components/AIAnalysis';
import { apiService } from './services/api';

function App() {
  const [healthStatus, setHealthStatus] = useState<{
    status: string;
    gemini_configured: boolean;
  } | null>(null);
  const [healthChecked, setHealthChecked] = useState(false);
  const [hasActiveFile, setHasActiveFile] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [dataVersion, setDataVersion] = useState<number>(0);

  useEffect(() => {
    checkHealth();
    checkCurrentFile();
  }, []);

  const checkHealth = async () => {
    try {
      const health = await apiService.healthCheck();
      setHealthStatus(health);
    } catch (error) {
      setHealthStatus({ status: 'unhealthy', gemini_configured: false });
    } finally {
      setHealthChecked(true);
    }
  };

  const getHealthIcon = () => {
    if (!healthChecked) return null;
    
    if (healthStatus?.status === 'healthy') {
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    } else {
      return <XCircle className="w-4 h-4 text-red-500" />;
    }
  };

  const checkCurrentFile = async () => {
    try {
      const response = await apiService.getCurrentFile();
      setHasActiveFile(!!response.data.file_path || response.data.using_default === true);
    } catch (e) {
      setHasActiveFile(false);
    }
  };

  const onUploadChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadError(null);
    setUploading(true);
    try {
      await apiService.uploadFile(file);
      setHasActiveFile(true);
      // Re-fetch basic info and bump data version to re-mount data-fetchers
      checkHealth();
      setDataVersion((v) => v + 1);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
      setHasActiveFile(false);
    } finally {
      // clear input value so same file can be re-selected if needed
      event.target.value = '';
      setUploading(false);
    }
  };

  const navigation = [
    {
      name: 'Dashboard',
      href: '/',
      icon: BarChart3,
      description: 'Transaction overview and statistics'
    },
    {
      name: 'Pattern Analysis',
      href: '/patterns',
      icon: Search,
      description: 'Identify transaction patterns'
    },
    {
      name: 'AI Analysis',
      href: '/ai-analysis',
      icon: Brain,
      description: 'AI-powered suspicious activity detection'
    }
  ];

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation Header */}
        <nav className="bg-white shadow-sm border-b">
          <div className="mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <AlertTriangle className="h-8 w-8 text-primary-600" />
                  <span className="ml-2 text-xl font-bold text-gray-900">
                    Transaction Pattern Finder
                  </span>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                  {navigation.map((item) => (
                    <NavLink
                      key={item.name}
                      to={item.href}
                      className={({ isActive }) =>
                        `inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                          isActive
                            ? 'border-primary-500 text-primary-600'
                            : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                        }`
                      }
                    >
                      <item.icon className="w-4 h-4 mr-2" />
                      {item.name}
                    </NavLink>
                  ))}
                </div>
              </div>
              
              {/* Health Status */}
              <div className="flex items-center space-x-4">
                {/* Upload control */}
                <div className="hidden sm:block">
                  <label className={`btn-secondary cursor-pointer ${uploading ? 'opacity-60 pointer-events-none' : ''}`}>
                    <input type="file" accept=".csv,.xlsx,.xls" className="hidden" onChange={onUploadChange} disabled={uploading} />
                    {uploading ? 'Uploading…' : 'Upload Data'}
                  </label>
                </div>
                {/* {healthChecked && (
                  <div className="flex items-center space-x-2 text-sm">
                    {getHealthIcon()}
                    <span className={`font-medium ${
                      healthStatus?.status === 'healthy' ? 'text-green-700' : 'text-red-700'
                    }`}>
                      Backend {healthStatus?.status === 'healthy' ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                )} */}
                
                {healthStatus?.gemini_configured === false && (
                  <div className="flex items-center space-x-2 text-sm text-yellow-700">
                    <AlertTriangle className="w-4 h-4 text-yellow-500" />
                    <span className="font-medium">AI Features Limited</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </nav>

        {/* Mobile Navigation */}
        <div className="sm:hidden bg-white border-b">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `block px-3 py-2 rounded-md text-base font-medium ${
                    isActive
                      ? 'bg-primary-50 border-primary-500 text-primary-700'
                      : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                  }`
                }
              >
                <div className="flex items-center">
                  <item.icon className="w-4 h-4 mr-3" />
                  <div>
                    <div>{item.name}</div>
                    <div className="text-xs text-gray-500">{item.description}</div>
                  </div>
                </div>
              </NavLink>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <main className="flex-1">
          {!hasActiveFile ? (
            <div className="p-8 max-w-2xl mx-auto">
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-medium text-gray-900">Upload a dataset to begin</h3>
                </div>
                <div className="card-content">
                  <p className="text-sm text-gray-600 mb-4">Upload a CSV or Excel file containing transactions. The UI will analyze and display insights based on your file.</p>
                  <label className={`btn-primary inline-flex items-center cursor-pointer ${uploading ? 'opacity-60 pointer-events-none' : ''}`}>
                    <input type="file" accept=".csv,.xlsx,.xls" className="hidden" onChange={onUploadChange} disabled={uploading} />
                    {uploading ? 'Uploading…' : 'Upload File'}
                  </label>
                  {uploadError && (
                    <p className="text-sm text-red-600 mt-3">{uploadError}</p>
                  )}
                  {uploading && (
                    <p className="text-sm text-gray-600 mt-3">Please wait while we process your file…</p>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <Routes>
              <Route path="/" element={<Dashboard key={`dash-${dataVersion}`} />} />
              <Route path="/patterns" element={<PatternAnalysis key={`pat-${dataVersion}`} />} />
              <Route path="/ai-analysis" element={<AIAnalysis key={`ai-${dataVersion}`} />} />
            </Routes>
          )}
        </main>

        {/* Footer */}
        
      </div>
    </Router>
  );
}

export default App;